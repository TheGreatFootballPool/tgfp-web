"""
An idempotent script that will scan the playergamepicks and award
the player who had the best week, but only if no other player tied them.
"""

from sqlmodel import Session

from models import Player, AwardSlug
from models.award_helpers import upsert_award_with_args
from models.model_helpers import current_nfl_season


def sync_won_the_week(week_no: int, session: Session) -> Player | None:
    """

    :param week_no: Week number to query
    :type week_no: int
    :param session: Active database session
    :type session: Session
    :return: Player or None if no player won the week
    :rtype: Player | None
    """
    active_players: list[Player] = Player.active_players(session=session)
    if len(active_players) < 2:
        raise Exception("Too few players")
    sorted_players = sorted(
        active_players, key=lambda p: p.wins(week_no=week_no), reverse=True
    )
    top_total_points = sorted_players[0].total_points(week_no=week_no)
    if top_total_points > sorted_players[1].total_points(week_no=week_no):
        player = sorted_players[0]
        upsert_award_with_args(
            session=session,
            player_id=player.id,
            slug=AwardSlug.WON_THE_WEEK,
            season=current_nfl_season(),
            week_no=week_no,
        )
