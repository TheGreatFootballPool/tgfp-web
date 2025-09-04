from __future__ import annotations
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Ensure new SQLModel tables are registered via side-effect import
import app.models  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = SQLModel.metadata

# --- Optional: limit autogenerate to specific tables (edit as needed) ---
# Example workflow (one model at a time):
# TABLES_TO_MIGRATE = {"api_keys"}
# For normal operation (all tables), leave it empty:
TABLES_TO_MIGRATE: set[str] = set()


def include_object(obj, name, type_, _reflected, _compare_to):
    """If TABLES_TO_MIGRATE is non-empty, include only those tables and their columns.
    Alembic calls this for tables, columns, indexes, constraints, etc.
    """
    if type_ == "table" and name == "apscheduler_jobs":
        return False

    if not TABLES_TO_MIGRATE:
        return True

    if type_ == "table":
        return name in TABLES_TO_MIGRATE

    parent_table = getattr(obj, "table", None)
    if parent_table is not None:
        return parent_table.name in TABLES_TO_MIGRATE

    return True


def run_migrations_offline() -> None:
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = os.getenv("DATABASE_URL", cfg.get("sqlalchemy.url"))

    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
