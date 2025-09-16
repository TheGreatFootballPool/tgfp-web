from sqlmodel import Field, Session, select
from enum import Enum

from .base import TGFPModelBase


class AwardSlug(str, Enum):
    QUICK_PICK = "quick_pick"
    WON_THE_WEEK = "won_the_week"
    PERFECT_WEEK = "perfect_week"
    IN_YOUR_FACE = "in_your_face"


class Award(TGFPModelBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    slug: str = Field(unique=True, index=True)
    description: str
    icon: str
    point_value: int

    @staticmethod
    def get_by_slug(session: Session, slug: AwardSlug) -> "Award":
        statement = select(Award).where(Award.slug == slug)
        return session.exec(statement).one()


# Award definitions for common awards (list form with explicit slug)
AWARD_DEFINITIONS: list[dict] = [
    {
        "slug": "quick_pick",
        "name": "Quick Pick",
        "description": "Awarded to the first player to get their pick in",
        "icon": "badge-quick-pick",
        "point_value": 1,
    },
    {
        "slug": "won_the_week",
        "name": "Won the Week",
        "description": "Awarded to the player who had the best weekly record",
        "icon": "badge-won-the-week",
        "point_value": 2,
    },
    {
        "slug": "perfect_week",
        "name": "Perfect Week",
        "description": "Awarded to any player that picks every game correctly",
        "icon": "badge-perfect-week",
        "point_value": 5,
    },
    {
        "slug": "in_your_face",
        "name": "In Your Face",
        "description": "Awarded to a player that is the only one to pick a winning team",
        "icon": "badge-iyf",
        "point_value": 3,
    },
]
