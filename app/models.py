""" All models for the great football pool """
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie, PydanticObjectId
from pydantic import BaseModel


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
    """ Game model """
    game_status: str
    favorite_team_id: PydanticObjectId
    road_team_id: PydanticObjectId
    home_team_id: PydanticObjectId
    spread: float
    start_time: datetime
    week_no: int
    road_team_score: int
    home_team_score: int
    season: int
    tgfp_nfl_game_id: str

    # pylint: disable=too-few-public-methods
    class Settings:
        """ The settings class """
        name = "games"


class PickDetail(BaseModel):
    """ PickDetail model """
    game_id: PydanticObjectId
    winner_id: PydanticObjectId


class Pick(Document):
    """ Pick model """
    player_id: PydanticObjectId
    week_no: int
    lock_team_id: PydanticObjectId
    upset_team_id: PydanticObjectId
    bonus: int
    wins: int
    losses: int
    season: int
    pick_detail: List[PickDetail]

    # pylint: disable=too-few-public-methods
    class Settings:
        """ The settings class """
        name = "picks"


async def init():
    """ Create the client connection"""
    client = AsyncIOMotorClient("mongodb://tgfp:development@localhost:27017/")

    await init_beanie(database=client.tgfp, document_models=[Player, Team, Pick, Game])
