""" Main entry point for website """
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI
from app.models import init, Player, Team, Game, Pick


@asynccontextmanager
async def lifespan(_: FastAPI):
    """ Initialize the model / DB connection """
    await init()
    yield
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    """ Hello World """
    return {"Hello": "World"}


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
    games = await Game.find(Game.season == 2023, Game.week_no == 1).to_list()
    return games


@app.get("/picks", response_model=List[Pick])
async def get_all_picks():
    """ Returns a list of all picks """
    picks = Pick.find(Pick.season == 2023, Pick.week_no == 2)
    return picks.to_list()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
