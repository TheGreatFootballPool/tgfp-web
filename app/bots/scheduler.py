from datetime import datetime, timedelta
from typing import List
from sqlmodel import Session

from bots.update_scores import update_game
from models import Game
from config import Config
from models.model_helpers import TGFPInfo, get_tgfp_info

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from db import scheduler_engine, engine
from bots.nag_players import nag_players

jobstores = {"default": SQLAlchemyJobStore(engine=scheduler_engine)}
executors = {"default": ThreadPoolExecutor(16)}
job_defaults = {"coalesce": False, "max_instances": 1}

scheduler = AsyncIOScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC"
)

config: Config = Config.get_config()


async def schedule_nag_players(info: TGFPInfo):
    """Creates the flows for nagging players"""
    with Session(engine) as session:
        session.info["TGFPInfo"] = info
        first_game: Game = Game.get_first_game_of_the_week(session)
        for delta in [60, 20, 7]:
            d: datetime = first_game.utc_start_time - timedelta(hours=0, minutes=delta)
            job_id: str = f"s{info.current_season}:w{info.current_week}:d{delta}"
            job_name: str = f"{delta} minutes before kickoff"
            trigger: DateTrigger = DateTrigger(run_date=d)
            job = scheduler.get_job(job_id)
            if job:
                scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                scheduler.add_job(
                    nag_players, name=job_name, trigger=trigger, id=job_id
                )


async def schedule_update_games(info: TGFPInfo):
    """Creates the flows for updating games"""
    with Session(engine) as session:
        session.info["TGFPInfo"] = info
        this_weeks_games: List[Game] = Game.games_for_week(session)
        for game in this_weeks_games:
            start_date = game.pacific_start_time
            end_date = start_date + timedelta(hours=6)
            job_id: str = f"s{info.current_season}:w{info.current_week}:g{game.id}"
            job_name: str = (
                f"{game.road_team.full_name} @ "
                f"{game.home_team.full_name}: "
                f"{start_date.strftime('%b %d, %Y %H:%M')}"
            )
            trigger: IntervalTrigger = IntervalTrigger(
                minutes=5, start_date=start_date, end_date=end_date, jitter=60
            )
            job = scheduler.get_job(job_id)
            if job:
                scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                scheduler.add_job(
                    update_game,
                    name=job_name,
                    trigger=trigger,
                    id=job_id,
                    args=[game.id],
                )


async def schedule_jobs():
    info: TGFPInfo = get_tgfp_info()
    await schedule_nag_players(info)
    await schedule_update_games(info)
