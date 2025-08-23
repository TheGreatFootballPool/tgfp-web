from __future__ import annotations
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

from new_models.sql.base import TimestampMixin


class PickDetailSQL(TimestampMixin, SQLModel, table=True):
    __tablename__ = "pick_details"
    __table_args__ = (
        UniqueConstraint("pick_id", "game_id", name="uq_pick_details_pick_game"),
    )
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    mongo_id: Optional[str] = None  # keep for migration/audit; safe to drop later

    pick_id: int = Field(foreign_key="picks.id", index=True)
    game_id: int = Field(foreign_key="games.id", index=True)
    winning_team_id: int = Field(foreign_key="teams.id", index=True)
