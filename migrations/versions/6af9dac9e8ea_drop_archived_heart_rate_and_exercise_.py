"""drop archived heart rate and exercise tables

Revision ID: 6af9dac9e8ea
Revises: 3d0828df1f83
Create Date: 2025-10-31 18:37:03.230312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6af9dac9e8ea'
down_revision: Union[str, Sequence[str], None] = '3d0828df1f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop archived heart rate and exercise tables - no longer needed with unified Activity model."""
    # Drop archived tables
    op.drop_table('heart_rate_data_archived')
    op.drop_table('exercise_sessions_archived')


def downgrade() -> None:
    """No downgrade - this is a permanent purge of archived tables."""
    # Cannot recreate these tables - data is permanently deleted
    raise NotImplementedError("Cannot downgrade - archived tables have been permanently purged")
