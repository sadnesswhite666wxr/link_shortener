from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from src.app.models.schemas.role import RoleRead


class UserBase(SQLModel):
    username: str = Field(unique=True)
    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserWithRoles(UserRead):
    roles: list[RoleRead] = []


class UserAddRole(SQLModel):
    roles: list[int]


class UserRemoveRole(SQLModel):
    roles: list[int]


class UserRedis(UserBase):
    id: int
    permissions: list[str]
    model_config = ConfigDict(from_attributes=True)
