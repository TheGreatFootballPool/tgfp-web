from sqlmodel import Session
from models import Team
from app.db import engine
from espn_nfl import ESPNNfl, ESPNNflTeam


def sync_the_team_records():
    nfl: ESPNNfl = ESPNNfl()
    with Session(engine) as session:
        teams = Team.all_teams(session)
        for team in teams:
            nfl_team: ESPNNflTeam = nfl.find_teams(team_id=team.tgfp_nfl_team_id)[0]
            team.wins = nfl_team.wins
            team.losses = nfl_team.losses
            team.ties = nfl_team.ties
        session.commit()
