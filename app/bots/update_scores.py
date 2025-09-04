"""Take a game, and get the current scores from TgfpNfl and update the TGFP game"""

import asyncio
from typing import List
from sqlmodel import Session

from db import engine
from models.model_helpers import TGFPInfo, get_tgfp_info
from tgfp_nfl import TgfpNfl

from models import Game


async def update_game(game_id: int):
    """
    Update all the wins / losses / scores, etc...
    @param game:
    @return: The current live status of the game
    """
    info: TGFPInfo = get_tgfp_info()
    nfl_data_source = TgfpNfl(week_no=info.current_week)
    with Session(engine) as session:
        game: Game | None = session.get(Game, game_id)
        if not game:
            return
        nfl_game = nfl_data_source.find_game(nfl_game_id=game.tgfp_nfl_game_id)
        game.home_team_score = int(nfl_game.total_home_points)
        game.road_team_score = int(nfl_game.total_away_points)
        game.game_status = nfl_game.game_status_type
        session.add(game)
        session.commit()
        # TODO: write some code to kill the job if the game is final


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(update_game(34))
