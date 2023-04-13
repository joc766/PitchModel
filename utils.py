import math
from progressbar import progressbar
from models import Base, Team, Game, Play, Player, Pitcher, Batter, PitcherRating, BatterRating, Position
from db_utils import create_session_scope, get_n_plays

SIGMA = 400

MAX_RESULT = 5
GROWTH_RATE = 9
K_FACTOR = 0.5

Y_INTERCEPT = 2.5

def calculate_ev(r_a, r_b):
    try:
        return 1 / (1 + 10 ** ((r_b - r_a) / SIGMA))
    except OverflowError:
        # print(r_b, r_a)
        return 0

def logistic_func(x):
    return MAX_RESULT / (1 + GROWTH_RATE * math.exp(-K_FACTOR * x))

def quadratic_func(x):
    return 0.2 * (x-1)**2 + Y_INTERCEPT

def basic_func(x):
    return 1.0

def calculate_xp(player):
    xp = max(1, 5 - (player.n_plays / 1000))
    return xp