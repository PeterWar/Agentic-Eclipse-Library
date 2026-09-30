"""d32 (V100 detall) · L'autocalibratge de d31 (Kuhn, Lin i Loranz 1991) resolt de cop: mínims quadrats dispersos (LSQR) amb totes les incògnites
alhora, ln C(x) per píxel, ln g_k per classe i ln T_k(D) per classe i calaix de 0,25 px. Ancoratge: ln T = 0 a D_real ≥ ANCORA (12 px per defecte:
la cua de la vora arriba a ~10 px) i ln g_curts = 0. Pes de cada observació ∝ √(pes LDIC). Només els fotogrames d'una època i els píxels d'un sector.
VALIDACIÓ (opcional) contra la veritat dels tardans (D_real ≥ 12) al mateix sector: biaix per calaix de D_real màxim del píxel.
Ús: d32_kll_lsqr.py <PA0> <PA1> <canal> [--validar] [--ancora 12] [--epoca primerencs|tardans] [--desa]
  --desa guarda lnT, lng i els calaixos a 4-RESULTATS/v100_detall_20260925/kll/KLL2_<PA0>_<PA1>_<canal>_<epoca>.npz"""
import json, sys, argparse
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import lsqr
ap = argparse.ArgumentParser(); ap.add_argument('pa0', type=float); ap.add_argument('pa1', type=float); ap.add_argument('canal', type=int)
ap.add_argument('--validar', action='store_true'); ap.add_argument('--ancora', type=float, default=12.0); ap.add_argument('--epoca', default='primerencs'); ap.add_argument('--desa', action='store_true')
A = ap.parse_args()
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925/kll'; O.mkdir(parents=True, exist_ok=True)
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL; DMIN_OBS = 0.5
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
sec = (((th - A.pa0) % 360) < ((A.pa1 - A.pa0) % 360)) & (d >= -3) & (d < A.ancora + 25); X = xx[sec].astype(np.float64); Y = yy[sec].astype(np.float64); npx = int(sec.sum())
t = np.array([f['time'] for f in fr]); ex = np.array([f['exposure'] for f in fr])
def classe(e): return 0 if e <= 1 / 800 else (1 if e <= 1 / 50 else 2)
cl = np.array([classe(e) for e in ex]); EPO = np.flatnonzero(t < 32) if A.epoca == 'primerencs' else np.flatnonzero(t > 80)
Dr = np.zeros((len(fr), npx), np.float32); V = np.zeros_like(Dr); W = np.zeros_like(Dr)
for j in range(len(fr)):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[sec] + DR - np.interp(pa, pag, eg, period=360)
    w = np.asarray(Wt[j, :, :, A.canal])[sec]; n = np.asarray(N[j, :, :, A.canal])[sec]; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j] = w
