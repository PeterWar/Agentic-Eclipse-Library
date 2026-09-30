import numpy as np, pickle, sys, json
from inversio import Inversio
sig = dict(np.load('SIG.npz')); vt = pickle.load(open('VAR_irls.pkl', 'rb'))
fr = [j for j in range(67) if sig['sig'][j].min() < 0.5]
Dedges = [0.6, 1.0, 1.5, 2.0, 3.0, 4.0]
for cfg in [dict(dphi=0.125, regD=0.05), dict(dphi=0.0625, regD=0.05), dict(dphi=0.125, regD=0.005), dict(dphi=0.25, regD=0.05)]:
    I = Inversio(sig_tab=sig, verbose=False, dphi=cfg['dphi']); I.var_tab = vt
    I.prepara(fr); I.construeix(fr); I.resol(regD=cfg['regD'])
    L = I.L; res = L['y'] - I.C.ravel()[L['p']] - I.pred_lun
    # palanca: w/Wt
    h = L['w'] / I.Wt[L['p']]
    out = []
    for a, b in zip(Dedges[:-1], Dedges[1:]):
        m = (L['D'] >= a) & (L['D'] < b) & (h < 0.9)
        out.append(np.sqrt(np.median((res[m] ** 2 / (1 - h[m])))))
    grups = {'curts inici 0-8': range(0, 9), 'mitjans 9-17': range(9, 18), 'mitjans tard 26-48': range(26, 49), 'curts tard 50-66': range(50, 67)}
    gtxt = []
    for g, rr in grups.items():
        m = np.isin(L['j'], list(rr)) & (L['D'] < 2) & (h < 0.9); gtxt.append(f'{g}: {np.sqrt(np.median(res[m]**2/(1-h[m]))):.3f}')
    print(cfg, 'σ mediana del residu per D:', ' '.join(f'{v:.3f}' for v in out), '|', ' | '.join(gtxt))
