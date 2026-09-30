"""m19 · La prova de la WOW al LLENÇ SENCER: les dues WOW del projecte (P04 WOW i P05 WOW bilateral, operador V95 wow_v95 amb els paràmetres de
l'etapa E2 de v98_20260925/f3_filtres_v98.py: 8 escales, centra_rad, iso, llindar 0,6–0,995, K de pantalla de la V95; entrada = base_G de la
linealitzada amb la franja A3C a la caixa lunar i el domini de la franja, com fa f3) sobre la base d'ABANS (E, la de la V104–V107) i la del
PILOT (flat 2D). Les constants de centratge per escala es mesuren a l'ABANS i es fan servir per a totes dues (la diferència és només la dada).
Sortida: pilot/wow_<P04|P05>_<abans|despres>_u16.npy (0–65535 com les capes 55/56) i M19_WOW.json (temps, constants).
Ús: m19_wow_llenc.py <lineal_abans> <lineal_despres> <franja.npz> [P04,P05]"""
import sys, json, time, gc
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924')); from wow_v95 import wow_v95
LA, LD, FR = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); QUINES = (sys.argv[4] if len(sys.argv) > 4 else 'P04,P05').split(',')
Q = np.load(FR); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s)); L0 = 0.6
PARAM = {'P05': (True, dict(centra_rad=True, iso=(0.5, 1.5), sig_rad=SIG, llindar=lambda s: (L0, 0.995)), 0.02317), 'P04': (False, dict(centra_rad=True, iso=(0.25, 0.75), sig_rad=SIG, llindar=lambda s: (L0, 0.995)), 0.03709)}
PD = OUT / 'pilot'; rep = {}
def entrada(L):
    a = np.load(L / 'base_G.npy').astype(np.float32); m = np.load(L / 'support.npy') & np.isfinite(a) & (a > 0)
    a[BOXQ] = Q['G']; m[BOXQ] = Q['domini'] & (Q['G'] > 0); return np.nan_to_num(a), m
for tag in QUINES:
    bil, P, K = PARAM[tag]; mus = None; rep[tag] = {}
    for et, L in (('abans', LA), ('despres', LD)):
        a, m = entrada(L); dmap = np.full(a.shape, 1e4, np.float32); t0 = time.time()
        q, _, mus_ = wow_v95(a, m, dmap, 8, bil, log=lambda s: None, mus=mus, **P)
        if mus is None: mus = mus_
        disp = np.where(m, 0.5 + K * np.nan_to_num(q), 0.5); u16 = np.round(np.clip(disp, 0, 1) * 65535).astype(np.uint16)
        np.save(PD / f'wow_{tag}_{et}_u16.npy', u16); rep[tag][et] = dict(segons=time.time() - t0, mus=[float(x) for x in mus]); print(tag, et, f'{time.time()-t0:.0f}s', flush=True)
        del a, m, q, disp, u16, dmap; gc.collect()
    desa(OUT / 'M19_WOW.json', rep)
