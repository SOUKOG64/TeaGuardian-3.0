import os
import sys
import tempfile
from pathlib import Path

# своя пустая БД и ключ для тестов, настоящие данные не трогаем
os.environ["TEA_DB"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["TEA_SECRET"] = "test-secret"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import config
from app.database import Base, SessionLocal, engine
from app.main import app
from app.repositories.users import ensure_roles
from app.services import auth as auth_service
from app.services import recipes as recipes_service

RECIPE = {"name": "Лунцзин", "temperature": 80, "brew_seconds": 45, "rating": 4,
          "category": "Зелёный", "tags": ["весна", "Весна", "лёгкий"], "notes": "Свежий"}


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_roles(db)
    auth_service._failures.clear()
    config.ADMIN_USERNAME = ""
    return TestClient(app, raise_server_exceptions=False)


def register(client, name="ivan", password="secret1"):
    r = client.post("/auth/register", json={"username": name, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


def headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_register_login_me(client):
    register(client)
    r = client.post("/auth/login", json={"username": "ivan", "password": "secret1"})
    assert r.status_code == 200
    me = client.get("/auth/me", headers=headers(r.json()))
    assert me.json()["username"] == "ivan" and me.json()["role"] == "user"


def test_starter_recipes_copied(client):
    t = register(client)
    items = client.get("/recipes", headers=headers(t)).json()
    assert [r["name"] for r in items][:2] == ["Да Хун Пао", "Те Гуаньинь"] and len(items) == 5


def test_errors_400_401_404(client):
    t = register(client)
    assert client.post("/auth/register", json={"username": "IVAN", "password": "secret1"}).status_code == 400
    assert client.post("/auth/register", json={"username": "ab", "password": "1"}).status_code == 400
    assert client.post("/auth/login", json={"username": "ivan", "password": "wrong!!"}).status_code == 401
    assert client.get("/recipes").status_code == 401
    assert client.get("/recipes", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/recipes/9999", headers=headers(t)).status_code == 404
    bad = dict(RECIPE, temperature=500)
    r = client.post("/recipes", json=bad, headers=headers(t))
    assert r.status_code == 400 and "temperature" in r.json()["detail"]


def test_crud(client):
    h = headers(register(client))
    created = client.post("/recipes", json=RECIPE, headers=h)
    assert created.status_code == 201
    body = created.json()
    assert body["category"] == "Зелёный" and body["tags"] == ["весна", "лёгкий"]
    rid = body["id"]
    assert client.get(f"/recipes/{rid}", headers=h).json()["name"] == "Лунцзин"
    patched = client.patch(f"/recipes/{rid}", json={"rating": 5, "tags": ["новый"]}, headers=h)
    assert patched.json()["rating"] == 5 and patched.json()["tags"] == ["новый"]
    assert patched.json()["name"] == "Лунцзин"  # остальное не тронуто
    assert client.patch(f"/recipes/{rid}", json={"category": None}, headers=h).json()["category"] is None
    assert client.delete(f"/recipes/{rid}", headers=h).status_code == 204
    assert client.get(f"/recipes/{rid}", headers=h).status_code == 404


def test_search_and_category_filter(client):
    h = headers(register(client))
    assert [r["name"] for r in client.get("/recipes?search=пуэр", headers=h).json()] == ["Шен Пуэр", "Шу Пуэр"]
    assert len(client.get("/recipes?category=Улун", headers=h).json()) == 2
    assert len(client.get("/recipes?search=нет-такого", headers=h).json()) == 0
    assert sorted(client.get("/categories", headers=h).json()) == ["Жёлтый", "Пуэр", "Улун"]


def test_user_sees_only_own_records(client):
    a, b = headers(register(client, "anna")), headers(register(client, "boris"))
    rid = client.post("/recipes", json=RECIPE, headers=a).json()["id"]
    assert client.get(f"/recipes/{rid}", headers=b).status_code == 404
    assert client.patch(f"/recipes/{rid}", json={"rating": 1}, headers=b).status_code == 404
    assert client.delete(f"/recipes/{rid}", headers=b).status_code == 404
    assert len(client.get("/recipes", headers=b).json()) == 5


def test_admin_sees_everything(client):
    config.ADMIN_USERNAME = "root"
    a = headers(register(client, "anna"))
    root = register(client, "root")
    assert client.get("/auth/me", headers=headers(root)).json()["role"] == "admin"
    rid = client.post("/recipes", json=RECIPE, headers=a).json()["id"]
    assert len(client.get("/recipes", headers=headers(root)).json()) == 11
    assert client.delete(f"/recipes/{rid}", headers=headers(root)).status_code == 204


def test_refresh_rotates_and_logout_revokes(client):
    t = register(client)
    new = client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]})
    assert new.status_code == 200
    # старый refresh-токен одноразовый
    assert client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401
    assert client.post("/auth/logout", json={"refresh_token": new.json()["refresh_token"]}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": new.json()["refresh_token"]}).status_code == 401


def test_login_brute_force_limited(client):
    register(client)
    for _ in range(5):
        assert client.post("/auth/login", json={"username": "ivan", "password": "nope-nope"}).status_code == 401
    assert client.post("/auth/login", json={"username": "ivan", "password": "secret1"}).status_code == 429


def test_unhandled_error_gives_500(client, monkeypatch):
    t = register(client)
    monkeypatch.setattr(recipes_service, "list_recipes", lambda *a: 1 / 0)
    r = client.get("/recipes", headers=headers(t))
    assert r.status_code == 500 and r.json() == {"detail": "Внутренняя ошибка сервера"}


def test_swagger_available(client):
    assert client.get("/docs").status_code == 200
    assert "/recipes/{recipe_id}" in client.get("/openapi.json").json()["paths"]
