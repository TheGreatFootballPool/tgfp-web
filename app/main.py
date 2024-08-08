""" Main entry point for website """
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI
from app.models import init, Player


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
    players: List[Player] = await Player.find_all().to_list()
    a_player: Player = await Player.find_one(Player.id == players[0].id)
    print(len(players))
    return [a_player]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
