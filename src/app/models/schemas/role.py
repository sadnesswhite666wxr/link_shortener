from sqlmodel import Field, SQLModel

from src.app.models.schemas.permission import PermissionRead


class RoleBase(SQLModel):
    name: str = Field(max_length=512, unique=True)
    description: str = Field(max_length=512)


class RoleCreate(RoleBase):
    permissions: list[int]


class RoleUpdate(RoleCreate):
    pass


class RoleRead(RoleBase):
    id: int


class RoleWithPermission(RoleRead):
    permissions: list[PermissionRead] = []
