from sqlmodel import Field, SQLModel


class PermissionBase(SQLModel):
    resource: str = Field(max_length=512)
    action: str = Field(max_length=512)


class PermissionCreate(PermissionBase):
    pass


class PermissionRead(PermissionBase):
    id: int
