import pandas
from enum import Enum
from dotenv import load_dotenv
from os import getenv
import sqlite3
import pickle
from os import makedirs
from os.path import exists

unit_size = .01

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
    # LDL = ('LDL', '', 'https://stat1-mlycdn.bmyy520.com/lol/Content/images/uploaded/league/0e3e4faf-67b4-4da1-acd4-9a0479928746.png')
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
str_to_league = { league.string: league for league in ALL_LEAGUES }
str_to_league['PRIME LEAGUE'] = League.PRM
str_to_league['CBLOL ACADEMY'] = League.CBLOLA
str_to_league['HITPOINT MASTERS'] = League.HM
str_to_league['ULTRALIGA'] = League.UL
str_to_league['ELITE SERIES'] = League.ESLOL
str_to_league['LVP SL'] = League.SL
str_to_league['LAL'] = League.AL
PREDICTABLE_LEAGUES = ALL_LEAGUES.copy()
# PREDICTABLE_LEAGUES.remove(League.CBLOLA)
# PREDICTABLE_LEAGUES.remove(League.LCKCL)
# PREDICTABLE_LEAGUES.remove(League.LCK)
# PREDICTABLE_LEAGUES.remove(League.HM)
# PREDICTABLE_LEAGUES.remove(League.GLL)
# PREDICTABLE_LEAGUES.remove(League.UL)
# PREDICTABLE_LEAGUES.remove(League.VCS)
# PREDICTABLE_LEAGUES.remove(League.PCS)
# PREDICTABLE_LEAGUES.remove(League.LCO)

