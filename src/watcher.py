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
import shutil
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
        _log.info('%s %s %s %s', blue_team, red_team, players, champs)
        assert blue_team != red_team, 'get_names failed with equal teams'
        self.q.put((self.game, players, champs, blue_team, red_team))

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

def test_watch():
    options = selenium.webdriver.chrome.options.Options()
    uid = uuid.uuid1()
    shutil.copytree('/home/cdimegl1/Betting/chrome-data/data/data4', f'/home/cdimegl1/Betting/chrome-data/data/{uid}')
    options.add_argument(f'--user-data-dir=/home/cdimegl1/Betting/chrome-data/data/{uid}')
    options.add_argument("--profile-directory=Profile 1")
    options.add_argument("--enable-features=UseOzonePlatform")
    options.add_argument("--ozone-platform=wayland")
    options.binary_location = '/usr/bin/google-chrome'
    options.add_experimental_option("excludeSwitches", ['enable-logging', 'enable-automation'])
    options.add_argument('--width=1920')
    options.add_argument('--height=1080')
    options.add_argument('--mute-audio')
    options.add_argument('--headless=new')
    options.add_argument('force-device-scale-factor=0.5')
    driver = webdriver.Chrome(chrome_options=options, executable_path='/usr/bin/chromedriver')
    driver.set_window_size(1920, 1080)
    driver.get('https://live.bilibili.com/blanc/6?liteVersion=true')
    player = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'web-player-inject-wrap')))       
    driver.execute_script('arguments[0].scrollIntoView();', player)
    ActionChains(driver).move_to_element(player).perform()
    time.sleep(1)
    quality = driver.find_element(By.CSS_SELECTOR, '.quality-wrap.svelte-s2ukfj')
    ActionChains(driver).move_to_element(quality).perform()
    time.sleep(1)
    qualities = driver.find_elements(By.CSS_SELECTOR, '.list-it.svelte-s2ukfj')
    for quality in qualities:
        if quality.text == '原画':
            driver.execute_script("arguments[0].click();", quality)
            # quality.click()
            break
    time.sleep(3)
    # button = driver.find_element(By.CSS_SELECTOR, '.right-area.svelte-koac9q').find_elements(By.CSS_SELECTOR, '.tip-wrap.svelte-11g6lf7')[0]
    ActionChains(driver).move_to_element(player).perform()
    driver.save_screenshot('test.png')
    fullscreen = driver.find_element(By.CSS_SELECTOR, '.right-area.svelte-4rgwwa').find_element(By.CSS_SELECTOR, '.tip-wrap.svelte-11g6lf7')
    fullscreen.click()
    # driver.execute_script("arguments[0].click();", fullscreen)
    # ActionChains(driver).move_by_offset(0, -200).perform()
    time.sleep(5)
    driver.save_screenshot('test.png')
    driver.quit()
    shutil.rmtree(f'/home/cdimegl1/Betting/chrome-data/data/{uid}')


class Bilibili(Watcher):
    def __init__(self, q, game, link):
        super().__init__(q, game)
        self.link = link

    def watch(self):
        while True:
            uid = uuid.uuid1()
            try:
                shutil.copytree('/home/cdimegl1/Betting/chrome-data/data/data4', f'/home/cdimegl1/Betting/chrome-data/data/{uid}')
                # data_dir = next(chrome_data_gen)
                options = selenium.webdriver.chrome.options.Options()
                options.add_argument(f'--user-data-dir=/home/cdimegl1/Betting/chrome-data/data/{uid}')
                options.add_argument("--profile-directory=Profile 1")
                options.add_argument("--enable-features=UseOzonePlatform")
                options.add_argument("--ozone-platform=wayland")
                options.binary_location = '/usr/bin/google-chrome'
                options.add_experimental_option("excludeSwitches", ['enable-logging', 'enable-automation'])
                options.add_argument('--width=1920')
                options.add_argument('--height=1080')
                options.add_argument('--mute-audio')
                options.add_argument('--headless=new')
                options.add_argument('force-device-scale-factor=0.5')
                self.driver = webdriver.Chrome(chrome_options=options, executable_path='/usr/bin/chromedriver')
                self.driver.set_window_size(1920, 1080)
                self.driver.get(self.link)
                player = WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'web-player-inject-wrap')))       
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
                time.sleep(20)
                ss_uid = uuid.uuid1()
                screenshotName = path.join('../screenshots', str(ss_uid)+'.png')
                self.driver.save_screenshot(screenshotName)
                im = cv2.imread(screenshotName)
                while not banner_present(im, self.game.league):
                    time.sleep(10)
                    self.driver.save_screenshot(screenshotName)
                    im_new = cv2.imread(screenshotName)
                    if mse(im, im_new) < 1:
                        raise Exception('consecutive screenshots are too similiar')
                    im = im_new
                _log.info('detected banner for %s', self.game)
                self.driver.quit()
                left, right = crop_image(im)
                blue_champs = get_champs(left)
                red_champs = get_champs(right)
                blue_names, blue_team = get_names(left, self.game.t1, self.game.t2, self.game.league)
                red_names, red_team = get_names(right, self.game.t1, self.game.t2, self.game.league)
                shutil.rmtree(f'/home/cdimegl1/Betting/chrome-data/data/{uid}')
                return blue_names + red_names, blue_champs + red_champs, blue_team, red_team
            except Exception:
                shutil.rmtree(f'/home/cdimegl1/Betting/chrome-data/data/{uid}')
                _log.warn('bilibili watcher failed for %s', self.game, exc_info=True)
                time.sleep(5)

def bilibili_link_gen():
    while True:
        yield 'https://live.bilibili.com/blanc/6?liteVersion=true' 
        yield 'https://live.bilibili.com/blanc/616?liteVersion=true' 

class Dispatcher():
    def __init__(self, game_nums={}) -> None:
        self.watchers = []
        self.game_nums = game_nums
        self.bilibili_link_gen = bilibili_link_gen()

    def update(self, q, games):
        to_delete = []
        for i in self.game_nums.keys():
            if i not in [game.matchid for game in games]:
                to_delete.append(i)
                finished = [watcher.game.matchid for watcher in self.watchers if watcher.game.matchid == i]
                finished_watchers = [watcher for watcher in self.watchers if watcher.game.matchid == i]
                self.watchers = [watcher for watcher in self.watchers if watcher.game.matchid not in finished]
                for watcher in finished_watchers:
                    if watcher.is_alive():
                            os.kill(watcher.pid, signal.SIGINT)
                    watcher.join()
                    _log.info('reaped process for %s', watcher.game)
        for i in to_delete:
            _log.info('deleting game_nums for %d', i)
            del self.game_nums[i]
        for game in games:
            if self.game_nums.get(game.matchid) is None:
                self.game_nums[game.matchid] = game.game
            if game.game > self.game_nums[game.matchid]:
                if game.live:
                    self.game_nums[game.matchid] = game.game
                    link = None
                    match game.league:
                        case League.LPL:
                            if League.LPL in [watcher.game.league for watcher in self.watchers]:
                                try:
                                    link = next(watcher.link for watcher in self.watchers if watcher.game.matchid == game.matchid)
                                except Exception:
                                    _log.info('getting next stream link for %s', game)
                                    link = next(self.bilibili_link_gen)
                            else:
                                link = next(self.bilibili_link_gen)
                        # case League.LDL:
                        #     pass
                    if link:
                        w = Bilibili(q, game, link)
                        w.start()
                        self.watchers.append(w)
                        _log.info('dispatched watcher for %s on %s', game, link)

