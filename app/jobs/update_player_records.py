from sqlmodel import Session

from models import Game, Player
from models.model_helpers import WeekInfo


def update_player_records(session: Session):
    week_infos: list[WeekInfo] = Game.get_distinct_week_infos(session=session)
    for player in Player.active_players(session=session):
        player.wins = 0
        player.losses = 0
        player.bonus = 0
        for week_info in week_infos:
            player.wins += player.wins_for_week(week_info=week_info)
            player.losses += player.losses_for_week(week_info=week_info)
            player.bonus += player.bonus_for_week(week_info=week_info)
        session.add(player)
    session.commit()
