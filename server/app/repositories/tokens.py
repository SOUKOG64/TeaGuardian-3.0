from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import commit
from ..models import RefreshToken


def add(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> None:
    db.add(RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    commit(db)


def get(db: Session, token_hash: str):
    return db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))


def revoke(db: Session, token: RefreshToken) -> None:
    token.revoked = True
    commit(db)
