from models import Pitcher, Batter, Play, Game
from elo_simulation import results_table
from utils import test_performance, calculate_ev, logistic_func
from db_utils import create_session_scope

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
        testing_plays = session.query(Play).filter(Play.training == False).all()
        
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

if __name__ == "__main__":
    print(results_table)
    total_wins, expected_wins, n_plays = test_predicted_outcomes()
    print(total_wins, expected_wins, n_plays)
    print(f"Inaccuracy: {total_wins - expected_wins} / {n_plays} = {(total_wins - expected_wins) / n_plays}")