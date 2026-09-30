"""d16 (V99 banda) · La transmissió de vora T(D) de cada fotograma: ln(V_j / referència neta) en funció de la distància al SEU limbe (D_obs),
per ANGLE DE POSICIÓ LUNAR (el lloc del limbe de la Lluna que fa l'ombra, calculat amb el centre del model d'aquell fotograma), classe i època.
Referència neta de cada píxel = la mateixa selecció física de l'a3b (pes × smoothstep(D_obs) per classe), que no inclou mai el fotograma
que es mesura quan aquest té D_obs < rampa. Normalització per classe i època: mediana a D_obs 15–30 px (el nivell de la classe).
Pregunta: és T(D) estable en el temps (època primerenca a la dreta contra època mitjana a la dreta) i al llarg del limbe (dreta contra
dalt/esquerra, amb els fotogrames de mitja totalitat que tenen dada neta a tots dos costats)? Si ho és, es pot mesurar allà on la banda no
té veritat i aplicar als 16 fotogrames que la veuen. Només lectura."""
import json, sys
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -6) & (d < 60); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum())
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr])
RAMPES = {'curts': (6.0, 9.0), 'mitjans': (5.0, 8.0), 'llargs': (6.0, 10.0)}
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
V = np.zeros((nF, npx), np.float32); Wz = np.zeros_like(V); Dz = np.zeros_like(V); PA = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300   # centre del model (cercle exacte): p − (D+Rm)·∇D
    cxj = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cyj = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    n_ = np.asarray(N[j, :, :, 1])[zona]; w_ = np.asarray(Wt[j, :, :, 1])[zona]
    V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); Wz[j] = w_; Dz[j] = Dj[zona] + DR
    PA[j] = (np.degrees(np.arctan2(-(Y - cyj), X - cxj)) + 360) % 360
S = np.stack([smoothstep(Dz[j], *RAMPES[cls[j]]) for j in range(nF)]); WS = Wz * S
ref = np.nansum(np.where(WS > 0, V * WS, 0), 0) / np.maximum(WS.sum(0), 1e-30); nref = (WS > 0).sum(0)
okref = (nref >= 3) & (ref > 0)
lr = np.where(okref[None] & (Wz > 0) & np.isfinite(V) & (V > 0), np.log(np.maximum(V, 1e-30) / np.maximum(ref, 1e-30)[None]), np.nan)
epoca = np.where(t < 32, 'primerenca', np.where(t < 80, 'mitjana', 'tardana'))
# nivell de cada classe i època (D_obs 15–30): la T és relativa a aquest nivell
niv = {}
for c in RAMPES:
    for e in ('primerenca', 'mitjana', 'tardana'):
        js = np.flatnonzero((cls == c) & (epoca == e))
        if js.size == 0: continue
        m = (Dz[js] >= 15) & (Dz[js] < 30) & np.isfinite(lr[js]); niv[f'{c}_{e}'] = float(np.median(lr[js][m])) if m.sum() > 1000 else None
DB = np.arange(-2, 12.01, 0.5)
rep = dict(nota='ln T (mediana de ln V_j/ref − nivell de classe i època) per calaix de D_obs (px, límit inferior) i sector d\'angle de posició lunar (15°)', nivell=niv, T={})
for c in RAMPES:
    for e in ('primerenca', 'mitjana', 'tardana'):
        js = np.flatnonzero((cls == c) & (epoca == e))
        if js.size == 0 or niv.get(f'{c}_{e}') is None: continue
        key = f'{c}_{e}'; rep['T'][key] = {}
        L = lr[js] - niv[key]; D_ = Dz[js]; P_ = PA[js]
        for a0 in range(0, 360, 15):
            sec = (((P_ - a0) % 360) < 15) & np.isfinite(L); row = {}
            for k in range(DB.size - 1):
                m = sec & (D_ >= DB[k]) & (D_ < DB[k + 1])
                if m.sum() >= 150: row[f'{DB[k]:.1f}'] = [round(float(np.median(L[m])), 3), int(m.sum())]
            if row: rep['T'][key][f'{a0}'] = row
        print(key, 'nivell', niv[key], flush=True)
        for a0, row in rep['T'][key].items():
            print('  PA', a0, ' '.join(f"{k}:{v[0]:+.2f}" for k, v in row.items() if float(k) in (0.0, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0)), flush=True)
(O / 'D16_TRANSMISSIO_VORA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
