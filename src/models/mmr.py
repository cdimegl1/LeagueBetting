from models.model import Model
from datetime import datetime, timedelta
from os import makedirs
from os.path import exists
from constants import ALL_LEAGUES, League, champions, PREDICTABLE_LEAGUES
import pandas
from logging import getLogger
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import pickle

_log = getLogger('main.mmr')

def expected(elo1, elo2):
    return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

def mmr_change(expected, actual, k):
    return k * (actual - expected)

def k_linear(matches, k=100):
    unique = matches['Tournament'].unique()
    tourn_to_k = {}
    step = k / len(unique)
    i = step
    for tourn in unique:
        tourn_to_k[tourn] = i
        i += step
    return tourn_to_k

def k_exponential(matches, k=75):
    unique = matches['Tournament'].unique()
    tourn_to_k = {}
    step = k / (2 ** len(unique))
    i = step
    for tourn in unique:
        i *= 2
        tourn_to_k[tourn] = i
    return tourn_to_k

def k_constant(matches, k=100):
    unique = matches['Tournament'].unique()
    tourn_to_k = {}
    for tourn in unique:
        tourn_to_k[tourn] = k
    return tourn_to_k

class Players(Model):

    def __init__(self, leagues=ALL_LEAGUES) -> None:
        self.dir_name = 'MMR_Players'
        self.data_path = f'../models/{self.dir_name}'
        if not exists(self.data_path):
            makedirs(self.data_path)
        self.leagues = leagues
        for league in self.leagues:
            if not exists(f'{self.data_path}/{league.string}'):
                makedirs(f'{self.data_path}/{league.string}')

    @staticmethod
    def get_team_mmr(team, mmrs):
        total = 0.0
        missing = 0
        if type(mmrs) is dict:
            for player in team:
                total += mmrs[player.lower()]
        else:
            for player in team:
                try:
                    total += mmrs.loc[player.lower()][0]
                except KeyError:
                    missing += 1
                    _log.warning('failed to get player mmr: %s', player)
        average = total / (5 - missing)
        total += average * missing
        return total / 5

    def get_mmrs(self, league: League, end_date=str(datetime.utcnow().date())):
        if exists(f'{self.data_path}/{league.string}/{end_date}/player_mmrs.csv'):
            return pandas.read_csv(f'{self.data_path}/{league.string}/{end_date}/player_mmrs.csv', index_col=0)
        return pandas.read_csv(f'{self.data_path}/{league.string}/player_mmrs.csv', index_col=0)

    def train(self, k_function=k_linear, start_date='2022', end_date='3000', store=False):
        for league in self.leagues:
            if not store and exists(f'{self.data_path}/{league.string}/{end_date}/player_mmrs.csv'):
                continue
            matches = self.matches.loc[self.matches['Short'] == league.string]
            matches = matches.loc[matches['DateTime UTC'] > start_date]
            matches = matches.loc[matches['DateTime UTC'] < end_date+' 00:00:00']
            matches = matches.sort_values(['DateTime UTC'])
            all_players = []
            for team1, team2 in zip(matches['Team1Players'], matches['Team2Players']):
                team1 = team1.split(',')
                team2 = team2.split(',')
                all_players.extend(team1 + team2)
            all_players = [player.lower() for player in all_players]
            mmrs = dict.fromkeys(all_players, 1200.0)
            k_values = k_function(matches)
            for _, match in matches.iterrows():
                winner = match['Winner']
                team1 = match['Team1Players'].split(',')
                team2 = match['Team2Players'].split(',')
                team1_mmr = self.get_team_mmr(team1, mmrs)
                team2_mmr = self.get_team_mmr(team2, mmrs)
                expected1 = expected(team1_mmr, team2_mmr)
                expected2 = expected(team2_mmr, team1_mmr)
                if winner == 1:
                    change = mmr_change(expected1, 1, k_values[match['Tournament']])
                    for player in team1:
                        mmrs[player.lower()] += change
                    for player in team2:
                        mmrs[player.lower()] -= change
                elif winner == 2:
                    change = mmr_change(expected2, 1, k_values[match['Tournament']])
                    for player in team1:
                        mmrs[player.lower()] -= change
                    for player in team2:
                        mmrs[player.lower()] += change
            df = pandas.DataFrame.from_dict(mmrs, orient='index')
            if store:
                if not exists(f'{self.data_path}/{league.string}/{end_date}'):
                    makedirs(f'{self.data_path}/{league.string}/{end_date}')
                df.to_csv(f'{self.data_path}/{league.string}/{end_date}/player_mmrs.csv')
            else:
                df.to_csv(f'{self.data_path}/{league.string}/player_mmrs.csv')

