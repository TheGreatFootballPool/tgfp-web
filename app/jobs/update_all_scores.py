"""Loop through all games and update their scores"""

from sqlmodel import Session

from jobs.update_game import _update_one_game

from models import Game
from models.model_helpers import current_week_info


def update_all_scores(session: Session):
    for game in Game.games_for_week(week_info=current_week_info(), session=session):
        _update_one_game(session, game_id=game.id)
