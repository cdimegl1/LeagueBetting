from pandas import DataFrame
from constants import PREDICTABLE_LEAGUES, db, ALL_LEAGUES, League, load_coefs
from dateutil import parser
from ast import literal_eval
from datetime import timedelta
from models.mmr import train

class DB_Game:
    def __init__(self, row) -> None:
        self.id = row['rowid']
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
    rows = cur.execute('SELECT rowid, * FROM bets').fetchall()
    cur.close()
    for row in rows:
        db_games.append(DB_Game(row))
    return db_games

db_games = load_db()

def sim_days(start, days, leagues=ALL_LEAGUES):
    total = 0.0
    total_league_units = dict.fromkeys(ALL_LEAGUES, 0)
    for _ in range(days):
        units, league_units = sim_day(start, leagues)
        for l, u in league_units.items():
            total_league_units[l] += u
        total += units
        print(f'day - {str(start.date())}: {units:+f}')
        start += timedelta(days=1)
    for l, u in total_league_units.items():
        print(f'{l.string}: {u:+f}')
    return total

def sim_league(start, days, league):
    return sim_days(start, days, [league])

def scipy_select(x, game, blue_win, vec):
    if (game.blue_odds > x[0] and
        game.blue_odds < x[1] and
        vec[0] > game.blue_odds + x[2] and
        vec[2] > game.blue_odds + x[3] and
        vec[0] > x[4] and
        vec[2] > x[5]):
        return 1
    if (game.red_odds > x[6] and
        game.red_odds < x[7] and
        vec[1] > game.red_odds + x[8] and
        vec[3] > game.red_odds + x[9] and
        vec[1] > x[10] and
        vec[3] > x[11]):
        return 2
    return 0
    # if (blue_win > x[0] and
    #     game.blue_odds > x[1] and
    #     blue_win > game.blue_odds + x[2] and
    #     vec[0] > x[3] and
    #     vec[2] > x[4]):
    #     return 1
    # if (1 - blue_win > x[5] and
    #     game.red_odds > x[6] and
    #     1 - blue_win > game.red_odds + x[7] and
    #     vec[1] > x[8] and
    #     vec[3] > x[9]):
    #     return 2
    # return 0

coefs = load_coefs()
def sim_day(date, leagues=ALL_LEAGUES, update=False):
    units = 0.0
    model = train(str(date.date()), True)
    db_games_copy = db_games.copy()
    # db_games_copy = [game for game in db_games_copy if game.dt.date() == date.date() and game.league in PREDICTABLE_LEAGUES]
    db_games_copy = [game for game in db_games_copy if game.dt.date() == date.date()]
    db_games_copy = [game for game in db_games_copy if game.league in leagues]
    league_units = dict.fromkeys(leagues, 0)
    for game in db_games_copy:
        res = None
        if real_win := get_winner(game, model.matches):
            change = -1
            units -= 1
            league_units[game.league] -= 1
            blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league, str(date.date()))
            vec = model.vec(game.blue_players, game.red_players, game.blue_champs, game.red_champs, game.league)
            try:
                # res = scipy_select(coefs[date.date()][game.league], game, blue_win, vec)
                res = scipy_select(coefs[date.date()]['all'], game, blue_win, vec)
            except:
                print(f'no coefs for {game.league}')
                if blue_win > .5 and blue_win > game.blue_odds:
                    res = 1
                elif 1 - blue_win > .5 and 1 - blue_win > game.red_odds:
                    res = 2
                else:
                    res = 0
            if res == 1:
                if update:
                    update_db(game, 1)
                if real_win == 1:
                    change = 1 / game.blue_odds
                    league_units[game.league] += change
                    units += change
                    change -= 1
            elif res == 2:
                if update:
                    update_db(game, 2)
                if real_win == 2:
                    change = 1 / game.red_odds
                    league_units[game.league] += change
                    units += change
                    change -= 1
            else:
                league_units[game.league] += 1
                units += 1
                change = 0.0
        # if game.league in PREDICTABLE_LEAGUES:
        #     if real_win := get_winner(game, model.matches):
        #         change = -1
        #         units -= 1
        #         league_units[game.league] -= 1
        #         blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league, str(date.date()))
        #         # if blue_win > game.blue_odds:
        #         # if blue_win > .5:
        #         if blue_win >= .45 and blue_win > game.blue_odds:
        #             if update:
        #                 update_db(game, 1)
        #             if real_win == 1:
        #                 change = 1 / game.blue_odds
        #                 league_units[game.league] += change
        #                 units += change
        #                 change -= 1
        #         # elif 1 - blue_win > .5:
        #         elif 1 - blue_win > .46 and 1 - blue_win > game.red_odds:
        #             if update:
        #                 update_db(game, 2)
        #             if real_win == 2:
        #                 change = 1 / game.red_odds
        #                 league_units[game.league] += change
        #                 units += change
        #                 change -= 1
        #         else:
        #             league_units[game.league] += 1
        #             units += 1
        #             change = 0.0
        # else:
        #     if real_win := get_winner(game, model.matches):
        #         change = -1
        #         units -= 1
        #         league_units[game.league] -= 1
        #         blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league, str(date.date()))
        #         vec = model.vec(game.blue_players, game.red_players, game.blue_champs, game.red_champs, game.league)
        #         # if blue_win > game.blue_odds:
        #         # if blue_win > .5:
        #         if blue_win > .5 and vec[2] > .62:
        #             if update:
        #                 update_db(game, 1)
        #             if real_win == 1:
        #                 change = 1 / game.blue_odds
        #                 league_units[game.league] += change
        #                 units += change
        #                 change -= 1
        #         # elif 1 - blue_win > .5:
        #         elif 1 - blue_win > .5 and vec[3] > .64:
        #             if update:
        #                 update_db(game, 2)
        #             if real_win == 2:
        #                 change = 1 / game.red_odds
        #                 league_units[game.league] += change
        #                 units += change
        #                 change -= 1
        #         else:
        #             league_units[game.league] += 1
        #             units += 1
        #             change = 0.0
            print(f'{game.league.string}: {game.blue_team} v {game.red_team} - {game.game} {blue_win:f} {change:+f} {res}')
    print(f'{units:+f}')
    # for l, u in league_units.items():
    #     print(f'{l.string}: {u:+f}')
    return units, league_units

