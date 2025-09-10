"""Take a game, and get the current scores from TgfpNfl and update the TGFP game"""

import logging

from apscheduler.jobstores.base import JobLookupError
from sqlmodel import Session

from db import engine
from .scheduler import job_scheduler
from models.model_helpers import current_nfl_season
from tgfp_nfl import TgfpNfl

from models import Game


def update_game(game_id: int):
    """
    Update all the wins / losses / scores, etc...
    @param game_id: The id of the game to update
    @type game_id: int
    :return: The current live status of the game
    """
    with Session(engine) as session:
        game: Game | None = session.get(Game, game_id)
        if not game:
            return
        nfl_data_source = TgfpNfl(week_no=game.week_no)
        nfl_game = nfl_data_source.find_game(nfl_game_id=game.tgfp_nfl_game_id)
        game.home_team_score = int(nfl_game.total_home_points)
        game.road_team_score = int(nfl_game.total_away_points)
        game.game_status = nfl_game.game_status_type
        session.add(game)
        session.commit()
        if game.is_final:
            job_id: str = f"s{current_nfl_season()}:w{game.week_no}:g{game.id}"
            try:
                logging.info("Removing job %s with game: %s", job_id, game.id)
                job_scheduler.remove_job(job_id)
            except JobLookupError:
                pass  # already gone; fine
            return
