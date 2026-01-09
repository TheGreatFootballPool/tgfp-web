from typing import Optional, List, TYPE_CHECKING
import sqlalchemy as sa
from sqlmodel import Field, Relationship, Session, select

from .base import TGFPModelBase
from .model_helpers import WeekInfo

if TYPE_CHECKING:
    from .player_game_pick import PlayerGamePick
    from .player_award import PlayerAward


class Player(TGFPModelBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str
    nick_name: str
    active: bool
    wins: int
    losses: int
    bonus: int
    email: str = Field(index=True, unique=True, description="player's email address")
    discord_id: int = Field(sa_type=sa.BigInteger, nullable=False)

    game_picks: List["PlayerGamePick"] = Relationship(back_populates="player")
    player_awards: List["PlayerAward"] = Relationship(back_populates="player")

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def total_points(self):
        return self.wins + self.bonus

    def picks_for_week(self, week_info: WeekInfo) -> List["PlayerGamePick"]:
        sess: Session = self.current_session
        from .player_game_pick import PlayerGamePick

        cache_key: str = f"player_{self.id}:{week_info.cache_key}"
        if sess.info.get(cache_key):
            return sess.info.get(cache_key)

        statement = select(PlayerGamePick).where(PlayerGamePick.player_id == self.id)
        statement = statement.where(PlayerGamePick.season == week_info.season)
        statement = statement.where(PlayerGamePick.season_type == week_info.season_type)
        statement = statement.where(PlayerGamePick.week_no == week_info.week_no)
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

    def wins_for_week(self, week_info: WeekInfo):
        record = self._record_from_picks(self.picks_for_week(week_info=week_info))
        return record["wins"]

    def losses_for_week(self, week_info: WeekInfo):
        record = self._record_from_picks(self.picks_for_week(week_info=week_info))
        return record["losses"]

    def bonus_for_week(self, week_info: WeekInfo):
        record = self._record_from_picks(self.picks_for_week(week_info=week_info))
        return record["bonus"]

    def total_points_for_week(self, week_info: WeekInfo) -> int:
        """
        Returns the number of total
        for the season if `week_no` is not specified.
        :return: :class:`int` - total number of points (wins + bonus)
         optionally for a single week, or all weeks
        """
        wins = self.wins_for_week(week_info=week_info)
        bonus = self.bonus_for_week(week_info=week_info)
        return wins + bonus

    @property
    def winning_pct(self) -> float:
        """
        Winning percentage for the current season
        :return: :class:`float`
        """
        wins_and_losses = float(self.wins + self.losses)
        if wins_and_losses:
            return self.wins / wins_and_losses

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

    def awards_for_week(self, week_info: WeekInfo):
        filtered_awards: list[PlayerAward] = []
        award: PlayerAward
        for award in self.player_awards:
            if (
                award.season == week_info.season
                and award.week_no == week_info.week_no
                and award.season_type == week_info.season_type
            ):
                filtered_awards.append(award)
        return filtered_awards
