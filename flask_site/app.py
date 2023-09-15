""" app file for The Great Football Pool website """
import os
from typing import List, Optional

from flask import Flask, session, request, abort
from flask import render_template, redirect, url_for, g
from flask_discord import DiscordOAuth2Session

from tgfp_lib import TGFP, TGFPPlayer, TGFPPick, TGFPGame

from config import get_config

config = get_config()
# timeout in seconds * minutes
seconds_in_one_day: int = 60*60*24
days_for_timeout: int = 14
COOKIE_TIME_OUT = days_for_timeout * seconds_in_one_day

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
# toolbar = DebugToolbarExtension(app)
app.config.from_object(config)
discord = DiscordOAuth2Session(app)


@app.before_request
def before_request():
    """ This runs before every single request to make sure the user is logged in """
    if os.path.exists("../maintenance"):
        abort(503)
    if 'static' not in request.path and '_profile' not in request.path:
        tgfp = None
        if not hasattr(g, 'tgfp'):
            tgfp = TGFP(config.MONGO_URI)
        # pylint: disable=assigning-non-slot
        g.current_week = tgfp.current_week()
        g.tgfp = tgfp
        if not get_player_from_session():
            player: TGFPPlayer = get_player_from_cookie()
            if player:
                save_player_to_session(player)


@app.after_request
def after_request(response):
    """ Always set the cookie if it's not set """
    player: Optional[TGFPPlayer] = None
    if session.get('clear_discord_id'):
        response.set_cookie('discord_id', expires=0)
        session.pop('clear_discord_id')
    elif not request.cookies.get('discord_id'):
        player: TGFPPlayer = get_player_from_session()
        if player and player.discord_id == 0:
            player = get_player_from_discord_login()
    if player:
        response.set_cookie('discord_id', str(player.discord_id), max_age=COOKIE_TIME_OUT)

    return response


@app.route("/callback")
def callback():
    """ discord callback url """
    discord.callback()
    player: TGFPPlayer = get_player_from_discord_login()
    if player is None:
        return redirect(url_for("no_player"))
    save_player_to_session(player)
    return redirect(url_for("home"))


@app.route('/discord_login')
def discord_login():
    """ create the discord session """
    return discord.create_session(scope=["identify"], prompt=False)


@app.route('/login')
def login():
    """ Login link """
    if 'player_name' in session:
        return redirect(url_for('home'))
    return render_template('login.j2')


@app.route('/')
def index():
    """ default route / -> home """
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    """ Home page"""
    return render_template('profile.j2')


@app.route('/home')
def home():
    """ Home page route for the football pool """
    if 'player_name' not in session:
        session['login_status'] = 'not logged in'
        return redirect(url_for('login'))

    return render_template('home.j2', home_page_text=g.tgfp.home_page_text())


@app.route('/picks')
def picks():
    """ Picks page route """
    if 'player_name' not in session:
        session['login_status'] = 'not logged in'
        return redirect(url_for('login'))

    tgfp = g.tgfp
    player_email = session['player_email']
    player = tgfp.find_players(player_email=player_email)[0]
    all_player_picks = tgfp.find_picks(week_no=g.current_week, player_id=player.id)
    pick = None
    if all_player_picks:
        return render_template(
            'error_picks.j2',
            error_messages=[
                "Sorry, you can't change your picks.  If you think this is a problem, contact John"
                ],
            goto_route='allpicks')

    games = tgfp.find_games(week_no=g.current_week, ordered_by='start_time')
    valid_games = []
    started_games = []
    game: TGFPGame
    for game in games:
        if game.is_pregame:
            valid_games.append(game)
        else:
            started_games.append(game)
    valid_lock_teams = []
    valid_upset_teams = []
    for game in valid_games:
        valid_upset_teams.append(tgfp.find_teams(team_id=game.underdog_team_id)[0])
        valid_lock_teams.append(tgfp.find_teams(team_id=game.home_team_id)[0])
        valid_lock_teams.append(tgfp.find_teams(team_id=game.road_team_id)[0])
    valid_lock_teams.sort(key=lambda x: x.long_name, reverse=False)
    valid_upset_teams.sort(key=lambda x: x.long_name, reverse=False)
    return render_template(
        'picks.j2',
        valid_games=valid_games,
        started_games=started_games,
        valid_lock_teams=valid_lock_teams,
        valid_upset_teams=valid_upset_teams,
        tgfp=tgfp,
        player=player,
        pick=pick
    )


# pylint: disable=too-many-locals
@app.route('/picks_form', methods=['POST'])
def picks_form():
    """ This is the form route that handles processing the form data from the picks page """
    tgfp = g.tgfp
    week_no = g.current_week
    if 'player_email' not in session:
        error_msg = "Your session timed out, please log out and log\
                     back in again -- if the problem persists, contact John"
        return render_template('error_picks.j2', error_messages=error_msg, goto_route='picks')

    player_email = session['player_email']
    player = tgfp.find_players(player_email=player_email)[0]
    games = tgfp.find_games(week_no=week_no, ordered_by='start_time')

    # now get the form variables
    lock_id = request.form["lock"]
    upset_id = request.form["upset"]
    pick_detail = []
    for game in games:
        print("Game")
        key = f"game_{game.id}"
        if key in request.form:
            winner_id = request.form[key]
            print("winner_id " + winner_id)
            item = {
                "game_id": game.id,
                "winner_id": TGFP.object_id_from_string(winner_id)
            }
            pick_detail.append(item)

    # Below is where we check for errors
    error_messages = get_error_messages(pick_detail, games, upset_id, lock_id)
    if error_messages:
        return render_template('error_picks.j2', error_messages=error_messages, goto_route='picks')

    player_pick = None
    player_picks = tgfp.find_picks(player_id=player.id, week_no=week_no)
    if player_picks:
        player_pick = player_picks[0]
    if not player_pick:
        player_pick = TGFPPick(tgfp=tgfp, data=None)

    player_pick.player_id = player.id
    player_pick.week_no = int(week_no)
    player_pick.lock_team_id = TGFP.object_id_from_string(lock_id)
    if upset_id:
        player_pick.upset_team_id = TGFP.object_id_from_string(upset_id)
    else:
        player_pick.upset_team_id = None

    player_pick.pick_detail = pick_detail
    player_pick.save()

    return render_template('picks_form.j2')