jj, pp = np.nonzero((W[EPO] > 0) & np.isfinite(V[EPO]) & (V[EPO] > 0) & (Dr[EPO] >= DMIN_OBS)); jf = EPO[jj]
lv = np.log(V[jf, pp]).astype(np.float64); Do = Dr[jf, pp].astype(np.float64); ko = cl[jf]; wo = np.sqrt(np.sqrt(W[jf, pp].astype(np.float64)))   # √ del pes (desviació ∝ 1/√pes)
DB = np.arange(DMIN_OBS, A.ancora + 1e-9, 0.25); nD = DB.size; ib = np.clip(np.digitize(Do, DB) - 1, 0, nD - 1); anc = Do >= A.ancora
# columnes: [lnC (npx)] [lnT classe k, calaix i (3·nD)] [ln g mitjans, ln g llargs]
nobs = lv.size; cols_C = pp; rows = np.arange(nobs)
colT = npx + ko * nD + ib; usaT = ~anc
nT = np.bincount(ko[usaT] * nD + ib[usaT], minlength=3 * nD); valT = nT >= 40     # calaixos amb prou dada
usaT &= valT[ko * nD + ib]
colg = npx + 3 * nD + (ko - 1); usag = ko > 0
R_ = np.concatenate([rows, rows[usaT], rows[usag]]); C_ = np.concatenate([cols_C, colT[usaT], colg[usag]]); D_ = np.concatenate([wo, wo[usaT], wo[usag]])
M = csr_matrix((D_, (R_, C_)), shape=(nobs, npx + 3 * nD + 2)); b = wo * lv
sol = lsqr(M, b, atol=1e-10, btol=1e-10, iter_lim=4000)[0]
lnC = sol[:npx]; lnT = sol[npx:npx + 3 * nD].reshape(3, nD); lng = np.concatenate([[0.0], sol[npx + 3 * nD:]]); lnT[~valT.reshape(3, nD)] = np.nan
noms = ['curts', 'mitjans', 'llargs']
print(f'sector {A.pa0:.0f}–{A.pa1:.0f} canal {"RGB"[A.canal]} època {A.epoca} ancora {A.ancora} · ln g mitjans {lng[1]:+.4f} llargs {lng[2]:+.4f} · obs {nobs}')
for k in range(3): print(' ', noms[k].ljust(7), ' '.join(f'{DB[i]:.1f}:{lnT[k, i]:+.3f}' for i in range(0, min(nD, 34), 2) if np.isfinite(lnT[k, i])))
rep = dict(sector=[A.pa0, A.pa1], canal='RGB'[A.canal], epoca=A.epoca, ancora=A.ancora, D=DB.round(2).tolist(), ln_guany=dict(mitjans=float(lng[1]), llargs=float(lng[2])),
           lnT={noms[k]: [None if not np.isfinite(v) else round(float(v), 4) for v in lnT[k]] for k in range(3)})
if A.validar:
    oth = np.flatnonzero(t > 40) if A.epoca == 'primerencs' else np.flatnonzero(t < 70)
    mv = (Dr[oth] >= 12) & (W[oth] > 0) & np.isfinite(V[oth]) & (V[oth] > 0)
    ver = np.where(mv, W[oth] * V[oth], 0).sum(0) / np.maximum(np.where(mv, W[oth], 0).sum(0), 1e-30); okv = (mv.sum(0) >= 3) & (ver > 0)
    Tfill = np.where(np.isfinite(lnT), lnT, 0.0); res = {}
    for nomv, useT in (('amb_KLL', True), ('sense_correccio', False)):
        m = Do >= 1.0; corr = (lng[ko] + np.where(anc, 0.0, Tfill[ko, ib])) if useT else np.zeros_like(lv)
        ww = wo[m] ** 2; lc = np.bincount(pp[m], weights=ww * (lv[m] - corr[m]), minlength=npx) / np.maximum(np.bincount(pp[m], weights=ww, minlength=npx), 1e-30)
        has = np.bincount(pp[m], minlength=npx) > 0; Dmax = np.full(npx, -9.0); np.maximum.at(Dmax, pp[m], Do[m])
        ok = has & okv; lr = lc - np.log(np.maximum(ver, 1e-30)); ref = ok & (Dmax >= A.ancora + 2) & (Dmax < A.ancora + 20)
        if ref.sum() < 100: print('  sense referència'); break
        r0 = np.median(lr[ref]); row = {}
        for lo in np.arange(1.0, 10.01, 0.5):
            z = ok & (Dmax >= lo) & (Dmax < lo + 0.5)
            if z.sum() >= 60: row[f'{lo:.1f}'] = round(float(np.median(lr[z]) - r0), 4)
        res[nomv] = row; print('  VALIDACIÓ', nomv, ' '.join(f'{k}:{v:+.3f}' for k, v in row.items()))
    rep['validacio'] = res
tag = f'{int(A.pa0)}_{int(A.pa1)}_{"RGB"[A.canal]}_{A.epoca}'
(O / f'KLL2_{tag}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
if A.desa: np.savez(O / f'KLL2_{tag}.npz', D=DB, lnT=lnT, lng=lng)
