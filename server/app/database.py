from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from . import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _setup_sqlite(conn, _):
    # SQLite по умолчанию не следит за внешними ключами и не умеет lower() для кириллицы
    conn.create_function("lower", 1, lambda s: s.lower() if isinstance(s, str) else s)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def commit(db: Session) -> None:
    """commit() с откатом при ошибке: единое место для всех записей в БД."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
