from datetime import datetime
from pydantic import BaseModel
from config import Config
from tgfp_nfl import TgfpNfl

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


def current_nfl_week() -> int:
    nfl = TgfpNfl()
    return nfl.current_nfl_week_no


class TGFPInfo(BaseModel):
    """
    :attributes:

    - :class:`int` current_season --> The current season (YYYY)
    - :class:`int` current_week --> This is the more comment week used.
    - :class:`str` app_version --> Debug information containing the app version
    - :class:`str` app_env --> Debug information containing the app environment
    """

    current_season: int
    current_week: int
    app_version: str
    app_env: str

    @property
    def last_week(self):
        return 1 if self.current_week == 1 else self.current_week - 1


def get_tgfp_info() -> TGFPInfo:
    """Returns the TGFPInfo object filled w/values"""
    return TGFPInfo(
        current_season=current_nfl_season(),
        current_week=current_nfl_week(),
        app_version=config.APP_VERSION,
        app_env=config.ENVIRONMENT,
    )
