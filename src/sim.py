from pandas import DataFrame
from constants import PREDICTABLE_LEAGUES, db, ALL_LEAGUES
from dateutil import parser
from ast import literal_eval
from datetime import timedelta
from models.mmr import train

class DB_Game:
    def __init__(self, row) -> None:
        self.dt = parser.parse(row['dt'], ignoretz=True)
        self.blue_team = row['blue_team']
        self.red_team = row['red_team']
        self.blue_players = literal_eval(row['blue_players'])
        self.red_players = literal_eval(row['red_players'])
        self.blue_champs = literal_eval(row['blue_champs'])
        self.red_champs = literal_eval(row['red_champs'])
        self.blue_odds = row['blue_odds']
        self.red_odds = row['red_odds']
        self.league = next(league for league in ALL_LEAGUES if league.string == row['league'])
        self.game = row['game']

def get_winner(db_game, scraped_games: DataFrame):
    matches = scraped_games.loc[scraped_games['Short'] == db_game.league.string]
    matches.loc[:, ['DateTime UTC']] = matches['DateTime UTC'].map(lambda x: parser.parse(x, ignoretz=True))
    def in_date_window(date):
        return date.date() == db_game.dt.date() or date.date() == db_game.dt.date() + timedelta(days=1) or date.date() == db_game.dt.date() - timedelta(days=1)
    matches = matches[matches['DateTime UTC'].apply(in_date_window)]
    by_dt_diff = matches.sort_values('DateTime UTC', key=lambda x: x.map(lambda y: abs(db_game.dt - y)))[:5]
    for _, row in by_dt_diff.iterrows():
        if row['Team1Picks'].split(',') == db_game.blue_champs and row['Team2Picks'].split(',') == db_game.red_champs and row['N GameInMatch'] == db_game.game:
            return int(row['Winner'])
    print(f'no match for {str(db_game.dt)} {db_game.league.string}: {db_game.blue_team} v {db_game.red_team} - {db_game.game}') 
    return False

def load_db():
    db_games = []
    cur = db.cursor()
    rows = cur.execute('SELECT * FROM bets').fetchall()
    cur.close()
    for row in rows:
        db_games.append(DB_Game(row))
    return db_games

def sim_day(date):
    units = 0.0
    model = train(str(date.date()))
    db_games = load_db()
    # db_games = [game for game in db_games if game.dt.date() == date.date() and game.league in PREDICTABLE_LEAGUES]
    db_games = [game for game in db_games if game.dt.date() == date.date()]
    for game in db_games:
        if real_win := get_winner(game, model.matches):
            change = -1
            units -= 1
            blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league)
            if game.league in PREDICTABLE_LEAGUES:
                if blue_win >= .60:
                    if real_win == 1:
                        change = 1 / game.blue_odds
                        units += change
                        change -= 1
                elif 1 - blue_win > .60:
                    if real_win == 2:
                        change = 1 / game.red_odds
                        units += change
                        change -= 1
                else:
                    units += 1
                    change = 0.0
            else:
                if blue_win >= .75:
                    if real_win == 1:
                        change = 1 / game.blue_odds
                        units += change
                        change -= 1
                elif 1 - blue_win > .75:
                    if real_win == 2:
                        change = 1 / game.red_odds
                        units += change
                        change -= 1
                else:
                    units += 1
                    change = 0.0
                # if game.blue_odds < game.red_odds:
                #     if real_win == 1:
                #         change = 1 / game.blue_odds
                #         units += change
                #         change -= 1
                # else:
                #     if real_win == 2:
                #         change = 1 / game.red_odds
                #         units += change
                #         change -= 1
            print(f'{game.league.string}: {game.blue_team} v {game.red_team} - {game.game} {blue_win:f} {change:+f}')
    print(f'{units:+f}')

