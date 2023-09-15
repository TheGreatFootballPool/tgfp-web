""" Configuration file """
from logging.handlers import RotatingFileHandler
import logging
import os

from prefect.blocks.system import Secret


# pylint: disable=missing-class-docstring
class InvalidEnvironment(Exception):
    pass


# pylint: disable=too-few-public-methods
class Config:
    """ Base configuration class """
    ENV: str = os.getenv('ENVIRONMENT')
    MONGO_URI = Secret.load(f'mongo-uri-{ENV}')

    #  Discord config variables
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv("OAUTHLIB_INSECURE_TRANSPORT")

    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

    LOG_LEVEL = os.getenv("LOG_LEVEL")

    SECRET_KEY = os.getenv("SECRET_KEY")

    def logger(self, name: str) -> logging.Logger:
        """ Return the common logger """
        logger: logging.Logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.LOG_LEVEL))
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/logs'
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        file_path += '/tgfp_logfile.log'
        handler = RotatingFileHandler(file_path, maxBytes=1000000, backupCount=10)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def get_config():
    """ Factory method for returning the correct config"""
    return Config()
