from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session
from pytz import timezone

from jobs import create_picks, update_game, nag_players
from models import Game
from config import Config
from models.model_helpers import TGFPInfo, get_tgfp_info

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from db import scheduler_engine, engine

jobstores = {"default": SQLAlchemyJobStore(engine=scheduler_engine)}
executors = {"default": ThreadPoolExecutor(16)}
job_defaults = {"coalesce": False, "max_instances": 1}

job_scheduler = AsyncIOScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC"
)

config: Config = Config.get_config()


def schedule_nag_players(info: TGFPInfo):
    """Creates the flows for nagging players"""
    with Session(engine) as session:
        session.info["TGFPInfo"] = info
        first_game: Game = Game.get_first_game_of_the_week(session)
        for delta in [60, 20, 7]:
            d: datetime = first_game.utc_start_time - timedelta(hours=0, minutes=delta)
            now_utc = datetime.now(ZoneInfo("UTC"))
            if now_utc >= d:
                continue
            job_id: str = f"s{info.current_season}:w{info.current_week}:d{delta}"
            job_name: str = f"{delta} minutes before kickoff"
            trigger: DateTrigger = DateTrigger(run_date=d)
            job = job_scheduler.get_job(job_id)
            if job:
                job_scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                job_scheduler.add_job(
                    nag_players, name=job_name, trigger=trigger, id=job_id
                )


def schedule_update_games(info: TGFPInfo):
    """Creates the flows for updating games"""
    with Session(engine) as session:
        session.info["TGFPInfo"] = info
        this_weeks_games: List[Game] = Game.games_for_week(session)
        for game in this_weeks_games:
            job_id: str = f"s{info.current_season}:w{info.current_week}:g{game.id}"

            # Use UTC for scheduling to avoid tzlocal/pytz issues
            now_utc = datetime.now(ZoneInfo("UTC"))
            kickoff_utc = game.utc_start_time  # should be tz-aware UTC
            end_date = kickoff_utc + timedelta(hours=8)

            # Decide the start date: if kickoff has passed
            if kickoff_utc <= now_utc:
                if game.is_final:
                    continue
                # Not final: start polling now (plus a tiny delay) so there's always a next run
                start_date = now_utc + timedelta(seconds=5)
            else:
                # Future kickoff: start at kickoff time
                start_date = kickoff_utc

            # Safety: if the computed window is invalid, do not schedule
            if end_date <= start_date:
                continue

            job_name: str = (
                f"{game.road_team.full_name} @ "
                f"{game.home_team.full_name}: "
                f"{start_date.strftime('%b %d, %Y %H:%M')}"
            )
            trigger: IntervalTrigger = IntervalTrigger(
                minutes=5, start_date=start_date, end_date=end_date, jitter=60
            )
            job = job_scheduler.get_job(job_id)
            if job:
                job_scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                job_scheduler.add_job(
                    update_game,
                    name=job_name,
                    trigger=trigger,
                    id=job_id,
                    args=[game.id],
                )


def schedule_create_picks():
    pacific = timezone("America/Los_Angeles")
    trigger = CronTrigger(day_of_week="wed", hour=6, minute=0, timezone=pacific)
    job = job_scheduler.get_job("create_picks")
    if job:
        job_scheduler.reschedule_job("create_picks", trigger=trigger)
    else:
        job_scheduler.add_job(create_picks, trigger=trigger, id="create_picks")


async def schedule_jobs():
    info: TGFPInfo = get_tgfp_info()
    schedule_nag_players(info)
    schedule_update_games(info)
    schedule_create_picks()
