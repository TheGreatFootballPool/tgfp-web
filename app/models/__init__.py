from sqlmodel import SQLModel  # anchor for Alembic target_metadata

# Import models so tables register at import time (for Alembic autogenerate)
from .api_key import ApiKey
from .game import Game
from .player_game_pick import PlayerGamePick
from .player import Player
from .team import Team
from .award import Award
from .player_award import PlayerAward

__all__ = [
    "SQLModel",
    "ApiKey",
    "Game",
    "PlayerGamePick",
    "Player",
    "Team",
    "Award",
    "PlayerAward",
]
