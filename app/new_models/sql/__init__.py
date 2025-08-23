# intentionally empty; importing submodules populates SQLModel.metadata
# Ensure Alembic can find metadata & models by importing this package.
from sqlmodel import SQLModel  # exposes SQLModel.metadata as the target metadata
from .base import TimestampMixin

# Import model classes so tables register at import time.
# Adjust names if your filenames differ.
from .team import TeamSQL
from .game import GameSQL
from .player import PlayerSQL
from .pick import PickSQL
from .pick_detail import PickDetailSQL

__all__ = [
    "SQLModel",
    "TimestampMixin",
    "TeamSQL",
    "GameSQL",
    "PlayerSQL",
    "PickSQL",
    "PickDetailSQL",
]
