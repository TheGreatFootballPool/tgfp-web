"""Take a game, and get the current scores from ESPNNfl and update the TGFP game"""

import logging

from apscheduler.jobstores.base import JobLookupError
from sqlmodel import Session

from db import engine
from .scheduler import job_scheduler, job_id_for_game_id
from espn_nfl import ESPNNfl

from models import Game


def _update_one_game(session: Session, game_id: int) -> Game | None:
    """
    Update all the wins / losses / scores, etc...
    @param game_id: The id of the game to update
    @type game_id: int
    :return: The current live status of the game
    """
    game: Game | None = session.get(Game, game_id)
    if not game:
        return None
    nfl_data_source = ESPNNfl(week_no=game.week_no, season_type=game.season_type)
    nfl_game = nfl_data_source.find_game(nfl_game_id=game.tgfp_nfl_game_id)
    if not nfl_game:
        logging.warning(
            f"No game with id {game_id}  Probably because ESPN was not responding"
        )
        return None
    game.home_team_score = int(nfl_game.total_home_points)
    game.road_team_score = int(nfl_game.total_away_points)
    game.game_status = nfl_game.game_status_type
    session.add(game)
    session.commit()
    return game


def update_a_game(game_id: int):
    """
    Update all the wins / losses / scores, etc...
    @param game_id: The id of the game to update
    @type game_id: int
    :return: The current live status of the game
    """
    with Session(engine) as session:
        game = _update_one_game(session=session, game_id=game_id)
        if game and game.is_final:
            job_id: str = job_id_for_game_id(game_id=game_id)
            try:
                logging.info("Removing job %s with game: %s", job_id, game.id)
                job_scheduler.remove_job(job_id)
            except JobLookupError:
                pass  # already gone; fine
