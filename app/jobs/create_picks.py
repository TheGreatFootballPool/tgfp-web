import logging
from typing import List

from sqlmodel import Session, select

from db import engine
from models import Game, Team
from models.model_helpers import TGFPInfo, get_tgfp_info
from tgfp_nfl import TgfpNfl, TgfpNflGame


class CreatePicksException(Exception):
    """Exception class"""

    def __init__(self, msg, *args):
        super().__init__(args)
        self.msg = msg

    def __str__(self):
        return f"Exception: {self.msg}"


def _game_from_nfl_game(
    session: Session, nfl_game: TgfpNflGame, info: TGFPInfo
) -> Game:
    road_team: Team = session.exec(
        select(Team).where(Team.tgfp_nfl_team_id == nfl_game.away_team.id)
    ).one()
    home_team: Team = session.exec(
        select(Team).where(Team.tgfp_nfl_team_id == nfl_game.home_team.id)
    ).one()
    if nfl_game.favored_team:
        fav_team: Team = session.exec(
            select(Team).where(Team.tgfp_nfl_team_id == nfl_game.favored_team.id)
        ).one()
    else:
        fav_team = home_team
    game = Game(
        favorite_team_id=fav_team.id,
        home_team_id=home_team.id,
        road_team_id=road_team.id,
        game_status=nfl_game.game_status_type,
        home_team_score=0,
        road_team_score=0,
        spread=nfl_game.spread,
        start_time=nfl_game.start_time,
        week_no=int(info.current_week),
        tgfp_nfl_game_id=nfl_game.id,
        season=info.current_season,
    )
    return game


def create_picks():
    """Creates the weekly picks page"""
    logging.info("Creating weekly picks page")
    info: TGFPInfo = get_tgfp_info()
    with Session(engine) as session:
        session.info["TGFPInfo"] = info
        week_no: int = info.current_week
        nfl: TgfpNfl = TgfpNfl(week_no=week_no)
        nfl_games: List[TgfpNflGame] = nfl.games()
        if not nfl_games:
            logging.error("No nfl_games found")
            raise CreatePicksException("There should have been games!!!")
        nfl_game: TgfpNflGame
        for nfl_game in nfl_games:
            logging.debug(
                f"Creating pick for nfl_game: {nfl_game}",
                nfl_game=nfl_game.extra_info,  # type: ignore[arg-type]
            )
            tgfp_game = _game_from_nfl_game(
                nfl_game=nfl_game, session=session, info=info
            )
            session.add(tgfp_game)
        session.commit()
