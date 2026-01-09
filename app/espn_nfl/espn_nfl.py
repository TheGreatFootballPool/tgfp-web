"""
This module contains all the necessary functions for interfacing with
a data source (ESPN / Yahoo for example) for retrieving scores, schedule data, etc.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Any, List
from dateutil import parser
import httpx


def _http_get_with_retry(url: str, **kwargs) -> httpx.Response:
    """
    Internal helper for GET requests with basic retry logic.

    Retries on transient server errors (501, 502, 503) up to 2 times.
    Uses exponential backoff for delays.

    :param url: Target URL
    :param kwargs: Extra keyword arguments passed to httpx.get()
    :return: httpx.Response object if successful
    :raises httpx.RequestError: For connection-level issues
    :raises httpx.HTTPStatusError: If retries exhausted and status still invalid
    """
    max_retries = 2
    delay = 1.0  # start with 1s, then 2s

    for attempt in range(max_retries + 1):  # includes first try
        try:
            response = httpx.get(url, **kwargs)
            if response.status_code in (501, 502, 503):
                raise httpx.HTTPStatusError(
                    f"Transient error {response.status_code} from {url}",
                    request=response.request,
                    response=response,
                )
            return response
        except (httpx.RequestError, httpx.HTTPStatusError):
            logging.warning(f"Retry attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay *= 2  # exponential backoff
    raise RuntimeError("Unexpected fallthrough in _http_get_with_retry")


@dataclass
class ESPNSeasonType:
    type_id: int
    name: str
    weeks: int
    skip_weeks: list


class ESPNNfl:
    """The main class for interfacing with Data Source JSON for sports"""

    # This is hard coded to match what ESPN provides.
    # More information can be found here: https://github.com/pseudo-r/Public-ESPN-API
    SEASON_TYPES: List[ESPNSeasonType] = [
        ESPNSeasonType(1, "Pre Season", 3, []),
        ESPNSeasonType(2, "Regular Season", 18, []),
        ESPNSeasonType(3, "Post Season", 5, [4]),
        ESPNSeasonType(4, "Off Season", 0, []),
    ]

    def __init__(
        self, week_no: Optional[int] = None, season_type: Optional[int] = None
    ):
        self._games = []
        self._teams = []
        self._standings = []
        self._games_source_data = None
        self._teams_source_data = None
        self._standings_source_data = None
        self._current_week_source_data: dict | None = None
        self._season = None
        self._season_type = season_type
        self._week_no = week_no
        self._base_url = "https://site.api.espn.com/apis/v2/sports/football/nfl/"
        self._base_site_url = (
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        )
        self._base_core_api_url = (
            "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
        )

    @property
    # Note, this cache only survives as long as the object is instantiated.
    #  in all cases, this is once per 'request'. once the request has returned the
    #  object is GC'd
    def _current_season_week_data(self) -> dict:
        """save the info for the current season, season_type and week"""
        if self._current_week_source_data:
            return self._current_week_source_data
        url_to_query = self._base_site_url + "/scoreboard"
        response = _http_get_with_retry(url_to_query)
        content = response.json()
        self._current_week_source_data = content
        return self._current_week_source_data

    def __get_games_source_data(self) -> list:
        """Get Games from ESPN -- defaults to current season
        :return: list of games
        """
        url_to_query = (
            self._base_site_url
            + f"/scoreboard?seasontype={self.season_type}&week={self.week_no}"
        )
        response = _http_get_with_retry(url_to_query)
        content = response.json()
        return content["events"]

    def __get_teams_source_data(self) -> list:
        """Get Teams from ESPN
        :return: list of teams
        """
        url_to_query = self._base_site_url + "/teams"
        response = _http_get_with_retry(url_to_query)
        content = response.json()
        return content["sports"][0]["leagues"][0]["teams"]

    def __get_standings_source_data(self) -> list:
        """Get Standings from ESPN
        :return: list of teams / standings
        """
        season_type = self.season_type
        if season_type == 3:
            season_type = 2
        url_to_query = self._base_url + f"/standings?seasontype={season_type}"
        response = _http_get_with_retry(url_to_query)
        content = response.json()
        afc_standings: list = content["children"][0]["standings"]["entries"]
        nfc_standings: list = content["children"][1]["standings"]["entries"]
        all_standings: list = afc_standings + nfc_standings
        return all_standings

    @property
    def season(self) -> int:
        return self._current_season_week_data["season"]["year"]

    @property
    def season_type(self) -> int:
        if self._season_type:
            return self._season_type
        self._season_type = self._current_season_week_data["season"]["type"]
        return self._season_type

    @property
    def week_no(self) -> int:
        if self._week_no:
            return self._week_no
        self._week_no = self._current_season_week_data["week"]["number"]
        return self._week_no

    def games(self) -> List[ESPNNflGame]:
        """
        Returns:
            a list of all ESPNNflGames in the JSON structure
        """
        if self._games:
            return self._games
        if not self._games_source_data:
            self._games_source_data = self.__get_games_source_data()
        for game_data in self._games_source_data:
            a_game: ESPNNflGame = ESPNNflGame(self, game_data=game_data)
            self._games.append(a_game)

        return self._games

    def teams(self) -> List[ESPNNflTeam]:
        """
        Build a list of teams using the teams source and standings source data
        Returns:
            a list of all TgfpNflTeams
        """
        if self._teams:
            return self._teams
        if not self._teams_source_data:
            self._teams_source_data = self.__get_teams_source_data()
        if not self._standings_source_data:
            self._standings_source_data = self.__get_standings_source_data()
        for team_data in self._teams_source_data:
            single_team_data: dict = team_data["team"]
            team_id: str = single_team_data["uid"]
            single_team_standings: ESPNNflStanding = (
                self.find_tgfp_nfl_standing_for_team(team_id)
            )
            team: ESPNNflTeam = ESPNNflTeam(single_team_data, single_team_standings)
            self._teams.append(team)
        return self._teams

    def standings(self) -> List[dict]:
        """
        Returns:
            a list of all ESPNNflGames in the JSON structure
        """
        if self._standings:
            return self._standings
        if not self._standings_source_data:
            self._standings_source_data = self.__get_standings_source_data()
        for standing_data in self._standings_source_data:
            self._standings.append(ESPNNflStanding(standing_data))
        return self._standings

    def find_game(self, nfl_game_id=None, event_id=None) -> Optional[ESPNNflGame]:
        """returns a list of all games that optionally"""
        found_game: Optional[ESPNNflGame] = None
        for game in self.games():
            found = True
            if nfl_game_id and nfl_game_id != game.id:
                found = False
            if event_id and event_id != game.event_id:
                found = False
            if found:
                found_game = game
                break

        return found_game

    def find_teams(self, team_id=None, short_name=None) -> List[ESPNNflTeam]:
        """returns a list of all teams optionally filtered by a single team_id"""
        found_teams = []
        for team in self.teams():
            found = True
            if team_id and team_id != team.id:
                found = False
            if short_name and short_name != team.short_name:
                found = False
            if found:
                found_teams.append(team)

        return found_teams

    def find_tgfp_nfl_standing_for_team(
        self, team_id: str
    ) -> Optional[ESPNNflStanding]:
        """Returns the 'ESPNNflStanding' for a team in the form of a dict
        'wins': <int>
        'losses': <int>
        'ties': <int>
        """
        standing: ESPNNflStanding
        for standing in self.standings():
            if team_id == standing.team_id:
                return standing
        return None


# noinspection PyTypeChecker
class ESPNNflGame:
    """A single game from the Data Source JSON"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, data_source: ESPNNfl, game_data):
        # pylint: disable=invalid-name
        self.id: str = game_data["uid"]
        # pylint: enable=invalid-name
        self._data_source = data_source
        self._game_source_data = game_data
        self._game_status_source_data: dict = game_data["competitions"][0]["status"]
        self._odds_source_data: List[dict[str, Any]] = []
        if "odds" in game_data["competitions"][0]:
            self._odds_source_data = game_data["competitions"][0]["odds"]
        self._home_team: Optional[ESPNNflTeam] = None
        self._away_team: Optional[ESPNNflTeam] = None
        self._favored_team: Optional[ESPNNflTeam] = None
        self._winning_team: Optional[ESPNNflTeam] = None
        self._spread: float = 0.0
        self._total_home_points: int = 0
        self._total_away_points: int = 0
        self.start_time = parser.parse(game_data["date"])
        self.week_no: int = game_data["week"]["number"]
        self.season_type: int = game_data["season"]["type"]
        self.season: int = game_data["season"]["year"]
        self.game_status_type = game_data["status"]["type"]["name"]
        self.event_id = int(game_data["id"])

    def _odds(self) -> Optional[ESPNNflOdd]:
        """
        Returns:
            the first odds, ignoring all others
        """
        return_odds: Optional[ESPNNflOdd] = None
        if self._odds_source_data:
            # noinspection PyTypeChecker
            first_odd: dict = self._odds_source_data[0]
            return_odds = ESPNNflOdd(data_source=self._data_source, odd_data=first_odd)
        return return_odds

    @property
    def favored_team(self) -> Optional[ESPNNflTeam]:
        if self._favored_team:
            return self._favored_team
        self.__set_home_away_favorite_teams_and_score()
        return self._favored_team

    @property
    def spread(self):
        if self._spread:
            return self._spread
        self.__set_home_away_favorite_teams_and_score()
        return self._spread

    @property
    def is_pregame(self):
        return self.game_status_type == "STATUS_SCHEDULED"

    @property
    def is_final(self):
        return self.game_status_type == "STATUS_FINAL"

    @property
    def home_team(self):
        if self._home_team:
            return self._home_team
        self.__set_home_away_favorite_teams_and_score()
        return self._home_team

    @property
    def away_team(self) -> ESPNNflTeam:
        if self._away_team:
            return self._away_team
        self.__set_home_away_favorite_teams_and_score()
        return self._away_team

    @property
    def winning_team(self) -> Optional[ESPNNflTeam]:
        teams: list = self._game_source_data["competitions"][0]["competitors"]
        if not self._winning_team and teams and "winner" in teams[0]:
            winner_idx = 0 if teams[0].get("winner") else 1
            self._winning_team = self._data_source.find_teams(
                team_id=teams[winner_idx]["uid"]
            )[0]
        return self._winning_team

    @property
    def total_home_points(self) -> int:
        if self._total_home_points:
            return self._total_home_points
        else:
            self.__set_home_away_favorite_teams_and_score()
        return self._total_home_points

    @property
    def total_away_points(self) -> int:
        if self._total_away_points:
            return self._total_away_points
        else:
            self.__set_home_away_favorite_teams_and_score()
        return self._total_away_points

    def __set_home_away_favorite_teams_and_score(self):
        teams: list = self._game_source_data["competitions"][0]["competitors"]
        if self._odds():
            if self._odds().favored_team_short_name is None:
                self._favored_team = self._home_team
                self._spread = 0.5
            else:
                self._favored_team = self._data_source.find_teams(
                    short_name=self._odds().favored_team_short_name
                )[0]
                self._spread = self._odds().favored_team_spread
        if teams[0]["homeAway"] == "home":
            self._total_home_points = int(teams[0]["score"])
            self._home_team = self._data_source.find_teams(team_id=teams[0]["uid"])[0]
            self._total_away_points = int(teams[1]["score"])
            self._away_team = self._data_source.find_teams(team_id=teams[1]["uid"])[0]
        else:
            self._total_home_points = int(teams[1]["score"])
            self._home_team = self._data_source.find_teams(team_id=teams[1]["uid"])[0]
            self._total_away_points = int(teams[0]["score"])
            self._away_team = self._data_source.find_teams(team_id=teams[0]["uid"])[0]

    @property
    def extra_info(self) -> dict:
        return {
            "description": self._game_source_data["name"],
            "game_time": self._game_source_data["status"]["type"]["detail"],
        }


