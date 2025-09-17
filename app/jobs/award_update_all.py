import logging

from sqlmodel import Session, select

from db import engine
from models import Game, PlayerGamePick, AwardSlug, Player
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


def sync_quick_pick(week_no: int, session: Session) -> bool:
    picks = PlayerGamePick.find_picks(
        season=current_nfl_season(), week_no=week_no, session=session
    )
    did_update: bool = False
    picks.sort(key=lambda x: x.created_at, reverse=False)
    if len(picks):
        pick: PlayerGamePick = picks[0]
        did_update = upsert_award_with_args(
            session=session,
            player_id=pick.player_id,
            slug=AwardSlug.QUICK_PICK,
            season=current_nfl_season(),
            week_no=week_no,
        )
    return did_update


def update_all_awards():
    with Session(engine) as session:
        for week_no in range(1, Game.most_recent_week(session) + 1):
            sync_perfect_week(week_no=week_no, session=session)
            sync_in_your_face(week_no=week_no, session=session)
            sync_quick_pick(week_no=week_no, session=session)
            sync_won_the_week(week_no=week_no, session=session)
