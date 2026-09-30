"""Prototip (només escriu al scratchpad): detall per bandes cartesianes amb guany
segons l'ESCALA ANGULAR i aplicat DESPRÉS de la corba de to, domini = RETALL,
base amb continuació C¹, terra de soroll per banda mesurat al cel net, rampa
radial exterior, topall suau. Mesura: anell de D per sectors, i contrast per
banda azimutal de la sortida a 1,3 / 2,3 / 3,5 R☉ contra el LINEAL i contra la
FOTO viva."""
import os, sys, time, math, json
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import map_coordinates, gaussian_filter
from pathlib import Path
import cv2
SCR = Path("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad")
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)
G_MAX = float(os.environ.get("G_MAX", "10"))       # multiplicador de sortida al pic del gep
TH0 = float(os.environ.get("TH0", "1.2"))           # graus, centre del gep
WLN = math.log(float(os.environ.get("WGEP", "2.6")))  # amplada del gep en ln
G_REST = float(os.environ.get("G_REST", "1.0"))     # multiplicador de sortida per a 3-21°
BETA_CEL = float(os.environ.get("BETA_CEL", "1.2")) # terra = β · rms del cel net per banda
S_MIN = float(os.environ.get("S_MIN", "5.5"))       # px: sota d'això, guany 0 (rampa fins a 2×)
R_RAMPA = (4.5, 6.0)                                 # R☉: rampa exterior de guany 1 → 0,3
A_TOPALL = float(os.environ.get("A_TOPALL", "0.5"))
T_FINA_MAX = float(os.environ.get("T_FINA_MAX", "5.0"))
W_POT = float(os.environ.get("W_POT", "2.0"))
TAG = os.environ.get("TAG", "p1")

OUT = M.OUT
hdr = np.load(OUT / "hdr_vixen_countss.npy")
varm = np.load(OUT / "hdr_vixen_var.npy")
H, W, _ = hdr.shape
cy, cx = H / 2.0, W / 2.0
r = M.anells(H, W, cy, cx); rs = r / M.R_SOL_PX
valid = np.all(np.isfinite(hdr), axis=2)
caixa = np.zeros_like(valid)
caixa[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1] = True
valid &= caixa
R_, G_ = hdr[..., 0], hdr[..., 1]
ref = valid & (rs > 1.3) & (rs < 1.5)
kr = float(np.median(G_[ref]) / np.median(R_[ref]))
L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan).astype(np.float32)
vG = np.nan_to_num(varm[..., 1]).astype(np.float32)
del varm, R_, G_
r_full = float(r[~valid & (rs > 1.5)].min())
log(f"domini RETALL; radi d'anell complet r_full = {r_full:.0f} px = {r_full/M.R_SOL_PX:.3f} R☉")

