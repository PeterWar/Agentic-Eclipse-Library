"""Correcció del HALO per corba de to (19-08-2026, migdia).

Diagnòstic: el halo de 3,5–5,6 R☉ de la base de Pere no és llum mal restada, és un GENOLL de la corba
de to per canal contra la lluminància física L (L_c − pla del cel, `flat_camp.py`): el blau té un
terra dur (0,197) per a L < 356 (r > 5,6 R☉), un tram dret entre 356 i 382 (r 5,6→4,3 R☉) i un
pendent suau més amunt; el verd el mateix amb el terra a L = 330. Un anell blau-blanc que s'acaba de
cop al terra = halo.

Correcció: per canal, corba mediana D_c(L) mesurada sobre la base ja corregida de camp; corba
objectiu S_c(L) = D_c per a L ≥ L_HI, i entre L0 (terra) i L_HI un Hermite cúbic monòton (valor del
terra i pendent 0 a L0; valor i pendent de D_c a L_HI). Desplaçament additiu per píxel
Δ_c = S_c(L) − D_c(L) avaluat amb la L física del píxel: depèn només de L, o sigui que no pot
crear cap anell, conserva l'estructura (additiu) i el color dels cantons (el terra no es mou).

Sortides a FD3_SCR/halo/: L_model.npy, corba_D.json, corba_delta.npy (H,W,3 float32), QA jpg/txt.
Variables: HALO_L0 (310), HALO_LHI (440), HALO_M0 (pendent al terra en fracció de la corda, 0.0).
"""
import os, sys, json, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import smooth01

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
LUM = os.environ.get('FD3_LUM', os.path.join(SCR, '..', 'treball', 'lum_llenc.npz'))
HO = os.path.join(SCR, 'halo'); os.makedirs(HO, exist_ok=True)
W, H = 7648, 5353
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
L0 = float(os.environ.get('HALO_L0', 310.0)); LHI = float(os.environ.get('HALO_LHI', 440.0)); M0F = float(os.environ.get('HALO_M0', 0.0))
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)
def gauss(a, s): return cv2.GaussianBlur(np.ascontiguousarray(a, np.float32), (0, 0), s, borderType=cv2.BORDER_REPLICATE)
def gauss_n(a, m, s): return gauss(a * m, s) / np.maximum(gauss(m, s), 1e-4)
def redueix(a, f):
    h, w = a.shape[:2]; h2, w2 = h // f * f, w // f * f; a = a[:h2, :w2]
    if a.ndim == 3: return a.reshape(h2 // f, f, w2 // f, f, a.shape[2]).mean(axis=(1, 3), dtype=np.float32)
    return a.reshape(h2 // f, f, w2 // f, f).mean(axis=(1, 3), dtype=np.float32)
def jpg(path, a01, q=88):
    a8 = np.clip(np.rint(np.asarray(a01) * 255), 0, 255).astype(np.uint8)
    if a8.ndim == 3: a8 = a8[..., ::-1]
    cv2.imwrite(path, a8, [cv2.IMWRITE_JPEG_QUALITY, q])
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
def interp_perfil(r_c, med, rr):
    ok = np.isfinite(med); return np.interp(rr, r_c[ok], med[ok]).astype(np.float32)

yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)

# ------------------------------------------------------------------ L_model (idèntic a flat_camp.py)
if os.path.exists(os.path.join(HO, 'L_model.npy')):
    Lm = np.load(os.path.join(HO, 'L_model.npy')); vc = np.load(os.path.join(HO, 'valid_eros.npy'))
    log('L_model carregat')
else:
    z = np.load(LUM); Lc = z['L_c']; vc = z['valid_c']
    k_ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81))
    vc = cv2.erode(vc.astype(np.uint8), k_, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
    prm = json.load(open(os.path.join(SCR, 'flat_params.json')))
    bx, by = prm['pla_per_1000px']
    plane = (bx * xx / 1000 + by * yy / 1000).astype(np.float32)
    f = 4
    Lc4 = redueix(Lc, f); vc4 = redueix(vc.astype(np.float32), f) > 0.99; rr4 = redueix(rr, f); pl4 = redueix(plane, f)
    r_c, med = mediana_anells(Lc4 - pl4, rr4, 8.0, ok=vc4)
    p_r = interp_perfil(r_c, med, rr)
    Lm = (Lc - plane).astype(np.float32)
    res = np.where(vc, Lm - p_r, 0).astype(np.float32); m = vc.astype(np.float32)
    ext = gauss_n(res, m, 120.0)
    Lm = np.where(vc, Lm, p_r + ext).astype(np.float32)
    Lm = gauss(Lm, 2.0)
    np.save(os.path.join(HO, 'L_model.npy'), Lm); np.save(os.path.join(HO, 'valid_eros.npy'), vc)
    del Lc, res, ext, m, plane, Lc4, vc4, rr4, pl4
    log('L_model fet i desat')

# ------------------------------------------------------------------ base corregida de camp (el que veu Pere sota els filtres)
bc = np.load(os.path.join(SCR, 'capes3', 'Base_corregida_camp.npy'), mmap_mode='r')

# ------------------------------------------------------------------ corba mediana D_c(L), bins de 2 unitats
sel = vc & (rr > 3.0 * R_SOL)
Ls = Lm[sel]
edges = np.arange(296.0, 760.0, 2.0); cent = 0.5 * (edges[1:] + edges[:-1])
idx = np.clip(np.digitize(Ls, edges) - 1, 0, len(cent) - 1)
order = np.argsort(idx, kind='stable'); idx_s = idx[order]
bounds = np.searchsorted(idx_s, np.arange(len(cent) + 1))
D = np.full((len(cent), 3), np.nan, np.float32); N = np.zeros(len(cent), int)
for c in range(3):
    v = (np.asarray(bc[..., c])[sel].astype(np.float32) / 65535.0)[order]
    for k in range(len(cent)):
        a, b = bounds[k], bounds[k + 1]
        if b - a >= 200:
            D[k, c] = np.median(v[a:b]); N[k] = b - a
ok = np.isfinite(D[:, 0])
log('corba mesurada; bins vàlids', int(ok.sum()), 'L de', cent[ok].min(), 'a', cent[ok].max())
# suavitzat lleu (σ 1 bin) per a les derivades
Ds = D.copy()
for c in range(3):
    y = np.interp(cent, cent[ok], D[ok, c])
    Ds[:, c] = cv2.GaussianBlur(y.reshape(1, -1).astype(np.float32), (0, 0), 1.0, borderType=cv2.BORDER_REPLICATE).ravel()

# ------------------------------------------------------------------ corba objectiu S_c: Hermite monòton entre L0 i LHI
def D_at(c, L): return float(np.interp(L, cent, Ds[:, c]))
def D_slope(c, L, h=8.0): return (D_at(c, L + h) - D_at(c, L - h)) / (2 * h)
S = Ds.copy(); info = {}
for c in range(3):
    F = float(np.median(D[(cent >= 300) & (cent <= 312), c][np.isfinite(D[(cent >= 300) & (cent <= 312), c])]))
    y1 = D_at(c, LHI); m1 = D_slope(c, LHI)
    delta = (y1 - F) / (LHI - L0)
    m0 = M0F * delta
    # Fritsch–Carlson: monòton si m0, m1 ∈ [0, 3·delta]
    m1c = min(max(m1, 0.0), 3 * delta)
    tt = (cent - L0) / (LHI - L0)
    h00 = 2 * tt**3 - 3 * tt**2 + 1; h10 = tt**3 - 2 * tt**2 + tt; h01 = -2 * tt**3 + 3 * tt**2; h11 = tt**3 - tt**2
    herm = h00 * F + h10 * (LHI - L0) * m0 + h01 * y1 + h11 * (LHI - L0) * m1c
    S[:, c] = np.where(cent <= L0, F, np.where(cent >= LHI, Ds[:, c], herm))
    info[c] = dict(terra=F, y_hi=y1, pendent_hi=m1, pendent_hi_usat=m1c, corda=delta)
    log(f'canal {c}: terra {F:.4f}, D({LHI:.0f})={y1:.4f}, pendent {m1*10:+.5f}/10 (usat {m1c*10:+.5f}), corda {delta*10:+.5f}/10')
np.save(os.path.join(HO, 'corba_S.npy'), S); np.save(os.path.join(HO, 'corba_D.npy'), Ds)
json.dump(dict(L0=L0, LHI=LHI, M0F=M0F, cent=cent.tolist(), D=np.nan_to_num(D).tolist(), Ds=Ds.tolist(), S=S.tolist(), N=N.tolist(), info=info),
          open(os.path.join(HO, 'corba_D.json'), 'w'))
# taula
print('   L      D_R    S_R   |  D_G    S_G   |  D_B    S_B    (Δ = S − D)')
for L in np.arange(300, LHI + 21, 8):
    k = int(np.argmin(np.abs(cent - L)))
    print(f' {cent[k]:5.0f}  ' + ' | '.join(f'{Ds[k,c]:.4f} {S[k,c]:.4f} {S[k,c]-Ds[k,c]:+.4f}' for c in range(3)))

# ------------------------------------------------------------------ Δ per píxel
delta = np.empty((H, W, 3), np.float32)
for c in range(3):
    dS = (S[:, c] - Ds[:, c]).astype(np.float32)
    delta[..., c] = np.interp(Lm, cent, dS, left=0.0, right=0.0).astype(np.float32)
# dins de 3 R☉ no hi ha res a fer (L > LHI): per seguretat, zero explícit
delta *= (rr > 2.8 * R_SOL)[..., None]
np.save(os.path.join(HO, 'corba_delta.npy'), delta)
log('Δ fet; percentils 1/50/99 (r>3.5R):', [np.round(np.percentile(delta[..., c][rr > 3.5 * R_SOL], [1, 50, 99]), 4).tolist() for c in range(3)])

# ------------------------------------------------------------------ QA: perfils abans/després, polar, vistes
b2 = redueix(bc, 2) / 65535.0; d2 = redueix(delta, 2); rr2 = redueix(rr, 2)
a2 = np.clip(b2 + d2, 0, 1)
np.save(os.path.join(HO, 'base_corba_x2.npy'), a2.astype(np.float32))
th2 = np.arctan2(np.arange(a2.shape[0])[:, None] * 2 + 0.5 - SOL[1], np.arange(a2.shape[1])[None, :] * 2 + 0.5 - SOL[0])
lines = []
for nom, im in (('abans', b2), ('despres', a2)):
    lines.append(nom)
    for c in range(3):
        r_c, med = mediana_anells(im[..., c], rr2, 4.0, r_min=R_SOL)
        okk = np.isfinite(med)
        prof = np.interp(np.arange(1.2, 10.6, 0.2) * R_SOL, r_c[okk], med[okk])
        lines.append(f'  canal {c}: ' + ' '.join(f'{v:.4f}' for v in prof))
    # derivada radial per sector (12 sectors) de la luminància: el màxim de |d²/dr²| diu si hi ha colze
    lum = im.mean(-1)
    for s_ in range(12):
        a0 = -math.pi + s_ * math.pi / 6
        sel_ = (th2 >= a0) & (th2 < a0 + math.pi / 6)
        r_c, med = mediana_anells(np.where(sel_, lum, np.nan), rr2, 8.0, ok=sel_, r_min=2.5 * R_SOL)
        okk = np.isfinite(med)
        p = np.interp(np.arange(2.6, 9.0, 0.1) * R_SOL, r_c[okk], med[okk])
        d1 = np.gradient(p); d2_ = np.gradient(d1)
        lines.append(f'  sector {s_:2d} ({math.degrees(a0):+4.0f}°): max|d2| {np.abs(d2_).max()*1e4:.2f}e-4 a r={2.6+0.1*int(np.argmax(np.abs(d2_))):.1f}R, max|d1| {np.abs(d1).max()*1e3:.2f}e-3')
open(os.path.join(HO, 'qa_perfils.txt'), 'w').write('\n'.join(lines))
print('\n'.join(lines))
lo, hi = 0.06, 0.30
jpg(os.path.join(HO, 'abans_x4.jpg'), redueix(np.clip(b2, 0, 1) ** 0.5, 2))
jpg(os.path.join(HO, 'despres_x4.jpg'), redueix(np.clip(a2, 0, 1) ** 0.5, 2))
jpg(os.path.join(HO, 'abans_estirat_x4.jpg'), redueix(np.clip((b2 - lo) / (hi - lo), 0, 1) ** 0.6, 2))
jpg(os.path.join(HO, 'despres_estirat_x4.jpg'), redueix(np.clip((a2 - lo) / (hi - lo), 0, 1) ** 0.6, 2))
jpg(os.path.join(HO, 'delta_x4.jpg'), redueix(np.clip(d2 * 10 + 0.5, 0, 1), 2))
# polar de la luminància (no del residu): angle vertical, radi horitzontal, 2–9 R☉, estirat
NA, NR = 1440, 2450
th = (2 * math.pi * np.arange(NA) / NA)[:, None]; r = np.arange(NR)[None, :].astype(np.float32)
mx = (SOL[0] / 2 - 0.25 + r * np.cos(th)).astype(np.float32); my = (SOL[1] / 2 - 0.25 + r * np.sin(th)).astype(np.float32)
for nom, im in (('abans', b2), ('despres', a2)):
    pol = cv2.remap(np.ascontiguousarray(im.mean(-1)), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    img = np.clip((pol - 0.10) / 0.20, 0, 1) ** 0.7
    img = cv2.resize(img, (NR // 2, NA // 2), interpolation=cv2.INTER_AREA)
    img = np.repeat(img[..., None], 3, -1)
    for k in range(1, 12):
        x_ = int(k * R_SOL / 4)
        if x_ < img.shape[1]: img[:, x_, :] = [1, 0, 0]
    jpg(os.path.join(HO, f'polar_lum_{nom}.jpg'), img)
log('fi')
