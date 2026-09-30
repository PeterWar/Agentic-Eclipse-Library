"""d37 (V100 detall; 2a versió: regressió ROBUSTA) · El mapa de contrast k(PA, dd) de la capa de detall: que la banda mostri el detall real AMB EL MATEIX PENDENT que el compost
natiu el mostra just a fora (β_ref, per sector, d36), ni més ni menys. Amb el render de prova (k = 1) i el de la V99 (sense capa):
γ = (β_prova − β_V99)/1 (resposta del compost per unitat de capa: Superposar + capes d'ajust de Pere), per PA (15°, finestra de 30°) i distància a la vora
de dada de la V99 (dd, calaixos de 0,5 px); k = max(0, (β_ref(PA) − β_V99(PA, dd)) / γ(PA, dd)), suavitzat (PA σ 15°, dd σ 0,5 px) i acotat a [0, 3].
Sortida: CAPA_DETALL_BANDA_K.npz (delta ja multiplicat per k; alfa; kmapa) per a b2_munta_v100.py amb k = 1."""
import json
from pathlib import Path
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d, gaussian_filter
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
Z = np.load(O / 'CAPA_DETALL_BANDA.npz'); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); DMIN9 = np.maximum(Q9['DMIN'], 0); NBZ = DMIN9.size
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 16.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); Xp = LX + R_ * np.cos(T_); Yp = LY - R_ * np.sin(T_); ox, oy = 4600, 3000
def ctang(tif):
    T = tifffile.imread(tif)[..., :3].astype(np.float64); Lc = np.log(np.maximum((T[..., 0] + 2 * T[..., 1] + T[..., 2]) / 4, 1))
    c = cv2.remap(Lc.astype(np.float32), (Xp - ox).astype(np.float32), (Yp - oy).astype(np.float32), cv2.INTER_LINEAR); return c - gaussian_filter1d(c, 8 / DS_, axis=1, mode='wrap')
c99 = ctang(R9 / 'vistes/V99_lluna.tif'); cpr = ctang(O / 'prova/vistes/V100_lluna.tif')
dl = cv2.remap(Z['delta'].astype(np.float32), (Xp - bx0).astype(np.float32), (Yp - by0).astype(np.float32), cv2.INTER_LINEAR)
al = cv2.remap(Z['alfa'].astype(np.float32), (Xp - bx0).astype(np.float32), (Yp - by0).astype(np.float32), cv2.INTER_LINEAR)
thp = np.degrees(tt); dm = DMIN9[(thp / 360 * NBZ).astype(int) % NBZ][None, :]; dd = rr[:, None] - dm
PAB = np.arange(0, 360, 15); DDB = np.array([-4.0, -0.5])   # dues zones: dins de la banda (dd < −0,5) i transició (−0,5 … 2)
DDW = {-4.0: (-4.0, -0.5), -0.5: (-0.5, 2.0)}
bref = np.full(PAB.size, np.nan); b99 = np.full((PAB.size, DDB.size), np.nan); gam = np.full_like(b99, np.nan)
SAT = None
def beta(x, y):   # mínims quadrats retallats: sense |δ| > 2,5σ_MAD ni residus > 3σ_MAD (protuberàncies, saturació)
    if x.size < 150: return np.nan
    sx = 1.4826 * np.median(np.abs(x - np.median(x))) + 1e-9; m = np.abs(x) < 2.5 * sx
    if m.sum() < 120: return np.nan
    b = np.sum(x[m] * y[m]) / np.sum(x[m] ** 2)
    for _ in range(3):
        r = y - b * x; sr = 1.4826 * np.median(np.abs(r[m])) + 1e-9; mm = m & (np.abs(r) < 3 * sr)
        if mm.sum() < 120: break
        b = np.sum(x[mm] * y[mm]) / np.sum(x[mm] ** 2)
    return float(b)
for i, a in enumerate(PAB):
    sel = ((((thp - a + 180) % 360) - 180) ** 2 < 15 ** 2)[None, :]; nosat = (cpr < 1e9)
    z = sel & (dd >= 2) & (dd < 7) & (np.abs(dl) > 0); bref[i] = beta(dl[z], c99[z])
    for j, lo in enumerate(DDB):
        z = sel & (dd >= DDW[lo][0]) & (dd < DDW[lo][1]) & (al > 0.05) & (np.abs(dl) > 0)
        b99[i, j] = beta(dl[z], c99[z]); bp = beta(dl[z], cpr[z]); gam[i, j] = bp - b99[i, j]
kk = (bref[:, None] - b99) / np.where(gam > 0.1, gam, np.nan); kk = np.clip(kk, 0, 3)
INTERIORS = (PAB >= 135) & (PAB <= 210); kk[INTERIORS] = np.nan    # allà manen les capes d'interiors de Pere (76, 96): k dels veïns
ok = np.isfinite(kk); kf = np.where(ok, kk, 0); w = ok.astype(float)
ks = gaussian_filter(kf, (1.0, 0.0), mode=('wrap', 'nearest')) / np.maximum(gaussian_filter(w, (1.0, 0.0), mode=('wrap', 'nearest')), 1e-6)
ks = np.where(gaussian_filter(w, (1.0, 0.0), mode=('wrap', 'nearest')) > 0.05, ks, np.nan)
for jj in range(ks.shape[1]):
    c_ = ks[:, jj]; f_ = np.isfinite(c_)
    if f_.any() and not f_.all(): ks[:, jj] = np.interp(PAB, PAB[f_], c_[f_], period=360)
# omple els calaixos sense estimació amb la mitjana del PA (i si cal, la global) — només per a píxels on la capa té alfa
fila = np.nanmean(ks, axis=1); glob = np.nanmedian(ks); fila = np.where(np.isfinite(fila), fila, glob); ks = np.where(np.isfinite(ks), ks, fila[:, None])
# a cartesià
yy, xx = np.mgrid[by0:by1, bx0:bx1]; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360; d = np.hypot(xx - LX, yy - LY) - RL
ddC = d - DMIN9[(th / 360 * NBZ).astype(int) % NBZ]
ia = th / 15.0; jd = np.clip((ddC + 0.5) / 1.5 + 0.5, 0, 1)   # rampa entre les dues zones (centre −2,25 i 0,75)
kext = np.concatenate([ks, ks[:1]], 0)   # periodicitat en PA
kC = cv2.remap(kext.astype(np.float32), jd.astype(np.float32), ia.astype(np.float32), cv2.INTER_LINEAR)
dk = (Z['delta'] * kC).astype(np.float32)
np.savez_compressed(O / 'CAPA_DETALL_BANDA_K.npz', box=Z['box'], delta=dk, alfa=Z['alfa'], kmapa=kC.astype(np.float32))
rep = dict(beta_V99_zones={int(a): [None if not np.isfinite(v) else round(float(v), 3) for v in b99[i]] for i, a in enumerate(PAB)}, gamma_zones={int(a): [None if not np.isfinite(v) else round(float(v), 3) for v in gam[i]] for i, a in enumerate(PAB)}, beta_ref={int(a): None if not np.isfinite(b) else round(float(b), 3) for a, b in zip(PAB, bref)},
           k_zones={int(a): [round(float(v), 3) for v in ks[i]] for i, a in enumerate(PAB)}, zones_dd=[[-4.0, -0.5], [-0.5, 2.0]])
(O / 'D37_MAPA_K.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); [print(a, 'β_ref', rep['beta_ref'][a], 'β99', rep['beta_V99_zones'][a], 'γ', rep['gamma_zones'][a], 'k', rep['k_zones'][a]) for a in rep['beta_ref']]
