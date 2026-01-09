"""This example requires the 'message_content' intent."""

import datetime
import logging

import humanize
from typing import List, Optional

import arrow
from discord_webhook import DiscordWebhook
from sqlmodel import Session

from db import engine
from models import Game, Player
from config import Config
from models.model_helpers import WeekInfo, current_week_info


def get_time_to_kickoff(game: Game) -> str:
    """Returns the humanized time until scheduled kickoff of the given game"""
    game_1_start = arrow.get(game.start_time)
    delta: datetime.timedelta = game_1_start - arrow.utcnow()
    return humanize.precisedelta(delta, suppress=["seconds"], format="%1.f")


def get_late_players(session: Session, week_info: WeekInfo) -> List[Player]:
    """Returns a list of players that have not yet put their picks in for the week"""
    late_players: List[Player] = []
    players: List[Player] = Player.active_players(session=session)
    for player in players:
        if not player.picks_for_week(week_info=week_info):
            late_players.append(player)
    return late_players


def get_nag_payload(session, week_info: WeekInfo) -> Optional[str]:
    """Gets the embed message to send to the server"""
    late_players = get_late_players(session=session, week_info=week_info)
    message: Optional[str] = None
    if late_players:
        first_game: Game = Game.get_first_game_of_the_week(
            session=session, week_info=week_info
        )
        time_to_kickoff = get_time_to_kickoff(first_game)
        message = "This is the TGFP NagBot with a friendly reminder to the following:\n"
        for player in late_players:
            logging.debug("Player: {name} needs to be nagged", name=player.nick_name)  # type: ignore[arg-type]
            message += f"• <@{player.discord_id}>\n"
        message += "\nYou still need to enter your picks."
        message += " Go to https://tgfp.us/picks and get 'em in!"
        message += f"\nKickoff of first game is in {time_to_kickoff}!"
    return message


def nag_the_players():
    """Sends a message to the players"""
    logging.info("NagBot starting")
    config: Config = Config.get_config()
    nag_payload = None
    week_info: WeekInfo = current_week_info()
    with Session(engine) as session:
        nag_payload = get_nag_payload(session=session, week_info=week_info)
    if nag_payload:
        webhook = DiscordWebhook(
            url=config.DISCORD_NAG_BOT_WEBHOOK_URL, content=nag_payload
        )
        webhook.execute()


if __name__ == "__main__":
    nag_the_players()
