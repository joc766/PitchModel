import logging
from datetime import date, datetime
import math
# import json

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError

import statsapi

from models import Team, Game, Play, Player, Pitcher, Batter, Base, PitcherRating, BatterRating
from progressbar import progressbar


DB_FILE = 'data/mlb.db'
LOG_FILE = 'logs/data.log'

INITIAL_RATING = 1000

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
    print('Loading players...')
    for season in seasons:
        players = statsapi.get('sports_players', {'sportId': 1, 'season': season})['people']
        for p in progressbar(players):
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
    last_day_21 = date(2021, 10, 3)
    print('Retrieving schedule...')
    games = statsapi.schedule(start_date='04/01/2021', end_date='10/03/2021', sportId=1)
    games += statsapi.schedule(start_date='04/07/2022', end_date='10/02/2022', sportId=1)
    print('Schedule received.')
    print('Loading games...')
    for g in progressbar(games):
        # read the game date as a DateTime object
        g['game_date'] = date.fromisoformat(g['game_date'])
        szn = 2021 if g['game_date'] <= last_day_21 else 2022
        new_game = Game(id=g['game_id'], date=g['game_date'], homeTeamId=g['home_id'], awayTeamId=g['away_id'], venue=g['venue_name'], szn=szn)
        session.add(new_game)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning('Game {} already exists'.format(g['game_id']))
            continue
        # get play by play for the game
        plays = statsapi.get('game_playByPlay', {'gamePk': g['game_id']})['allPlays']
        for p in plays:
            new_play = Play(gameId=g['game_id'], result=p['result']['event'], pitcherId=p['matchup']['pitcher']['id'], batterId=p['matchup']['batter']['id'], game=new_game, atBatIndex=p['about']['atBatIndex'])
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
    print('Initializing pitcher ratings...')
    for pitcher in progressbar(pitchers):
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
    print('Initializing pitcher ratings...')
    for batter in progressbar(batters):
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

def get_number_of_games():
    print('Updating n_games for each pitcher...')
    # get all of the pitchers
    pitchers = session.query(Pitcher).all()
    for pitcher in progressbar(pitchers):
        # get the number of games for each pitcer
        count = session.query(Play).filter(Play.pitcherId == pitcher.playerId).count()
        pitcher.n_plays = count
        session.commit()
    
    # get all of the batters
    batters = session.query(Batter).all()
    print('Updating n_games for each batter...')
    for batter in progressbar(batters):
        # get the number of games for each batter
        count = session.query(Play).filter(Play.batterId == batter.playerId).count()
        batter.n_plays = count
        session.commit()

def clean_play_outcomes():
    all_plays = session.query(Play).all()

    bunt_outs = {'Bunt Groundout', 'Bunt Pop Out', 'Bunt Lineout', 'Bunt Flyout',\
                 'Bunt Forceout', 'Bunt Double Play', 'Bunt Grounded Into DP', 'Bunt Out'}
    
    caught_steals = {'Caught Stealing', 'Caught Stealing 2B', 'Caught Stealing 3B', 'Caught Stealing Home',\
                     'Caught Stealing 2B CS', 'Caught Stealing 3B CS', 'Caught Stealing Home CS'}
    
    pickoffs = {'Pickoff', 'Pickoff 1B', 'Pickoff 2B', 'Pickoff 3B', 'Pickoff Caught Stealing 2B',\
                'Pickoff Caught Stealing 3B', 'Pickoff Caught Stealing Home', 'Stolen Base 2B'}

    outs = {'Field Error', 'Field Out', 'Fielders Choice', 'Fielders Choice Out',\
            'Double Play', 'Forceout', 'Game Advisory', 'Grounded Into DP', 'Groundout',\
            'Lineout', 'Pop Out', 'Runner Out', 'Strikeout', 'Strikeout Double Play', 'Triple Play', 'Batter Out', 'Flyout',\
            'Sac Bunt', 'Sac Fly', 'Sac Fly Double Play', 'Sac Bunt Double Play'}
    
    walks_or_eq = {'Wild Pitch', 'Passed Ball', 'Intent Walk', 'Hit By Pitch', 'Balk', 'Catcher Interference'}
    print('Cleaning play outcomes...')
    i = 0
    updates = {
        'Bunt Out': 0,
        'Pickoff': 0,
        'Out': 0,
        'Walk': 0,
        'DNS': 0,
    }
    for play in progressbar(all_plays):
        if play.result in caught_steals or play.result in pickoffs:
            play.result = 'DNS'
            updates['DNS'] += 1
        elif play.result in outs or play.result in bunt_outs:
            play.result = 'Out'
            updates['Out'] += 1
        elif play.result in walks_or_eq:
            play.result = 'Walk'
            updates['Walk'] += 1
        if i+1 % 100 == 0:
            session.commit()
        i += 1
    session.commit()
    print(updates)
        
        
def add_training_column():
    all_rows = session.query(Play).options(joinedload(Play.game)).order_by(asc(Play.game.date)).all()
    split_index = int(len(all_rows) * 0.75)
    training_rows = all_rows[:split_index]
    testing_rows = all_rows[split_index:]
    for row in training_rows:
        row.training = True

    for row in testing_rows:
        row.training = False
    
    session.commit()

def assign_training_data():
    # Define the split percentage
    TRAINING_PERCENTAGE = 0.75

    # Get all plays from the database
    games = session.query(Game).all()

    # Sort the plays chronologically by date
    games_sorted = sorted(games, key=lambda game: game.date)

    # Calculate the number of training and testing rows based on the split percentage
    n_training = math.ceil(len(games_sorted) * TRAINING_PERCENTAGE)
    # n_testing = len(games_sorted) - n_training

    # print(n_testing, n_training)

    # Update the training/testing flag for the appropriate number of rows
    for i, game in enumerate(games_sorted):
        if i < n_training:
            game.training = True
        else:
            game.training = False

    # Commit the changes to the database
    session.commit()


def main():
    Base.metadata.create_all(engine)
    read_all_games()
    # read_all_players([2021, 2022])
    # get_number_of_games()
    # initialize_ratings()
    clean_play_outcomes()
    # set the 'training' column to True for all rows
    # add_training_column()
    assign_training_data()

    session.close()


if __name__ == "__main__":
    main()
    session.close()
