"""Main entry point for website"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Final, List

import uvicorn
from beanie import PydanticObjectId
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from fastapi_discord import DiscordOAuthClient, User

# pylint: disable=ungrouped-imports
from starlette import status
from starlette.datastructures import MutableHeaders
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from api.nag_players import nag_players
from api.schedule_kestra_flows import schedule_kestra_flows
from api.update_scores import update_game
from api.update_team_records import update_team_records
from models import (
    db_init,
    Player,
    TGFPInfo,
    get_tgfp_info,
    Game,
    PickDetail,
    Team,
    Pick,
    ApiKey,
)
from api.create_picks import create_picks, CreatePicksException
from config import Config


SECONDS: Final[int] = 60 * 60 * 24
DAYS: Final[int] = 365
COOKIE_TIME_OUT = DAYS * SECONDS

# pylint: disable=duplicate-code
config: Config = Config.get_config()

discord: DiscordOAuthClient = DiscordOAuthClient(
    config.DISCORD_CLIENT_ID, config.DISCORD_CLIENT_SECRET, config.DISCORD_REDIRECT_URI
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # use token authentication


def ordinal(n: int):
    """Returns the 'place' ordinal string for a given int"""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


async def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    """Check to see if we have an authorized token"""
    found_key: Optional[ApiKey] = await ApiKey.find_one(ApiKey.token == api_key)
    if found_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden"
        )
    set_user({"email": "kestra@sturgeon.me", "username": "kestra"})


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Perform all app initialization before 'yield'"""
    await db_init(config)
    await discord.init()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
# noinspection PyTypeChecker
app.add_middleware(
    SessionMiddleware, secret_key=config.SESSION_SECRET_KEY, max_age=None
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# noinspection PyTypeChecker
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


async def get_player_from_request(request: Request) -> Optional[Player]:
    """Return the deserialized player object from the request session"""
    player: Optional[Player] = None
    if request.scope.get("session") is not None:
        player_id: str = request.session.get("player_id")
        if player_id:
            player = await Player.get(PydanticObjectId(player_id))
    return player


async def verify_player(request: Request) -> Player:
    """Make sure we have a player session, otherwise, get one"""
    player: Player = await get_player_from_request(request)
    if player:
        return player
    discord_id = request.cookies.get("tgfp-discord-id")
    if discord_id:
        player = await get_player_by_discord_id(int(discord_id))
        if player:
            request.session["player_id"] = str(player.id)
            set_user({"email": player.email, "username": player.nick_name})
            return player
        # clear the discord id and fall through to exception
        request.cookies.pop("tgfp-discord-id")
    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"}
    )


async def get_latest_info(request: Request) -> Optional[TGFPInfo]:
    """Returns the current TGFPInfo object"""
    info = await get_tgfp_info()
    info.app_version = config.APP_VERSION
    info.app_env = config.ENVIRONMENT
    request.session["tgfp_info"] = info.model_dump_json()
    return info


@app.get("/discord_login")
async def discord_login():
    """Login url for discord"""
    return RedirectResponse(discord.oauth_login_url)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, info: TGFPInfo = Depends(get_latest_info)):
    """Login page for discord"""
    context = {"info": info}
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


@app.get("/logout")
async def logout(request: Request):
    """Logs the user out and clears the session"""
    request.session.clear()
    redirect_url = request.url_for("login")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("tgfp-discord-id")
    return response


@app.get("/callback")
async def callback(code: str, request: Request):
    """Callback url for discord"""
    token, _ = await discord.get_access_token(code)
    new_header = MutableHeaders(request.headers)
    new_header["Authorization"] = f"Bearer {token}"
    # pylint: disable=protected-access
    request._headers = new_header
    request.scope.update(headers=request.headers.raw)
    user: User = await discord.user(request)
    player: Player = await get_player_by_discord_id(int(user.id))
    if player:
        redirect_url = request.url_for("home")
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="tgfp-discord-id",
            value=user.id,
            max_age=COOKIE_TIME_OUT,
        )
    else:
        redirect_url = request.url_for("login")
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@app.get("/")
def root(request: Request):
    """Redirect '/' to /home"""
    return RedirectResponse(request.url_for("home"), status.HTTP_301_MOVED_PERMANENTLY)


