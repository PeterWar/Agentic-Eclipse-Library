"""(1) vora vàlida i radi inscrit REAL; (2) <D>(r) 3–8,5 R☉; (3) mitjana de cada banda
vs distància a la vora superior; (4) anisotropia del cel a 11–47 px; (5) espectre
azimutal amb diferència radial i soroll simulat."""
import sys, time, math
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import map_coordinates
from pathlib import Path
import cv2
SCR = Path("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad")
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)
OUT = M.OUT
hdr = np.load(OUT / "hdr_vixen_countss.npy")
varm = np.load(OUT / "hdr_vixen_var.npy")
H, W, _ = hdr.shape
cy, cx = H / 2.0, W / 2.0
r = M.anells(H, W, cy, cx); rs = r / M.R_SOL_PX
valid = np.all(np.isfinite(hdr), axis=2)
R_, G_ = hdr[..., 0], hdr[..., 1]
ref = valid & (rs > 1.3) & (rs < 1.5)
kr = float(np.median(G_[ref]) / np.median(R_[ref]))
L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan).astype(np.float32)
vG = np.nan_to_num(varm[..., 1]).astype(np.float32)
del hdr, varm, R_, G_

# (1) vora vàlida
rows_ok = np.where(valid.any(axis=1))[0]; cols_ok = np.where(valid.any(axis=0))[0]
# radi inscrit real: distància mínima del centre a un píxel NO vàlid fora del disc
inval = ~valid & (rs > 2.0)
r_inscrit_real = float(r[inval].min())
log(f"files vàlides {rows_ok.min()}–{rows_ok.max()}, columnes {cols_ok.min()}–{cols_ok.max()}; "
    f"radi inscrit geomètric {min(H,W)/2:.0f} px = {min(H,W)/2/M.R_SOL_PX:.3f} R☉; "
    f"radi inscrit REAL de dades vàlides {r_inscrit_real:.0f} px = {r_inscrit_real/M.R_SOL_PX:.3f} R☉")
# on és el punt més proper?
iy, ix = np.unravel_index(np.argmin(np.where(inval, r, 1e9)), r.shape)
log(f"   el píxel invàlid més proper al centre és a fila {iy}, columna {ix}")
# fracció d'anell vàlid per radi entre 4,8 i 5,4 R☉
ib = r.astype(np.int32)
n = ib.max() + 1
tot = np.bincount(ib.ravel(), minlength=n); okc = np.bincount(ib[valid], minlength=n)
for rr in np.arange(4.8, 5.45, 0.05):
    k = int(rr * M.R_SOL_PX)
    print(f"   r={rr:.2f} R☉ ({k} px): fracció d'anell amb dades {okc[k]/max(tot[k],1):.4f}")

# base viva i D viu (com etapa_foto)
base, perfil = M.perfil_azimutal(np.where(valid, L, np.nan), r, min(H, W) / 2.0, cy, cx)
q = np.where(valid, L / np.maximum(base, 1e-9), 1.0).astype(np.float32)
corr = M.desenfoca_valid(q, valid, 250.0)
base2 = base * np.maximum(corr, 1e-3)
norm = np.where(valid, L / np.maximum(base2, 1e-6), 1.0).astype(np.float32)
lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base2, 1e-6)).astype(np.float32)
cel_z = valid & (rs > 4.0) & (rs < 5.1)
ks, t_hp = M.transferencia_soroll(M.BANDES_PX)
obs = float(np.std((norm - M.desenfoca(norm, 2.0))[cel_z])) / t_hp
esp = float(np.median(sig[cel_z])); sig *= obs / esp
sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)
esc = M.BANDES_PX; G = M.GUANYS_BANDA
prev = M.desenfoca_valid(lnorm, valid, esc[0])
b0 = M.desenfoca_valid(lnorm, valid, esc[1])
sig_cel = float(np.median(sig_log[cel_z]))
f_sist = max(float(np.sqrt(np.mean(((prev - b0)[cel_z]) ** 2))) / (ks[0] * sig_cel), 1.0)
D = np.zeros(lnorm.shape, np.float32)
# (3) mitjana de banda vs distància a la vora superior (columnes centrals cx±800), i a la inferior
top = rows_ok.min(); bot = rows_ok.max()
c0, c1 = int(cx - 800), int(cx + 800)
log(f"(3) mitjana de cada banda crua per franja de distància a la vora SUPERIOR (fila {top}) a les columnes {c0}–{c1}:")
franges = [(0, 20), (20, 50), (50, 100), (100, 200), (200, 350), (350, 600), (600, 900)]
print("   banda px     " + "  ".join(f"{a}-{b}".rjust(9) for a, b in franges) + "   | pes×guany al cel")
bandes = []
for j, (s0, s1) in enumerate(zip(esc[:-1], esc[1:])):
    seg = M.desenfoca_valid(lnorm, valid, s1)
    b = prev - seg; prev = seg
    row = []
    for a, bb in franges:
        sl = b[top + a: top + bb, c0:c1]
        row.append(f"{1e4*float(sl.mean()):+8.2f}")
    if G[j] > 0:
        n2 = (ks[j] * f_sist * sig_log) ** 2
        v = M.desenfoca(b ** 2, 4.0 * s1)
        w = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0, 1).astype(np.float32)
        D += G[j] * w * b
        wc = float(w[cel_z].mean())
    else:
        wc = 0.0
    print(f"  {s0:5.1f}-{s1:5.1f}  " + "  ".join(row) + f"   | {wc*G[j]:.2f}   (×1e-4)", flush=True)
    if 6.8 <= s0 <= 29:
        bandes.append((s0, s1, b))
