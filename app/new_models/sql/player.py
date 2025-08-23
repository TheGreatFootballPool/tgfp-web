from __future__ import annotations
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

from new_models.sql.base import TimestampMixin


class PlayerSQL(TimestampMixin, SQLModel, table=True):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("mongo_id", name="uq_players_mongo_id"),
        UniqueConstraint("email", name="uq_players_email"),
    )
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    mongo_id: str  # 24-char hex from Mongo

    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str
    # at top
    import sqlalchemy as sa

    # inside PlayerSQL
    discord_id: int = Field(
        default=0,
        sa_column=sa.Column(sa.BigInteger(), nullable=False),  # was Integer
    )
