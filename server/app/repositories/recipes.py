from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import commit
from ..models import Category, Recipe, Tag


def get(db: Session, recipe_id: int) -> Optional[Recipe]:
    return db.get(Recipe, recipe_id)


def find(db: Session, user_id: Optional[int], search: Optional[str], category: Optional[str]) -> list[Recipe]:
    """user_id=None значит «все пользователи» (для администратора)."""
    query = select(Recipe).order_by(Recipe.id)
    if user_id is not None:
        query = query.where(Recipe.user_id == user_id)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(or_(func.lower(Recipe.name).like(like), func.lower(Recipe.notes).like(like)))
    if category:
        query = query.where(Recipe.category.has(Category.name == category))
    return list(db.scalars(query))


def category_names(db: Session, user_id: Optional[int]) -> list[str]:
    query = select(Category.name).join(Recipe, Recipe.category_id == Category.id).distinct()
    if user_id is not None:
        query = query.where(Recipe.user_id == user_id)
    return list(db.scalars(query.order_by(Category.name)))


def get_or_create_category(db: Session, name: str) -> Category:
    item = db.scalar(select(Category).where(Category.name == name))
    if not item:
        item = Category(name=name)
        db.add(item)
        db.flush()
    return item


def get_or_create_tag(db: Session, name: str) -> Tag:
    item = db.scalar(select(Tag).where(Tag.name == name))
    if not item:
        item = Tag(name=name)
        db.add(item)
        db.flush()
    return item


def add_many(db: Session, items: list[Recipe]) -> None:
    db.add_all(items)
    commit(db)


def save(db: Session) -> None:
    commit(db)


def delete(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
    commit(db)
