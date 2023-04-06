from models import Base, Team, Game, Play, Player, Pitcher, Batter, PitcherRating, BatterRating
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import numpy as np
import math

from progressbar import progressbar
from collections import defaultdict

import time


DB_FILE = 'data/mlb.db'

engine = create_engine('sqlite:///' + DB_FILE, echo=False)

Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)

K = 16
SIGMA = 400
PLAYS_PER_UPDATE = 100
MAX_RESULT = 5
GROWTH_RATE = 9
K_FACTOR = 1

# 8 represents a full win for the batter, 0 represents a full loss for the batter
# -1 for a do not count
# results_table = {
#     'DNS': -1,
#     'Out': 0,
#     'Walk': 14,
#     'Single': 15,
#     'Double': 16,
#     'Triple': 17,
#     'Home Run': 20,
# }

def logistic_func(c, a, k, x):
    return c / (1 + a * math.exp(-k * x))

results_table = {
    'DNS': -1,
    'Out': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 0),
    'Walk': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 1),
    'Single': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 2),
    'Double': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 3),
    'Triple': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 4),
    'Home Run': logistic_func(MAX_RESULT, GROWTH_RATE, K_FACTOR, 5),
}

def calculate_ev(r_a, r_b):
    return 1 / (1 + 10 ** ((r_b - r_a) / SIGMA))

def test_performance(pitchers_table=None, batters_table=None):
    """Test the performance of the model on the test set
    
    Returns:
        total_inaccuracy (float): the total inaccuracy of the model
        average_inaccuracy (float): the average inaccuracy of the model
        average_outcome (float): the average outcome of the model
    """
    if pitchers_table is None:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
    
    if batters_table is None:
        all_batters = session.query(Batter).all()
        batters_table = {batter.playerId: batter for batter in all_batters}

    print("Measuring Model Performance...")
    testing_plays = session.query(Play).filter(Play.training == False).all()
    
    max_result = MAX_RESULT

    # measure the accuracy of the model
    total_inaccuracy = 0.0
    n_plays = 0
    total_outcome = 0.0
    for play in testing_plays:
        pitcher_rating = pitchers_table[play.pitcherId].rating.value
        batter_rating = batters_table[play.batterId].rating.value

        e_b = calculate_ev(batter_rating, pitcher_rating)
        prediction = e_b
        result = play.result
        observed = results_table[result] 
        if observed != -1:
            observed /= max_result
            total_outcome += observed
            inaccuracy = abs(observed - prediction)
            total_inaccuracy += inaccuracy
            n_plays += 1
        
    return total_inaccuracy, total_inaccuracy / n_plays, total_outcome/n_plays




def main():
    # select all of the games with training = True
    games = session.query(Game).all()
    
    all_pitchers = session.query(Pitcher).all()
    all_batters = session.query(Batter).all()

    pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
    batters_table = {batter.playerId: batter for batter in all_batters}

    # the three elements in the values are the total e_p, s_p, and the number of plays for that player since last update
    pitcher_ratings = {pitcher.playerId: pitcher.rating.value for pitcher in all_pitchers}
    batter_ratings = {batter.playerId: batter.rating.value for batter in all_batters}

    print('Simulating Games...')
    max_val = max(results_table.values())
    for game in progressbar(games):
        # game_pitcher_rewards tracks the pitcher's expected value and scored value for each game. An update will be made at the end of the game
        game_pitcher_rewards = dict.fromkeys([play.pitcherId for play in game.plays], [0, 0])
        game_batter_rewards = dict.fromkeys([play.batterId for play in game.plays], [0, 0])
        for play in game.plays:
            if play.training:
                if results_table[play.result] == -1:
                    continue

                e_b = calculate_ev(batter_ratings[play.batterId], pitcher_ratings[play.pitcherId])
                e_p = 1 - e_b
                game_pitcher_rewards[play.pitcherId][0] += e_p
                game_batter_rewards[play.batterId][0] += e_b

                # normallize the play result to be between 0 and 1
                s_b = results_table[play.result] / max_val
                s_p = 1 - s_b
                game_pitcher_rewards[play.pitcherId][1] += s_p
                game_batter_rewards[play.batterId][1] += s_b

        for pitcher_id, (e_p, s_p) in game_pitcher_rewards.items():
            pitcher_ratings[pitcher_id] += K * (s_p - e_p)
        
        for batter_id, (e_b, s_b) in game_batter_rewards.items():
            batter_ratings[batter_id] += K * (s_b - e_b)
    
    # update all of the pitchers' ratings in the database if they are different from before
    print("updating pitcher ratings...")
    for pitcher_id, rating in progressbar(pitcher_ratings.items()):
        pitcher = pitchers_table[pitcher_id]
        if pitcher.rating.value != rating:
            pitcher.rating.value = rating
            session.commit()
    
    # update all of the batters' ratings in the database if they are different from before
    print("updating batter ratings...")
    for batter_id, rating in progressbar(batter_ratings.items()):
        batter = batters_table[batter_id]
        if batter.rating.value != rating:
            batter.rating.value = rating
            session.commit()

    results = test_performance(pitchers_table, batters_table)
    print("Total Inaccuracy: {}".format(results[0]))
    print("Average Inaccuracy: {}".format(results[1]))
    print("Average outcome: {}".format(results[2]))


if __name__ == "__main__":
    main()
    # results = test_performance()
    # print("Total Inaccuracy: {}".format(results[0]))
    # print("Average Inaccuracy: {}".format(results[1]))
    # print("Average Outcome: {}".format(results[2]))