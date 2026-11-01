import os
import secrets
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("TEA_DB", f"sqlite:///{BASE / 'teaguardian.db'}")

# Кто зарегистрируется с этим логином, станет администратором (видит все записи).
# По умолчанию пусто: админа нет.
ADMIN_USERNAME = os.getenv("TEA_ADMIN", "")

ACCESS_MINUTES = 30
REFRESH_DAYS = 30


def _load_secret() -> str:
    """Ключ для подписи JWT: из переменной TEA_SECRET или из файла secret.key (создаётся сам)."""
    if os.getenv("TEA_SECRET"):
        return os.environ["TEA_SECRET"]
    path = BASE / "secret.key"
    if not path.exists():
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip()


SECRET_KEY = _load_secret()
