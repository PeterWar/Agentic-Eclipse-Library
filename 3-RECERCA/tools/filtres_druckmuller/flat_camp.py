"""Flat artificial del camp per a la base de FiltresSEMIFINAL (19-08-2026, nit).

La base de Pere (Aplicant_Filtres.tif = llenç E, 7648×5353) porta artefactes de compost al camp
exterior: arcs de màscares radials (el més fort a ~8,6 R☉), la caixa Vixen, els triangles del
marc Sony (girat 33°) als cantons, una costura vertical a x = x_Sol (embolcall polar de
Photoshop), franges fosques, i el gradient real del cel. La correcció es fa contra una
REFERÈNCIA FÍSICA: la lluminància calibrada dels dos trens al mateix llenç (`lum_llenc.npz`,
L_c = Vixen HDR + Sony ≥1 s aplanat, registrats), que no ha passat per cap màscara de Photoshop.

    T_c(L) : LUT monòtona base_c ↔ ln L_model, per canal, ajustada a 2–10 R☉ (la base és una
             funció molt estreta de L_c: σ 1–3 nivells de 255)
    L_model = L_c − pla del cel (ajustat a r > 6 R☉), amb el racó sense Sony omplert per
             extrapolació suau
    Δ_c    = base_c − T_c(L_model)                      (el que la base té de més o de menys)
    Δ0(r)  = mediana azimutal de Δ per radi              (part radial: anells, LUT)
    Δ_nr   = Δ − Δ0 → passabaix σ 10 px + zones de vora (arcs, costures, triangles) exactes
    Corr   = w1(r)·LP(Δ_nr) + w1e(r)·E·(Δ_nr − LP) + w2(r)·Δ0(r)
             w1: 5→6,5 R☉ (part suau: no toca l'halo de color de Pere ni la corona), w1e: 3,5→5 R☉
             (vores dures: arcs, costures, marc), w2: 6→7,5 R☉ (part radial), tot smoothstep

Cap pes radial no talla res que no sigui ja ~0 al lloc on comença: T s'ajusta a la mateixa
zona i Δ0 s'aparta de la transició, o sigui que la correcció NO pot deixar cap anell al final
de la corona; el QA polar ho comprova.

Sortides (FD3_SCR): flat_corr.npy (H,W,3 float32, correcció a restar), flat_qa/*.jpg, flat_params.json
"""
import os, sys, json, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import smooth01

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
LUM = os.environ.get('FD3_LUM', os.path.join(SCR, '..', 'treball', 'lum_llenc.npz'))
QA = os.path.join(SCR, 'flat_qa'); os.makedirs(QA, exist_ok=True)
W, H = 7648, 5353
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)

# paràmetres
R_FIT = (2.0, 10.0)          # R☉, ajust de la LUT
R_PLA = 6.0                  # R☉, ajust del pla del cel
W1 = (5.0, 6.5)              # R☉, rampa de la part no radial suau (passabaix)
W1E = (3.5, 5.0)             # R☉, rampa de les zones de vora (arcs, costures, vores dures)
W2 = (6.0, 7.5)              # R☉, rampa de la part radial
SIG_LP = 24.0                # px, passabaix de Δ_nr
SIG_E = 1.0                  # px, suavitzat mínim a les zones de vora
TAU_E = 0.002                # llindar de vora (unitats 0-1)
ARCS = [(3800, 3870), (4540, 4630)]   # px: arcs de màscara circular de la base (8,6 i 10,3 R☉), bandes de vora geomètriques
N_T_MAX = 0.0025             # soroll local màxim del model T perquè una zona de vora s'apliqui exacta
MIN_EXT_E = 60               # px, extensió mínima d'una component per ser vora (i no una estrella)
SEAM_X = 4020                # costura polar de Photoshop (x = x_Sol), files de dalt i de baix
SEAM_BAND = 60               # px de mitja amplada de la zona de vora de la costura
G_CLIP = (1.0, 2.5)          # guany de Pere sobre l'estructura no radial de T, per anell
E_STARS_MAX = 25             # px, extensió màxima d'una taca que es considera estrella

def gauss(a, s):
    return cv2.GaussianBlur(np.ascontiguousarray(a, np.float32), (0, 0), s, borderType=cv2.BORDER_REPLICATE)

def gauss_n(a, m, s):
    return gauss(a * m, s) / np.maximum(gauss(m, s), 1e-4)

