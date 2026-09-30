from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from src.app.models.schemas.permission import PermissionBase
from src.app.models.tables.role_permission import RolePermissionLink

if TYPE_CHECKING:
    from .role import Role


class Permission(PermissionBase, table=True):
    __tablename__ = "permission"
    id: int = Field(default=None, primary_key=True)

    __table_args__ = (UniqueConstraint("resource", "action", name="uq_resource_action"),)

    roles: list["Role"] = Relationship(
        link_model=RolePermissionLink,
        back_populates="permissions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
