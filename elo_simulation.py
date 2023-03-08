from models import Base, Team, Game, Play, Player, Pitcher, Batter, PitcherRating, BatterRating
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from progressbar import progressbar
from collections import defaultdict


DB_FILE = 'data/mlb.db'

engine = create_engine('sqlite:///' + DB_FILE, echo=False)

Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)

K = 32
SIGMA = 400

def calculate_ev(r_a, r_b):
    return 1 / (1 + 10 ** ((r_b - r_a) / SIGMA))
    

def main():
    games = session.query(Game).all()
    for game in progressbar(games):
        # these dictionaries will hold the pitcher or batter, their total expected reward, and their total actual reward for the game
        game_pitchers = defaultdict(lambda: [0, 0])
        game_batters = defaultdict(lambda: [0, 0])
        for play in game.plays:
            pitcher = session.query(Pitcher).filter_by(playerId=play.pitcherId).first()
            batter = session.query(Batter).filter_by(playerId=play.batterId).first()
            try:
                e_p = calculate_ev(pitcher.rating.value, batter.rating.value)
            except Exception as e:
                print(pitcher)
                print(batter)
                raise e
            e_b = 1 - e_p
            game_pitchers[play.pitcherId][0] += e_p
            game_batters[play.batterId][0] += e_b

            s_b = None
            play_result = play.result
            if play_result == 'Single' or play_result == 'Walk' or play_result == 'Hit By Pitch':
                s_b = 5
            elif play_result == 'Double':
                s_b = 6
            elif play_result == 'Triple':
                s_b = 7
            elif play_result == 'Home Run':
                s_b = 8
            else:
                s_b = 0
            
            s_b = s_b / 8
            game_batters[play.batterId][1] += s_b
            game_pitchers[play.pitcherId][1] += 1 - s_b
        # update the ratings for each pitcher and batter
        for pitcher_id, (e_p, s_p) in game_pitchers.items():
            pitcher = session.query(Pitcher).filter_by(playerId=pitcher_id).first()
            pitcher.rating.value += K * (s_p - e_p)
            session.commit()


if __name__ == "__main__":
    main()