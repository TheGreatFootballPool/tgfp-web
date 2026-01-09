import logging

from sqlmodel import Session, select

from db import engine
from espn_nfl import ESPNNfl
from jobs.award_notify_discord import send_award_notification
from models import Game, PlayerGamePick, AwardSlug, Player
from models.award_helpers import upsert_award_with_args
from models.model_helpers import WeekInfo


def _games_exist_and_all_games_are_final(week_info: WeekInfo, session: Session) -> bool:
    statement = select(Game).where(
        Game.season == week_info.season,
        Game.season_type == week_info.season_type,
        Game.week_no == week_info.week_no,
    )
    games: list[Game] = list(session.exec(statement).all())
    if not games:
        return False
    for game in games:
        if not game.is_final:
            return False
    return True


def sync_won_the_week(week_info: WeekInfo, session: Session):
    active_players: list[Player] = Player.active_players(session=session)
    if len(active_players) < 2:
        raise Exception("Too few players")
    sorted_players = sorted(
        active_players, key=lambda p: p.wins_for_week(week_info), reverse=True
    )
    top_total_points = sorted_players[0].total_points_for_week(week_info=week_info)
    if top_total_points > sorted_players[1].total_points_for_week(week_info=week_info):
        player = sorted_players[0]
        upsert_award_with_args(
            session=session,
            player_id=player.id,
            slug=AwardSlug.WON_THE_WEEK,
            week_info=week_info,
        )


def sync_in_your_face(week_info: WeekInfo, session: Session):
    games: list[Game] = Game.games_for_week(week_info=week_info, session=session)
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
                week_info=week_info,
                game_id=game.id,
            )


def sync_perfect_week(week_info: WeekInfo, session: Session):
    active_players: list[Player] = Player.active_players(session=session)
    if len(active_players) < 2:
        logging.error("Too few players")
        raise Exception("Too few players")
    for player in active_players:
        losses: int = player.losses_for_week(week_info=week_info)
        wins: int = player.wins_for_week(week_info=week_info)
        if losses == 0 and wins > 0:
            upsert_award_with_args(
                session=session,
                player_id=player.id,
                slug=AwardSlug.PERFECT_WEEK,
                week_info=week_info,
            )


def sync_quick_pick(week_info: WeekInfo, session: Session) -> bool:
    picks = PlayerGamePick.find_picks_for_week(week_info=week_info, session=session)
    picks.sort(key=lambda x: x.created_at, reverse=False)
    if len(picks):
        pick: PlayerGamePick = picks[0]
        upsert_award_with_args(
            session=session,
            player_id=pick.player_id,
            slug=AwardSlug.QUICK_PICK,
            week_info=week_info,
        )


def update_all_awards():
    logging.debug("Updating all awards")
    espn_nfl: ESPNNfl = ESPNNfl()
    season_types = espn_nfl.SEASON_TYPES
    with Session(engine) as session:
        for season_type in season_types:
            for week_no in range(1, season_type.weeks + 1):
                week_info: WeekInfo = WeekInfo(
                    season_type=season_type.type_id,
                    season=espn_nfl.season,
                    week_no=week_no,
                )
                if not _games_exist_and_all_games_are_final(
                    week_info=week_info, session=session
                ):
                    return  # Early Return when done
                sync_perfect_week(week_info=week_info, session=session)
                sync_in_your_face(week_info=week_info, session=session)
                sync_quick_pick(week_info=week_info, session=session)
                sync_won_the_week(week_info=week_info, session=session)
        send_award_notification(session=session)