class Champions(Model):

    def __init__(self, leagues=ALL_LEAGUES, player_model=None, league_specific_champs=True, end_date=str(datetime.utcnow().date())) -> None:
        if player_model:
            self.player_model = player_model
        else:
            self.player_model = Players(leagues)
        self.dir_name = 'MMR_Champions'
        self.data_path = f'../models/{self.dir_name}'
        if not exists(self.data_path):
            makedirs(self.data_path)
        self.leagues = leagues
        for league in self.leagues:
            if not exists(f'{self.data_path}/{league.string}'):
                makedirs(f'{self.data_path}/{league.string}')
        if not exists(f'{self.data_path}/all'):
            makedirs(f'{self.data_path}/all')
        self.player_mmrs = {}
        for league in leagues:
            self.player_mmrs[league] = self.player_model.get_mmrs(league, end_date)
        self.league_specific_champs = league_specific_champs

    def get_mmrs(self, league: League, end_date=str(datetime.utcnow().date())):
        if exists(f'{self.data_path}/{league.string}/{end_date}/champions_mmrs.csv'):
            return pandas.read_csv(f'{self.data_path}/{league.string}/{end_date}/champions_mmrs.csv', index_col=0)
        return pandas.read_csv(f'{self.data_path}/{league.string}/champion_mmrs.csv', index_col=0)

    def train(self, k_function=k_linear, start_date='2022', end_date='3000', store=False):
        if self.league_specific_champs:
            for league in self.leagues:
                if not store and exists(f'{self.data_path}/{league.string}/{end_date}/champion_mmrs.csv'):
                    continue
                matches = self.matches.loc[self.matches['Short'] == league.string]
                matches = matches.loc[matches['DateTime UTC'] > start_date]
                matches = matches.loc[matches['DateTime UTC'] < end_date+' 00:00:00']
                matches = matches.sort_values(['DateTime UTC'])
                champ_mmrs = dict.fromkeys(champions, 1200.00)
                player_mmrs = self.player_model.get_mmrs(league, end_date)
                k_values = k_function(matches)
                for _, match in matches.iterrows():
                    winner = match['Winner']
                    team1 = match['Team1Players'].split(',')
                    team2 = match['Team2Players'].split(',')
                    team1_picks = match['Team1Picks'].split(',')
                    team2_picks = match['Team2Picks'].split(',')
                    team1_mmr = Players.get_team_mmr(team1, player_mmrs)
                    team2_mmr = Players.get_team_mmr(team2, player_mmrs)
                    expected1 = expected(team1_mmr, team2_mmr)
                    expected2 = expected(team2_mmr, team1_mmr)
                    if winner == 1:
                        change = mmr_change(expected1, 1, k_values[match['Tournament']])
                        for champ in team1_picks:
                            champ_mmrs[champ] += change
                        for champ in team2_picks:
                            champ_mmrs[champ] -= change
                    elif winner == 2:
                        change = mmr_change(expected2, 1, k_values[match['Tournament']])
                        for champ in team1_picks:
                            champ_mmrs[champ] -= change
                        for champ in team2_picks:
                            champ_mmrs[champ] += change
                df = pandas.DataFrame.from_dict(champ_mmrs, orient='index')
                if store:
                    if not exists(f'{self.data_path}/{league.string}/{end_date}'):
                        makedirs(f'{self.data_path}/{league.string}/{end_date}')
                    df.to_csv(f'{self.data_path}/{league.string}/{end_date}/champion_mmrs.csv')
                else:
                    df.to_csv(f'{self.data_path}/{league.string}/champion_mmrs.csv')
        else:
            matches = self.matches.loc[self.matches['DateTime UTC'] > start_date]
            matches = matches.loc[matches['Short'].isin([league.string for league in self.leagues])]
            matches = matches.loc[matches['DateTime UTC'] < end_date+' 00:00:00']
            matches.sort_values(['DateTime UTC'])
            champ_mmrs = dict.fromkeys(champions, 1200.00)
            k_values = k_function(matches)
            for _, match in matches.iterrows():
                winner = match['Winner']
                team1 = match['Team1Players'].split(',')
                team2 = match['Team2Players'].split(',')
                team1_picks = match['Team1Picks'].split(',')
                team2_picks = match['Team2Picks'].split(',')
                league = next(league for league in ALL_LEAGUES if match['Short'] == league.string)
                team1_mmr = Players.get_team_mmr(team1, self.player_mmrs[league])
                team2_mmr = Players.get_team_mmr(team2, self.player_mmrs[league])
                expected1 = expected(team1_mmr, team2_mmr)
                expected2 = expected(team2_mmr, team1_mmr)
                if winner == 1:
                    change = mmr_change(expected1, 1, k_values[match['Tournament']])
                    for champ in team1_picks:
                        champ_mmrs[champ] += change
                    for champ in team2_picks:
                        champ_mmrs[champ] -= change
                elif winner == 2:
                    change = mmr_change(expected2, 1, k_values[match['Tournament']])
                    for champ in team1_picks:
                        champ_mmrs[champ] -= change
                    for champ in team2_picks:
                        champ_mmrs[champ] += change
            df = pandas.DataFrame.from_dict(champ_mmrs, orient='index')
            df.to_csv(f'{self.data_path}/all/champion_mmrs.csv')


