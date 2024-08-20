""" Main entry point for website """
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Final, List

import pydantic_core
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates

# pylint: disable=ungrouped-imports
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette_discord import DiscordOAuthClient
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
import sentry_sdk


from app.config import Config
from app.models import db_init, Player, TGFPInfo, get_tgfp_info
from app.api.create_picks import create_picks, CreatePicksException

sentry_sdk.init(
    dsn="https://df0bb7eec46f36b0bf27935fba45470e@sentry.sturgeonfamily.com/2",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
)

SECONDS: Final[int] = 60*60*24
DAYS: Final[int] = 365
COOKIE_TIME_OUT = DAYS * SECONDS


def init_config() -> Config:
    """ Initialize the config object """
    async def asyncfunc() -> Config:
        return await Config.get_config()
    return asyncio.run(asyncfunc())


config: Config = init_config()

discord: DiscordOAuthClient = DiscordOAuthClient(
    config.DISCORD_CLIENT_ID,
    config.DISCORD_CLIENT_SECRET,
    config.DISCORD_REDIRECT_URI
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """ Perform all app initialization before 'yield' """
    # Initialize the model / DB connection
    await db_init()
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
# noinspection PyTypeChecker
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET_KEY,
    max_age=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_tgfp_info_from_request(request: Request) -> Optional[TGFPInfo]:
    """ Return the deserialized TGFPInfo object """
    tgfp_info: Optional[TGFPInfo] = None
    if request.scope.get('session') is not None:
        tgfp_json: str = request.session.get('tgfp_info')
        if tgfp_json and 'season' in tgfp_json:
            tgfp_info = TGFPInfo.model_validate(
                pydantic_core.from_json(tgfp_json)
            )
    return tgfp_info


def get_player_from_request(request: Request) -> Optional[Player]:
    """ Return the deserialized player object from the request session """
    player: Optional[Player] = None
    if request.scope.get('session') is not None:
        player_json: str = request.session.get('player')
        if player_json and 'name' in player_json:
            player = Player.model_validate(
                pydantic_core.from_json(player_json)
            )
    return player


async def verify_player(request: Request) -> Player:
    """ Make sure we have a player session, otherwise, get one"""
    player: Player = get_player_from_request(request)
    if player:
        return player
    discord_id = request.cookies.get("tgfp-discord-id")
    if discord_id:
        player = await get_player_by_discord_id(int(discord_id))
        if player:
            request.session["player"] = player.model_dump_json()
            return player
        # clear the discord id and fall through to exception
        request.cookies.pop("tgfp-discord-id")
    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={'Location': '/login'})


async def get_latest_info(request: Request) -> Optional[TGFPInfo]:
    """ Returns the current TGFPInfo object """
    info: TGFPInfo = get_tgfp_info_from_request(request)
    if info:
        return info
    info = await get_tgfp_info()
    request.session['tgfp_info'] = info.model_dump_json()
    return info


@app.get("/discord_login")
async def discord_login():
    """ Login url for discord """
    return discord.redirect()


@app.get("/login")
async def login(request: Request, info: TGFPInfo = Depends(get_tgfp_info)):
    """ Login page for discord """
    context = {
        'info': info
    }
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


@app.get("/logout")
async def logout(request: Request):
    """ Logs the user out and clears the session """
    request.session.clear()
    redirect_url = request.url_for('login')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie('tgfp-discord-id')
    return response


@app.get("/callback")
async def callback(code: str, request: Request):
    """ Callback url for discord """
    user = await discord.login(code)
    player: Player = await get_player_by_discord_id(user.id)
    if player:
        redirect_url = request.url_for('home')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key='tgfp-discord-id',
            value=str(user.id),
            max_age=COOKIE_TIME_OUT,
        )
    else:
        redirect_url = request.url_for('login')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@app.get("/")
def root(request: Request):
    """ Redirect '/' to /home """
    return RedirectResponse(request.url_for('home'), status.HTTP_301_MOVED_PERMANENTLY)


@app.get("/home", response_class=HTMLResponse)
def home(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Home page """
    context = {
        'player': player,
        'info': info
    }
    return templates.TemplateResponse(
            request=request, name="home.j2", context=context
        )


@app.get('/standings')
async def standings(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Returns the standings page """
    players: List[Player] = await Player.find({'active': True}).to_list()
    players.sort(key=lambda x: x.total_points, reverse=True)
    context = {
        'player': player,
        'info': info,
        'active_players': players
    }
    return templates.TemplateResponse(
        request=request, name="standings.j2", context=context
    )


@app.post("/api/create_picks_page")
async def create_picks_page():
    """ API for creating the picks page """
    try:
        await create_picks()
    except CreatePicksException as e:
        # pylint: disable=raise-missing-from
        raise HTTPException(status_code=500, detail=str(e))
    return {'success': True}


async def get_player_by_discord_id(discord_id: int) -> Optional[Player]:
    """ Returns a player by their discord ID """
    player: Player = await Player.find_one(Player.discord_id == discord_id)
    return player


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
