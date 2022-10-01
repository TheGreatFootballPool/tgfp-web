""" Configuration file """
from logging.handlers import RotatingFileHandler
import logging
import os


# pylint: disable=missing-class-docstring
class InvalidEnvironment(Exception):
    pass


# pylint: disable=too-few-public-methods
class Config:
    """ Base configuration class """
    #  Discord config variables
    DISCORD_ADMIN_EMAIL = os.getenv("DISCORD_ADMIN_EMAIL")
    DISCORD_BOT_CHANNEL_ID = os.getenv("DISCORD_BOT_CHANNEL_ID")
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_GUILD = os.getenv("DISCORD_GUILD")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    DISCORD_WEBHOOK_BOT_ID = os.getenv("DISCORD_WEBHOOK_BOT_ID")
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv("OAUTHLIB_INSECURE_TRANSPORT")

    LOGIN_URL = os.getenv("LOGIN_URL")
    LOG_LEVEL = os.getenv("LOG_LEVEL")

    #  Mongo variables
    MONGODUMP_BIN = os.getenv("MONGODUMP_BIN")
    MONGO_BACKUP_FOLDER = os.getenv("MONGO_BACKUP_FOLDER")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SENTRY_DSN_TGFP_WEB = os.getenv("SENTRY_DSN_TGFP_WEB")
    TGFP_WEB_CHECK_URL = os.getenv("TGFP_WEB_CHECK_URL")

    DOPPLER_ENVIRONMENT = os.getenv("DOPPLER_ENVIRONMENT")

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
