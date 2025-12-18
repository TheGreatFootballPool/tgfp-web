"""Configuration file"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
@dataclass
class Config:
    """Base configuration class"""

    # pylint: disable=invalid-name

    # Non-Secrets
    # Secrets (I keep these in 1Password)
    API_BASE_URL: str
    APP_VERSION: str
    COOKIE_RETENTION_DAYS: int
    DATABASE_URL: str
    DISCORD_AUTH_TOKEN: str
    DISCORD_AWARD_BOT_WEBHOOK_URL: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_GUILD_ID: str
    DISCORD_NAG_BOT_CHANNEL_ID: str
    DISCORD_NAG_BOT_WEBHOOK_URL: str
    DISCORD_REDIRECT_URI: str
    ENVIRONMENT: str
    KESTRA_HOST: str
    KESTRA_NAMESPACE: str
    LISTMONK_API_URL: str
    LISTMONK_AUTH_HASH: str
    LISTMONK_LIST_ID: str
    LOG_LEVEL: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_PASSWORD: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_SSL_TLS: bool
    MAIL_STARTTLS: bool
    MAIL_USERNAME: str
    SENTRY_DSN: str
    SEQ_API_KEY: str
    SEQ_SERVER_URL: str
    SESSION_SECRET_KEY: str
    UMAMI_TRACKING_ID: str
    WEB_SECRET_KEY: str

    @classmethod
    def get_config(cls):
        """Factory method for returning the correct config"""
        load_dotenv()
        new_config = cls(
            API_BASE_URL=os.getenv("API_BASE_URL"),
            APP_VERSION=os.getenv("APP_VERSION"),
            COOKIE_RETENTION_DAYS=int(os.getenv("COOKIE_RETENTION_DAYS")),
            DATABASE_URL=os.getenv("DATABASE_URL"),
            DISCORD_AUTH_TOKEN=os.getenv("DISCORD_AUTH_TOKEN"),
            DISCORD_AWARD_BOT_WEBHOOK_URL=os.getenv("DISCORD_AWARD_BOT_WEBHOOK_URL"),
            DISCORD_CLIENT_ID=os.getenv("DISCORD_CLIENT_ID"),
            DISCORD_CLIENT_SECRET=os.getenv("DISCORD_CLIENT_SECRET"),
            DISCORD_GUILD_ID=os.getenv("DISCORD_GUILD_ID"),
            DISCORD_NAG_BOT_CHANNEL_ID=os.getenv("DISCORD_NAG_BOT_CHANNEL_ID"),
            DISCORD_NAG_BOT_WEBHOOK_URL=os.getenv("DISCORD_NAG_BOT_WEBHOOK_URL"),
            DISCORD_REDIRECT_URI=os.getenv("DISCORD_REDIRECT_URI"),
            ENVIRONMENT=os.getenv("ENVIRONMENT"),
            KESTRA_HOST=os.getenv("KESTRA_HOST"),
            KESTRA_NAMESPACE=os.getenv("KESTRA_NAMESPACE"),
            LISTMONK_API_URL=os.getenv("LISTMONK_API_URL"),
            LISTMONK_AUTH_HASH=os.getenv("LISTMONK_AUTH_HASH"),
            LISTMONK_LIST_ID=os.getenv("LISTMONK_LIST_ID"),
            LOG_LEVEL=os.getenv("LOG_LEVEL"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_PORT=int(os.getenv("MAIL_PORT")),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_SSL_TLS=False,
            MAIL_STARTTLS=bool(os.getenv("MAIL_STARTTLS")),
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            SENTRY_DSN=os.getenv("SENTRY_DSN"),
            SEQ_API_KEY=os.getenv("SEQ_API_KEY"),
            SEQ_SERVER_URL=os.getenv("SEQ_SERVER_URL"),
            SESSION_SECRET_KEY=os.getenv("SESSION_SECRET_KEY"),
            UMAMI_TRACKING_ID=os.getenv("UMAMI_TRACKING_ID"),
            WEB_SECRET_KEY=os.getenv("WEB_SECRET_KEY"),
        )
        return new_config
