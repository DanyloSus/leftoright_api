"""add match status and winner_entity_id columns; extend sessionstatus enum

Revision ID: a1b2c3d4e5f6
Revises: 6c1cf0896daa
Create Date: 2026-03-31 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6c1cf0896daa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('winner_entity_id', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('status', sa.String(), nullable=False, server_default='PENDING'))
    op.create_foreign_key(
        'fk_matches_winner_entity_id',
        'matches', 'entities',
        ['winner_entity_id'], ['id'],
        ondelete='SET NULL',
    )
    # Extend the PostgreSQL enum with new values (no-op on SQLite)
    op.execute("DO $$ BEGIN "
               "ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'waiting'; "
               "EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN "
               "ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'finished'; "
               "EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN "
               "ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'paused'; "
               "EXCEPTION WHEN duplicate_object THEN null; END $$;")


def downgrade() -> None:
    op.drop_constraint('fk_matches_winner_entity_id', 'matches', type_='foreignkey')
    op.drop_column('matches', 'winner_entity_id')
    op.drop_column('matches', 'status')
    # Note: PostgreSQL does not support removing enum values — downgrade leaves enum intact
