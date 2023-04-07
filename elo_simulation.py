from models import Base, Team, Game, Play, Player, Pitcher, Batter, PitcherRating, BatterRating
from db_utils import create_session_scope

from utils import logistic_func, quadratic_func, basic_func, calculate_ev, MAX_RESULT
from progressbar import progressbar

K = 16
PLAYS_PER_UPDATE = 100

def results_func(x):
    return basic_func(x)

results_table = {
    'DNS': -1,
    'Out': 0.0,
    'Walk': results_func(1),
    'Single': results_func(2),
    'Double': results_func(3),
    'Triple': results_func(4),
    'Home Run': results_func(5),
}

def main():
    with create_session_scope() as session:
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
                    s_b = results_table[play.result]
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


if __name__ == "__main__":
    main()