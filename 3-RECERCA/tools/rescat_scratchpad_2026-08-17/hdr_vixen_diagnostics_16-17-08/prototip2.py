"""Prototip v2: detall ANGULAR, estadistica d'anell ROBUSTA, sense mitjana d'anell per banda.
Nomes llegeix repositori i sortida; escriu al scratchpad.
"""
import sys, math, json, time, os
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import gaussian_filter1d, gaussian_filter, map_coordinates
import cv2

SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
t0 = time.time()
def log(*a):
    print(f"[{time.time()-t0:5.0f}s]", *a, flush=True)

OUT = M.OUT
hdr = np.load(OUT / "hdr_vixen_countss.npy")
varm = np.load(OUT / "hdr_vixen_var.npy")
H, W, _ = hdr.shape
cy, cx = H / 2.0, W / 2.0
r = M.anells(H, W, cy, cx)
rs = r / M.R_SOL_PX
valid = np.all(np.isfinite(hdr), axis=2)
r_complet = min(H, W) / 2.0
R_, G_ = hdr[..., 0], hdr[..., 1]
ref = valid & (rs > 1.3) & (rs < 1.5)
kr = float(np.median(G_[ref]) / np.median(R_[ref]))
L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan)
base, perfil = M.perfil_azimutal(np.where(valid, L, np.nan), r, r_complet, cy, cx)
q = np.where(valid, L / np.maximum(base, 1e-9), 1.0).astype(np.float32)
corr = M.desenfoca_valid(q, valid, 250.0)
base = base * np.maximum(corr, 1e-3)
del q, corr
norm = np.where(valid, L / np.maximum(base, 1e-6), 1.0).astype(np.float32)
vG = np.nan_to_num(varm[..., 1])
sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base, 1e-6)).astype(np.float32)
del varm, vG
cel_z = valid & (rs > 4.0) & (rs < 5.1)
_ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
obs = float(np.std((norm - M.desenfoca(norm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig[cel_z]))
sig = sig * (obs / esp)
lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)
# ⚠️ el mapa de variancia te pixels aillats amb valors absurds (fins x1000): es retallen a 3x la mediana anular
ib = r.astype(np.int32)
nb = int(ib.max()) + 1
cnt = np.bincount(ib[valid], minlength=nb).astype(np.float64)
ok_r = cnt > 60
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

D_now = np.load(f"{SCR}/D_now.npy")

# ---------- piramide (dades i soroll sintetic), un cop
rng = np.random.default_rng(1)
zn = rng.standard_normal((H, W)).astype(np.float32)
zn = cv2.blur(zn, (2, 2), borderType=cv2.BORDER_REFLECT)
zn /= float(zn.std())
zn = (zn * sig_log).astype(np.float32)
ESC = M.BANDES_PX
DEG = 180.0 / math.pi
BANDS = []   # (s0, s1, b, bn)
prev = M.desenfoca_valid(lnorm, valid, ESC[0]); prevn = M.desenfoca_valid(zn, valid, ESC[0])
for s0, s1 in zip(ESC[:-1], ESC[1:]):
    seg = M.desenfoca_valid(lnorm, valid, s1); segn = M.desenfoca_valid(zn, valid, s1)
    BANDS.append((s0, s1, (prev - seg).astype(np.float32), (prevn - segn).astype(np.float32)))
    prev, prevn = seg, segn
del zn, prev, prevn, seg, segn
log("piramide feta")

# ---------- estadistica d'anell robusta per banda (un cop)
def robust_ring_power(x, m=None):
    """potencia d'anell robusta: (1,4826 · mediana |x|)^2 via mediana aproximada per anell.
    Per rapidesa: mitjana retallada a 4 sigma robusta, amb la sigma robusta feta amb la
    mitjana de |x| (per a gaussiana, mean|x| = 0,798 sigma)."""
    ax = np.abs(x)
    s_rob = ring_mean(ax, m) / 0.798
    lim = (4.0 * s_rob)[ib].astype(np.float32)
    mm = (ax <= lim)
    return ring_mean(x * x, mm if m is None else (m & mm))

STATS = []
zona_cel = (np.arange(nb) > 4.0 * M.R_SOL_PX) & (np.arange(nb) < 5.0 * M.R_SOL_PX)
for (s0, s1, b, bn) in BANDS:
    s_mid = math.sqrt(s0 * s1)
    rm = suavitza_r(ring_mean(b), max(3.0, 0.5 * s_mid))
    b -= rm[ib].astype(np.float32)          # ⛔ mata qualsevol anell: la banda queda amb mitjana d'anell zero
    pb = suavitza_r(robust_ring_power(b), max(6.0, 1.0 * s_mid))
    pn = suavitza_r(robust_ring_power(bn), max(6.0, 1.0 * s_mid))
    f2 = 1.0
    if s_mid < 9.0:
        f2 = max(1.0, float(np.nanmean(pb[zona_cel]) / max(np.nanmean(pn[zona_cel]), 1e-18)))
    pn = pn * f2
    STATS.append(dict(s_mid=s_mid, pb=pb, pn=pn, f2=f2))
    print(f"  banda {s0}-{s1}: f2={f2:.2f} (sistematic fi, en potencia)")
log("estadistica feta")

def build_D(G_MAX=9.0, TH0=1.5, SW=2.6, GAMMA_R=0.25, EQ_CAP=1.8, KAPPA=2.5, PSF_FLOOR=3.5, G_CAP=12.0, WPIX=True, verbose=True):
    SLN = math.log(SW)
    D = np.zeros((H, W), np.float32)
    rr = np.maximum(np.arange(nb, dtype=np.float64), 1.0)
    for (s0, s1, b, bn), st in zip(BANDS, STATS):
        s_mid = st["s_mid"]
        if s_mid < PSF_FLOOR:
            continue
        pb, pn = st["pb"], st["pn"]
        snr2 = np.maximum(pb / np.maximum(pn, 1e-18) - 1.0, 0.0)
        Wr = snr2 / (snr2 + 1.0)
        A = np.sqrt(np.maximum(pb - pn, 0.0))
        theta = (s_mid / rr) * DEG
        g = G_MAX * np.exp(-np.log(np.maximum(theta, 1e-6) / TH0) ** 2 / (2 * SLN ** 2)) * Wr
        ref_m = (rr > 1.5 * M.R_SOL_PX) & (rr < 2.5 * M.R_SOL_PX) & (A > 0)
        if ref_m.sum() > 10 and GAMMA_R > 0:
            A_ref = float(np.nanmedian(A[ref_m]))
            g = g * np.clip((A_ref / np.maximum(A, 1e-9)) ** GAMMA_R, 1.0 / EQ_CAP, EQ_CAP)
        g = np.minimum(suavitza_r(np.nan_to_num(g), max(6.0, 0.5 * s_mid)), G_CAP)
        if WPIX:
            n2 = pn[ib].astype(np.float32)
            v = M.desenfoca(b * b, 4.0 * s1)
            w = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
        else:
            w = 1.0
        beta = (KAPPA * np.maximum(A, 1e-6))[ib].astype(np.float32)
        D += g[ib].astype(np.float32) * w * (beta * np.tanh(b / beta))
        if verbose:
            fila = " ".join(f"r{rq}:th{theta[int(rq*M.R_SOL_PX)]:.2f}/snr{math.sqrt(snr2[int(rq*M.R_SOL_PX)]):.1f}/g{g[int(rq*M.R_SOL_PX)]:.1f}"
                            for rq in (1.2, 1.6, 2.3, 3.0, 3.5, 4.3, 5.2, 6.0, 7.0) if int(rq * M.R_SOL_PX) < nb)
            print(f"  {s0:5.1f}-{s1:5.1f}: {fila}")
    D = np.where(valid, D, 0.0)
    return np.clip(D, -0.7, 0.7)

# ---------- render (com etapa_foto, sense earthshine); retorna t i imatge 8 bits (t es display-referred)
srgb = (np.nan_to_num(hdr) * M.WB_DIURN) @ M.CAM_A_SRGB.T
Lum = np.maximum(srgb @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)
c = srgb / Lum[..., None]
Lp = np.where(valid, np.maximum(np.nan_to_num(L), 0.0), 0.0)
num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (10, 10, 0)); den = gaussian_filter(Lp, 10)
c = num / np.maximum(den, 1e-9)[..., None]
val_ext = valid | (rs < 1.30)
prou = gaussian_filter(val_ext.astype(np.float32), 10) > 0.995
zc = valid & (rs > 1.5) & (rs < 2.2); zs = valid & (rs > 6.2) & (rs < 7.0)
mc = np.array([float(np.median(c[..., i][zc])) for i in range(3)]); ms = np.array([float(np.median(c[..., i][zs])) for i in range(3)])
mc, ms = mc / mc[1], ms / ms[1]
c = np.where(prou[..., None], c, ms)
kc = np.array(M.OBJ_CORONA) / mc; ks = np.array(M.OBJ_CEL) / ms
cel_lin = float(np.median(np.nan_to_num(L)[zs]))
u = np.clip(np.log10(np.maximum(np.nan_to_num(L), cel_lin) / cel_lin) / math.log10(max(float(np.median(np.nan_to_num(L)[zc])) / cel_lin, 1.2)), 0, 1)[..., None]
CROMA = c * (kc * u + ks * (1 - u))
CROMA = CROMA / np.maximum(CROMA @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)[..., None]
del srgb, Lum, c, num, den, u
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
def render(D):
    u0 = a_u0(np.where(valid, L * np.exp(D), np.nan))
    lu = np.log(u0)
    t = np.exp(coef[0] + coef[1] * lu + coef[2] * lu ** 2)
    t = np.where(u0 > math.exp(ancs[0][0]), M.NIV_NUCLI + (1 - M.NIV_NUCLI) * (1 - np.exp(-(u0 / math.exp(ancs[0][0]) - 1) * 3)), t)
    t = np.clip(t, 0, 1).astype(np.float32)
    img = np.clip(CROMA * t[..., None], 0, 1); img = np.maximum(img, 0.004)
    img = img[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1]
    return t, (img * 255).astype(np.uint8)[..., ::-1]

