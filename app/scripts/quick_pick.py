""" Script will give me the player with the first pick for the current week """
import asyncio
from typing import List

from models import Player, Pick, db_init
from config import Config


async def main(week_no: int):
    """ Main method """
    config: Config = Config.get_config()
    await db_init(config)
    players: List[Player] = await Player.active_players(fetch_links=True)
    players_with_picks: List[Player] = []
    for player in players:
        pick: Pick = player.pick_for_week(week_no)
        if pick:
            if pick.created_at:
                players_with_picks.append(player)

    if players_with_picks:
        first_player: Player = players_with_picks[0]
        for player in players_with_picks:
            if (player.pick_for_week(week_no).created_at <
                    first_player.pick_for_week(week_no).created_at):
                first_player = player
        print(first_player)
    else:
        print("nobody has entered their picks yet")

if __name__ == '__main__':
    asyncio.run(main(3))
