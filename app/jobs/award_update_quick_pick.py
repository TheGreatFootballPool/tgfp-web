from sqlmodel import Session

from db import engine
from jobs.award_update_all import sync_quick_pick
from models import Game


def update_quick_pick():
    did_update: bool = False
    with Session(engine) as session:
        for week_no in range(1, Game.most_recent_week(session) + 1):
            did_update = sync_quick_pick(week_no=week_no, session=session)
    if did_update:
        pass
        # TODO: Ping discord with the quick pick award notice (See #150)