# ---------- metrica: rms per banda angular de ln(t) a tres anells (com research/76 §5 decies)
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

def informe(nom, t):
    lt = np.log(np.maximum(np.nan_to_num(t), 1e-4)).astype(np.float32)
    for (a, b_) in ((1.25, 1.4), (2.05, 2.55), (3.2, 3.8)):
        mo = metrica(lt, a, b_); ml = metrica(lnorm, a, b_)
        print(f"  {nom:9s} anell {a}-{b_}: " + "  ".join(f"{k}:{mo[k]:.4f}({mo[k]/max(ml[k],1e-9):.1f}x)" for k in mo))

t_now, img_now = render(D_now); log("render ara")
informe("ARA", t_now)
cv2.imwrite(f"{SCR}/foto_ara_2400.jpg", cv2.resize(img_now, (2400, 1600), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])

VARIANTS = {
    "A": dict(G_MAX=9.0, TH0=1.5, SW=2.6, GAMMA_R=0.25, EQ_CAP=1.8, KAPPA=2.5),
    "B": dict(G_MAX=11.0, TH0=1.3, SW=2.6, GAMMA_R=0.35, EQ_CAP=2.0, KAPPA=2.5),
    "C": dict(G_MAX=9.0, TH0=1.5, SW=2.6, GAMMA_R=0.0, EQ_CAP=1.0, KAPPA=99.0),
}
sy, sx = cy - M.RETALL[0], cx - M.RETALL[2]; Rp = M.R_SOL_PX
retalls = {
    "plomalls_nord": (int(sy - 1.9 * Rp), int(sy - 1.0 * Rp), int(sx - 0.45 * Rp), int(sx + 0.45 * Rp)),
    "cel_3.5_est": (int(sy - 0.45 * Rp), int(sy + 0.45 * Rp), int(sx + 3.05 * Rp), int(sx + 3.95 * Rp)),
    "cercle_5.2_dalt": (0, 900, int(sx - 450), int(sx + 450)),
    "corona_SE": (int(sy + 0.6 * Rp), int(sy + 1.5 * Rp), int(sx + 0.9 * Rp), int(sx + 1.8 * Rp)),
    "streamer_W": (int(sy - 0.45 * Rp), int(sy + 0.45 * Rp), int(sx - 3.0 * Rp), int(sx - 2.1 * Rp)),
}
for nom, kw in VARIANTS.items():
    print(f"\n=== variant {nom}: {kw}")
    D = build_D(**kw)
    t, img = render(D); log(f"render {nom}")
    informe(nom, t)
    rmD = ring_mean(D)
    print("  mitjana d'anell de D x1000 (4.8..7.5):", " ".join(f"{1000*rmD[int(rq*Rp)]:+.2f}" for rq in np.arange(4.8, 7.6, 0.3) if int(rq*Rp) < nb))
    cv2.imwrite(f"{SCR}/foto_{nom}_2400.jpg", cv2.resize(img, (2400, 1600), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for rn, (y0, y1, x0, x1) in retalls.items():
        a = img_now[y0:y1, x0:x1]; b_ = img[y0:y1, x0:x1]
        sep = np.full((a.shape[0], 12, 3), 255, np.uint8)
        cv2.imwrite(f"{SCR}/retall_{nom}_{rn}.jpg", np.concatenate([a, sep, b_], axis=1), [cv2.IMWRITE_JPEG_QUALITY, 92])
    np.save(f"{SCR}/D_{nom}.npy", D)
log("fet")
