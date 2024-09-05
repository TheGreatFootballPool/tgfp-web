"""This example requires the 'message_content' intent."""
import asyncio
import datetime
from typing import List, Optional

import arrow
import sentry_sdk
from paho.mqtt import client as mqtt_client
from discord_webhook import DiscordWebhook
import nest_asyncio

from models import Game, Player, db_init, TGFPInfo, get_tgfp_info
from config import Config

nest_asyncio.apply()

CONFIG = Config.get_config()


def connect_mqtt():
    """ Connect to the mqtt broker """
    # noinspection PyArgumentList
    client = mqtt_client.Client(
        client_id='tgfp-mqtt-nag-bot',
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(CONFIG.MQTT_USERNAME, CONFIG.MQTT_PASSWORD)
    # client.on_connect = on_connect
    client.connect(CONFIG.MQTT_HOST)
    return client


def subscribe(client: mqtt_client):
    """ Subscribe to topics """
    def on_message(_, __, msg):
        if msg.topic == f"{CONFIG.MQTT_TOPIC}/nag-bot":
            loop = asyncio.get_event_loop()
            nag_payload = loop.run_until_complete(get_nag_payload())
            if nag_payload:
                webhook = DiscordWebhook(
                    url=CONFIG.DISCORD_NAG_BOT_WEBHOOK_URL,
                    content=nag_payload
                )
                webhook.execute()

    client.subscribe(f"{CONFIG.MQTT_TOPIC}/#")
    client.on_message = on_message


async def get_first_game_of_the_week(info: TGFPInfo) -> Game:
    """ Returns the 'first' game of the week """
    games: List[Game] = await Game.find_many(
        Game.season == info.season, Game.week_no == info.display_week
    ).to_list()
    games.sort(key=lambda x: x.start_time, reverse=True)
    return games[-1]


async def get_nag_payload() -> Optional[str]:
    """ Gets the embed message to send to the server """
    print("Getting nag payload")
    info: TGFPInfo = await get_tgfp_info()
    first_game: Game = await get_first_game_of_the_week(info)
    game_1_start = arrow.get(first_game.start_time)
    delta: datetime.timedelta = game_1_start - arrow.utcnow()
    kickoff_in_minutes: int = round(delta.seconds / 60)
    late_players: List[Player] = []
    message: Optional[str] = None
    players: List[Player] = await Player.find_all(fetch_links=True).to_list()
    for player in players:
        player_has_picks: bool = False
        for pick in player.picks:
            if pick.week_no == info.display_week:
                player_has_picks = True
        if player.active and not player_has_picks:
            late_players.append(player)

    if late_players:
        message = "This is the TGFP NagBot with a friendly reminder to the following:\n"
        for player in late_players:
            message += f"• <@{player.discord_id}>\n"
        message += "\nYou still need to enter your picks."
        message += " Go to https://tgfp.us/picks and get 'em in!"
        message += f"\nKickoff of first game is in {kickoff_in_minutes} minutes!"
    else:
        if CONFIG.ENVIRONMENT == 'development':
            message = "No players to nag"
    return message


async def main():
    """ Main method """
    sentry_sdk.init(
        dsn=CONFIG.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    await db_init(CONFIG)
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    asyncio.run(main())
