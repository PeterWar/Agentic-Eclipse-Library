"""Prototip v3: la corba de to s'aplica al PERFIL RADIAL i tota l'estructura azimutal
(bandes DoG sense mitjana d'anell + residu de gran escala) s'afegeix en espai de
PANTALLA amb guany declarat per periode angular, compensacio de dilucio del cel
i Wiener a nivell d'anell. Nomes llegeix; escriu al scratchpad.
"""
import sys, math, json, time, os
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import gaussian_filter1d, gaussian_filter, map_coordinates
import cv2

SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:5.0f}s]", *a, flush=True)

OUT = M.OUT
hdr = np.load(OUT / "hdr_vixen_countss.npy")
varm = np.load(OUT / "hdr_vixen_var.npy")
H, W, _ = hdr.shape
cy, cx = H / 2.0, W / 2.0
r = M.anells(H, W, cy, cx); rs = r / M.R_SOL_PX
valid = np.all(np.isfinite(hdr), axis=2)
r_complet = min(H, W) / 2.0
R_, G_ = hdr[..., 0], hdr[..., 1]
ref = valid & (rs > 1.3) & (rs < 1.5)
kr = float(np.median(G_[ref]) / np.median(R_[ref]))
L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan)
base_r, perfil = M.perfil_azimutal(np.where(valid, L, np.nan), r, r_complet, cy, cx)
q = np.where(valid, L / np.maximum(base_r, 1e-9), 1.0).astype(np.float32)
corr = M.desenfoca_valid(q, valid, 250.0)
lncorr = np.log(np.maximum(corr, 1e-3)).astype(np.float32)
base = base_r * np.maximum(corr, 1e-3)
del q, corr
norm = np.where(valid, L / np.maximum(base, 1e-6), 1.0).astype(np.float32)
vG = np.nan_to_num(varm[..., 1])
sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base, 1e-6)).astype(np.float32)
del varm, vG
cel_z = valid & (rs > 4.0) & (rs < 5.1)
_ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
obs = float(np.std((norm - M.desenfoca(norm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig[cel_z])); sig = sig * (obs / esp)
lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)
ib = r.astype(np.int32); nb = int(ib.max()) + 1
cnt = np.bincount(ib[valid], minlength=nb).astype(np.float64)
def ring_mean(x, m=None):
    mm = valid if m is None else (valid & m)
    s = np.bincount(ib[mm], weights=x[mm].astype(np.float64), minlength=nb)
    c = np.bincount(ib[mm], minlength=nb).astype(np.float64)
    return np.where(c > 30, s / np.maximum(c, 1), np.nan)
def suavitza_r(p, s):
    okk = np.isfinite(p); idx = np.arange(nb)
    p2 = np.interp(idx, idx[okk], p[okk]) if okk.sum() > 2 else np.nan_to_num(p)
    return gaussian_filter1d(p2, s, mode="nearest")
med_sig = suavitza_r(ring_mean(sig_log), 20)
sig_log = np.minimum(sig_log, (3.0 * med_sig)[ib].astype(np.float32))
log("preparat")

# ---------- piramide
rng = np.random.default_rng(1)
zn = rng.standard_normal((H, W)).astype(np.float32)
zn = cv2.blur(zn, (2, 2), borderType=cv2.BORDER_REFLECT); zn /= float(zn.std())
zn = (zn * sig_log).astype(np.float32)
ESC = M.BANDES_PX; DEG = 180.0 / math.pi
BANDS = []
prev = M.desenfoca_valid(lnorm, valid, ESC[0]); prevn = M.desenfoca_valid(zn, valid, ESC[0])
for s0, s1 in zip(ESC[:-1], ESC[1:]):
    seg = M.desenfoca_valid(lnorm, valid, s1); segn = M.desenfoca_valid(zn, valid, s1)
    BANDS.append((s0, s1, (prev - seg).astype(np.float32), (prevn - segn).astype(np.float32)))
    prev, prevn = seg, segn
RESIDU = (prev + lncorr).astype(np.float32)
_dummy = 0          # gran escala: > 324 px sigma, inclou el gradient de cel
del zn, prevn, seg, segn, prev
log("piramide feta")

def robust_ring_power(x, m=None):
    ax = np.abs(x); s_rob = ring_mean(ax, m) / 0.798
    lim = (4.0 * s_rob)[ib].astype(np.float32); mm = (ax <= lim)
    return ring_mean(x * x, mm if m is None else (m & mm))
def lam_peak(s0, s1):
    f2 = math.log(s1 / s0) / (math.pi ** 2 * (s1 ** 2 - s0 ** 2)); return 1.0 / math.sqrt(f2)
STATS = []
zona_cel = (np.arange(nb) > 4.0 * M.R_SOL_PX) & (np.arange(nb) < 5.0 * M.R_SOL_PX)
for (s0, s1, b, bn) in BANDS:
    s_mid = math.sqrt(s0 * s1); lam = lam_peak(s0, s1)
    rm = suavitza_r(ring_mean(b), max(3.0, 0.5 * s_mid))
    b -= rm[ib].astype(np.float32)
    pb = suavitza_r(robust_ring_power(b), max(6.0, 1.0 * s_mid))
    pn = suavitza_r(robust_ring_power(bn), max(6.0, 1.0 * s_mid))
    f2 = 1.0
    if s_mid < 9.0:
        f2 = max(1.0, float(np.nanmean(pb[zona_cel]) / max(np.nanmean(pn[zona_cel]), 1e-18)))
    pn = pn * f2
    STATS.append(dict(s_mid=s_mid, lam=lam, pb=pb, pn=pn, f2=f2))
    print(f"  banda sigma {s0}-{s1}: periode pic {lam:.0f} px, f2={f2:.2f}")
RESIDU = RESIDU - suavitza_r(ring_mean(RESIDU), 30)[ib].astype(np.float32)
log("estadistica feta (residu sense mitjana d'anell)")

# ---------- corba de to sobre el PERFIL RADIAL
dins = valid & (rs > 1.03) & (rs < 6.0)
lo = float(np.percentile(L[dins], 0.02)) * 0.85
hi = float(np.percentile(L[valid & (rs < 1.06)], 99.6))
def a_u0(x):
    uu = (np.log10(np.maximum(np.nan_to_num(x), lo * 0.5)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    uu = np.where(uu > 0.06, uu, 0.06 * np.exp(np.minimum(uu - 0.06, 0) / 0.06))
    return np.clip(uu, 1e-4, None)
u0_ref = a_u0(L)
ancs = []
for r0, niv in ((1.05, M.NIV_NUCLI), (2.0, M.NIV_CORONA), (6.8, M.NIV_CEL)):
    m = valid & (rs > r0 * 0.97) & (rs < r0 * 1.03)
    ancs.append((math.log(max(float(np.median(u0_ref[m])), 1e-9)), math.log(niv)))
Amat = np.array([[1.0, a, a * a] for a, _ in ancs]); coef = np.linalg.solve(Amat, np.array([bb for _, bb in ancs]))
del u0_ref
def corba(x):
    u0 = a_u0(x); lu = np.log(u0)
    t = np.exp(coef[0] + coef[1] * lu + coef[2] * lu ** 2)
    t = np.where(u0 > math.exp(ancs[0][0]), M.NIV_NUCLI + (1 - M.NIV_NUCLI) * (1 - np.exp(-(u0 / math.exp(ancs[0][0]) - 1) * 3)), t)
    return np.clip(t, 1e-4, 1)
# pendent de la corba actual al llarg del perfil (informatiu)
prof = np.maximum(perfil, 1e-6)
lp = np.log(prof); lps = gaussian_filter1d(lp, 60, mode="nearest")
kk = np.arange(nb); wmix = np.clip((kk - 4.3*M.R_SOL_PX)/(0.4*M.R_SOL_PX), 0, 1)
prof = np.exp((1-wmix)*lp + wmix*lps)
t_rad = corba(prof)
dlnt = np.gradient(np.log(t_rad)); dlnL = np.gradient(np.log(prof))
pend = dlnt / np.where(np.abs(dlnL) > 1e-9, dlnL, np.nan)
print("pendent d ln t / d ln L de la corba ACTUAL al llarg del perfil radial:")
for rq in (1.1, 1.2, 1.3, 1.5, 1.8, 2.0, 2.3, 2.7, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0):
    k = int(rq * M.R_SOL_PX)
    if k < nb - 1: print(f"   {rq}: t={t_rad[k]:.3f}  pendent={np.nanmedian(pend[k-20:k+20]):.3f}")
lnt_rad = np.log(t_rad)[ib].astype(np.float32)

# ---------- croma (com etapa_foto)
srgb = (np.nan_to_num(hdr) * M.WB_DIURN) @ M.CAM_A_SRGB.T
Lum = np.maximum(srgb @ np.array([0.2126, 0.7152, 0.0722]), 1e-9); c = srgb / Lum[..., None]
Lp = np.where(valid, np.maximum(np.nan_to_num(L), 0.0), 0.0)
num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (10, 10, 0)); den = gaussian_filter(Lp, 10)
c = num / np.maximum(den, 1e-9)[..., None]
prou = gaussian_filter((valid | (rs < 1.30)).astype(np.float32), 10) > 0.995
zc = valid & (rs > 1.5) & (rs < 2.2); zs = valid & (rs > 6.2) & (rs < 7.0)
mc = np.array([float(np.median(c[..., i][zc])) for i in range(3)]); ms = np.array([float(np.median(c[..., i][zs])) for i in range(3)])
mc, ms = mc / mc[1], ms / ms[1]; c = np.where(prou[..., None], c, ms)
kc = np.array(M.OBJ_CORONA) / mc; ks = np.array(M.OBJ_CEL) / ms
cel_lin = float(np.median(np.nan_to_num(L)[zs]))
u = np.clip(np.log10(np.maximum(np.nan_to_num(L), cel_lin) / cel_lin) / math.log10(max(float(np.median(np.nan_to_num(L)[zc])) / cel_lin, 1.2)), 0, 1)[..., None]
CROMA = c * (kc * u + ks * (1 - u)); CROMA = CROMA / np.maximum(CROMA @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)[..., None]
del srgb, Lum, c, num, den, u
# nivell del cel+halo per a la dilucio: mediana anular a 6,5-7 Rsol
S_cel = float(np.nanmedian(perfil[int(6.5 * M.R_SOL_PX):int(7.0 * M.R_SOL_PX)]))
print(f"S_cel (perfil a 6,5-7 Rsol) = {S_cel:.1f} ADU/s")

# ---------- guany declarat per PERIODE angular (graus): amplificacio en pantalla respecte del lineal
GAM_TAB = [(0.25, 0.0), (0.45, 2.0), (0.7, 5.0), (1.2, 8.0), (2.0, 9.0), (4.0, 7.0), (8.0, 4.0), (15.0, 2.0), (30.0, 1.1), (60.0, 0.8), (400.0, 0.7)]
def gam_lambda(theta):
    xs = np.log([a for a, _ in GAM_TAB]); ys = [g for _, g in GAM_TAB]
    return np.interp(np.log(np.maximum(theta, 1e-6)), xs, ys)

def build(G_SCALE=1.0, PHI_EXP=0.5, PHI_CAP=2.5, W_K=1.0, KAPPA=2.5, PSF_FLOOR=3.5, G_RES=0.7, WPIX=True, verbose=True):
    """retorna ln t (display) complet"""
    rr = np.maximum(np.arange(nb, dtype=np.float64), 1.0)
    Phi = np.clip((prof / np.maximum(prof - S_cel, 1e-6)) ** PHI_EXP, 1.0, PHI_CAP)
    Phi = suavitza_r(Phi, 30)
    Dd = (G_RES * Phi)[ib].astype(np.float32) * RESIDU
    for (s0, s1, b, bn), st in zip(BANDS, STATS):
        if st["s_mid"] < PSF_FLOOR: continue
        pb, pn = st["pb"], st["pn"]
        snr2 = np.maximum(pb / np.maximum(pn, 1e-18) - 1.0, 0.0)
        Wr = snr2 / (snr2 + W_K)
        A = np.sqrt(np.maximum(pb - pn, 0.0))
        theta = (st["lam"] / rr) * DEG
        g = G_SCALE * gam_lambda(theta) * Phi * Wr
        g = suavitza_r(np.nan_to_num(g), max(6.0, 0.5 * st["s_mid"]))
        if WPIX:
            v = M.desenfoca(b * b, 4.0 * s1)
            w = np.clip(1.0 - pn[ib].astype(np.float32) / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
        else: w = 1.0
        beta = (KAPPA * np.maximum(A, 1e-6))[ib].astype(np.float32)
        Dd += g[ib].astype(np.float32) * w * (beta * np.tanh(b / beta))
        if verbose:
            print(f"  s{s0:5.1f}-{s1:5.1f} (l={st['lam']:4.0f}px): " + " ".join(
                f"r{rq}:{theta[int(rq*M.R_SOL_PX)]:.1f}deg/snr{math.sqrt(snr2[int(rq*M.R_SOL_PX)]):.0f}/g{g[int(rq*M.R_SOL_PX)]:.1f}"
                for rq in (1.2, 1.6, 2.3, 3.0, 3.5, 4.3, 5.2, 6.0, 7.0) if int(rq * M.R_SOL_PX) < nb))
    Dd = np.where(valid, Dd, 0.0)
    return lnt_rad + Dd

def imatge(lnt):
    t = np.exp(np.clip(lnt, -9.2, 0.0)).astype(np.float32)
    img = np.clip(CROMA * t[..., None], 0, 1); img = np.maximum(img, 0.004)
    img = img[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1]
    return t, (img * 255).astype(np.uint8)[..., ::-1]

BANDES_DEG = [(18, 72), (6, 18), (2, 6), (0.9, 2), (0.4, 0.9), (0.18, 0.4)]
def metrica(field, a, b_):
    ra, rb = a * M.R_SOL_PX, b_ * M.R_SOL_PX
    rows = np.arange(ra, rb, 4.0)
    Nphi = int(2 ** math.ceil(math.log2(2 * math.pi * rb * 1.2)))
    phi = np.linspace(0, 2 * math.pi, Nphi, endpoint=False)
    P = np.zeros(Nphi // 2 + 1); n = 0
    for rr_ in rows:
        yy = cy + rr_ * np.sin(phi); xx = cx + rr_ * np.cos(phi)
        s = map_coordinates(field, [yy, xx], order=1, mode="nearest"); s -= s.mean()
        P += np.abs(np.fft.rfft(s)) ** 2; n += 1
    P /= n; m = np.arange(len(P)); out = {}
    for (d0, d1) in BANDES_DEG:
        sel = (m >= 360.0 / d1) & (m < 360.0 / d0)
        out[f"{d0}-{d1}"] = math.sqrt(2 * P[sel].sum()) / Nphi
    return out
lnL = np.log(np.maximum(np.nan_to_num(L), 1e-3)).astype(np.float32)
def informe(nom, lnt):
    for (a, b_) in ((1.25, 1.4), (2.05, 2.55), (3.2, 3.8), (4.0, 4.6)):
        mo = metrica(lnt, a, b_); ml = metrica(lnL, a, b_)
        print(f"  {nom:9s} anell {a}-{b_}: " + "  ".join(f"{k}:{mo[k]:.4f}({mo[k]/max(ml[k],1e-9):.1f}x)" for k in mo))

sy, sx = cy - M.RETALL[0], cx - M.RETALL[2]; Rp = M.R_SOL_PX
retalls = {
    "plomalls_nord": (int(sy - 1.9 * Rp), int(sy - 1.0 * Rp), int(sx - 0.45 * Rp), int(sx + 0.45 * Rp)),
    "zoom_plomall": (int(sy - 1.55 * Rp), int(sy - 1.15 * Rp), int(sx - 0.2 * Rp), int(sx + 0.2 * Rp)),
    "zoom_limbe_E": (int(sy - 0.2 * Rp), int(sy + 0.2 * Rp), int(sx + 1.02 * Rp), int(sx + 1.42 * Rp)),
    "zoom_2.3_N": (int(sy - 2.5 * Rp), int(sy - 2.1 * Rp), int(sx - 0.2 * Rp), int(sx + 0.2 * Rp)),
    "cel_3.5_est": (int(sy - 0.45 * Rp), int(sy + 0.45 * Rp), int(sx + 3.05 * Rp), int(sx + 3.95 * Rp)),
    "cercle_5.2_dalt": (0, 900, int(sx - 450), int(sx + 450)),
    "corona_SE": (int(sy + 0.6 * Rp), int(sy + 1.5 * Rp), int(sx + 0.9 * Rp), int(sx + 1.8 * Rp)),
    "streamer_W": (int(sy - 0.45 * Rp), int(sy + 0.45 * Rp), int(sx - 3.0 * Rp), int(sx - 2.1 * Rp)),
}
img_now = cv2.imread(str(OUT / "corona_vixen_FOTO.tif"), cv2.IMREAD_UNCHANGED)
if img_now is not None and img_now.dtype == np.uint16:
    img_now = (img_now / 257.0).astype(np.uint8)
    if img_now.ndim == 3 and img_now.shape[2] == 4: img_now = img_now[..., :3]
log(f"FOTO actual llegida: {None if img_now is None else img_now.shape}")

VARIANTS = {
    "E1": dict(G_SCALE=1.0, PHI_EXP=0.5, PHI_CAP=2.0, W_K=1.5, KAPPA=3.0, PSF_FLOOR=2.5),
    "E2": dict(G_SCALE=0.75, PHI_EXP=0.5, PHI_CAP=2.0, W_K=1.5, KAPPA=3.0, PSF_FLOOR=2.5),
}
for nom, kw in VARIANTS.items():
    print(f"\n=== variant {nom}: {kw}")
    lnt = build(**kw)
    t, img = imatge(lnt); log(f"render {nom}")
    informe(nom, np.log(t))
    rmD = ring_mean(lnt - lnt_rad)
    print("  mitjana d'anell del detall x1000 (4.8..7.5):", " ".join(f"{1000*rmD[int(rq*Rp)]:+.2f}" for rq in np.arange(4.8, 7.6, 0.3) if int(rq*Rp) < nb))
    # perfil de t per anell prop del cercle inscrit (el que Pere mesurava)
    rt = ring_mean(t)
    print("  t mitja d'anell 4.9..5.5:", " ".join(f"{rt[int(rq*Rp)]:.4f}" for rq in np.arange(4.9, 5.55, 0.05)))
    cv2.imwrite(f"{SCR}/foto_{nom}_2400.jpg", cv2.resize(img, (2400, 1600), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
    if img_now is not None and img_now.shape[:2] == img.shape[:2]:
        for rn, (y0, y1, x0, x1) in retalls.items():
            a = img_now[y0:y1, x0:x1]; b_ = img[y0:y1, x0:x1]
            sep = np.full((a.shape[0], 12, 3), 255, np.uint8)
            mos = np.concatenate([a, sep, b_], axis=1)
            if rn.startswith("zoom"): mos = cv2.resize(mos, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(f"{SCR}/retall_{nom}_{rn}.jpg", mos, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(f"{SCR}/foto_{nom}_full.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])
log("fet")
