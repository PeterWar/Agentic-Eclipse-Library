import sys, math
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
SP = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/"
z = np.load(SP + "bandes.npz")
valid = z["valid"]
H, W = valid.shape
cy, cx = H / 2.0, W / 2.0
# 1) efecte de la franja de vora sobre les bandes actuals (files 85–500, x central)
print("=== mitjana per files de les bandes 47-76 (b7) i 76-123 (b8) prop de la vora superior (x 2500-4500), en % ===")
b7, b8, b6 = z["b7"], z["b8"], z["b6"]
for y0 in (85, 100, 120, 150, 200, 250, 300, 400, 500, 700):
    sl = slice(y0, y0 + 15)
    m = valid[sl, 2500:4500]
    print(f"files {y0:4d}: b6(29-47) {100*float(b6[sl,2500:4500][m].mean()):+.3f}  b7 {100*float(b7[sl,2500:4500][m].mean()):+.3f}  b8 {100*float(b8[sl,2500:4500][m].mean()):+.3f}")

# 2) base amb la franja exclosa
hdr = np.load(M.OUT / "hdr_vixen_countss.npy", mmap_mode="r")
R_ = np.array(hdr[..., 0]); G_ = np.array(hdr[..., 1]); del hdr
r = M.anells(H, W, cy, cx); rs = r / M.R_SOL_PX
ref = valid & (rs > 1.3) & (rs < 1.5)
kr = float(np.median(G_[ref]) / np.median(R_[ref]))
L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan); del R_, G_
cob = np.load(M.OUT / "hdr_vixen_cobertura.npy", mmap_mode="r")
c1 = np.array(cob[..., 1]); del cob
print("cobertura verd: percentils 1/5/50 dins valid:", np.percentile(c1[valid], [1, 5, 50]))
print("cobertura a les files 42-49 (x central):", np.percentile(c1[42:50, 2500:4500], [5, 50, 95]), " files 60-70:", np.percentile(c1[60:70, 2500:4500], [5, 50, 95]))
lim = int(min(H, W) / 2.0)
vf = valid.copy()
vf[:60, :] = False; vf[H - 60:, :] = False; vf[:, :60] = False; vf[:, W - 60:] = False
ib = r.astype(np.int32); n = int(ib.max()) + 1
lim_m = int(0.97 * lim)
raw = np.full(n, np.nan)
for k in range(lim_m):
    m = vf & (ib == k)
    if m.sum() > 60:
        raw[k] = float(L[m].mean())
idx = np.arange(n); ok = np.isfinite(raw); k_min = int(idx[ok].min())
lnr = np.log(np.maximum(idx, 1))
lp = np.log(np.maximum(np.interp(idx, idx[ok], raw[ok]), 1e-9))
NG = 6000
g = np.linspace(lnr[k_min], lnr[lim_m - 1], NG)
lp_g = np.interp(g, lnr[k_min:lim_m], lp[k_min:lim_m]); dg = g[1] - g[0]
win = int(2 * round(2.5 * 0.03 / dg) + 1)
lp_sg = savgol_filter(lp_g, win, 2, mode="interp")
# extensió física: ln(A r^-a + B) ajustada a 3.5–5.0 Rsol
zf = (g >= math.log(3.5 * M.R_SOL_PX)) & (g <= math.log(5.0 * M.R_SOL_PX))
def f(x, lnA, a, lnB):
    return np.log(np.exp(lnA - a * x) + np.exp(lnB))
p0 = (lp_sg[zf][0] + 2.5 * g[zf][0], 2.5, lp_sg[zf][-1] - 0.5)
try:
    popt, _ = curve_fit(f, g[zf], lp_sg[zf], p0=p0, maxfev=20000)
    fit_all = f(lnr, *popt)
    print("ajust A r^-a + B: a =", popt[1], " B/L(5Rs) =", math.exp(popt[2]) / math.exp(f(math.log(5*M.R_SOL_PX), *popt)))
except Exception as e:
    print("ajust físic ha fallat:", e); cf = np.polyfit(g[zf], lp_sg[zf], 2); fit_all = np.polyval(cf, lnr)
lp_in = np.interp(lnr, g, lp_sg)
u = np.clip((lnr - math.log(0.80 * lim)) / (math.log(0.97 * lim) - math.log(0.80 * lim)), 0, 1)
wmix = u * u * (3 - 2 * u)
lp_new = (1 - wmix) * lp_in + wmix * fit_all
lp_new[:k_min] = lp_in[k_min]
perfil_n = np.exp(lp_new); base_n = perfil_n[np.clip(ib, 0, n - 1)]
q = np.where(vf, L / np.maximum(base_n, 1e-9), 1.0).astype(np.float32)
corr_n = M.desenfoca_valid(q, vf, 250.0)
base_n2 = base_n * np.maximum(corr_n, 1e-3)
lnorm_n = np.log(np.maximum(np.where(vf, L / base_n2, 1.0), 1e-3)).astype(np.float32)
yy = np.abs(np.arange(H) - cy)[:, None] * np.ones((1, W), np.float32)
tang = yy > 2200
def azim(x, r0, r1, pas, excl):
    e = np.arange(r0, r1, pas); out = []
    for a, b in zip(e[:-1], e[1:]):
        m = vf & (rs >= a) & (rs < b) & ~excl
        out.append(float(x[m].mean()) if m.sum() > 100 else np.nan)
    return e[:-1], np.array(out)
print("\n=== ln(norm) mitjà per anell, base NOVA amb franja exclosa, sense la tangència, 4.4–5.7 (pas 0.04) ===")
e, v = azim(lnorm_n, 4.4, 5.7, 0.04, tang)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))
print("=== dispersió d'anell a anell (rms de la diferència entre bins veïns), 3.0–5.1 Rsol: ")
e, v = azim(lnorm_n, 3.0, 5.1, 0.02, tang)
print(f"  {100*float(np.nanstd(np.diff(v))):.3f} %  (màxim |dif| {100*float(np.nanmax(np.abs(np.diff(v)))):.3f} %)")
# comparació amb la base actual (del mesura1: perfil_act) al mateix criteri
perfil_c = np.load(SP + "perfil_act.npy"); base_c = perfil_c[np.clip(ib, 0, n - 1)]
q = np.where(vf, L / np.maximum(base_c, 1e-9), 1.0).astype(np.float32)
corr_c = M.desenfoca_valid(q, vf, 250.0)
lnorm_c = np.log(np.maximum(np.where(vf, L / (base_c * np.maximum(corr_c, 1e-3)), 1.0), 1e-3)).astype(np.float32)
print("=== mateix, base ACTUAL (sense tangència) ===")
e, v = azim(lnorm_c, 4.4, 5.7, 0.04, tang)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))
e, v = azim(lnorm_c, 3.0, 5.1, 0.02, tang)
print(f"  dispersió anell a anell {100*float(np.nanstd(np.diff(v))):.3f} %  (màxim {100*float(np.nanmax(np.abs(np.diff(v)))):.3f} %)")
