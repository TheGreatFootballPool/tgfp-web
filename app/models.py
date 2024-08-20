""" All models for the great football pool """
from __future__ import annotations

from datetime import datetime
from typing import List, Final
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie, Link
from pydantic import BaseModel

PRO_BOWL_WEEK: Final[int] = 22

# pylint: disable=too-many-ancestors
# pylint: disable=too-few-public-methods


class TGFPInfo(BaseModel):
    """
    It's required to have a DB init called already to use this class
    :attributes:

    - :class:`int` season --> The current season (YYYY)
    - :class:`int` display_week --> This is the more comment week used.
    - :class:`int` active_week --> Used for last_wins, last_losses etc.
    """
    season: int
    display_week: int
    active_week: int


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


class PickDetail(Document):
    """ PickDetail model """
    game: Link[Game]
    winning_team: Link[Team]


class Pick(Document):
    """ Pick model """
    player: Link[Player]
    week_no: int
    lock_team: Link[Team]
    upset_team: Link[Team]
    bonus: int
    wins: int
    losses: int
    season: int
    pick_detail: List[PickDetail]

    class Settings:
        """ The settings class """
        name = "picks"


class PickHistory(Pick):
    """Model class for saving picks from previous seasons in a table"""
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


PickHistory.model_rebuild()
Player.model_rebuild()


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
        active_week=current_active_week,
    )


async def db_init(models=None):
    """ Create the client connection"""
    if models is None:
        models = [Pick, PickDetail, Game, Team, Player, PickHistory]
    client = AsyncIOMotorClient("mongodb://tgfp:development@localhost:27017/")

    await init_beanie(database=client.tgfp, document_models=models)
