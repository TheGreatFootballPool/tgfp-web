"""
An idempotent script that will scan the playergamepicks and award
the player who got the first pick for the week the 'quick pick' award
"""

from sqlmodel import Session, select

from db import engine
from models import PlayerGamePick, Player, Game
from models.model_helpers import current_nfl_season


def find_in_your_face(week_no: int, session: Session) -> list[Player] | None:
    games: list[Game] = Game.games_for_week(
        session=session, season=current_nfl_season(), week_no=week_no
    )
    for game in games:
        statement = select(PlayerGamePick).where(PlayerGamePick.game_id == game.id)
        picks: list[PlayerGamePick] = list(session.exec(statement).all())
        winners: list[Player] = []
        for pick in picks:
            if pick.is_win:
                winners.append(pick.player)
        if len(winners) == 1:
            print(f"Got an In Your Face: {winners[0].nick_name} for game {game.id}")


if __name__ == "__main__":
    with Session(engine) as s:
        find_in_your_face(week_no=1, session=s)
