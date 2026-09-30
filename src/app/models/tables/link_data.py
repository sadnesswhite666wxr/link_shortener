from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field

from src.app.models.schemas.link_data import LinkDataBase


class LinkData(LinkDataBase, table=True):
    __tablename__ = "link_data"

    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    created_by: int = Field(default=None, foreign_key="user.id", ondelete="CASCADE")
