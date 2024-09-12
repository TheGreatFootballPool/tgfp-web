""" Used to create the picks page """
from typing import List

import httpx
from discord_webhook import DiscordWebhook
from tgfp_nfl import TgfpNfl, TgfpNflGame

from config import Config
from models import Team, TGFPInfo, get_tgfp_info, Game

# from send_picks_ready_campaign import send_campaign_email

def _create_campaign(config: Config, week_no: int) -> int:
    """
    Creates the listmonk campaign
    @return: int ID of the campaign
    """
    auth_hash = config.LISTMONK_AUTH_HASH
    list_id: int = int(config.LISTMONK_LIST_ID)
    url = config.LISTMONK_API_URL + 'campaigns'
    data = {
        "lists": [
            list_id
        ],
        "subject": f"Picks Page is READY for week {week_no}",
        "template_id": 5,
        "type": "regular",
        "body": f"The Picks page is ready for week {week_no}",
        "name": f"Picks Page is READY for week {week_no}",
        "content_type": "richtext"
    }
    headers = {
        "Authorization": f"Basic {auth_hash}",
        "Content-Type": "application/json; charset=utf-8",
    }
    result = httpx.post(url=url, json=data, headers=headers)
    json_result = result.json()
    return json_result['data']['id']


def send_campaign_email(week_no: int):
    """ Send a 'picks page is ready email"""
    config: Config = Config.get_config()
    auth_hash = config.LISTMONK_AUTH_HASH
    campaign_id = _create_campaign(config, week_no)

    url = config.LISTMONK_API_URL + f"campaigns/{campaign_id}/status"
    data = {"status": "running"}
    headers = {
        "Authorization": f"Basic {auth_hash}",
        "Content-Type": "application/json; charset=utf-8",
    }
    httpx.put(url=url, json=data, headers=headers)


def send_discord_msg(week_no: int):
    config: Config = Config.get_config()
    msg: str = f"""Hey @everyone!

The picks page is ready for week {week_no}:
https://tgfp.us/picks

Go get 'em!"""
    webhook = DiscordWebhook(
        url=config.DISCORD_NAG_BOT_WEBHOOK_URL,
        content=msg
    )
    webhook.execute()

class CreatePicksException(Exception):
    """ Exception class """
    def __init__(self, msg, *args):
        super().__init__(args)
        self.msg = msg

    def __str__(self):
        return f"Exception: {self.msg}"


async def create_picks() -> dict:
    """ Creates the weekly picks page """
    info: TGFPInfo = await get_tgfp_info()
    week_no: int = info.display_week
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
            spread=nfl_game.spread,
            start_time=nfl_game.start_time,
            week_no=int(week_no),
            tgfp_nfl_game_id=nfl_game.id,
            season=info.season
        )
        # noinspection PyArgumentList
        await tgfp_game.save()

    send_campaign_email(week_no)
    send_discord_msg(week_no)
    return {'success': True}

if __name__ == '__main__':
    send_discord_msg(2)
    send_campaign_email(2)
