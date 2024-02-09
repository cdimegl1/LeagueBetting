import mwclient
import pandas
import time
import constants
import json

def get_rosters():
    site = mwclient.Site('lol.fandom.com', path='/')
    response = site.api('cargoquery',
            limit='max',
            offset=0,
            tables='Teams, Players',
            fields='Teams.OverviewPage=Team, Teams.Short, Teams.Region, GROUP_CONCAT(Players.ID)=ID, GROUP_CONCAT(Players.OverviewPage)=Name',
            where='NOT Teams.IsDisbanded AND Teams.Name NOT LIKE "%College%"',
            join_on='Teams.OverviewPage=Players.Team',
            group_by='Players.Team',
            format='csv'
            )
    parsed = json.dumps(response)
    decoded = json.loads(parsed)
    result = [entry for entry in [e['title'] for e in decoded['cargoquery']]]
    response = site.api('cargoquery',
            limit='max',
            offset=500,
            tables='Teams, Players',
            fields='Teams.OverviewPage=Team, Teams.Short, Teams.Region, GROUP_CONCAT(Players.ID)=ID, GROUP_CONCAT(Players.OverviewPage)=Name',
            where='NOT Teams.IsDisbanded AND Teams.Name NOT LIKE "%College%"',
            join_on='Teams.OverviewPage=Players.Team',
            group_by='Players.Team',
            format='csv'
            )
    parsed = json.dumps(response)
    decoded = json.loads(parsed)
    result2 = [entry for entry in [e['title'] for e in decoded['cargoquery']]]
    result = result + result2
    result = pandas.DataFrame(result).set_index('Team')
    result['Short'] = result['Short'].str.replace('.', '')
    return result

def get_tournaments(leagues: list[constants.League]=constants.ALL_LEAGUES, year: int=2022, exclude_playoffs: bool=False):
    site = mwclient.Site('lol.fandom.com', path='/')
    df = pandas.DataFrame()
    for league in leagues:
        short_name = league.string
        where_str = "AND Tournaments.Name NOT LIKE '%%playoffs%%'" if exclude_playoffs else ''
        response = site.api('cargoquery',
                limit='max',
                tables='Tournaments, Leagues',
                fields='Tournaments.Name=Name, Leagues.League_Short=Short, Tournaments.DateStart=Date',
                where=f"Leagues.League_Short='{short_name}' AND YEAR(Tournaments.DateStart) > {year} AND MONTH(Tournaments.DateStart) > 0 AND Tournaments.Name NOT LIKE '%%placements%%' AND Tournaments.Name NOT LIKE '%%lock in%%' AND Tournaments.Name NOT LIKE '%%championship%%' AND Tournaments.Name NOT LIKE '%%qualifier%%' AND Tournaments.Name NOT LIKE '%%promotion%%' AND Tournaments.Name NOT LIKE '%%final%%'" + where_str,
                join_on='Tournaments.League=Leagues.League',
                format='csv'
                )
        response = response['cargoquery']
        league = pandas.DataFrame([x['title'] for x in response])
        df = pandas.concat([df, league])
        print(f'got {len(league):d} tournaments from {short_name}')
        time.sleep(1.5)
    return df

# TODO only get new matches
def get_matches(tournaments=None):
    if tournaments is None:
        tournaments = pandas.read_csv('../data/tournaments.csv')
    df = pandas.DataFrame()
    site = mwclient.Site('lol.fandom.com', path='/')
    for _, tourn in tournaments.iterrows():
        name = tourn['Name']
        response = site.api('cargoquery',
                limit='max',
                tables='ScoreboardGames',
                fields='ScoreboardGames.Winner, ScoreboardGames.Team1Players, ScoreboardGames.Team1Picks, ScoreboardGames.Team2Players, ScoreboardGames.Team2Picks, ScoreboardGames.Team1, ScoreboardGames.Team2, ScoreboardGames.DateTime_UTC, ScoreboardGames.N_GameInMatch',
                where=f'ScoreboardGames.Tournament="{name}"',
                format='json'
                )
        curr = [x['title'] for x in response['cargoquery']]
        curr = pandas.DataFrame(curr)
        curr['Short'] = tourn['Short']
        curr['Tournament'] = name
        df = pandas.concat([df, curr])
        print(f"scraped {len(curr):d} matches from {tourn['Name']}")
        time.sleep(1.5)
    return df

