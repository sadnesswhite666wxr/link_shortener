from urllib.parse import urlparse

from pydantic import computed_field, field_validator
from sqlmodel import Field, SQLModel

from src.app.utils.base62 import encode_base62


class LinkDataBase(SQLModel):
    origin: str = Field(max_length=512)


class LinkDataRead(LinkDataBase):
    id: int
    origin: str

    @computed_field
    @property
    def shorten(self) -> str:
        return encode_base62(self.id)


class LinkDataCreate(LinkDataBase):
    @field_validator("origin")
    @classmethod
    def validate_origin(cls, v: str):
        url_clean = v.strip()
        result = urlparse(url_clean)
        has_valid_scheme = result.scheme in ("http", "https")
        has_net_loc = bool(result.netloc)

        if not (has_valid_scheme and has_net_loc):
            raise ValueError("Неверный формат URL. Требуется http:// или https://")

        return url_clean


class LinkDataUpdate(LinkDataCreate):
    pass


class LinkDataRedis(LinkDataBase):
    id: int
    created_by: int

    @computed_field
    @property
    def shorten(self) -> str:
        return encode_base62(self.id)
