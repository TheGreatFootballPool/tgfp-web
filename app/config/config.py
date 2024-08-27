""" Configuration file """
import os
from dataclasses import dataclass
from dotenv import load_dotenv


# pylint: disable=too-few-public-methods
@dataclass
class Config:
    """ Base configuration class """
    # pylint: disable=invalid-name
    ENVIRONMENT: str
    MONGO_URI: str
    WEB_SECRET_KEY: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    SESSION_SECRET_KEY: str
    SENTRY_DSN: str

    @classmethod
    def get_config(cls):
        """ Factory method for returning the correct config"""
        load_dotenv()
        config = cls(
            ENVIRONMENT=os.getenv('ENVIRONMENT'),
            MONGO_URI=os.getenv('MONGO_URI'),
            WEB_SECRET_KEY=os.getenv('WEB_SECRET_KEY'),
            DISCORD_CLIENT_ID=os.getenv('DISCORD_CLIENT_ID'),
            DISCORD_CLIENT_SECRET=os.getenv('DISCORD_CLIENT_SECRET'),
            DISCORD_REDIRECT_URI=os.getenv('DISCORD_REDIRECT_URI'),
            SESSION_SECRET_KEY=os.getenv('SESSION_SECRET_KEY'),
            SENTRY_DSN=os.getenv('SENTRY_DSN')
        )
        return config
