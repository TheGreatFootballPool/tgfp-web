""" Configuration file """
import logging
import os

from prefect.blocks.system import Secret
from prefect import variables, get_run_logger


# pylint: disable=missing-class-docstring
class InvalidEnvironment(Exception):
    pass


# pylint: disable=too-few-public-methods
def get_logger():
    """ Return the common logger """
    return get_run_logger()


class Config:
    """ Base configuration class """
    ENV: str = os.getenv('ENVIRONMENT')
    s: Secret = Secret.load(f'mongo-uri-{ENV}')
    MONGO_URI = s.get()
    OAUTHLIB_INSECURE_TRANSPORT = int(variables.get(f'discord_oauthlib_insecure_transport_{ENV}'))
    s = Secret.load('discord-client-id')
    DISCORD_CLIENT_ID = s.get()
    s = Secret.load(f'discord-client-secret-{ENV}')
    DISCORD_CLIENT_SECRET = s.get()
    DISCORD_REDIRECT_URI = variables.get(f'discord_redirect_ui_{ENV}')
    s = Secret.load(f'web-secret-key-{ENV}')
    SECRET_KEY = s.get()


def get_config():
    """ Factory method for returning the correct config"""
    return Config()
