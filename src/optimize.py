import scipy.optimize
from constants import ALL_LEAGUES, load_coefs
import sim
from datetime import datetime, timedelta
import pickle
import time
from multiprocessing import Process, Queue

class Optimizer:
    def __init__(self) -> None:
        self.x0 = []
        self.args = []
        self.names = []
        self.bounds = []

    def add_var(self, name, bound, x0):
        self.x0.append(x0)
        self.names.append(name)
        self.bounds.append(bound)

    def add_arg(self, arg):
        self.args.append(arg)

    def lower(self):
        return [x[0] for x in self.bounds]

    def upper(self):
        return [x[1] for x in self.bounds]

    def optimize(self):
        # solver_opts = { 'disp': 101, 'eps': .10, 'maxfun': 5, 'maxiter': 5, 'maxls': 5 }
        # solver_opts = { 'disp': True, 'return_all': True, 'maxfev': 20 }
        solver_opts = { 'disp': True }
        # optimize_args = { 'method': 'TNC', 'options': solver_opts }
        optimize_args = { 'method': 'trust-constr', 'options': solver_opts }
        # return scipy.optimize.minimize(fun=scipy_sim_days, x0=self.x0, method='Powell', args=tuple(self.args), bounds=self.bounds, options=solver_opts)
        sp = sim.SciPy()
        # return scipy.optimize.basinhopping(func=sp.scipy_sim_days, x0=self.x0, minimizer_kwargs=optimize_args, disp=True, niter=500)
        # return scipy.optimize.direct(func=scipy_sim_days, bounds=self.bounds, args=tuple(self.args), locally_biased=True, f_min=-1.9)
        return scipy.optimize.dual_annealing(func=sp.scipy_sim_days, bounds=self.bounds, args=tuple(self.args), x0=self.x0, no_local_search=False, maxiter=1000, minimizer_kwargs=optimize_args, callback=lambda x, f, ctx: print(f'{x}\n{f}'))
        # return scipy.optimize.dual_annealing(func=sp.scipy_sim_days, bounds=self.bounds, args=tuple(self.args), x0=self.x0, no_local_search=True, maxiter=2000)

def accept_test(f_new, x_new, f_old, x_old):
    if f_new < 0.0:
        return 'force accept'
    if f_new >= 0.0:
        return False
    if f_old >= 0.0:
        return 'force accept'

def optimize(leagues, start=datetime(2024, 2, 7), days=(datetime.now() - datetime(2024, 2, 7)).days, q=None):
    opt = Optimizer()
    opt.add_arg(start)
    opt.add_arg(days)
    opt.add_arg(leagues)
    # opt.add_var('blue_win', (0.3, 1.0), 0.3)
    # opt.add_var('blue_odds_l', (0.0, 1.0), 0.0)
    # opt.add_var('blue_edge', (-0.3, 1.0), 0.0)
    # opt.add_var('blue_players_l', (0.0, 1.0), 0.0)
    # opt.add_var('blue_champs_l', (0.0, 1.0), 0.0)
    # opt.add_var('red_win', (0.3, 1.0), 0.3)
    # opt.add_var('red_odds_l', (0.0, 1.0), 0.0)
    # opt.add_var('red_edge', (-0.3, 1.0), 0.0)
    # opt.add_var('red_players_l', (0.0, 1.0), 0.0)
    # opt.add_var('red_champs_l', (0.0, 1.0), 0.0)
    opt.add_var('blue_odds_l', (0.0, 1.0), 0.0)
    opt.add_var('blue_odds_u', (0.0, 1.0), 0.0)
    # opt.add_var('blue_edge', (-1.0, 1.0), 0.0)
    # opt.add_var('blue_players_edge', (-1.0, 1.0), 0.0)
    # opt.add_var('blue_champs_edge', (-1.0, 1.0), 0.0)
    opt.add_var('blue_players_l', (0.0, 1.0), 0.0)
    opt.add_var('blue_champs_l', (0.0, 1.0), 0.0)
    # opt.add_var('blue_win', (0.0, 1.0), 0.0)
    opt.add_var('red_odds_l', (0.0, 1.0), 0.0)
    opt.add_var('red_odds_u', (0.0, 1.0), 0.0)
    # opt.add_var('red_edge', (-1.0, 1.0), 0.0)
    # opt.add_var('red_players_edge', (-1.0, 1.0), 0.0)
    # opt.add_var('red_champs_edge', (-1.0, 1.0), 0.0)
    opt.add_var('red_players_l', (0.0, 1.0), 0.0)
    opt.add_var('red_champs_l', (0.0, 1.0), 0.0)
    # opt.add_var('red_win', (0.0, 1.0), 0.0)
    if q:
        res = opt.optimize()
        q.put((leagues[0], res))
    else:
        return opt.optimize()

def threaded_optimize(league, start, days, q):
    t = Process(target=optimize, args=(league, start, days, q))
    t.start()
    return t

def optimize_day(day=datetime.utcnow()):
    q = Queue()
    threads = []
    coefs = load_coefs()
    league_coefs = None
    if coefs.get(day.date()) is None:
        league_coefs = {}
    else:
        league_coefs = coefs[day.date()]
    # for league in ALL_LEAGUES:
    #     threads.append(threaded_optimize([league], datetime(2024, 2, 26), (day - datetime(2024, 2, 26)).days, q))
    q_len = 0
    i = 0
    vals = []
    while len(vals) != len(ALL_LEAGUES):
        while q_len <= 4 and i < len(ALL_LEAGUES):
            print(ALL_LEAGUES[i].string)
            threads.append(threaded_optimize([ALL_LEAGUES[i]], datetime(2024, 2, 6), (day - datetime(2024, 2, 6)).days, q))
            time.sleep(.5)
            q_len += 1
            i += 1
        if len(vals) == len(ALL_LEAGUES):
            break
        while val := q.get():
            q_len -= 1
            vals.append(val)
            if q_len < 4:
                break
    for league, res in vals:
        league_coefs[league] = res.x
        print(f'{league.string}: {res.fun}\t {res.x}')
    coefs[day.date()] = league_coefs
    pickle.dump(coefs, open('../models/Selector/model.skl', 'wb'))
    for t in threads:
        t.join()

def optimize_day_all(day=datetime.utcnow()):
    coefs = load_coefs()
    res = optimize(ALL_LEAGUES, datetime(2024, 2, 6), (day - datetime(2024, 2, 6)).days)
    print(f'all: {res.fun}\t {res.x}')
    if coefs.get(day.date()) is None:
        coefs[day.date()] = { 'all': res.x }
    else:
        coefs[day.date()]['all'] = res.x
    pickle.dump(coefs, open('../models/Selector/model.skl', 'wb'))

def optimize_days_all(start=datetime(2024, 2, 5), days=(datetime.utcnow() - datetime(2024, 2, 5)).days):
    for _ in range(days):
        optimize_day_all(start)
        start += timedelta(days=1)

