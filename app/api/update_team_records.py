""" Loop through all the teams, and update their record for the week """
import asyncio
from typing import List

from tgfp_nfl import TgfpNfl
from models import TGFPInfo, get_tgfp_info, Team, db_init
from config import Config


async def update_team_records():
    """
    Update all the wins / losses / ties of each team
    """
    info: TGFPInfo = await get_tgfp_info()
    nfl_data_source = TgfpNfl(week_no=info.display_week)
    teams: List[Team] = await Team.find_all().to_list()
    for nfl_team in nfl_data_source.teams():
        for team in teams:
            if team.tgfp_nfl_team_id == nfl_team.id:
                team.wins = nfl_team.wins
                team.losses = nfl_team.losses
                team.ties = nfl_team.ties
                team.logo_url = nfl_team.logo_url
                # noinspection PyArgumentList
                await team.save()
                break


async def main():
    """ Here so that I can run this manually if I need to """
    config: Config = Config.get_config()
    await db_init(config)
    await update_team_records()


if __name__ == '__main__':
    asyncio.run(main())
