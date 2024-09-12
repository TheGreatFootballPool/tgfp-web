import asyncio
from typing import List

from fontTools.merge.util import first

from config import Config
from models import Player, TGFPInfo, get_tgfp_info, Pick, db_init


async def main():
    config: Config = Config.get_config()
    await db_init(config)
    info: TGFPInfo = await get_tgfp_info()
    week_no: int = info.active_week
    players: List[Player] = await Player.find_many(
        Player.active == True,
        fetch_links=True
    ).to_list()
    players_with_picks: List[Player] = []
    for player in players:
        pick: Pick = player.pick_for_week(week_no)
        if pick:
            if pick.created_at:
                players_with_picks.append(player)

    if players_with_picks:
        first_player: Player = players_with_picks[0]
        for player in players_with_picks:
            if player.pick_for_week(week_no).created_at < first_player.pick_for_week(week_no).created_at:
                first_player = player
        print(first_player)
    else:
        print("nobody has entered their picks yet")

if __name__ == '__main__':
    asyncio.run(main())

