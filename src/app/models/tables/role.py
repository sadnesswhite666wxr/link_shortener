from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from src.app.models.schemas.role import RoleBase
from src.app.models.tables.role_permission import RolePermissionLink
from src.app.models.tables.user_role import UserRoleLink

if TYPE_CHECKING:
    from .permission import Permission
    from .user import User


class Role(RoleBase, table=True):
    __tablename__ = "role"
    id: int = Field(default=None, primary_key=True)

    permissions: list["Permission"] = Relationship(
        link_model=RolePermissionLink,
        back_populates="roles",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    users: list["User"] = Relationship(
        link_model=UserRoleLink,
        back_populates="roles",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
