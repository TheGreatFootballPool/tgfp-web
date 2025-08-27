# app/models/player_game_pick.py
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
import sqlalchemy as sa

from .base import TGFPModelBase

if TYPE_CHECKING:
    from .player import Player
    from .game import Game
    from .team import Team


class PlayerGamePick(TGFPModelBase, table=True):
    __table_args__ = (
        sa.UniqueConstraint("player_id", "game_id", name="uq_playergamepick_player_game"),
        sa.Index(
            "uq_one_lock_per_week",
            "player_id", "season", "week_no",
            unique=True,
            postgresql_where=sa.text("is_lock = true"),
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)

    player_id: int = Field(foreign_key="player.id", index=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    picked_team_id: int = Field(foreign_key="team.id", index=True)

    # denormalized for constraints/queries
    # TODO: add constraints to ensure there is only one lock per / season/ week
    season: int = Field(index=True)
    week_no: int = Field(index=True)


    # game-time choices
    is_lock: bool = False
    is_upset: bool = False
    # scoring cache (optional — can be computed on the fly)
    awarded_points: int = 0
    is_win: bool = False

    # convenience relationships (view-only is fine if you prefer)
    player: "Player" = Relationship(back_populates="game_picks")
    game: "Game" = Relationship()
    picked_team: "Team" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "PlayerGamePick.picked_team_id==Team.id", "viewonly": True}
    )