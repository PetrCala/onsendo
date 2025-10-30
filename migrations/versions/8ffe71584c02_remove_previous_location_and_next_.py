"""Remove previous_location and next_location from visit table

Revision ID: 8ffe71584c02
Revises: 62c926c2f8af
Create Date: 2025-10-30 18:21:55.161891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ffe71584c02'
down_revision: Union[str, Sequence[str], None] = '62c926c2f8af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('onsen_visits', schema=None) as batch_op:
        batch_op.drop_column('previous_location')
        batch_op.drop_column('next_location')


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('onsen_visits', schema=None) as batch_op:
        batch_op.add_column(sa.Column('next_location', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('previous_location', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key(None, 'onsen_visits', ['previous_location'], ['id'])
        batch_op.create_foreign_key(None, 'onsen_visits', ['next_location'], ['id'])
