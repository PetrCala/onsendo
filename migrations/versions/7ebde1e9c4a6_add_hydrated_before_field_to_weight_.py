"""Add hydrated_before field to weight_measurements

Revision ID: 7ebde1e9c4a6
Revises: bc54de4d293d
Create Date: 2025-11-11 16:37:20.466901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ebde1e9c4a6'
down_revision: Union[str, Sequence[str], None] = 'bc54de4d293d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add hydrated_before column to weight_measurements
    op.add_column('weight_measurements', sa.Column('hydrated_before', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove hydrated_before column from weight_measurements
    op.drop_column('weight_measurements', 'hydrated_before')
