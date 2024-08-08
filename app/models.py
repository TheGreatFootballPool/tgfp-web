""" All models for the great football pool """

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie


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


async def init():
    """ Create the client connection"""
    client = AsyncIOMotorClient("mongodb://tgfp:development@localhost:27017/")

    await init_beanie(database=client.tgfp, document_models=[Player])
