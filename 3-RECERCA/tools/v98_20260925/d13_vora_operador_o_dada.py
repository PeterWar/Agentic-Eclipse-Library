"""d13 (V98) · Prova discriminant (Codex, 25-09): el vorell fosc del primer píxel de dada de la RHEF local és de l'OPERADOR (la vora del
domini) o de la DADA? Es calcula la RHEF local 30° amb el domini normal i amb el domini retallat 5 px més (dv ≥ 5). Si el vorell es desplaça
a la vora nova (dv = 5), és l'operador; si a dv ≈ 5–8 el resultat retallat surt normal i el vorell es queda al lloc de la vora original, és la dada."""
import sys, os, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('V97_SORT', str(ARREL / '4-RESULTATS/v98_20260925/_scratch_d13'))
from v97_comu import *
from rhef_local_sim import rhef_local_sim
R = ARREL / '4-RESULTATS/v98_20260925'; Q = np.load(R / 'lineal_v98_franja/A3B_franja_neta.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
a = np.load(R / 'lineal_v98/base_G.npy').astype(np.float32); m = np.load(R / 'lineal_v98/support.npy') & np.isfinite(a) & (a > 0); m[BOXQ] = Q['domini'] & (a[BOXQ] > 0)
r, t = coords(); LX, LY, RL = [float(v) for v in Q['centre']]; yy, xx = np.mgrid[qy0:qy1, qx0:qx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
DM = np.maximum(Q['DMIN'], 0); dv = d - DM[(th / 360 * len(DM)).astype(int) % len(DM)]
m2 = m.copy(); m2[BOXQ] &= ~((dv < 5) & (d < 45))
out = {}
for nom, mm in (('normal', m), ('retallat5', m2)):
    q = rhef_local_sim(a, mm, r, t, 30., 7.5, CX, CY, log=lambda s: None, nmin=200)[BOXQ]
    for a0, a1 in ((120, 160), (200, 250), (80, 110)):
        s = (th >= a0) & (th < a1) & mm[BOXQ] & np.isfinite(q)
        out[f'{nom} {a0}-{a1}'] = [round(float(np.median(q[s & (dv >= k) & (dv < k + 1)])), 3) if (s & (dv >= k) & (dv < k + 1)).sum() > 20 else None for k in range(0, 14)]
        print(nom, f'{a0}-{a1}', 'dv 0..13:', out[f'{nom} {a0}-{a1}'], flush=True)
(R / 'D13_VORA_OPERADOR_O_DADA.json').write_text(json.dumps(out, indent=1))
