from os import path
from selenium.webdriver.common.by import By
import selenium.webdriver.chrome.options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import models.mmr
import selenium.webdriver.firefox.options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timezone
import constants
import api
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process, Queue
import time
import signal
import sys
from fuzzywuzzy import fuzz
from logging import getLogger
import watcher
import logger

_log = getLogger('main.bettor')

class Game:
    def __init__(self, game):
        self.t1 = game.find_element(By.CSS_SELECTOR, '.teamName.leftname').text
        self.t2 = game.find_element(By.CSS_SELECTOR, '.teamName.rightname').text
        self.matchid = int(game.get_attribute('data-parentmatchid'))
        try:
            game_str = game.find_element(By.CLASS_NAME, 'info').text
            self.game = int(''.join(filter(str.isdigit, game_str)))
        except Exception:
            self.game = 0
        try:
            game.find_element(By.CLASS_NAME, 'live_icn')
            self.live = True
        except Exception:
            self.live = False
        icon_src = game.find_element(By.CLASS_NAME, 'league_icon').find_element(By.TAG_NAME, 'img').get_attribute('src')
        try:
            self.league = next(league for league in constants.ALL_LEAGUES if league.src == icon_src)
        except Exception:
            self.league = None
            _log.warn('no league for icon src %s', icon_src)

    def __repr__(self):
        if self.league:
            return f'{self.league.string}: {self.t1} v {self.t2} game {self.game:d}'
        else:
            return f'{self.t1} v {self.t2} game {self.game:d}'

def get_games():
    games = []
    # os.environ['MOZ_HEADLESS_WIDTH'] = '1920'
    # os.environ['MOZ_HEADLESS_HEIGHT'] = '1080'
    # profile = selenium.webdriver.FirefoxProfile('/home/cdimegl1/.mozilla/firefox/eufah8l8.default-release')
    profile = selenium.webdriver.FirefoxProfile('/home/cdimegl1/Betting/firefox-data/profile1')
    options = selenium.webdriver.firefox.options.Options()
    options.headless = True
    while True:
        driver = webdriver.Firefox(options=options, service=Service(log_path=path.devnull), firefox_profile=profile)
        driver.set_window_size(1920, 1080)
        try:
            driver.get('https://www.esportsbet.io/esportsbull/')
            WebDriverWait(driver, 60, poll_frequency=2).until(
                    EC.frame_to_be_available_and_switch_to_it('iFrameResizer0'))
            old_button = WebDriverWait(driver, 60, poll_frequency=1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    '.prodBtn.oldEsports'))).click()
            WebDriverWait(driver, 60, poll_frequency=2).until(
                    EC.presence_of_element_located((By.CLASS_NAME,
                                                    'gametype_btn'))).click()
            time.sleep(1)
            games = WebDriverWait(driver, 60, poll_frequency=2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    '.gamesListins_content.el_pg')))
            games = games.find_elements(By.TAG_NAME, 'a')[:10]
            games = [Game(game) for game in games[:10]]
        except KeyboardInterrupt:
            _log.info('closing game schedule fetcher')
            driver.quit()
            raise 
        except Exception:
            _log.warn('failed to get games', exc_info=True, stack_info=True)
            driver.quit()
            continue
        else:
            driver.quit()
            break
    _log.debug('got games %s', games)
    _log.info('got games successfully')
    return games[:10]

def match_games(site_games, api_games):
    matches = []
    for a in api_games:
        a1 = a.blue_team.lower()
        a2 = a.red_team.lower()
        candidates = []
        for s in site_games:
            s1 = s.t1.lower()
            s2 = s.t2.lower()
            if (fuzz.partial_ratio(a1, s1) + fuzz.partial_ratio(a2, s2)) > 130 or (fuzz.partial_ratio(a2, s1) + fuzz.partial_ratio(a1, s2)) > 130:
                if s.league and s.live and s.game > 0:
                    candidates.append((max(fuzz.partial_ratio(a1, s1) + fuzz.partial_ratio(a2, s2), fuzz.partial_ratio(a2, s1) + fuzz.partial_ratio(a1, s2)), s))
        if candidates:
            s = max(candidates, key=lambda x: x[0])[1]
            matches.append((s, a, a.gameId))
            _log.info('found match for game %s', s)
    return matches

