""" Take a game, and get the current scores from TgfpNfl and update the TGFP game """
from typing import List

from tgfp_nfl import TgfpNfl

from models import TGFPInfo, get_tgfp_info, Game, Player


async def update_game(game: Game) -> Game:
    """
    Update all the wins / losses / scores, etc...
    @param game:
    @return: The current live status of the game
    """
    info: TGFPInfo = await get_tgfp_info()
    nfl_data_source = TgfpNfl(week_no=info.display_week)
    await _update_scores(nfl_data_source, game)
    if game.is_final:
        await _update_player_win_loss()
    return game


async def _update_scores(nfl_data_source, game: Game) -> str:
    """
    Update the tgfp_game with the data from the nfl data source
    @param nfl_data_source: current nfl game day data
    @param game: game to update
    @return: Status of the game
    """
    nfl_game = nfl_data_source.find_game(nfl_game_id=game.tgfp_nfl_game_id)
    game.home_team_score = int(nfl_game.total_home_points)
    game.road_team_score = int(nfl_game.total_away_points)
    game.game_status = nfl_game.game_status_type
    # noinspection PyArgumentList
    await game.save()
    return game.game_status


async def _update_player_win_loss():
    # pylint: disable=singleton-comparison
    active_players: List[Player] = await Player.find_many(
        Player.active == True  # noqa E712
    ).to_list()
    player: Player
    for player in active_players:
        await player.fetch_pick_links()
        for pick in player.picks:
            pick.load_record()
        # noinspection PyArgumentList
        await player.save()
