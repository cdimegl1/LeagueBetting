from pandas import pandas

class Model:
    DATA_DIR = '../data'
    rosters = pandas.read_csv(f'{DATA_DIR}/rosters.csv')
    tournaments = pandas.read_csv(f'{DATA_DIR}/tournaments.csv')
    matches = pandas.read_csv(f'{DATA_DIR}/matches.csv', index_col=0)
