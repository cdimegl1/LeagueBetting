import api
import models.mmr
import constants
from datetime import datetime, timezone
from fuzzywuzzy import process, fuzz
import constants

def from_api(code, league_name, blue_odds, red_odds):
    blue_odds = 1 / blue_odds
    red_odds = 1 / red_odds
    api_games = api.get_schedule()
    g: api.Game
    for game in api_games:
        if game.blue_code.lower() == code.lower() or game.red_code.lower() == code.lower():
            g = game
            break
    assert g is not None
    league = next(league for league in constants.ALL_LEAGUES if league.string == league_name)
    print(league)
    blue_players, red_players = g.get_players()
    blue_champs, red_champs = g.get_champs()
    players = blue_players + red_players
    champs = blue_champs + red_champs
    model = models.mmr.PlayersAndChampions()
    blue_win = run_model(model, players, champs, league)
    vec = model.vec(players[:5], players[-5:], champs[:5], champs[-5:], league)
    on = select_side(constants.coefs[datetime.utcnow().date()][league], blue_odds, red_odds, blue_win, vec)
    if on == 0:
        print('no bet')
    if on == 1:
        print(g.blue_team)
    if on == 2:
        print(g.red_team)
    log_bet(g.blue_team, g.red_team, g.number, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, 1 - blue_win, league, on)

def china(blue_team, red_team, num, players, champs, blue_odds, red_odds):
    blue_odds = 1 / blue_odds
    red_odds = 1 / red_odds
    league = constants.League.LPL
    names = []
    final_score = 0
    team1Name = blue_team
    team2Name = red_team
    if any([x in team1Name for x in ['Team', 'The']]):
        team1Name = team1Name.split()[1]
    else:
        team1Name = team1Name.split()[0]
    if any([x in team2Name for x in ['Team', 'The']]):
        team2Name = team2Name.split()[1]
    else:
        team2Name = team2Name.split()[0]
    team1 = constants.rosters['Team'].apply(lambda x: x.lower()).str.split()
    mask = team1.apply(lambda x: team1Name.lower() in x)
    team1 = ','.join(constants.rosters[mask]['ID'].ravel().flatten()).split(',')
    team1Names = ','.join(constants.rosters[mask]['Name'].ravel().flatten()).split(',')
    team2 = constants.rosters['Team'].apply(lambda x: x.lower()).str.split()
    mask = team2.apply(lambda x: team2Name.lower() in x)
    team2 = ','.join(constants.rosters[mask]['ID'].ravel().flatten()).split(',')
    team2Names = ','.join(constants.rosters[mask]['Name'].ravel().flatten()).split(',')
    blue_names = [process.extractOne(x, team1)[0] for x in players[:5]]
    red_names = [process.extractOne(x, team2)[0] for x in players[-5:]]
    blue_players = [process.extractOne(x, team1Names, scorer=fuzz.partial_ratio)[0] for x in blue_names]
    red_players = [process.extractOne(x, team2Names, scorer=fuzz.partial_ratio)[0] for x in red_names]
    players = blue_players + red_players
    champs = [process.extractOne(x, constants.champions)[0] for x in champs]
    model = models.mmr.PlayersAndChampions()
    blue_win = run_model(model, players, champs, league)
    vec = model.vec(players[:5], players[-5:], champs[:5], champs[-5:], league)
    on = select_side(constants.coefs[datetime.utcnow().date()][league], blue_odds, red_odds, blue_win, vec)
    if on == 0:
        print('no bet')
    if on == 1:
        print(blue_team)
    if on == 2:
        print(red_team)
    log_bet(blue_team, red_team, num, players[:5], players[-5:], champs[:5], champs[-5:], blue_odds, red_odds, blue_win, 1 - blue_win, league, on)

def from_team(blue_team, red_team, league):
    pass

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
        blue_win > blue_odds + x[2] and
        blue_win > x[3]):
        return 1
    if (red_odds > x[4] and
        red_odds < x[5] and
        1 - blue_win > red_odds + x[6] and
        1 - blue_win > x[7]):
        return 2
    return 0

