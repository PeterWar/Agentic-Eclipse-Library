"""m2b (V106) · Brno com a JUTGE, el mètode de la m2 de la V105 amb composts arbitraris: ¿el detall que la capa nova AFEGEIX (ΔH = H_nou − H_vell,
detall tangencial del compost emulat) coincideix amb el que veuen els composts publicats de Brno (capes ocultes 230–233)? Cap píxel de Brno entra enlloc.
Ús: m2b_jutge_brno.py <COMP_vell.npy> <COMP_nou.npy> [<sortida.json>]"""
import sys, json, numpy as np, cv2
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
R0 = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, LLUNA, RLLUNA
C4 = np.load(sys.argv[1]); C5 = np.load(sys.argv[2])
S = Estat(R0 / '4-RESULTATS/v103_banda_20260926/E/estat_v103'); box = (4677, 3077, 6077, 4477); cx, cy = LLUNA; R = RLLUNA
dg = np.arange(-2, 12.01, 0.5); nth = int(round(2 * np.pi * R / 0.5)); th = np.linspace(0, 2 * np.pi, nth, endpoint=False); dth = np.degrees(th)
X = (cx + np.cos(th)[None, :] * (R + dg[:, None]) - box[0]).astype(np.float32); Y = (cy - np.sin(th)[None, :] * (R + dg[:, None]) - box[1]).astype(np.float32)
pol = lambda a: cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR)
def hp(p): l = np.log(np.maximum(p, 1e-4)); return gaussian_filter1d(l, 2.0, axis=1, mode='wrap') - gaussian_filter1d(l, 64.0, axis=1, mode='wrap')
L = lambda C: (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
H4 = hp(pol(L(C4))); H5 = hp(pol(L(C5))); dH = H5 - H4; act = np.abs(dH) > 1e-4
rep = {}
for lid in (230, 231, 232, 233):
    Bq = S.rgb(lid, box); Lb = L(Bq) if Bq.ndim == 3 else Bq
    if Lb.max() <= 0: continue
    Hb = hp(pol(np.maximum(Lb, 1e-4))); Lbp = pol(Lb); rep[lid] = {}
    for zona, (lo, hi) in {'dalt 60-110': (60, 110), 'dalt-esq 110-150': (110, 150), 'esq 150-210': (150, 210), 'baix-esq 210-250': (210, 250), 'baix 250-290': (250, 290), 'dreta 300-360': (300, 360)}.items():
        s = (dth >= lo) & (dth < hi); rows = []
        for i, d in enumerate(dg):
            m = s & act[i] & (Lbp[i] > 1e-3); m2 = s & (Lbp[i] > 1e-3)
            if m.sum() < 100: continue
            c = lambda x, mm: float(np.corrcoef(x[i][mm], Hb[i][mm])[0, 1])
            rows.append(dict(d=float(d), corr_afegit=c(dH, m), corr_vell=c(H4, m2), corr_nou=c(H5, m2), n=int(m.sum())))
        if rows: rep[lid][zona] = rows
for lid, z in rep.items():
    for zona, rows in z.items():
        print(f'Brno {lid} · {zona}: ' + '  '.join(f"d{r['d']:g}:{r['corr_afegit']:+.2f}({r['corr_vell']:+.2f}→{r['corr_nou']:+.2f})" for r in rows))
if len(sys.argv) > 3: open(sys.argv[3], 'w').write(json.dumps(rep, indent=1))
