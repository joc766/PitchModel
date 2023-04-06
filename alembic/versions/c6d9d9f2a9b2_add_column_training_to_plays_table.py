"""Add column training to plays table

Revision ID: c6d9d9f2a9b2
Revises: 
Create Date: 2023-04-02 14:53:40.242245

"""
from alembic import op
import sqlalchemy as sa
from sys import stderr


# revision identifiers, used by Alembic.
revision = 'c6d9d9f2a9b2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    print("Adding column training to plays...", file=stderr)
    op.add_column('plays', sa.Column('training', sa.Boolean, nullable=False, server_default=sa.text('true')))

def downgrade() -> None:
    print("Dropping column training from plays...", file=stderr)
    # op.drop_column('my_table', 'training')
