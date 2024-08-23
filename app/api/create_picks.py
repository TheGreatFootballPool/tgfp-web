""" Used to create the picks page """
from typing import List

from tgfp_nfl import TgfpNfl, TgfpNflGame

from app.models import Team, TGFPInfo, get_tgfp_info, Game

DEBUG = True
# from send_picks_ready_campaign import send_campaign_email


class CreatePicksException(Exception):
    """ Exception class """
    def __init__(self, msg, *args):
        super().__init__(args)
        self.msg = msg

    def __str__(self):
        return f"Exception: {self.msg}"


async def create_picks() -> dict:
    """ Creates the weekly picks page """
    info: TGFPInfo = await get_tgfp_info(debug=DEBUG)
    week_no: int = info.display_week
    if DEBUG:
        nfl = TgfpNfl(season_type=1, week_no=week_no)
    else:
        nfl: TgfpNfl = TgfpNfl(week_no=week_no)
    nfl_games: List[TgfpNflGame] = nfl.games()
    if not nfl_games:
        raise CreatePicksException("There should have been games!!!")
    nfl_game: TgfpNflGame
    for nfl_game in nfl_games:
        road_team: Team = await Team.find_one(Team.tgfp_nfl_team_id == nfl_game.away_team.id)
        home_team: Team = await Team.find_one(Team.tgfp_nfl_team_id == nfl_game.home_team.id)
        if nfl_game.favored_team:
            fav_team = await Team.find_one(Team.tgfp_nfl_team_id == nfl_game.favored_team.id)
        else:
            fav_team = home_team
        tgfp_game = Game(
            favorite_team=fav_team,
            home_team=home_team,
            road_team=road_team,
            game_status=nfl_game.game_status_type,
            home_team_score=0,
            road_team_score=0,
            spread=nfl_game.spread + .5,
            start_time=nfl_game.start_time,
            week_no=int(week_no),
            tgfp_nfl_game_id=nfl_game.id,
            season=info.season
        )
        # noinspection PyArgumentList
        await tgfp_game.save()
    return {'success': True}

    # send_campaign_email(week_no)
