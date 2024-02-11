import pandas
from enum import Enum
from dotenv import load_dotenv
from os import getenv
import sqlite3

unit_size = .09

db = sqlite3.connect('../bets.db')
db.row_factory = sqlite3.Row

class League(Enum):

    AL = ('AL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/7df73cc0-339e-474c-8c3a-6078e015f116.png')
    CBLOL = ('CBLOL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/3a3d5cab-d715-489b-994b-e9b8d0f703ad.png')
    CBLOLA = ('CBLOL.A', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/e5b68d90-f2e8-4891-af6d-7b3da919561a.png')
    EBL = ('EBL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/0d2261f3-f67e-472c-9678-799186e9f7d5.png')
    ESLOL = ('ESLOL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/fc40d17b-5dc5-4847-8ca4-a160d9f3ece0.png')
    GLL = ('GLL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/93c754b2-f5bb-407f-972e-4edfc79c2f74.png')
    HM = ('HM', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/2633c8af-163f-415f-8c11-6fb0d4dae773.png')
    LCK = ('LCK', 'https://twitch.tv/lck', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/212f5f4e-edb6-41da-9013-5ca57391169a.png')
    LCKCL = ('LCK CL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/64293049-896f-4002-acac-1c4022de7c0f.png')
    LCO = ('LCO', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/371acaad-c39d-4752-ab4b-a31d2dd3ab87.png')
    LCS = ('LCS', 'https://twitch.tv/lcs', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/559042c7-2a5a-460a-87b1-5f022ab668d9.png')
    LEC = ('LEC', 'https://twitch.tv/lec', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/088a66fa-9646-4bba-8d34-189e68a31d4e.png')
    LFL = ('LFL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/bad11f8d-01bb-4bf8-be9a-8ca93e8339ad.png')
    LIT = ('LIT', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/9112dab3-7424-4c22-9408-f442e40e3536.png')
    LJL = ('LJL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/7fefa1c5-fc4f-447d-b0dc-e2f085c719a7.png')
    LLA = ('LLA', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/6e624978-3927-4953-a5a2-228f55a77eb3.png')
    LPL = ('LPL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/8366ad4e-8004-42bd-bdce-707848bb4800.png')
    LPLOL = ('LPLOL' ,'', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/6527688d-dd37-4ae6-b388-205628f716f0.png')
    NACL = ('NACL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/18facc86-1be1-4362-8046-684d0a76c4d2.png')
    NLC = ('NLC', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/2f78142a-5d0a-4c67-b8bf-1e03a050dcf8.png')
    PCL = ('PCL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/881c65c8-55cc-4ce7-8c06-e33ce17ca20f.png')
    PCS = ('PCS', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/379282a2-0f40-4201-a821-3165b95b971d.png')
    PRM = ('PRM', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/0143e854-143d-4524-a031-07274b419105.png')
    SL = ('SL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/11a1075b-b6ed-44c6-a059-c0d572f7e6a7.png')
    TCL = ('TCL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/84dd2734-7fb8-43c1-88e9-738fa4126e0e.png')
    UL = ('UL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/eb5d415c-0982-48bb-ba84-25b5e77ec5fa.png')
    VCS = ('VCS', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/9b8b726f-08a6-40bf-bff4-3055c45ab4c0.png')

    def __init__(self, name, link, src) -> None:
        self.string = name
        self.link = link
        self.src = src

ALL_LEAGUES = list(League.__members__.values())
PREDICTABLE_LEAGUES = ALL_LEAGUES.copy()
# PREDICTABLE_LEAGUES.remove(League.CBLOL)
PREDICTABLE_LEAGUES.remove(League.CBLOLA)
PREDICTABLE_LEAGUES.remove(League.SL)
PREDICTABLE_LEAGUES.remove(League.TCL)
PREDICTABLE_LEAGUES.remove(League.NACL)
PREDICTABLE_LEAGUES.remove(League.LCS)
PREDICTABLE_LEAGUES.remove(League.NLC)
PREDICTABLE_LEAGUES.remove(League.LPLOL)
PREDICTABLE_LEAGUES.remove(League.LIT)
PREDICTABLE_LEAGUES.remove(League.LEC)
PREDICTABLE_LEAGUES.remove(League.LCKCL)
PREDICTABLE_LEAGUES.remove(League.LCO)
# PREDICTABLE_LEAGUES.remove(League.LFL)

rosters = pandas.read_csv('../data/rosters.csv')

champions = [
    'Aatrox',
    'Ahri',
    'Akali',
    'Akshan',
    'Alistar',
    'Amumu',
    'Anivia',
    'Annie',
    'Aphelios',
    'Ashe',
    'Aurelion Sol',
    'Azir',
    'Bard',
    "Bel'Veth",
    'Blitzcrank',
    'Brand',
    'Braum',
    'Briar',
    'Caitlyn',
    'Camille',
    'Cassiopeia',
    "Cho'Gath",
    'Corki',
    'Darius',
    'Diana',
    'Dr. Mundo',
    'Draven',
    'Ekko',
    'Elise',
    'Evelynn',
    'Ezreal',
    'Fiddlesticks',
    'Fiora',
    'Fizz',
    'Galio',
    'Gangplank',
    'Garen',
    'Gnar',
    'Gragas',
    'Graves',
    'Gwen',
    'Hecarim',
    'Heimerdinger',
    'Hwei',
    'Illaoi',
    'Irelia',
    'Ivern',
    'Janna',
    'Jarvan IV',
    'Jax',
    'Jayce',
    'Jhin',
    'Jinx',
    "K'Sante",
    "Kai'Sa",
    'Kalista',
    'Karma',
    'Karthus',
    'Kassadin',
    'Katarina',
    'Kayle',
    'Kayn',
    'Kennen',
    "Kha'Zix",
    'Kindred',
    'Kled',
    "Kog'Maw",
    'LeBlanc',
    'Lee Sin',
    'Leona',
    'Lillia',
    'Lissandra',
    'Lucian',
    'Lulu',
    'Lux',
    'Malphite',
    'Malzahar',
    'Maokai',
    'Master Yi',
    'Milio',
    'Miss Fortune',
    'Mordekaiser',
    'Morgana',
    'Naafiri',
    'Nami',
    'Nasus',
    'Nautilus',
    'Neeko',
    'Nidalee',
    'Nilah',
    'Nocturne',
    'Nunu',
    'Olaf',
    'Orianna',
    'Ornn',
    'Pantheon',
    'Poppy',
    'Pyke',
    'Qiyana',
    'Quinn',
    'Rakan',
    'Rammus',
    "Rek'Sai",
    'Rell',
    'Renata Glasc',
    'Renekton',
    'Rengar',
    'Riven',
    'Rumble',
    'Ryze',
    'Samira',
    'Sejuani',
    'Senna',
    'Seraphine',
    'Sett',
    'Shaco',
    'Shen',
    'Shyvana',
    'Singed',
    'Sion',
    'Sivir',
    'Skarner',
    'Smolder',
    'Sona',
    'Soraka',
    'Swain',
    'Sylas',
    'Syndra',
    'Tahm Kench',
    'Taliyah',
    'Talon',
    'Taric',
    'Teemo',
    'Thresh',
    'Tristana',
    'Trundle',
    'Tryndamere',
    'Twisted Fate',
    'Twitch',
    'Udyr',
    'Urgot',
    'Varus',
    'Vayne',
    'Veigar',
    "Vel'Koz",
    'Vex',
    'Vi',
    'Viego',
    'Viktor',
    'Vladimir',
    'Volibear',
    'Warwick',
    'Wukong',
    'Xayah',
    'Xerath',
    'Xin Zhao',
    'Yasuo',
    'Yone',
    'Yorick',
    'Yuumi',
    'Zac',
    'Zed',
    'Zeri',
    'Ziggs',
    'Zilean',
    'Zoe',
    'Zyra'
]

load_dotenv()
TESSERACT_BINARY = getenv('TESSERACT_BINARY')
ESPORTSBETIO_USERNAME = getenv('ESPORTSBETIO_USERNAME')
ESPORTSBETIO_PASSWORD = getenv('ESPORTSBETIO_PASSWORD')
CHROME_DATA_DIR = getenv('CHROME_DATA_DIR')
API_KEY = getenv('API_KEY')
