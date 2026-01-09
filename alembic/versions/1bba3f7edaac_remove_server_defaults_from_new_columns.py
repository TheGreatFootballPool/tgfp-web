"""remove server defaults from new columns

Revision ID: 1bba3f7edaac
Revises: 20f54c1632bc
Create Date: 2026-01-08 18:16:28.797358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1bba3f7edaac'
down_revision: Union[str, Sequence[str], None] = '20f54c1632bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove server defaults from season_type columns
    op.alter_column('game', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)
    op.alter_column('playeraward', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)
    op.alter_column('playergamepick', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)

    # Remove server defaults from player stats columns
    op.alter_column('player', 'wins',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)
    op.alter_column('player', 'losses',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)
    op.alter_column('player', 'bonus',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Restore server defaults
    op.alter_column('player', 'bonus',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('0'),
                   existing_nullable=False)
    op.alter_column('player', 'losses',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('0'),
                   existing_nullable=False)
    op.alter_column('player', 'wins',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('0'),
                   existing_nullable=False)

    op.alter_column('playergamepick', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('2'),
                   existing_nullable=False)
    op.alter_column('playeraward', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('2'),
                   existing_nullable=False)
    op.alter_column('game', 'season_type',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text('2'),
                   existing_nullable=False)
