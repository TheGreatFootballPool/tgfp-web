""" Main entry point for website """
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Final, List

import pydantic_core
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates

# pylint: disable=ungrouped-imports
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette_discord import DiscordOAuthClient
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
import sentry_sdk


from app.config import Config
from app.models import db_init, Player, TGFPInfo, get_tgfp_info, Game, PickDetail, Team, Pick
from app.api.create_picks import create_picks, CreatePicksException


SECONDS: Final[int] = 60*60*24
DAYS: Final[int] = 365
COOKIE_TIME_OUT = DAYS * SECONDS


def init_config() -> Config:
    """ Initialize the config object """
    async def asyncfunc() -> Config:
        return await Config.get_config()
    return asyncio.run(asyncfunc())


config: Config = init_config()

sentry_sdk.init(
    dsn="https://df0bb7eec46f36b0bf27935fba45470e@sentry.sturgeonfamily.com/2",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=config.ENVIRONMENT,
)

discord: DiscordOAuthClient = DiscordOAuthClient(
    config.DISCORD_CLIENT_ID,
    config.DISCORD_CLIENT_SECRET,
    config.DISCORD_REDIRECT_URI
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """ Perform all app initialization before 'yield' """
    # Initialize the model / DB connection
    await db_init()
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
# noinspection PyTypeChecker
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET_KEY,
    max_age=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_tgfp_info_from_request(request: Request) -> Optional[TGFPInfo]:
    """ Return the deserialized TGFPInfo object """
    tgfp_info: Optional[TGFPInfo] = None
    if request.scope.get('session') is not None:
        tgfp_json: str = request.session.get('tgfp_info')
        if tgfp_json and 'season' in tgfp_json:
            tgfp_info = TGFPInfo.model_validate(
                pydantic_core.from_json(tgfp_json)
            )
    return tgfp_info


def get_player_from_request(request: Request) -> Optional[Player]:
    """ Return the deserialized player object from the request session """
    player: Optional[Player] = None
    if request.scope.get('session') is not None:
        player_json: str = request.session.get('player')
        if player_json and 'name' in player_json:
            player = Player.model_validate(
                pydantic_core.from_json(player_json)
            )
    return player


async def verify_player(request: Request) -> Player:
    """ Make sure we have a player session, otherwise, get one"""
    player: Player = get_player_from_request(request)
    if player:
        return player
    discord_id = request.cookies.get("tgfp-discord-id")
    if discord_id:
        player = await get_player_by_discord_id(int(discord_id))
        if player:
            request.session["player"] = player.model_dump_json()
            return player
        # clear the discord id and fall through to exception
        request.cookies.pop("tgfp-discord-id")
    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={'Location': '/login'})


async def get_latest_info(request: Request) -> Optional[TGFPInfo]:
    """ Returns the current TGFPInfo object """
    info: TGFPInfo = get_tgfp_info_from_request(request)
    if info:
        return info
    info = await get_tgfp_info()
    request.session['tgfp_info'] = info.model_dump_json()
    return info


@app.get("/discord_login")
async def discord_login():
    """ Login url for discord """
    return discord.redirect()


@app.get("/login")
async def login(request: Request, info: TGFPInfo = Depends(get_tgfp_info)):
    """ Login page for discord """
    context = {
        'info': info
    }
    return templates.TemplateResponse(request=request, name="login.j2", context=context)


@app.get("/logout")
async def logout(request: Request):
    """ Logs the user out and clears the session """
    request.session.clear()
    redirect_url = request.url_for('login')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie('tgfp-discord-id')
    return response


@app.get("/callback")
async def callback(code: str, request: Request):
    """ Callback url for discord """
    user = await discord.login(code)
    player: Player = await get_player_by_discord_id(user.id)
    if player:
        redirect_url = request.url_for('home')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key='tgfp-discord-id',
            value=str(user.id),
            max_age=COOKIE_TIME_OUT,
        )
    else:
        redirect_url = request.url_for('login')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@app.get("/")
