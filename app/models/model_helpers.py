from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Session, select, col

from .game import Game
from db import engine


class TGFPInfo(BaseModel):
    """
    It's required to have a DB init called already to use this class
    :attributes:

    - :class:`int` season --> The current season (YYYY)
    - :class:`int` display_week --> This is the more comment week used.
    - :class:`int` active_week --> Used for last_wins, last_losses etc.
    - :class:`str` app_version --> Debug information containing the app version
    - :class:`str` app_env --> Debug information containing the app environment
    """

    season: int = 2025
    display_week: int = 1
    active_week: int = 1
    app_version: str = "not_set"
    app_env: str = "not_set"


async def get_tgfp_info() -> TGFPInfo:
    """Returns the TGFPInfo object filled w/values"""
    # Get the current season.
    # NOTE: The current season is the year in which the season starts.
    #  -- if the month Jan - May (1-5) then consider the year before the starting
    #  season.
    year = datetime.now().year
    month = datetime.now().month
    if month < 6:
        year -= 1
    current_season: int = year

    # get display_week and current_active_week
    a_game: Optional[Game] = None
    with Session(engine) as session:
        statement = (
            select(Game)
            .where(Game.season == current_season)
            .order_by(col(Game.id).desc())
            .limit(1)
        )
        results = session.exec(statement)
        a_game = results.first()

    if a_game is None:
        # EARLY RETURN
        return TGFPInfo(season=current_season, display_week=1, active_week=1)
    last_weeks_games: List[Game] = await Game.find(
        {"season": a_game.season, "week_no": a_game.week_no}
    ).to_list()

    all_complete = True
    for g in last_weeks_games:
        if not g.is_final:
            all_complete = False
    if all_complete:
        display_week = a_game.week_no + 1
    else:
        display_week = a_game.week_no
    display_week += 1 if display_week == PRO_BOWL_WEEK else 0
    current_active_week = a_game.week_no
    return TGFPInfo(
        season=current_season,
        display_week=display_week,
        active_week=current_active_week,
    )