def redueix(a, f):
    h, w = a.shape[:2]; h2, w2 = h // f * f, w // f * f
    a = a[:h2, :w2]
    if a.ndim == 3:
        return a.reshape(h2 // f, f, w2 // f, f, a.shape[2]).mean(axis=(1, 3), dtype=np.float32)
    return a.reshape(h2 // f, f, w2 // f, f).mean(axis=(1, 3), dtype=np.float32)

def jpg(path, a01, q=88):
    a8 = np.clip(np.rint(np.asarray(a01) * 255), 0, 255).astype(np.uint8)
    if a8.ndim == 3: a8 = a8[..., ::-1]
    cv2.imwrite(path, a8, [cv2.IMWRITE_JPEG_QUALITY, q])

def estira(a, lo, hi): return np.clip((a - lo) / (hi - lo), 0, 1)

def mediana_anells(img, rr, dr, ok=None, r_min=0.0):
    """mediana per anell de dr px; retorna r_c, med (nan on no hi ha prou píxels)."""
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1)
    sel = np.ones(rr.shape, bool) if ok is None else ok.copy()
    sel &= rr >= r_min
    v = img[sel]; ii = idx[sel]
    order = np.argsort(ii, kind='stable'); v = v[order]; ii = ii[order]
    b = np.searchsorted(ii, np.arange(n + 1))
    med = np.full(n, np.nan, np.float32)
    for k in range(n):
        if b[k + 1] - b[k] >= 30:
            med[k] = np.median(v[b[k]:b[k + 1]])
    return (np.arange(n) + 0.5) * dr, med

def interp_perfil(r_c, med, rr):
    ok = np.isfinite(med)
    return np.interp(rr, r_c[ok], med[ok]).astype(np.float32)

# ---------------------------------------------------------------- càrrega
base = np.load(os.path.join(SCR, 'capa0_rgb16.npy'), mmap_mode='r')
z = np.load(LUM)
Lc = z['L_c']; vc = z['valid_c']
# la vora del marc Sony (girat) porta una tira brillant a L_c: s'erosiona la validesa 40 px (sense
# tocar les vores del llenç) i el forat es reomple per extrapolació com el racó
ERODE_PX = 40
k_ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ERODE_PX + 1, 2 * ERODE_PX + 1))
vc = cv2.erode(vc.astype(np.uint8), k_, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
log('carregat', base.shape, Lc.shape, 'valid_c (erosionada)', vc.mean())
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]
xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)

# ---------------------------------------------------------------- pla del cel i perfil m0 (a ×4)
f = 4
Lc4 = redueix(Lc, f); vc4 = redueix(vc.astype(np.float32), f) > 0.99
rr4 = redueix(rr, f); xx4 = redueix(np.broadcast_to(xx, (H, W)).astype(np.float32), f); yy4 = redueix(np.broadcast_to(yy, (H, W)).astype(np.float32), f)
plane4 = np.zeros_like(Lc4); coef = None
for it in range(4):
    r_c, med = mediana_anells(Lc4 - plane4, rr4, 8.0, ok=vc4)
    p0 = interp_perfil(r_c, med, rr4)
    sel = vc4 & (rr4 > R_PLA * R_SOL)
    A = np.stack([np.ones(sel.sum()), xx4[sel] / 1000, yy4[sel] / 1000], 1)
    coef, *_ = np.linalg.lstsq(A, (Lc4 - p0)[sel], rcond=None)
    plane4 = (coef[0] + coef[1] * xx4 / 1000 + coef[2] * yy4 / 1000).astype(np.float32)
log('pla del cel per 1000 px (b, c):', coef[1], coef[2], '(a irrellevant)')
r_c, med = mediana_anells(Lc4 - plane4, rr4, 8.0, ok=vc4)
plane = (coef[1] * xx / 1000 + coef[2] * yy / 1000).astype(np.float32)   # sense constant
p_r = interp_perfil(r_c, med, rr)
del Lc4, rr4, xx4, yy4, plane4

# ---------------------------------------------------------------- L_model: L_c − pla, racó omplert
Lm = (Lc - plane).astype(np.float32)
res = np.where(vc, Lm - p_r, 0).astype(np.float32)
m = vc.astype(np.float32)
# extrapolació suau del residu cap al racó (convolució normalitzada, σ 120 px) només fora de valid
ext = gauss_n(res, m, 120.0)
Lm = np.where(vc, Lm, p_r + ext).astype(np.float32)
Lm = gauss(Lm, 2.0)
del res, ext, Lc
log('L_model fet; L rang', float(np.percentile(Lm, 0.1)), float(np.percentile(Lm, 99.9)))

