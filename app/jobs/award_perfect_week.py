"""
An idempotent script that will scan the playergamepicks and award
the player who had a PERFECT WEEK (no losses)
"""

import logging
from sqlmodel import Session

from db import engine
from models import Player


def find_players_with_perfect_week(
    week_no: int, session: Session
) -> list[Player] | None:
    """

    :param week_no: Week number to query
    :type week_no: int
    :param session: Active database session
    :type session: Session
    :return: a list of players who have perfect week
    :rtype: list[Player]
    """
    active_players: list[Player] = Player.active_players(session=session)
    players: list[Player] = []
    if len(active_players) < 2:
        logging.error("Too few players")
        raise Exception("Too few players")
    for p in active_players:
        if p.losses(week_no=week_no) == 0:
            players.append(p)
    return players


if __name__ == "__main__":
    with Session(engine) as s:
        perfect_players = find_players_with_perfect_week(week_no=2, session=s)
        for player in perfect_players:
            print(player.nick_name, player.total_points(week_no=2))
