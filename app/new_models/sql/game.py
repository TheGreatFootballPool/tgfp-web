from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field

from new_models.sql.base import TimestampMixin


class GameSQL(TimestampMixin, SQLModel, table=True):
    __tablename__ = "games"

    # Surrogate PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # Bridge to Mongo for migration/audits
    mongo_id: Optional[str] = Field(default=None, description="Mongo ObjectId (hex)")

    # Core game fields (mirror Beanie names where possible)
    season: int = Field(index=True)
    week_no: int = Field(index=True)
    start_time: int = Field(index=True, description="unix ts")

    # Team relationships (FKs → teams.id)
    home_team_id: int = Field(foreign_key="teams.id", index=True)
    road_team_id: int = Field(foreign_key="teams.id", index=True)
    favorite_team_id: Optional[int] = Field(
        default=None, foreign_key="teams.id", index=True
    )

    # Status / scoring
    game_status: str = Field(default="STATUS_SCHEDULED", index=True)
    spread: float = 0.0
    home_team_score: Optional[int] = None
    road_team_score: Optional[int] = None

    # External reference (not a PK)
    tgfp_nfl_game_id: Optional[str] = Field(default=None, index=True)