class ESPNNflTeam:
    """The class that wraps the Data Source JSON for each team"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    def __init__(self, team_data: dict, team_standings: ESPNNflStanding):
        self.data = team_data
        self.id = team_data["uid"]
        self.city = team_data["location"]
        self.long_name = team_data["shortDisplayName"]
        self.short_name: str = str(team_data["abbreviation"]).lower()
        self.full_name = team_data["displayName"]
        self.logo_url = team_data["logos"][0]["href"]
        self.color = team_data["color"]
        self.alternate_color = team_data["alternateColor"]
        self.wins = team_standings.wins
        self.losses = team_standings.losses
        self.ties = team_standings.ties

    def tgfp_id(self, tgfp_teams):
        """
        Args:
            tgfp_teams: list of teams to loop through
        Returns:
            the tgfp_id for the current data_source's team, None if not found
        """
        found_team_id = None
        for team in tgfp_teams:
            if self.id == team.tgfp_nfl_team_id:
                found_team_id = team.id
                break
        return found_team_id


class ESPNNflOdd:
    """Wraps the data source JSON for each 'odd' (spread)"""

    # pylint: disable=too-few-public-methods

    def __init__(self, data_source, odd_data):
        self._data_source = data_source
        self._odd_source_data = odd_data

    @property
    def favored_team_short_name(self) -> Optional[str]:
        """
        Get the favorite team short name
        Returns:
            Optional[str]: favored team short name (lower case) or None if no team is favored
        Notes:
                the string we're parsing looks like:
                DAL -3.5
                or
                EVEN
        """
        favorite: str = self._odd_source_data["details"].split()[0].lower()
        if favorite == "even":
            return None
        return favorite

    @property
    def favored_team_spread(self) -> float:
        if self.favored_team_short_name is None:
            return 0
        favorite: str = self._odd_source_data["details"]
        # noinspection PyTypeChecker
        spread: float = float(favorite.split()[1]) * -1
        return spread


class ESPNNflStanding:
    """Wraps the data source JSON for standings data for a team"""

    def __init__(self, source_standings_data: dict):
        self.team_id: str = source_standings_data["team"]["uid"]
        self.wins = 0
        self.losses = 0
        self.ties = 0
        for stat in source_standings_data["stats"]:
            if stat["type"] == "wins":
                self.wins = int(stat["value"])
            if stat["type"] == "losses":
                self.losses = int(stat["value"])
            if stat["type"] == "ties":
                self.ties = int(stat["value"])
