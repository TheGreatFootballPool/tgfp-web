from typing import Optional, List
from sqlmodel import Field, Session, select

from .base import TGFPModelBase  # your SQLModel base with timestamps, etc.


class Team(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    city: str
    long_name: str
    losses: int
    short_name: str
    ties: int
    wins: int
    full_name: str
    logo_url: str
    tgfp_nfl_team_id: str = Field(
        index=True, unique=True, description="External TGFP/NFL team id"
    )
    discord_emoji: str

    @staticmethod
    def all_teams(session: Session) -> List["Team"]:
        """returns a list of all teams"""
        statement = select(Team)
        return list(session.exec(statement).all())
