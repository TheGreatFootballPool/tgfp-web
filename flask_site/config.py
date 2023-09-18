""" Configuration file """
import os

from prefect import get_run_logger
from prefect_helpers import get_secret


# pylint: disable=missing-class-docstring
class InvalidEnvironment(Exception):
    pass


# pylint: disable=too-few-public-methods
def get_logger():
    """ Return the common logger """
    return get_run_logger()


class Config:
    """ Base configuration class """
    MONGO_URI: str = get_secret('mongo-uri')
    OAUTHLIB_INSECURE_TRANSPORT: str = get_secret(
        'discord_oauthlib_insecure_transport',
        is_var=True
    )
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = OAUTHLIB_INSECURE_TRANSPORT
    DISCORD_CLIENT_ID = get_secret('discord-client-id', use_env=False)
    DISCORD_CLIENT_SECRET = get_secret('discord-client-secret')
    DISCORD_REDIRECT_URI = get_secret('discord_redirect_ui', is_var=True)
    SECRET_KEY = get_secret('web-secret-key')


def get_config():
    """ Factory method for returning the correct config"""
    return Config()
