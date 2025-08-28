from typing import Optional, List, TYPE_CHECKING
import sqlalchemy as sa
from sqlmodel import Field, Relationship

from .base import TGFPModelBase

if TYPE_CHECKING:
    from .player_game_pick import PlayerGamePick


class Player(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str
    discord_id: int = Field(sa_type=sa.BigInteger, nullable=False)

    game_picks: List["PlayerGamePick"] = Relationship(back_populates="player")

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name
