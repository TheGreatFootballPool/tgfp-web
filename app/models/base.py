from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlmodel import SQLModel, Field


class TGFPModelBase(SQLModel):
    """Base class for all tables: automatically includes created_at/updated_at."""
    __abstract__ = True  # prevents its own table being created

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": False,
        }
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
            "nullable": False,
        }
    )