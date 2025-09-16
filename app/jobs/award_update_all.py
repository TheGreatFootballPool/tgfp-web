from sqlmodel import Session

from db import engine
from jobs.award_in_your_face import sync_in_your_face
from jobs.award_perfect_week import sync_perfect_week
from jobs.award_quick_pick import sync_quick_pick
from jobs.award_won_the_week import sync_won_the_week
from models import Game


def main():
    with Session(engine) as s:
        for week_no in range(1, Game.most_recent_week(s) + 1):
            sync_perfect_week(week_no=week_no, session=s)
            sync_in_your_face(week_no=week_no, session=s)
            sync_quick_pick(week_no=week_no, session=s)
            sync_won_the_week(week_no=week_no, session=s)


if __name__ == "__main__":
    main()
