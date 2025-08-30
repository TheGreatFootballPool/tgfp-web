"""
This module contains all the necessary functions for interfacing with
a data source (ESPN / Yahoo for example) for retrieving scores, schedule data, etc.
"""

from __future__ import annotations

from typing import Optional, Tuple, Any
from dateutil import parser
import httpx


class TgfpNfl:
    """The main class for interfacing with Data Source json for sports"""

    def __init__(
        self,
        week_no: Optional[int] = None,
        season_type: Optional[int] = None,
        debug=False,
    ):
        self._games = []
        self._teams = []
        self._standings = []
        self._games_source_data = None
        self._teams_source_data = None
        self._standings_source_data = None
        self._debug = debug
        self._week_no = week_no if week_no else 1
        self._season_type: Optional[int] = season_type
        self._base_url = "https://site.api.espn.com/apis/v2/sports/football/nfl/"
        self._base_site_url = (
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        )
        self._base_core_api_url = (
            "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
        )

    def __get_games_source_data(self) -> list:
        """Get Games from ESPN -- defaults to current season
        :return: list of games
        """
        content: dict = {}
        week_no = self._week_no - 18 if self._week_no > 18 else self._week_no
        url_to_query = (
            self._base_site_url
            + f"/scoreboard?seasontype={self.season_type}&week={week_no}"
        )
        try:
            response = httpx.get(url_to_query)
            content = response.json()
        except httpx.RequestError:
            print("HTTP Request failed")
        return content["events"]

    def __get_teams_source_data(self) -> list:
        """Get Teams from ESPN
        :return: list of teams
        """
        content: dict = {}
        url_to_query = self._base_site_url + "/teams"
        try:
            response = httpx.get(url_to_query)
            content = response.json()
        except httpx.RequestError:
            print("HTTP Request failed")
        return content["sports"][0]["leagues"][0]["teams"]

    def __get_standings_source_data(self) -> list:
        """Get Standings from ESPN
        :return: list of teams / standings
        """
        content: dict = {}
        season_type = self.season_type
        if season_type == 3:
            season_type = 2
        url_to_query = self._base_url + f"/standings?seasontype={season_type}"
        try:
            response = httpx.get(url_to_query)
            content = response.json()
        except httpx.RequestError:
            print("HTTP Request failed")
        afc_standings: list = content["children"][0]["standings"]["entries"]
        nfc_standings: list = content["children"][1]["standings"]["entries"]
        all_standings: list = afc_standings + nfc_standings
        return all_standings

    def __get_game_predictor_source_data(self, event_id: int) -> dict:
        """Get Game Predictions from ESPN
        :return: game prediction source data for one game
        """
        content: dict = {}
        url_to_query = (
            self._base_core_api_url
            + f"events/{event_id}/competitions/{event_id}/predictor"
        )
        try:
            response = httpx.get(url_to_query)
            content = response.json()
        except httpx.RequestError:
            print("HTTP Request failed")

        return content

    @property
    def season_type(self) -> int:
        """
        Returns the season_type
           -Season types are:
            1: Preseason
                weeks 1-4 (HOF game is week=1)
            2: Regular Season
                weeks 1-18
            3: Post Season
                Week #'s
                -#1 = Wild Card Round
                -#2 = Divisional Round
                -#3 = Conference Championships
                -#4 = Super Bowl
        Returns:

        """
        if self._season_type:
            return self._season_type
        return 3 if self._week_no > 18 else 2

    @property
    def current_nfl_week_no(self) -> int:
        """Returns the current NFL week number based on a live call to the API (0 if not found)"""
        url_to_query = self._base_site_url + "/scoreboard"
        week_no: int = 0
        try:
            response = httpx.get(url_to_query)
            content = response.json()
            week_no: int = content["week"]["number"]

        except httpx.RequestError:
            print("HTTP Request failed")
        return week_no

    def games(self) -> List[TgfpNflGame]:
        """
        Returns:
            a list of all TgfpNflGames in the json structure
        """
        if self._games:
            return self._games
        if not self._games_source_data:
            self._games_source_data = self.__get_games_source_data()
        for game_data in self._games_source_data:
            single_game_data = self.__get_game_predictor_source_data(
                int(game_data["id"])
            )
            a_game: TgfpNflGame = TgfpNflGame(
                self, game_data=game_data, game_prediction_data=single_game_data
            )
            self._games.append(a_game)

        return self._games

    def teams(self) -> List[TgfpNflTeam]:
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
            single_team_standings: TgfpNflStanding = (
                self.find_tgfp_nfl_standing_for_team(team_id)
            )
            team: TgfpNflTeam = TgfpNflTeam(single_team_data, single_team_standings)
            self._teams.append(team)
        return self._teams

    def standings(self) -> List[dict]:
        """
        Returns:
            a list of all TgfpNflGames in the json structure
        """
        if self._standings:
            return self._standings
        if not self._standings_source_data:
            self._standings_source_data = self.__get_standings_source_data()
        for standing_data in self._standings_source_data:
            self._standings.append(TgfpNflStanding(standing_data))
        return self._standings

    def find_game(self, nfl_game_id=None, event_id=None) -> Optional[TgfpNflGame]:
        """returns a list of all games that optionally"""
        found_game: Optional[TgfpNflGame] = None
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

    def find_teams(self, team_id=None, short_name=None) -> List[TgfpNflTeam]:
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
    ) -> Optional[TgfpNflStanding]:
        """Returns the 'TgfpNflStanding' for a team in the form of a dict
        'wins': <int>
        'losses': <int>
        'ties': <int>
        """
        standing: TgfpNflStanding
        for standing in self.standings():
            if team_id == standing.team_id:
                return standing
        return None


