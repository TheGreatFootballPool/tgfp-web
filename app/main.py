"""Main entry point for website"""

import os
from typing import Annotated, Optional, List
from models.model_helpers import TGFPInfo, get_tgfp_info
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status

# TODO: Re-enable the middleware
# from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlmodel import Session, select
from db import engine
from models import Player
from app.routers import auth


from config import Config
from routers.auth import get_player_by_discord_id

config = Config.get_config()


app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(auth.router)
app.add_middleware(
    SessionMiddleware, secret_key=config.SESSION_SECRET_KEY, max_age=None
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# noinspection PyTypeChecker
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


def _get_session():
    with Session(engine) as session:
        yield session


async def _get_latest_info():
    """Returns the current TGFPInfo object"""
    return get_tgfp_info()


SessionDep = Annotated[Session, Depends(_get_session)]


async def _verify_player(request: Request) -> int:
    """Make sure we have a player session, otherwise, get one"""
    cookie = request.cookies.get("tgfp-discord-id")
    if cookie:
        player_discord_id: Optional[int] = int(cookie)
        return player_discord_id

    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/login"},
    )


@app.get("/")
async def home(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    info: TGFPInfo = Depends(_get_latest_info),
):
    """Home page"""
    player: Player = await get_player_by_discord_id(session, discord_id)
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
async def standings(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    info: TGFPInfo = Depends(_get_latest_info),
):
    """Returns the standings page"""
    session.info["TGFPInfo"] = info
    player: Player = await get_player_by_discord_id(session, discord_id)
    players: List[Player] = list(
        session.exec(select(Player).where(Player.active)).all()
    )
    players.sort(key=lambda x: x.total_points, reverse=True)
    context = {"player": player, "info": info, "active_players": players}
    return templates.TemplateResponse(
        request=request, name="standings.j2", context=context
    )


@app.get("/rules")
async def rules(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    info: TGFPInfo = Depends(_get_latest_info),
):
    """Rules page"""
    player: Player = await get_player_by_discord_id(session, discord_id)
    context = {"player": player, "info": info}
    return templates.TemplateResponse(request=request, name="rules.j2", context=context)


@app.get("/logout")
def logout():
    return {"success": True}


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, info: TGFPInfo = Depends(_get_latest_info)):
    """Login page for discord"""
    context = {"info": info}
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


if __name__ == "__main__":
    reload = os.getenv("ENVIRONMENT", "development") != "production"
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=6701, reload=reload, access_log=False
    )
