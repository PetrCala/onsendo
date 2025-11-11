"""Remove time_of_day from weight_measurements

Revision ID: f4cb55698f58
Revises: 7ebde1e9c4a6
Create Date: 2025-11-11 16:43:28.451679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4cb55698f58'
down_revision: Union[str, Sequence[str], None] = '7ebde1e9c4a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove time_of_day column from weight_measurements
    op.drop_column('weight_measurements', 'time_of_day')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add time_of_day column to weight_measurements
    op.add_column('weight_measurements', sa.Column('time_of_day', sa.String(), nullable=True))
