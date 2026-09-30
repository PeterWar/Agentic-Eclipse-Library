"""d22 (V99 banda) · El col·lapse de d19 per CANAL (R, G, B abans de la matriu), amb la silueta d'ordre 2 (D21_silueta_o2.npz), fotogrames tardans
(t > 40 s: dada neta de referència a dalt i a l'esquerra) i primerencs (a la dreta). ln T relatiu al nivell del sector a 8–14 px.
Pregunta: el blau (cua més llarga a la dreta, d21) és pitjor a dalt (dispersió atmosfèrica vertical amb el Sol baix)? Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(O / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -8) & (d < 45); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum())
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cl = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr])
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
Dr = np.zeros((nF, npx), np.float32); PA = np.zeros_like(Dr)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(PA[j], pag, eg, period=360)
rep = {}; DB = np.arange(1.0, 8.01, 0.5)
for c, nomc in enumerate('RGB'):
    V = np.zeros((nF, npx), np.float32); Wz = np.zeros_like(V)
    for j in range(nF):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); Wz[j] = w
    WS = Wz * (Dr >= 9)
    ref = np.nansum(np.where(WS > 0, V * WS, 0), 0) / np.maximum(WS.sum(0), 1e-30); okref = ((WS > 0).sum(0) >= 3) & (ref > 0)
    L = np.where(okref[None] & (Wz > 0) & np.isfinite(V) & (V > 0), np.log(np.maximum(V, 1e-30) / np.maximum(ref, 1e-30)[None]), np.nan)
    for ep, js in (('tard', np.flatnonzero(t > 40)), ('prim', np.flatnonzero(t < 32))):
        Lj = L[js]; Dj_ = Dr[js]; Pj = PA[js]; key = f'{nomc}_{ep}'; rep[key] = {}
        for a0 in range(0, 360, 30):
            sec = (((Pj - a0) % 360) < 30) & np.isfinite(Lj); ml = sec & (Dj_ >= 8) & (Dj_ < 14)
            if ml.sum() < 300: continue
            lv = float(np.median(Lj[ml])); row = {}
            for k0 in DB:
                m = sec & (Dj_ >= k0) & (Dj_ < k0 + 0.5)
                if m.sum() >= 150: row[f'{k0:.1f}'] = round(float(np.median(Lj[m])) - lv, 3)
            if row: rep[key][f'{a0}'] = row
        print(key); [print('  PA', a, ' '.join(f"{k}:{v:+.3f}" for k, v in r.items() if float(k) in (2.0, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0))) for a, r in rep[key].items()]
(O / 'D22_COLLAPSE_RGB.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
