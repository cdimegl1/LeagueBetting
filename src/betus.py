from multiprocessing import Queue
import copy
# from queue import Queue
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.webdriver.chrome.options
import watcher
from datetime import datetime, timezone, timedelta
from bettor import GameFetcher
import signal
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from fuzzywuzzy import fuzz
import constants
import api
from logging import getLogger
from fuzzywuzzy import fuzz
from time import sleep
import models.mmr
import logger

_log = getLogger('main.betus')

class DriverlessGame:
    def __init__(self, game) -> None:
        self.t1 = game.t1
        self.t2 = game.t2
        self.league = game.league

    def __repr__(self):
        if self.league:
            return f'{self.league.string}: {self.t1} v {self.t2}'
        else:
            return f'{self.t1} v {self.t2}'

class Game:
    def __init__(self, game, driver):
        self.driver = driver
        self.ele = game
        team_names = game.find_elements(By.CSS_SELECTOR, '.vgAKr.nhhlw')
        self.t1 = team_names[0].text
        self.t2 = team_names[1].text
        league_element = game.find_element(By.CLASS_NAME, 'yQXfW').find_element(By.CLASS_NAME, 'TPTLb').get_attribute('title')
        try:
            # self.league = next(league for league in constants.ALL_LEAGUES if league.string == league_element.upper())
            self.league = constants.str_to_league[league_element.upper()]
        except Exception:
            self.league = None
            _log.warn('no league for name %s', league_element)

    def get_odds(self, num):
        try:
            self.ele.find_element(By.CLASS_NAME, 'YXBt9').click()
        except:
            pass
        sleep(1)
        rows = self.ele.find_elements(By.CLASS_NAME, 'QRuJL')
        self.driver.execute_script('arguments[0].scrollIntoView();', self.ele)
        for row in rows:
            if row.find_element(By.CLASS_NAME, 'cl79F').text == f'WINNER MAP {num:d}':
                odds = row.find_elements(By.CSS_SELECTOR, '.tFiVV.on_SO')
                while True:
                    left_side = WebDriverWait(odds[0], 30,
                                            poll_frequency=0.5).until(
                                                    EC.presence_of_element_located(
                                                        (By.CSS_SELECTOR,
                                                        '.vjymC.jArAv:not(.qXQFA)'))).text
                    if left_side != '':
                        break
                while True:
                    right_side = WebDriverWait(odds[1], 30,
                                            poll_frequency=0.5).until(
                                                    EC.presence_of_element_located(
                                                        (By.CSS_SELECTOR,
                                                            '.vjymC.jArAv:not(.qXQFA)'))).text
                    if right_side != '':
                        break
                return 1 / float(left_side), 1 / float(right_side)
        self.ele.find_element(By.CLASS_NAME, 'y3ntc').click()
        odds = self.ele.find_elements(By.CSS_SELECTOR, '.tFiVV.on_SO')
        left_side = None
        right_side = None
        while True:
            left_side = WebDriverWait(odds[0], 30,
                                        poll_frequency=0.5).until(
                                                EC.presence_of_element_located(
                                                    (By.CSS_SELECTOR,
                                                    '.vjymC.jArAv:not(.qXQFA)')))
            if left_side.text != '':
                break
        while True:
            right_side = WebDriverWait(odds[1], 30,
                                        poll_frequency=0.5).until(
                                                EC.presence_of_element_located(
                                                    (By.CSS_SELECTOR,
                                                    '.vjymC.jArAv:not(.qXQFA)')))
            if right_side.text != '':
                break
        return 1 / float(left_side.text), 1 / float(right_side.text)
    
    def __repr__(self):
        if self.league:
            return f'{self.league.string}: {self.t1} v {self.t2}'
        else:
            return f'{self.t1} v {self.t2}'

saved_betus_games = []

