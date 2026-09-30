"""HALO, segona peça (19-08-2026, tarda): treure la component azimutalment UNIFORME de la llum de
corona+aurèola de 3,2 a 5,5 R☉ i mapar-ho amb una corba sense terra (vegeu corba_halo.py per al
diagnòstic del genoll).

Mesura: l'excés de L sobre el cel (L − 305) a 4–9 R☉ val 1,9e-9 B☉ a 5 R☉ i 8e-10 a 8 R☉ (factor
2,77e-11 B☉ per ADU/s, research/75): és la corona K+F real (±50 %), no un artefacte. La corba de Pere
la pinta com un halo gris-blanc damunt d'un cel blau. Eliminar-lo = restar la part uniforme en L
(el que fan LASCO i els filtres radials de Brno), conservant l'estructura (raigs) i amb una corba
quasi lineal prop del cel perquè els raigs no desapareguin al terra.

    p(r)   = mediana azimutal de L_model; cel = mediana p(r > 9,5 R☉)
    A(r)   = w(r)·(p(r) − cel), w = smootherstep((r − R1)/(R2 − R1))   (C2: cap colze)
    S_c(L) = D_c per a L ≥ LHI; Hermite monòton entre L0 i LHI amb pendent = corda al terra (M0F=1)
    Δ_c    = S_c(L − A(r)) − D_c(L)                                      per píxel, additiu

Sortides a FD3_SCR/halo/: uniform_delta.npy, QA. Variables: HU_R1 (3.2), HU_R2 (5.5), HALO_L0, HALO_LHI, HALO_M0 (1.0).
"""
import os, sys, json, math, time
import numpy as np, cv2
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo')
W, H = 7648, 5353
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
R1 = float(os.environ.get('HU_R1', 3.2)); R2 = float(os.environ.get('HU_R2', 5.5))
L0 = float(os.environ.get('HALO_L0', 310.0)); LHI = float(os.environ.get('HALO_LHI', 440.0)); M0F = float(os.environ.get('HALO_M0', 1.0))
TAG = os.environ.get('HU_TAG', 'v1')
Q_ENV = float(os.environ.get('HU_Q', 25.0))      # percentil per anell de l'envolupant inferior que es resta (25 = quartil baix)
K_SOFT = float(os.environ.get('HU_K', 6.0))      # ADU/s: asímptota del retall suau per sota del cel
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)
def redueix(a, f):
    h, w = a.shape[:2]; h2, w2 = h // f * f, w // f * f; a = a[:h2, :w2]
    if a.ndim == 3: return a.reshape(h2 // f, f, w2 // f, f, a.shape[2]).mean(axis=(1, 3), dtype=np.float32)
    return a.reshape(h2 // f, f, w2 // f, f).mean(axis=(1, 3), dtype=np.float32)
def jpg(path, a01, q=88):
    a8 = np.clip(np.rint(np.asarray(a01) * 255), 0, 255).astype(np.uint8)
    if a8.ndim == 3: a8 = a8[..., ::-1]
    cv2.imwrite(path, a8, [cv2.IMWRITE_JPEG_QUALITY, q])
def smootherstep(t):
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)
def mediana_anells(img, rr, dr, ok=None, r_min=0.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1)
    sel = np.ones(rr.shape, bool) if ok is None else ok.copy()
    sel &= rr >= r_min
    v = img[sel]; ii = idx[sel]
    order = np.argsort(ii, kind='stable'); v = v[order]; ii = ii[order]
    b = np.searchsorted(ii, np.arange(n + 1))
    med = np.full(n, np.nan, np.float32)
    for k in range(n):
        if b[k + 1] - b[k] >= 30: med[k] = np.median(v[b[k]:b[k + 1]])
    return (np.arange(n) + 0.5) * dr, med

yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
Lm = np.load(os.path.join(HO, 'L_model.npy')); vc = np.load(os.path.join(HO, 'valid_eros.npy'))
cj = json.load(open(os.path.join(HO, 'corba_D.json')))
cent = np.array(cj['cent']); Ds = np.array(cj['Ds'])
log('carregat')

# ------------------------------------------------------------------ p(r), cel, A(r)
def percentil_anells(img, rr, dr, q, ok=None, r_min=0.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1)
    sel = np.ones(rr.shape, bool) if ok is None else ok.copy(); sel &= rr >= r_min
    v = img[sel]; ii = idx[sel]
    order = np.argsort(ii, kind='stable'); v = v[order]; ii = ii[order]
    b = np.searchsorted(ii, np.arange(n + 1))
    out = np.full(n, np.nan, np.float32)
    for k in range(n):
        if b[k + 1] - b[k] >= 30: out[k] = np.percentile(v[b[k]:b[k + 1]], q)
    return (np.arange(n) + 0.5) * dr, out
# envolupant inferior p_Q fins a 6,5 R☉; de 6,5 a 8,5 passa a la mediana (p50) perquè el camp llunyà
# quedi exactament al nivell del cel (i no 7 ADU/s per sobre dels cantons)
r_c, medq = percentil_anells(Lm, rr, 4.0, Q_ENV, ok=vc, r_min=1.2 * R_SOL)
r_c, med5 = percentil_anells(Lm, rr, 4.0, 50.0, ok=vc, r_min=1.2 * R_SOL)
def neteja(m):
    okk = np.isfinite(m); y = np.interp(r_c, r_c[okk], m[okk]).astype(np.float32)
    return cv2.GaussianBlur(y.reshape(1, -1), (0, 0), 3.0, borderType=cv2.BORDER_REPLICATE).ravel()
pq = neteja(medq); p5 = neteja(med5)
vq = smootherstep((r_c - 6.5 * R_SOL) / (2.0 * R_SOL))
p_s = ((1 - vq) * pq + vq * p5).astype(np.float32)
cel = float(np.median(Lm[vc & (rr > 9.5 * R_SOL)]))
exc = np.maximum(p_s - cel, 0.0)
log(f'envolupant p{Q_ENV:.0f} per anell (→ p50 de 6,5 a 8,5 R☉); cel {cel:.1f}')
w_r = smootherstep((r_c - R1 * R_SOL) / ((R2 - R1) * R_SOL))
A_r = (w_r * exc).astype(np.float32)
A = np.interp(rr, r_c, A_r).astype(np.float32)
log(f'cel {cel:.1f}; excés p−cel a 3/3.5/4/5/6/7/8/9 R☉:', [round(float(np.interp(R * R_SOL, r_c, exc)), 1) for R in (3, 3.5, 4, 5, 6, 7, 8, 9)])
log('A(r) a 3/3.5/4/4.5/5/5.5/6/8 R☉:', [round(float(np.interp(R * R_SOL, r_c, A_r)), 1) for R in (3, 3.5, 4, 4.5, 5, 5.5, 6, 8)])

# ------------------------------------------------------------------ corba S_c (pendent de corda al terra)
def D_at(c, L): return float(np.interp(L, cent, Ds[:, c]))
def D_slope(c, L, h=8.0): return (D_at(c, L + h) - D_at(c, L - h)) / (2 * h)
S = Ds.copy(); info = {}
for c in range(3):
    F = D_at(c, 306.0)
    y1 = D_at(c, LHI); m1 = D_slope(c, LHI); delta = (y1 - F) / (LHI - L0)
    m0 = M0F * delta; m1c = min(max(m1, 0.0), 3 * delta)
    tt = (cent - L0) / (LHI - L0)
    h00 = 2 * tt**3 - 3 * tt**2 + 1; h10 = tt**3 - 2 * tt**2 + tt; h01 = -2 * tt**3 + 3 * tt**2; h11 = tt**3 - tt**2
    herm = h00 * F + h10 * (LHI - L0) * m0 + h01 * y1 + h11 * (LHI - L0) * m1c
    # per sota de L0: continuació lineal amb el pendent m0 (cap terra: els raigs no moren)
    S[:, c] = np.where(cent <= L0, F + m0 * (cent - L0), np.where(cent >= LHI, Ds[:, c], herm))
    info[c] = dict(terra=F, pendent_terra=m0, y_hi=y1, pendent_hi=m1c, corda=delta)
    log(f'canal {c}: terra {F:.4f}, pendent al terra {m0*10:+.5f}/10, D({LHI:.0f})={y1:.4f}, pendent {m1c*10:+.5f}/10')
np.save(os.path.join(HO, f'uniform_S_{TAG}.npy'), S)

# ------------------------------------------------------------------ Δ per píxel
x = Lm - A - cel
Lp = (cel + np.where(x >= 0, x, -K_SOFT * (1.0 - np.exp(np.minimum(x, 0) / K_SOFT)))).astype(np.float32)   # retall suau: mai per sota de cel − K_SOFT
del x
delta = np.empty((H, W, 3), np.float32)
for c in range(3):
    delta[..., c] = (np.interp(Lp, cent, S[:, c]) - np.interp(Lm, cent, Ds[:, c], left=Ds[0, c], right=Ds[-1, c])).astype(np.float32)
delta *= (rr > 2.6 * R_SOL)[..., None]
# ------------------------------------------------------------------ 1) saturació suau al terra per canal: cap píxel baixa del cel;
# els que Pere ja tenia per sota (el sud fosc) no es toquen
bc = np.load(os.path.join(SCR, 'capes3', 'Base_corregida_camp.npy'), mmap_mode='r')
def satura(delta_c, V, F):
    a = np.maximum(V - F, 0.0)
    neg = np.where(a > 1e-6, -a * (1.0 - np.exp(-np.abs(delta_c) / np.maximum(a, 1e-6))), 0.0)
    d2 = np.where(delta_c < 0, neg, delta_c).astype(np.float32)
    wz = smootherstep((rr - 3.0 * R_SOL) / (0.6 * R_SOL))
    return ((1 - wz) * delta_c + wz * d2).astype(np.float32)
for c in range(3):
    V = np.asarray(bc[..., c], np.float32) / 65535.0
    delta[..., c] = satura(delta[..., c], V, float(info[c]['terra']))
    del V
# ------------------------------------------------------------------ 2) terme radial: la mediana per anell (DESPRÉS de saturar) cau
# sobre l'objectiu S_c(L_t), amb L_t = cel + (1 − w_t)·(p50 − cel): el resplendor mitjà se'n va del tot cap a R2+0,5
# (per píxel es resta l'envolupant p_Q, que és més baixa, perquè l'estructura quedi positiva i les llacunes al cel)
r_c5, med5b = percentil_anells(Lm, rr, 4.0, 50.0, ok=vc, r_min=1.2 * R_SOL)
ok5 = np.isfinite(med5b); p50 = np.interp(r_c, r_c5[ok5], med5b[ok5]).astype(np.float32)
p50 = cv2.GaussianBlur(p50.reshape(1, -1), (0, 0), 3.0, borderType=cv2.BORDER_REPLICATE).ravel()
w_t = smootherstep((r_c - R1 * R_SOL) / ((R2 + 0.5 - R1) * R_SOL))
Lt = (cel + (1.0 - w_t) * np.maximum(p50 - cel, 0.0)).astype(np.float32)
ramp_in = smootherstep((r_c - 3.0 * R_SOL) / (0.8 * R_SOL))
rho_all = []
for c in range(3):
    V = np.asarray(bc[..., c], np.float32) / 65535.0
    nou = V + delta[..., c]
    r_c3, med3 = mediana_anells(nou, rr, 4.0, ok=vc, r_min=1.2 * R_SOL)
    ok3 = np.isfinite(med3)
    medi = np.interp(r_c, r_c3[ok3], med3[ok3])
    target = np.interp(Lt, cent, S[:, c])
    rho = (target - medi) * ramp_in
    rho = cv2.GaussianBlur(rho.reshape(1, -1).astype(np.float32), (0, 0), 3.0, borderType=cv2.BORDER_REPLICATE).ravel()
    rho[r_c > 11.0 * R_SOL] = 0.0
    rho_all.append(rho)
    delta[..., c] += np.interp(rr, r_c, rho).astype(np.float32) * (rr > 2.6 * R_SOL)
    # 3) segona saturació (el terme radial negatiu podria tornar a baixar del terra)
    delta[..., c] = satura(delta[..., c], V, float(info[c]['terra']))
    log(f'   terme radial canal {c}: rho a 3.5/4/5/5.5/6/7/8/9 R☉:', [round(float(np.interp(R * R_SOL, r_c, rho)), 4) for R in (3.5, 4, 5, 5.5, 6, 7, 8, 9)])
    del V, nou
log('saturació + terme radial fets; percentils 1/50/99 de Δ (r 3-6R):', [np.round(np.percentile(delta[..., c][(rr > 3 * R_SOL) & (rr < 6 * R_SOL)], [1, 50, 99]), 4).tolist() for c in range(3)])
np.save(os.path.join(HO, f'uniform_delta_{TAG}.npy'), delta)
log('Δ fet; percentils 1/50/99 (r 3–6R):', [np.round(np.percentile(delta[..., c][(rr > 3 * R_SOL) & (rr < 6 * R_SOL)], [1, 50, 99]), 4).tolist() for c in range(3)])
json.dump(dict(Q_ENV=Q_ENV, K_SOFT=K_SOFT, R1=R1, R2=R2, L0=L0, LHI=LHI, M0F=M0F, cel=cel, r_c=r_c.tolist(), p=p_s.tolist(), A=A_r.tolist(), S=S.tolist(), info=info, rho=[r.tolist() for r in rho_all]),
          open(os.path.join(HO, f'uniform_{TAG}.json'), 'w'))

# ------------------------------------------------------------------ QA
b2 = redueix(bc, 2) / 65535.0; d2 = redueix(delta, 2); rr2 = redueix(rr, 2)
a2 = np.clip(b2 + d2, 0, 1)
np.save(os.path.join(HO, f'base_uniform_{TAG}_x2.npy'), a2.astype(np.float32))
lines = [f'{TAG}: R1={R1} R2={R2} L0={L0} LHI={LHI} M0F={M0F}']
for nom, im in (('abans', b2), ('despres', a2)):
    lines.append(nom + '  (perfil per canal d 1,2 a 10,4 R cada 0,2)')
    for c in range(3):
        r_c2, med2 = mediana_anells(im[..., c], rr2, 4.0, r_min=R_SOL)
        ok2 = np.isfinite(med2)
        prof = np.interp(np.arange(1.2, 10.6, 0.2) * R_SOL, r_c2[ok2], med2[ok2])
        lines.append(f'  canal {c}: ' + ' '.join(f'{v:.4f}' for v in prof))
# contrast dels raigs: desviació estàndard azimutal de la luminància per anell (estructura) abans/després
th2 = np.arctan2(np.arange(a2.shape[0])[:, None] * 2 + 0.5 - SOL[1], np.arange(a2.shape[1])[None, :] * 2 + 0.5 - SOL[0])
for nom, im in (('abans', b2), ('despres', a2)):
    lum = im.mean(-1); s = []
    for R in (3.5, 4, 4.5, 5, 5.5, 6, 7):
        sel = (rr2 > (R - 0.1) * R_SOL) & (rr2 < (R + 0.1) * R_SOL)
        v = lum[sel]; s.append(f'{R}R σ={np.std(v):.4f} p5-95={np.percentile(v,95)-np.percentile(v,5):.4f}')
    lines.append(nom + ' estructura azimutal: ' + '; '.join(s))
open(os.path.join(HO, f'qa_uniform_{TAG}.txt'), 'w').write('\n'.join(lines)); print('\n'.join(lines))
jpg(os.path.join(HO, f'uniform_{TAG}_despres_x4.jpg'), redueix(np.clip(a2, 0, 1) ** 0.5, 2))
lo, hi = 0.06, 0.30
jpg(os.path.join(HO, f'uniform_{TAG}_despres_estirat_x4.jpg'), redueix(np.clip((a2 - lo) / (hi - lo), 0, 1) ** 0.6, 2))
# polar de luminància
NA, NR = 1440, 2450
th = (2 * math.pi * np.arange(NA) / NA)[:, None]; r = np.arange(NR)[None, :].astype(np.float32)
mx = (SOL[0] / 2 - 0.25 + r * np.cos(th)).astype(np.float32); my = (SOL[1] / 2 - 0.25 + r * np.sin(th)).astype(np.float32)
pol = cv2.remap(np.ascontiguousarray(a2.mean(-1)), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
img = np.clip((pol - 0.10) / 0.20, 0, 1) ** 0.7
img = cv2.resize(img, (NR // 2, NA // 2), interpolation=cv2.INTER_AREA); img = np.repeat(img[..., None], 3, -1)
for k in range(1, 12):
    x_ = int(k * R_SOL / 4)
    if x_ < img.shape[1]: img[:, x_, :] = [1, 0, 0]
jpg(os.path.join(HO, f'polar_lum_uniform_{TAG}.jpg'), img)
log('fi')
