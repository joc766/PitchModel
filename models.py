from enum import Enum, auto 

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship, backref, reconstructor
from sqlalchemy.ext.declarative import declarative_base

DB_FILE = 'data/mlb.db'

Base = declarative_base()
engine = create_engine('sqlite:///' + DB_FILE, echo=False)

class Position(Enum):
    PITCHER = 0
    BATTER = 1

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    locationName = Column(String(255), nullable=False)

    # could later add a pitcher or batter relationship for picking lineups

    def __str__(self):
        return self.name

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=False)
    fullName = Column(String(255), nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    primaryNumber = Column(String(20))
    position = Column(String(4))
    teamId = Column(Integer, ForeignKey('teams.id'))

    team = relationship("Team")

    def __str__(self):
        return f"{self.fullName}, {self.position}, {self.team}"
    

class PitcherOutcome(Base):
    __tablename__ = 'pitcher_outcomes'

    id = Column(Integer, primary_key=True)
    pitcherId = Column(Integer, ForeignKey('pitchers.id'))
    outs = Column(Integer)
    singles = Column(Integer)
    doubles = Column(Integer)
    triples = Column(Integer)
    home_runs = Column(Integer)

    pitcher = relationship("Pitcher", uselist=False, foreign_keys=[pitcherId])

    outcome_columns = {
        'out': 'outs',
        'single': 'singles',
        'double': 'doubles',
        'triple': 'triples',
        'home run': 'home_runs',
    }

    def get_outcome_count(self, outcome_str: str):
        column_name = self.outcome_columns[outcome_str.lower()]
        return getattr(self, column_name)
    
    def increment_outcome_count(self, outcome_str: str, increment=1):
        # still need to session.commit() after calling this
        column_name = self.outcome_columns[outcome_str.lower()]
        current_value = getattr(self, column_name)
        new_value = current_value + increment
        setattr(self, column_name, new_value)
        return new_value

    def __str__(self):
        return f"{self.pitcherId}: {self.pitcher.player.fullName}, {self.pitcher.player.team}"

class Pitcher(Base):
    __tablename__ = 'pitchers'

    id = Column(Integer, primary_key=True)
    playerId = Column(Integer, ForeignKey('players.id'))
    ratingId = Column(Integer, ForeignKey('pitcher_ratings.id'))
    pitchHand = Column(String(10))
    n_plays = Column(Integer, default=0)
    outcomesId = Column(Integer, ForeignKey('pitcher_outcomes.id'))

    player = relationship("Player", foreign_keys=[playerId])
    rating = relationship("PitcherRating", uselist=False, foreign_keys=[ratingId])
    outcomes = relationship("PitcherOutcome", uselist=False, foreign_keys=[outcomesId])

    def __str__(self):
        return f"{self.id}: {self.player.fullName}, {self.player.team}"

    def __hash__(self):
        return hash(self.id)

class Batter(Base):
    __tablename__ = 'batters'

    id = Column(Integer, primary_key=True)
    playerId = Column(Integer, ForeignKey('players.id'))
    ratingId = Column(Integer, ForeignKey('batter_ratings.id'))
    batSide = Column(String(10))
    n_plays = Column(Integer, default=0)

    player = relationship("Player", foreign_keys=[playerId])
    rating = relationship("BatterRating", uselist=False, foreign_keys=[ratingId])

    def __str__(self):
        return f"{self.id}: {self.player.fullName}, {self.player.team}"

    def __hash__(self):
        return hash(self.id)

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, autoincrement=False)

    date = Column(Date)
    homeTeamId = Column(Integer, ForeignKey('teams.id'))
    awayTeamId = Column(Integer, ForeignKey('teams.id'))
    venue = Column(String(255))
    szn = Column(Integer)
    training = Column(Boolean, default=True)

    plays = relationship("Play", order_by="Play.atBatIndex", back_populates="game", uselist=True)


class Play(Base):
    __tablename__ = 'plays'

    id = Column(Integer, primary_key=True, autoincrement=True)

    gameId = Column(Integer, ForeignKey('games.id'))
    result = Column(String(255))
    pitcherId = Column(Integer, ForeignKey('pitchers.playerId'))
    batterId = Column(Integer, ForeignKey('batters.playerId'))
    atBatIndex = Column(Integer)
    inning = Column(Integer)
    outs = Column(Integer)
    runnersOn = Column(Integer)

    game = relationship("Game", back_populates="plays", uselist=False)
    pitcher = relationship("Pitcher")
    batter = relationship("Batter")


class PitcherRating(Base):
    __tablename__ = 'pitcher_ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    pitcherId = Column(Integer, ForeignKey('pitchers.id'))
    value = Column(Integer)

    pitcher = relationship("Pitcher", uselist=False, foreign_keys=[pitcherId])

    def __str__(self):
        return f"{self.value}"
    
class BatterRating(Base):
    __tablename__ = 'batter_ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    batterId = Column(Integer, ForeignKey('batters.id'))
    value = Column(Integer)

    batter = relationship("Batter", uselist=False, foreign_keys=[batterId])

    def __str__(self):
        return f"{self.value}"