@app.get("/rules", response_class=HTMLResponse)
def rules(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
):
    """Rules page"""
    context = {"player": player, "info": info}
    return templates.TemplateResponse(request=request, name="rules.j2", context=context)


@app.get("/home", response_class=HTMLResponse)
def home(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
):
    """Home page"""
    context = {"player": player, "info": info}
    return templates.TemplateResponse(request=request, name="home.j2", context=context)


@app.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
    profile_player_id: str = None,
):
    """Player Profile Page"""
    if profile_player_id:
        profile_player: Player = await Player.get(PydanticObjectId(profile_player_id))
    else:
        profile_player: Player = player
    num_players: int = len(await Player.active_players())
    games_back: int = await profile_player.games_back()
    labels: List[str] = []
    values: List[int] = []
    for i in range(0, info.active_week):
        week_no: int = i + 1
        labels.append(f"Week {week_no}")
        values.append(await profile_player.get_standings_through(week_no))
    data: dict = {"labels": labels, "data": values}
    current_place: str = ordinal(values[-1])
    context = {
        "player": player,
        "profile_player": profile_player,
        "page_title": "Profile",
        "info": info,
        "the_data": data,
        "num_players": num_players,
        "games_back": games_back,
        "current_place": current_place,
    }
    return templates.TemplateResponse(
        request=request, name="new_base.j2", context=context
    )


@app.get("/standings", response_class=HTMLResponse)
async def standings(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
):
    """Returns the standings page"""
    players: List[Player] = await Player.find({"active": True}).to_list()
    players.sort(key=lambda x: x.total_points, reverse=True)
    context = {"player": player, "info": info, "active_players": players}
    return templates.TemplateResponse(
        request=request, name="standings.j2", context=context
    )


@app.get("/allpicks", response_class=HTMLResponse)
async def allpicks(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
    week_no: int = None,
):
    """All Picks page"""
    picks_week_no = info.display_week
    if week_no:
        picks_week_no = week_no
    active_players: List[Player] = await Player.active_players()
    active_players.sort(key=lambda x: x.total_points, reverse=True)
    games: List[Game] = (
        await Game.find(
            Game.week_no == picks_week_no, Game.season == info.season, fetch_links=True
        )
        .sort("+start_time")
        .to_list()
    )
    teams: List[Team] = await Team.find_all().to_list()
    context = {
        "player": player,
        "info": info,
        "active_players": active_players,
        "week_no": picks_week_no,
        "games": games,
        "teams": teams,
    }
    return templates.TemplateResponse(
        request=request, name="allpicks.j2", context=context
    )


@app.get("/picks", response_class=HTMLResponse)
async def picks(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
):
    """Picks page"""
    if player.pick_for_week(info.display_week):
        context = {
            "error_messages": [
                "Sorry, you can't change your picks.  If you think this is a problem, contact John"
            ],
            "goto_route": "allpicks",
            "player": player,
            "info": info,
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    games: List[Game] = (
        await Game.find(
            Game.week_no == info.display_week,
            Game.season == info.season,
            fetch_links=True,
        )
        .sort("+start_time")
        .to_list()
    )
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
        "info": info,
        "player": player,
        "pick": pick,
    }
    return templates.TemplateResponse(request=request, name="picks.j2", context=context)


