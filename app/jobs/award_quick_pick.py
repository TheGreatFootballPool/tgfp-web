"""
An idempotent script that will scan the playergamepicks and award
the player who got the first pick for the week the 'quick pick' award
"""

from sqlmodel import Session

from models import PlayerGamePick, AwardSlug
from models.award_helpers import upsert_award_with_args
from models.model_helpers import current_nfl_season


def sync_quick_pick(week_no: int, session: Session):
    picks = PlayerGamePick.find_picks(
        season=current_nfl_season(), week_no=week_no, session=session
    )
    picks.sort(key=lambda x: x.created_at, reverse=False)
    if len(picks):
        pick: PlayerGamePick = picks[0]
        upsert_award_with_args(
            session=session,
            player_id=pick.player_id,
            slug=AwardSlug.QUICK_PICK,
            season=current_nfl_season(),
            week_no=week_no,
        )
