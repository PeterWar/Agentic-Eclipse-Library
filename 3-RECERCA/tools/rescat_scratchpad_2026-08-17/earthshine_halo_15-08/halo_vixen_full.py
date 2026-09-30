#!/usr/bin/env python3
"""Etapa 2 — Vixen: model de halo de dos nuclis (SENSE LROC a l'ajust), pila
10,3 s (+2 s si passa la porta), i etapa 3: porta de fusio amb la Sony i pila
unica. Graella comuna: binat x3 del Vixen (6,474 arcsec/px) = binat x2 Sony.
"""
import json, os, re, time
import numpy as np, tifffile
from scipy.ndimage import shift as ndshift, gaussian_filter, map_coordinates, rotate
from numpy.fft import rfft2, irfft2

S = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"
CAL = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Calibrated_Claude"
OUTV = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Earthshine_Claude"
OUTS = "/Users/USUARI/Desktop/Eclipse 2026/300mm/Earthshine_Claude"
OUTF = "/Users/USUARI/Desktop/Eclipse 2026/Earthshine_FINAL"
os.makedirs(OUTF, exist_ok=True)
HW = 1200; B = 3; N = 2*HW//B          # 800
R_FULL = 452.6; R = R_FULL/B           # 150.9
SAT16 = 65000.0
def log(m): print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

limb = {f["name"]: f for f in np.load(f"{S}/limb_v3.npy", allow_pickle=True)}
exif = json.load(open(f"{S}/exif_unfiltered.json"))
def pe(s):
    s = str(s); m = re.match(r"^(\d+)/(\d+)$", s)
    return int(m.group(1))/int(m.group(2)) if m else (10.3 if s == "10" else float(s))
expo = {os.path.basename(x["SourceFile"]).replace(".CR3", ""): pe(x["ExposureTime"]) for x in exif}
LADDER = [f"572A{n}" for n in range(2967, 2985)]          # 1/2000 ... 10,3 s, t=12..54
CIENCIA = {"10s": ["572A2982", "572A2983", "572A2984"], "2s": ["572A2979", "572A2980", "572A2981"]}
centres = {n: (limb[n]["moon_x"], limb[n]["moon_y"]) for n in LADDER}
cache = {}
def crop(name):
    if name in cache: return cache[name]
    cx, cy = centres[name]
    img = tifffile.imread(f"{CAL}/{name}_cal.tif")[..., 1].astype(np.float32)
    ci, cj = int(round(cx)), int(round(cy))
    y0, x0 = cj-HW-4, ci-HW-4
    sub = np.zeros((2*HW+8, 2*HW+8), np.float32) + np.nan
    ys, xs = slice(max(y0, 0), min(y0+2*HW+8, img.shape[0])), slice(max(x0, 0), min(x0+2*HW+8, img.shape[1]))
    sub[ys.start-y0:ys.stop-y0, xs.start-x0:xs.stop-x0] = img[ys, xs]
    sub = np.nan_to_num(sub, nan=np.nanmedian(sub))
    sub = ndshift(sub, (-(cy-cj), -(cx-ci)), order=1, mode="nearest")[4:-4, 4:-4]
    sat = sub > SAT16
    b = sub.reshape(N, B, N, B).mean(axis=(1, 3)); bsat = sat.reshape(N, B, N, B).max(axis=(1, 3)) > 0
    cache[name] = (b, bsat); return cache[name]
yy, xx = np.mgrid[0:N, 0:N]
rr = np.hypot(xx-N/2+0.5, yy-N/2+0.5)
disc_src = rr < R+6; fitmask = rr < 133.5; inner = fitmask; disc = rr < R
def source_map(name):
    order = sorted(LADDER, key=lambda n: -expo[n]); ref_exp = expo[name]
    src = np.full((N, N), np.nan, np.float32)
    for n in order:
        b, bsat = crop(n); scaled = b*(ref_exp/expo[n]); take = np.isnan(src) & ~bsat; src[take] = scaled[take]
    still = np.isnan(src)
    if still.any():
        b, bsat = crop(order[-1]); src[still] = (b*(ref_exp/expo[order[-1]]))[still]
    src[disc_src] = 0
    return src
P = 2048
ky, kx = np.mgrid[0:P, 0:P]; kd = np.hypot(np.minimum(kx, P-kx), np.minimum(ky, P-ky))
def kernel_fft(s, beta):
    K = 1.0/(1.0+(kd/s)**2)**beta; K /= K.sum(); return rfft2(K)
