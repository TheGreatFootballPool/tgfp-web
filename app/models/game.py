from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

import pytz
from sqlmodel import Field, Relationship, Session, select, col

from .base import TGFPModelBase
from .model_helpers import current_nfl_season

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
        """Return start_time as US/Pacific tz-aware datetime."""
        pac = pytz.timezone("America/Los_Angeles")
        if self.start_time.tzinfo is None:
            # assume stored as UTC naive
            utc_dt = self.start_time.replace(tzinfo=pytz.utc)
        else:
            utc_dt = self.start_time.astimezone(pytz.utc)
        return pac.normalize(utc_dt.astimezone(pac))

    @property
    def utc_start_time(self) -> datetime:
        """Return start_time as a UTC-aware datetime."""
        if self.start_time.tzinfo is None:
            # assume it's stored as UTC naive
            return self.start_time.replace(tzinfo=pytz.utc)
        # convert any aware datetime to UTC
        return self.start_time.astimezone(pytz.utc)

    @property
    def winning_team(self) -> Optional["Team"]:
        if self.is_final:
            if self.home_team_score > self.road_team_score:
                return self.home_team
            if self.home_team_score < self.road_team_score:
                return self.road_team
        return None

    @staticmethod
    def games_for_week(session: Session, season: int = None) -> List["Game"]:
        """Gets a list of games for a given week and season, sorted by game start time."""
        search_week: int = Game.most_recent_week(session)
        search_season: int = season if season else current_nfl_season()

        statement = (
            select(Game)
            .where(Game.season == search_season)
            .where(Game.week_no == search_week)
            .order_by(Game.start_time)
        )

        games = list(session.exec(statement).all())
        return games

    @staticmethod
    def most_recent_week(session: Session) -> int:
        """
        if there are no records in the table at all, return 0
        else grab the most recent game and return its week_no
        """
        search_season: int = current_nfl_season()

        statement = (
            select(Game)
            .where(Game.season == search_season)
            .order_by(col(Game.start_time).desc())
        )
        last_game = session.exec(statement).first()
        if last_game is None:
            return 0
        return last_game.week_no

    @staticmethod
    def get_first_game_of_the_week(session: Session) -> "Game":
        """Returns the 'first' game of a week given the info"""
        games: List[Game] = Game.games_for_week(session)
        games.sort(key=lambda x: x.start_time, reverse=True)
        return games[-1]
