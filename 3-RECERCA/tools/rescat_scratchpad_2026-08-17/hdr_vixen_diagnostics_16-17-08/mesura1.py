import sys, math, time
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

t0 = time.time()
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
vG = np.nan_to_num(varm[..., 1])
del hdr, varm
print(f"carregat {time.time()-t0:.0f}s  H={H} W={W} lim={int(r_complet)} = {r_complet/M.R_SOL_PX:.3f} Rsol")

# --- base actual
base_c, perfil_c = M.perfil_azimutal(np.where(valid, L, np.nan), r, r_complet, cy, cx)
q = np.where(valid, L / np.maximum(base_c, 1e-9), 1.0).astype(np.float32)
corr = M.desenfoca_valid(q, valid, 250.0)
base_c2 = base_c * np.maximum(corr, 1e-3)
lnorm_c = np.log(np.maximum(np.where(valid, L / base_c2, 1.0), 1e-3)).astype(np.float32)

def azim_mean(x, r0, r1, pas):
    edges = np.arange(r0, r1, pas)
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = valid & (rs >= a) & (rs < b)
        out.append(float(np.nanmean(x[m])) if m.sum() > 100 else np.nan)
    return edges[:-1], np.array(out)

print("\n=== ln(norm) mitjà per anell, base ACTUAL, 4.4–5.7 Rsol (pas 0.02) ===")
e, v = azim_mean(lnorm_c, 4.4, 5.7, 0.02)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))
print("=== 6.9–7.75 ===")
e, v = azim_mean(lnorm_c, 6.9, 7.75, 0.02)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))

# --- base proposada: perfil mesurat només fins a lim, suavitzat en ln r,
# extensió analítica quadràtica en (ln r, ln p) ajustada a 0.7–1.0 lim, mescla suau
ib = r.astype(np.int32)
n = int(ib.max()) + 1
lim = int(r_complet)
raw = np.full(n, np.nan)
bo = valid & np.isfinite(L)
for k in range(lim):
    m = bo & (ib == k)
    if m.sum() > 60:
        raw[k] = float(L[m].mean())
idx = np.arange(n)
ok = np.isfinite(raw)
k_min = int(idx[ok].min())
lnr = np.log(np.maximum(idx, 1))
lp = np.log(np.maximum(np.interp(idx, idx[ok], raw[ok]), 1e-9))
# suavitzat en ln r: remostrejar a reixa uniforme en ln r
NG = 6000
g = np.linspace(lnr[k_min], lnr[lim - 1], NG)
lp_g = np.interp(g, lnr[k_min:lim], lp[k_min:lim])
dg = g[1] - g[0]
sig_x = 0.03           # 3 % del radi
win = int(2 * round(2.5 * sig_x / dg) + 1)
lp_sg = savgol_filter(lp_g, win, 2, mode="interp")
# extensió: quadràtica en ln r sobre 0.7–1.0 lim
z0 = g >= math.log(0.70 * lim)
cf = np.polyfit(g[z0], lp_sg[z0], 2)
fit_all = np.polyval(cf, lnr)
lp_in = np.interp(lnr, g, lp_sg)
# mescla: 0 a 0.78 lim, 1 a 0.98 lim (smoothstep)
u = np.clip((lnr - math.log(0.78 * lim)) / (math.log(0.98 * lim) - math.log(0.78 * lim)), 0, 1)
wmix = u * u * (3 - 2 * u)
lp_new = (1 - wmix) * lp_in + wmix * fit_all
lp_new[:k_min] = lp_in[k_min]
perfil_n = np.exp(lp_new)
base_n = perfil_n[np.clip(ib, 0, n - 1)]
q = np.where(valid, L / np.maximum(base_n, 1e-9), 1.0).astype(np.float32)
corr_n = M.desenfoca_valid(q, valid, 250.0)
print(f"corr 2-D nova: {float(corr_n[valid].min()):.3f}–{float(corr_n[valid].max()):.3f}")
base_n2 = base_n * np.maximum(corr_n, 1e-3)
lnorm_n = np.log(np.maximum(np.where(valid, L / base_n2, 1.0), 1e-3)).astype(np.float32)
print("\n=== ln(norm) mitjà per anell, base NOVA, 4.4–5.7 ===")
e, v = azim_mean(lnorm_n, 4.4, 5.7, 0.02)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))
print("=== 6.9–7.75 ===")
e, v = azim_mean(lnorm_n, 6.9, 7.75, 0.02)
print(" ".join(f"{a:.2f}:{100*b:+.2f}" for a, b in zip(e, v)))
# diferència de perfils dins
print("\n=== perfil nou / perfil actual − 1 (%), r=1.05..7.7 cada 0.25 Rsol ===")
for rr in np.arange(1.05, 7.75, 0.25):
    k = int(rr * M.R_SOL_PX)
    print(f"{rr:.2f}:{100*(perfil_n[k]/perfil_c[k]-1):+.2f}", end="  ")