def get_odds(driver, game, num):
    _log.info('getting odds for %s', game)
    sleep(1)
    try:
        games = get_games(driver)
        ele = None
        for g in games:
            if game.t1 == g.t1:
                ele = g.ele
                break
        try:
            ele.find_element(By.CLASS_NAME, 'YXBt9').click()
        except:
            pass
        rows = ele.find_elements(By.CLASS_NAME, 'QRuJL')
        driver.execute_script('arguments[0].scrollIntoView();', ele)
        for row in rows:
            if row.find_element(By.CLASS_NAME, 'cl79F').text == f'WINNER MAP {num:d}':
                _log.info('waiting for odds')
                odds = row.find_elements(By.CSS_SELECTOR, '.tFiVV.on_SO')
                while True:
                    left_side = WebDriverWait(odds[0], 30,
                                            poll_frequency=2.0).until(
                                                    EC.presence_of_element_located(
                                                        (By.CSS_SELECTOR,
                                                        '.vjymC.jArAv:not(.qXQFA)'))).text
                    if left_side != '':
                        break
                while True:
                    right_side = WebDriverWait(odds[1], 30,
                                            poll_frequency=2.0).until(
                                                    EC.presence_of_element_located(
                                                        (By.CSS_SELECTOR,
                                                            '.vjymC.jArAv:not(.qXQFA)'))).text
                    if right_side != '':
                        break
                ele.find_element(By.CLASS_NAME, 'y3ntc').click()
                return 1 / float(left_side), 1 / float(right_side)
        _log.info('waiting for odds')
        games = get_games(driver)
        for g in games:
            if game.t1 == g.t1:
                ele = g.ele
                break
        ele.find_element(By.CLASS_NAME, 'y3ntc').click()
        odds = ele.find_elements(By.CSS_SELECTOR, '.tFiVV.on_SO')
        left_side = None
        right_side = None
        while True:
            left_side = WebDriverWait(odds[0], 30,
                                        poll_frequency=0.5).until(
                                                EC.presence_of_element_located(
                                                    (By.CSS_SELECTOR,
                                                    '.vjymC.jArAv:not(.qXQFA)'))).text
            if left_side != '':
                break
        while True:
            right_side = WebDriverWait(odds[1], 30,
                                        poll_frequency=0.5).until(
                                                EC.presence_of_element_located(
                                                    (By.CSS_SELECTOR,
                                                    '.vjymC.jArAv:not(.qXQFA)'))).text
            if right_side != '':
                break
        return 1 / float(left_side), 1 / float(right_side)
    except Exception as e:
        _log.warning('failed to get odds', exc_info=True)

def start_driver():
    options = webdriver.ChromeOptions() 
    options.add_argument(f'--user-data-dir=/home/cdimegl1/Betting/chrome-data/betus')
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False) 
    options.add_argument("--enable-features=UseOzonePlatform")
    options.add_argument("--ozone-platform=wayland")
    driver = webdriver.Chrome(options=options) 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    driver.get('https://www.betus.com.pa/e-sports')
    return driver

def login(driver):
    try:
        driver.find_element(By.ID, 'loginAccount').send_keys(constants.BETUS_ID)
        sleep(1)
        driver.find_element(By.ID, 'loginPassword').send_keys(constants.BETUS_PASSWORD)
        sleep(2)
        driver.find_element(By.CLASS_NAME, 'login-submit').click()
        _log.info('logged in')
        sleep(5)
    except Exception as e:
        print(e)
        _log.info('already logged in')
        sleep(5)
    driver.get('https://www.betus.com.pa/e-sports')
    WebDriverWait(driver, 10, poll_frequency=2).until(
            EC.frame_to_be_available_and_switch_to_it('upb-iframe'))
    button = WebDriverWait(driver, 20, poll_frequency=2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            '.POzGs[title=\"League of Legends\"]')))
    ActionChains(driver).move_to_element(button).click(button).perform()
    sleep(5) 

def get_games(driver):
    games = driver.find_elements(By.CLASS_NAME, 'CIXLg')[:8]
    games = [Game(game, driver) for game in games]
    if len(games) == 0:
        login(driver)
    return games[:7]

class Matcher:
    def __init__(self, excluded) -> None:
        self.gameIds = []
        self.excluded = excluded

    def get_matches(self, driver):
        betus_games = get_games(driver)
        global saved_betus_games
        saved_betus_games = betus_games
        api_games = list(filter(lambda x: x.gameId not in self.excluded, api.get_schedule()))
        matches = []
        for a in api_games:
            a1 = a.blue_team.lower()
            a2 = a.red_team.lower()
            candidates = []
            for s in betus_games:
                s1 = s.t1.lower()
                s2 = s.t2.lower()
                if (fuzz.partial_ratio(a1, s1) + fuzz.partial_ratio(a2, s2)) > 150 or (fuzz.partial_ratio(a2, s1) + fuzz.partial_ratio(a1, s2)) > 150:
                    candidates.append((max(fuzz.partial_ratio(a1, s1) + fuzz.partial_ratio(a2, s2), fuzz.partial_ratio(a2, s1) + fuzz.partial_ratio(a1, s2)), s))
            if candidates and a.gameId not in self.gameIds:
                s = max(candidates, key=lambda x: x[0])[1]
                matches.append((s, a, a.gameId))
                self.gameIds.append(a.gameId)
                _log.info('matched %s - %d - id: %s', s, a.number, a.gameId)
        return matches