class PlayersAndChampions(Model):

    def __init__(self, leagues=ALL_LEAGUES, champion_model=None, end_date=str(datetime.utcnow().date())):
        if champion_model:
            self.champion_model = champion_model
        else:
            self.champion_model = Champions(leagues)
        self.leagues = leagues
        self.player_model = self.champion_model.player_model
        self.player_mmrs = self.champion_model.player_mmrs
        self.champion_mmrs = {}
        self.dir_name = 'MMR_PlayersAndChampions'
        self.data_path = f'../models/{self.dir_name}'
        if not exists(self.data_path):
            makedirs(self.data_path)
        for league in self.leagues:
            if not exists(f'{self.data_path}/{league.string}'):
                makedirs(f'{self.data_path}/{league.string}')
        if self.champion_model.league_specific_champs:
            for league in self.leagues:
                self.champion_mmrs[league] = self.champion_model.get_mmrs(league, end_date)
        else:
            for league in self.leagues:
                self.champion_mmrs[league] = pandas.read_csv(f'{self.champion_model.data_path}/all/champion_mmrs.csv', index_col=0)

    def get_training(self, league: League):
        return pandas.read_csv(f'{self.data_path}/{league.string}/training.csv')

    def vec(self, team1_players, team2_players, team1_champs, team2_champs, league, trace=False):
        v = []
        mmrs = []
        missing = 0
        for player in team1_players:
            try:
                mmrs.append(self.player_mmrs[league].loc[player.lower()][0])
            except KeyError:
                _log.warning('failed to get player mmr: %s', player)
                missing += 1
        average = None
        try:
            average = sum(mmrs) / len(mmrs)
        except Exception:
            average = 1200
        if trace:
            _log.info(mmrs)
        for _ in range(missing):
            mmrs.append(average)
        v.append(sum(mmrs) / len(mmrs))
        mmrs = []
        missing = 0
        for player in team2_players:
            try:
                mmrs.append(self.player_mmrs[league].loc[player.lower()][0])
            except KeyError:
                _log.warning('failed to get player mmr: %s', player)
                missing += 1
        try:
            average = sum(mmrs) / len(mmrs)
        except Exception:
            average = 1200
        if trace:
            _log.info(mmrs)
        for _ in range(missing):
            mmrs.append(average)
        v.append(sum(mmrs) / len(mmrs))
        mmrs = []
        missing = 0
        for champion in team1_champs:
            try:
                mmrs.append(self.champion_mmrs[league].loc[champion][0])
            except KeyError:
                _log.warning('failed to get champion mmr', exc_info=True, stack_info=True)
                missing += 1
        average = sum(mmrs) / len(mmrs)
        if trace:
            _log.info(mmrs)
        for _ in range(missing):
            mmrs.append(average)
        v.append(sum(mmrs) / len(mmrs))
        mmrs = []
        missing = 0
        for champion in team2_champs:
            try:
                mmrs.append(self.champion_mmrs[league].loc[champion][0])
            except KeyError:
                _log.warning('failed to get champion mmr', exc_info=True, stack_info=True)
                missing += 1
        average = sum(mmrs) / len(mmrs)
        if trace:
            _log.info(mmrs)
        for _ in range(missing):
            mmrs.append(average)
        v.append(sum(mmrs) / len(mmrs))
        if trace:
            _log.info(v)
        v[0] = expected(v[0], v[1])
        v[1] = 1 - v[0]
        v[2] = expected(v[2], v[3])
        v[3] = 1 - v[2]
        return v
        # for player in team1_players + team2_players:
        #     try:
        #         v.append(self.player_mmrs[league].loc[player][0])
        #     except KeyError as e:
        #         v.append(1200.0)
        # for champion in team1_champs + team2_champs:
        #     try:
        #         v.append(self.champion_mmrs[league].loc[champion][0])
        #     except KeyError as e:
        #         v.append(1200.0)
        # return v
        #
    def training_vec(self, team1_players, team2_players, team1_champs, team2_champs, league, red_win):
        v = self.vec(team1_players, team2_players, team1_champs, team2_champs, league)
        v.append(red_win)
        return v

    def create_training_data(self, start_date='2023-04', end_date='3000'):
        for league in self.leagues:
            rows = []
            matches = self.matches.loc[(self.matches['Short'] == league.string) & (self.matches['DateTime UTC'] > start_date) & (self.matches['DateTime UTC'] < end_date+' 00:00:00')]
            if len(matches) > 0:
                for _, match in matches.iterrows():
                    team1 = match['Team1Players'].split(',')
                    team2 = match['Team2Players'].split(',')
                    team1_picks = match['Team1Picks'].split(',')
                    team2_picks = match['Team2Picks'].split(',')
                    red_win = int(match['Winner']) - 1
                    v = self.training_vec(team1, team2, team1_picks, team2_picks, league, red_win)
                    v.append(match['DateTime UTC'])
                    rows.append(v)
                df = pandas.DataFrame(rows)
                df.columns = [*df.columns[:-2], 'red_win', 'DateTime UTC']
                df.to_csv(f'{self.data_path}/{league.string}/training.csv', index=False)

    def train(self, leagues=ALL_LEAGUES, classifier=LogisticRegression(max_iter=100000000, solver='lbfgs', penalty=None), stored=False, date=str(datetime.utcnow().date())):
        for league in leagues:
            df = pandas.read_csv(f'{self.data_path}/{league.string}/training.csv')
            # train, test = train_test_split(df, test_size=.1)
            # train = df.loc[df['DateTime UTC'] < '2024']
            # test = df.loc[df['DateTime UTC'] > '2024']
            train = df
            x_cols = list(df.columns.values)
            x_cols.remove('red_win')
            x_cols.remove('DateTime UTC')
            # x_cols.remove('N GameInMatch')
            # scaler = MinMaxScaler()
            x_train = train[x_cols].values
            y_train = train['red_win'].values
            # x_test = test[x_cols].values
            # y_test = test['red_win'].values
            # x_train = scaler.fit_transform(train[x_cols].values)
            # y_train = train['red_win'].values
            # x_test = scaler.transform(test[x_cols].values)
            # y_test = test['red_win'].values
            curr_max = None
            max_acc = 0.0
            for i in range(1):
                classifier_curr = clone(classifier)
                classifier_curr.fit(x_train, y_train)
                acc = classifier_curr.score(x_train, y_train)
                if acc > max_acc:
                    curr_max = classifier_curr
                    max_acc = acc

            print(league.string)
            print(curr_max.coef_)
            print('train accuracy')
            print(curr_max.score(x_train, y_train))
            if stored:
                if not exists(f'{self.data_path}/{league.string}/{date}'):
                    makedirs(f'{self.data_path}/{league.string}/{date}')
                pickle.dump(classifier_curr, open(f'{self.data_path}/{league.string}/{date}/model.skl', 'wb'))
            else:
                pickle.dump(classifier_curr, open(f'{self.data_path}/{league.string}/model.skl', 'wb'))

            # pickle.dump(scaler, open(f'{self.data_path}/{league.string}/scaler.skl', 'wb'))

    def predict(self, players, champs, league, date='', trace=False):
        v = self.vec(players[:5], players[-5:], champs[:5], champs[-5:], league, trace)
        model = pickle.load(open(f'{self.data_path}/{league.string}/model.skl', 'rb')) if not date else pickle.load(open(f'{self.data_path}/{league.string}/{date}/model.skl', 'rb'))
        v = [v]
        # scaler = pickle.load(open(f'{self.data_path}/{league.string}/scaler.skl', 'rb'))
        # v = scaler.transform(v)
        if trace:
            _log.info(v)
        return model.predict_proba(v)[0][0]

    def test(self, end_date, classifier=LogisticRegression(max_iter=100000000, solver='liblinear', penalty='l2')):
        num_correct = 0
        total = 0
        for league in self.leagues:
            df = pandas.read_csv(f'{self.data_path}/{league.string}/training.csv')
            train = df.loc[df['DateTime UTC'] < end_date+' 00:00:00']
            test = df.loc[df['DateTime UTC'] > end_date]
            if len(test) == 0:
                continue
            x_cols = list(df.columns.values)
            x_cols.remove('red_win')
            x_cols.remove('DateTime UTC')
            x_train = train[x_cols].values
            y_train = train['red_win'].values
            x_test = test[x_cols].values
            y_test = test['red_win'].values
            classifier_curr = clone(classifier)
            classifier_curr.fit(x_train, y_train)
            acc = classifier_curr.score(x_test, y_test)
            total += len(y_test)
            num_correct += len(y_test) * acc
            print(league.string)
            print(len(y_test))
            print('test accuracy')
            print(acc)
            print('train accuracy')
            print(classifier_curr.score(x_train, y_train))
        print(f'total: {num_correct/total:f}')

    def test_day(self, test_date, classifier=LogisticRegression(max_iter=100000000, solver='liblinear', penalty='l1')):
        num_correct = 0
        total = 0
        league_correct = dict.fromkeys(self.leagues, 0.0)
        league_total = dict.fromkeys(self.leagues, 0.0)
        for league in self.leagues:
            df = pandas.read_csv(f'{self.data_path}/{league.string}/training.csv')
            train = df.loc[df['DateTime UTC'] < str(test_date)]
            test = df.loc[(df['DateTime UTC'] > str(test_date)) & (df['DateTime UTC'] < str(test_date + timedelta(days=1)))]
            if len(test) == 0 or len(train) == 0:
                continue
            x_cols = list(df.columns.values)
            x_cols.remove('red_win')
            x_cols.remove('DateTime UTC')
            x_train = train[x_cols].values
            y_train = train['red_win'].values
            x_test = test[x_cols].values
            y_test = test['red_win'].values
            classifier_curr = clone(classifier)
            classifier_curr.fit(x_train, y_train)
            acc = classifier_curr.score(x_test, y_test)
            total += len(y_test)
            num_correct += len(y_test) * acc
            league_total[league] += len(y_test)
            league_correct[league] += len(y_test) * float(acc)
            # print(league.string)
            # print(len(y_test))
            # print('test accuracy')
            # print(acc)
            # print('train accuracy')
            # print(classifier_curr.score(x_train, y_train))
        # print(f'total: {num_correct/total:f}')
        # print(league_correct, league_total)
        return league_correct, league_total

