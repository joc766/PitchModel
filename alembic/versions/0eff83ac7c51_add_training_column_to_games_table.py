"""Add training column to games table

Revision ID: 0eff83ac7c51
Revises: 533e31bcc063
Create Date: 2023-04-12 11:15:57.224525

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eff83ac7c51'
down_revision = '533e31bcc063'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('games', sa.Column('training', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column(sa.Column('games', 'training', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###