def root(request: Request):
    """ Redirect '/' to /home """
    return RedirectResponse(request.url_for('home'), status.HTTP_301_MOVED_PERMANENTLY)


@app.get("/rules")
def rules(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Rules page """
    context = {
        'player': player,
        'info': info
    }
    return templates.TemplateResponse(request=request, name="rules.j2", context=context)


@app.get("/home", response_class=HTMLResponse)
def home(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Home page """
    context = {
        'player': player,
        'info': info
    }
    return templates.TemplateResponse(
            request=request, name="home.j2", context=context
        )


@app.get('/standings')
async def standings(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Returns the standings page """
    players: List[Player] = await Player.find({'active': True}).to_list()
    players.sort(key=lambda x: x.total_points, reverse=True)
    context = {
        'player': player,
        'info': info,
        'active_players': players
    }
    return templates.TemplateResponse(
        request=request, name="standings.j2", context=context
    )


@app.get('/allpicks')
async def allpicks(
        _: Request,
        __: Player = Depends(verify_player),
        ___: TGFPInfo = Depends(get_tgfp_info)
):
    """ All Picks page """
    return {'status': True}


@app.get("/picks")
async def picks(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)
):
    """ Picks page """
    if len(player.picks) > 0:
        context = {
            'error_messages': [
                "Sorry, you can't change your picks.  If you think this is a problem, contact John"
            ],
            'goto_route': 'allpicks',
            'player': player,
            'info': info
        }
        return templates.TemplateResponse(
            request=request, name="error_picks.j2", context=context
        )
    games: List[Game] = await Game.find(
        Game.week_no == info.display_week,
        Game.season == info.season
    ).sort("-start_time").to_list()
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
        'valid_games': valid_games,
        'started_games': started_games,
        'valid_lock_teams': valid_lock_teams,
        'valid_upset_teams': valid_upset_teams,
        'info': info,
        'player': player,
        'pick': pick
    }
    return templates.TemplateResponse(
            request=request, name="picks.j2", context=context
        )


# pylint: disable=too-many-locals
@app.post('/picks_form')
async def picks_form(
        request: Request,
        player: Player = Depends(verify_player),
        info: TGFPInfo = Depends(get_tgfp_info)):
    """ This is the form route that handles processing the form data from the picks page """
    games: List[Game] = await Game.find(
        Game.week_no == info.display_week,
        Game.season == info.season
    ).sort("-start_time").to_list()
    form = await request.form()
    # now get the form variables
    lock_id = form.get('lock')
    upset_id = form.get('upset')
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
    error_messages = get_error_messages(pick_detail, games, upset_id, lock_id)
    if error_messages:
        context = {
            'error_messages': error_messages,
            'goto_route': 'picks',
            'player': player,
            'info': info
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
        week_no=info.display_week,
        season=info.season,
        lock_team=lock_team,
        upset_team=upset_team
    )

    pick.pick_detail = pick_detail
    player.picks.append(pick)
    await player.save()


@app.post("/api/create_picks_page")
async def create_picks_page():
    """ API for creating the picks page """
    try:
        await create_picks()
    except CreatePicksException as e:
        # pylint: disable=raise-missing-from
        raise HTTPException(status_code=500, detail=str(e))
    return {'success': True}


async def get_player_by_discord_id(discord_id: int) -> Optional[Player]:
    """ Returns a player by their discord ID """
    player: Player = await Player.find_one(Player.discord_id == discord_id)
    return player


def get_error_messages(
        pick_detail: List[PickDetail],
        games: List[Game],
        upset_id: str,
        lock_id: str
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
        if upset_id:
            if str(game.favorite_team.id) == upset_id:
                errors.append("You cannot pick a favorite as your upset")
    if upset_id:
        pick_is_ok = False
        for pick_item in pick_detail:
            if upset_id == str(pick_item.winning_team.id):
                pick_is_ok = True

        if not pick_is_ok:
            errors.append("You cannot choose an upset that you didn't choose as a winner")

    return errors


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
