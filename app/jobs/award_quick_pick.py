"""
An idempotent script that will scan the playergamepicks and award
the player who got the first pick for the week the 'quick pick' award
"""

from sqlmodel import Session

from db import engine
from models import PlayerGamePick
from models.model_helpers import current_nfl_season


def find_quick_pick_for_week(week_no: int, session: Session):
    picks = PlayerGamePick.find_picks(
        season=current_nfl_season(), week_no=week_no, session=session
    )
    picks.sort(key=lambda x: x.created_at, reverse=False)
    if len(picks):
        pick: PlayerGamePick = picks[0]
        print(f"Player with first pick for week {week_no}: {pick.player.first_name}")


if __name__ == "__main__":
    with Session(engine) as s:
        find_quick_pick_for_week(week_no=3, session=s)
