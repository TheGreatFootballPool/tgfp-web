""" All models for the great football pool """
from __future__ import annotations

from datetime import datetime
from typing import List, Final, Optional

import pytz
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie, Link
from pydantic import BaseModel

from config import Config

PRO_BOWL_WEEK: Final[int] = 22


# pylint: disable=too-many-ancestors
# pylint: disable=too-few-public-methods
class ApiKey(Document):
    """ Model for all API Keys """
    token: str
    description: str

    class Settings:
        """ The settings class """
        name = "api_keys"


class TGFPInfo(BaseModel):
    """
    It's required to have a DB init called already to use this class
    :attributes:

    - :class:`int` season --> The current season (YYYY)
    - :class:`int` display_week --> This is the more comment week used.
    - :class:`int` active_week --> Used for last_wins, last_losses etc.
    - :class:`str` app_version --> Debug information containing the app version
    - :class:`str` app_env --> Debug information containing the app environment
    """
    season: int = 2023
    display_week: int = 14
    active_week: int = 14
    app_version: str = "not_set"
    app_env: str = "not_set"


class Team(Document):
    """Team model"""
    city: str
    long_name: str
    losses: int
    short_name: str
    ties: int
    wins: int
    full_name: str
    logo_url: str
    tgfp_nfl_team_id: str
    discord_emoji: str

    class Settings:
        """ The settings class """
        name = "teams"


class Game(Document):
    """
    NFL Game model
    Attributes:

    - :class:`str` game_status
    - :class:`Team` favorite_team
    - :class:`Team` road_team
    - :class:`Team` home_team
    - :class:`float` spread
    - :class:`datetime` start_time
    - :class:`int` week_no
    - :class:`int` road_team_score
    - :class:`int` home_team_score
    - :class:`int` season
    - :class:`str` tgfp_nfl_game_id
    """
    game_status: str
    favorite_team: Link[Team]
    road_team: Link[Team]
    home_team: Link[Team]
    spread: float
    start_time: datetime
    week_no: int
    road_team_score: int
    home_team_score: int
    season: int
    tgfp_nfl_game_id: str

    class Settings:
        """ The settings class """
        name = "games"

    @property
    def is_final(self):
        """ Returns true if the game is final """
        return self.game_status == 'STATUS_FINAL'

    @property
    def is_pregame(self):
        """ Returns true if the game is pregame """
        return self.game_status == 'STATUS_SCHEDULED'

    @property
    def underdog_team(self) -> Link[Team]:
        """ Returns the underdog """
        if self.favorite_team == self.home_team:
            return self.road_team

        return self.home_team

    @property
    def pacific_start_time(self):
        """ Returns the start time in the US/Pacific timezone"""
        utc_dt = self.start_time.replace(tzinfo=pytz.utc)
        pac_dt = pytz.timezone('US/Pacific')
        return pac_dt.normalize(utc_dt.astimezone(pac_dt))

    @staticmethod
    async def get_first_game_of_the_week(info: TGFPInfo) -> Game:
        """ Returns the 'first' game of a week given the info  """
        games: List[Game] = await Game.find_many(
            Game.season == info.season, Game.week_no == info.display_week
        ).to_list()
        games.sort(key=lambda x: x.start_time, reverse=True)
        return games[-1]


class PickDetail(Document):
    """
    Pick Detail Model
    Attributes:

    - :class:`Link` [ :class:`Game` ] game
    - :class:`Link` [ :class:`Team` ] winning_team
    """
    game: Link[Game]
    winning_team: Link[Team]


