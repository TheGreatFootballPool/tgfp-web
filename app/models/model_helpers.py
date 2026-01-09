from dataclasses import dataclass

from app.config import Config
from app.espn_nfl import ESPNNfl, ESPNSeasonType

config = Config.get_config()


@dataclass
class WeekInfo:
    season: int
    season_type: int
    week_no: int

    @property
    def cache_key(self):
        return f"{self.season}-{self.season_type}-{self.week_no}"

    @property
    def season_type_name(self) -> str:
        season_type: ESPNSeasonType = ESPNNfl.SEASON_TYPES[self.season_type - 1]
        return season_type.name


def current_week_info() -> WeekInfo:
    tgfp_nfl = ESPNNfl()
    week_info = WeekInfo(
        season=tgfp_nfl.season,
        season_type=tgfp_nfl.season_type,
        week_no=tgfp_nfl.week_no,
    )
    return week_info
