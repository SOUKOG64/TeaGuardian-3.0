from typing import Optional

from sqlalchemy.orm import Session

from ..errors import NotFound
from ..models import Recipe, User
from ..repositories import recipes as repo

# Стартовые рецепты: копируются каждому новому пользователю
STARTER = [
    ("Да Хун Пао", 95, 25, "Улун", "Скалистый улун. Первые проливы короткие."),
    ("Те Гуаньинь", 90, 30, "Улун", "Светлый улун, цветочный аромат."),
    ("Шен Пуэр", 95, 20, "Пуэр", "Сырой пуэр. Первый пролив можно слить."),
    ("Шу Пуэр", 95, 15, "Пуэр", "Выдержанный пуэр, тёмный настой."),
    ("Жёлтый чай", 85, 40, "Жёлтый", "Мягкий, нежный вкус. Не кипятком."),
]


def is_admin(user: User) -> bool:
    return user.role.name == "admin"


def _clean_tags(names: list[str]) -> list[str]:
    result: list[str] = []
    for name in names:
        name = name.strip()[:30]
        if name and name.lower() not in [t.lower() for t in result]:
            result.append(name)
    return result


def _apply(db: Session, recipe: Recipe, data: dict) -> None:
    """Записывает присланные поля в рецепт. Категория и теги хранятся в своих таблицах."""
    if "category" in data:
        name = (data.pop("category") or "").strip()
        recipe.category = repo.get_or_create_category(db, name) if name else None
    if "tags" in data:
        recipe.tags = [repo.get_or_create_tag(db, n) for n in _clean_tags(data.pop("tags"))]
    for key, value in data.items():
        setattr(recipe, key, value)


def _owned(db: Session, user: User, recipe_id: int) -> Recipe:
    recipe = repo.get(db, recipe_id)
    # чужую запись не выдаём и не подтверждаем, что она существует
    if recipe is None or (recipe.user_id != user.id and not is_admin(user)):
        raise NotFound("Рецепт не найден")
    return recipe


def create_starter(db: Session, user: User) -> None:
    items = [
        Recipe(user_id=user.id, name=n, temperature=t, brew_seconds=s, rating=0, notes=note,
               category=repo.get_or_create_category(db, c))
        for n, t, s, c, note in STARTER
    ]
    repo.add_many(db, items)


def list_recipes(db: Session, user: User, search: Optional[str], category: Optional[str]) -> list[Recipe]:
    return repo.find(db, None if is_admin(user) else user.id, search, category)


def list_categories(db: Session, user: User) -> list[str]:
    return repo.category_names(db, None if is_admin(user) else user.id)


def get_recipe(db: Session, user: User, recipe_id: int) -> Recipe:
    return _owned(db, user, recipe_id)


def create_recipe(db: Session, user: User, data: dict) -> Recipe:
    recipe = Recipe(user_id=user.id, name=data.pop("name"), temperature=data.pop("temperature"),
                    brew_seconds=data.pop("brew_seconds"))
    _apply(db, recipe, data)
    repo.add_many(db, [recipe])
    return recipe


def update_recipe(db: Session, user: User, recipe_id: int, data: dict) -> Recipe:
    recipe = _owned(db, user, recipe_id)
    # null можно прислать только для категории (это «убрать категорию»)
    data = {k: v for k, v in data.items() if v is not None or k == "category"}
    _apply(db, recipe, data)
    repo.save(db)
    return recipe


def delete_recipe(db: Session, user: User, recipe_id: int) -> None:
    repo.delete(db, _owned(db, user, recipe_id))