# ---------------------------------------------------------------- LUT T_c
lnL = np.log(np.maximum(Lm, 1.0)).astype(np.float32)
lnL4 = redueix(lnL, f); rr4 = redueix(rr, f); vc4 = redueix(vc.astype(np.float32), f) > 0.99
sel = vc4 & (rr4 > R_FIT[0] * R_SOL) & (rr4 < R_FIT[1] * R_SOL)
x = lnL4[sel]
xb = np.linspace(np.percentile(x, 0.02), np.percentile(x, 99.98), 241)
xc = 0.5 * (xb[1:] + xb[:-1])
LUT = []
T4 = np.zeros((lnL4.shape[0], lnL4.shape[1], 3), np.float32)
b4 = redueix(base, f) / 65535.0
for c in range(3):
    y = b4[..., c][sel]
    idx = np.digitize(x, xb) - 1
    med = np.full(len(xc), np.nan, np.float32)
    for k in range(len(xc)):
        s_ = y[idx == k]
        if s_.size >= 40: med[k] = np.median(s_)
    okk = np.isfinite(med)
    yy_ = np.interp(xc, xc[okk], med[okk])
    yy_ = cv2.GaussianBlur(yy_.reshape(1, -1).astype(np.float32), (0, 0), 1.5, borderType=cv2.BORDER_REPLICATE).ravel()
    yy_ = np.maximum.accumulate(yy_)          # monòtona no decreixent
    LUT.append((xc.copy(), yy_.copy()))
    T4[..., c] = np.interp(lnL4, xc, yy_)
    r_ = b4[..., c][sel] - T4[..., c][sel]
    log(f'LUT canal {c}: rang T {yy_[0]:.4f}..{yy_[-1]:.4f}; residu ×4 a la zona d\'ajust: mediana {np.median(r_):.4f}, σ {1.4826*np.median(np.abs(r_-np.median(r_))):.4f}')
np.save(os.path.join(SCR, 'flat_T4.npy'), T4)
del lnL4, b4, rr4, vc4

# ---------------------------------------------------------------- Δ a plena resolució, amb el guany de Pere
# T_nr = T − T_m0(r): l'estructura no radial que la referència física té; la base la porta amb un guany
# g(r) > 1 (extensió radial, detall tangencial, corbes de Pere). Es mesura per anell (pendent robust
# de base_nr sobre T_nr) i es CONSERVA: la correcció només toca el que no és proporcional a l'estructura
# real, o sigui els artefactes.
D = np.empty((H, W, 3), np.float32)
Tfull = np.empty((H, W, 3), np.float32)
for c in range(3):
    xc, yy_ = LUT[c]
    Tfull[..., c] = np.interp(lnL, xc, yy_).astype(np.float32)
    D[..., c] = np.asarray(base[..., c], np.float32) / 65535.0 - Tfull[..., c]
del lnL
# guany per anell sobre la luminància (×4)
lb4 = redueix(np.asarray(base, np.float32).mean(-1) / 65535.0, f); lt4 = redueix(Tfull.mean(-1), f)
rr4 = redueix(rr, f); vc4 = redueix(vc.astype(np.float32), f) > 0.99
r_c, mb = mediana_anells(lb4, rr4, 8.0, ok=vc4); r_c, mt = mediana_anells(lt4, rr4, 8.0, ok=vc4)
nb = lb4 - interp_perfil(r_c, mb, rr4); nt = lt4 - interp_perfil(r_c, mt, rr4)
rings = np.arange(1.5, 11.6, 0.5)
gr = []; gc = []
for i in range(len(rings) - 1):
    s_ = vc4 & (rr4 >= rings[i] * R_SOL) & (rr4 < rings[i + 1] * R_SOL)
    if s_.sum() < 500: continue
    x_ = nt[s_]; y_ = nb[s_]; wg = np.ones_like(x_)
    for it in range(6):
        A = np.stack([np.ones_like(x_), x_], 1) * wg[:, None]
        cf, *_ = np.linalg.lstsq(A, y_ * wg, rcond=None)
        rs = y_ - (cf[0] + cf[1] * x_); sg = 1.4826 * np.median(np.abs(rs)) + 1e-6
        wg = np.minimum(1, 1.5 * sg / np.maximum(np.abs(rs), 1e-9))
    gr.append(0.5 * (rings[i] + rings[i + 1])); gc.append(float(cf[1]))
