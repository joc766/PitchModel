import logging
# import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import statsapi

from models import Team, Game, Play, Player, Pitcher, Batter, Base, PitcherRating, BatterRating


DB_FILE = 'data/mlb.db'
LOG_FILE = 'logs/data.log'

engine = create_engine('sqlite:///' + DB_FILE, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

logger = logging.getLogger(__name__)
handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def read_all_players(seasons):
    for season in seasons:
        players = statsapi.get('sports_players', {'sportId': 1, 'season': season})['people']
        for p in players:
            if not p.get('primaryNumber'):
                p['primaryNumber'] = 'NA'
            new_player = Player(id=p['id'], fullName=p['fullName'], firstName=p['firstName'], lastName=p['lastName'], primaryNumber=p['primaryNumber'], position=p['primaryPosition']['abbreviation'], teamId=p["currentTeam"]["id"])
            session.add(new_player)

            # just add every player as a two-way player
            new_pitcher = Pitcher(playerId=p['id'], pitchHand=p['pitchHand']['code'])
            session.add(new_pitcher)
            new_batter = Batter(playerId=p['id'], batSide=p['batSide']['code'])
            session.add(new_batter)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.warning('Player {} already exists'.format(p['id']))


def read_all_teams():
    teams = statsapi.get('teams', {'sportId': 1})['teams']   
    for t in teams:
        new_team = Team(id=t['id'], name=t['name'], abbreviation=t['abbreviation'], locationName=t['locationName'])
        session.add(new_team)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning('Team {} already exists'.format(t['id']))


def read_all_games():
    print('Retrieving schedule...')
    games = statsapi.schedule(start_date='04/07/2022', end_date='10/02/2022', sportId=1)
    print('Schedule received.')
    for i, g in enumerate(games):
        if i % 100 == 0:
            print('Processing game {} of {}'.format(i, len(games)))
        new_game = Game(id=g['game_id'], date=g['game_date'], homeTeamId=g['home_id'], awayTeamId=g['away_id'], venue=g['venue_name'])
        session.add(new_game)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning('Game {} already exists'.format(g['game_id']))
        # get play by play for the game
        plays = statsapi.get('game_playByPlay', {'gamePk': g['game_id']})['allPlays']
        for p in plays:
            new_play = Play(gameId=g['game_id'], result=p['result']['event'], pitcherId=p['matchup']['pitcher']['id'], batterId=p['matchup']['batter']['id'], game=new_game)
            session.add(new_play)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.warning('Play already exists for game {}'.format(g['game_id']))

def initialize_ratings():
    # Create a rating for each pitcher
    pitchers = session.query(Pitcher).all()
    i = 0
    for pitcher in pitchers:
        rating = PitcherRating(id=i, pitcherId=pitcher.id, value=1500)
        pitcher.ratingId = i
        session.commit()
        session.add(rating)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            print('Rating for pitcher {} already exists'.format(pitcher.playerId))
        i += 1

    # Create a rating for each batter
    batters = session.query(Batter).all()
    for batter in batters:
        rating = BatterRating(id=i, batterId=batter.id, value=1500)
        batter.ratingId = i
        session.commit()
        session.add(rating)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            print('Rating for batter {} already exists'.format(batter.playerId))
        i += 1

def reset_ratings():
    # Reset pitcher ratings
    pitchers = session.query(Pitcher).all()
    for pitcher in pitchers:
        rating = session.query(PitcherRating).filter_by(id=pitcher.ratingId).first()
        rating.value = 1500
        session.commit()

    # Reset batter ratings
    batters = session.query(Batter).all()
    for batter in batters:
        rating = session.query(BatterRating).filter_by(id=batter.ratingId).first()
        rating.value = 1500
        session.commit()


def main():
    Base.metadata.create_all(engine)
    # read_all_players([2022])
    # initialize_ratings()
    reset_ratings()

if __name__ == "__main__":
    main()
    session.close()
