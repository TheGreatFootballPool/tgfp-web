""" Used to create the picks page """
from typing import List

from tgfp_nfl import TgfpNfl, TgfpNflGame

from app.models import Team, TGFPInfo, get_tgfp_info, Game

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
    tgfp_teams: List[Team] = await Team.find_all().to_list()
    info: TGFPInfo = await get_tgfp_info()
    week_no: int = info.display_week
    nfl: TgfpNfl = TgfpNfl(week_no=week_no)
    nfl_games: List[TgfpNflGame] = nfl.games()
    if not nfl_games:
        raise CreatePicksException("There should have been games!!!")
    for nfl_game in nfl_games:
        try:
            road_team_id = nfl_game.away_team.tgfp_id(tgfp_teams)
            home_team_id = nfl_game.home_team.tgfp_id(tgfp_teams)
            fav_team_id = nfl_game.favored_team.tgfp_id(tgfp_teams)
        except KeyError as e:
            raise CreatePicksException("KeyError from getting game detail") from e
        tgfp_game = Game(
            favorite_team_id=fav_team_id,
            game_status=nfl_game.game_status_type,
            home_team_id=home_team_id,
            home_team_score=0,
            road_team_id=road_team_id,
            road_team_score=0,
            spread=nfl_game.spread,
            start_time=nfl_game.start_time,
            week_no=int(week_no),
            tgfp_nfl_game_id=nfl_game.id,
            season=info.season
        )
        # noinspection PyArgumentList
        await tgfp_game.save()
    return {'success': True}

    # send_campaign_email(week_no)