# coefs = dict.fromkeys(ALL_LEAGUES)
# coefs[League.AL] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
# coefs[League.CBLOL] = [ 3.701e-01, 2.133e-01, 4.283e-02, 1.750e-02, 5.154e-01, 4.163e-01, 3.581e-01, -2.780e-01, 1.956e-01, 3.506e-01 ]
# coefs[League.CBLOLA] = [ 6.629e-01, 2.824e-03, -2.572e-01, 3.543e-01, 2.066e-01, 3.151e-01, 1.343e-01, -2.788e-01, 2.062e-01, 5.459e-01 ]
# coefs[League.EBL] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
# coefs[League.ESLOL] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
# coefs[League.GLL] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
# coefs[League.HM] = [ 3.110e-01, 3.357e-01, -1.604e-01, 1.864e-02, 2.632e-01, 5.690e-01, 4.341e-01, 9.130e-02, 2.237e-01, 5.807e-01 ]
# coefs[League.LCK] = [ 3.462e-01, 4.639e-01, -2.772e-01, 1.917e-01, 6.188e-02, 6.379e-01, 9.387e-01, -2.734e-01, 1.558e-01, 1.978e-01 ]
# coefs[League.LCKCL] = [ 3.714e-01, 2.174e-01, -2.616e-01, 1.625e-01, 5.905e-01, 3.113e-01, 2.860e-01, -2.529e-01, 9.541e-02, 5.038e-02 ]
# coefs[League.LCO] = [ 5.208e-01, 3.961e-01, -2.964e-01, 1.101e-01, 3.667e-01, 4.671e-01, 3.553e-01, -2.972e-01, 3.770e-02, 1.091e-01 ]
# coefs[League.LCS] = [ 5.478e-01, 3.413e-02, 4.909e-03, 2.548e-01, 2.548e-01, 9.022e-01, 7.081e-01, 7.081e-01, 7.956e-01, 7.956e-01 ]
# coefs[League.LEC] = [ 6.602e-01, 2.361e-01, 6.930e-03, 2.361e-01, 3.820e-01, 7.327e-01, 9.999e-01, 9.999e-01, 9.999e-01, 9.999e-01 ]
# coefs[League.LFL] = [ 4.467e-01, 4.012e-02, -4.612e-02, 2.774e-01, 2.634e-01, 3.480e-01, 1.984e-01, -1.714e-01, 1.085e-01, 5.294e-01 ]
# coefs[League.LIT] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
# coefs[League.LJL] = [ 3.690e-01, 3.900e-01, -2.257e-01, 1.009e-01, 3.623e-01, 5.462e-01, 2.199e-01, -2.961e-01, 3.817e-01, 1.091e-01 ]
# coefs[League.LLA] = [ 3.293e-01, 3.444e-01, -8.382e-02, 6.492e-02, 3.099e-01, 3.121e-01, 4.205e-01, -2.569e-01, 1.899e-01, 1.216e-01 ]
# coefs[League.LPL] = [ 3.015e-01, 7.390e-02, -2.624e-01, 7.547e-02, 4.037e-01, 3.394e-01, 3.566e-01, -1.938e-01, 1.680e-01, 3.871e-02 ]
# coefs[League.LPLOL] = [ 7.788e-01, 9.995e-01, -6.937e-01, -8.491e-01, 5.081e-01, 1.653e-01, 3.175e-01, 9.240e-01, -7.710e-01, -7.620e-01, 2.625e-01, 6.810e-02 ]
# coefs[League.NACL] = [ 3.457e-01, 8.831e-01, -7.235e-01, 6.437e-02, 1.494e-01, 6.240e-01, 5.099e-01, 8.132e-01, -2.584e-01, -8.991e-01, 2.751e-01, 5.249e-02 ]
# coefs[League.NLC] = [ 7.547e-01, 1.640e-01, -1.648e-01, 2.096e-01, 2.813e-01, 5.394e-01, 3.598e-01, -2.217e-01, 6.077e-02, 1.440e-01 ]
# coefs[League.PCS] = [ 3.562e-01, 1.632e-01, 2.968e-02, 2.590e-01, 6.275e-01, 3.107e-01, 4.462e-01, -2.175e-01, 4.990e-01, 3.654e-01 ]
# coefs[League.PRM] = [ 4.256e-01, 2.676e-01, -2.110e-01, 1.933e-01, 4.969e-01, 3.011e-01, 1.613e-01, -1.333e-01, 3.756e-02, 5.735e-02 ]
# coefs[League.SL] = [ 4.494e-01, 5.846e-02, 1.236e-01, 2.308e-01, 6.398e-01, 3.149e-01, 1.955e-01, -2.831e-01, 4.210e-02, 1.488e-02 ]
# coefs[League.TCL] = [ 3.141e-01, 3.370e-01, -2.318e-01, 1.019e-01, 4.470e-01, 3.283e-01, 2.109e-01, -2.960e-01, 3.247e-01, 2.644e-01 ]
# coefs[League.UL] = [ 3.478e-01, 6.322e-02, 5.137e-03, 3.462e-02, 3.605e-01, 4.991e-01, 6.568e-02, -2.718e-01, 4.722e-01, 3.726e-01 ]
# coefs[League.VCS] = [ 3.242e-01, 2.332e-01, -8.268e-02, 4.434e-02, 5.714e-01, 3.267e-01, 3.955e-01, -1.795e-01, 8.123e-02, 6.609e-01 ]
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

def load_coefs():
    try:
        return pickle.load(open('../models/Selector/model.skl', 'rb'))
    except Exception:
        print('failed to load coefs')
        if not exists(f'../models/Selector'):
            makedirs(f'../models/Selector')
        pickle.dump({}, open('../models/Selector/model.skl', 'wb'))
        return {}

coefs = load_coefs()

load_dotenv()
TESSERACT_BINARY = getenv('TESSERACT_BINARY')
ESPORTSBETIO_USERNAME = getenv('ESPORTSBETIO_USERNAME')
ESPORTSBETIO_PASSWORD = getenv('ESPORTSBETIO_PASSWORD')
BETUS_ID = getenv('BETUS_ID')
BETUS_PASSWORD = getenv('BETUS_PASSWORD')
CHROME_DATA_DIR = getenv('CHROME_DATA_DIR')
API_KEY = getenv('API_KEY')
