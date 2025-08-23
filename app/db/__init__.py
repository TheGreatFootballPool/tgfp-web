from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Containers talk to postgres:5432; host runs can override via env (e.g., localhost:5433)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://tgfp:tgfp@postgres:5432/tgfp",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


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
    from app.new_models.sql import team, game, player, pick, pick_detail  # noqa: F401
