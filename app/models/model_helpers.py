from datetime import datetime
from pydantic import BaseModel
from app.config import Config

config = Config.get_config()


def current_nfl_season() -> int:
    # NOTE: The current season is the year in which the season starts.
    #  -- if the month Jan - May (1-5) then consider the year before the starting
    #  season.
    year = datetime.now().year
    month = datetime.now().month
    if month < 6:
        year -= 1
    return year
