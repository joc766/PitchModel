"""create table pitcher_outcomes and link to pitchers table

Revision ID: de11c69f5fef
Revises: 09b867b67369
Create Date: 2023-04-24 10:08:50.137321

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de11c69f5fef'
down_revision = '09b867b67369'
branch_labels = None
depends_on = None


"""create table pitcher_outcomes and link to pitchers table

Revision ID: <revision_id>
Revises: <previous_revision_id> (if applicable)
Create Date: <create_date>

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
# revision = '<revision_id>'
# down_revision = '<previous_revision_id>'
# create_date = '<create_date>'


def upgrade():
    # create pitcher_outcomes table
    op.create_table('pitcher_outcomes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pitcherId', sa.Integer(), nullable=False),
        sa.Column('outs', sa.Integer(), nullable=True),
        sa.Column('walks', sa.Integer(), nullable=True),
        sa.Column('singles', sa.Integer(), nullable=True),
        sa.Column('doubles', sa.Integer(), nullable=True),
        sa.Column('triples', sa.Integer(), nullable=True),
        sa.Column('home_runs', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['pitcherId'], ['pitchers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    with op.batch_alter_table('pitchers') as batch_op:
        batch_op.add_column(sa.Column('outcomesId', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('pitchers_outcomes_fk', 'pitcher_outcomes', ['outcomesId'], ['id'])


def downgrade():
    pass