def test(start_date='2023-04', end_date=str(datetime.now() - timedelta(days=1))):
    leagues = ALL_LEAGUES
    players = Players(leagues)
    players.train(k_exponential, start_date=start_date, end_date=end_date)
    champs = Champions(leagues, players, True)
    champs.train(k_exponential, start_date=start_date, end_date=end_date)
    combined = PlayersAndChampions(leagues, champs)
    combined.create_training_data(start_date)
    combined.test(end_date)
    return combined

def train(end_date=str(datetime.utcnow().date()), store=True):
    leagues = ALL_LEAGUES
    players = Players(leagues)
    players.train(k_exponential, start_date='2023-04', end_date=end_date, store=store)
    champs = Champions(leagues, players, True, end_date)
    champs.train(k_constant, start_date='2024-00-00', end_date=end_date, store=store)
    combined = PlayersAndChampions(leagues, champs, end_date)
    if store:
        combined.create_training_data('2023-04', end_date=end_date)
        combined.train(stored=True, date=end_date)
    return combined

def test_days(train_start='2023-04', start_date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7), days=7):
    leagues = ALL_LEAGUES.copy()
    # leagues.remove(League.CBLOL)
    # leagues.remove(League.CBLOLA)
    # leagues.remove(League.SL)
    # leagues.remove(League.TCL)
    # leagues.remove(League.NACL)
    # leagues.remove(League.LCS)
    # leagues.remove(League.NLC)
    # leagues.remove(League.LPLOL)
    # leagues.remove(League.LIT)
    # leagues.remove(League.LEC)
    # leagues.remove(League.LCKCL)
    # leagues.remove(League.LCO)
    leagues_correct = dict.fromkeys(leagues, 0.0)
    leagues_total = dict.fromkeys(leagues, 0.0)
    for i in range(days):
        print(f'day: {i+1}')
        players = Players(leagues)
        players.train(k_exponential, start_date=train_start, end_date=str(start_date))
        champs = Champions(leagues, players, True)
        champs.train(k_exponential, start_date=train_start, end_date=str(start_date))
        combined = PlayersAndChampions(leagues, champs)
        combined.create_training_data(train_start)
        league_correct, league_total = combined.test_day(start_date)
        for league in league_total.keys():
            leagues_correct[league] += league_correct[league]
            leagues_total[league] += league_total[league]
        start_date = start_date + timedelta(days=1)
    for league in leagues:
        if leagues_total[league] > 0:
            print(f'{league.string}\ngames: {leagues_total[league]}\naccuracy: {leagues_correct[league]/leagues_total[league]}')
    print(f'total: {sum(leagues_correct.values())/sum(leagues_total.values())}')

def select_side(league, left_win, right_win, left_odds, right_odds, vec):
    if league in PREDICTABLE_LEAGUES:
        if left_win > 0.45 and left_win > left_odds:
            return 1
        elif right_win > 0.46 and right_win > right_odds:
            return 2
    else:
        if left_win > .5 and vec[2] > .62:
            return 1
        elif right_win > .5 and vec[3] > .64:
            return 2
    return 0
    # if league in PREDICTABLE_LEAGUES:
    #     if left_win > 0.5:
    #         left_side.click()
    #         return True
    #     elif right_win > 0.5:
    #         right_side.click()
    #         return True
    # else:
    #     if left_win > 0.5:
    #         left_side.click()
    #         return True
    #     elif right_win > 0.5:
    #         right_side.click()
    #         return True
    # return False

