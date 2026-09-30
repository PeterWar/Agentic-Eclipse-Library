"""Prototip: detall ANGULAR amb bandes sense mitjana d'anell + Wiener d'anell.
Compara amb el detall actual (M.detall_bandes) i renderitza retalls.
Nomes llegeix el repositori i la carpeta de sortida; escriu al scratchpad.
"""
import sys, math, json, time, os
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import gaussian_filter1d, gaussian_filter
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
log("preparat")

# ---------------- detall ACTUAL
D_now = M.detall_bandes(lnorm, valid, sig_log, cel_z, M.GUANYS_BANDA)
D_now = np.clip(D_now, -0.7, 0.7)
np.save(f"{SCR}/D_now.npy", D_now)
log("D_now fet")

# ---------------- detall PROPOSAT
ib = r.astype(np.int32)
nb = int(ib.max()) + 1
cnt = np.bincount(ib[valid], minlength=nb).astype(np.float64)
ok_r = cnt > 60

def ring_mean(x):
    s = np.bincount(ib[valid], weights=x[valid].astype(np.float64), minlength=nb)
    return np.where(ok_r, s / np.maximum(cnt, 1), np.nan)

def suavitza_r(p, s):
    """suavitzat 1-D al llarg del radi, amb forats interpolats"""
    okk = np.isfinite(p)
    idx = np.arange(nb)
    p2 = np.interp(idx, idx[okk], p[okk]) if okk.sum() > 2 else np.nan_to_num(p)
    return gaussian_filter1d(p2, s, mode="nearest")

# soroll sintetic amb la correlacio del drizzle, escalat pel mapa calibrat
rng = np.random.default_rng(1)
zn = rng.standard_normal((H, W)).astype(np.float32)
zn = cv2.blur(zn, (2, 2), borderType=cv2.BORDER_REFLECT)
zn /= float(zn.std())
zn = (zn * sig_log).astype(np.float32)

ESC = M.BANDES_PX                          # mateixa piramide en px
DEG = 180.0 / math.pi
G_MAX = float(os.environ.get("G_MAX", "9.0"))
TH0 = float(os.environ.get("TH0", "1.7"))          # graus, centre de la gepa angular
SLN = math.log(float(os.environ.get("SW", "3.0")))  # amplada log de la gepa
GAMMA_R = float(os.environ.get("GAMMA_R", "0.5"))  # equalitzacio radial parcial
KAPPA = float(os.environ.get("KAPPA", "2.5"))      # genoll suau per banda (x rms d'anell)
PSF_FLOOR = 3.5                                     # px: per sota, guany zero

def G_theta(theta_deg):
    return G_MAX * np.exp(-np.log(np.maximum(theta_deg, 1e-6) / TH0) ** 2 / (2 * SLN ** 2))

