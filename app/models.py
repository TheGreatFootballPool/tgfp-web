""" All models for the great football pool """
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie, Link


# pylint: disable=too-many-ancestors
class Player(Document):
    """ Player model """
    first_name: str
    last_name: str
    nick_name: str
    active: bool
    email: str
    discord_id: int

    # pylint: disable=too-few-public-methods
    class Settings:
        """ The settings class """
        name = "players"

    @property
    def full_name(self):
        """ Returns player's full name """
        return self.first_name + ' ' + self.last_name


class Team(Document):
    """ Team model """
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

    # pylint: disable=too-few-public-methods
    class Settings:
        """ The settings class """
        name = "teams"


class Game(Document):
    """ Game model class"""
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

    # pylint: disable=too-few-public-methods

    @property
    def is_final(self):
        """ Returns true if the game is final """
        return self.game_status == 'STATUS_FINAL'

    class Settings:
        """ The settings class """
        name = "games"


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

    # pylint: disable=too-few-public-methods
    class Settings:
        """ The settings class """
        name = "picks"


async def db_init(models=None):
    """ Create the client connection"""
    if models is None:
        models = [Pick, PickDetail, Game, Team, Player]
    client = AsyncIOMotorClient("mongodb://tgfp:development@localhost:27017/")

    await init_beanie(database=client.tgfp, document_models=models)
