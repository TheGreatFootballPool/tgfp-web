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

    @property
    def is_skip_week(self) -> bool:
        """
        Check if the current week is a skip week for this season type.

        Returns:
            True if this week should be skipped (e.g., postseason bye week), False otherwise
        """
        season_type: ESPNSeasonType = ESPNNfl.SEASON_TYPES[self.season_type - 1]
        return self.week_no in season_type.skip_weeks


def current_week_info() -> WeekInfo:
    espn_nfl = ESPNNfl()
    week_info = WeekInfo(
        season=espn_nfl.season,
        season_type=espn_nfl.season_type,
        week_no=espn_nfl.week_no,
    )
    return week_info
