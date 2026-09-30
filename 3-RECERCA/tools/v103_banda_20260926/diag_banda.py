"""Diagnòstic (només lectura): què hi ha als fotogrames de l'INSTANT de presentació (t 14,4–22,4 s, Lluna a ≤ 1,1 px) dins de la banda de 4 px
que la V99/V101 deixa sense dada al costat d'avanç de la Lluna. Compara amb la selecció a3c (V99 B). Sortida al scratchpad."""
import json, sys
from pathlib import Path
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d
ARREL = Path.home() / 'Desktop/Eclipse 2026'; OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL; T_PRES = 18.433
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def ss(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
d_pres = np.hypot(xx - LX, yy - LY) - RL - np.interp(th.ravel(), pag, eg, period=360).reshape(hb, wb)   # distància a la silueta REAL de presentació
def dreal(j):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = hb // 2, wb - 100
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; return Dj + DR - np.interp(pa.ravel(), pag, eg, period=360).reshape(hb, wb)
DT = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0; LO, HI = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.75, 1.75)
INST = [j for j in range(len(fr)) if abs(fr[j]['time'] - T_PRES) <= DT]
print('fotogrames de l\'instant:', [(fr[j]['name'][-8:-4], round(fr[j]['time'], 1), f"1/{1/fr[j]['exposure']:.0f}") for j in INST])
def apila(js, lo, hi, paritat=None):
    num = np.zeros((hb, wb, 3)); den = np.zeros((hb, wb, 3)); nf = np.zeros((hb, wb), np.int16)
    for i, j in enumerate(js):
        if paritat is not None and i % 2 != paritat: continue
        s = ss(dreal(j), lo, hi)
        for c in range(3):
            w = np.asarray(Wt[j, :, :, c], np.float64) * s; num[..., c] += np.asarray(N[j, :, :, c], np.float64) * s; den[..., c] += w
        nf += (den[..., 1] > 0) & (s > 0)
    E = np.where(den > 0, num / np.maximum(den, 1e-30), 0); E = np.einsum('ij,...j->...i', Mx, E * gn); return E.astype(np.float32), nf, den[..., 1]
E_i, NF_i, W_i = apila(INST, LO, HI); E_p, _, _ = apila(INST, LO, HI, 0); E_s, _, _ = apila(INST, LO, HI, 1)
A = np.load(R9 / 'B/lineal_v99_franja/A3C_franja_silueta.npz'); E_a = A['E']; dom_a = A['domini_E']
# ---- mesures per sector i calaix de d_pres
def dog_tang(lum, sector, r0, r1, DS=0.5):
    """detall tangencial: DoG 2→16 px al llarg de l'arc, en ln, per a un sector [a0,a1] i radis RL+r0..RL+r1 (pas 0,25 px)."""
    a0, a1 = sector; rr = np.arange(r0, r1, 0.25); tt = np.radians(np.arange(a0, a1, DS / RL * 180 / np.pi))
    R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); e_ = np.interp(np.degrees(T_).ravel() % 360, pag, eg, period=360).reshape(R_.shape)
    PX = (LX + (R_ + e_) * np.cos(T_) - bx0).astype(np.float32); PY = (LY - (R_ + e_) * np.sin(T_) - by0).astype(np.float32)
    P = cv2.remap(np.log(np.maximum(lum, 1e-6)).astype(np.float32), PX, PY, cv2.INTER_LINEAR)
    g2 = gaussian_filter1d(P, 2 / DS, axis=1, mode='nearest'); g16 = gaussian_filter1d(P, 16 / DS, axis=1, mode='nearest'); return rr, P, g2 - g16
