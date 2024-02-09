from multiprocessing import Process
from logging import getLogger
import multiprocessing
import signal
import constants
import cv2
import os
import sys
import uuid
import selenium
import time
from selenium import webdriver
import selenium.webdriver.chrome.options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from os import path
from image import mse, get_champs, get_names, crop_image, banner_present
from constants import League

_log = getLogger('main.watcher')

class Watcher(Process):
    def __init__(self, q, game):
        super().__init__()
        self.link = ''
        self.driver = None
        self.q = q
        self.game = game

    def watch(self):
        _log.error('watch is not implemented')
        return []
    
    def run(self):
        def cleanup(num, frame):
            _log.info('cleaning up watcher on %s', self.link)
            try:
                self.driver.quit()
                sys.exit()
            except Exception:
                pass
        signal.signal(signal.SIGINT, cleanup)
        players, champs, blue_team, red_team = self.watch()
        assert blue_team != red_team, 'get_names failed with equal teams'
        self.q.put((self.game, players, champs, blue_team, red_team))
        self.driver.quit()

class ChromeDataProvider:
    def __init__(self) -> None:
        self.lock = multiprocessing.Lock()
        self.num = 1

    def get(self):
        while True:
            with self.lock:
                yield f'{constants.CHROME_DATA_DIR}/data/data{self.num}'
                self.num += 1
                if self.num == 6:
                    self.num = 1

chrome_data_gen = ChromeDataProvider().get()

class Bilibili(Watcher):
    def __init__(self, q, game, link):
        super().__init__(q, game)
        self.link = link

    def watch(self):
        options = selenium.webdriver.chrome.options.Options()
        # options.add_argument('--headless=new')
        data_dir = next(chrome_data_gen)
        options.add_argument(f"--user-data-dir={data_dir}")
        options.add_argument("--profile-directory=Profile 1")
        options.add_argument("--enable-features=UseOzonePlatform")
        options.add_argument("--ozone-platform=wayland")
        options.binary_location = '/usr/bin/google-chrome'
        options.add_experimental_option("excludeSwitches", ['enable-logging', 'enable-automation'])
        options.add_argument('--width=1920')
        options.add_argument('--height=1080')
        options.add_argument('--mute-audio')
        #options.add_argument('force-device-scale-factor=0.75')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.set_window_size(1920, 1080)
        while True:
            try:
                self.driver.get(self.link)
                player = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'web-player-inject-wrap')))       
                self.driver.execute_script('arguments[0].scrollIntoView();', player)
                ActionChains(self.driver).move_to_element(player).perform()
                time.sleep(1)
                quality = self.driver.find_element(By.CSS_SELECTOR, '.quality-wrap.svelte-s2ukfj')
                ActionChains(self.driver).move_to_element(quality).perform()
                time.sleep(1)
                qualities = self.driver.find_elements(By.CSS_SELECTOR, '.list-it.svelte-s2ukfj')
                for quality in qualities:
                    if quality.text == '原画':
                        self.driver.execute_script("arguments[0].click();", quality)
                        # quality.click()
                        break
                time.sleep(3)
                # button = self.driver.find_element(By.CSS_SELECTOR, '.right-area.svelte-koac9q').find_elements(By.CSS_SELECTOR, '.tip-wrap.svelte-11g6lf7')[0]
                ActionChains(self.driver).move_to_element(player).perform()
                fullscreen = self.driver.find_element(By.CSS_SELECTOR, '.right-area.svelte-4rgwwa').find_element(By.CSS_SELECTOR, '.tip-wrap.svelte-11g6lf7')
                fullscreen.click()
                # self.driver.execute_script("arguments[0].click();", fullscreen)
                # ActionChains(self.driver).move_by_offset(0, -200).perform()
                time.sleep(5)
                uid = uuid.uuid1()
                screenshotName = path.join('../screenshots', str(uid)+'.png')
                self.driver.save_screenshot(screenshotName)
                im = cv2.imread(screenshotName)
                self.driver.quit()
                while not banner_present(im, self.game.league.string):
                    time.sleep(30)
                    self.driver.save_screenshot(screenshotName)
                    im_new = cv2.imread(screenshotName)
                    if mse(im, im_new) < 1:
                        raise Exception('consecutive screenshots are too similiar')
                    im = im_new
                left, right = crop_image(im)
                blue_champs = get_champs(left)
                red_champs = get_champs(right)
                blue_names, blue_team = get_names(left, self.game.t1, self.game.t2, self.game.league)
                red_names, red_team = get_names(right, self.game.t1, self.game.t2, self.game.league)
                return blue_names + red_names, blue_champs + red_champs, blue_team, red_team
            except Exception:
                _log.warn('bilibili watcher failed for %s', self.game, stack_info=True, exc_info=True)

class Dispatcher():
    def __init__(self) -> None:
        self.watchers = []
        self.game_nums = {}

    def update(self, q, games):
        to_delete = []
        for k in self.game_nums.keys():
            if k not in [game.matchid for game in games]:
                to_delete.append(k)
                finished = [watcher for watcher in self.watchers if watcher.game.matchid == k]
                self.watchers = [watcher for watcher in self.watchers if watcher not in finished]
                for watcher in finished:
                    os.kill(watcher.pid(), signal.SIGINT)
                    watcher.join()
                    _log.info('reaped process for %s', watcher.game)
        for k in to_delete:
            del self.game_nums[k]
        for game in games:
            if self.game_nums.get(game.matchid) is None:
                self.game_nums[game.matchid] = game.game
            if game.game > self.game_nums[game.matchid]:
                if game.live:
                    self.game_nums[game.matchid] = game.game
                    match game.league:
                        case League.LPL:
                            link = None
                            if League.LPL in [watcher.game.league for watcher in self.watchers]:
                                link = 'https://live.bilibili.com/blanc/616?liteVersion=true' 
                            else:
                                link = 'https://live.bilibili.com/blanc/6?liteVersion=true'
                            w = Bilibili(q, game, link)
                            w.start()
                            self.watchers.append(w)
                            _log.info('dispatched watcher for %s', game)

