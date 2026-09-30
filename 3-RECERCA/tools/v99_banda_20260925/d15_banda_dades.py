"""d15 (V99 banda) · Què hi ha, de dada real, a la banda sense dada de la V98 (0 ≤ d < DMIN, dalt i esquerra)?
Per a cada píxel de la banda i cada fotograma Vixen: D_obs (distància al limbe observat d'aquell fotograma). Per azimut (5°) i distància
(calaixos d'1 px): nombre de fotogrames amb D_obs ≥ 1, 2, 3, 4, 5 px; pes efectiu (en fotogrames curts) i D_obs màxim.
També, per comparar, a 6–10 px (fora de la banda) i a la dreta. Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
Q = np.load(ARREL / '4-RESULTATS/v98_20260925/lineal_v98_franja/A3B_franja_neta.npz')
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = float(meta['radius_model']) - RL
Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
DMIN = Q['DMIN']; NBZ = DMIN.size; ib = (th / 360 * NBZ).astype(int) % NBZ; dmin = DMIN[ib]
zona = (d >= 0) & (d < 12); dz = d[zona]; tz = th[zona]; nF = len(fr)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr])
curts = np.flatnonzero(cls == 'curts'); _wc = np.asarray(Wt[curts[0], ::7, ::7, 1]); W_CURT = float(np.median(_wc[_wc > 0]))
Dz = np.zeros((nF, zona.sum()), np.float32); Wz = np.zeros_like(Dz)
for j in range(nF): Dz[j] = np.asarray(Dm[j])[zona] + DR; Wz[j] = np.asarray(Wt[j, :, :, 1])[zona]
rep = dict(W_CURT=W_CURT, nota='n_Dk = nombre de fotogrames amb pes > 0 i D_obs ≥ k; w_Dk = pes efectiu en fotogrames curts; Dmax = mediana del D_obs màxim; classes = fotogrames amb D_obs ≥ 2 per classe', sectors={})
for a0 in range(0, 360, 15):
    sec = (((tz - a0) % 360) < 15); s_ = {}
    for d0 in range(0, 10):
        z = sec & (dz >= d0) & (dz < d0 + 1)
        if z.sum() < 20: continue
        D = Dz[:, z]; W = Wz[:, z]; r = {}
        for k in (1, 2, 3, 4, 5, 6):
            m = (D >= k) & (W > 0); r[f'n_D{k}'] = float(np.median(m.sum(0))); r[f'w_D{k}'] = round(float(np.median((W * m).sum(0))) / W_CURT, 1)
        r['Dmax'] = round(float(np.median(np.where(W > 0, D, -99).max(0))), 2)
        m2 = (D >= 2) & (W > 0); r['classes_D2'] = {c: float(np.median(m2[cls == c].sum(0))) for c in ('curts', 'mitjans', 'llargs')}
        r['frac_banda'] = round(float((dz[z] < dmin[zona][z]).mean()), 2)
        s_[f'{d0}-{d0+1}'] = r
    rep['sectors'][f'{a0}-{a0+15}'] = s_
    print(a0, {k: (v['n_D2'], v['n_D3'], v['w_D3'], v['Dmax'], v['frac_banda']) for k, v in s_.items()}, flush=True)
(O / 'D15_BANDA_DADES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
