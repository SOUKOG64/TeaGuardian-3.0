from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import commit
from ..errors import BadRequest
from ..models import Role, User

ROLES = ("user", "admin")


def ensure_roles(db: Session) -> None:
    for name in ROLES:
        if not db.scalar(select(Role).where(Role.name == name)):
            db.add(Role(name=name))
    commit(db)


def get_role(db: Session, name: str) -> Role:
    return db.scalar(select(Role).where(Role.name == name))


def get_by_username(db: Session, username: str):
    return db.scalar(select(User).where(func.lower(User.username) == username.lower()))


def get_by_id(db: Session, user_id: int):
    return db.get(User, user_id)


def create(db: Session, username: str, password_hash: str, role: Role) -> User:
    user = User(username=username, password_hash=password_hash, role=role)
    db.add(user)
    try:
        commit(db)
    except IntegrityError:
        raise BadRequest("Такой логин уже занят")
    return user
