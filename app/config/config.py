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
    BUGSINK_DSN: str
    COOKIE_RETENTION_DAYS: int
    DATABASE_URL: str
    DISCORD_AUTH_TOKEN: str
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
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    SESSION_SECRET_KEY: str
    WEB_SECRET_KEY: str
    UMAMI_TRACKING_ID: str

    @classmethod
    def get_config(cls):
        """Factory method for returning the correct config"""
        load_dotenv()
        new_config = cls(
            API_BASE_URL=os.getenv("API_BASE_URL"),
            APP_VERSION=os.getenv("APP_VERSION"),
            BUGSINK_DSN=os.getenv("BUGSINK_DSN"),
            COOKIE_RETENTION_DAYS=int(os.getenv("COOKIE_RETENTION_DAYS")),
            DATABASE_URL=os.getenv("DATABASE_URL"),
            DISCORD_AUTH_TOKEN=os.getenv("DISCORD_AUTH_TOKEN"),
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
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_PORT=int(os.getenv("MAIL_PORT")),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
            MAIL_STARTTLS=bool(os.getenv("MAIL_STARTTLS")),
            MAIL_SSL_TLS=False,
            SESSION_SECRET_KEY=os.getenv("SESSION_SECRET_KEY"),
            WEB_SECRET_KEY=os.getenv("WEB_SECRET_KEY"),
            UMAMI_TRACKING_ID=os.getenv("UMAMI_TRACKING_ID"),
        )
        return new_config
