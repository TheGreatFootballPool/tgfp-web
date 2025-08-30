"""Used to create the picks page"""

import asyncio
from typing import List

import httpx
from discord_webhook import DiscordWebhook

from db import engine
from models.model_helpers import TGFPInfo, get_tgfp_info
from tgfp_nfl import TgfpNfl, TgfpNflGame
from sqlmodel import Session, select

from models import Team, Game
from config import Config


def _create_campaign(config: Config, week_no: int) -> int:
    """
    Creates the listmonk campaign
    @return: int ID of the campaign
    """
    auth_hash = config.LISTMONK_AUTH_HASH
    list_id: int = int(config.LISTMONK_LIST_ID)
    url = config.LISTMONK_API_URL + "campaigns"
    data = {
        "lists": [list_id],
        "subject": f"Picks Page is READY for week {week_no}",
        "template_id": 5,
        "type": "regular",
        "body": f"The Picks page is ready for week {week_no}",
        "name": f"Picks Page is READY for week {week_no}",
        "content_type": "richtext",
    }
    headers = {
        "Authorization": f"Basic {auth_hash}",
        "Content-Type": "application/json; charset=utf-8",
    }
    result = httpx.post(url=url, json=data, headers=headers)
    json_result = result.json()
    return json_result["data"]["id"]


def send_campaign_email(week_no: int):
    """Send a 'picks page is ready email"""
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
    """Send the 'picks page is ready' message to the discord server"""
    config: Config = Config.get_config()
    msg: str = f"""Hey @everyone!

The picks page is ready for week {week_no}:
https://tgfp.us/picks

Go get 'em!"""
    webhook = DiscordWebhook(url=config.DISCORD_NAG_BOT_WEBHOOK_URL, content=msg)
    webhook.execute()


class CreatePicksException(Exception):
    """Exception class"""

    def __init__(self, msg, *args):
        super().__init__(args)
        self.msg = msg

    def __str__(self):
        return f"Exception: {self.msg}"


def game_from_nfl_game(session: Session, nfl_game: TgfpNflGame, info: TGFPInfo) -> Game:
    road_team: Team = session.exec(
        select(Team).where(Team.tgfp_nfl_team_id == nfl_game.away_team.id)
    ).one()
    home_team: Team = session.exec(
        select(Team).where(Team.tgfp_nfl_team_id == nfl_game.home_team.id)
    ).one()
    if nfl_game.favored_team:
        fav_team: Team = session.exec(
            select(Team).where(Team.tgfp_nfl_team_id == nfl_game.favored_team.id)
        ).one()
    else:
        fav_team = home_team
    game = Game(
        favorite_team_id=fav_team.id,
        home_team_id=home_team.id,
        road_team_id=road_team.id,
        game_status=nfl_game.game_status_type,
        home_team_score=0,
        road_team_score=0,
        spread=nfl_game.spread,
        start_time=nfl_game.start_time,
        week_no=int(info.current_week),
        tgfp_nfl_game_id=nfl_game.id,
        season=info.current_season,
    )
    return game


def create_picks(session: Session) -> dict:
    """Creates the weekly picks page"""
    info: TGFPInfo = get_tgfp_info()
    week_no: int = info.current_week
    nfl: TgfpNfl = TgfpNfl(week_no=week_no)
    nfl_games: List[TgfpNflGame] = nfl.games()
    if not nfl_games:
        raise CreatePicksException("There should have been games!!!")
    nfl_game: TgfpNflGame
    for nfl_game in nfl_games:
        tgfp_game = game_from_nfl_game(nfl_game=nfl_game, session=session, info=info)
        session.add(tgfp_game)
    session.commit()
    # send_campaign_email(week_no)
    # send_discord_msg(week_no)
    return {"success": True}


if __name__ == "__main__":
    with Session(engine) as a_session:
        create_picks(session=a_session)
