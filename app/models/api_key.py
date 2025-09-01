from typing import Optional
from sqlmodel import SQLModel, Field

from .base import TGFPModelBase


class ApiKey(TGFPModelBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True, description="API token string")
    description: str