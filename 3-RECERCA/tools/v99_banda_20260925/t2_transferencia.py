"""t2 (V99 banda) · Mesura de la transferència de la modulació injectada (t1) a través dels filtres, per distància a la vora del domini
(dv = d − DMIN(θ)): amplitud demodulada 2·|⟨Δ·e^{−iφ}⟩| (Δ = filtre injectat − filtre de la V99; φ = 2π·s/λ) i fase, relatives a l'interior
(dv 15–30 px). Porta de Codex: transferència 0,90–1,10 i cap salt de fase; si a λ = 8 la transferència arran de la vora cau més que a λ = 24,
seria «lupa» (el gra fi s'hi perd). Ús: t2_transferencia.py <filtres_base> <filtres_injectats> <franja.npz> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
BASE, INJ, FR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
Q = np.load(FR); cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = DMIN.size
y0, y1, x0, x1 = 3150, 3500, 4950, 5800
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dv = d - np.maximum(DMIN, 0)[(th / 360 * NBZ).astype(int) % NBZ]; s = np.radians(th) * R
TAGS = {55: 'P04_WOW', 56: 'P05_WOW_bilateral', 54: 'P03_MGN', 50: '01', 51: '04', 52: '05', 53: '06'}
BINS = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 12), (15, 30)]; rep = {}
for lid, tag in TAGS.items():
    fi = INJ / f'{tag}_u16.npy'
    if not fi.exists(): continue
    b = np.load(BASE / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float64) / 65535; j = np.load(fi, mmap_mode='r')[y0:y1, x0:x1].astype(np.float64) / 65535
    al = np.minimum(np.load(BASE / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1], np.load(INJ / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1]) / 65535
    D = j - b; rep[lid] = {'tag': tag}
    for (a0, a1, lam) in ((62, 93, 8.0), (97, 128, 24.0)):
        sec = (th >= a0) & (th < a1) & (al >= 0.99); ph = 2 * np.pi * s / lam; res = {}
        for lo, hi in BINS:
            z = sec & (dv >= lo) & (dv < hi)
            if z.sum() < 100: continue
            c = np.mean(D[z] * np.exp(-1j * ph[z])); res[f'{lo}-{hi}'] = (2 * abs(c), float(np.degrees(np.angle(c))))
        if '15-30' not in res: continue
        a_int, p_int = res['15-30']
        rep[lid][f'lambda{int(lam)}'] = {k: dict(amplitud=round(v[0], 5), transferencia=round(v[0] / a_int, 3), fase_rel_graus=round(((v[1] - p_int + 180) % 360) - 180, 1)) for k, v in res.items()}
    print(lid, tag, {l: {k: (v['transferencia'], v['fase_rel_graus']) for k, v in r.items()} for l, r in rep[lid].items() if l.startswith('lambda')}, flush=True)
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
