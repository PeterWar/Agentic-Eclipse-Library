"""d31 (V100 detall) · AUTOCALIBRATGE de la transmissió de vora amb la redundància de la mateixa escena (Kuhn, Lin i Loranz 1991, PASP 103, 1097:
el pla de camp d'imatges desplaçades d'una escena estàtica, resolt només amb les imatges). Aquí l'escena estàtica és la corona C(x) i el «pla de
camp» és la transmissió de la Lluna que es mou, T_k(D_real), més el guany de cada classe d'exposició g_k (curts / mitjans / llargs).
Model: ln V_j(x) = ln C(x) + ln g_k(j) + ln T_k(j)(D_j(x)),  amb ln T = 0 a D_real ≥ D_ANCORA (6 px) i ln g_curts = 0.
Només els fotogrames d'UNA època (per defecte els primerencs, t < 32 s: els que veuen la banda) i els píxels d'UN sector (PA de la imatge).
Solució per mínims quadrats alternats (ponderats pel pes LDIC), T per calaixos de 0,25 px.
VALIDACIÓ a la dreta (PA 300–30, on la Lluna s'allunya i els tardans en donen la veritat): C corregida dels primerencs contra la veritat (tardans
amb D_real ≥ 9), biaix per calaix de D_real. Ús: d31_kll_autocalibratge.py <PA0> <PA1> <canal 0|1|2> [validar]. Sortida: JSON a 4-RESULTATS/v100_detall_20260925/kll/."""
import json, sys
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925/kll'; O.mkdir(parents=True, exist_ok=True)
PA0, PA1, CH = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); VALIDA = len(sys.argv) > 4
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL; D_ANCORA = 6.0; DMIN_OBS = 0.5
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
sec = (((th - PA0) % 360) < ((PA1 - PA0) % 360)) & (d >= -3) & (d < 30); X = xx[sec].astype(np.float64); Y = yy[sec].astype(np.float64); dsec = d[sec]; npx = int(sec.sum())
t = np.array([f['time'] for f in fr]); ex = np.array([f['exposure'] for f in fr])
def classe(e): return 0 if e <= 1 / 800 else (1 if e <= 1 / 50 else 2)
cl = np.array([classe(e) for e in ex]); EPO = np.flatnonzero(t < 32)
Dr = np.zeros((len(fr), npx), np.float32); V = np.zeros_like(Dr); W = np.zeros_like(Dr)
for j in range(len(fr)):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360; Dr[j] = Dj[sec] + DR - np.interp(pa, pag, eg, period=360)
    w = np.asarray(Wt[j, :, :, CH])[sec]; n = np.asarray(N[j, :, :, CH])[sec]; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); W[j] = w
# observacions de l'època
jj, pp = np.nonzero((W[EPO] > 0) & np.isfinite(V[EPO]) & (V[EPO] > 0) & (Dr[EPO] >= DMIN_OBS)); jf = EPO[jj]
lv = np.log(V[jf, pp]).astype(np.float64); Do = Dr[jf, pp].astype(np.float64); ko = cl[jf]; wo = np.sqrt(W[jf, pp]).astype(np.float64)   # pes ∝ √LDIC (robust)
DB = np.arange(DMIN_OBS, D_ANCORA + 1e-9, 0.25); ib = np.clip(np.digitize(Do, DB) - 1, 0, DB.size - 1); ancora = Do >= D_ANCORA
lnT = np.zeros((3, DB.size)); lng = np.zeros(3); lnC = np.zeros(npx)
for it in range(40):
    corr = lng[ko] + np.where(ancora, 0.0, lnT[ko, ib])
    lnC = np.bincount(pp, weights=wo * (lv - corr), minlength=npx) / np.maximum(np.bincount(pp, weights=wo, minlength=npx), 1e-30)
    r = lv - lnC[pp]
    for k in (1, 2):
        m = (ko == k) & ancora
        if m.sum() > 100: lng[k] = np.sum(wo[m] * (r[m] - lnT[k, ib[m]] * 0)) / np.sum(wo[m])
    for k in range(3):
        m = (ko == k) & ~ancora
        if m.sum() == 0: continue
        num = np.bincount(ib[m], weights=wo[m] * (r[m] - lng[k]), minlength=DB.size); den = np.bincount(ib[m], weights=wo[m], minlength=DB.size)
        nn = np.bincount(ib[m], minlength=DB.size); lnT[k] = np.where(nn >= 50, num / np.maximum(den, 1e-30), lnT[k])
rep = dict(sector=[PA0, PA1], canal='RGB'[CH], fotogrames=[int(j) for j in EPO], D=DB.round(2).tolist(),
           lnT={['curts', 'mitjans', 'llargs'][k]: [round(float(v), 4) for v in lnT[k]] for k in range(3)}, ln_guany={'mitjans': round(float(lng[1]), 4), 'llargs': round(float(lng[2]), 4)},
           n_obs={['curts', 'mitjans', 'llargs'][k]: np.bincount(ib[(ko == k) & ~ancora], minlength=DB.size).tolist() for k in range(3)})
print('sector', PA0, PA1, 'canal', 'RGB'[CH], 'ln g (mitjans, llargs):', rep['ln_guany'])
for k, nom in enumerate(['curts', 'mitjans', 'llargs']): print(' ', nom, ' '.join(f'{DB[i]:.2f}:{lnT[k, i]:+.3f}' for i in range(0, DB.size, 2)))
if VALIDA:   # veritat: tardans amb D_real ≥ 9; C corregida dels primerencs (mitjana ponderada de ln V − ln g − ln T, només D_real ≥ 1)
    LAT = np.flatnonzero(t > 40); mv = (Dr[LAT] >= 9) & (W[LAT] > 0) & np.isfinite(V[LAT]) & (V[LAT] > 0)
    ver = np.where(mv, W[LAT] * V[LAT], 0).sum(0) / np.maximum(np.where(mv, W[LAT], 0).sum(0), 1e-30); okv = (mv.sum(0) >= 3) & (ver > 0)
    res = {}
    for nomv, useT in (('amb_KLL', True), ('sense_correccio', False)):
        m = Do >= 1.0; corr = (lng[ko] + np.where(ancora, 0.0, lnT[ko, ib])) if useT else np.zeros_like(lv)
        lc = np.bincount(pp[m], weights=wo[m] * (lv[m] - corr[m]), minlength=npx) / np.maximum(np.bincount(pp[m], weights=wo[m], minlength=npx), 1e-30)
        has = np.bincount(pp[m], minlength=npx) > 0; Dmax = np.full(npx, -9.0); np.maximum.at(Dmax, pp[m], Do[m])
        ok = has & okv; lr = lc - np.log(np.maximum(ver, 1e-30)); ref = ok & (Dmax >= 12) & (Dmax < 25); r0 = np.median(lr[ref]); row = {}
        for lo in np.arange(1.0, 8.01, 0.5):
            z = ok & (Dmax >= lo) & (Dmax < lo + 0.5)
            if z.sum() >= 60: row[f'{lo:.1f}'] = round(float(np.median(lr[z]) - r0), 4)
        res[nomv] = row; print('  VALIDACIÓ', nomv, ' '.join(f'{k}:{v:+.3f}' for k, v in row.items()))
    rep['validacio_contra_veritat'] = res
(O / f'KLL_{int(PA0)}_{int(PA1)}_{"RGB"[CH]}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