class Pick(Document):
    """
    Player Pick Model
    Attributes:

    - :class:`int` week_no
    - :class:`int` season
    - :class:`Link` [ :class:`Team` ] lock_team
    - :class:`Optional` [ :class:`Link` [ :class:`Team` ]] upset_team
    - :class:`int` bonus = 0
    - :class:`int` wins = 0
    - :class:`int` losses = 0
    - :class:`List` [ :class:`PickDetail` ] pick_detail = []
    """
    created_at: Optional[datetime] = None
    week_no: int
    lock_team: Link[Team]
    upset_team: Optional[Link[Team]] = None
    bonus: int = 0
    wins: int = 0
    losses: int = 0
    season: int
    pick_detail: List[PickDetail] = []

    class Settings:
        """ The settings class """
        name = "picks"

    def winning_team_for_game(self, game: Game, teams: List[Team]) -> Optional[Team]:
        """
        Go through each game in the picks for the week, and
        when we have a match, return the winner for that game
        :param teams: Pre-fetched list of teams
        :param game:
        :return:
        """
        winning_team: Optional[Team] = None
        detail: PickDetail
        winning_team_id: Optional[ObjectId] = None
        for detail in self.pick_detail:
            if isinstance(detail.game, Link):
                if str(detail.game.ref.id) == str(game.id):
                    winning_team_id = detail.winning_team.ref.id
                    break
            else:
                raise Exception("Picks was 'fetched' and I expected it not to be!")
        if winning_team_id:
            for team in teams:
                if winning_team_id == team.id:
                    winning_team = team
                    break
        return winning_team

    def load_record(self):
        """
        This method goes through the current pick's games, determines the winner and
        updates the score of the week's pick object.
        """
        # go through each game in pick_detail
        self.wins = 0
        self.losses = 0
        self.bonus = 0

        detail: PickDetail
        for detail in self.pick_detail:
            # noinspection PyTypeChecker
            game: Game = detail.game
            if not game.is_final:
                continue
            if game.road_team_score == game.home_team_score:
                self.losses += 1
            else:
                if game.road_team_score > game.home_team_score:
                    winning_team = game.road_team
                    losing_team = game.home_team
                else:
                    winning_team = game.home_team
                    losing_team = game.road_team
                # noinspection PyTypeChecker
                self._update_wins(detail, winning_team)
                # noinspection PyTypeChecker
                self._update_bonus(winning_team, losing_team)

    def _update_wins(self, pick: PickDetail, winning_team: Team):
        if winning_team.id == pick.winning_team.id:
            self.wins += 1
        else:
            self.losses += 1

    def _update_bonus(self, winning_team: Team, losing_team: Team):
        if winning_team.id == self.lock_team.id:
            self.bonus += 1
        if losing_team.id == self.lock_team.id:
            self.bonus -= 1
        if self.upset_team is not None:
            if winning_team.id == self.upset_team.id:
                self.bonus += 1


class PickHistory(Pick):
    """Model class for saving picks from previous seasons in a table"""
    player: Link[Player]

    class Settings:
        """ The settings class """
        name = "picks_history"