def convolve(src, KF):
    pad = np.zeros((P, P), np.float32); o = (P-N)//2; pad[o:o+N, o:o+N] = src
    return irfft2(rfft2(pad)*KF, s=(P, P))[o:o+N, o:o+N]

log("retalls Vixen (18 fotogrames)...")
for n in LADDER: crop(n)
obs = {n: crop(n)[0] for n in CIENCIA["10s"]}
src = {n: source_map(n) for n in CIENCIA["10s"]}
NARROW = [(s, b_) for s in (1.5, 3, 6, 12, 24) for b_ in (0.6, 1.0, 1.5)]
WIDE = [(s, b_) for s in (40, 80, 160, 320, 640) for b_ in (0.6, 1.0, 1.5, 2.5)]
CONV = {}
for k in NARROW+WIDE:
    KF = kernel_fft(*k)
    for n in CIENCIA["10s"]: CONV[(k, n)] = convolve(src[n], KF)
X1 = (xx-N/2)/N; Y1 = (yy-N/2)/N
def design(k1, k2):
    rows, rhs = [], []
    for i, n in enumerate(CIENCIA["10s"]):
        m = fitmask
        cols = [CONV[(k1, n)][m], CONV[(k2, n)][m], X1[m], Y1[m]] + [np.ones(m.sum()) if j == i else np.zeros(m.sum()) for j in range(3)]
        rows.append(np.stack(cols, 1)); rhs.append(obs[n][m])
    return np.vstack(rows), np.concatenate(rhs)
best = None
for k1 in NARROW:
    for k2 in WIDE:
        Amat, bvec = design(k1, k2); sol, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
        rms = float(np.sqrt(np.mean((bvec-Amat@sol)**2)))
        if sol[0] < 0 or sol[1] < 0: rms += 1e6
        if best is None or rms < best[0]: best = (rms, k1, k2, sol)
rms, k1, k2, sol = best; A1, A2 = sol[0], sol[1]
log(f"VIXEN 2 nuclis (sense LROC): proper s={k1[0]} beta={k1[1]} A1={A1:.4f} · ample s={k2[0]} beta={k2[1]} A2={A2:.4f} · pla=({sol[2]:.0f},{sol[3]:.0f}) · rms={rms:.1f}")
KF1, KF2 = kernel_fft(*k1), kernel_fft(*k2); plane = sol[2]*X1 + sol[3]*Y1
def emap(name):
    b, _ = crop(name); sc = source_map(name)
    halo = A1*convolve(sc, KF1) + A2*convolve(sc, KF2)
    E = (b - halo - plane*(expo[name]/10.3))/expo[name]; E[~disc] = 0; E[disc] -= np.median(E[inner]); return E
def hf_noise(E): return float((E-gaussian_filter(E, 2.5))[inner].std())
def ncc(a, b, m):
    a = a[m]-a[m].mean(); b = b[m]-b[m].mean(); return float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b)))
gate_mask = rr < 120
def hp(img, sg=25): return gaussian_filter(img, 1.5) - gaussian_filter(img, sg)

# LROC en orientacio Sony (la graella final): reutilitza el de la Sony (mateixa geometria binada)
son = np.load(f"{S}/halo_sony_result_noLROC.npz")
LROC_S = son["LROCn"]; LROCz = LROC_S.copy(); LROCz[~disc] = 0
def to_sony(Ev): return rotate(Ev, 327.25, reshape=False, order=1)
def r_full(Emap): return ncc(gaussian_filter(Emap, 1.5), gaussian_filter(LROCz, 1.5), gate_mask)
def r_hp(Emap): return ncc(hp(Emap), hp(LROCz), gate_mask)
E, sig = {}, {}
for lay in ("10s", "2s"):
    for n in CIENCIA[lay]:
        E[n] = to_sony(emap(n)); sig[n] = hf_noise(E[n])
        log(f"  {lay} {n}: sigma={sig[n]:.1f} ADU16/s · r_hp(LROC)={r_hp(E[n]):.3f} · r_full(LROC)={r_full(E[n]):.3f}")
num = np.zeros((N, N)); den = 0.0; vstacks = {}
for lay in ("10s", "2s"):
    for n in CIENCIA[lay]: num += E[n]/sig[n]**2; den += 1/sig[n]**2
    vstacks[lay] = num/den
    log(f"  => Vixen pila fins {lay}: r_hp(LROC)={r_hp(vstacks[lay]):.3f} · r_full(LROC)={r_full(vstacks[lay]):.3f} · soroll={hf_noise(vstacks[lay]):.2f}")