D = np.clip(D, -0.7, 0.7)
# (2) <D>(r)
def ring_mean(x, m):
    w = np.bincount(ib[m], minlength=n).astype(np.float64)
    s = np.bincount(ib[m], weights=x[m].astype(np.float64), minlength=n)
    return np.where(w > 30, s / np.maximum(w, 1), np.nan)
rmD = ring_mean(D, valid)
log("(2) <D> per anell (×100), 3–8,5 R☉ cada 0,1:")
for rr in np.arange(3.0, 8.6, 0.1):
    k0, k1 = int(rr * M.R_SOL_PX), int((rr + 0.1) * M.R_SOL_PX)
    print(f"   {rr:.1f}: {100*np.nanmean(rmD[k0:k1]):+.3f}", end="  ")
    if abs((rr * 10) % 10 - 9) < 1e-6: print()
print()
# també per sectors: dalt, baix, esquerra, dreta a 5,0–5,4 (D mitjà)
ang = np.degrees(np.arctan2(-(np.arange(H) - cy)[:, None], (np.arange(W) - cx)[None, :]))
for nom, (a0, a1) in (("dreta", (-20, 20)), ("dalt", (70, 110)), ("esquerra", (160, 180)), ("baix", (-110, -70))):
    z = valid & (rs > 5.0) & (rs < 5.4) & (((ang > a0) & (ang < a1)) | ((nom == "esquerra") & (ang < -160)))
    z2 = valid & (rs > 4.4) & (rs < 4.8) & (((ang > a0) & (ang < a1)) | ((nom == "esquerra") & (ang < -160)))
    print(f"   <D> a 5,0–5,4 sector {nom}: {100*float(D[z].mean()):+.3f} %   a 4,4–4,8: {100*float(D[z2].mean()):+.3f} %")
np.save(SCR / "fable_D_viu.npy", D)

# (4) anisotropia del cel: espectre 2-D d'un tros de cel a 3,3–5,3 R☉ (esquerra), banda 11–47 px
log("(4) anisotropia del cel (esquerra del Sol), potència per direcció, longituds d'ona 11–47 px:")
y0, x0 = int(cy - 512), int(cx - 2450)
patch = lnorm[y0:y0 + 1024, x0:x0 + 1024].astype(np.float64)
pv = valid[y0:y0 + 1024, x0:x0 + 1024]
print(f"   tros vàlid: {pv.mean():.3f}; radi de {rs[y0:y0+1024, x0:x0+1024].min():.2f} a {rs[y0:y0+1024, x0:x0+1024].max():.2f} R☉")
patch = patch - patch.mean()
win = np.hanning(1024)[:, None] * np.hanning(1024)[None, :]
F = np.fft.fftshift(np.fft.fft2(patch * win))
P = np.abs(F) ** 2
ky = np.fft.fftshift(np.fft.fftfreq(1024))[:, None]; kx = np.fft.fftshift(np.fft.fftfreq(1024))[None, :]
kk = np.hypot(ky, kx); ang_k = np.degrees(np.arctan2(-ky, kx)) % 180   # direcció del vector d'ona
sel = (kk > 1 / 47) & (kk < 1 / 11)
for a0 in range(0, 180, 22):
    m = sel & (ang_k >= a0) & (ang_k < a0 + 22.5)
    print(f"   direcció d'ona {a0:3d}–{a0+22}°: potència relativa {P[m].mean()/P[sel].mean():.3f}")
