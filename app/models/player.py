from typing import Optional, List, TYPE_CHECKING
import sqlalchemy as sa
from sqlmodel import Field, Relationship, Session, select

from .base import TGFPModelBase
from .model_helpers import current_nfl_season

if TYPE_CHECKING:
    from .player_game_pick import PlayerGamePick
    from .player_award import PlayerAward


class Player(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str = Field(index=True, unique=True, description="player's email address")
    discord_id: int = Field(sa_type=sa.BigInteger, nullable=False)

    game_picks: List["PlayerGamePick"] = Relationship(back_populates="player")
    player_awards: List["PlayerAward"] = Relationship(back_populates="player")

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    def picks(
        self, all_seasons: bool = False, season: int = None, week_no: int = None
    ) -> List["PlayerGamePick"]:
        """
        This is a wrapper that sets reasonable defaults for searching picks

        - empty parameters defaults to current season, all weeks
        - If season is specified with no week, then all picks for that season are returned
        - If week is specified with no season then current season specific week is returned
        - NOTE: all_seasons = True overrides and returns all picks
        """
        if all_seasons:
            return self._find_picks()

        search_season: int = season if season else current_nfl_season()
        return self._find_picks(
            season=search_season,
            week_no=week_no,
        )

    def _find_picks(
        self,
        season: int = None,
        week_no: int = None,
    ) -> List["PlayerGamePick"]:
        """
        Returns a list of picks can be filtered by season and week_no
        """
        sess: Session = self.current_session
        from .player_game_pick import PlayerGamePick

        cache_key: str = f"player_game_pick_p{self.id}_s{season}_w{week_no}"
        if sess.info.get(cache_key):
            return sess.info.get(cache_key)

        statement = select(PlayerGamePick).where(PlayerGamePick.player_id == self.id)
        if season:
            statement = statement.where(PlayerGamePick.season == season)
        if week_no:
            statement = statement.where(PlayerGamePick.week_no == week_no)
        picks = list(sess.exec(statement).all())
        sess.info[cache_key] = picks
        return picks

    def pick_for_game_id(self, game_id: int) -> "PlayerGamePick":
        from .player_game_pick import PlayerGamePick

        # Search cached picks first (across all cached weeks)
        session: Session = self.current_session
        statement = (
            select(PlayerGamePick)
            .where(PlayerGamePick.player_id == self.id)
            .where(PlayerGamePick.game_id == game_id)
        )
        return session.exec(statement).one()

    @staticmethod
    def _record_from_picks(picks: List["PlayerGamePick"]) -> dict:
        """
        :param picks:
        :type picks:
        :return: {'wins', 'losses', 'bonus'}
        :rtype: dict
        """
        l_wins = 0
        l_losses = 0
        l_bonus = 0
        for pick in picks:
            l_wins += 1 if pick.is_win else 0
            l_losses += 1 if pick.is_loss else 0
            l_bonus += pick.bonus_points
        return {
            "wins": l_wins,
            "losses": l_losses,
            "bonus": l_bonus,
        }

    def wins(self, all_seasons: bool = False, season: int = None, week_no: int = None):
        record = self._record_from_picks(self.picks(all_seasons, season, week_no))
        return record["wins"]

    def losses(
        self, all_seasons: bool = False, season: int = None, week_no: int = None
    ):
        record = self._record_from_picks(self.picks(all_seasons, season, week_no))
        return record["losses"]

    def bonus(self, all_seasons: bool = False, season: int = None, week_no: int = None):
        record = self._record_from_picks(self.picks(all_seasons, season, week_no))
        return record["bonus"]

    @property
    def total_points(self, all_seasons: bool = False, week_no=None, season=None) -> int:
        """
        Returns the number of total
        for the season if `week_no` is not specified.
        :return: :class:`int` - total number of points (wins + bonus)
         optionally for a single week, or all weeks
        """
        return self.wins(
            all_seasons=all_seasons, week_no=week_no, season=season
        ) + self.bonus(all_seasons=all_seasons, week_no=week_no, season=season)

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
    def by_discord_id(session: Session, discord_id: int) -> Optional["Player"]:
        """Returns a player by their discord ID"""
        statement = select(Player).where(Player.discord_id == discord_id).limit(1)
        result = session.exec(statement)
        player: Optional[Player] = result.first()
        return player
