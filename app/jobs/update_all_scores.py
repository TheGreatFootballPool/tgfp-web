"""Loop through all games and update their scores"""

import logging

from sqlmodel import Session

from db import engine
from tgfp_nfl import TgfpNfl

from models import Game


def update_a_game(session: Session, game_id: int):
    """
    Update all the wins / losses / scores, etc...
    @param game_id: The id of the game to update
    @type game_id: int
    :return: The current live status of the game
    """
    game: Game | None = session.get(Game, game_id)
    if not game:
        return
    nfl_data_source = TgfpNfl(week_no=game.week_no)
    nfl_game = nfl_data_source.find_game(nfl_game_id=game.tgfp_nfl_game_id)
    if not nfl_game:
        logging.warning(
            f"No game with id {game_id}  Probably because ESPN was not responding"
        )
        return
    game.home_team_score = int(nfl_game.total_home_points)
    game.road_team_score = int(nfl_game.total_away_points)
    game.game_status = nfl_game.game_status_type
    session.add(game)
    session.commit()


def update_all_scores(session: Session):
    for game in Game.games_for_week(session=session):
        update_a_game(session, game_id=game.id)