D_new = np.zeros((H, W), np.float32)
prev = M.desenfoca_valid(lnorm, valid, ESC[0]); prevn = M.desenfoca_valid(zn, valid, ESC[0])
taula = []
zona_cel = ok_r & (rs.min() >= 0) & (np.arange(nb) > 4.0 * M.R_SOL_PX) & (np.arange(nb) < 5.1 * M.R_SOL_PX)
for j, (s0, s1) in enumerate(zip(ESC[:-1], ESC[1:])):
    seg = M.desenfoca_valid(lnorm, valid, s1); segn = M.desenfoca_valid(zn, valid, s1)
    b = prev - seg; bn = prevn - segn
    prev, prevn = seg, segn
    s_mid = math.sqrt(s0 * s1)
    if s_mid < PSF_FLOOR:
        taula.append((s0, s1, "PSF floor: guany 0"))
        continue
    # 1. mitjana d'anell de la banda -> es treu (mata qualsevol anell)
    rm = ring_mean(b)
    rm_s = suavitza_r(rm, max(3.0, 0.5 * s_mid))
    b = b - rm_s[ib].astype(np.float32)
    # 2. potencia d'anell: dades i soroll
    pb = suavitza_r(ring_mean(b * b), max(6.0, 1.0 * s_mid))
    pn = suavitza_r(ring_mean(bn * bn), max(6.0, 1.0 * s_mid))
    # sistematic d'escala fina: mesurat a 4-5,1 Rsol nomes per a bandes fines (alla es soroll pur)
    f2 = 1.0
    if s_mid < 8.0:
        f2 = max(1.0, float(np.nanmean(pb[zona_cel]) / max(np.nanmean(pn[zona_cel]), 1e-18)))
    pn = pn * f2
    snr2 = np.maximum(pb / np.maximum(pn, 1e-18) - 1.0, 0.0)
    Wr = snr2 / (snr2 + 1.0)                       # Wiener a nivell d'anell
    A = np.sqrt(np.maximum(pb - pn, 0.0))          # amplitud real de la banda per anell
    # 3. guany angular
    rr = np.maximum(np.arange(nb, dtype=np.float64), 1.0)
    theta = (s_mid / rr) * DEG
    g = G_theta(theta) * Wr
    # 4. equalitzacio radial parcial: referencia = amplitud a 1,5-2,5 Rsol on la banda te theta 0,5-6 graus
    ref_m = (rr > 1.5 * M.R_SOL_PX) & (rr < 2.5 * M.R_SOL_PX) & (A > 0)
    if ref_m.sum() > 10 and GAMMA_R > 0:
        A_ref = float(np.nanmedian(A[ref_m]))
        eq = np.clip((A_ref / np.maximum(A, 1e-9)) ** GAMMA_R, 0.33, 3.0)
        g = g * eq
    g = suavitza_r(np.nan_to_num(g), max(6.0, 0.5 * s_mid))
    # 5. porta per pixel (suau) i genoll suau
    n2 = (pn[ib]).astype(np.float32)
    v = M.desenfoca(b.astype(np.float32) ** 2, 4.0 * s1)
    w = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
    beta = (KAPPA * np.maximum(A, 1e-6))[ib].astype(np.float32)
    bk = beta * np.tanh(b / beta)
    D_new += (g[ib].astype(np.float32)) * w * bk
    # informe per radi
    fila = []
    for rq in (1.2, 1.6, 2.3, 3.0, 3.5, 4.3, 5.2, 6.0, 7.0):
        k = int(rq * M.R_SOL_PX)
        if k < nb:
            fila.append(f"r{rq}: th={theta[k]:.2f}deg snr={math.sqrt(snr2[k]):.1f} g={g[k]:.1f}")
    taula.append((s0, s1, f"f2={f2:.2f} | " + " ".join(fila)))
    log(f"banda {s0}-{s1}: " + taula[-1][2])
D_new = np.where(valid, D_new, 0.0)
D_new = np.clip(D_new, -0.7, 0.7)
np.save(f"{SCR}/D_new.npy", D_new)
log("D_new fet")

# ---------------- anell: mitjana d'anell de D_now i D_new prop del cercle inscrit
for nom, D in (("ara", D_now), ("proposta", D_new)):
    rmD = ring_mean(D)
    print(f"\n{nom}: mitjana d'anell de D (x1000)")
    for rq in np.arange(4.7, 7.6, 0.1):
        k = int(rq * M.R_SOL_PX)
        if k < nb and np.isfinite(rmD[k]):
            print(f"  {rq:4.1f}: {1000*rmD[k]:+7.2f}", end="")
    print()

