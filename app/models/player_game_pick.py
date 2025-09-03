# app/models/player_game_pick.py
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
import sqlalchemy as sa

from .base import TGFPModelBase

if TYPE_CHECKING:
    # noinspection PyUnusedImports
    from .player import Player
    from .game import Game
    from .team import Team


class PlayerGamePick(TGFPModelBase, table=True):
    """
    Represents a single pick a player makes for a specific NFL game.

    This table enforces **one pick per (player, game)** and allows at most
    **one lock per player per week** via a partial unique index. A few
    columns (e.g., ``season``, ``week_no``) are *denormalized* to simplify
    constraints and common queries.

    :ivar id: Primary key.
    :vartype id: int | None
    :ivar player_id: FK → ``player.id``. The owner of the pick.
    :vartype player_id: int
    :ivar game_id: FK → ``game.id``. The game the pick refers to.
    :vartype game_id: int
    :ivar picked_team_id: FK → ``team.id``. The team the player picked to win.
    :vartype picked_team_id: int

    :ivar season: Denormalized season value (e.g., 2025). Indexed.
    :vartype season: int
    :ivar week_no: Denormalized week number within the season. Indexed.
    :vartype week_no: int

    :ivar is_lock: Whether the pick is designated as the player's weekly lock.
                  At most **one** lock is permitted per ``(player_id, season, week_no)``.
    :vartype is_lock: bool
    :ivar is_upset: Whether the player marked this pick as an upset.
    :vartype is_upset: bool

    :ivar awarded_points: Cached scoring for this pick. Optional—can be computed
                          by your scoring logic. Defaults to ``0``.
    :vartype awarded_points: int
    :ivar is_win: Whether this pick ultimately won. Defaults to ``False``.
    :vartype is_win: bool

    Relationships
    -------------
    - ``player`` (:class:`Player`): Back-populates ``Player.game_picks``.
    - ``game`` (:class:`Game`): The referenced game (lazy-loaded by default).
    - ``picked_team`` (:class:`Team`): Convenience relationship to the picked team (view-only).

    Constraints & Indexes
    ---------------------
    - ``uq_playergamepick_player_game``: unique ``(player_id, game_id)``.
    - ``uq_one_lock_per_week``: partial unique index over
      ``(player_id, season, week_no)`` where ``is_lock = true`` to restrict one lock per week.

    Notes
    -----
    - Keep ``season`` and ``week_no`` consistent with the referenced ``game``—set them
      explicitly when creating picks (e.g., from ``Game.season`` / ``Game.week_no``).
    - If lazy-loading causes unwanted autoflush during validation/queries, consider
      using ``session.no_autoflush`` for read-only paths.
    """

    __table_args__ = (
        sa.UniqueConstraint(
            "player_id", "game_id", name="uq_playergamepick_player_game"
        ),
        sa.Index(
            "uq_one_lock_per_week",
            "player_id",
            "season",
            "week_no",
            unique=True,
            postgresql_where=sa.text("is_lock = true"),
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)

    player_id: int = Field(foreign_key="player.id", index=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    picked_team_id: int = Field(foreign_key="team.id", index=True)

    # denormalized for constraints/queries
    season: int = Field(index=True)
    week_no: int = Field(index=True)

    # game-time choices
    is_lock: bool = False
    is_upset: bool = False

    @property
    def is_win(self) -> bool:
        if self.game.winning_team and self.game.winning_team.id == self.picked_team_id:
            return True
        return False

    @property
    def is_loss(self) -> bool:
        if self.game.winning_team and self.game.winning_team.id != self.picked_team_id:
            return True
        return False

    @property
    def bonus_points(self) -> int:
        bonus_points = 0
        if self.is_win and self.is_lock:
            bonus_points += 1
        if self.is_win and self.is_upset:
            bonus_points += 1
        if self.is_loss and self.is_lock:
            bonus_points -= 1
        return bonus_points

    player: "Player" = Relationship(back_populates="game_picks")
    game: "Game" = Relationship()
    picked_team: "Team" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "PlayerGamePick.picked_team_id==Team.id",
            "viewonly": True,
        }
    )
