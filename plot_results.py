import matplotlib.pyplot as plt
import numpy as np

from prediction_model import PredictionModel, EloModel, DumbModel, RandomModel, results_table, partial_results_table
from db_utils import get_all_plays, create_session_scope

def get_differences(model: PredictionModel, session, results_table=partial_results_table):
    differences = []
    testing_plays = get_all_plays(session, training=False)

    for play in testing_plays:
        result = play.result
        prediction = model.predict_partial(play)
        observed = results_table[result]

        if observed != -1:
            difference = abs(observed - prediction)
            differences.append(difference)

    return differences

def get_running_wins(model: PredictionModel, session, results_table=partial_results_table):
    total_wins = 0
    expected_wins = 0
    n_plays = 0

    running_wins = []

    testing_plays = get_all_plays(session, training=False)
    for play in testing_plays:
        result = play.result
        prediction = model.predict_partial(play)
        observed = results_table[result]
        if observed != -1:
            total_wins += observed
            expected_wins += prediction
            n_plays += 1

            running_wins.append((total_wins - expected_wins)/n_plays)
    
    return running_wins

def plot_line_chart(differences):
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(differences)), differences, label='Difference (Total Wins - Expected Wins)')
    plt.xlabel('Play Number')
    plt.ylabel('Difference')
    plt.title('Inaccuracy of Model Over Time')
    plt.legend()
    plt.show()

def plot_histogram(differences):
    plt.figure(figsize=(12, 6))
    plt.hist(differences, bins=20, alpha=0.75, edgecolor='black')
    plt.xlabel('Difference')
    plt.ylabel('Frequency')
    plt.title('Histogram of Differences Between Total Wins and Expected Wins')
    plt.show()

def plot_running_accuracy(differences):
    cumulative_differences = np.cumsum(differences)
    play_numbers = np.arange(1, len(differences) + 1)
    running_accuracy = cumulative_differences / play_numbers

    plt.figure(figsize=(12, 6))
    plt.plot(play_numbers, running_accuracy, label='Running Inaccuracy')
    plt.xlabel('Play Number')
    plt.ylabel('Running Inaccuracy')
    plt.title('Running Inaccuracy of Model Over Time')
    plt.legend()
    plt.show()


def plot_running_accuracy(differences):
    cumulative_differences = np.cumsum(differences)
    play_numbers = np.arange(1, len(differences) + 1)
    running_accuracy = cumulative_differences / play_numbers

    plt.figure(figsize=(12, 6))
    plt.plot(play_numbers, running_accuracy, label='Running Inaccuracy')
    plt.xlabel('Play Number')
    plt.ylabel('Running Inaccuracy')
    plt.title('Running Inaccuracy of Model Over Time')
    plt.legend()
    plt.show()

def plot_running_accuracy_multiple_models(models, model_names, session):
    plt.figure(figsize=(12, 6))
    
    for model, name in zip(models, model_names):
        differences = get_running_wins(model, session)
        cumulative_differences = np.cumsum(differences)
        play_numbers = np.arange(1, len(differences) + 1)
        running_accuracy = cumulative_differences / play_numbers
        
        plt.plot(play_numbers, running_accuracy, label=f'Running Inaccuracy ({name})')

    plt.xlabel('Play Number')
    plt.ylabel('Running Inaccuracy')
    plt.title('Running Inaccuracy of Models Over Time')
    plt.legend()
    plt.show()




with create_session_scope() as session:
    # Create the model
    elo_model = EloModel(session)
    dumb_model = DumbModel()
    random_model = RandomModel()
    # Calculate the differences
    # differences = get_differences(elo_model, session)
    # plot_running_accuracy(differences)
    plot_running_accuracy_multiple_models([elo_model, dumb_model, random_model], ['Elo', 'Dumb', 'Random'], session)
    # # Plot the line chart
    # plot_line_chart(differences)

    # # Plot the histogram
    # plot_histogram(differences)
