import sys

from models import Pitcher, Batter, Play
from utils import calculate_ev
from db_utils import create_session_scope, get_all_games, get_all_plays
from prediction_model import PredictionModel, EloModel, DumbModel, RandomModel, results_table, partial_results_table

def test_partial_pbp(model: PredictionModel, session, results_table=partial_results_table):
    """Test the play by play accuracy of the model
    
        returns: (wrong_predictions, n_plays, total_outcome)
    """     

    wrong_predictions = 0
    n_plays = 0
    total_outcome = 0.0
    print(results_table)

    for play in get_all_plays(session, training=False):
        result = play.result
        # only test plays that are not outs
        if result != 'DNS': 
            prediction = model.predict_partial(play)
            # print(prediction) # prediction is in terms of expected batter wins
            observed = results_table[result] 

            if observed != -1:
                total_outcome += observed
                if observed != prediction:
                    wrong_predictions += 1
                n_plays += 1
                total_outcome += observed
        
    return wrong_predictions, n_plays, total_outcome

def test_partial_lt(model: PredictionModel, session, results_table=partial_results_table):
    """ Test how accurate the model is at projecting long-term outcomes """
    total_wins = 0
    expected_wins = 0
    n_plays = 0

    testing_plays = get_all_plays(session, training=False)

    for play in testing_plays:
        result = play.result
        # only test plays that are not outs
        prediction = model.predict_partial(play)
        # print(prediction)
        observed = results_table[result] 
        if observed != -1:
            total_wins += observed
            expected_wins += prediction
            n_plays += 1
        
    return total_wins, expected_wins, n_plays

def test_lt(model: PredictionModel, session, results_table=results_table):
    """ Test how accurate the model is at projecting long-term outcomes """
    total_wins = 0
    expected_wins = 0
    n_plays = 0

    testing_plays = get_all_plays(session, training=False)

    for play in testing_plays:
        prediction = model.predict(play)
        result = play.result
        observed = results_table[result] 
        if observed != -1:
            total_wins += observed
            expected_wins += prediction
            n_plays += 1
        
    return total_wins, expected_wins, n_plays
    
def test_pbp(model: PredictionModel, session, results_table=results_table):
    """Test the play by play accuracy of the model
    
        returns: (wrong_predictions, n_plays, total_outcome)
    """     

    wrong_predictions = 0
    n_plays = 0
    total_outcome = 0.0

    for play in get_all_plays(session, training=False):

        prediction = model.predict(play)
        # print(prediction) # prediction is in terms of expected batter wins
        result = play.result
        observed = results_table[result] 

        if observed != -1:
            total_outcome += observed
            if observed != prediction:
                wrong_predictions += 1
            n_plays += 1
            total_outcome += observed
        
    return wrong_predictions, n_plays, total_outcome

def main():
    NORMAL_MODE = 0
    PARTIAL_MODE = 1

    modes = {
        "partial": PARTIAL_MODE,
        "normal": NORMAL_MODE
    }

    try:
        mode = modes[sys.argv[1]] if len(sys.argv) > 1 else NORMAL_MODE
    except KeyError:
        print(f"Invalid mode: {sys.argv[1]}")
        return
    
    with create_session_scope() as session:
        elo_model = EloModel(session)
        # elo_model.train(suppress_output=False)
        dumb_model = DumbModel()
        random_model = RandomModel()
        if mode == PARTIAL_MODE:
            # wrong_predictions, n_plays, total_outcome = test_partial_pbp(elo_model, session)
            # print(f"Play-by-Play Inaccuracy: {wrong_predictions / n_plays}")

            wrong_predictions, n_plays, total_outcome = test_partial_pbp(dumb_model, session)
            print(f"Average outcome = {total_outcome / n_plays}")


            total_wins, expected_wins, n_plays = test_partial_lt(elo_model, session)
            print(f"Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

            total_wins, expected_wins, n_plays = test_partial_lt(dumb_model, session)
            print(f"Baseline Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

            total_wins, expected_wins, n_plays = test_partial_lt(random_model, session)
            print(f"Random Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")
        
        if mode == NORMAL_MODE:

            total_wins, expected_wins, n_plays = test_lt(elo_model, session)
            print(f"Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

            wrong_predictions, n_plays, total_outcome = test_pbp(elo_model, session)
            print(f"Play-by-Play Inaccuracy: {wrong_predictions / n_plays}")

            wrong_predictions, n_plays, total_outcome = test_pbp(dumb_model, session)
            print(f"Baseline Inaccuracy: {wrong_predictions / n_plays}")

            wrong_predictions, n_plays, total_outcome = test_pbp(random_model, session)
            print(f"Random Inaccuracy: {wrong_predictions / n_plays}")

if __name__ == "__main__":
    main()