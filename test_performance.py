from models import Pitcher, Batter, Play, Game
from elo_simulation import results_table
from utils import calculate_ev, logistic_func
from db_utils import create_session_scope, get_all_games, get_all_plays

def test_long_term(pitchers_table=None, batters_table=None, session=None):
    """ Test how accurate the model is at projecting long-term outcomes """
    total_wins = 0
    expected_wins = 0
    n_plays = 0

    with create_session_scope(session) as session:
        if not pitchers_table:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        if not batters_table:
            all_batters = session.query(Batter).all()
            batters_table = {batter.playerId: batter for batter in all_batters}

        testing_plays = get_all_plays(session, training=False)

        for play in testing_plays:
            pitcher_rating = pitchers_table[play.pitcherId].rating.value
            batter_rating = batters_table[play.batterId].rating.value

            e_b = calculate_ev(batter_rating, pitcher_rating)
            prediction = 1 if e_b > 0.5 else 0
            result = play.result
            observed = results_table[result] 
            if observed != -1:
                total_wins += observed
                expected_wins += prediction
                n_plays += 1
            
        return total_wins, expected_wins, n_plays
    
def test_play_by_play(results_table, pitchers_table=None, batters_table=None, session=None):
    """Test the play by play accuracy of the model
    
        returns: (wrong_predictions, n_plays, total_outcome)
    """
    with create_session_scope(session) as session:
        if not pitchers_table:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        if not batters_table:
            all_batters = session.query(Batter).all()
            batters_table = {batter.playerId: batter for batter in all_batters}
            
        testing_plays = get_all_plays(session, training=False)

        # measure the accuracy of the model
        wrong_predictions = 0
        n_plays = 0
        total_outcome = 0.0
        for play in testing_plays:
            pitcher_rating = pitchers_table[play.pitcherId].rating.value
            batter_rating = batters_table[play.batterId].rating.value

            e_b = calculate_ev(batter_rating, pitcher_rating)
            prediction = int(e_b > 0.5) # predict a win if the batter is expected to win else predict a loss
            result = play.result
            observed = results_table[result] 

            if observed != -1:
                total_outcome += observed
                if observed != prediction:
                    wrong_predictions += 1
                n_plays += 1
                total_outcome += observed
            
        return wrong_predictions, n_plays, total_outcome
    
def test_baseline(results_table, pitchers_table=None, batters_table=None, session=None):
    """ Test the accuracy of the baseline model
    
        returns: (wrong_predictions, n_plays, total_outcome)
        """
    with create_session_scope(session) as session:
        if not pitchers_table:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        if not batters_table:
            all_batters = session.query(Batter).all()
            batters_table = {batter.playerId: batter for batter in all_batters}

    testing_plays = get_all_plays(session, training=False)
    
    # measure the accuracy of the predicting the most frequent outcome (0 for an out)
    wrong_predictions = 0
    n_plays = 0
    total_outcome = 0.0
    for play in testing_plays:
        prediction = 0
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
    total_wins, expected_wins, n_plays = test_long_term()
    print(f"Long-term Inaccuracy: {abs(total_wins - expected_wins) / n_plays}")

    wrong_predictions, n_plays, total_outcome = test_play_by_play(results_table)
    print(f"Play-by-Play Inaccuracy: {wrong_predictions / n_plays}")

    wrong_predictions, n_plays, total_outcome = test_baseline(results_table)
    print(f"Baseline Inaccuracy: {wrong_predictions / n_plays}")
