from __future__ import annotations
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

from new_models.sql.base import TimestampMixin


class PickSQL(TimestampMixin, SQLModel, table=True):
    __tablename__ = "picks"
    __table_args__ = (
        UniqueConstraint("mongo_id", name="uq_picks_mongo_id"),
        UniqueConstraint(
            "player_id", "season", "week_no", name="uq_picks_player_season_week"
        ),
    )
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    mongo_id: Optional[str] = (
        None  # present for the one-time migration; drop later if you want
    )

    # ownership / identity
    player_id: int = Field(foreign_key="players.id", index=True)

    # week context
    season: int = Field(index=True)
    week_no: int = Field(index=True)

    # choices / scoring (FKs point at teams)
    lock_team_id: int = Field(foreign_key="teams.id", index=True)
    upset_team_id: Optional[int] = Field(
        default=None, foreign_key="teams.id", index=True
    )

    bonus: int = 0
    wins: int = 0
    losses: int = 0

    created_at: Optional[int] = None  # unix ts to match your pattern
