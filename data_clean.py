import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import statsapi

from models import Player, Pitcher, Batter, Base


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
            new_player = Player(id=p['id'], fullName=p['fullName'], firstName=p['firstName'], lastName=p['lastName'], primaryNumber=p['primaryNumber'], position=p['primaryPosition']['abbreviation'])
            session.add(new_player)

            if new_player.position == 'P':
                new_pitcher = Pitcher(playerId=p['id'], pitchHand=p['pitchHand']['code'])
                session.add(new_pitcher)
            else:
                new_batter = Batter(playerId=p['id'], batSide=p['batSide']['code'])
                session.add(new_batter)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.warning('Player {} already exists'.format(p['id']))

def read_all_games(seasons):
    pass
            

def main():
    # set up sqlalchemy
    Base.metadata.create_all(engine)
    # read all players
    read_all_players([2022])

if __name__ == "__main__":
    main()