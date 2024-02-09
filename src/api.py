import requests
import json
import datetime
from constants import rosters, champions, API_KEY
from fuzzywuzzy import fuzz, process

API_URL = 'https://esports-api.lolesports.com/persisted/gw'
LIVE_API_URL = 'https://feed.lolesports.com/livestats/v1'

def get_event_details(matchId):
    response = json.loads(requests.get(API_URL+'/getEventDetails', params={'hl': 'en-US', 'id': matchId}, headers={'x-api-key': API_KEY}).text)
    #print(json.dumps(response, indent=4))
    return response

def get_schedule():
    results = []
    response = json.loads(requests.get(API_URL+'/getSchedule', params={'hl': 'en-US'}, headers={'x-api-key': API_KEY}).text)
    events = response['data']['schedule']['events']
    # print(json.dumps(response, indent=4))
    for event in events:
        try:
            if event['state'] == 'inProgress' or (event['state'] != 'completed' and datetime.datetime.fromisoformat(event['startTime'].replace('Z','')) < datetime.datetime.utcnow()):
                matchId = event['match']['id']
                match = get_event_details(int(matchId))
                t1, t2 = match['data']['event']['match']['teams']
                for game in match['data']['event']['match']['games']:
                    if game['state'] in ('unstarted', 'inProgress'):
                        window = get_game_window(game['id'])
                        g = Game(t1, t2, window, game['id'])
                        results.append(g)
                        print(g.blue_team, g.red_team, g.blue_players, g.red_players, g.blue_champs, g.red_champs)
        except Exception as e:
            pass
            #print(e)
    return results


def get_game_window(gameId):
    response = json.loads(requests.get(LIVE_API_URL+'/window/'+gameId, headers={'x-api-key': API_KEY}).text)
    return response

class Game:
    def __init__(self, t1, t2, window, gameId):
        self.gameId = gameId
        blue_team_MD = window['gameMetadata']['blueTeamMetadata']
        red_team_MD = window['gameMetadata']['redTeamMetadata']
        if t1['id'] == blue_team_MD['esportsTeamId']:
            self.blue_team = t1['name']
            self.blue_code = t1['code']
        elif t2['id'] == blue_team_MD['esportsTeamId']:
            self.blue_team = t2['name']
            self.blue_code = t2['code']
        if t1['id'] == red_team_MD['esportsTeamId']:
            self.red_team = t1['name']
            self.red_code = t1['code']
        elif t2['id'] == red_team_MD['esportsTeamId']:
            self.red_team = t2['name']
            self.red_code = t2['code']
        self.blue_players = []
        self.red_players = []
        self.blue_champs = []
        self.red_champs = []
        for p in blue_team_MD['participantMetadata']:
            self.blue_players.append(p['summonerName'].split()[-1])
            champ = p['championId']
            if champ == 'MonkeyKing':
                self.blue_champs.append('Wukong')
            else:
                self.blue_champs.append(champ)
        for p in red_team_MD['participantMetadata']:
            self.red_players.append(p['summonerName'].split()[-1])
            champ = p['championId']
            if champ == 'MonkeyKing':
                self.red_champs.append('Wukong')
            else:
                self.red_champs.append(champ)

    def get_players(self):
        bt = self.blue_code.lower()
        rt = self.red_code.lower()

        team_names = rosters['Short']

        candidates = []
        for name in team_names:
            candidates.append((fuzz.partial_ratio(bt, name.lower()), name))
        candidates.sort(key=lambda x: x[0])
        mask = team_names.apply(lambda x: x in map(lambda y: y[1], candidates[-5:]))
        blue_names = rosters[mask]['Name'].ravel().flatten()
        blue_names = ','.join([x for x in blue_names if isinstance(x, str)]).split(',')
        blue_res = []
        for i in range(5):
            blue_res.append(process.extractOne(self.blue_players[i], blue_names)[0])

        candidates = []
        for name in team_names:
            candidates.append((fuzz.partial_ratio(rt, name.lower()), name))
        candidates.sort(key=lambda x: x[0])
        mask = team_names.apply(lambda x: x in map(lambda y: y[1], candidates[-5:]))
        red_names = rosters[mask]['Name'].ravel().flatten()
        red_names = ','.join([x for x in red_names if isinstance(x, str)]).split(',')
        red_res = []
        for i in range(5):
            red_res.append(process.extractOne(self.red_players[i], red_names)[0])
        return blue_res, red_res

    def get_champs(self):
        champs = [process.extractOne(x, champions)[0] for x in self.blue_champs + self.red_champs]
        return champs[:5], champs[-5:]
