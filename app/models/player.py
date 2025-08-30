from typing import Optional, List, TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy.orm.session import object_session
from sqlmodel import Field, Relationship, Session, select

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
    email: str
    discord_id: int = Field(sa_type=sa.BigInteger, nullable=False)

    game_picks: List["PlayerGamePick"] = Relationship(back_populates="player")

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def current_session(self) -> Session:
        sess: Session = object_session(self)
        if sess is None:
            raise RuntimeError("This Player isn't attached to a Session!")
        return sess

    @property
    def tgfp_info(self) -> TGFPInfo:
        return self.current_session.info["TGFPInfo"]

    def picks_for_week(
        self, season: int = None, week_no: int = None
    ) -> List["PlayerGamePick"]:
        """Gets the picks for the season / week_no or the current week / season default"""
        search_week: int = week_no if week_no else self.tgfp_info.current_week
        search_season: int = season if season else self.tgfp_info.current_season
        from .player_game_pick import PlayerGamePick

        sess: Session = self.current_session
        statement = (
            select(PlayerGamePick)
            .where(PlayerGamePick.player_id == self.id)
            .where(PlayerGamePick.season == search_season)
            .where(PlayerGamePick.week_no == search_week)
        )

        picks = list(sess.exec(statement).all())
        return picks

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
