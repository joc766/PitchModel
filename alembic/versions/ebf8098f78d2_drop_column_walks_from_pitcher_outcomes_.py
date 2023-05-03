"""drop column walks from pitcher_outcomes table

Revision ID: ebf8098f78d2
Revises: de11c69f5fef
Create Date: 2023-05-02 14:02:52.815202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebf8098f78d2'
down_revision = 'de11c69f5fef'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table without the walks column
    op.create_table(
        'pitcher_outcomes_new',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('pitcherId', sa.Integer, nullable=False),
        sa.Column('outs', sa.Integer),
        sa.Column('singles', sa.Integer),
        sa.Column('doubles', sa.Integer),
        sa.Column('triples', sa.Integer),
        sa.Column('home_runs', sa.Integer),
        sa.ForeignKeyConstraint(['pitcherId'], ['pitchers.id'])
    )

    # Copy the data from the original table to the new table
    op.execute("""
        INSERT INTO pitcher_outcomes_new (id, "pitcherId", outs, singles, doubles, triples, home_runs)
        SELECT id, "pitcherId", outs, singles, doubles, triples, home_runs
        FROM pitcher_outcomes;
    """)

    # Drop the original table
    op.drop_table('pitcher_outcomes')

    # Rename the new table to the original table name
    op.rename_table('pitcher_outcomes_new', 'pitcher_outcomes')


def downgrade():
    # Reverse the process to revert the schema change
    op.create_table(
        'pitcher_outcomes_new',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('pitcherId', sa.Integer, nullable=False),
        sa.Column('outs', sa.Integer),
        sa.Column('walks', sa.Integer),
        sa.Column('singles', sa.Integer),
        sa.Column('doubles', sa.Integer),
        sa.Column('triples', sa.Integer),
        sa.Column('home_runs', sa.Integer),
        sa.ForeignKeyConstraint(['pitcherId'], ['pitchers.id'])
    )

    op.execute("""
        INSERT INTO pitcher_outcomes_new (id, "pitcherId", outs, walks, singles, doubles, triples, home_runs)
        SELECT id, "pitcherId", outs, 0, singles, doubles, triples, home_runs
        FROM pitcher_outcomes;
    """)

    op.drop_table('pitcher_outcomes')
    op.rename_table('pitcher_outcomes_new', 'pitcher_outcomes')

