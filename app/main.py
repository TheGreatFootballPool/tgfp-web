"""Main entry point for website"""

from datetime import datetime
import os
from contextlib import asynccontextmanager
from typing import Optional, List

from pytz import timezone
import sqlalchemy.exc

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlmodel import Session, select
from db import engine
from models import Player, PlayerGamePick, Team, Game, Award
from jobs.scheduler import schedule_jobs, job_scheduler
from models.award_helpers import init_award_table
from app.routers import auth, mail, admin
from apscheduler.triggers.cron import CronTrigger

from config import Config
from models.model_helpers import current_week_info, WeekInfo

config = Config.get_config()


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
):
    job_scheduler.start()
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        # Add data like request headers and IP for users, if applicable;
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        max_request_body_size="always",
        # Setting up the release is highly recommended. The SDK will try to
        # infer it, but explicitly setting it is more reliable:
        release=config.APP_VERSION,
        environment=config.ENVIRONMENT,
        traces_sample_rate=0.01,
        # Enable structured logging (allows sentry_sdk.logger at any level)
        enable_logs=True,
        # Block automatic INFO logs from uvicorn, but allow explicit sentry_sdk.logger calls
        integrations=[
            LoggingIntegration(
                level="WARNING",  # Only capture WARNING+ from standard Python logging
                event_level="WARNING",  # Only send WARNING+ as events
                sentry_logs_level=None,  # Don't automatically capture logs from standard loggers
            ),
        ],
    )
    init_award_table()
    try:
        pacific = timezone("America/Los_Angeles")
        trigger = CronTrigger(day_of_week="wed", hour=7, minute=0, timezone=pacific)
        job_scheduler.add_job(
            "app.jobs.scheduler:schedule_jobs_current_week",
            trigger=trigger,
            id="weekly_planner",
            replace_existing=True,
        )
        job_scheduler.add_job(
            "app.jobs.award_update_all:update_all_awards",
            trigger="date",
            run_date=datetime.now(timezone("UTC")),
            id="update_all_awards_startup",
            replace_existing=True,
        )
        schedule_jobs(week_info=current_week_info())

        yield
    finally:
        job_scheduler.shutdown(wait=True)


