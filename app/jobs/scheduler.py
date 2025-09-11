from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session
from pytz import timezone

from models import Game
from config import Config
from models.model_helpers import current_nfl_season

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


def schedule_nag_players():
    """Creates the flows for nagging players"""
    with Session(engine) as session:
        first_game: Game = Game.get_first_game_of_the_week(session)
        for delta in [60, 20, 7]:
            d: datetime = first_game.utc_start_time - timedelta(hours=0, minutes=delta)
            now_utc = datetime.now(ZoneInfo("UTC"))
            if now_utc >= d:
                continue
            current_season: str = str(current_nfl_season())
            job_id: str = f"s{current_season}:w{first_game.week_no}:d{delta}"
            job_name: str = f"{delta} minutes before kickoff"
            trigger: DateTrigger = DateTrigger(run_date=d)
            job = job_scheduler.get_job(job_id)
            if job:
                job_scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                job_scheduler.add_job(
                    "app.jobs.nag_players:nag_the_players",
                    name=job_name,
                    trigger=trigger,
                    id=job_id,
                )


def schedule_update_games():
    """Creates the flows for updating games"""
    with Session(engine) as session:
        this_weeks_games: List[Game] = Game.games_for_week(session)
        for game in this_weeks_games:
            current_season: str = str(current_nfl_season())
            job_id: str = f"s{current_season}:w{game.week_no}:g{game.id}"

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
                    "app.jobs.update_game:update_a_game",
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
        job_scheduler.add_job(
            "app.jobs.create_picks:create_the_picks", trigger=trigger, id="create_picks"
        )


def schedule_sync_team_records():
    pacific = timezone("America/Los_Angeles")
    trigger = CronTrigger(day_of_week="tue", hour=4, minute=0, timezone=pacific)
    job = job_scheduler.get_job("sync_team_records")
    if job:
        job_scheduler.reschedule_job("sync_team_records", trigger=trigger)
    else:
        job_scheduler.add_job(
            "app.jobs.sync_team_records:sync_the_team_records",
            trigger=trigger,
            id="sync_team_records",
        )


async def schedule_jobs():
    schedule_nag_players()
    schedule_update_games()
    schedule_create_picks()
    schedule_sync_team_records()
