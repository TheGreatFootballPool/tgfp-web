"""
An idempotent script that will scan the playergamepicks and award
the player who got the first pick for the week the 'quick pick' award
"""

from sqlmodel import Session, select

from models import PlayerGamePick, Player, Game, AwardSlug
from models.award_helpers import upsert_award_with_args
from models.model_helpers import current_nfl_season


def sync_in_your_face(week_no: int, session: Session) -> list[Player] | None:
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
            player: Player = winners[0]
            upsert_award_with_args(
                session=session,
                player_id=player.id,
                slug=AwardSlug.IN_YOUR_FACE,
                season=current_nfl_season(),
                week_no=week_no,
                game_id=game.id,
            )