# ---------- base: mitjanes d'anell exactes dins r_full, continuació C¹ enfora
ib = r.astype(np.int32); n = ib.max() + 1; idx = np.arange(n)
wc = np.bincount(ib[valid], minlength=n).astype(np.float64)
sc = np.bincount(ib[valid], weights=L[valid].astype(np.float64), minlength=n)
lim = int(r_full) - 2
prof = np.where((wc > 60) & (idx < lim), sc / np.maximum(wc, 1), np.nan)
ok = np.isfinite(prof); k_min = int(idx[ok].min())
lp = np.log(np.interp(idx, idx[ok], prof[ok]))
lp = np.convolve(np.pad(lp, 8, mode="edge"), np.ones(17) / 17, "valid")
lnr = np.log(np.maximum(idx, 1))
z0 = (idx >= 0.75 * lim) & (idx < lim)
cf = np.polyfit(lnr[z0], lp[z0], 2)
fit = np.polyval(cf, lnr)
u = np.clip((idx - 0.85 * lim) / (0.97 * lim - 0.85 * lim), 0, 1); u = u * u * (3 - 2 * u)
lp_new = (1 - u) * lp + u * fit
lp_new[:k_min] = lp[k_min]
perfil = np.exp(lp_new)
base = perfil[np.clip(ib, 0, n - 1)].astype(np.float32)
norm = np.where(valid, L / base, 1.0).astype(np.float32)
lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
sig_log = np.where(valid, np.sqrt(np.maximum(vG, 0)) / np.maximum(L, 1e-6), 0.0).astype(np.float32)
del vG
cel_z = valid & (rs > 4.0) & (rs < 5.0)
ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
obs = float(np.std((lnorm - M.desenfoca(lnorm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig_log[cel_z])); sig_log *= obs / esp
sig_cel = float(np.median(sig_log[cel_z]))
log(f"soroll ×{obs/esp:.3f}, sig_cel = {sig_cel:.5f}")

# ---------- corba de to (com etapa_foto, calibrada sobre L sense realçar) i el seu pendent
dins = valid & (rs > 1.03) & (rs < 6.0)
lo = float(np.percentile(L[dins], 0.02)) * 0.85
hi = float(np.percentile(L[valid & (rs < 1.06)], 99.6))
def a_u0(x):
    u = (np.log10(np.maximum(np.nan_to_num(x), lo * 0.5)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    u = np.where(u > 0.06, u, 0.06 * np.exp(np.minimum(u - 0.06, 0) / 0.06))
    return np.clip(u, 1e-4, None)
u0 = a_u0(L)
ancs = []
for r0, niv in ((1.05, M.NIV_NUCLI), (2.0, M.NIV_CORONA), (6.8, M.NIV_CEL)):
    m = valid & (rs > r0 * 0.97) & (rs < r0 * 1.03)
    ancs.append((math.log(max(float(np.median(u0[m])), 1e-9)), math.log(niv)))
A = np.array([[1.0, a, a * a] for a, _ in ancs]); coef = np.linalg.solve(A, np.array([b for _, b in ancs]))
def corba(x):
    uu = a_u0(x); lu = np.log(uu)
    t = np.exp(coef[0] + coef[1] * lu + coef[2] * lu ** 2)
    t = np.where(uu > math.exp(ancs[0][0]), M.NIV_NUCLI + (1 - M.NIV_NUCLI) * (1 - np.exp(-(uu / math.exp(ancs[0][0]) - 1) * 3)), t)
    return np.clip(t, 0, 1)
t = corba(L).astype(np.float32)
# pendent d ln t / d ln L sobre el perfil (funció suau del radi)
tp = corba(perfil * math.exp(0.02)); tm = corba(perfil * math.exp(-0.02))
pend_r = ((np.log(np.maximum(tp, 1e-6)) - np.log(np.maximum(tm, 1e-6))) / 0.04)
pend_r = np.convolve(np.pad(pend_r, 20, mode="edge"), np.ones(41) / 41, "valid")
pend = pend_r[np.clip(ib, 0, n - 1)].astype(np.float32)
log("pendent de la corba (d ln t/d ln L) al perfil: " + "  ".join(
    f"{rr}R☉={pend_r[int(rr*M.R_SOL_PX)]:.3f}" for rr in (1.1, 1.2, 1.3, 1.5, 1.8, 2.0, 2.3, 2.7, 3.0, 4.0, 5.0, 6.0)))

# ---------- bandes
esc = M.BANDES_PX
prev = M.desenfoca_valid(lnorm, valid, esc[0])
D = np.zeros(lnorm.shape, np.float32)
def ring_mean(x, m):
    w_ = np.bincount(ib[m], minlength=n).astype(np.float64)
    s_ = np.bincount(ib[m], weights=x[m].astype(np.float64), minlength=n)
    return np.where(w_ > 30, s_ / np.maximum(w_, 1), np.nan), w_
# distància a la vora del RETALL (per apodar les bandes amples)
yy = np.arange(H)[:, None]; xx = np.arange(W)[None, :]
dvora = np.minimum(np.minimum(yy - M.RETALL[0], M.RETALL[1] - yy), np.minimum(xx - M.RETALL[2], M.RETALL[3] - xx)).astype(np.float32)
rampa_ext = np.clip((R_RAMPA[1] - rs) / (R_RAMPA[1] - R_RAMPA[0]), 0, 1); rampa_ext = 0.3 + 0.7 * rampa_ext
def gep(theta_deg):
    return math.exp(-(math.log(theta_deg / TH0)) ** 2 / (2 * WLN ** 2))
log(f"guanys: G_MAX={G_MAX} a θ0={TH0}°, amplada ln {WLN:.2f}, restauració {G_REST} a 3–21°, S_MIN={S_MIN} px, β_cel={BETA_CEL}")
print("   banda px    rms cel net  soroll fotó   f_j   T(1.2R)  g(1.2R) T(2.3R) g(2.3R)  T(4R) g(4R)   w mitjà 1.2/2.3/3.5/4.5")
info = []
for j, (s0, s1) in enumerate(zip(esc[:-1], esc[1:])):
    seg = M.desenfoca_valid(lnorm, valid, s1)
    b = prev - seg; prev = seg
    smid = math.sqrt(s0 * s1)
    if smid < S_MIN * 0.7:
        print(f"  {s0:5.1f}-{s1:5.1f}  descartada (σ mitjana {smid:.1f} px < {S_MIN})")
        continue
    # 1. treu la mitjana d'anell de la banda (suavitzada radialment)
    rm, _ = ring_mean(b, valid)
    okr = np.isfinite(rm); rm = np.interp(idx, idx[okr], rm[okr])
    sr = max(30, int(1.5 * s1)); rm = np.convolve(np.pad(rm, sr, mode="edge"), np.ones(2 * sr + 1) / (2 * sr + 1), "valid")
    b = b - rm[np.clip(ib, 0, n - 1)].astype(np.float32)
    # 2. terra de soroll: fotó transferit × sistemàtic fi, o β × rms del cel net
    rms_cel = float(np.sqrt(np.mean(b[cel_z].astype(np.float64) ** 2)))
    n_fot = ks[j] * sig_cel
    f_j = rms_cel / max(n_fot, 1e-12)
    n2 = np.maximum(ks[j] * 2.3 * sig_log, BETA_CEL * rms_cel * np.sqrt(sig_log / sig_cel)) ** 2
    v = M.desenfoca(b * b, 4.0 * s1)
    w = (np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0) ** W_POT).astype(np.float32)
    # 3. guany en unitats de SORTIDA segons l'escala angular a cada radi
    theta = np.degrees(2.35 * smid / np.maximum(r, 1.0))   # FWHM angular del tret que la banda veu millor
    T = 1.0 + (G_MAX - 1.0) * np.exp(-(np.log(theta / TH0)) ** 2 / (2 * WLN ** 2))
    T = np.where(theta > 2.5, np.maximum(T, G_REST), T)    # restauració natural a 2,5–6°
    # per damunt de ~8° de FWHM no es restaura res: la corba mana (T → pendent → g = 0)
    fade = np.clip((10.0 - theta) / 4.0, 0, 1)
    T = pend + (T - pend) * fade
    T = np.minimum(T, T_FINA_MAX) if smid < 6.0 else T      # les bandes fines, com a molt ×T_FINA_MAX
    fina = np.clip(smid / S_MIN - 1.0, 0.0, 1.0)            # rampa òptica: 0 a S_MIN, 1 a 2·S_MIN
    g = np.maximum(T - pend, 0.0) * fina * rampa_ext
    # 4. apoda les bandes amples prop de la vora del retall
    apod = np.clip(dvora / (2.0 * s1), 0, 1)
    cont = (g * w * apod * b).astype(np.float32)
    D += cont
    def at(rr): return int(rr * M.R_SOL_PX)
    def wz(a, c):
        z = valid & (rs > a) & (rs < c); return float(w[z].mean())
    def gz(rr):
        z = valid & (rs > rr * 0.98) & (rs < rr * 1.02); return float(g[z].mean()), float(np.mean(T[z]))
    g12, T12 = gz(1.2); g23, T23 = gz(2.3); g4, T4 = gz(4.0)
    print(f"  {s0:5.1f}-{s1:5.1f}  {rms_cel:10.6f}  {n_fot:10.6f}  {f_j:5.1f}   {T12:5.2f}  {g12:5.2f}   {T23:5.2f}  {g23:5.2f}   {T4:5.2f} {g4:5.2f}   "
          f"{wz(1.15,1.3):.2f}/{wz(2.2,2.4):.2f}/{wz(3.4,3.6):.2f}/{wz(4.4,4.6):.2f}", flush=True)
    info.append(dict(banda=(s0, s1), rms_cel=rms_cel, f_j=f_j))
del prev, seg, b, v, w
D = (A_TOPALL * np.tanh(D / A_TOPALL)).astype(np.float32)
D = np.where(valid, D, 0.0)
np.save(SCR / f"fable_D_{TAG}.npy", D)
log(f"D: percentils 1/99 = {np.percentile(D[valid],1):+.3f}/{np.percentile(D[valid],99):+.3f}")
for (a_, c_) in ((1.1, 1.3), (1.3, 1.6), (2.2, 2.4), (3.4, 3.6), (4.4, 4.6)):
    z_ = valid & (rs > a_) & (rs < c_)
    print(f"   D a {a_}-{c_} R☉: sd {np.std(D[z_]):.3f}, p1/p99 {np.percentile(D[z_],1):+.3f}/{np.percentile(D[z_],99):+.3f}")

# ---------- anell de D per sectors i global, 1 px, 4,4–6,0 R☉
rmD, _ = ring_mean(D, valid)
print("  <D> anell global (×100) cada 0,05 R☉ de 4,4 a 6,0:")
print("   " + " ".join(f"{rr:.2f}:{100*np.nanmean(rmD[int(rr*M.R_SOL_PX):int((rr+0.05)*M.R_SOL_PX)]):+.3f}" for rr in np.arange(4.4, 6.0, 0.05)))
ang = np.degrees(np.arctan2(-(np.arange(H) - cy)[:, None], (np.arange(W) - cx)[None, :]))
for nom, (a0, a1) in (("dreta", (-20, 20)), ("dalt", (70, 110)), ("esquerra", (160, 200)), ("baix", (-110, -70))):
    aa = np.where(ang < -160, ang + 360, ang) if nom == "esquerra" else ang
    for (r0, r1) in ((4.4, 4.8), (4.8, 5.0), (5.0, 5.2), (5.2, 5.4), (5.4, 5.8)):
        z = valid & (rs > r0) & (rs < r1) & (aa > a0) & (aa < a1)
        if z.sum() > 500:
            print(f"     sector {nom:9s} {r0}-{r1}: <D>={100*float(D[z].mean()):+.3f} %  sd {100*float(D[z].std()):.3f}", end="")
    print()

# ---------- sortida: D DESPRÉS de la corba, topall suau a dalt
tt = t * np.exp(D)
tt = np.where(tt > 0.92, 0.92 + 0.08 * np.tanh((tt - 0.92) / 0.08), tt).astype(np.float32)

# ---------- mètrica: contrast per banda azimutal m de la luminància de SORTIDA vs LINEAL vs FOTO viva
N = 16384; th = np.linspace(0, 2 * math.pi, N, endpoint=False)
bm = [(5, 20), (20, 60), (60, 180), (180, 400), (400, 900), (900, 2000)]
def spec(x, r0px, c=(cy, cx), nrad=9, drad=4.0):
    P = np.zeros(N // 2 + 1); cnt = 0
    for i in range(nrad):
        rr = r0px + (i - nrad // 2) * drad
        v = map_coordinates(x, [c[0] + rr * np.sin(th), c[1] + rr * np.cos(th)], order=1, mode="nearest")
        if not np.all(np.isfinite(v)): continue
        v = v / v.mean() - 1.0
        P += np.abs(np.fft.rfft(v)) ** 2 / N ** 2; cnt += 1
    return P / max(cnt, 1)
import tifffile
foto = tifffile.imread(str(OUT / "corona_vixen_FOTO.tif")).astype(np.float32) / 65535.0
def srgb_lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
Yf = foto @ np.array([0.2126, 0.7152, 0.0722], np.float32)   # unitats de PANTALLA, com t
del foto
cf_ = (cy - M.RETALL[0], cx - M.RETALL[2])
print("  contrast rms per banda m (relatiu a la mitjana): LINEAL norm | FOTO viva (Y lineal) | PROTOTIP (t·e^D)")
print("  R☉    " + "".join(f"{a}-{b}".rjust(28) for a, b in bm))
for r0 in (1.15, 1.3, 1.6, 2.3, 3.0, 3.5, 4.5):
    P0 = spec(norm, r0 * M.R_SOL_PX); P1 = spec(Yf, r0 * M.R_SOL_PX, c=cf_); P2 = spec(tt, r0 * M.R_SOL_PX)
    row = f"  {r0:4.2f} "
    for a, b in bm:
        c0 = math.sqrt(2 * P0[a:b].sum()); c1 = math.sqrt(2 * P1[a:b].sum()); c2 = math.sqrt(2 * P2[a:b].sum())
        row += f"  {c0:.4f} {c1:.4f}({c1/c0:4.1f}) {c2:.4f}({c2/c0:4.1f})"
    print(row, flush=True)
del Yf

# ---------- render de previsualització (color com etapa_foto) i retalls 1:1
srgb = (np.nan_to_num(hdr) * M.WB_DIURN) @ M.CAM_A_SRGB.T
del hdr
Lr = np.maximum(srgb @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)
c = srgb / Lr[..., None]; del srgb, Lr
Lp = np.where(valid, np.maximum(np.nan_to_num(L), 0.0), 0.0)
num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (10, 10, 0)); den = gaussian_filter(Lp, 10)
c = num / np.maximum(den, 1e-9)[..., None]; del num, den
val_ext = valid | (rs < 1.30)
prou = gaussian_filter(val_ext.astype(np.float32), 10) > 0.995
zc = valid & (rs > 1.5) & (rs < 2.2); zs = valid & (rs > 6.2) & (rs < 7.0)
mc = np.array([float(np.median(c[..., i][zc])) for i in range(3)]); ms = np.array([float(np.median(c[..., i][zs])) for i in range(3)])
mc, ms = mc / mc[1], ms / ms[1]
c = np.where(prou[..., None], c, ms)
kc = np.array(M.OBJ_CORONA) / mc; ks_ = np.array(M.OBJ_CEL) / ms
cel_lin = float(np.median(np.nan_to_num(L)[zs]))
uu = np.clip(np.log10(np.maximum(np.nan_to_num(L), cel_lin) / cel_lin) / math.log10(max(float(np.median(np.nan_to_num(L)[zc])) / cel_lin, 1.2)), 0, 1)[..., None]
img = c * (kc * uu + ks_ * (1 - uu)); del c
img = img / np.maximum(img @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)[..., None]
img = (img * tt[..., None]).astype(np.float32)
cami = OUT / "earthshine_disc.npz"
if cami.exists():
    z = np.load(cami); d = z["disc"].astype(np.float64)
    dcy, dcx, rl = float(z["cy"]), float(z["cx"]), float(z["rl"])
    oy = float(z["lluna_y"]) - float(z["sol_y"]) + cy; ox = float(z["lluna_x"]) - float(z["sol_x"]) + cx
    yy2 = (np.arange(H) - oy)[:, None]; xx2 = (np.arange(W) - ox)[None, :]; rd = np.hypot(xx2, yy2)
    sy = (np.arange(H) - oy + dcy * 2) / 2.0; sx = (np.arange(W) - ox + dcx * 2) / 2.0
    gy = np.clip(sy, 0, d.shape[0] - 1).astype(int); gx = np.clip(sx, 0, d.shape[1] - 1).astype(int)
    relleu = gaussian_filter(d, 1.5)[np.ix_(gy, gx)]
    cua = np.clip((rl * 2 * 0.965 - rd) / (rl * 2 * 0.06), 0, 1)
    relleu = relleu * cua + np.median(relleu[rd < rl * 1.6]) * (1 - cua)
    q = np.percentile(relleu[rd < rl * 1.5], [3, 97]); ue = np.clip((relleu - q[0]) / max(q[1] - q[0], 1e-9), 0, 1)
    cel_t = float(np.median(tt[valid & (rs > 6.2) & (rs < 7.0)])); n0, n1 = cel_t * 1.25, cel_t * 2.1
    disc_t = n0 + (n1 - n0) * ue; c_es = np.array([1.07, 1.0, 0.93])
    buit = (~valid).astype(np.uint8); buit[rd > rl * 2 * 1.25] = 0
    buit[:M.RETALL[0]] = 0; buit[M.RETALL[1] + 1:] = 0; buit[:, :M.RETALL[2]] = 0; buit[:, M.RETALL[3] + 1:] = 0
    dist = cv2.distanceTransform(1 - buit, cv2.DIST_L2, 5).astype(np.float32)
    pes = np.clip(1.0 - dist / 14.0, 0, 1)[..., None]
    img = img * (1 - pes) + (disc_t[..., None] * c_es) * pes
img = np.clip(img, 0, 1); img = np.maximum(img, 0.004)
img = img[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1]
def srgb_enc(a): return np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(np.maximum(a, 0), 1 / 2.4) - 0.055)
im8 = (np.clip(img, 0, 1)[..., ::-1] * 255).astype(np.uint8)   # img ja és valor de pantalla
cv2.imwrite(str(SCR / f"fable_foto_{TAG}_2400.jpg"), cv2.resize(im8, (2400, 1600), interpolation=cv2.INTER_AREA), [int(cv2.IMWRITE_JPEG_QUALITY), 94])
# retalls 1:1: dalt (plomalls), esquerra a 3,5 R☉ (cel), regió a 5,0–5,3 R☉ dalt (anell), i cantonada
Cy, Cx = int(cy - M.RETALL[0]), int(cx - M.RETALL[2])
retalls = {"dalt_plomalls": (Cy - 1350, Cy - 470, Cx - 500, Cx + 500),
           "esquerra_2R": (Cy - 450, Cy + 450, Cx - 1500, Cx - 500),
           "cel_3.5R_dreta": (Cy - 400, Cy + 400, Cx + 1150, Cx + 2050),
           "anell_5R_dalt": (Cy - 2234, Cy - 1900, Cx - 900, Cx + 900),
           "cantonada_dreta_baix": (Cy + 1500, Cy + 2276, Cx + 2200, Cx + 3300)}
for nom, (y0, y1, x0, x1) in retalls.items():
    y0, x0 = max(y0, 0), max(x0, 0)
    cv2.imwrite(str(SCR / f"fable_{TAG}_{nom}.jpg"), im8[y0:y1, x0:x1], [int(cv2.IMWRITE_JPEG_QUALITY), 95])
log("fi")
