""" Script will give me the player with the first pick for the current week """
import asyncio
from typing import List

from models import Player, Pick, db_init, Award, PlayerAward, Game, Team
from config import Config


async def in_your_face(week_no: int, season: int):
    """ Determine if there is an in your face pick for the week """
    # first let's see if there is a game with an IYF
    config: Config = Config.get_config()
    await db_init(config)
    players: List[Player] = await Player.active_players(fetch_links=True)
    teams: List[Team] = await Team.find_all().to_list()
    award: Award = await Award.find_one(Award.name == 'Quick Pick')
    games: List[Game] = await Game.find_many(
        Game.week_no == week_no,
        Game.season == season,
        fetch_links=True
    ).to_list()
    for game in games:
        if game.winning_team is None:
            # raise Exception("All games should have winners!")
            continue

        winning_players: List[Player] = []
        player: Player
        for player in players:
            pick: Pick = player.pick_for_week(week_no)
            if pick and pick.winning_team_for_game(game, teams).id == game.winning_team.id:
                winning_players.append(player)

        if len(winning_players) == 1:
            award: Award = await Award.find_one(Award.name == 'In Your Face')
            player_award: PlayerAward = PlayerAward(
                award=award,
                player=winning_players[0],
                week_no=week_no,
                season=season
            )
            # noinspection PyArgumentList
            await player_award.save()

            print("In Your Face!!!")
        else:
            print(f"ho hum: {len(winning_players)}")



async def won_the_week(week_no: int, season: int):
    """ Determine if there was a 'won the week' award for the week """


async def quick_pick(week_no: int, season: int):
    """ Main method """
    config: Config = Config.get_config()
    await db_init(config)
    players: List[Player] = await Player.active_players(fetch_links=True)
    players_with_picks: List[Player] = []
    award: Award = await Award.find_one(Award.name == 'Quick Pick')
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
        player_award: PlayerAward = PlayerAward(
            award=award,
            player=first_player,
            week_no=week_no,
            season=season
        )
        # noinspection PyArgumentList
        await player_award.save()

if __name__ == '__main__':
    # asyncio.run(quick_pick(2, season=2024))
    asyncio.run(in_your_face(2, season=2024))
