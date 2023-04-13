from models import Pitcher, Batter, Play, Game
from elo_simulation import results_table
from utils import calculate_ev, logistic_func
from db_utils import create_session_scope, get_all_games, get_all_plays

def test_predicted_outcomes(pitchers_table=None, batters_table=None, session=None):
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

        print("Measuring Model Performance...")
        testing_plays = get_all_plays(session, training=False)
        
        max_result = max(results_table.values())

        inverse_results = {v: k for k, v in results_table.items()}

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
        testing_games = get_all_games(session, training=False)
        testing_plays = []
        for game in testing_games:
            testing_plays.extend(game.plays)
        
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
                # observed /= max_result
                total_outcome += observed
                inaccuracy = abs(observed - prediction)
                total_inaccuracy += inaccuracy
                n_plays += 1
            
        return total_inaccuracy, total_inaccuracy / n_plays, total_outcome/n_plays
    
def test_baseline(results_table, pitchers_table=None, batters_table=None, session=None):
    with create_session_scope(session) as session:
        if not pitchers_table:
            all_pitchers = session.query(Pitcher).all()
            pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        if not batters_table:
            all_batters = session.query(Batter).all()
            batters_table = {batter.playerId: batter for batter in all_batters}

    testing_plays = get_all_plays(session, training=False)
    
    # measure the accuracy of the predicting the most frequent outcome (0 for an out)
    total_inaccuracy = 0.0
    n_plays = 0
    total_outcome = 0.0
    for play in testing_plays:
        result = play.result
        observed = results_table[result] 
        if observed != -1:
            total_outcome += observed
            total_inaccuracy += observed
            n_plays += 1
    
    return total_inaccuracy, total_inaccuracy / n_plays, total_outcome/n_plays

if __name__ == "__main__":
    total_wins, expected_wins, n_plays = test_predicted_outcomes()
    print(f"Long-term Inaccuracy: {(total_wins - expected_wins) / n_plays}") 
    total_inaccuracy, average_inaccuracy, average_outcome = test_baseline(results_table)
    print(f"Play-by-Play Inaccuracy: {average_inaccuracy}")
    print(f"Average Outcome: {average_outcome}")