SECTORS = {'dalt 60-130': (60, 130), 'dalt-esq 130-170': (130, 170), 'baix-esq 205-250': (205, 250), 'dreta 300-60 (control)': (300, 420)}
BINS = [(0.5, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 7), (7, 10)]
rep = {}
for nom, sec in SECTORS.items():
    rr, Pi, Di = dog_tang(E_i[..., 1], sec, 0.0, 12.0); _, Pp, Dp = dog_tang(np.maximum(E_p[..., 1], 1e-6), sec, 0.0, 12.0); _, Ps, Ds_ = dog_tang(np.maximum(E_s[..., 1], 1e-6), sec, 0.0, 12.0)
    _, Pa, Da = dog_tang(np.where(dom_a, E_a[..., 1], 0), sec, 0.0, 12.0)
    # cobertura de la instant stack (NF) i de l'a3c en polar
    a0, a1 = sec; tt = np.radians(np.arange(a0, a1, 0.5 / RL * 180 / np.pi)); R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); e_ = np.interp(np.degrees(T_).ravel() % 360, pag, eg, period=360).reshape(R_.shape)
    PX = (LX + (R_ + e_) * np.cos(T_) - bx0).astype(np.float32); PY = (LY - (R_ + e_) * np.sin(T_) - by0).astype(np.float32)
    NFp = cv2.remap(NF_i.astype(np.float32), PX, PY, cv2.INTER_NEAREST); DOMa = cv2.remap(dom_a.astype(np.float32), PX, PY, cv2.INTER_NEAREST)
    r = {}
    for lo, hi in BINS:
        m = (rr >= lo) & (rr < hi); ok = np.isfinite(Pi[m]) & (NFp[m] > 0)
        di, dp, ds = Di[m][ok], Dp[m][ok], Ds_[m][ok]
        rho = float(np.corrcoef(dp, ds)[0, 1]) if ok.sum() > 50 else None
        r[f'{lo}-{hi}'] = dict(px=int(ok.sum()), NF_p50=float(np.median(NFp[m][ok])) if ok.any() else None, cobertura_a3c=round(float(DOMa[m].mean()), 3),
                             nivell_ln_instant_menys_a3c=round(float(np.median((Pi[m] - Pa[m])[ok & (DOMa[m] > 0)])), 4) if (ok & (DOMa[m] > 0)).sum() > 50 else None,
                             detall_rms_instant=round(float(np.std(di)), 4) if ok.any() else None, detall_rms_a3c=round(float(np.std(Da[m][DOMa[m] > 0])), 4) if (DOMa[m] > 0).sum() > 50 else None,
                             rho_meitats_instant=round(rho, 3) if rho is not None else None)
    rep[nom] = r
json.dump(dict(instant=[fr[j]['name'] for j in INST], rampa=[LO, HI], sectors=rep), open(OUT / 'DIAG_BANDA.json', 'w'), indent=1, ensure_ascii=False)
for nom, r in rep.items():
    print('==', nom)
    for k, v in r.items(): print(f"  d {k:>6}: px {v['px']:6d} NF {v['NF_p50']} cob_a3c {v['cobertura_a3c']:.2f} nivell {v['nivell_ln_instant_menys_a3c']} rms_inst {v['detall_rms_instant']} rms_a3c {v['detall_rms_a3c']} rho_meitats {v['rho_meitats_instant']}")
# ---- làmines 4:1 (log, mateixa escala) de l'instant i de l'a3c, a dalt i a baix-esquerra
def crop(img, x0, y0, x1, y1): return img[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
def lam(img, lo, hi):
    l = np.log(np.maximum(img, 1e-6)); u = np.clip((l - lo) / (hi - lo), 0, 1); return (u * 255).astype(np.uint8)
caixes = {'dalt': (5150, 3290, 5600, 3400), 'dalt_esq': (4930, 3330, 5200, 3560), 'baix_esq': (4930, 4000, 5250, 4240)}
np.savez_compressed(OUT / 'E_instant.npz', E=E_i, NF=NF_i, W=W_i, box=np.array([by0, by1, bx0, bx1]))
for nom, (x0, y0, x1, y1) in caixes.items():
    a = crop(E_i[..., 1], x0, y0, x1, y1); b = crop(np.where(dom_a, E_a[..., 1], 0), x0, y0, x1, y1)
    ok = (b > 0); lo, hi = np.percentile(np.log(b[ok]), [1, 99.5])
    L = np.concatenate([lam(a, lo, hi), np.full((a.shape[0], 6), 128, np.uint8), lam(b, lo, hi)], axis=1)
    L = cv2.resize(L, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST); cv2.imwrite(str(OUT / f'LAM_{nom}_instant_vs_a3c_4a1.png'), L)
print('fet', OUT)
