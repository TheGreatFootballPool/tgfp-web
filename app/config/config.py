""" Configuration file """
import os
from dataclasses import dataclass

from app.config.one_password_helpers import OnePasswordHelper


# pylint: disable=too-few-public-methods
@dataclass
class Config:
    """ Base configuration class """
    # pylint: disable=invalid-name
    ENVIRONMENT: str
    MONGO_URI: str
    SECRET_KEY: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    SESSION_SECRET_KEY: str

    @classmethod
    async def get_config(cls):
        """ Factory method for returning the correct config"""
        env: str = os.getenv('ENVIRONMENT')
        assert env is not None
        helper = OnePasswordHelper(env)
        mongo_uri: str = await helper.get_setting('mongo-uri')
        secret_key: str = await helper.get_setting('web-secret-key')
        discord_client_id: str = await helper.get_setting('discord-client-id')
        discord_client_secret: str = await helper.get_setting('discord-client-secret')
        discord_redirect_uri: str = await helper.get_setting('discord-redirect-uri')
        session_secret_key: str = await helper.get_setting('session-secret-key')
        config = cls(
            ENVIRONMENT=env,
            MONGO_URI=mongo_uri,
            SECRET_KEY=secret_key,
            DISCORD_CLIENT_ID=discord_client_id,
            DISCORD_CLIENT_SECRET=discord_client_secret,
            DISCORD_REDIRECT_URI=discord_redirect_uri,
            SESSION_SECRET_KEY=session_secret_key
        )
        return config
