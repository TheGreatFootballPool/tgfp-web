"""
An idempotent script that will scan the playergamepicks and award
the player who had a PERFECT WEEK (no losses)
"""

import logging
from sqlmodel import Session

from models import Player, AwardSlug
from models.award_helpers import upsert_award_with_args
from models.model_helpers import current_nfl_season


def sync_perfect_week(week_no: int, session: Session) -> list[Player] | None:
    active_players: list[Player] = Player.active_players(session=session)
    if len(active_players) < 2:
        logging.error("Too few players")
        raise Exception("Too few players")
    for player in active_players:
        if player.losses(week_no=week_no) == 0:
            upsert_award_with_args(
                session=session,
                player_id=player.id,
                slug=AwardSlug.PERFECT_WEEK,
                season=current_nfl_season(),
                week_no=week_no,
            )
