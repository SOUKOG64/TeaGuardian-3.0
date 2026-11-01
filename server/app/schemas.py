from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=32)]


class Credentials(BaseModel):
    username: Username
    password: str = Field(min_length=6, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str


class RecipeIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    temperature: int = Field(ge=0, le=100)
    brew_seconds: int = Field(gt=0, le=86400)
    rating: int = Field(default=0, ge=0, le=5)
    category: Optional[str] = Field(default=None, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=10)
    notes: str = Field(default="", max_length=2000)


class RecipeUpdate(BaseModel):
    """Для PATCH: присылать можно только те поля, которые меняются."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    temperature: Optional[int] = Field(default=None, ge=0, le=100)
    brew_seconds: Optional[int] = Field(default=None, gt=0, le=86400)
    rating: Optional[int] = Field(default=None, ge=0, le=5)
    category: Optional[str] = Field(default=None, max_length=40)
    tags: Optional[list[str]] = Field(default=None, max_length=10)
    notes: Optional[str] = Field(default=None, max_length=2000)


class RecipeOut(BaseModel):
    id: int
    name: str
    temperature: int
    brew_seconds: int
    rating: int
    category: Optional[str]
    tags: list[str]
    notes: str

    @classmethod
    def of(cls, r) -> "RecipeOut":
        return cls(
            id=r.id,
            name=r.name,
            temperature=r.temperature,
            brew_seconds=r.brew_seconds,
            rating=r.rating,
            category=r.category.name if r.category else None,
            tags=sorted(t.name for t in r.tags),
            notes=r.notes,
        )