def dispatch(excluded=[], game_nums={}):
    _log.info('starting bettor')
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    driver = start_driver()
    def cleanup(signum, frame):
        driver.quit()
        _log.info('quit driver')
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, cleanup)
    login(driver)
    matcher = Matcher(excluded)
    dispatcher = watcher.Dispatcher(game_nums)
    fetcher = GameFetcher()
    q = Queue()
    last_time = datetime.now() - timedelta(seconds=61)
    while True:
        try:
            if (datetime.now() - last_time).seconds > 60:
                last_time = datetime.now()
                dispatcher.update(q, fetcher.get_games())
                matches = matcher.get_matches(driver)
                for s, a, gameId in matches:
                    s = DriverlessGame(s)
                    q.put((s, a))
                sleep(1)
                print(q.qsize())
            if not q.empty():
                _log.info('queue not empty')
                val = q.get()
                if len(val) == 2:
                    site_game, api_game = val
                    blue_team = api_game.blue_team
                    red_team = api_game.red_team
                    blue_players, red_players = api_game.get_players()
                    _log.info(blue_players)
                    _log.info(red_players)
                    blue_champs, red_champs = api_game.get_champs()
                    _log.info('placing bet for %s', site_game)
                    if fuzz.partial_ratio(blue_team.lower(), site_game.t1.lower()) > fuzz.partial_ratio(blue_team.lower(), site_game.t2.lower()) and fuzz.partial_ratio(red_team.lower(), site_game.t2.lower()) > fuzz.partial_ratio(red_team.lower(), site_game.t1.lower()):
                        blue_team = site_game.t1
                        red_team = site_game.t2
                    elif fuzz.partial_ratio(red_team.lower(), site_game.t2.lower()) < fuzz.partial_ratio(red_team.lower(), site_game.t1.lower()) and fuzz.partial_ratio(blue_team.lower(), site_game.t2.lower()) > fuzz.partial_ratio(blue_team.lower(), site_game.t1.lower()):
                        blue_team = site_game.t2
                        red_team = site_game.t1
                    else:
                        _log.error('team sides could not be matched to site sides')

                    _log.info('blue team: %s', blue_team)
                    _log.info('red team: %s', red_team)
                    model = models.mmr.PlayersAndChampions()
                    blue_win = run_model(model, blue_players+red_players, blue_champs+red_champs, site_game.league)
                    vec = model.vec(blue_players, red_players, blue_champs, red_champs, site_game.league)
                    red_win = 1 - blue_win
                    _log.info('blue win: %f', blue_win)
                    _log.info('red win: %f', red_win)
                    left_win = None
                    right_win = None
                    blue_odds = None
                    red_odds = None
                    left_odds, right_odds = get_odds(driver, site_game, api_game.number)
                    if blue_team == site_game.t1:
                        left_win = blue_win
                        right_win = red_win
                        blue_odds = left_odds
                        red_odds = right_odds
                    elif blue_team == site_game.t2:
                        left_win = red_win
                        right_win = blue_win
                        blue_odds = right_odds
                        red_odds = left_odds
                    else:
                        _log.error('teams do not match')
                        return
                    _log.info(site_game)
                    _log.info('model odds: %f %f', left_win, right_win)
                    _log.info('site odds: %f %f', left_odds, right_odds)
                    on = select_side(constants.coefs[datetime.utcnow().date()][site_game.league], blue_odds, red_odds, blue_win, vec)
                    # on = select_side(constants.coefs[datetime.utcnow().date()]['all'], blue_odds, red_odds, blue_win, vec)
                    if on == 0:
                        _log.info('no bet placed for %s', site_game)
                    if on == 1:
                        if blue_team == site_game.t1:
                            _log.info('BET: %s LEFT', site_game)
                        else:
                            _log.info('BET: %s RIGHT', site_game)
                    elif on == 2:
                        if red_team == site_game.t2:
                            _log.info('BET: %s RIGHT', site_game)
                        else:
                            _log.info('BET: %s LEFT', site_game)
                    log_bet(blue_team, red_team, api_game.number, blue_players, red_players, blue_champs, red_champs, blue_odds, red_odds, blue_win, red_win, site_game.league, on)
                else:
                    site_game, players, champs, blue_team, red_team = val
                    _log.info(players)
                    _log.info(champs)
                    _log.info('placing bet for %s', site_game)
                    _log.info('blue team: %s', blue_team)
                    _log.info('red team: %s', red_team)
                    model = models.mmr.PlayersAndChampions()
                    blue_win = run_model(model, players, champs, site_game.league)
                    vec = model.vec(players[:5], players[-5:], champs[:5], champs[-5:], site_game.league)
                    red_win = 1 - blue_win
                    _log.info('blue win: %f', blue_win)
                    _log.info('red win: %f', red_win)
                    left_win = None
                    right_win = None
                    blue_odds = None
                    red_odds = None
                    candidates = []
                    s = get_games(driver)
                    for s in s:
                       s1 = s.t1.lower()
                       s2 = s.t2.lower()
                       candidates.append((s, 'left', fuzz.partial_ratio(s1, blue_team)))
                       candidates.append((s, 'right', fuzz.partial_ratio(s2, blue_team)))
                    s, side, score = max(candidates, key=lambda x: x[2])
                    if blue_team == s.t1 or red_team == s.t2:
                        side = 'left'
                    elif blue_team == s.t2 or red_team == s.t1:
                        side = 'right'
                    left_odds, right_odds = get_odds(driver, s, site_game.game)
                    if side == 'left':
                        left_win = blue_win
                        right_win = red_win
                        blue_odds = left_odds
                        red_odds = right_odds
                    elif side == 'right':
                        left_win = red_win
                        right_win = blue_win
                        blue_odds = right_odds
                        red_odds = left_odds
                    else:
                        _log.error('teams do not match')
                        return
                    _log.info(site_game)
                    _log.info('model odds: %f %f', left_win, right_win)
                    _log.info('site odds: %f %f', left_odds, right_odds)
                    on = select_side(constants.coefs[datetime.utcnow().date()][site_game.league], blue_odds, red_odds, blue_win, vec)
                    # on = select_side(constants.coefs[datetime.utcnow().date()]['all'], blue_odds, red_odds, blue_win, vec)
                    if on == 0:
                        _log.info('no bet placed for %s', site_game)
                    if on == 1:
                        if side == 'left':
                            _log.info('BET: %s LEFT', site_game)
                        else:
                            _log.info('BET: %s RIGHT', site_game)
                    elif on == 2:
                        if side == 'right':
                            _log.info('BET: %s LEFT', site_game)
                        else:
                            _log.info('BET: %s RIGHT', site_game)
                    log_bet(blue_team, red_team, site_game.game, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, red_win, site_game.league, on)
            else:
                sleep(5)
                continue
        except Exception as e:
            print(e)
            continue

