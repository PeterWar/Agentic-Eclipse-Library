"""Mesura: senyal/soroll per banda ANGULAR i per radi sobre el compost lineal.

Nomes llegeix; escriu resultats al scratchpad.
"""
import sys, math, json, time
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import map_coordinates
import cv2

SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
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
base, perfil = M.perfil_azimutal(np.where(valid, L, np.nan), r, r_complet, cy, cx)
print(f"carregat i perfil: {time.time()-t0:.0f}s", flush=True)

# --- 0. hi ha ripple radial a L mateix (no nomes al perfil)?  perfil mitja d'anell de G
ib = r.astype(np.int32)
n = int(ib.max()) + 1
w_ok = valid & np.isfinite(G_)
sumG = np.bincount(ib[w_ok], weights=G_[w_ok].astype(np.float64), minlength=n)
cnt = np.bincount(ib[w_ok], minlength=n)
prof_full = np.where(cnt > 60, sumG / np.maximum(cnt, 1), np.nan)
np.save(f"{SCR}/prof_full_G.npy", prof_full)
np.save(f"{SCR}/perfil_base.npy", perfil)
np.save(f"{SCR}/cnt_anell.npy", cnt)

# --- 1. norm com a etapa_foto
q = np.where(valid, L / np.maximum(base, 1e-9), 1.0).astype(np.float32)
corr = M.desenfoca_valid(q, valid, 250.0)
base2 = base * np.maximum(corr, 1e-3)
norm = np.where(valid, L / np.maximum(base2, 1e-6), 1.0).astype(np.float32)
vG = np.nan_to_num(varm[..., 1])
sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base2, 1e-6)).astype(np.float32)
del varm, vG, q, corr
cel_z = valid & (rs > 4.0) & (rs < 5.1)
_ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
obs = float(np.std((norm - M.desenfoca(norm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig[cel_z]))
sig = sig * (obs / esp)
print(f"calibratge soroll: mapa {esp:.5f} mesurat {obs:.5f} x{obs/esp:.3f}", flush=True)
lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)

# perfil radial de norm (ripple del quocient)
sumN = np.bincount(ib[valid], weights=norm[valid].astype(np.float64), minlength=n)
cntN = np.bincount(ib[valid], minlength=n)
prof_norm = np.where(cntN > 60, sumN / np.maximum(cntN, 1), np.nan)
np.save(f"{SCR}/prof_norm.npy", prof_norm)

# --- 2. camp de soroll sintetic amb la correlacio del drizzle, escalat per sig_log
rng = np.random.default_rng(1)
z = rng.standard_normal((H, W)).astype(np.float32)
z = cv2.blur(z, (2, 2), borderType=cv2.BORDER_REFLECT)
z /= float(z.std())
zn = z * sig_log
del z
print(f"soroll sintetic: {time.time()-t0:.0f}s", flush=True)

# --- 3. espectres azimutals per anell
anells_R = [(1.08, 1.18), (1.25, 1.40), (1.5, 1.7), (1.9, 2.1), (2.05, 2.55), (2.6, 3.0), (3.2, 3.8), (4.0, 4.6), (4.8, 5.15)]
BANDES_DEG = [(18, 72), (6, 18), (2, 6), (0.9, 2), (0.4, 0.9), (0.18, 0.4), (0.08, 0.18)]
res = {}
for (a, b) in anells_R:
    ra, rb = a * M.R_SOL_PX, b * M.R_SOL_PX
    rows = np.arange(ra, rb, 3.0)
    Nphi = int(2 ** math.ceil(math.log2(2 * math.pi * rb * 1.2)))
    phi = np.linspace(0, 2 * math.pi, Nphi, endpoint=False)
    P_obs = np.zeros(Nphi // 2 + 1); P_n = np.zeros_like(P_obs); P_d = np.zeros_like(P_obs)
    nrows = 0; nd = 0
    prev = None
    for rr in rows:
        yy = cy + rr * np.sin(phi); xx = cx + rr * np.cos(phi)
        s = map_coordinates(lnorm, [yy, xx], order=1, mode="nearest")
        v = map_coordinates(valid.astype(np.float32), [yy, xx], order=1, mode="nearest")
        if v.min() < 0.999:
            continue
        zz = map_coordinates(zn, [yy, xx], order=1, mode="nearest")
        s = s - s.mean(); zz = zz - zz.mean()
        F = np.fft.rfft(s); Fz = np.fft.rfft(zz)
        P_obs += np.abs(F) ** 2; P_n += np.abs(Fz) ** 2; nrows += 1
        if prev is not None:
            Fd = np.fft.rfft(s - prev)
            P_d += np.abs(Fd) ** 2; nd += 1
        prev = s
    if nrows == 0:
        continue
    P_obs /= nrows; P_n /= nrows; P_d /= max(nd, 1) * 2.0
    m = np.arange(len(P_obs))
    fila = {}
    for (d0, d1) in BANDES_DEG:
        m0, m1 = 360.0 / d1, 360.0 / d0
        sel = (m >= m0) & (m < m1)
        # rms azimutal de la banda: sqrt(2*sum P / N^2)  (Parseval per a rfft)
        rms_o = math.sqrt(2 * P_obs[sel].sum()) / Nphi
        rms_n = math.sqrt(2 * P_n[sel].sum()) / Nphi
        rms_d = math.sqrt(2 * P_d[sel].sum()) / Nphi
        sig2 = max(rms_o ** 2 - rms_d ** 2, 0.0)
        fila[f"{d0}-{d1}"] = dict(rms_obs=rms_o, rms_noise_map=rms_n, rms_noise_diff=rms_d,
                                  rms_signal=math.sqrt(sig2), snr=math.sqrt(sig2) / max(rms_d, 1e-12))
    res[f"{a}-{b}"] = fila
    print(f"\nanell {a}-{b} Rsol ({nrows} files, Nphi={Nphi}, {time.time()-t0:.0f}s)")
    print("   banda(deg)   rms_obs   n_mapa   n_diff   senyal    S/N")
    for k, f in fila.items():
        print(f"   {k:>9}  {f['rms_obs']:.5f}  {f['rms_noise_map']:.5f}  {f['rms_noise_diff']:.5f}  {f['rms_signal']:.5f}  {f['snr']:6.2f}")
    sys.stdout.flush()

json.dump(res, open(f"{SCR}/snr_bandes.json", "w"), indent=1)
print("fet", time.time() - t0)
