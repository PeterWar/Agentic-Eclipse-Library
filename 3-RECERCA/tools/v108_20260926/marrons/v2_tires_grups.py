"""v2 · Tires redreçades de cada traç a partir dels FOTOGRAMES (graella 1/4, sources_v36), mitjana del contrast relatiu per GRUP independent:
Sony A llargs (≥ 1 s), Sony B llargs (≥ 1 s), Vixen llargs (≥ 1 s). Si la recta hi és als tres, al mateix lloc del llenç, és fixa al cel.
Ús: v2_tires_grups.py <sortida.png> [lim=0.0015]"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
dst = sys.argv[1]; kw = dict(a.split('=') for a in sys.argv[2:]); lim = float(kw.get('lim', 0.0015))
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text()); CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'; Q = 4
GR = [('sony', 'sony_A', 1.0), ('sony', 'sony_B', 1.0), ('vixen', 'vixen', 1.0)]
blocs = []; mesures = {}
for tr in TRACOS:
    z = g[str(tr['k'])]; c = np.array(z['centre']); d = np.array(z['direccio']); n = np.array([-d[1], d[0]]); L = z['llarg'] + 800
    s = np.arange(-L / 2, L / 2 + 1e-6, 8.0); t = np.arange(-300, 300.01, 4.0)
    X = ((c[0] + s[:, None] * d[0] + t[None, :] * n[0]) - 1.5) / Q; Y = ((c[1] + s[:, None] * d[1] + t[None, :] * n[1]) - 1.5) / Q
    fila = []
    for tren, grup, emin in GR:
        meta = json.loads((CR / f'{tren}_meta.json').read_text())['frames']; V = np.load(CR / f'{tren}_v.npy', mmap_mode='r'); Wt = np.load(CR / f'{tren}_w.npy', mmap_mode='r')
        xa, xb = int(max(0, X.min() - 40)), int(min(V.shape[2], X.max() + 40)); ya, yb = int(max(0, Y.min() - 40)), int(min(V.shape[1], Y.max() + 40))
        num = np.zeros_like(X, np.float32); den = np.zeros_like(X, np.float32); nf = 0
        for j, m in enumerate(meta):
            if m['group'] != grup or m['exp'] < emin: continue
            v = np.asarray(V[j, ya:yb, xa:xb], np.float32); w = np.asarray(Wt[j, ya:yb, xa:xb], np.float32); ok = (w > 0) & np.isfinite(v) & (v > 0)
            if ok.mean() < 0.05: continue
            wf = ok.astype(np.float32); vv = np.where(ok, v, 0)
            sm = cv2.GaussianBlur(vv * wf, (0, 0), 12) / np.maximum(cv2.GaussianBlur(wf, (0, 0), 12), 1e-6)
            r = np.where(ok, vv / np.maximum(sm, 1e-12) - 1, 0).astype(np.float32)
            r = cv2.GaussianBlur(r * wf, (0, 0), 0.8) / np.maximum(cv2.GaussianBlur(wf, (0, 0), 0.8), 1e-6)
            P = cv2.remap(r, (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            Pw = cv2.remap(wf * m['exp'], (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            num += P * Pw; den += Pw; nf += 1
        A = np.where(den > 0, num / np.maximum(den, 1e-9), np.nan)
        with np.errstate(all='ignore'): pr = np.nanmean(A[np.abs(s) <= z['llarg'] / 2], 0)
        mesures[f"T{tr['k']}_{grup}"] = dict(n_fotogrames=nf, solc=float(np.nanmean(pr[np.abs(t) <= 4]) - np.nanmean(pr[(np.abs(t) >= 24) & (np.abs(t) <= 200)])) if nf else None)
        u = np.clip(128 + 127 * np.nan_to_num(A.T, nan=0) / lim, 0, 255).astype(np.uint8); u = cv2.resize(u, (u.shape[1] * 2, u.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
        u = cv2.cvtColor(u, cv2.COLOR_GRAY2BGR); u[:, [int((L / 2 - z['llarg'] / 2) / 8 * 2), int((L / 2 + z['llarg'] / 2) / 8 * 2)]] = (0, 160, 0)
        u[u.shape[0] // 2 - 20:u.shape[0] // 2 - 16, ::8] = (0, 0, 255); u[u.shape[0] // 2 + 16:u.shape[0] // 2 + 20, ::8] = (0, 0, 255)
        cv2.putText(u, f"T{tr['k']} {grup} >=1s ({nf} fot.)", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1); fila.append(u)
    blocs.append(np.hstack([np.pad(f, ((0, 4), (0, 8), (0, 0)), constant_values=60) for f in fila]))
wmax = max(b.shape[1] for b in blocs); out = np.vstack([np.pad(b, ((0, 0), (0, wmax - b.shape[1]), (0, 0)), constant_values=60) for b in blocs])
cv2.putText(out, f'contrast relatiu per fotograma (v/g12-1 a 1/4), mitjana ponderada per exposicio, +-{lim*1e4:g} per 10000', (4, out.shape[0] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
cv2.imwrite(dst, out); print(dst, out.shape); print(json.dumps(mesures, indent=0))
desa(OUT / 'V2_TIRES_GRUPS.json', mesures)
