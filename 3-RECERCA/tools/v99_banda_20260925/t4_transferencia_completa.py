"""t4 (V99 banda, tancament de Codex) · Transferència de la injecció t3 per filtre i versió, per distància a la vora del SEU domini (dv):
  · tangencial, PA 62–128° (les dues freqüències als mateixos píxels): amplitud demodulada a λ = 8 i λ = 24 px;
  · radial, PA 202–248°: per a finestres de dv de 6 px, ajust A·cos + B·sin de 2π·d/6 a la mediana azimutal de Δ;
  · dues versions de cada mesura: Δ amb alfa ≥ 0,99 (el filtre sol), i Δ·alfa amb alfa ≥ 0,05 (el que entra al compost, INCLÒS el primer tram
    de vora), relatives a l'interior (dv 15–30 / finestra 15–27).
Porta de Codex: 0,90–1,10. Ús: t4_transferencia_completa.py <filtres_base> <filtres_inj> <franja.npz> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
BASE, INJ, FR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
Q = np.load(FR); cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = DMIN.size
y0, y1, x0, x1 = 3150, 4450, 4700, 5950
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dv = d - np.maximum(DMIN, 0)[(th / 360 * NBZ).astype(int) % NBZ]; s = np.radians(th) * R
TAGS = {55: 'P04_WOW', 56: 'P05_WOW_bilateral', 54: 'P03_MGN', 51: '04', 50: '01', 52: '05', 53: '06'}
BT = [(0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 12), (15, 30)]; rep = {}
for lid, tag in TAGS.items():
    if not (INJ / f'{tag}_u16.npy').exists(): continue
    b = np.load(BASE / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float64) / 65535; j = np.load(INJ / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float64) / 65535
    al = np.load(BASE / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float64) / 65535; D = j - b; r = {'tag': tag}
    for mode, (Dm, amin) in (('filtre', (D, 0.99)), ('compost', (D * al, 0.05))):
        tg = (th >= 62) & (th < 128) & (al >= amin)
        for lam in (8.0, 24.0):
            ph = 2 * np.pi * s / lam; res = {}
            for lo, hi in BT:
                z = tg & (dv >= lo) & (dv < hi)
                if z.sum() >= 80: res[f'{lo}-{hi}'] = 2 * abs(np.mean(Dm[z] * np.exp(-1j * ph[z])))
            if '15-30' in res: r[f'{mode}_tang_l{int(lam)}'] = {k: round(v / res['15-30'], 3) for k, v in res.items()}
        rd = (th >= 202) & (th < 248) & (al >= amin); DB = np.arange(-1, 32, 0.25); prof = np.array([np.median(Dm[rd & (dv >= k) & (dv < k + 0.25)]) if (rd & (dv >= k) & (dv < k + 0.25)).sum() > 20 else np.nan for k in DB])
        dc = DB + 0.125
        def amp(lo, hi):
            z = (dv_c := dc) >= lo; z &= dc < hi; z &= np.isfinite(prof)
            if z.sum() < 12: return np.nan
            dd = dc[z] + np.interp(0, [0], [0]); A = np.stack([np.cos(2 * np.pi * (dd) / 6), np.sin(2 * np.pi * dd / 6), np.ones_like(dd)], 1)
            return float(np.hypot(*np.linalg.lstsq(A, prof[z], rcond=None)[0][:2]))
        ai = amp(15, 27); r[f'{mode}_radial'] = {f'{lo}-{lo+6}': round(amp(lo, lo + 6) / ai, 3) for lo in (0, 3, 6, 9)} if np.isfinite(ai) and ai > 0 else None
    rep[lid] = r; print(lid, tag, json.dumps({k: v for k, v in r.items() if k != 'tag'}), flush=True)
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
