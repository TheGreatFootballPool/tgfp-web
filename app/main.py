"""Main entry point for website"""

import os
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from models.model_helpers import TGFPInfo, get_tgfp_info
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException

# TODO: Re-enable the middleware
# from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlmodel import Session
from db import engine
from models import Player


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Perform all app initialization before 'yield'"""
    # TODO: enable this
    # await discord.init()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
# noinspection PyTypeChecker
# TODO: Re-enable the middleware

# app.add_middleware(
#     SessionMiddleware, secret_key=config.SESSION_SECRET_KEY, max_age=None
# )
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# noinspection PyTypeChecker
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


def get_session():
    with Session(engine) as session:
        yield session


async def get_latest_info():
    # TODO: Finish porting this
    """Returns the current TGFPInfo object"""
    info = await get_tgfp_info()
    info.app_version = "unset"  # TODO: config.APP_VERSION
    info.app_env = "development"  # TODO: config.ENVIRONMENT
    return info


SessionDep = Annotated[Session, Depends(get_session)]


async def verify_player(request: Request) -> Player:
    # """Make sure we have a player session, otherwise, get one"""
    # player: Player = await get_player_from_request(request)
    # if player:
    #     return player
    # discord_id = request.cookies.get("tgfp-discord-id")
    # if discord_id:
    #     player = await get_player_by_discord_id(int(discord_id))
    #     if player:
    #         request.session["player_id"] = str(player.id)
    #         set_user({"email": player.email, "username": player.nick_name})
    #         return player
    #     # clear the discord id and fall through to exception
    #     request.cookies.pop("tgfp-discord-id")
    # raise HTTPException(
    #     status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"}
    # )
    with Session(engine) as session:
        player: Optional[Player] = session.get(Player, 1)
        if not player:
            raise HTTPException(status_code=404)
    return player


@app.get("/")
def home(
    request: Request,
    player: Player = Depends(verify_player),
    session: Session = Depends(get_session),
    info: TGFPInfo = Depends(get_latest_info),
):
    """Home page"""
    context = {"player": player, "info": info}
    return templates.TemplateResponse(request=request, name="home.j2", context=context)


@app.get("/profile")
def profile():
    return {"success": True}


@app.get("/picks")
def picks():
    return {"success": True}


@app.get("/allpicks")
def allpicks():
    return {"success": True}


@app.get("/standings")
def standings():
    return {"success": True}


@app.get("/rules")
def rules():
    return {"success": True}


@app.get("/logout")
def logout():
    return {"success": True}


if __name__ == "__main__":
    reload = os.getenv("ENVIRONMENT", "development") != "production"
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=6701, reload=reload, access_log=False
    )
