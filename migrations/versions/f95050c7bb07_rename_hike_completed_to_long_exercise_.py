"""rename hike_completed to long_exercise_completed

Revision ID: f95050c7bb07
Revises: a5449e85bc5a
Create Date: 2025-10-21 10:28:50.958993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f95050c7bb07'
down_revision: Union[str, Sequence[str], None] = 'a5449e85bc5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Rename hike_completed to long_exercise_completed."""
    # SQLite doesn't support direct column rename in Alembic
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('rule_revisions', schema=None) as batch_op:
        batch_op.alter_column(
            'hike_completed',
            new_column_name='long_exercise_completed',
            existing_type=sa.Boolean(),
            existing_nullable=True
        )


def downgrade() -> None:
    """Downgrade schema: Rename long_exercise_completed back to hike_completed."""
    # Reverse the column rename
    with op.batch_alter_table('rule_revisions', schema=None) as batch_op:
        batch_op.alter_column(
            'long_exercise_completed',
            new_column_name='hike_completed',
            existing_type=sa.Boolean(),
            existing_nullable=True
        )
