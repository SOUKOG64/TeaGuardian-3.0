from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import RecipeIn, RecipeOut, RecipeUpdate
from ..services import recipes as service
from .deps import current_user

router = APIRouter(tags=["recipes"])


@router.get("/recipes", response_model=list[RecipeOut], summary="Список рецептов")
def list_recipes(
    search: Optional[str] = Query(None, description="Поиск по названию и заметкам"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return [RecipeOut.of(r) for r in service.list_recipes(db, user, search, category)]


@router.post("/recipes", response_model=RecipeOut, status_code=201, summary="Создать рецепт")
def create_recipe(data: RecipeIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return RecipeOut.of(service.create_recipe(db, user, data.model_dump()))


@router.get("/recipes/{recipe_id}", response_model=RecipeOut, summary="Один рецепт")
def get_recipe(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return RecipeOut.of(service.get_recipe(db, user, recipe_id))


@router.patch("/recipes/{recipe_id}", response_model=RecipeOut, summary="Изменить рецепт")
def update_recipe(recipe_id: int, data: RecipeUpdate, user: User = Depends(current_user),
                  db: Session = Depends(get_db)):
    return RecipeOut.of(service.update_recipe(db, user, recipe_id, data.model_dump(exclude_unset=True)))


@router.delete("/recipes/{recipe_id}", status_code=204, summary="Удалить рецепт")
def delete_recipe(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    service.delete_recipe(db, user, recipe_id)
    return Response(status_code=204)


@router.get("/categories", response_model=list[str], summary="Категории пользователя")
def list_categories(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return service.list_categories(db, user)
