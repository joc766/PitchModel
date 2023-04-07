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