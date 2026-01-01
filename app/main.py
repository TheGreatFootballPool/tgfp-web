"""Main entry point for website"""

from datetime import datetime
import os
from contextlib import asynccontextmanager
from typing import Optional, List

from pytz import timezone

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
import sentry_sdk
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
from models.model_helpers import current_nfl_season
from app.routers import auth, mail, admin
from apscheduler.triggers.cron import CronTrigger

from config import Config
from logging_config import init_logging

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
        traces_sample_rate=1.0,
        profile_lifecycle="manual",
        profile_session_sample_rate=1.0,
    )
    init_logging()
    init_award_table()
    try:
        pacific = timezone("America/Los_Angeles")
        trigger = CronTrigger(day_of_week="wed", hour=7, minute=0, timezone=pacific)
        job = job_scheduler.get_job("weekly_planner")
        if job:
            job_scheduler.reschedule_job("weekly_planner", trigger=trigger)
        else:
            job_scheduler.add_job(
                "app.jobs.scheduler:schedule_jobs", trigger=trigger, id="weekly_planner"
            )
        job_scheduler.add_job(
            "app.jobs.award_update_all:update_all_awards",
            trigger="date",
            run_date=datetime.now(timezone("UTC")),
            id="update_all_awards_startup",
            replace_existing=True,
        )

        schedule_jobs()

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
):
    """Home page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "config": config,
        "current_week": Game.most_recent_week(session),
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
):
    """Home page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "config": config,
        "current_week": Game.most_recent_week(session),
    }
    return templates.TemplateResponse(request=request, name="home.j2", context=context)


@app.get("/profile")
def profile(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
):
    player: Player = Player.by_discord_id(session, discord_id)
    context = {"player": player, "config": config}
    return templates.TemplateResponse(
        request=request, name="coming_soon.j2", context=context
    )


@app.get("/picks", response_class=HTMLResponse)
def picks(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
):
    """Picks page"""
    player: Player = Player.by_discord_id(session, discord_id)
    if player.picks(week_no=Game.most_recent_week(session=session)):
        context = {
            "error_messages": [
                "Sorry, you can't change your picks.  If you think this is a problem, contact John"
            ],
            "goto_route": "allpicks",
            "player": player,
            "config": config,
            "current_week": Game.most_recent_week(session),
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    games: List[Game] = Game.games_for_week(session)
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
        "current_week": Game.most_recent_week(session),
    }
    return templates.TemplateResponse(request=request, name="picks.j2", context=context)


@app.post("/picks_form")
async def picks_form(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
):
    player: Player = Player.by_discord_id(session, discord_id)
    games: List[Game] = Game.games_for_week(session)
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
                season=current_nfl_season(),
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
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    session.commit()
    job_scheduler.add_job(
        "app.jobs.award_update_all:update_all_awards",
        trigger="date",
        run_date=datetime.now(timezone("UTC")),
        id=f"update_all_awards_{player.id}_{Game.most_recent_week(session)}",
        replace_existing=True,
    )

    context = {"player": player, "config": config}
    return templates.TemplateResponse(
        request=request, name="picks_form.j2", context=context
    )


@app.get("/allpicks")
def allpicks(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    week_no: int = None,
):
    player: Player = Player.by_discord_id(session, discord_id)
    current_week: int = Game.most_recent_week(session)
    picks_week_no = week_no if week_no else current_week
    active_players: List[Player] = Player.active_players(session)
    # Prefetch all picks for all players to populate session cache
    Player.prefetch_picks_for_players(session, active_players)
    active_players.sort(key=lambda x: x.total_points(), reverse=True)
    games: List[Game] = Game.games_for_week(session, week_no=picks_week_no)
    teams: List[Team] = Team.all_teams(session)
    context = {
        "player": player,
        "active_players": active_players,
        "week_no": picks_week_no,
        "current_week": current_week,
        "games": games,
        "teams": teams,
        "config": config,
    }
    return templates.TemplateResponse(
        request=request, name="allpicks.j2", context=context
    )


@app.get("/standings")
async def standings(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
):
    """Returns the standings page"""
    player: Player = Player.by_discord_id(session, discord_id)
    players: List[Player] = list(
        session.exec(select(Player).where(Player.active)).all()
    )
    # Prefetch all picks and awards for all players to populate session cache
    Player.prefetch_picks_for_players(session, players)
    Player.prefetch_awards_for_players(session, players)
    players.sort(key=lambda x: x.total_points(), reverse=True)
    games: List[Game] = Game.games_for_week(session)
    most_recent_week: int = Game.most_recent_week(session)
    all_games_in_pregame: bool = True
    for game in games:
        if not game.is_pregame:
            all_games_in_pregame = False
            break
    if all_games_in_pregame and most_recent_week > 1:
        most_recent_week -= 1
    context = {
        "player": player,
        "most_recent_week": most_recent_week,
        "active_players": players,
        "config": config,
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
):
    """Rules page"""
    player: Player = Player.by_discord_id(session, discord_id)
    context = {
        "player": player,
        "current_week": Game.most_recent_week(session),
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
async def login(request: Request):
    """Login page for discord"""
    context = {"config": config}
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


if __name__ == "__main__":
    assert os.getenv("ENVIRONMENT") == "local_dev"
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=6801, reload=True, access_log=False
    )