class Bettor(Process):

    def __init__(self, q):
        super().__init__()
        self.q = q
        # self.driver = None

    def start_driver(self):
        options = selenium.webdriver.firefox.options.Options()
        profile = selenium.webdriver.FirefoxProfile('/home/cdimegl1/Betting/firefox-data/profile1')
        caps = DesiredCapabilities().FIREFOX
        caps['pageLoadStragey'] = 'eager'
        # options.headless = True
        self.driver = webdriver.Firefox(options=options, service=Service(log_path=path.devnull), desired_capabilities=caps, firefox_profile=profile)

    def login(self):
        try:
            self.driver.get('https://esportsbet.io')
            self.driver.find_element(By.CSS_SELECTOR,
                                     '.ButtonsStyled__RegisterButton-sc-16c3xpm-1.jENxMU').click()
            login = self.driver.find_elements(By.CSS_SELECTOR,
                                              '.LoginStyled__Input-sc-i43fsv-22.dfMPJA')
            login[0].clear()
            login[0].send_keys(constants.ESPORTSBETIO_USERNAME)
            login[1].clear()
            login[1].send_keys(constants.ESPORTSBETIO_PASSWORD)
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR,'.CustomButtonStyled__Button-sc-1fr3aja-0.blQEmU').click()
            time.sleep(5)
            _log.info('logged in')
        except Exception:
            _log.info('already logged in')
            time.sleep(5)
        try:
            WebDriverWait(self.driver, 4,
                          poll_frequency=2).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                  '.Modal2Styled__ModalClose-sc-1krmo8u-4.hNgmTW'))).click()
        except Exception:
            pass
        self.switch_to_btc()
        self.driver.switch_to.parent_frame()
        currency_before = float(self.driver.find_element(By.CSS_SELECTOR, '.CurrencyBalanceDropdownStyled__Amount-sc-ey47rs-9.aenmd').text)
        _log.info('current balance: %f', currency_before)


    def switch_to_btc(self):
        selected_currency = WebDriverWait(self.driver, 10, poll_frequency=2).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.CurrencyBalanceDropdownStyled__DropdownButton-sc-ey47rs-1.DPvoO')))
        selected_currency = selected_currency.find_element(By.TAG_NAME, 'svg')
        selected_currency = selected_currency.get_attribute('data-djid')
        if 'btc' not in selected_currency:
            WebDriverWait(self.driver, 20, poll_frequency=2).until( EC.presence_of_element_located( (By.CSS_SELECTOR, '.CurrencyBalanceDropdownStyled__DropdownButton-sc-ey47rs-1.DPvoO'))).click()
            crypto_options = self.driver.find_elements(By.CSS_SELECTOR, '.CurrencyBalanceDropdownStyled__DropdownSuboption-sc-ey47rs-5.xWsiZ')
            for opt in crypto_options:
                if 'BTC' in opt.text:
                    opt.click()
                    _log.info('switched to btc')
                    break
            time.sleep(10)
        else:
            _log.info('using btc')

    def nav_to_odds_page(self):
        self.driver.get('https://esportsbet.io/esportsbull')
        WebDriverWait(self.driver, 60, poll_frequency=2).until(
                EC.frame_to_be_available_and_switch_to_it('iFrameResizer0'))
        WebDriverWait(self.driver, 60, poll_frequency=2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                '.prodBtn.oldEsports'))).click()
        # self.driver.execute_script('arguments[0].scrollIntoView();', old_button)
        WebDriverWait(self.driver, 60, poll_frequency=2).until(
                EC.presence_of_element_located((By.CLASS_NAME,
                                                'gametype_btn'))).click()
        live_odds = self.driver.find_element(By.CLASS_NAME,
                                             'icon-fi-simple-arrow-right')
        # time.sleep(1)
        # self.driver.execute_script('arguments[0].scrollIntoView();', live_odds)
        # actions = ActionChains(self.driver)
        # actions.move_to_element(live_odds).perform()
        live_odds.click()
        _log.info('navigated to odds page')
        time.sleep(3)

    def click_game_in_list(self, site_game):
        while True:
            try:
                games = WebDriverWait(self.driver, 10, poll_frequency=2).until( EC.presence_of_element_located((By.CSS_SELECTOR, '.gamesListins_content.el_pg')))
                games = games.find_elements(By.TAG_NAME, 'a')[:10]
                for g in games:
                    matchid = int(g.get_attribute('data-parentmatchid'))
                    if matchid == site_game.matchid:
                        self.driver.execute_script("arguments[0].click();", g)
                        # g.click()
                        _log.info('clicked match %s', site_game)
                        break
                time.sleep(5)
            except Exception:
                _log.warn('failed to click game %s', site_game, exc_info=True, stack_info=True)
                self.nav_to_odds_page()
                continue
            else:
                break

    def input_bet(self, site_game, api_game, players, champs, blue_team, red_team, blue_win, red_win):
        try:
            currency_before = float(self.driver.find_element(By.CSS_SELECTOR, '.CurrencyBalanceDropdownStyled__Amount-sc-ey47rs-9.aenmd').text)
            WebDriverWait(self.driver, 20, poll_frequency=2).until(EC.frame_to_be_available_and_switch_to_it('iFrameResizer0'))
            left_side = WebDriverWait(self.driver, 60, poll_frequency=0.5).until( EC.presence_of_element_located( (By.CSS_SELECTOR, '.ah_odds_button.ah_left:not(.paused)')))
            right_side = self.driver.find_element(By.CSS_SELECTOR, '.ah_odds_button.ah_right')
            left_odds = 1 / float(left_side.find_element(By.CLASS_NAME, 'ah_odds').text)
            right_odds = 1 / float(right_side.find_element(By.CLASS_NAME, 'ah_odds').text)
            left_win = None
            right_win = None
            bet_on = ''
            amount = constants.unit_size
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
                self.nav_to_odds_page()
                _log.error('teams do not match')
                return
            _log.info(site_game)
            _log.info('model odds: %f %f', left_win, right_win)
            _log.info('site odds: %f %f', left_odds, right_odds)
            selected = models.mmr.select_side(left_side, right_side, site_game.league, left_win, right_win, left_odds, right_odds)
            if not selected:
                _log.info('no bet placed for %s', site_game)
                log_bet(blue_team, red_team, site_game.game, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, red_win, site_game.league)
                return
            amount = max(amount, .01)
            if currency_before < 0.01:
                _log.error('not enough currency')
                log_bet(blue_team, red_team, site_game.game, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, red_win, site_game.league)
                self.nav_to_odds_page()
                return
            input_bet = WebDriverWait(self.driver, 10, poll_frequency=.5).until( EC.presence_of_element_located( (By.CLASS_NAME, 'betplacementAmount_input')))
            input_bet = input_bet.find_element(By.CSS_SELECTOR, "input")
            input_bet.send_keys(str(round(amount, 2)))
            time.sleep(.1)
            bet_button = self.driver.find_element(By.CLASS_NAME, 'betButton')
            self.driver.execute_script('arguments[0].scrollIntoView();', bet_button)
            bet_button.click()
            success = WebDriverWait(self.driver, 15, poll_frequency=.5).until( EC.presence_of_element_located( (By.CLASS_NAME, 'bet_success_status'))).text
            assert 'Bet Placed Successfully' in success, 'betting error: bet did not go through'
        except Exception:
            _log.warn('retrying bet for %s', site_game, exc_info=True)
            if api_game:
                self.q.put((site_game, api_game))
            else:
                self.q.put((site_game, players, champs, blue_team, red_team))
        else:
            _log.info('placed bet for %s', site_game)
            log_bet(blue_team, red_team, site_game.game, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, red_win, site_game.league)

    def place_bet(self, site_game, api_game, players, champs, blue_team, red_team):

        if fuzz.partial_ratio(blue_team.lower(), site_game.t1.lower()) > fuzz.partial_ratio(blue_team.lower(), site_game.t2.lower()) or fuzz.partial_ratio(red_team.lower(), site_game.t2.lower()) > fuzz.partial_ratio(red_team.lower(), site_game.t1.lower()):
            blue_team = site_game.t1
            red_team = site_game.t2
        elif fuzz.partial_ratio(red_team.lower(), site_game.t2.lower()) < fuzz.partial_ratio(red_team.lower(), site_game.t1.lower()) or fuzz.partial_ratio(blue_team.lower(), site_game.t2.lower()) > fuzz.partial_ratio(blue_team.lower(), site_game.t1.lower()):
            blue_team = site_game.t2
            red_team = site_game.t1
        else:
            _log.error('team sides could not be matched to site sides')

        _log.info('blue team: %s', blue_team)
        _log.info('red team: %s', red_team)
        blue_win = run_model(models.mmr.PlayersAndChampions(), players, champs, site_game.league)
        red_win = 1 - blue_win
        _log.info('blue win: %f', blue_win)
        _log.info('red win: %f', red_win)
        self.click_game_in_list(site_game)
        self.driver.switch_to.parent_frame()
        try:
            self.switch_to_btc()
        except Exception:
            _log.warn('failed to swtich to btc', exc_info=True, stack_info=True)
            if api_game:
                self.q.put((site_game, api_game))
            else:
                self.q.put((site_game, players, champs, blue_team, red_team))
            return
        self.driver.switch_to.parent_frame()
        self.input_bet(site_game, api_game, players, champs, blue_team, red_team, blue_win, red_win)

    def run(self):
        def cleanup(num, frame):
            _log.info('cleaning up bettor process')
            try:
                self.driver.quit()
                sys.exit()
            except Exception:
                pass
        signal.signal(signal.SIGINT, cleanup)
        self.start_driver()
        while True:
            try:
                self.login()
                self.nav_to_odds_page()
                while True:
                    if self.q.empty():
                        time.sleep(5)
                    else:
                        q_val = self.q.get()
                        if len(q_val) == 2:
                            site_game, api_game = q_val
                            blue_team = api_game.blue_team
                            red_team = api_game.red_team
                            blue_players, red_players = api_game.get_players()
                            print(blue_players, red_players)
                            blue_champs, red_champs = api_game.get_champs()

                            _log.info('placing bet for %s', site_game)
                            self.place_bet(site_game, api_game, blue_players+red_players, blue_champs+red_champs, blue_team, red_team) 
                        else:
                            site_game, players, champs, blue_team, red_team = q_val
                            _log.info('placing bet for %s', site_game)
                            self.place_bet(site_game, None, players, champs, blue_team, red_team) 
                        self.nav_to_odds_page()
            except Exception:
                _log.warn('restarting bettor', exc_info=True, stack_info=True)
                continue

