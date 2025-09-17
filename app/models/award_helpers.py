from sqlmodel import Session, select

from db import engine
from models import AwardSlug, Award, PlayerAward

import logging

from models.award import AWARD_DEFINITIONS


# Upsert function for awards
def init_award_table() -> None:
    """Insert or update awards from AWARD_DEFINITIONS into the DB using SQLModel."""
    with Session(engine) as session:
        for row in AWARD_DEFINITIONS:
            slug_enum = AwardSlug(row["slug"])  # validate & use enum
            existing = session.exec(
                select(Award).where(Award.slug == slug_enum)
            ).first()

            if existing:
                existing.name = row["name"]
                existing.description = row["description"]
                existing.icon = row["icon"]
                existing.point_value = row["point_value"]
                logging.info(
                    "init_award_helper: Award {} already exists".format(row["slug"])
                )
            else:
                # ✅ set slug to the string value; SQLModel will coerce back to AwardSlug on load
                award = Award(
                    slug=slug_enum,
                    name=row["name"],
                    description=row["description"],
                    icon=row["icon"],
                    point_value=row["point_value"],
                )
                session.add(award)

        session.commit()


def upsert_award_with_args(
    session: Session,
    player_id: int,
    slug: AwardSlug,
    season: int,
    week_no: int,
    game_id: int = None,
) -> bool:
    did_update: bool = False
    the_award: Award = Award.get_by_slug(session=session, slug=slug)
    statement = (
        select(PlayerAward)
        .where(PlayerAward.player_id == player_id)
        .where(PlayerAward.award_id == the_award.id)
        .where(PlayerAward.season == season)
        .where(PlayerAward.week_no == week_no)
    )
    if game_id:
        statement = statement.where(PlayerAward.game_id == game_id)
    existing = session.exec(statement).first()
    if not existing:
        did_update = True
        player_award: PlayerAward = PlayerAward(
            player_id=player_id,
            award_id=the_award.id,
            season=season,
            week_no=week_no,
            game_id=game_id,
        )
        session.add(player_award)
    session.commit()
    return did_update
