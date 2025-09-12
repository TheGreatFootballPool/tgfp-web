from sqlmodel import Field

from .base import TGFPModelBase


class Award(TGFPModelBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str
    icon: str
    point_value: int
