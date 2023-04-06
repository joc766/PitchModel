"""Change Game date column to Date type

Revision ID: 533e31bcc063
Revises: c6d9d9f2a9b2
Create Date: 2023-04-02 15:07:03.157905

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '533e31bcc063'
down_revision = 'c6d9d9f2a9b2'
branch_labels = None
depends_on = None


from sqlalchemy import String, Date, text, Column, Integer, ForeignKey
from sys import stderr

def upgrade():
    print('Changing Game.date column to Date type...', file=stderr)
    # Create a new temporary table with the desired schema
    op.create_table(
        'games_temp',
        Column('id', Integer, primary_key=True, autoincrement=False),
        Column('date', Date),
        Column('homeTeamId', Integer, ForeignKey('teams.id')),
        Column('awayTeamId', Integer, ForeignKey('teams.id')),
        Column('venue', String(255)),
        Column('szn', Integer)
    )

    # Copy the data from the original table to the temporary table, converting date strings to Date objects
    op.execute("INSERT INTO games_temp SELECT id, substr(date, 1, 10), homeTeamId, awayTeamId, venue, szn FROM games")

    # Drop the original table
    op.drop_table('games')

    # Rename the temporary table to the original table's name
    op.rename_table('games_temp', 'games')


def downgrade():
    print('Changing Game.date column to String type...', file=stderr)
    # Create a new temporary table with the original schema
    op.create_table(
        'games_temp',
        Column('id', Integer, primary_key=True, autoincrement=False),
        Column('date', String(20)),
        Column('homeTeamId', Integer, ForeignKey('teams.id')),
        Column('awayTeamId', Integer, ForeignKey('teams.id')),
        Column('venue', String(255)),
        Column('szn', Integer)
    )

    # Copy the data from the original table to the temporary table, converting Date objects to string format
    op.execute("INSERT INTO games_temp SELECT id, strftime('%Y-%m-%d', date), homeTeamId, awayTeamId, venue, szn FROM games")

    # Drop the original table
    op.drop_table('games')

    # Rename the temporary table to the original table's name
    op.rename_table('games_temp', 'games')


