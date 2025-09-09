from sqlmodel import Session
from models import Team
from app.db import engine
from tgfp_nfl import TgfpNfl, TgfpNflTeam


def sync_team_records():
    nfl: TgfpNfl = TgfpNfl()
    with Session(engine) as session:
        teams = Team.all_teams(session)
        for team in teams:
            nfl_team: TgfpNflTeam = nfl.find_teams(team_id=team.tgfp_nfl_team_id)[0]
            team.wins = nfl_team.wins
            team.losses = nfl_team.losses
            team.ties = nfl_team.ties
        session.commit()
