from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship
import sqlalchemy as sa

from .base import TGFPModelBase

if TYPE_CHECKING:
    # noinspection PyUnusedImports
    from .award import Award
    from .player import Player
    from .game import Game


class PlayerAward(TGFPModelBase, table=True):
    __table_args__ = (
        sa.UniqueConstraint(
            "player_id",
            "award_id",
            "season",
            "week_no",
            "game_id",
            name="uq_playeraward_player_award_week",
        ),
    )
    id: int | None = Field(default=None, primary_key=True)

    player_id: int = Field(foreign_key="player.id", index=True)
    award_id: int = Field(foreign_key="award.id", index=True)
    season: int = Field(index=True)
    week_no: int = Field(index=True)
    game_id: int | None = Field(foreign_key="game.id", index=True)
    notified_at: datetime | None = Field(default=None)
    player: "Player" = Relationship(back_populates="player_awards")
    award: "Award" = Relationship()
    game: "Game" = Relationship()