# porta de la capa 2 s del Vixen
vix_final = vstacks["10s"] if r_full(vstacks["10s"]) >= r_full(vstacks["2s"]) else vstacks["2s"]
vix_lay = "10s" if vix_final is vstacks["10s"] else "10s+2s"
log(f"Vixen: capa acceptada = {vix_lay}")

# ── etapa 3: porta de fusio Sony (2x8 s, sense LROC) + Vixen ─────────────
sony8 = son["stack8"]; sig_s = hf_noise(sony8); sig_v = hf_noise(vix_final)
r_sv_hp = ncc(hp(sony8), hp(vix_final), gate_mask); r_sv_full = ncc(gaussian_filter(sony8, 1.5), gaussian_filter(vix_final, 1.5), gate_mask)
log(f"Sony8 vs Vixen (mateixa graella/orientacio): r_hp={r_sv_hp:.3f} · r_full={r_sv_full:.3f}")
# unitats: totes dues en ADU16/s del seu propi cos; per combinar, escala el Vixen a la Sony per guany (regressio lineal dins del disc) — nomes guany+offset, com demanava Codex
m = gate_mask
g = np.polyfit(vix_final[m], sony8[m], 1); vix_scaled = np.polyval(g, vix_final); vix_scaled[~disc] = 0
sig_vs = hf_noise(vix_scaled)
w_s, w_v = 1/sig_s**2, 1/sig_vs**2
fused = (sony8*w_s + vix_scaled*w_v)/(w_s+w_v); fused[~disc] = 0
log(f"guany Vixen->Sony {g[0]:.3f} · pesos Sony {w_s/(w_s+w_v):.2f} / Vixen {w_v/(w_s+w_v):.2f}")
for tag, im in (("Sony 2x8 s", sony8), ("Vixen", vix_scaled), ("FUSIO", fused)):
    log(f"  {tag}: r_hp(LROC)={r_hp(im):.3f} · r_full(LROC)={r_full(im):.3f} · soroll={hf_noise(im):.2f} ADU16/s")
# residu inter-tren: te estructura?
resid = sony8 - vix_scaled
log(f"residu Sony-Vixen: rms {resid[m].std():.2f} · r_hp(residu, LROC)={r_hp(resid):.3f} (ha de ser ~0 si el residu no te estructura d'albedo)")
gate_ok = r_full(fused) >= r_full(sony8) - 0.005 and r_hp(fused) >= r_hp(sony8) - 0.005
log(f"PORTA DE FUSIO: {'PASSA' if gate_ok else 'NO PASSA'} (la fusio no empitjora cap validacio fora de mostra)")
final = fused if gate_ok else sony8
np.savez(f"{S}/earthshine_final.npz", final=final, sony8=sony8, vixen=vix_scaled, fused=fused, gate_ok=gate_ok, LROC=LROC_S,
         A1=A1, A2=A2, k1=k1, k2=k2, rms=rms, r_final_full=r_full(final), r_final_hp=r_hp(final))
tifffile.imwrite(f"{OUTV}/earthshine_VIXEN_halo_model_stack_ADU16_per_s_orientSony.tif", vix_final.astype(np.float32))
tifffile.imwrite(f"{OUTF}/earthshine_FINAL_ADU16_per_s_lineal.tif", final.astype(np.float32))
def viewable(r_, mm, k=3.0):
    s_ = r_[mm].std(); v = np.clip((r_/(k*s_)+1)/2, 0, 1); v[~mm] = 0.0; return (v*65535).astype(np.uint16)
tifffile.imwrite(f"{OUTF}/earthshine_FINAL_visible.tif", viewable(gaussian_filter(final, 1.0), disc), compression="zlib")
tifffile.imwrite(f"{OUTF}/earthshine_SONY_2x8s_visible.tif", viewable(gaussian_filter(sony8, 1.0), disc), compression="zlib")
tifffile.imwrite(f"{OUTF}/earthshine_VIXEN_visible.tif", viewable(gaussian_filter(vix_scaled, 1.0), disc), compression="zlib")
log(f"escrit a {OUTF} · producte final = {'FUSIO Sony+Vixen' if gate_ok else 'Sony 2x8 s'}")
