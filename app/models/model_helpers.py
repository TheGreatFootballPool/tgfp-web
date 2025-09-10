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


class TGFPInfo(BaseModel):
    """
    :attributes:

    - :class:`int` current_season --> The current season (YYYY)
    - :class:`str` app_version --> Debug information containing the app version
    - :class:`str` app_env --> Debug information containing the app environment
    """

    current_season: int
    app_version: str
    app_env: str
    umami_tracking_id: str
    bugsink_dsn: str


def get_tgfp_info() -> TGFPInfo:
    """Returns the TGFPInfo object filled w/values"""
    return TGFPInfo(
        current_season=current_nfl_season(),
        app_version=config.APP_VERSION,
        app_env=config.ENVIRONMENT,
        umami_tracking_id=config.UMAMI_TRACKING_ID,
        bugsink_dsn=config.BUGSINK_DSN,
    )