app = FastAPI(
    title="TGFP",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(mail.router)
app.include_router(admin.router)
app.add_middleware(
    SessionMiddleware, secret_key=config.SESSION_SECRET_KEY, max_age=None
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# noinspection PyTypeChecker
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


def _get_session():
    with Session(engine) as session:
        yield session


def _get_current_week_info() -> WeekInfo:
    return current_week_info()


def get_error_messages(
    player_picks: List[PlayerGamePick], games: List[Game], upset_id: int, lock_id: int
) -> List[str]:
    """
     Get Error Messages
    Args:
       player_picks: list of all the picks details
       games: all the current week's games
       upset_id: team_id of the upset team
       lock_id: lock_id of the lock team
    Returns:
        :class:`List` - error_message array (empty array if none)
    """
    errors = []
    # First let's make sure that the form was completed (no missed picks)
    if len(player_picks) != len(games):
        errors.append("You missed a pick")

    # Now let's make sure that the lock and pick are the same
    if lock_id:
        # loop through each pick until I find a pick that matches the lock, if not found, then warn
        found_lock: bool = False
        for pick in player_picks:
            if pick.picked_team_id == lock_id:
                found_lock = True
        if not found_lock:
            errors.append("You need to actually pick the team you picked for a lock")
    else:
        # Cool, now let's see if they missed their lock
        errors.append("You missed your lock.  (You must choose a lock)")

    if upset_id:
        found_upset: bool = False
        for pick in player_picks:
            if pick.picked_team_id == upset_id:
                found_upset = True
        if not found_upset:
            errors.append(
                "You cannot choose an upset that you didn't choose as a winner"
            )

    return errors


async def _verify_player(request: Request) -> int:
    """Make sure we have a player session, otherwise, get one"""
    cookie = request.cookies.get("tgfp-discord-id")
    if cookie:
        player_discord_id: Optional[int] = int(cookie)
        return player_discord_id

    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/login"},
    )


@app.get("/")
def home(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Home page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "config": config,
        "week_info": week_info,
    }
    return templates.TemplateResponse(request=request, name="home.j2", context=context)


@app.get("/ping")
def ping():
    return {"status": "pong"}


@app.get("/home")
def home_legacy(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Home page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "config": config,
        "week_info": week_info,
    }
    return templates.TemplateResponse(request=request, name="home.j2", context=context)


@app.get("/profile")
def profile(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    player: Player = Player.by_discord_id(session, discord_id)
    context = {"player": player, "config": config, "week_info": week_info}
    return templates.TemplateResponse(
        request=request, name="coming_soon.j2", context=context
    )


@app.get("/picks", response_class=HTMLResponse)
def picks(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Picks page"""
    player: Player = Player.by_discord_id(session, discord_id)

    # Check if this is a skip week (e.g., postseason bye week)
    if week_info.is_skip_week:
        context = {
            "error_messages": [
                f"There are no games during {week_info.season_type_name} week {week_info.week_no} (bye week)."
            ],
            "goto_route": "allpicks",
            "player": player,
            "config": config,
            "week_info": week_info,
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )

    if player.picks_for_week(week_info):
        context = {
            "error_messages": [
                "Sorry, you can't change your picks.  If you think this is a problem, contact John"
            ],
            "goto_route": "allpicks",
            "player": player,
            "config": config,
            "week_info": week_info,
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    games: List[Game] = Game.games_for_week(session=session, week_info=week_info)
    valid_games = []
    started_games = []
    game: Game
    for game in games:
        if game.is_pregame:
            valid_games.append(game)
        else:
            started_games.append(game)
    valid_lock_teams = []
    valid_upset_teams = []
    for game in valid_games:
        valid_upset_teams.append(game.underdog_team)
        valid_lock_teams.append(game.home_team)
        valid_lock_teams.append(game.road_team)
    valid_lock_teams.sort(key=lambda x: x.long_name, reverse=False)
    valid_upset_teams.sort(key=lambda x: x.long_name, reverse=False)
    pick = None
    context = {
        "valid_games": valid_games,
        "started_games": started_games,
        "valid_lock_teams": valid_lock_teams,
        "valid_upset_teams": valid_upset_teams,
        "player": player,
        "config": config,
        "pick": pick,
        "week_info": week_info,
    }
    return templates.TemplateResponse(request=request, name="picks.j2", context=context)


@app.post("/picks_form")
async def picks_form(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    player: Player = Player.by_discord_id(session=session, discord_id=discord_id)

    # Check if picks already exist for this week
    existing_picks = player.picks_for_week(week_info)
    if existing_picks:
        # Log to Sentry - user somehow got past the picks page guard
        # Early return after sending log.
        original_timestamp = existing_picks[0].created_at
        current_timestamp = datetime.now(timezone("UTC"))
        sentry_sdk.logger.warning(
            f"Player {player.id} ({player.full_name}) attempted to resubmit picks for week {week_info.week_no}",
            extra={
                "player_id": player.id,
                "player_name": player.full_name,
                "week_info": f"{week_info.season} S{week_info.season_type} W{week_info.week_no}",
                "existing_picks_count": len(existing_picks),
                "original_picks_timestamp": original_timestamp.isoformat(),
                "resubmit_attempt_timestamp": current_timestamp.isoformat(),
                "time_delta_seconds": (
                    current_timestamp - original_timestamp
                ).total_seconds(),
                "user_agent": request.headers.get("user-agent"),
                "referer": request.headers.get("referer"),
                "client_host": request.client.host if request.client else None,
            },
        )
        # Gracefully show success page without saving duplicate picks
        session.rollback()
        context = {"player": player, "config": config, "week_info": week_info}
        return templates.TemplateResponse(
            request=request, name="picks_form.j2", context=context
        )

    games: List[Game] = Game.games_for_week(session=session, week_info=week_info)
    form = await request.form()
    # now get the form variables
    lock_id: int = int(form.get("lock")) if form.get("lock") else 0
    upset_id: int = int(form.get("upset")) if form.get("upset") else 0
    pick_detail: List[PlayerGamePick] = []
    for game in games:
        key = f"game_{game.id}"
        if key in form:
            winner_id = int(form.get(key))
            is_lock = winner_id == lock_id
            is_upset = winner_id == upset_id
            pg_pick: PlayerGamePick = PlayerGamePick(
                player_id=player.id,
                game_id=game.id,
                picked_team_id=winner_id,
                season=week_info.season,
                season_type=week_info.season_type,
                week_no=game.week_no,
                is_lock=is_lock,
                is_upset=is_upset,
            )
            pick_detail.append(pg_pick)
            session.add(pg_pick)

    # Below is where we check for errors
    error_messages = get_error_messages(pick_detail, games, upset_id, lock_id)
    if error_messages:
        context = {
            "error_messages": error_messages,
            "goto_route": "picks",
            "player": player,
            "config": config,
            "week_info": week_info,
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    try:
        session.commit()
        job_scheduler.add_job(
            "app.jobs.award_update_all:update_all_awards",
            trigger="date",
            run_date=datetime.now(timezone("UTC")),
            id=f"update_all_awards_{player.id}_{week_info.week_no}",
            replace_existing=True,
        )
    except sqlalchemy.exc.IntegrityError:
        # Race condition: concurrent submission passed the earlier check
        session.rollback()
        sentry_sdk.logger.warning(
            f"Race condition: Player {player.id} ({player.full_name}) concurrent pick submission for week {week_info.week_no}",
            extra={
                "player_id": player.id,
                "player_name": player.full_name,
                "week_info": f"{week_info.season} S{week_info.season_type} W{week_info.week_no}",
                "user_agent": request.headers.get("user-agent"),
                "referer": request.headers.get("referer"),
                "client_host": request.client.host if request.client else None,
            },
        )

    context = {"player": player, "config": config, "week_info": week_info}
    return templates.TemplateResponse(
        request=request, name="picks_form.j2", context=context
    )


@app.get("/allpicks")
def allpicks(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
    week_no: int = None,
    season_type: int = None,
    season: int = None,
):
    player: Player = Player.by_discord_id(session, discord_id)

    if week_no and season_type and season:
        display_week_info = WeekInfo(
            week_no=week_no, season_type=season_type, season=season
        )
    else:
        display_week_info = week_info

    # If displaying a skip week, show the previous week instead
    # NOTE TO REVIEWERS: I know I'm modifying the week_info but that's OK
    if display_week_info.is_skip_week:
        if display_week_info.week_no <= 1:
            sentry_sdk.logger.error(
                "Skip week should NEVER be true if the week is <= 1"
            )
        else:
            display_week_info.week_no -= 1

    active_players: List[Player] = Player.active_players(session=session)
    active_players.sort(key=lambda x: x.total_points, reverse=True)
    games: List[Game] = Game.games_for_week(
        session=session, week_info=display_week_info
    )
    teams: List[Team] = Team.all_teams(session=session)
    all_week_infos: List[WeekInfo] = Game.get_distinct_week_infos(session=session)
    context = {
        "player": player,
        "active_players": active_players,
        "display_week_info": display_week_info,
        "week_info": week_info,
        "games": games,
        "teams": teams,
        "config": config,
        "all_week_infos": all_week_infos,
    }
    return templates.TemplateResponse(
        request=request, name="allpicks.j2", context=context
    )


@app.get("/standings")
async def standings(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Returns the standings page"""
    player: Player = Player.by_discord_id(session, discord_id)
    players: List[Player] = list(
        session.exec(select(Player).where(Player.active)).all()
    )
    players.sort(key=lambda x: x.total_points, reverse=True)

    # For skip weeks or if all games are pregame, show previous week's standings
    most_recent_week: int = week_info.week_no
    should_show_previous_week = False

    if week_info.is_skip_week:
        # Skip week (e.g., postseason bye) - use previous week
        should_show_previous_week = True
    else:
        # Check if all games are still pregame
        games: List[Game] = Game.games_for_week(session=session, week_info=week_info)
        all_games_in_pregame: bool = all(game.is_pregame for game in games)
        if all_games_in_pregame and most_recent_week > 1:
            should_show_previous_week = True

    if should_show_previous_week and most_recent_week > 1:
        most_recent_week -= 1
    context = {
        "player": player,
        "most_recent_week": most_recent_week,
        "active_players": players,
        "config": config,
        "week_info": week_info,
        "awards": session.exec(select(Award)),
    }
    return templates.TemplateResponse(
        request=request, name="standings.j2", context=context
    )


@app.get("/rules")
async def rules(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Rules page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "week_info": week_info,
        "config": config,
    }
    return templates.TemplateResponse(request=request, name="rules.j2", context=context)


@app.get("/logout")
def logout(
    request: Request,
):
    request.session.clear()
    redirect_url = request.url_for("login")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("tgfp-discord-id")
    return response


@app.get("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    week_info: WeekInfo = Depends(_get_current_week_info),
):
    """Login page for discord"""
    context = {"config": config, "week_info": week_info}
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


if __name__ == "__main__":
    assert os.getenv("ENVIRONMENT") == "local_dev"
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=6801, reload=True, access_log=False
    )
