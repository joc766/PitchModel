from abc import abstractmethod
from sqlalchemy.orm import Session
import random

from utils import calculate_ev, basic_func, linear_func, calculate_xp
from db_utils import get_all_games
from models import Pitcher, Batter, Play, Position
from progressbar import progressbar

results_func = basic_func
results_table = {
    'DNS': -1,
    'Out': 0.0,
    'Walk': results_func(1),
    'Single': results_func(2),
    'Double': results_func(3),
    'Triple': results_func(4),
    'Home Run': results_func(5),
}

results_fnc = linear_func
partial_results_table = {
    'Out': 0.0,
    'Single': 0.25,
    'Double': 0.5,
    'Triple': 0.75,
    'Home Run': 1.0,
}



class PredictionModel:

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def predict(self, play):
        pass

    @abstractmethod
    def predict_partial(self, play):
        pass

    @abstractmethod
    def predict_partial_outcomes(self, play) -> tuple[float, list[float]]:
        pass

class EloModel:
    ### can only exist within a session scope

    def __init__(self, session: Session, results_table=results_table, partial_results_table=partial_results_table):    
        all_pitchers = session.query(Pitcher).all()
        all_batters = session.query(Batter).all()

        pitchers_table = {pitcher.playerId: pitcher for pitcher in all_pitchers}
        batters_table = {batter.playerId: batter for batter in all_batters}

        self.player_tables = [pitchers_table, batters_table] # lines up with Position enum

        pitcher_ratings = {pitcher.playerId: pitcher.rating.value for pitcher in all_pitchers}
        batter_ratings = {batter.playerId: batter.rating.value for batter in all_batters}

        self.ratings_tables = [pitcher_ratings, batter_ratings]

        self.session = session

        self.results_table = results_table
        self.partial_results_table = partial_results_table
        self.K = 16
        self.results_as_integers = {result: i for i, result in enumerate(self.partial_results_table.keys())}
        

    def update_ratings(self, ratings, position: Position):
        i = 0
        for player_id, rating in ratings:
            player = self.player_tables[position][player_id]
            if player.rating.value != rating:
                player.rating.value = rating
                self.session.add(player)
                if i % 250 == 0:
                    self.session.commit()
                i += 1

    def simulate_elo(self, suppress_output=True):
        games = get_all_games(self.session, training=True)
        n_plays_pitchers_table = {playerId: 0 for playerId in self.player_tables[Position.PITCHER.value].keys()}
        n_plays_batters_table = {playerId: 0 for playerId in self.player_tables[Position.BATTER.value].keys()}

        if not suppress_output:
            print('Simulating Games...')
            games = progressbar(games)

        for game in games:
            # game_pitcher_rewards tracks the pitcher's expected value and scored value for each game. An update will be made at the end of the game
            game_pitcher_rewards = dict.fromkeys([play.pitcherId for play in game.plays], [0, 0])
            game_batter_rewards = dict.fromkeys([play.batterId for play in game.plays], [0, 0])
            for play in game.plays:
                if self.results_table[play.result] == -1:
                    continue

                pitcher: Pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]

                pitcher_rating = self.ratings_tables[Position.PITCHER.value][play.pitcherId]
                batter_rating = self.ratings_tables[Position.BATTER.value][play.batterId]

                e_b = calculate_ev(batter_rating, pitcher_rating)
                e_p = 1 - e_b
                game_pitcher_rewards[play.pitcherId][0] += e_p
                game_batter_rewards[play.batterId][0] += e_b

                s_b = self.results_table[play.result]
                s_p = 1 - s_b
                game_pitcher_rewards[play.pitcherId][1] += s_p
                game_batter_rewards[play.batterId][1] += s_b

                n_plays_pitchers_table[play.pitcherId] += 1
                n_plays_batters_table[play.batterId] += 1

            for pitcher_id, (e_p, s_p) in game_pitcher_rewards.items():
                # xp_factor = calculate_xp(n_plays_pitchers_table[pitcher_id])
                xp_factor = 1
                change = self.K * (s_p - e_p) * xp_factor
                self.ratings_tables[Position.PITCHER.value][pitcher_id] += change

            for batter_id, (e_b, s_b) in game_batter_rewards.items():
                # xp_factor = calculate_xp(n_plays_batters_table[batter_id])
                xp_factor = 1
                change = self.K * (s_b - e_b) * xp_factor
                self.ratings_tables[Position.BATTER.value][batter_id] += change
            
        pitcher_ratings = self.ratings_tables[Position.PITCHER.value].items()
        if not suppress_output:
            print("updating pitcher ratings...")
            pitcher_ratings = progressbar(pitcher_ratings)
        self.update_ratings(pitcher_ratings, Position.PITCHER.value)
        
        batter_ratings = self.ratings_tables[Position.BATTER.value].items()
        if not suppress_output:
            print("updating batter ratings...")
            batter_ratings = progressbar(batter_ratings)
        self.update_ratings(batter_ratings, Position.BATTER.value)

    def train(self, suppress_output=True):
        self.simulate_elo(suppress_output=suppress_output)

    def calculate_ev(self, batter_rating, pitcher_rating, pitcher: Pitcher, batter: Batter, play: Play):
        e_b = 1 / (1 + 10 ** ((pitcher_rating - batter_rating) / 400))
        # now, given the probability of a hit, calculate the expected value of that hit and multiply by the probability of a hit
        hit_value = 0
        outcome_freqs = {i: 0 for i in range(1, len(self.partial_results_table))}
        n_outs = pitcher.outcomes.get_outcome_count("out")
        n_zeros = 0
        for outcome, value in self.partial_results_table.items():
            if value <= 0:
                continue
            outcome_ind = self.results_as_integers[outcome]
            try:
                outcome_freq = pitcher.outcomes.get_outcome_count(outcome) / (pitcher.n_plays - n_outs)
            except ZeroDivisionError:
                outcome_freq = 0.25
            outcome_freqs[outcome_ind] = outcome_freq * e_b
            hit_value += value * outcome_freq
        
        return e_b * hit_value, e_b, outcome_freqs


    def predict_partial(self, play: Play):
        pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]
        batter = self.player_tables[Position.BATTER.value][play.batterId]
        pitcher_rating = pitcher.rating.value
        batter_rating = batter.rating.value

        e_b = self.calculate_ev(batter_rating, pitcher_rating, pitcher, batter, play)
        return e_b

    def predict(self, play: Play):
        pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]
        batter = self.player_tables[Position.BATTER.value][play.batterId]
        # pitcher_rating = pitcher.rating.value
        # batter_rating = batter.rating.value
        pitcher_rating = self.ratings_tables[Position.PITCHER.value][play.pitcherId]
        batter_rating = self.ratings_tables[Position.BATTER.value][play.batterId]

        e_b = calculate_ev(batter_rating, pitcher_rating)
        prediction = e_b 

        self.simulate_play(play)

        return prediction
    
    def predict_partial_outcomes(self, play: Play) -> tuple[float, list[float]]:
        pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]
        batter = self.player_tables[Position.BATTER.value][play.batterId]
        # pitcher_rating = pitcher.rating.value
        # batter_rating = batter.rating.value
        pitcher_rating = self.ratings_tables[Position.PITCHER.value][play.pitcherId]
        batter_rating = self.ratings_tables[Position.BATTER.value][play.batterId]

        e_b, hit_prob, partial_probs = self.calculate_ev(batter_rating, pitcher_rating, pitcher, batter, play)
        prediction = e_b
        outcome_probs = [1-hit_prob]
        outcome_probs.extend(partial_probs.values())

        self.simulate_play(play)

        return prediction, outcome_probs
    
    def simulate_play(self, play: Play):
        pitcher: Pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]

        pitcher_rating = self.ratings_tables[Position.PITCHER.value][play.pitcherId]
        batter_rating = self.ratings_tables[Position.BATTER.value][play.batterId]

        e_b = calculate_ev(batter_rating, pitcher_rating)
        e_p = 1 - e_b

        s_b = self.results_table[play.result]
        s_p = 1 - s_b

        # pitcher.outcomes.increment_outcome_count(play.result)

        # xp_factor = calculate_xp(self.ratings_tables[Position.PITCHER.values][play.pitcher_id])
        xp_factor = 1
        change = self.K * (s_p - e_p) * xp_factor
        self.ratings_tables[Position.PITCHER.value][play.pitcherId] += change
        # xp_factor = calculate_xp(self.ratings_tables[Position.BATTER.values][play.batter_id])
        xp_factor = 1
        change = self.K * (s_b - e_b) * xp_factor
        self.ratings_tables[Position.BATTER.value][play.batterId] += change
    
class DumbModel:
    def __init__(self):
        pass

    def predict(self, play):
        return 0
    
    def predict_partial(self, play):
        return 0.28 # guess the average outcome of all of the testing data
    
    def predict_partial_outcomes(self, play):
        return 0.0,  [0.96, 0.01, 0.01, 0.01, 0.01]

class RandomModel:
    def __init__(self):
        pass

    def predict(self, play):
        return random.randint(0, 1)
    
    def predict_partial(self, play):
        return random.random()
    
    def predict_partial_outcomes(self, play):
        total = 1.0
        outcomes = []
        for i in range(5):
            new_val = random.uniform(0, total)
            outcomes.append(new_val)
            total -= new_val
        return random.random(), [random.random() for i in range(5)]