# ---------------- render (luminancia + color, com etapa_foto sense earthshine)
def render(D):
    Lr = np.where(valid, L * np.exp(D), np.nan)
    Lc = Lr; Lc0 = L
    dins = valid & (rs > 1.03) & (rs < 6.0)
    lo = float(np.percentile(Lc0[dins], 0.02)) * 0.85
    hi = float(np.percentile(Lc0[valid & (rs < 1.06)], 99.6))
    def a_u0(x):
        u = (np.log10(np.maximum(np.nan_to_num(x), lo * 0.5)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
        u = np.where(u > 0.06, u, 0.06 * np.exp(np.minimum(u - 0.06, 0) / 0.06))
        return np.clip(u, 1e-4, None)
    u0 = a_u0(Lc); u0_ref = a_u0(Lc0)
    ancs = []
    for r0, niv in ((1.05, M.NIV_NUCLI), (2.0, M.NIV_CORONA), (6.8, M.NIV_CEL)):
        m = valid & (rs > r0 * 0.97) & (rs < r0 * 1.03)
        ancs.append((math.log(max(float(np.median(u0_ref[m])), 1e-9)), math.log(niv)))
    A = np.array([[1.0, a, a * a] for a, _ in ancs])
    coef = np.linalg.solve(A, np.array([b for _, b in ancs]))
    lu = np.log(u0)
    t = np.exp(coef[0] + coef[1] * lu + coef[2] * lu ** 2)
    t = np.where(u0 > math.exp(ancs[0][0]), M.NIV_NUCLI + (1 - M.NIV_NUCLI) * (1 - np.exp(-(u0 / math.exp(ancs[0][0]) - 1) * 3)), t)
    t = np.clip(t, 0, 1)
    # color
    srgb = (np.nan_to_num(hdr) * M.WB_DIURN) @ M.CAM_A_SRGB.T
    Lum = np.maximum(srgb @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)
    c = srgb / Lum[..., None]
    Lp = np.where(valid, np.maximum(np.nan_to_num(L), 0.0), 0.0)
    num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (10, 10, 0))
    den = gaussian_filter(Lp, 10)
    c = num / np.maximum(den, 1e-9)[..., None]
    val_ext = valid | (rs < 1.30)
    prou = gaussian_filter(val_ext.astype(np.float32), 10) > 0.995
    zc = valid & (rs > 1.5) & (rs < 2.2); zs = valid & (rs > 6.2) & (rs < 7.0)
    mc = np.array([float(np.median(c[..., i][zc])) for i in range(3)])
    ms = np.array([float(np.median(c[..., i][zs])) for i in range(3)])
    mc, ms = mc / mc[1], ms / ms[1]
    c = np.where(prou[..., None], c, ms)
    kc = np.array(M.OBJ_CORONA) / mc; ks = np.array(M.OBJ_CEL) / ms
    cel_lin = float(np.median(np.nan_to_num(L)[zs]))
    u = np.clip(np.log10(np.maximum(np.nan_to_num(L), cel_lin) / cel_lin) / math.log10(max(float(np.median(np.nan_to_num(L)[zc])) / cel_lin, 1.2)), 0, 1)[..., None]
    img = c * (kc * u + ks * (1 - u))
    img = img / np.maximum(img @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)[..., None]
    img = img * t[..., None]
    img = np.clip(img, 0, 1); img = np.maximum(img, 0.004)
    img = img[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1]
    return (M.a_srgb(img) * 255).astype(np.uint8)[..., ::-1]

img_now = render(D_now); log("render ara")
img_new = render(D_new); log("render proposta")
cv2.imwrite(f"{SCR}/foto_ara_2400.jpg", cv2.resize(img_now, (2400, 1600), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite(f"{SCR}/foto_prop_2400.jpg", cv2.resize(img_new, (2400, 1600), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
# retalls 1:1 (coordenades a la imatge retallada: sol a (cy-85, cx-40))
sy, sx = cy - M.RETALL[0], cx - M.RETALL[2]
Rp = M.R_SOL_PX
retalls = {
    "plomalls_nord": (int(sy - 1.9 * Rp), int(sy - 1.0 * Rp), int(sx - 0.45 * Rp), int(sx + 0.45 * Rp)),
    "cel_3.5_est": (int(sy - 0.45 * Rp), int(sy + 0.45 * Rp), int(sx + 3.05 * Rp), int(sx + 3.95 * Rp)),
    "cercle_5.2_dalt": (0, 900, int(sx - 450), int(sx + 450)),
    "corona_SE": (int(sy + 0.6 * Rp), int(sy + 1.5 * Rp), int(sx + 0.9 * Rp), int(sx + 1.8 * Rp)),
}
for nom, (y0, y1, x0, x1) in retalls.items():
    a = img_now[y0:y1, x0:x1]; b = img_new[y0:y1, x0:x1]
    sep = np.full((a.shape[0], 12, 3), 255, np.uint8)
    cv2.imwrite(f"{SCR}/retall_{nom}.jpg", np.concatenate([a, sep, b], axis=1), [cv2.IMWRITE_JPEG_QUALITY, 92])
json.dump({"taula": taula, "G_MAX": G_MAX, "TH0": TH0, "GAMMA_R": GAMMA_R, "KAPPA": KAPPA}, open(f"{SCR}/prototip_params.json", "w"), indent=1)
log("fet")