def run_model(model, players, champs, league):
    return model.predict(players, champs, league, str(datetime.utcnow().date()), True)

def log_bet(blue_team, red_team, game, blue_players, red_players, blue_champs, red_champs, blue_odds, red_odds, blue_win, red_win, league, on=0):
    cur = constants.db.cursor()
    cur.execute(r'INSERT INTO bets (dt, league, blue_team, red_team, game, blue_players, red_players, blue_champs, red_champs, blue_odds, red_odds, blue_win, red_win, "on") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (datetime.now(timezone.utc), league.string, blue_team, red_team, game, str(blue_players), str(red_players), str(blue_champs), str(red_champs), blue_odds, red_odds, blue_win, red_win, on))
    constants.db.commit()
    cur.close()

def select_side(x, blue_odds, red_odds, blue_win, vec):
    if (blue_odds > x[0] and
        blue_odds < x[1] and
        vec[0] > x[2] and
        vec[2] > x[3]):
        return 1
    if (red_odds > x[4] and
        red_odds < x[5] and
        vec[1] > x[6] and
        vec[3] > x[7]):
        return 2
    return 0
    # if (blue_odds > x[0] and
    #     blue_odds < x[1] and
    #     vec[0] > x[2] and
    #     vec[2] > x[3] and
    #     blue_win > x[4]):
    #     return 1
    # if (red_odds > x[5] and
    #     red_odds < x[6] and
    #     vec[1] > x[7] and
    #     vec[3] > x[8] and
    #     1 - blue_win > x[9]):
    #     return 2
    # return 0
    # if (blue_win > x[0] and
    #     blue_odds > x[1] and
    #     blue_win > blue_odds + x[2] and
    #     vec[0] > x[3] and
    #     vec[2] > x[4]):
    #     return 1
    # if (1 - blue_win > x[5] and
    #     red_odds > x[6] and
    #     1 - blue_win > red_odds + x[7] and
    #     vec[1] > x[8] and
    #     vec[3] > x[9]):
    #     return 2
    # return 0