gr = np.array(gr); gc = np.clip(np.array(gc), *G_CLIP)
gc_s = cv2.GaussianBlur(gc.reshape(1, -1).astype(np.float32), (0, 0), 1.2, borderType=cv2.BORDER_REPLICATE).ravel()
log('guany g(r) per anell (R☉: g brut → suau):', [(float(a), round(float(b), 2), round(float(c_), 2)) for a, b, c_ in zip(gr, gc, gc_s)])
g_r = np.interp(rr, gr * R_SOL, gc_s).astype(np.float32)
Tm0 = np.empty_like(Tfull)
for c in range(3):
    r_c, mt = mediana_anells(Tfull[..., c], rr, 4.0, ok=vc, r_min=1.0 * R_SOL)
    Tm0[..., c] = interp_perfil(r_c, mt, rr)
D -= (g_r - 1.0)[..., None] * (Tfull - Tm0)
Tfine = Tfull.mean(-1)
del Tfull, Tm0, lb4, lt4, nb, nt, rr4, vc4
log('Δ fet (amb guany); percentils 1/50/99 (r>4R):', [np.round(np.percentile(D[..., c][rr > 4 * R_SOL], [1, 50, 99]), 4).tolist() for c in range(3)])

# ---------------------------------------------------------------- Δ0(r) i Δ_nr
D0 = np.empty_like(D)
perfils = []
for c in range(3):
    r_c, med = mediana_anells(D[..., c], rr, 2.0, ok=vc, r_min=1.2 * R_SOL)
    okk = np.isfinite(med)
    tmp = np.interp(r_c, r_c[okk], med[okk]).astype(np.float32)
    tmp = cv2.GaussianBlur(tmp.reshape(1, -1), (0, 0), 1.5, borderType=cv2.BORDER_REPLICATE).ravel()
    D0[..., c] = np.interp(rr, r_c, tmp).astype(np.float32)
    perfils.append(tmp)
np.save(os.path.join(SCR, 'flat_D0_perfils.npy'), np.stack([r_c] + perfils))
Dnr = D - D0
del D
log('Δ0 fet')

# ---------------------------------------------------------------- passabaix + zones de vora
Dlp = np.empty_like(Dnr); D2 = np.empty_like(Dnr)
for c in range(3):
    Dlp[..., c] = gauss(Dnr[..., c], SIG_LP)
    D2[..., c] = gauss(Dnr[..., c], 2.0)
diff = np.abs(D2 - Dlp).mean(-1)
del D2
cand = (diff > TAU_E).astype(np.uint8)
n, lab, stats, _ = cv2.connectedComponentsWithStats(cand, connectivity=8)
keep = np.zeros(n, bool)
ext_ = np.maximum(stats[:, cv2.CC_STAT_WIDTH], stats[:, cv2.CC_STAT_HEIGHT])
keep = ext_ >= MIN_EXT_E
keep[0] = False
E_raw = keep[lab].astype(np.float32)
del lab
# banda geomètrica de la costura polar (x = x_Sol), només on la costura existeix (dalt i baix)
xs_ = np.arange(W)
band = (np.abs(xs_ - SEAM_X) < SEAM_BAND).astype(np.float32)[None, :]
rows = ((np.arange(H) < 700) | (np.arange(H) > 4700)).astype(np.float32)[:, None]
E_raw = np.maximum(E_raw, band * rows)
for a0, a1 in ARCS:
    E_raw = np.maximum(E_raw, ((rr >= a0) & (rr <= a1)).astype(np.float32))
# porta de soroll: on el model T és sorollós (vora del marc Sony), la correcció exacta injectaria soroll
nT = gauss(np.abs(Tfine - gauss(Tfine, 3.0)), 8.0)
gate = smooth01((N_T_MAX - nT) / 0.001)
E_raw *= gate
jpg(os.path.join(QA, 'porta_soroll_T_x4.jpg'), redueix(gate, 4))
E = np.clip(gauss(E_raw, 4.0) * 3.0, 0, 1)
E = smooth01(E)
log('zones de vora: candidats', int(cand.sum()), 'components', n, 'conservades', int(keep.sum()), 'fracció E>0.5', float((E > 0.5).mean()))
jpg(os.path.join(QA, 'zones_vora_x4.jpg'), redueix(E, 4))
del Tfine
w1 = smooth01((rr - W1[0] * R_SOL) / ((W1[1] - W1[0]) * R_SOL)).astype(np.float32)
w1e = smooth01((rr - W1E[0] * R_SOL) / ((W1E[1] - W1E[0]) * R_SOL)).astype(np.float32)
w2 = smooth01((rr - W2[0] * R_SOL) / ((W2[1] - W2[0]) * R_SOL)).astype(np.float32)
Corr = np.empty_like(Dnr)
for c in range(3):
    De = gauss(Dnr[..., c], SIG_E)
    Corr[..., c] = w1 * Dlp[..., c] + w1e * E * (De - Dlp[..., c]) + w2 * D0[..., c]