# pylint: enable=too-many-locals


@app.route('/allpicks', defaults={'week_no': None})
@app.route('/allpicks/<int:week_no>')
def allpicks(week_no=None):
    """ route for the 'allpicks' page """
    tgfp = g.tgfp
    if 'player_name' not in session:
        session['login_status'] = 'not logged in'
        return redirect(url_for('login'))

    picks_week_no = g.current_week
    if week_no:
        picks_week_no = week_no
    player_email = session['player_email']
    active_players = tgfp.find_players(
        player_active=True,
        ordered_by='total_points',
        reverse_order=True)
    player = tgfp.find_players(player_email=player_email)[0]
    games = tgfp.find_games(week_no=picks_week_no, ordered_by='start_time')
    return render_template(
        'allpicks.j2',
        games=games,
        active_players=active_players,
        tgfp=tgfp,
        player=player,
        week_no=picks_week_no)


@app.route('/standings')
def standings():
    """ route for the 'standings' page """
    if 'player_name' not in session:
        session['login_status'] = 'not logged in'
        return redirect(url_for('login'))

    active_players = g.tgfp.find_players(
        player_active=True,
        ordered_by="total_points",
        reverse_order=True)
    return render_template(
        'standings.j2',
        active_players=active_players)


@app.route('/clan_standings')
def clan_standings():
    """ route for the 'standings' page """
    if 'player_name' not in session:
        session['login_status'] = 'not logged in'
        return redirect(url_for('login'))

    clans = g.tgfp.clans(ordered_by='total_points', reverse_order=True)
    return render_template(
        'clan_standings.j2',
        clans=clans)


# pylint: disable=missing-function-docstring
@app.route('/rules')
def rules():
    return render_template('rules.j2')


@app.route('/picks_form_static')
def picks_form_static():
    return render_template('picks_form.j2')


@app.route('/no_player')
def no_player():
    return render_template('no_player.j2')


@app.route('/logout')
def logout():
    session.clear()
    # pylint: disable=assigning-non-slot
    g.current_week = None
    g.tgfp = None
    session['login_status'] = 'not logged in'
    clear_player_from_session()
    session['clear_discord_id'] = "YES"
    app.secret_key = os.urandom(32)
    return redirect(url_for('home'))


@app.errorhandler(503)
def error_503(error):
    # pylint: disable=unused-argument
    assert error
    return "The Great Football Pool is undergoing some maintenance right now, we'll be back soon!"


# pylint: enable=missing-function-docstring
def get_error_messages(pick_detail, games, upset_id, lock_id):
    """
     Get Error Messages
    Args:
        pick_detail: list of all the picks details
       games: all the current week's games
       upset_id: team_id of the upset team
       lock_id: lock_id of the lock team
    Returns:
        error_message array (empty array if none)
    """
    errors = []
    if len(pick_detail) != len(games):
        errors.append("You missed a pick")
    if not lock_id:
        errors.append("You missed your lock.  (You must choose a lock)")
    for game in games:
        if upset_id:
            if game.favorite_team_id == TGFP.object_id_from_string(upset_id):
                errors.append("You cannot pick a favorite as your upset")
    if upset_id:
        pick_is_ok = False
        for pick_item in pick_detail:
            if upset_id == str(pick_item['winner_id']):
                pick_is_ok = True

        if not pick_is_ok:
            errors.append("You cannot choose an upset that you didn't choose as a winner")

    return errors


def save_player_to_session(player: TGFPPlayer):
    """ Saves the player to the session """
    session['login_status'] = 'logged in'
    session['player_name'] = player.first_name + ' ' + player.last_name
    session['player_email'] = player.email


def clear_player_from_session():
    """ Clears out the player session data """
    session['login_status'] = 'not logged in'
    if session.get('player_name'):
        session.pop('player_name')
    if session.get('player_email'):
        session.pop('player_email')


def get_player_from_session() -> Optional[TGFPPlayer]:
    """ Instantiate a player from existing session data Return None if player can't be found """
    if session.get('player_email'):
        return get_player_by_email(session.get('player_email'))
    return None


def get_player_from_cookie() -> Optional[TGFPPlayer]:
    """ Gets the player from the browser cookie """
    discord_id = request.cookies.get('discord_id')
    if discord_id:
        return get_player_by_discord_id(int(discord_id))
    return None


def get_player_from_discord_login() -> Optional[TGFPPlayer]:
    """ Returns the currently logged in player, None if not logged in """
    discord_user = discord.fetch_user()
    if discord_user:
        return get_player_by_discord_id(discord_user.id)

    return None


def get_player_by_discord_id(discord_id: int) -> Optional[TGFPPlayer]:
    """ Returns a player by their discord ID """
    tgfp = g.tgfp
    players: List[TGFPPlayer] = tgfp.find_players(discord_id=discord_id)
    if len(players) == 1:
        return players[0]
    return None


def get_player_by_email(email: str) -> Optional[TGFPPlayer]:
    """ Returns a player by their email """
    tgfp = g.tgfp
    players: List[TGFPPlayer] = tgfp.find_players(player_email=email)
    if len(players) == 1:
        return players[0]
    return None


if __name__ == '__main__':
    app.run()
