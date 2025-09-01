from typing import Optional, List, TYPE_CHECKING, Dict, Tuple
import sqlalchemy as sa
from sqlmodel import Field, Relationship, Session, select
from sqlalchemy import event
from pydantic import PrivateAttr

from .base import TGFPModelBase
from .model_helpers import TGFPInfo

if TYPE_CHECKING:
    from .player_game_pick import PlayerGamePick


class Player(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str = Field(index=True, unique=True, description="player's email address")
    discord_id: int = Field(sa_type=sa.BigInteger, nullable=False)

    game_picks: List["PlayerGamePick"] = Relationship(back_populates="player")

    _picks_for_week: Dict[Tuple[int, int], List] = PrivateAttr(default_factory=dict)

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def tgfp_info(self) -> TGFPInfo:
        return self.current_session.info["TGFPInfo"]

    def picks_for_week(
        self, season: int = None, week_no: int = None
    ) -> List["PlayerGamePick"]:
        """Gets the picks for the season/week_no or the
        current week/season by default, with per-(season, week) caching."""
        search_week: int = week_no if week_no else self.tgfp_info.current_week
        search_season: int = season if season else self.tgfp_info.current_season
        key: Tuple[int, int] = (search_season, search_week)
        from .player_game_pick import PlayerGamePick

        # Return from cache if present
        cached = self._picks_for_week.get(key)
        if cached is not None:
            return cached

        # Query and cache
        sess: Session = self.current_session
        statement = (
            select(PlayerGamePick)
            .where(PlayerGamePick.player_id == self.id)
            .where(PlayerGamePick.season == search_season)
            .where(PlayerGamePick.week_no == search_week)
        )
        picks = list(sess.exec(statement).all())
        self._picks_for_week[key] = picks
        return picks

    def pick_for_game_id(self, game_id: int) -> "PlayerGamePick":
        from .player_game_pick import PlayerGamePick

        # Search cached picks first (across all cached weeks)
        for picks in self._picks_for_week.values():
            for pick in picks:
                if pick.game_id == game_id:
                    return pick
        session: Session = self.current_session
        statement = select(PlayerGamePick).where(PlayerGamePick.game_id == game_id)
        return session.exec(statement).one()

    def wins(self, week_no=None, season=None) -> int:
        """return the number of wins optionally for a single week, or through week_no"""
        local_wins = 0
        pick: PlayerGamePick
        for pick in self.picks_for_week(season=season, week_no=week_no):
            local_wins += 1 if pick.is_win else 0
        return local_wins

    def losses(self, week_no=None, season=None) -> int:
        """return the number of wins optionally for a single week, or through week_no"""
        local_losses = 0
        pick: PlayerGamePick
        for pick in self.picks_for_week(season=season, week_no=week_no):
            local_losses += 1 if pick.is_win is False else 0
        return local_losses

    def bonus(self, week_no=None, season=None) -> int:
        """return the number of wins optionally for a single week, or through week_no"""
        local_bonus = 0
        pick: PlayerGamePick
        for pick in self.picks_for_week(season=season, week_no=week_no):
            local_bonus += 1 if pick.is_win and (pick.is_lock or pick.is_upset) else 0
        return local_bonus

    @property
    def total_points(self) -> int:
        """
        Returns the number of total
        for the season if `week_no` is not specified.
        :return: :class:`int` - total number of points (wins + bonus)
         optionally for a single week, or all weeks
        """
        return self.wins() + self.bonus()

    @property
    def winning_pct(self) -> float:
        """
        Winning percentage for the current season
        :return: :class:`float`
        """
        wins_and_losses = float(self.wins() + self.losses())
        if wins_and_losses:
            return self.wins() / wins_and_losses

        return 0

    @staticmethod
    def active_players(session: Session) -> List["Player"]:
        """returns a list of active players"""
        statement = select(Player).where(Player.active)
        return list(session.exec(statement).all())

    @staticmethod
    def player_by_discord_id(session: Session, discord_id: int) -> Optional["Player"]:
        """Returns a player by their discord ID"""
        statement = select(Player).where(Player.discord_id == discord_id).limit(1)
        result = session.exec(statement)
        player: Optional[Player] = result.first()
        return player


@event.listens_for(Player, "load")
def _ensure_private_attrs_on_load(target: Player, _context):
    # Ensure the private storage exists
    priv = getattr(target, "__pydantic_private__", None)
    if priv is None:
        # Avoid Pydantic interception; set the attribute directly
        object.__setattr__(target, "__pydantic_private__", {})
        priv = target.__pydantic_private__

    # Initialize the private cache if missing/None, without touching getattr/hasattr
    if priv.get("_picks_for_week") is None:
        priv["_picks_for_week"] = {}
