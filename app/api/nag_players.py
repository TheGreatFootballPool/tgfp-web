"""This example requires the 'message_content' intent."""

import datetime
from typing import List, Optional

import arrow
from discord_webhook import DiscordWebhook

from models import Game, Player
from config import Config


def get_minutes_to_kickoff(game: Game) -> int:
    """Returns the number of minutes before the scheduled kickoff of the given game"""
    game_1_start = arrow.get(game.start_time)
    delta: datetime.timedelta = game_1_start - arrow.utcnow()
    return round(delta.seconds / 60)


async def get_late_players() -> List[Player]:
    """Returns a list of players that have not yet put their picks in for the week"""
    late_players: List[Player] = []
    players: List[Player] = await Player.find_all(fetch_links=True).to_list()
    for player in players:
        player_has_picks: bool = False
        for pick in player.picks:
            if pick.week_no == info.display_week:
                player_has_picks = True
        if player.active and not player_has_picks:
            late_players.append(player)
    return late_players


async def get_nag_payload(info: TGFPInfo) -> Optional[str]:
    """Gets the embed message to send to the server"""
    late_players = await get_late_players(info)
    message: Optional[str] = None
    if late_players:
        first_game: Game = await Game.get_first_game_of_the_week(info)
        kickoff_in_minutes = get_minutes_to_kickoff(first_game)
        message = "This is the TGFP NagBot with a friendly reminder to the following:\n"
        for player in late_players:
            message += f"• <@{player.discord_id}>\n"
        message += "\nYou still need to enter your picks."
        message += " Go to https://tgfp.us/picks and get 'em in!"
        message += f"\nKickoff of first game is in {kickoff_in_minutes} minutes!"
    return message


async def nag_players(info: TGFPInfo):
    """Sends a message to the players"""
    config: Config = Config.get_config()
    nag_payload = await get_nag_payload(info)
    if nag_payload:
        webhook = DiscordWebhook(
            url=config.DISCORD_NAG_BOT_WEBHOOK_URL, content=nag_payload
        )
        webhook.execute()