del Dnr, Dlp, De, D0
np.save(os.path.join(SCR, 'flat_corr.npy'), Corr)
log('Corr guardat; percentils 1/50/99 (r>4R):', [np.round(np.percentile(Corr[..., c][rr > 4 * R_SOL], [1, 50, 99]), 4).tolist() for c in range(3)])

# ---------------------------------------------------------------- QA
b8 = redueix(base, 8) / 65535.0
c8 = redueix(Corr, 8)
corr8 = np.clip(b8 - c8, 0, 1)
np.save(os.path.join(SCR, 'flat_base_corr_x8.npy'), corr8)
jpg(os.path.join(QA, 'corr_x8.jpg'), estira(c8, -0.05, 0.05))
lo, hi = 0.07, 0.22
jpg(os.path.join(QA, 'base_estirada_x8.jpg'), estira(b8, lo, hi))
jpg(os.path.join(QA, 'corregida_estirada_x8.jpg'), estira(corr8, lo, hi))
# residu radial de la corregida
rr8 = redueix(rr, 8)
r_c8, med8 = mediana_anells(corr8.mean(-1), rr8, 4.0)
res8 = corr8.mean(-1) - interp_perfil(r_c8, med8, rr8)
jpg(os.path.join(QA, 'corregida_residu_x8.jpg'), estira(res8, -0.03, 0.03))
r_c8, med8b = mediana_anells(b8.mean(-1), rr8, 4.0)
res8b = b8.mean(-1) - interp_perfil(r_c8, med8b, rr8)
jpg(os.path.join(QA, 'base_residu_x8.jpg'), estira(res8b, -0.03, 0.03))
# polar de la corregida (residu) a ×2
b2 = redueix(base, 2) / 65535.0; c2 = np.clip(b2 - redueix(Corr, 2), 0, 1)
rr2 = redueix(rr, 2)
for nom, im in (('base', b2), ('corregida', c2)):
    lum = im.mean(-1)
    r_c2, med2 = mediana_anells(lum, rr2, 2.0)
    res2 = lum - interp_perfil(r_c2, med2, rr2)
    NA, NR = 1440, 2450
    th = (2 * math.pi * np.arange(NA) / NA)[:, None]; r = np.arange(NR)[None, :].astype(np.float32)
    mx = (SOL[0] / 2 - 0.25 + r * np.cos(th)).astype(np.float32); my = (SOL[1] / 2 - 0.25 + r * np.sin(th)).astype(np.float32)
    pol = cv2.remap(np.ascontiguousarray(res2), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    img = estira(pol, -0.03, 0.03)
    img = cv2.resize(img, (NR // 2, NA // 2), interpolation=cv2.INTER_AREA)
    img = np.repeat(img[..., None], 3, -1)
    for k in range(1, 12):
        x_ = int(k * R_SOL / 4)
        if x_ < img.shape[1]: img[:, x_, :] = [1, 0, 0]
    jpg(os.path.join(QA, f'polar_residu_{nom}.jpg'), img)
    # perfil radial de la lum (per veure si hi ha anells nous): derivada
    okk = np.isfinite(med2)
    np.save(os.path.join(SCR, f'flat_perfil_lum_{nom}.npy'), np.stack([r_c2[okk], med2[okk]]))
json.dump(dict(pla_per_1000px=[float(coef[1]), float(coef[2])], R_FIT=R_FIT, R_PLA=R_PLA, W1=W1, W1E=W1E, W2=W2, ARCS=ARCS, G_CLIP=G_CLIP, ERODE_PX=ERODE_PX, N_T_MAX=N_T_MAX, SIG_LP=SIG_LP, SIG_E=SIG_E,
               TAU_E=TAU_E, MIN_EXT_E=MIN_EXT_E, LUT={c: dict(x=LUT[c][0].tolist(), y=LUT[c][1].tolist()) for c in range(3)}),
          open(os.path.join(SCR, 'flat_params.json'), 'w'), indent=1)
log('fi')
