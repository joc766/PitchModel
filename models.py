from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base= declarative_base()


class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    locationName = Column(String(255), nullable=False)

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=False)
    fullName = Column(String(255), nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    primaryNumber = Column(String(20))
    position = Column(String(4))
    teamId = Column(Integer, ForeignKey('teams.id'))

    team = relationship("Team", backref=backref("players", uselist=False))

class Pitcher(Base):
    __tablename__ = 'pitchers'

    id = Column(Integer, primary_key=True)
    playerId = Column(Integer, ForeignKey('players.id'))
    pitchHand = Column(String(10))

    player = relationship("Player", backref=backref("pitcher", uselist=False))

class Batter(Base):
    __tablename__ = 'batters'

    id = Column(Integer, primary_key=True)
    playerId = Column(Integer, ForeignKey('players.id'))
    batSide = Column(String(10))

    player = relationship("Player", backref=backref("batter", uselist=False))

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, autoincrement=False)

    date = Column(String(20))
    homeTeamId = Column(Integer, ForeignKey('teams.id'))
    awayTeamId = Column(Integer, ForeignKey('teams.id'))
    venue = Column(String(255))

    plays = relationship("Play", back_populates="game")


class Play(Base):
    __tablename__ = 'plays'

    id = Column(Integer, primary_key=True, autoincrement=True)

    gameId = Column(Integer, ForeignKey('games.id'))
    result = Column(String(255))
    pitcherId = Column(Integer, ForeignKey('pitchers.id'))
    batterId = Column(Integer, ForeignKey('batters.id'))

    game = relationship("Game", back_populates="plays")


