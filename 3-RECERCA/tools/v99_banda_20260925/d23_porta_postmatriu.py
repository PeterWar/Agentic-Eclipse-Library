"""d23 (V99 banda) · La porta de biaix sobre el que veuen els FILTRES: el verd post-matriu G' (NRGF, RHEF, WOW, MGN, ACHF azimutals) i la
lluminància post-matriu L' = (R'+2G'+B')/4 (ACHF isòtrops). Silueta d'ordre 2 només de tardans (D21_silueta_o2_tardans.npz: exclusió estricta).
(1) Exclusió a la dreta: A = primerencs (t < 32) amb rampa sobre D_real, B = veritat (t > 40, D_real ≥ 9), per canal i després matriu; biaix =
    ln(A'/B') al calaix − el de 10–20 px.
(2) Dalt i esquerra (sense veritat per als primerencs): col·lapse dels TARDANS per fotograma en post-matriu, ln(V'_j/ref') per PA i D_real, relatiu
    al nivell del sector a 8–14 px (la mateixa silueta).
Porta de Codex: |biaix| ≤ 2 % per sector. Només lectura."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(O / 'D21_silueta_o2_tardans.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32)
zona = (d >= -8) & (d < 40); X = xx[zona].astype(np.float64); Y = yy[zona].astype(np.float64); th = ((np.degrees(np.arctan2(-(Y - LY), X - LX)) + 360) % 360)
nF = len(fr); npx = int(zona.sum()); t = np.array([f['time'] for f in fr])
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
Dr = np.zeros((nF, npx), np.float32); PA = np.zeros_like(Dr); V = np.zeros((nF, npx, 3), np.float32); W = np.zeros_like(V)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    PA[j] = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[zona] + DR - np.interp(PA[j], pag, eg, period=360)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c])[zona]; n = np.asarray(N[j, :, :, c])[zona]; V[j, :, c] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j, :, c] = w
def post(E):   # E (..., 3) cru → (G', L')
    P = np.einsum('ij,...j->...i', Mx, E * gn); return P[..., 1], (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4
def mitjana(js, sfun):
    num = np.zeros((npx, 3)); den = np.zeros((npx, 3)); dm = np.zeros(npx); dw = np.zeros(npx)
    for j in js:
        s = sfun(j)
        for c in range(3):
            m = (W[j, :, c] > 0) & np.isfinite(V[j, :, c]) & (s > 0); w = np.where(m, W[j, :, c] * s, 0); num[:, c] += np.where(m, w * V[j, :, c], 0); den[:, c] += w
            if c == 1: dm += w * np.where(m, Dr[j], 0); dw += w
    E = np.where((den > 0).all(1)[:, None], num / np.maximum(den, 1e-30), np.nan); return E, np.where(dw > 0, dm / np.maximum(dw, 1e-30), np.nan)
rep = {'exclusio_dreta': {}, 'collapse_tardans': {}}
PROVA = np.flatnonzero(t < 32); ALTRES = np.flatnonzero(t > 40)
EB, _ = mitjana(ALTRES, lambda j: (Dr[j] >= 9).astype(float)); GB, LB = post(EB)
for nom, (lo, hi) in {'3.5-6': (3.5, 6), '4-6.5': (4, 6.5), '4.5-7': (4.5, 7), '5-7.5': (5, 7.5)}.items():
    EA, Dmit = mitjana(PROVA, lambda j: smoothstep(Dr[j], lo, hi)); GA, LA = post(EA); rep['exclusio_dreta'][nom] = {}
    for sn, (a0, a1) in {'280-330': (280, 330), '330-15': (330, 375), '15-65': (15, 65)}.items():
        sec = (((th - a0) % 360) < (a1 - a0)); row = {}
        for q, (A_, B_) in (('G', (GA, GB)), ('L', (LA, LB))):
            ok = sec & np.isfinite(A_) & np.isfinite(B_) & (A_ > 0) & (B_ > 0); ref = ok & (Dmit >= 10) & (Dmit < 20); r0 = float(np.median(np.log(A_[ref] / B_[ref])))
            for k0 in np.arange(lo, lo + 3.01, 0.5):
                zz = ok & (Dmit >= k0) & (Dmit < k0 + 0.5)
                if zz.sum() >= 100: row[f'{q}{k0:.1f}'] = round(float(np.median(np.log(A_[zz] / B_[zz]))) - r0, 4)
        rep['exclusio_dreta'][nom][sn] = row
    print('exclusió', nom, json.dumps(rep['exclusio_dreta'][nom]), flush=True)
# (2) col·lapse dels tardans en post-matriu
Eref, _ = mitjana(np.arange(nF), lambda j: (Dr[j] >= 9).astype(float)); Gr, Lr = post(Eref)
js = np.flatnonzero(t > 40); DB = np.arange(2.0, 8.01, 0.5)
for q in ('G', 'L'):
    rep['collapse_tardans'][q] = {}
    LLs = []; DDs = []; PPs = []
    for j in js:
        okj = (W[j] > 0).all(1) & np.isfinite(V[j]).all(1)
        if okj.sum() == 0: continue
        Gj, Lj = post(np.where(okj[:, None], V[j], np.nan)); vj, rj = (Gj, Gr) if q == 'G' else (Lj, Lr)
        m = okj & np.isfinite(rj) & (rj > 0) & (vj > 0); LLs.append(np.log(vj[m] / rj[m])); DDs.append(Dr[j][m]); PPs.append(PA[j][m])
    LL = np.concatenate(LLs); DD = np.concatenate(DDs); PP = np.concatenate(PPs)
    for a0 in range(0, 360, 30):
        sec = ((PP - a0) % 360) < 30; ml = sec & (DD >= 8) & (DD < 14)
        if ml.sum() < 300: continue
        lv = float(np.median(LL[ml])); row = {}
        for k0 in DB:
            m = sec & (DD >= k0) & (DD < k0 + 0.5)
            if m.sum() >= 150: row[f'{k0:.1f}'] = round(float(np.median(LL[m])) - lv, 4)
        if row: rep['collapse_tardans'][q][f'{a0}'] = row
    print('col·lapse tardans', q); [print('  PA', a, ' '.join(f"{k}:{v:+.3f}" for k, v in r.items() if float(k) in (3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0))) for a, r in rep['collapse_tardans'][q].items()]
(O / 'D23_PORTA_POSTMATRIU.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
