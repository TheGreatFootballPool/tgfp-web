""" Main entry point for website """
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from app.config import Config
from app.models import db_init, Player, Team, Game, Pick

config: Optional[Config] = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    """ Perform all app initialization before 'yield' """
    # pylint: disable=global-statement
    global config
    config = await Config.get_config()
    # Initialize the model / DB connection
    await db_init()
    await config.DISCORD_CLIENT.init()
    yield
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/login")
async def login():
    """ Login url for discord """
    return {"url": config.DISCORD_CLIENT.oauth_login_url}


@app.get("/callback")
async def callback(code: str):
    """ Callback url for discord """
    token, refresh_token = await config.DISCORD_CLIENT.get_access_token(code)
    return {"access_token": token, "refresh_token": refresh_token}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """ Hello World """
    return templates.TemplateResponse(
            request=request, name="index.j2", context={"id": id}
        )


@app.get("/players", response_model=List[Player])
async def get_all_players():
    """ Returns a list of all players """
    return await Player.find_all().to_list()


@app.get("/teams", response_model=List[Team])
async def get_all_teams():
    """ Returns a list of all teams """
    return await Team.find_all().to_list()


@app.get("/games", response_model=List[Game])
async def get_all_games():
    """ Returns a list of all games """
    games = await Game.find(Game.season == 2023, Game.week_no == 2, fetch_links=True).to_list()
    return games


@app.get("/picks", response_model=List[Pick])
async def get_all_picks():
    """ Returns a list of all picks """
    picks = await Pick.find(
        Pick.season == 2023,
        Pick.week_no == 2,
        fetch_links=True).to_list()
    for pick in picks:
        for detail in pick.pick_detail:
            await detail.fetch_all_links()
    return picks


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
