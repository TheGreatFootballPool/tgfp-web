from __future__ import annotations
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

from new_models.sql.base import TimestampMixin


class TeamSQL(TimestampMixin, SQLModel, table=True):
    """
    Relational version of Team (Beanie) with a surrogate PK and preserved mongo_id.
    """

    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("mongo_id", name="uq_teams_mongo_id"),
        UniqueConstraint("tgfp_nfl_team_id", name="uq_teams_tgfp_id"),
    )

    # Surrogate PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # Bridge back to Mongo (24-char hex string)
    mongo_id: str = Field(description="Mongo ObjectId as 24-char hex string")

    # External key (useful but not PK; can change upstream)
    tgfp_nfl_team_id: Optional[str] = Field(default=None, index=True)

    # Domain fields (mirror Beanie.Team)
    city: str
    long_name: str
    short_name: str = Field(index=True)  # not unique; teams can rename/move
    full_name: str
    logo_url: str
    discord_emoji: str
    wins: int = 0
    losses: int = 0
    ties: int = 0
