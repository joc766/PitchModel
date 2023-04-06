import math
from progressbar import progressbar
from models import Base, Team, Game, Play, Player, Pitcher, Batter, PitcherRating, BatterRating
from db_utils import create_session_scope

SIGMA = 400

MAX_RESULT = 5
GROWTH_RATE = 9
K_FACTOR = 0.5

Y_INTERCEPT = 2.5

def calculate_ev(r_a, r_b):
    return 1 / (1 + 10 ** ((r_b - r_a) / SIGMA))

def logistic_func(x):
    return MAX_RESULT / (1 + GROWTH_RATE * math.exp(-K_FACTOR * x))

def quadratic_func(x):
    return 0.2 * (x-1)**2 + Y_INTERCEPT

def basic_func(x):
    return 1.0

def test_performance(results_table, pitchers_table=None, batters_table=None, session=None):
    """Test the performance of the model on the test set
    
    Returns:
        total_inaccuracy (float): the total inaccuracy of the model
        average_inaccuracy (float): the average inaccuracy of the model
        average_outcome (float): the average outcome of the model
    """
    with create_session_scope(session) as session:
        if not pitchers_table:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        if not batters_table:
            all_batters = session.query(Batter).all()
            batters_table = {batter.playerId: batter for batter in all_batters}

        print("Measuring Model Performance...")
        testing_plays = session.query(Play).filter(Play.training == False).all()
        
        max_result = max(results_table.values())

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