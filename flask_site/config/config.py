""" Configuration file """
import os

from config.prefect_helpers import PrefectHelper


# pylint: disable=too-few-public-methods
class Config:
    """ Base configuration class """
    ENVIRONMENT: str = os.getenv('ENVIRONMENT')
    assert ENVIRONMENT is not None
    helper = PrefectHelper(ENVIRONMENT)

    MONGO_URI: str = helper.get_secret('mongo-uri')
    OAUTHLIB_INSECURE_TRANSPORT: str = helper.get_variable('discord_oauthlib_insecure_transport')
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = OAUTHLIB_INSECURE_TRANSPORT
    DISCORD_CLIENT_ID = helper.get_secret('discord-client-id')
    DISCORD_CLIENT_SECRET = helper.get_secret('discord-client-secret')
    DISCORD_REDIRECT_URI = helper.get_variable('discord_redirect_uri')
    SECRET_KEY = helper.get_secret('web-secret-key')


def get_config():
    """ Factory method for returning the correct config"""
    return Config()