# noinspection PyTypeChecker
class TgfpNflGame:
    """A single game from the Data Source json"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, data_source: TgfpNfl, game_data, game_prediction_data):
        # pylint: disable=invalid-name
        self.id: str = game_data["uid"]
        # pylint: enable=invalid-name
        self._data_source = data_source
        self._game_source_data = game_data
        self._game_status_source_data: dict = game_data["competitions"][0]["status"]
        self._odds_source_data: List[dict[str, Any]] = []
        if "odds" in game_data["competitions"][0]:
            self._odds_source_data = game_data["competitions"][0]["odds"]
        self._game_predictor_source_data = game_prediction_data
        self._home_team: Optional[TgfpNflTeam] = None
        self._away_team: Optional[TgfpNflTeam] = None
        self._favored_team: Optional[TgfpNflTeam] = None
        self._winning_team: Optional[TgfpNflTeam] = None
        self._spread: float = 0.0
        self._total_home_points: int = 0
        self._total_away_points: int = 0
        self.start_time = parser.parse(game_data["date"])
        self.game_status_type = game_data["status"]["type"]["name"]
        self.event_id = int(game_data["id"])

    def _odds(self) -> Optional[TgfpNflOdd]:
        """
        Returns:
            the first odds, ignoring all others
        """
        return_odds: Optional[TgfpNflOdd] = None
        if self._odds_source_data:
            # noinspection PyTypeChecker
            first_odd: dict = self._odds_source_data[0]
            return_odds = TgfpNflOdd(data_source=self._data_source, odd_data=first_odd)
        return return_odds

    def _prediction_helper(
        self, stat_name: str, home_team: bool = True, key: str = "displayValue"
    ) -> str | float:
        team = "homeTeam" if home_team else "awayTeam"
        statistics: list = self._game_predictor_source_data[team]["statistics"]
        for stat in statistics:
            if stat["name"] == stat_name:
                return stat[key]
        return "Not Found"

    @property
    def favored_team(self) -> Optional[TgfpNflTeam]:
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
    def away_team(self) -> TgfpNflTeam:
        if self._away_team:
            return self._away_team
        self.__set_home_away_favorite_teams_and_score()
        return self._away_team

    @property
    def winning_team(self) -> Optional[TgfpNflTeam]:
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

    @property
    def home_team_predicted_win_pct(self) -> float:
        return float(self._prediction_helper("gameProjection"))

    @property
    def away_team_predicted_win_pct(self) -> float:
        return float(self._prediction_helper("gameProjection", home_team=False))

    @property
    def home_team_fpi(self) -> float:
        return float(
            self._prediction_helper("oppSeasonStrengthRating", home_team=False)
        )

    @property
    def away_team_fpi(self) -> float:
        return float(self._prediction_helper("oppSeasonStrengthRating"))

    @property
    def home_team_predicted_pt_diff(self) -> float:
        return float(self._prediction_helper("teamPredPtDiff"))

    @property
    def matchup_quality(self) -> float:
        return float(self._prediction_helper("matchupQuality"))

    @property
    def away_team_predicted_pt_diff(self) -> float:
        return float(self._prediction_helper("teamPredPtDiff", home_team=False))

    @property
    def predicted_winning_diff_team(self) -> Tuple[float, TgfpNflTeam]:
        """
        Get the predicted winner of the game, and the point differential
        Returns:
           - float, TgfpNflTeam # Point differential (float) winning team
        """
        # get either home or away, it doesn't matter
        diff: float = self.home_team_predicted_pt_diff
        if diff > 0:
            return diff, self.home_team
        diff = self.away_team_predicted_pt_diff
        return diff, self.away_team

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


class TgfpNflTeam:
    """The class that wraps the Data Source JSON for each team"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    def __init__(self, team_data: dict, team_standings: TgfpNflStanding):
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


class TgfpNflOdd:
    """Wraps the data source json for each 'odd' (spread)"""

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


class TgfpNflStanding:
    """Wraps the data source json for standings data for a team"""

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


if __name__ == "__main__":
    nfl = TgfpNfl()
    print(nfl.current_nfl_week_no)
