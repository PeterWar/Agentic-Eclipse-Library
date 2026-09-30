"""j16 (V98) · Arcs llunyans concèntrics amb el Sol (Artefactes_V95 §5: ACHF 06 i RHEF a 4–5 R☉, i arcs grans). Per a cada filtre i sector de 30°,
perfil radial (mediana per anell d'1 px centrat al Sol, r 600–3400 px), pas alt en r (menys gaussiana σ 40 px): els arcs coherents al llarg de
l'azimut hi queden. Nul: el mateix amb el centre desplaçat 400 px (un arc centrat al Sol hi perd la coherència). Índex = RMS / RMS del nul.
Ús: j16_arcs_llunyans.py <sortida.json> nom=<carpeta filtres> ..."""
import sys, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
CX, CY = 5361.768, 3775.748; H, W = 7506, 10551
TAG = {43: 'P02_RHEF', 53: '06', 52: '05', 50: '01', 55: 'P04_WOW', 56: 'P05_WOW_bilateral', 41: 'P01_NRGF', 49: '07'}
def arcs(u, al, cx, cy, pas=2):
    y, x = np.mgrid[0:H:pas, 0:W:pas]; r = np.hypot(x - cx, y - cy); th = (np.degrees(np.arctan2(-(y - cy), x - cx)) + 360) % 360
    uu = u[::pas, ::pas]; ok = (al[::pas, ::pas] > 0.99) & (r >= 600) & (r < 3400); res = {}
    for a0 in range(0, 360, 30):
        s = ok & (((th - a0) % 360) < 30); ri = r[s].astype(int) - 600
        if s.sum() < 5000: continue
        order = np.argsort(ri); rs = ri[order]; vs = uu[s][order]; cut = np.searchsorted(rs, np.arange(2801))
        prof = np.array([np.median(vs[cut[i]:cut[i + 1]]) if cut[i + 1] - cut[i] > 20 else np.nan for i in range(2800)])
        f = np.isfinite(prof)
        if f.sum() < 500: continue
        p = np.interp(np.arange(2800), np.flatnonzero(f), prof[f]); hp = p - gaussian_filter1d(p, 40)
        res[f'{a0}-{a0+30}'] = float(np.sqrt(np.mean(hp[f] ** 2)))
    return res
out = {}
for arg in sys.argv[2:]:
    nom, carp = arg.split('='); carp = Path(carp); out[nom] = {}
    for lid, tag in TAG.items():
        fu = carp / f'{tag}_u16.npy'
        if not fu.exists(): continue
        u = np.load(fu, mmap_mode='r').astype(np.float32) / 65535; al = np.load(carp / f'{tag}_alfa_u16.npy', mmap_mode='r').astype(np.float32) / 65535
        a = arcs(u, al, CX, CY); n = arcs(u, al, CX + 400, CY - 300)
        idx = {k: round(a[k] / max(n.get(k, np.nan), 1e-9), 2) for k in a if k in n}
        out[nom][lid] = dict(tag=tag, rms_sol=a, rms_nul=n, index=idx, index_max=max(idx.values()) if idx else None)
        print(nom, lid, tag, 'índex màx', out[nom][lid]['index_max'], 'per sector', idx, flush=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
