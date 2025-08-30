from contextlib import asynccontextmanager
from typing import Final, Optional

from fastapi import APIRouter, FastAPI, Request, status
from sqlmodel import Session, select
from starlette.responses import RedirectResponse
from starlette.datastructures import MutableHeaders
from fastapi_discord import DiscordOAuthClient, User

from app.config import Config
from db import engine
from models import Player

config = Config.get_config()
SECONDS_IN_A_DAY: Final[int] = 60 * 60 * 24
COOKIE_TIME_OUT = config.COOKIE_RETENTION_DAYS * SECONDS_IN_A_DAY

discord: DiscordOAuthClient = DiscordOAuthClient(
    config.DISCORD_CLIENT_ID, config.DISCORD_CLIENT_SECRET, config.DISCORD_REDIRECT_URI
)


@asynccontextmanager
async def auth_lifespan(_: FastAPI):
    await discord.init()
    yield


router = APIRouter(lifespan=auth_lifespan, prefix="/auth", tags=["auth"])


def get_player_by_discord_id(session: Session, discord_id: int) -> Optional[Player]:
    """Returns a player by their discord ID"""
    statement = select(Player).where(Player.discord_id == discord_id).limit(1)
    result = session.exec(statement)
    player: Optional[Player] = result.first()
    return player


@router.get("/discord_login")
async def discord_login():
    """Login url for discord"""
    return RedirectResponse(discord.oauth_login_url)


@router.get("/callback")
async def callback(code: str, request: Request):
    """Callback url for discord"""
    token, _ = await discord.get_access_token(code)
    new_header = MutableHeaders(request.headers)
    new_header["Authorization"] = f"Bearer {token}"
    request._headers = new_header
    request.scope.update(headers=request.headers.raw)
    user: User = await discord.user(request)
    with Session(engine) as session:
        player: Player = get_player_by_discord_id(session, int(user.id))
    if player:
        redirect_url = request.url_for("home")
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="tgfp-discord-id",
            value=user.id,
            max_age=COOKIE_TIME_OUT,
        )
    else:
        redirect_url = request.url_for("login")
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response