print("   (la deriva va a 46,5° en (x, −y) → estries de patró fix ALLARGADES en aquella direcció "
      "→ excés de potència amb el vector d'ona PERPENDICULAR, ~136°)")
sel2 = (kk > 1 / 11) & (kk < 1 / 4)
print("   i a 4–11 px:")
for a0 in range(0, 180, 22):
    m = sel2 & (ang_k >= a0) & (ang_k < a0 + 22.5)
    print(f"   direcció d'ona {a0:3d}–{a0+22}°: potència relativa {P[m].mean()/P[sel2].mean():.3f}")

# (5) espectre azimutal amb diferència radial i soroll simulat
N = 16384; th = np.linspace(0, 2 * math.pi, N, endpoint=False)
bm = [(5, 20), (20, 60), (60, 180), (180, 400), (400, 900), (900, 2000), (2000, 4000)]
rng = np.random.default_rng(1)
z = rng.standard_normal((2048, 2048)).astype(np.float32)
z = cv2.blur(z, (2, 2), borderType=cv2.BORDER_REFLECT); z /= z.std()
def spec(x, r0px, c=(cy, cx), nrad=9, drad=4.0):
    P = np.zeros(N // 2 + 1); Pd = np.zeros(N // 2 + 1); cnt = 0
    for i in range(nrad):
        rr = r0px + (i - nrad // 2) * drad
        yy = c[0] + rr * np.sin(th); xx = c[1] + rr * np.cos(th)
        v = map_coordinates(x, [yy, xx], order=1, mode="nearest")
        yy2 = c[0] + (rr + 6) * np.sin(th); xx2 = c[1] + (rr + 6) * np.cos(th)
        v2 = map_coordinates(x, [yy2, xx2], order=1, mode="nearest")
        if not (np.all(np.isfinite(v)) and np.all(np.isfinite(v2))): continue
        v = v - v.mean(); v2 = v2 - v2.mean()
        P += np.abs(np.fft.rfft(v)) ** 2 / N ** 2; Pd += np.abs(np.fft.rfft((v - v2) / math.sqrt(2))) ** 2 / N ** 2; cnt += 1
    return P / max(cnt, 1), Pd / max(cnt, 1)
log("(5) contrast rms per banda azimutal m: total | diferència radial 6 px/√2 | soroll pur simulat")
print("  R☉   " + "".join(f"{a}-{b}".rjust(24) for a, b in bm))
for r0 in (1.15, 1.3, 1.5, 1.8, 2.3, 3.0, 3.7, 4.5, 5.0):
    P, Pd = spec(lnorm, r0 * M.R_SOL_PX)
    zz = valid & (rs > r0 * 0.98) & (rs < r0 * 1.02)
    s_pix = float(np.median(sig_log[zz]))
    # soroll pur: mostreig del mateix anell dins el camp sintètic (radi acotat al tros)
    rr_s = min(r0 * M.R_SOL_PX, 1000.0)
    Pn, _ = spec(z * s_pix, rr_s, c=(1024.0, 1024.0), nrad=5)
    row = f"  {r0:4.2f} "
    for a, b in bm:
        row += f"  {math.sqrt(2*P[a:b].sum()):.5f}/{math.sqrt(2*Pd[a:b].sum()):.5f}/{math.sqrt(2*Pn[a:b].sum()):.5f}"
    print(row, flush=True)
print("   ⚠️ el soroll simulat a radis > 1000 px està mostrejat a 1000 px (menys mostres per grau: cota superior)")
log("fi")