def dispatch(excluded=[], game_nums={}):
    _log.info('starting bettor')
    gIds = []
    q = Queue()
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    # original_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    bettor = Bettor(q)
    bettor.start()
    # dispatcher = watcher.Dispatcher()
    def cleanup(signum, frame):
        bettor.join()
        _log.info('reaped bettor')
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, cleanup)
    time.sleep(90)
    while True:
        site_games = None
        try:
            site_games = get_games()
        except Exception:
            continue
        site_games = list(filter(lambda x: x.matchid not in excluded, site_games))
        api_games = api.get_schedule()
        matches = match_games(site_games, api_games)
        for s, a, gameId in matches:
            if gameId not in gIds and s.game > 0:
                gIds.append(gameId)
                q.put((s, a))
        # dispatcher.update(q, site_games)
        time.sleep(90)

def run_model(model, players, champs, league):
    return model.predict(players, champs, league)

def log_bet(blue_team, red_team, game, blue_players, red_players, blue_champs, red_champs, blue_odds, red_odds, blue_win, red_win, league):
    cur = constants.db.cursor()
    cur.execute('INSERT INTO bets (dt, league, blue_team, red_team, game, blue_players, red_players, blue_champs, red_champs, blue_odds, red_odds, blue_win, red_win) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (datetime.now(timezone.utc), league.string, blue_team, red_team, game, str(blue_players), str(red_players), str(blue_champs), str(red_champs), blue_odds, red_odds, blue_win, red_win))
    constants.db.commit()
    cur.close()

