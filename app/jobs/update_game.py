"""Take a game, and get the current scores from TgfpNfl and update the TGFP game"""

from apscheduler.jobstores.base import JobLookupError
from sqlmodel import Session

from db import engine
from jobs import scheduler
from models.model_helpers import TGFPInfo, get_tgfp_info
from tgfp_nfl import TgfpNfl

from models import Game


def update_game(game_id: int):
    """
    Update all the wins / losses / scores, etc...
    @param game_id: The id of the game to update
    @type game_id: int
    :return: The current live status of the game
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
        if game.is_final:
            job_id: str = f"s{info.current_season}:w{info.current_week}:g{game.id}"
            try:
                scheduler.remove_job(job_id)
            except JobLookupError:
                pass  # already gone; fine
            return

        # TODO: write some code to kill the job if the game is final