print()
np.save("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/perfil_nou.npy", perfil_n)
np.save("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/perfil_act.npy", perfil_c)

# --- soroll per píxel en unitats de ln(norm), calibrat com etapa_foto
sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base_n2, 1e-6)).astype(np.float32)
cel_z = valid & (rs > 4.0) & (rs < 5.1)
ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
norm = np.exp(lnorm_n)
obs = float(np.std((norm - M.desenfoca(norm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig[cel_z]))
sig = sig * (obs / esp)
sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)
print(f"\nsoroll: mapa {esp:.5f} mesurat {obs:.5f} factor {obs/esp:.3f}")

# --- S/N per banda i zona radial
zones = [(1.06, 1.25), (1.25, 1.6), (1.6, 2.2), (2.2, 3.0), (3.0, 4.0), (4.0, 5.0)]
esc = M.BANDES_PX
prev = M.desenfoca_valid(lnorm_n, valid, esc[0])
b0 = M.desenfoca_valid(lnorm_n, valid, esc[1])
f_sist = float(np.sqrt(np.mean(((prev - b0)[cel_z]).astype(np.float64) ** 2))) / max(ks[0] * float(np.median(sig_log[cel_z])), 1e-12)
print(f"f_sist {f_sist:.2f}")
ks = [k * max(f_sist, 1.0) for k in ks]
print("\n=== rms de banda (%) / soroll de banda (%) / S/N d'amplitud sqrt(max(rms²-n²,0))/n per zona ===")
print("banda px      " + "  ".join(f"{a:.2f}-{b:.2f}Rs" for a, b in zones))
bandes = {}
for j, (s0, s1) in enumerate(zip(esc[:-1], esc[1:])):
    seg = M.desenfoca_valid(lnorm_n, valid, s1)
    b = prev - seg
    prev = seg
    if s1 <= 123:
        bandes[j] = b.copy()
    row = []
    for (a, c) in zones:
        m = valid & (rs > a) & (rs < c)
        rms = float(np.sqrt(np.mean(b[m].astype(np.float64) ** 2)))
        nz = ks[j] * float(np.median(sig_log[m]))
        sn = math.sqrt(max(rms * rms - nz * nz, 0)) / max(nz, 1e-12)
        row.append(f"{100*rms:5.2f}/{100*nz:5.2f}/{sn:5.1f}")
    print(f"{s0:5.1f}-{s1:5.1f}  " + "  ".join(row))
    # graus per banda al centre de zona
print("angle (graus) del centre de banda per zona: " + "  ".join(
    f"{(math.sqrt(s0*s1))/(0.5*(a+c)*M.R_SOL_PX)*180/math.pi:.2f}" for (a, c) in zones for s0, s1 in [(6.8, 11.0)]))
np.savez("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/bandes.npz",
         **{f"b{j}": bandes[j] for j in bandes}, lnorm=lnorm_n, sig_log=sig_log, valid=valid)
print(f"total {time.time()-t0:.0f}s")
