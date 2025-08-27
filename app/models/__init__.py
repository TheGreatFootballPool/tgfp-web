from sqlmodel import SQLModel  # anchor for Alembic target_metadata

# Import models so tables register at import time (for Alembic autogenerate)
from .api_key import ApiKey
from .game import Game
from .player import Player
from .team import Team
from .player_game_pick import PlayerGamePick

__all__ = [
    "SQLModel",
    "ApiKey",
    "Game",
    "PlayerGamePick",
    "Player",
    "Team",
]