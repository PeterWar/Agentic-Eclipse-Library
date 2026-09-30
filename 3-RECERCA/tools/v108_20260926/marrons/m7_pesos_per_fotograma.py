"""m7 · Els PESOS de cada fotograma a banda i banda de cada traç (sources_v36/cau/{tren}_w.npy, graella 1/4): perfil perpendicular de w/w_max
(mitjana al llarg) de −240 a +240 px. Si un traç és la frontera d'una finestra de pes (sostre de saturació, terra, vora del fotograma), el pes
d'algun fotograma hi canvia (graó) o hi té un extrem. Sortida: M7_PESOS.json (per traç i fotograma: w/w_max a t = −160, −40, 0, +40, +160; salt màxim)."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text()); CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'; Q = 4
res = {}
for tr in TRACOS:
    z = g[str(tr['k'])]; c = np.array(z['centre']); d = np.array(z['direccio']); n = np.array([-d[1], d[0]]); L = z['llarg']
    s = np.arange(-L / 2, L / 2 + 1e-6, 4.0); t = np.arange(-240, 240.01, 4.0)
    X = (((c[0] + s[:, None] * d[0] + t[None, :] * n[0]) - 1.5) / Q).astype(np.float32); Y = (((c[1] + s[:, None] * d[1] + t[None, :] * n[1]) - 1.5) / Q).astype(np.float32)
    res[tr['k']] = {}
    for tren in ('sony', 'vixen'):
        meta = json.loads((CR / f'{tren}_meta.json').read_text())['frames']; Wt = np.load(CR / f'{tren}_w.npy', mmap_mode='r')
        xa, xb = int(max(0, X.min() - 4)), int(min(Wt.shape[2], X.max() + 4)); ya, yb = int(max(0, Y.min() - 4)), int(min(Wt.shape[1], Y.max() + 4))
        files = []
        for j, m in enumerate(meta):
            w = np.asarray(Wt[j, ya:yb, xa:xb], np.float32) / m['w_max']
            P = cv2.remap(w, X - xa, Y - ya, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); pr = P.mean(0)
            if pr.max() < 0.02: continue
            at = lambda tt: float(pr[np.argmin(np.abs(t - tt))])
            dpr = np.abs(np.diff(pr)); k = int(np.argmax(dpr))
            files.append(dict(nom=m['name'], grup=m['group'], exp=m['exp'], w_rel={str(tt): round(at(tt), 4) for tt in (-160, -40, 0, 40, 160)}, salt_max=float(dpr[k] * 10), t_salt=float(t[k])))
        res[tr['k']][tren] = files
        canvi = [f for f in files if abs(f['w_rel']['-40'] - f['w_rel']['40']) > 0.02 or abs(f['w_rel']['0'] - 0.5 * (f['w_rel']['-40'] + f['w_rel']['40'])) > 0.02]
        print(f"T{tr['k']} {tren}: {len(files)} fotogrames amb pes; canvien a ±40 px: " + ', '.join(f"{f['nom'][-8:-4]}({f['exp']:g}s) {f['w_rel']['-40']:.2f}/{f['w_rel']['0']:.2f}/{f['w_rel']['40']:.2f}" for f in canvi), flush=True)
desa(OUT / 'M7_PESOS.json', res)