class SciPy:
    def __init__(self) -> None:
        self.ran_once = False
        self.saved_game_models = {}
        self.saved_game_results = {}

    def scipy_sim_days(self, x, start, days, leagues):
        total = 0.0
        total_bets = 0
        for _ in range(days):
            units, bets = self.scipy_sim_day(x, start, leagues)
            total += units
            total_bets += bets
            start += timedelta(days=1)
        self.ran_once = True
        # print(total, total_bets)
        return -total

    def scipy_sim_day(self, x, date, leagues):
        units = 0.0
        bets = 0
        model = None
        if not self.ran_once:
            model = train(str(date.date()), False)
            # self.ran_once = True
        db_games_copy = [game for game in db_games if game.dt.date() == date.date() and game.league in leagues]
        for game in db_games_copy:
            real_win = self.saved_game_results.get(game.dt)
            if real_win is None:
                winner = get_winner(game, model.matches)
                self.saved_game_results[game.dt] = winner
                real_win = winner
            if real_win:
                change = -1
                units -= 1
                loaded_models = self.saved_game_models.get(game.dt)
                blue_win = None
                vec = None
                if loaded_models is None:
                    blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league, str(date.date()))
                    vec = model.vec(game.blue_players, game.red_players, game.blue_champs, game.red_champs, game.league)
                    self.saved_game_models[game.dt] = (blue_win, vec)
                else:
                    blue_win, vec = loaded_models
                res = scipy_select(x, game, blue_win, vec)
                if res == 1:
                    bets += 1
                    if real_win == 1:
                        change = 1 / game.blue_odds
                        units += change
                        change -= 1
                elif res == 2:
                    bets += 1
                    if real_win == 2:
                        change = 1 / game.red_odds
                        units += change
                        change -= 1
                else:
                    units += 1
                    change = 0.0
        return units, bets

def update_db(game, on):
    cur = db.cursor()
    cur.execute(r'UPDATE bets SET "on"=?  WHERE rowid=?', (on, game.id))
    cur.close()
    db.commit()

def update_game(row_id):
    game = next(game for game in db_games if row_id == game.id)
    model = train(str(game.dt.date()), False)
    blue_win = model.predict(game.blue_players+game.red_players, game.blue_champs+game.red_champs, game.league, str(game.dt.date()))
    vec = model.vec(game.blue_players, game.red_players, game.blue_champs, game.red_champs, game.league)
    res = scipy_select(coefs[game.league], game, blue_win, vec)
    update_db(game, res)