class Player(Document):
    """
    Player and their picks
    Attributes:

    - :class:`str` first_name --> The first name of the player
    - :class:`str` last_name --> The last name of the player
    - :class:`str` nickname --> The nickname of the player
    - :class:`bool` active --> Flag indicating the player is currently active
    - :class:`str` email --> The email address of the player
    - :class:`int` discord_id --> The discord id of the player
    - :class:`Pick` picks[] --> The list of all picks for the current season
    """
    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str
    discord_id: int
    picks: List[Pick] = []

    class Settings:
        """ The settings class """
        name = "players"

    @property
    def full_name(self) -> str:
        """
        Full name of the player
        :returns: :class:`str` full_name - full name of the player (first + last)
        """
        return self.first_name + ' ' + self.last_name

    # noinspection DuplicatedCode
    def wins(self, week_no=None) -> int:
        """
        Returns the number of wins for the specified week, or total wins
        for the season if `week_no` is not specified.
        :param week_no: :class:`int`: the week number default is None
        :return: :class:`int`: total number of wins optionally for a single week, or all weeks
        """
        local_wins = 0
        pick: Pick
        for pick in self.picks:
            if week_no is None:
                local_wins += pick.wins
            elif pick.week_no == week_no:
                local_wins += pick.wins
        return local_wins

    def wins_through(self, week_no: int) -> int:
        """
        Return total wins for all weeks up to and including given week_no
        :param week_no:
        :return:
        """
        wins: int = 0
        pick: Pick
        for pick in self.picks:
            if pick.week_no <= week_no:
                wins += pick.wins
        return wins

    def losses(self, week_no: int = None) -> int:
        """
        Returns the number of losses for the specified week, or total losses
        for the season if `week_no` is not specified.
        :param week_no: :class:`int` the week number default is None
        :return: :class:`int` - total number of losses optionally for a single week, or all weeks
        """
        local_losses = 0
        pick: Pick
        for pick in self.picks:
            if not week_no or pick.week_no == week_no:
                local_losses += pick.losses
        return local_losses

    def losses_through(self, week_no: int) -> int:
        """
        Return total losses for all weeks up to and including given week_no
        :param week_no:
        :return:
        """
        losses: int = 0
        pick: Pick
        for pick in self.picks:
            if pick.week_no <= week_no:
                losses += pick.losses
        return losses

    # noinspection DuplicatedCode
    def bonus(self, week_no=None) -> int:
        """
        Returns the number of bonus points for the specified week, or total bonus
        for the season if `week_no` is not specified.
        :param week_no: :class:`int`: the week number default is None
        :return: :class:`int` - total number of bonus points
         optionally for a single week, or all weeks
        """
        local_bonus = 0
        pick: Pick
        for pick in self.picks:
            if week_no is None:
                local_bonus += pick.bonus
            elif week_no and pick.week_no == week_no:
                local_bonus += pick.bonus
        return local_bonus

    def bonus_through(self, week_no: int) -> int:
        """
        Return total bonus points for all weeks up to and including given week_no
        :param week_no:
        :return:
        """
        bonus: int = 0
        pick: Pick
        for pick in self.picks:
            if pick.week_no <= week_no:
                bonus += pick.bonus
        return bonus

    @property
    def total_points(self) -> int:
        """
        Returns the number of total
        for the season if `week_no` is not specified.
        :return: :class:`int` - total number of points (wins + bonus)
         optionally for a single week, or all weeks
        """
        return self.wins() + self.bonus()

    def total_points_through(self, week_no: int) -> int:
        """
        Returns the number of total for the season if `through_week_no` is not specified.
        If the through_week_no is specified then total points through the given week
        :return: :class:`int` - total number of points (wins + bonus)
         optionally for a single week, or all weeks
        """
        return self.wins_through(week_no) + self.bonus_through(week_no)

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

    @property
    async def get_standings(self) -> int:
        """ Returns the 'place' the player is (optionally for a given week) """
        active_players: List[Player] = await Player.active_players()
        player_count: int = 1
        for player in active_players:
            if self.total_points < player.total_points:
                player_count += 1
        return player_count

    async def get_standings_through(self, week_no: int) -> int:
        """ Returns the 'place' the player is (optionally for a given week) """
        active_players: List[Player] = await Player.active_players()
        # start out in first place
        player_count: int = 1
        for player in active_players:
            if self.total_points_through(week_no) < player.total_points_through(week_no):
                player_count += 1
        return player_count

    async def games_back(self) -> int:
        """ Returns the number of games behind """
        players: List[Player] = await Player.active_players()
        players.sort(key=lambda x: x.total_points, reverse=True)
        return players[0].total_points - self.total_points

    def pick_for_week(self, week_no: int) -> Optional[Pick]:
        """
        Returns the picks for the given week
        :param week_no:
        :return:
        """
        pick: Optional[Pick] = None
        for a_pick in self.picks:
            if a_pick.week_no is week_no:
                pick = a_pick
                break
        return pick

    async def fetch_pick_links(self, week_no: Optional[int] = None):
        """ Fetches all links for the pick for the week given """
        for pick in self.picks:
            if week_no is None or pick.week_no == week_no:
                await pick.fetch_all_links()
                detail: PickDetail
                for detail in pick.pick_detail:
                    await detail.fetch_all_links()

    @staticmethod
    async def active_players(fetch_links: bool = False) -> List[Player]:
        """ returns a list of active players """
        # pylint: disable=singleton-comparison
        return await Player.find_many(
            Player.active == True,  # noqa E712
            fetch_links=fetch_links
        ).to_list()


PickHistory.model_rebuild()
Player.model_rebuild()


# Helper methods
async def get_tgfp_info() -> TGFPInfo:
    """ Returns the TGFPInfo object filled w/values """
    # Get the current season.
    # NOTE: The current season is the year in which the season starts.
    #  -- if the month Jan - May (1-5) then consider the year before the starting
    #  season.
    year = datetime.now().year
    month = datetime.now().month
    if month < 6:
        year -= 1
    current_season: int = year

    # get display_week and current_active_week
    a_game: Game = await Game.find(
        {'season': current_season}
    ).sort("-_id").limit(1).first_or_none()
    if a_game is None:
        # EARLY RETURN
        return TGFPInfo(
            season=current_season,
            display_week=1,
            active_week=1
        )
    last_weeks_games: List[Game] = await Game.find({
        'season': a_game.season,
        'week_no': a_game.week_no
    }).to_list()

    all_complete = True
    any_complete = False
    for g in last_weeks_games:
        if not g.is_final:
            all_complete = False
        else:
            any_complete = True
    pro_bowl_adjustment: int = 1 if a_game.week_no == PRO_BOWL_WEEK else 0
    if all_complete:
        display_week = a_game.week_no + 1 + pro_bowl_adjustment
    else:
        display_week = a_game.week_no + pro_bowl_adjustment
    if any_complete:
        current_active_week = a_game.week_no
    else:
        current_active_week = a_game.week_no
    return TGFPInfo(
        season=current_season,
        display_week=display_week,
        active_week=current_active_week
    )


async def db_init(config: Config, models=None):
    """ Create the client connection"""
    if models is None:
        models = [Pick, PickDetail, Game, Team, Player, PickHistory, ApiKey]
    client = AsyncIOMotorClient(config.MONGO_URI)

    await init_beanie(database=client.tgfp, document_models=models)