# pylint: disable=too-many-locals
@app.post("/picks_form")
async def picks_form(
    request: Request,
    player: Player = Depends(verify_player),
    info: TGFPInfo = Depends(get_latest_info),
):
    """This is the form route that handles processing the form data from the picks page"""
    games: List[Game] = (
        await Game.find(
            Game.week_no == info.display_week,
            Game.season == info.season,
            fetch_links=True,
        )
        .sort("-start_time")
        .to_list()
    )
    form = await request.form()
    # now get the form variables
    lock_id = form.get("lock")
    upset_id = form.get("upset")
    pick_detail: List[PickDetail] = []
    for game in games:
        key = f"game_{game.id}"
        if key in form:
            winner_id = form.get(key)
            winning_team: Team = await Team.get(winner_id)
            detail: PickDetail = PickDetail(
                game=game,
                winning_team=winning_team,
            )
            pick_detail.append(detail)

    # Below is where we check for errors
    error_messages = await get_error_messages(pick_detail, games, upset_id, lock_id)
    if error_messages:
        context = {
            "error_messages": error_messages,
            "goto_route": "picks",
            "player": player,
            "info": info,
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )

    lock_team: Team = await Team.get(lock_id)
    if upset_id:
        upset_team = await Team.get(upset_id)
    else:
        upset_team = None
    pick: Pick = Pick(
        id=PydanticObjectId(),
        created_at=datetime.now(),
        week_no=info.display_week,
        season=info.season,
        lock_team=lock_team,
        upset_team=upset_team,
    )

    pick.pick_detail = pick_detail
    player.picks.append(pick)
    # noinspection PyArgumentList
    await player.save()
    context = {"player": player, "info": info}
    return templates.TemplateResponse(
        request=request, name="picks_form.j2", context=context
    )


@app.post("/api/create_picks_page", dependencies=[Depends(api_key_auth)])
async def api_create_picks_page():
    """API for creating the picks page"""
    try:
        await create_picks()
    except CreatePicksException as e:
        # pylint: disable=raise-missing-from
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True}


@app.post("/api/nag_players", dependencies=[Depends(api_key_auth)])
async def api_nag_players(info: TGFPInfo = Depends(get_latest_info)):
    """Sends a message to discord to nag the players that haven't done their picks yet"""
    await nag_players(info)
    return {"success": True}


@app.post("/api/schedule_kestra_flows", dependencies=[Depends(api_key_auth)])
async def api_schedule_kestra_flows(info: TGFPInfo = Depends(get_latest_info)):
    """Schedule all the kestra flows"""
    await schedule_kestra_flows(info)
    return {"success": True}


@app.get(
    "/api/update_game/{game_id}",
    response_model=Game,
    dependencies=[Depends(api_key_auth)],
)
async def api_update_game(game_id: str):
    """API to tell trigger a game update (given the game ID)"""
    game: Game = await Game.get(PydanticObjectId(game_id))
    await update_game(game)
    return game


@app.post("/api/update_team_records", dependencies=[Depends(api_key_auth)])
async def api_update_team_records():
    """When called, will update all the team's win / loss record"""
    await update_team_records()
    return {"success": True}


async def get_player_by_discord_id(discord_id: int) -> Optional[Player]:
    """Returns a player by their discord ID"""
    player: Player = await Player.find_one(Player.discord_id == discord_id)
    return player


async def get_error_messages(
    pick_detail: List[PickDetail], games: List[Game], upset_id: str, lock_id: str
) -> List:
    """
     Get Error Messages
    Args:
       pick_detail: list of all the picks details
       games: all the current week's games
       upset_id: team_id of the upset team
       lock_id: lock_id of the lock team
    Returns:
        :class:`List` - error_message array (empty array if none)
    """
    errors = []
    if len(pick_detail) != len(games):
        errors.append("You missed a pick")
    if not lock_id:
        errors.append("You missed your lock.  (You must choose a lock)")
    for game in games:
        await game.fetch_link("favorite_team")
        if upset_id:
            if str(game.favorite_team.id) == upset_id:
                errors.append("You cannot pick a favorite as your upset")
    if upset_id:
        pick_is_ok = False
        for pick_item in pick_detail:
            await pick_item.fetch_link("winning_team")
            if upset_id == str(pick_item.winning_team.id):
                pick_is_ok = True

        if not pick_is_ok:
            errors.append(
                "You cannot choose an upset that you didn't choose as a winner"
            )

    return errors


if __name__ == "__main__":
    reload: bool = os.getenv("ENVIRONMENT") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=6701, reload=reload, access_log=False)
