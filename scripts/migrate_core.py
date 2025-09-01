# Ensure repo root is importable so `import app` works when running this file directly
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path[:0] = [str(ROOT)]
# scripts/migrate_core.py
import os  # noqa: E402
from typing import Any, Dict  # noqa: E402, E402

from pymongo import MongoClient  # noqa: E402
from bson import ObjectId  # noqa: E402
from datetime import timezone  # noqa: E402
from sqlmodel import create_engine, Session  # noqa: E402

# Import your SQLModel classes
from app.models import (
    Team,
    Player,
    ApiKey,
)  # Team/Player/ApiKey must exist  # noqa: E402
# If your model package name/path differs, adjust the import above.

# --- Config ---
MONGO_URI = "mongodb://tgfp:f_xUG9VGGYxP@tgfp-db:27017/"
MONGO_DB = "tgfp"  # change if your prod DB name differs
POSTGRES_URL = "postgresql+psycopg://tgfp:tgfp@127.0.0.1:5433/tgfp"

# Optional: set to True to print docs instead of writing
DRY_RUN = bool(int(os.getenv("DRY_RUN", "0")))


def created_from_objectid(oid: ObjectId):
    """Extract creation time from Mongo ObjectId as UTC-aware datetime."""
    if isinstance(oid, ObjectId):
        return oid.generation_time.astimezone(timezone.utc)


def get_str(d: Dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key, default)
    return "" if v is None else str(v)


# noinspection PyBroadException
def get_int(d: Dict[str, Any], key: str, default: int = 0) -> int:
    v = d.get(key, default)
    try:
        return int(v)
    except Exception:
        return default


def migrate_teams(session: Session, mdb) -> int:
    teams_coll = mdb.get_collection("teams")
    count = 0
    for t in teams_coll.find({}):
        team = Team(
            city=get_str(t, "city"),
            long_name=get_str(t, "long_name"),
            losses=get_int(t, "losses"),
            short_name=get_str(t, "short_name"),
            ties=get_int(t, "ties"),
            wins=get_int(t, "wins"),
            full_name=get_str(t, "full_name"),
            logo_url=get_str(t, "logo_url"),
            tgfp_nfl_team_id=get_str(t, "tgfp_nfl_team_id"),
            discord_emoji=get_str(t, "discord_emoji"),
            created_at=created_from_objectid(t.get("_id")),
        )
        if DRY_RUN:
            print("[DRY RUN] Team ->", team)
        else:
            session.add(team)
            count += 1
    if not DRY_RUN:
        session.commit()
    return count


def migrate_players(session: Session, mdb) -> int:
    players_coll = mdb.get_collection("players")
    count = 0
    for p in players_coll.find({}):
        player = Player(
            first_name=get_str(p, "first_name"),
            last_name=get_str(p, "last_name"),
            nick_name=get_str(p, "nick_name"),
            active=bool(p.get("active", True)),
            email=get_str(p, "email"),
            discord_id=get_int(p, "discord_id"),
            created_at=created_from_objectid(p.get("_id")),
        )
        if DRY_RUN:
            print("[DRY RUN] Player ->", player)
        else:
            session.add(player)
            count += 1
    if not DRY_RUN:
        session.commit()
    return count


def migrate_api_keys(session: Session, mdb) -> int:
    # The collection name might be "api_keys" or similar; adjust if needed.
    # If you never stored keys in Mongo, this will just no-op.
    names = set(mdb.list_collection_names())
    if "api_keys" not in names:
        print("No 'api_keys' collection found in Mongo; skipping.")
        return 0

    apikeys_coll = mdb.get_collection("api_keys")
    count = 0
    for k in apikeys_coll.find({}):
        ak = ApiKey(
            token=get_str(k, "token"),
            description=get_str(k, "description"),
        )
        if DRY_RUN:
            print("[DRY RUN] ApiKey ->", ak)
        else:
            session.add(ak)
            count += 1
    if not DRY_RUN:
        session.commit()
    return count


def main():
    # --- Connect sources ---
    mongo = MongoClient(MONGO_URI)
    mdb = mongo[MONGO_DB]

    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)

    # --- Migrate ---
    with Session(engine) as session:
        t = migrate_teams(session, mdb)
        print(f"Inserted {t} team(s).")

        p = migrate_players(session, mdb)
        print(f"Inserted {p} player(s).")

        a = migrate_api_keys(session, mdb)
        print(f"Inserted {a} api key(s).")

    print("Done.")


if __name__ == "__main__":
    main()
