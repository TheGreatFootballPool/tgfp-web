""" Configuration file """
import os
from dataclasses import dataclass

from fastapi_discord import DiscordOAuthClient

from app.config.one_password_helpers import OnePasswordHelper


# pylint: disable=too-few-public-methods
@dataclass
class Config:
    """ Base configuration class """
    # pylint: disable=invalid-name
    ENVIRONMENT: str
    MONGO_URI: str
    SECRET_KEY: str
    DISCORD_CLIENT: DiscordOAuthClient

    @classmethod
    async def get_config(cls):
        """ Factory method for returning the correct config"""
        env: str = os.getenv('ENVIRONMENT')
        assert env is not None
        helper = OnePasswordHelper(env)
        mongo_uri: str = await helper.get_setting('mongo-uri')
        discord_client_id: str = await helper.get_setting('discord-client-id')
        discord_client_secret: str = await helper.get_setting('discord-client-secret')
        discord_redirect_uri: str = await helper.get_setting('discord-redirect-uri')
        secret_key: str = await helper.get_setting('web-secret-key')
        discord_client: DiscordOAuthClient = DiscordOAuthClient(
            discord_client_id,
            discord_client_secret,
            discord_redirect_uri,
            ("identify", "guilds", "email")
        )
        config = cls(
            ENVIRONMENT=env,
            MONGO_URI=mongo_uri,
            SECRET_KEY=secret_key,
            DISCORD_CLIENT=discord_client
        )
        return config
