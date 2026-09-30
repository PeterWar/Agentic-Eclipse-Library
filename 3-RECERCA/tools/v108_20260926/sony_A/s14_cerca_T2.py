"""s14 · Reconciliació amb la ronda 1 (T2 «encara significatiu» al compost després del flat 2D): la mateixa mesura de s1, però amb CERCA
local (±60 px, ±1,5°, com m11/m17) al voltant de la geometria M3 i també al voltant de la marca de Pere (C5), i el nul fet amb la MATEIXA
cerca a rectes paral·leles (±150…600 px) i girades (±5°, ±10°) de la mateixa imatge. Diu ON cau el mínim de la cerca.
Sortida: S14_CERCA_T2.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
c5 = json.loads((ARREL / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
TH = np.arange(-1.5, 1.501, 0.25); res = {}
def cerca(r, org, c, d, L):
    best = (np.inf, None, None)
    for dth in TH:
        dd = gira(d, dth); t, pr, _ = perfil(r, org, c, dd, L, tmax=120)
        for t0 in np.arange(-60, 60.1, 2.0):
            D = profunditat(t, pr, t0)
            if np.isfinite(D) and D < best[0]: best = (D, float(dth), float(t0))
    return best
for k in (1, 2):
    tr = TRACOS[k]; box = caixa_tr(tr, 900)
    geoms = {'M3': (tr['centre'], tr['d'])}
    i = c5[k - 1]['info']; dc = np.array(i['direccio'], float); dc /= np.linalg.norm(dc); geoms['marca_C5'] = (np.array(i['centre'], float), dc)
    for nom in ('compost_ctrl', 'compost_f2d', 'A_ctrl', 'A_f2d'):
        a, ch = obre(nom); r = rel_map(retall(a, ch, box))
        for gn, (c, d) in geoms.items():
            v, dth, t0 = cerca(r, box[:2], c, d, tr['llarg']); n = np.array([-d[1], d[0]])
            nul = []
            for off in list(range(-600, -149, 90)) + list(range(150, 601, 90)):
                vv = cerca(r, box[:2], c + off * n, d, tr['llarg'])[0]
                if np.isfinite(vv): nul.append(vv)
            for g in (-10, -5, 5, 10):
                vv = cerca(r, box[:2], c, gira(d, g), tr['llarg'])[0]
                if np.isfinite(vv): nul.append(vv)
            nul = np.array(nul); p = float((np.sum(nul <= v) + 1) / (len(nul) + 1))
            res.setdefault(f'T{k}', {}).setdefault(nom, {})[gn] = dict(minim=v, dtheta=dth, t0=t0, nul=nul.tolist(), p=p, n_nul=int(len(nul)))
            print(f"T{k} {nom:13s} cerca al voltant de {gn:8s}: mínim {v*1e4:+7.1f}‱ a dθ {dth:+.2f}°, t {t0:+.0f} px · nul (mateixa cerca) mediana {np.median(nul)*1e4:+.1f}‱, mín {nul.min()*1e4:+.1f}‱ · p {p:.3f} ({len(nul)} nuls)", flush=True)
desa(OUT / 'S14_CERCA_T2.json', res)
