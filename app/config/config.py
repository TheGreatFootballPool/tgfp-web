""" Configuration file """
import os
from dataclasses import dataclass
from dotenv import load_dotenv


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
@dataclass
class Config:
    """ Base configuration class """
    # pylint: disable=invalid-name
    ENVIRONMENT: str
    MONGO_URI: str
    WEB_SECRET_KEY: str
    API_BASE_URL: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    DISCORD_GUILD_ID: str
    DISCORD_AUTH_TOKEN: str
    DISCORD_NAG_BOT_CHANNEL_ID: str
    DISCORD_NAG_BOT_WEBHOOK_URL: str
    KESTRA_NAMESPACE: str
    KESTRA_HOST: str
    SESSION_SECRET_KEY: str
    SENTRY_DSN: str
    APP_VERSION: str

    @classmethod
    def get_config(cls):
        """ Factory method for returning the correct config"""
        load_dotenv()
        config = cls(
            ENVIRONMENT=os.getenv('ENVIRONMENT'),
            MONGO_URI=os.getenv('MONGO_URI'),
            WEB_SECRET_KEY=os.getenv('WEB_SECRET_KEY'),
            API_BASE_URL=os.getenv('API_BASE_URL'),
            DISCORD_CLIENT_ID=os.getenv('DISCORD_CLIENT_ID'),
            DISCORD_GUILD_ID=os.getenv('DISCORD_GUILD_ID'),
            DISCORD_CLIENT_SECRET=os.getenv('DISCORD_CLIENT_SECRET'),
            DISCORD_REDIRECT_URI=os.getenv('DISCORD_REDIRECT_URI'),
            DISCORD_AUTH_TOKEN=os.getenv('DISCORD_AUTH_TOKEN'),
            DISCORD_NAG_BOT_CHANNEL_ID=os.getenv('DISCORD_NAG_BOT_CHANNEL_ID'),
            DISCORD_NAG_BOT_WEBHOOK_URL=os.getenv('DISCORD_NAG_BOT_WEBHOOK_URL'),
            SESSION_SECRET_KEY=os.getenv('SESSION_SECRET_KEY'),
            KESTRA_NAMESPACE=os.getenv('KESTRA_NAMESPACE'),
            KESTRA_HOST=os.getenv('KESTRA_HOST'),
            SENTRY_DSN=os.getenv('SENTRY_DSN'),
            APP_VERSION=os.getenv('APP_VERSION')
        )
        return config
