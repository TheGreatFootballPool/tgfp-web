""" Schedule all Kestra Flows """
import os
from datetime import datetime, timedelta
from typing import List

from string import Template
import requests

from models import TGFPInfo, Game
from config import Config

dir_path = os.path.dirname(os.path.realpath(__file__))
template_folder = os.path.join(dir_path, 'templates')

config: Config = Config.get_config()


def create_flow(flow: str):
    """
    Create the flow string
    :param flow: Creates the flow string
    :return: None
    """
    try:
        # noinspection HttpUrlsUsage
        requests.post(
            url=f"http://{config.KESTRA_HOST}/api/v1/flows",
            timeout=30,
            headers={
                "Content-Type": "application/x-yaml",
            },
            data=flow)
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


def delete_last_weeks_flows():
    """ Deletes last weeks flows """
    try:
        # noinspection HttpUrlsUsage
        requests.delete(
            url=f"http://{config.KESTRA_HOST}/api/v1/flows/delete/by-query",
            timeout=30,
            params={
                "namespace": f"{config.KESTRA_NAMESPACE}.weekly",
            },
        )
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


async def schedule_nag_players(info: TGFPInfo):
    """ Creates the flows for nagging players """
    first_game: Game = await Game.get_first_game_of_the_week(info)
    for delta in [60, 20, 7]:
        d: datetime = first_game.pacific_start_time - timedelta(hours=0, minutes=delta)
        with open(f"{template_folder}/nag_player_flow.yml", 'r', encoding='utf-8') as f:
            src = Template(f.read())
            result = src.substitute(
                flow_id=f"nag_flow_{delta}",
                namespace=f"{config.KESTRA_NAMESPACE}.weekly",
                uri=f"{config.API_BASE_URL}/nag_players",
                cron=f"{d.minute} {d.hour} {d.day} {d.month} *"
            )
        create_flow(result)


async def schedule_update_games(info: TGFPInfo):
    """ Creates the flows for updating games """
    this_weeks_games: List[Game] = await Game.find_many(
        Game.week_no == info.display_week,
        Game.season == info.season,
        fetch_links=True
    ).to_list()
    for game in this_weeks_games:
        d = game.pacific_start_time
        with open(f"{template_folder}/game_update_flow.yml", 'r', encoding='utf-8') as f:
            src = Template(f.read())
            result = src.substitute(
                flow_id=f"update_game_{game.road_team.short_name}_{game.home_team.short_name}",
                namespace=f"{config.KESTRA_NAMESPACE}.weekly",
                uri=f"{config.API_BASE_URL}/update_game/{game.id}",
                cron=f"{d.minute} {d.hour} {d.day} {d.month} *"
            )
        create_flow(result)


async def schedule_kestra_flows(info: TGFPInfo):
    """ main logic for scheduling all the kestra flows """
    delete_last_weeks_flows()
    await schedule_nag_players(info)
    await schedule_update_games(info)
