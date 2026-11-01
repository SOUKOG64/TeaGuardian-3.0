import time
from datetime import timedelta

from sqlalchemy.orm import Session

from .. import config, security
from ..errors import BadRequest, TooManyRequests, Unauthorized
from ..models import User, now
from ..repositories import tokens, users
from ..schemas import TokenPair, UserOut
from . import recipes as recipes_service

# Защита от подбора пароля: не больше 5 неудачных входов за 5 минут на один логин
_failures: dict[str, list[float]] = {}
MAX_FAILURES = 5
WINDOW = 300


def _check_limit(key: str) -> None:
    recent = [t for t in _failures.get(key, []) if time.time() - t < WINDOW]
    _failures[key] = recent
    if len(recent) >= MAX_FAILURES:
        raise TooManyRequests("Слишком много неудачных попыток входа. Подождите 5 минут")


def _issue(db: Session, user: User) -> TokenPair:
    refresh = security.new_refresh_token()
    tokens.add(db, user.id, security.hash_token(refresh), now() + timedelta(days=config.REFRESH_DAYS))
    return TokenPair(access_token=security.make_access_token(user.id), refresh_token=refresh)


def register(db: Session, username: str, password: str) -> TokenPair:
    if users.get_by_username(db, username):
        raise BadRequest("Такой логин уже занят")
    is_admin = bool(config.ADMIN_USERNAME) and username.lower() == config.ADMIN_USERNAME.lower()
    user = users.create(db, username, security.hash_password(password),
                        users.get_role(db, "admin" if is_admin else "user"))
    recipes_service.create_starter(db, user)
    return _issue(db, user)


def login(db: Session, username: str, password: str) -> TokenPair:
    key = username.lower()
    _check_limit(key)
    user = users.get_by_username(db, username)
    if user is None or not security.verify_password(password, user.password_hash):
        _failures.setdefault(key, []).append(time.time())
        raise Unauthorized("Неверный логин или пароль")
    return _issue(db, user)


def refresh(db: Session, refresh_token: str) -> TokenPair:
    row = tokens.get(db, security.hash_token(refresh_token))
    if row is None or row.revoked or row.expires_at < now():
        raise Unauthorized("Сессия истекла, войдите снова")
    tokens.revoke(db, row)  # каждый refresh-токен одноразовый
    return _issue(db, row.user)


def logout(db: Session, refresh_token: str) -> None:
    row = tokens.get(db, security.hash_token(refresh_token))
    if row is not None and not row.revoked:
        tokens.revoke(db, row)


def user_from_token(db: Session, access_token: str) -> User:
    user = users.get_by_id(db, security.read_access_token(access_token))
    if user is None:
        raise Unauthorized("Пользователь не найден")
    return user


def profile(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, role=user.role.name)
