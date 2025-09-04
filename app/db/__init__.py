from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Config

config = Config.get_config()

DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# APScheduler job store engine (defaults to main DB unless SCHED_DB_URL is set)
SCHED_DB_URL = os.getenv("SCHED_DB_URL", DATABASE_URL)
scheduler_engine = create_engine(SCHED_DB_URL, pool_pre_ping=True, future=True)


@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_models() -> None:
    """
    Import SQLModel tables so SQLModel.metadata is populated for Alembic.
    Keep imports local to avoid import cycles.
    """
    from app.models.sql import team, game, player, pick, pick_detail  # noqa: F401
