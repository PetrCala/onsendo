"""Remove is_onsen_monitoring column from activities

Revision ID: 3d0828df1f83
Revises: 75f5027ba821
Create Date: 2025-10-30 20:31:50.930372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d0828df1f83'
down_revision: Union[str, Sequence[str], None] = '75f5027ba821'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove is_onsen_monitoring column from activities table.

    NOTE: Before running this migration, you should run the one-off data migration script:
        python scripts/migrate_onsen_monitoring_type.py [--env dev|prod]

    This ensures all activities with is_onsen_monitoring=True have their activity_type
    set to 'onsen_monitoring' before the column is dropped.
    """
    # Drop the is_onsen_monitoring column
    op.drop_column('activities', 'is_onsen_monitoring')


def downgrade() -> None:
    """
    Re-add is_onsen_monitoring column to activities table.

    NOTE: This downgrade migration will add the column back but set all values to False.
    If you need to restore the original values, you would need to identify activities
    with activity_type='onsen_monitoring' and manually set is_onsen_monitoring=True.
    """
    # Re-add the is_onsen_monitoring column (all values will be False by default)
    op.add_column('activities', sa.Column('is_onsen_monitoring', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Optional: Populate is_onsen_monitoring based on activity_type
    # Uncomment if you want automatic restoration during downgrade
    # op.execute("""
    #     UPDATE activities
    #     SET is_onsen_monitoring = TRUE
    #     WHERE activity_type = 'onsen_monitoring'
    # """)
