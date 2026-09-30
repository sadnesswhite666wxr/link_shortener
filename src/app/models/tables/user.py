from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from src.app.models.schemas.user import UserBase
from src.app.models.tables.user_role import UserRoleLink

if TYPE_CHECKING:
    from .role import Role


class User(UserBase, table=True):
    __tablename__ = "user"
    id: int = Field(default=None, primary_key=True)
    hashed_password: str

    roles: list["Role"] = Relationship(
        link_model=UserRoleLink,
        back_populates="users",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
