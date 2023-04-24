from abc import abstractmethod
from sqlalchemy.orm import Session
import random

from utils import calculate_ev, basic_func, linear_func
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
    'DNS': -1,
    'Out': 0.0,
    'Walk': results_func(1),
    'Single': results_func(1),
    'Double': results_func(2),
    'Triple': results_func(3),
    'Home Run': results_func(4),
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
        

    def update_ratings(self, ratings, position: Position):
        i = 0
        for player_id, rating in ratings:
            player = self.player_tables[position][player_id]
            if player.rating.value != rating:
                player.rating.value = rating
                if i % 250 == 0:
                    self.session.commit()
                i += 1

    def simulate_elo(self, suppress_output=True):
        games = get_all_games(self.session, training=True)

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

                pitcher.outcomes_table[play.result] += 1

            for pitcher_id, (e_p, s_p) in game_pitcher_rewards.items():
                # xp_factor = calculate_xp(pitchers_table[pitcher_id])
                xp_factor = 1
                change = self.K * (s_p - e_p) * xp_factor
                self.ratings_tables[Position.PITCHER.value][pitcher_id] += change

            for batter_id, (e_b, s_b) in game_batter_rewards.items():
                # xp_factor = calculate_xp(batters_table[batter_id])
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
        for outcome, value in self.partial_results_table.items():
            if value <= 0:
                continue
            outcome_freq = pitcher.outcomes_table[outcome] / pitcher.n_plays
            hit_value += value * outcome_freq
        
        return e_b * hit_value


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
        pitcher_rating = pitcher.rating.value
        batter_rating = batter.rating.value

        e_b = calculate_ev(batter_rating, pitcher_rating)
        prediction = int(e_b > 0.5) # predict a win if the batter is expected to win else predict a loss
        return prediction
    
    def predict_partials(self, play: Play):
        pitcher = self.player_tables[Position.PITCHER.value][play.pitcherId]
        batter = self.player_tables[Position.BATTER.value][play.batterId]
        pitcher_rating = pitcher.rating.value
        batter_rating = batter.rating.value

        e_b = calculate_ev(batter_rating, pitcher_rating)
        prediction = e_b
        if prediction < 0.5:
            return 0
        else:
            # TODO figure out how to predict the most likely outcome
            return 1
    
class DumbModel:
    def __init__(self):
        pass

    def predict(self, play):
        return 0
    
    def predict_partial(self, play):
        return 0