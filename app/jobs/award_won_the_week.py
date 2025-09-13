"""
An idempotent script that will scan the playergamepicks and award
the player who had the best week, but only if no other player tied them.
"""

import logging
from sqlmodel import Session

from db import engine
from models import Player


def find_player_with_most_wins(week_no: int, session: Session) -> Player | None:
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
        logging.error("Too few players")
        raise Exception("Too few players")
    sorted_players = sorted(
        active_players, key=lambda p: p.wins(week_no=week_no), reverse=True
    )
    top_total_points = sorted_players[0].total_points(week_no=week_no)
    if top_total_points > sorted_players[1].total_points(week_no=week_no):
        return sorted_players[0]
    return None


if __name__ == "__main__":
    with Session(engine) as s:
        top_player = find_player_with_most_wins(week_no=2, session=s)
        if top_player:
            print(top_player.nick_name)
