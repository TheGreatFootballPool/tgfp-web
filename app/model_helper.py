"""
These are helper methods for getting information about the football pool that
involves multiple model queries
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Final

from app.models import Game, db_init

PRO_BOWL_WEEK: Final[int] = 22


def current_season() -> int:
    """
    Returns the current season.
    NOTE: The current season is the year in which the season starts.
     -- if the month Jan - May (1-5) then consider the year before the starting
     season.
    """
    year = datetime.now().year
    month = datetime.now().month
    if month < 6:
        year -= 1
    return year


async def current_week() -> int:
    """
    Gets the current week

    This is defined the current week.
    It will advance to the next week once all games are 'final'
    """
    await db_init()
    game: Game = await Game.find(
        {'season': current_season()}
    ).sort("-_id").limit(1).first_or_none()
    print(game)
    if game is None:
        return 1
    last_weeks_games: List[Game] = await Game.find({
        'season': game.season,
        'week_no': game.week_no
    }).to_list()
    all_games_completed = True
    game: Optional[Game] = None
    for game in last_weeks_games:
        if not game.is_final:
            all_games_completed = False
            break
    if all_games_completed:
        this_week = game.week_no + 1
    else:
        this_week = game.week_no

    if this_week == PRO_BOWL_WEEK:
        this_week += 1
    return this_week

if __name__ == '__main__':
    asyncio.run(current_week())
