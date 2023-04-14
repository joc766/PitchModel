from models import Pitcher, Batter
from utils import calculate_ev
from db_utils import create_session_scope, get_all_games, get_all_plays
from prediction_model import EloModel, DumbModel, results_table

def test_long_term(model, session):
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
    
def test_play_by_play(model, session, results_table=results_table):
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
    

if __name__ == "__main__":
    # total_wins, expected_wins, n_plays = test_long_term()
    # print(f"Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

    with create_session_scope() as session:

        elo_model = EloModel(session)
        dumb_model = DumbModel()

        total_wins, expected_wins, n_plays = test_long_term(elo_model, session)
        print(f"Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

        wrong_predictions, n_plays, total_outcome = test_play_by_play(elo_model, session)
        print(f"Play-by-Play Inaccuracy: {wrong_predictions / n_plays}")

        wrong_predictions, n_plays, total_outcome = test_play_by_play(dumb_model, session)
        print(f"Baseline Inaccuracy: {wrong_predictions / n_plays}")
