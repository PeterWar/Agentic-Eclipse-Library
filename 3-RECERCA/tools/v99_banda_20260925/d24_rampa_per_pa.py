"""d24 (V99 banda) · La rampa de selecció per ANGLE DE POSICIÓ, mesurada: on el dèficit de vora post-matriu (G' i L' = el que veuen els filtres)
ja és ≤ LLINDAR, per a l'època que veu cada sector (primerencs on es pot mesurar: PA 240–60, on la Lluna s'allunya; si no, tardans).
Silueta d'ordre 2 només de tardans (D21_silueta_o2_tardans.npz) per mesurar; el resultat s'aplica amb la silueta comuna d'ordre 2.
Col·lapse per fotograma en post-matriu: ln(X_j/X_ref) per PA (15°) i D_real (0,25 px), relatiu al nivell del sector a 8–14 px;
D_llindar(PA) = primer D a partir del qual el pitjor de G' i L' és ≥ −LLINDAR (i ho continua sent). Suavitzat circular (σ 15°), acotat a [3,5; 6,5].
Sortida: RAMPA_PA_V99.json (lo per grau; hi = lo + AMPLE). Només lectura de la dada."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
LLINDAR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.015; AMPLE = 2.5
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(O / 'D21_silueta_o2_tardans.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -10) & (d < 40); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); nF = len(fr); npx = int(zona.sum()); t = np.array([f['time'] for f in fr])
Dr = np.zeros((nF, npx), np.float32); PA = np.zeros_like(Dr); V = np.zeros((nF, npx, 3), np.float32); W = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(PA[j], pag, eg, period=360)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j, :, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, :, c] = w
def post(E): P = np.einsum('ij,...j->...i', Mx, E * gn); return P[..., 1], (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4
num = np.zeros((npx, 3)); den = np.zeros((npx, 3))
for j in range(nF):
    for c in range(3):
        m = (W[j, :, c] > 0) & np.isfinite(V[j, :, c]) & (Dr[j] >= 9); num[:, c] += np.where(m, W[j, :, c] * V[j, :, c], 0); den[:, c] += np.where(m, W[j, :, c], 0)
Eref = np.where((den > 0).all(1)[:, None], num / np.maximum(den, 1e-30), np.nan); Gr, Lr = post(Eref)
DB = np.arange(2.0, 8.01, 0.25); taula = {}
for ep, js in (('prim', np.flatnonzero(t < 32)), ('tard', np.flatnonzero(t > 40))):
    LG, LL_, DD, PP = [], [], [], []
    for j in js:
        okj = (W[j] > 0).all(1) & np.isfinite(V[j]).all(1)
        Gj, Lj = post(np.where(okj[:, None], V[j], np.nan)); m = okj & np.isfinite(Gr) & (Gr > 0) & (Lr > 0) & (Gj > 0) & (Lj > 0)
        LG.append(np.log(Gj[m] / Gr[m])); LL_.append(np.log(Lj[m] / Lr[m])); DD.append(Dr[j][m]); PP.append(PA[j][m])
    LG = np.concatenate(LG); LL_ = np.concatenate(LL_); DD = np.concatenate(DD); PP = np.concatenate(PP); taula[ep] = {}
    for a0 in range(0, 360, 15):
        sec = ((PP - a0 + 7.5) % 360) < 15; ml = sec & (DD >= 8) & (DD < 14)
        if ml.sum() < 300: continue
        lg0 = np.median(LG[ml]); ll0 = np.median(LL_[ml]); prof = []
        for k0 in DB:
            m = sec & (DD >= k0) & (DD < k0 + 0.25)
            prof.append(min(np.median(LG[m]) - lg0, np.median(LL_[m]) - ll0) if m.sum() >= 100 else np.nan)
        prof = np.array(prof); f = np.isfinite(prof)
        if f.sum() < 8: continue
        dol = np.flatnonzero(f & (prof < -LLINDAR)); dlim = float(DB[dol.max()] + 0.25) if dol.size else float(DB[f][0])
        cobert = float(DB[f][0])   # si el perfil no arriba prou a prop, el llindar només és una cota
        taula[ep][a0] = dict(D_llindar=round(dlim, 2), primer_D_mesurat=cobert, cota=bool(not dol.size and cobert > 3.5), perfil={f'{k:.2f}': round(float(v), 4) for k, v in zip(DB, prof) if np.isfinite(v)})
    print(ep, {a: (v['D_llindar'], v['primer_D_mesurat']) for a, v in taula[ep].items()}, flush=True)
# època que veu la banda a cada PA: els primerencs on es poden mesurar i no són cota; si no, els tardans
lo15 = {}
for a0 in range(0, 360, 15):
    p = taula['prim'].get(a0); q = taula['tard'].get(a0)
    if p and not p['cota'] and p['primer_D_mesurat'] <= 3.5: lo15[a0] = ('prim', p['D_llindar'])
    elif q and not q['cota']: lo15[a0] = ('tard', q['D_llindar'])
    elif p: lo15[a0] = ('prim_cota', p['D_llindar'])
angs = np.array(sorted(lo15)); vals = np.array([lo15[a][1] for a in angs])
g = np.interp(np.arange(360), angs, vals, period=360); lo = np.clip(gaussian_filter1d(g, 15, mode='wrap'), 3.5, 6.5)
lo = np.maximum(lo, np.clip(g, 3.5, 6.5) - 0.25)   # el suavitzat no pot baixar més d'un quart de píxel per sota del mesurat
rep = dict(llindar=LLINDAR, ample=AMPLE, per_15graus={f'{a}': dict(epoca=lo15[a][0], D=lo15[a][1]) for a in angs}, lo_per_grau=[round(float(v), 3) for v in lo],
           nota='lo(PA) sobre D_real (silueta comuna d\'ordre 2); rampa smoothstep lo → lo+ample per a totes les classes', taula=taula)
(O / f'RAMPA_PA_V99_{int(LLINDAR*1000)}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print('lo(PA) cada 15°:', ' '.join(f"{a}:{lo[a]:.2f}" for a in range(0, 360, 15)))
