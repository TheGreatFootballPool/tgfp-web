from datetime import datetime
from typing import Optional, TYPE_CHECKING

import pytz
from sqlmodel import Field, Relationship

from .base import TGFPModelBase

if TYPE_CHECKING:
    from .team import Team


class Game(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys to teams (matches favorite/road/home links in Beanie)
    favorite_team_id: int = Field(foreign_key="team.id", index=True)
    road_team_id: int = Field(foreign_key="team.id", index=True)
    home_team_id: int = Field(foreign_key="team.id", index=True)

    # Core fields (same names/types as Beanie)
    game_status: str
    spread: float
    start_time: datetime = Field(index=True)
    week_no: int = Field(index=True)
    road_team_score: int
    home_team_score: int
    season: int = Field(index=True)
    tgfp_nfl_game_id: str = Field(
        index=True, unique=True, description="External TGFP/NFL game id"
    )

    # View-only relationships for convenience (no schema impact)
    home_team: "Team" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Game.home_team_id==Team.id",
            "viewonly": True,
        }
    )
    road_team: "Team" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Game.road_team_id==Team.id",
            "viewonly": True,
        }
    )
    favorite_team: "Team" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Game.favorite_team_id==Team.id",
            "viewonly": True,
        }
    )

    # ----- helpers matching the original model -----
    @property
    def is_final(self) -> bool:
        """Returns true if the game is final"""
        return self.game_status == "STATUS_FINAL"

    @property
    def is_pregame(self) -> bool:
        """Returns true if the game is pregame"""
        return self.game_status == "STATUS_SCHEDULED"

    @property
    def underdog_team(self) -> Optional["Team"]:
        """Returns the underdog (mirrors original logic)."""
        if self.favorite_team_id == self.home_team_id:
            return self.road_team
        return self.home_team

    @property
    def pacific_start_time(self) -> datetime:
        """Returns the start time in the US/Pacific timezone"""
        utc_dt = self.start_time.replace(tzinfo=pytz.utc)
        pac = pytz.timezone("US/Pacific")
        return pac.normalize(utc_dt.astimezone(pac))
