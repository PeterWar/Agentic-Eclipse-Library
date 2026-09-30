#!/usr/bin/env python3
"""Etapa 1 — Sony: model fisic de halo i piles niades d'earthshine.

Tot en retalls alineats a la Lluna (centre de limbe de cada fotograma),
binats x2 (6,468 arcsec/px), 800x800 (r < 800 px de resolucio plena).

Model dins del disc:  obs = A * (Font_corona (*) K_ales) + b * LROC + c
  - Font_corona: HDR del grup del fotograma (cascada per saturacio), disc lunar
    a zero (la Lluna no emet).
  - K_ales(d) = 1/(1+(d/s)^2)^beta, unitari; A = fraccio de llum a les ales.
  - LROC: mapa d'albedo orientat (rot 71,5, libracio +4/-1), suavitzat.
Ajust de (s, beta) per graella, (A, b, c) lineals, sobre les dues ancores de
8 s conjuntament. Despres, el mateix nucli s'aplica als 2 s i 1 s.
"""
import json, os, re, time
import numpy as np, tifffile
from scipy.ndimage import shift as ndshift, gaussian_filter, map_coordinates
from numpy.fft import rfft2, irfft2

S = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"
CAL = "/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA/calibrated"
OUT = "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Earthshine/Historic/Earthshine_Claude_Sony"
HW = 800          # semiamplada del retall en px de resolucio plena
B = 2             # binat
N = 2*HW//B       # 800
R_FULL = 302.0
R = R_FULL/B      # 151 px binats
SAT16 = 65000.0

def log(m): print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

limb = {f["name"]: f for f in np.load(f"{S}/limb_sony.npy", allow_pickle=True)}
exif = json.load(open(f"{S}/exif_sony.json"))
def pe(s):
    s = str(s); m = re.match(r"^(\d+)/(\d+)$", s)
    return int(m.group(1))/int(m.group(2)) if m else float(s)
expo = {os.path.basename(x["SourceFile"]).replace(".ARW", ""): pe(x["ExposureTime"]) for x in exif}

GROUPS = {
    "T1": ["DSC06982", "DSC06983", "DSC06984"],
    "A1": ["DSC06985", "DSC06986", "DSC06987", "DSC06983", "DSC06981"],   # + 1/30 de T1 + 1/100 de C2
    "A3": ["DSC06991", "DSC06992", "DSC06993", "DSC06995", "DSC06981"],
    "T2": ["DSC06994", "DSC06995", "DSC06996"],
    "T3": ["DSC06997", "DSC06998", "DSC06999"],
}
CIENCIA = {"8s": ["DSC06987", "DSC06993"], "2s": ["DSC06984", "DSC06996", "DSC06999"], "1s": ["DSC06985", "DSC06991"]}
GROUP_OF = {"DSC06987": "A1", "DSC06993": "A3", "DSC06984": "T1", "DSC06996": "T2", "DSC06999": "T3",
            "DSC06985": "A1", "DSC06991": "A3"}

# centres: els del limbe; DSC06981 (contacte, 1/100) no te limbe -> el de 06982 desplacat pel moviment relatiu (~1,7 px): negligible al binat
centres = {n: (f["moon_x"], f["moon_y"]) for n, f in limb.items()}
centres["DSC06981"] = centres["DSC06982"]

cache = {}
def crop(name):
    """retall alineat a la Lluna, binat x2, en ADU16 (float32)."""
    if name in cache: return cache[name]
    cx, cy = centres[name]
    img = tifffile.imread(f"{CAL}/{name}_cal.tif")[..., 1].astype(np.float32)
    ci, cj = int(round(cx)), int(round(cy))
    sub = img[cj-HW-4:cj+HW+4, ci-HW-4:ci+HW+4]
    sub = ndshift(sub, (-(cy-cj), -(cx-ci)), order=1, mode="nearest")[4:-4, 4:-4]
    sat = (sub > SAT16)
    b = sub.reshape(N, B, N, B).mean(axis=(1, 3))
    bsat = sat.reshape(N, B, N, B).max(axis=(1, 3)) > 0
    cache[name] = (b, bsat)
    return cache[name]

yy, xx = np.mgrid[0:N, 0:N]
rr = np.hypot(xx-N/2+0.5, yy-N/2+0.5)
disc_src = rr < R+6          # font zero (Lluna)
fitmask = rr < 133.5         # r<267 plena
inner = fitmask

# ── LROC orientat (mateixa geometria) ───────────────────────────────────
M = np.load(f"{S}/lroc_4k_gray.npy").astype(np.float32); MH, MW = M.shape
u = (xx-N/2+0.5)/R; v = -(yy-N/2+0.5)/R; rr2 = u*u+v*v; disc = rr2 < 1
w = np.sqrt(np.clip(1-rr2, 0, None))
def render(theta_deg, lon0, lat0):
    th = np.radians(theta_deg)
    uu = u*np.cos(th) - v*np.sin(th); vv = u*np.sin(th) + v*np.cos(th)
    la0, lo0 = np.radians(lat0), np.radians(lon0)
    o = np.array([np.cos(la0)*np.cos(lo0), np.cos(la0)*np.sin(lo0), np.sin(la0)])
    zax = np.array([0, 0, 1.0]); Y = zax - np.dot(zax, o)*o; Y /= np.linalg.norm(Y); X = np.cross(Y, o)
    P = uu[..., None]*X + vv[..., None]*Y + w[..., None]*o
    lon = np.degrees(np.arctan2(P[..., 1], P[..., 0])); lat = np.degrees(np.arcsin(np.clip(P[..., 2], -1, 1)))
    xm = (lon/360.0)*MW + 2048; ym = (90-lat)/180.0*MH
    g = map_coordinates(M, [ym.ravel(), xm.ravel()], order=1, mode="wrap").reshape(N, N); g[~disc] = 0
    return g
LROC = gaussian_filter(render(71.5, 4, -1), 1.0); LROC[~disc] = 0
LROCn = LROC/LROC[disc].mean()      # normalitzat a mitjana 1 dins del disc

# ── HDR de font per grup ─────────────────────────────────────────────────
def source_map(group):
    names = GROUPS[group]
    order = sorted(names, key=lambda n: -expo[n])     # de mes llarg a mes curt
    ref_exp = expo[order[0]]
    src = np.full((N, N), np.nan, np.float32)
    for n in order:
        b, bsat = crop(n)
        scaled = b*(ref_exp/expo[n])
        take = np.isnan(src) & ~bsat
        src[take] = scaled[take]
    still = np.isnan(src)
    if still.any():
        b, bsat = crop(order[-1]); src[still] = (b*(ref_exp/expo[order[-1]]))[still]   # cota inferior
    src[disc_src] = 0
    return src, ref_exp, int(still.sum())

# ── nucli i convolucio FFT ───────────────────────────────────────────────
P = 2048
ky, kx = np.mgrid[0:P, 0:P]
kd = np.hypot(np.minimum(kx, P-kx), np.minimum(ky, P-ky))   # distancia amb wrap (nucli centrat a l'origen)
def kernel_fft(s, beta):
    K = 1.0/(1.0+(kd/s)**2)**beta
    K /= K.sum()
    return rfft2(K)
def convolve(src, KF):
    pad = np.zeros((P, P), np.float32); o = (P-N)//2
    pad[o:o+N, o:o+N] = src
    out = irfft2(rfft2(pad)*KF, s=(P, P))
    return out[o:o+N, o:o+N]

# ── ajust conjunt: DOS nuclis (ales properes + dispersio ampla) + pla de cel + LROC ──
log("retalls i fonts...")
obs8, src8 = {}, {}
for n in CIENCIA["8s"]:
    obs8[n] = crop(n)[0]
    src8[n], ref_exp, nsat = source_map(GROUP_OF[n])
NARROW = [(s, b_) for s in (1.5, 3, 6, 12, 24) for b_ in (0.6, 1.0, 1.5)]
WIDE = [(s, b_) for s in (40, 80, 160, 320, 640) for b_ in (0.6, 1.0, 1.5, 2.5)]
log(f"precalcul de {len(NARROW)+len(WIDE)} convolucions x 2 fotogrames...")
CONV = {}
for k in NARROW + WIDE:
    KF = kernel_fft(*k)
    for n in CIENCIA["8s"]:
        CONV[(k, n)] = convolve(src8[n], KF)
X1 = (xx-N/2)/N; Y1 = (yy-N/2)/N
def design(k1, k2, with_lroc=True, with_plane=True):
    rows, rhs = [], []
    for i, n in enumerate(CIENCIA["8s"]):
        m = fitmask
        cols = [CONV[(k1, n)][m], CONV[(k2, n)][m]]
        if with_lroc: cols.append(LROCn[m])
        if with_plane: cols += [X1[m], Y1[m]]
        cols += [np.ones(m.sum()) if j == i else np.zeros(m.sum()) for j in range(2)]
        rows.append(np.stack(cols, 1)); rhs.append(obs8[n][m])
    return np.vstack(rows), np.concatenate(rhs)
best = None
for k1 in NARROW:
    for k2 in WIDE:
        Amat, bvec = design(k1, k2)
        sol, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
        rms = float(np.sqrt(np.mean((bvec-Amat@sol)**2)))
        if sol[0] < 0 or sol[1] < 0: rms += 1e6      # amplituds fisiques
        if best is None or rms < best[0]: best = (rms, k1, k2, sol)
rms, k1, k2, sol = best
A1, A2, bL = sol[0], sol[1], sol[2]
log(f"MILLOR 2 nuclis: proper s={k1[0]} beta={k1[1]} A1={A1:.4f} · ample s={k2[0]} beta={k2[1]} A2={A2:.4f} · b_LROC={bL:.1f} · pla=({sol[3]:.0f},{sol[4]:.0f}) · c={sol[5]:.0f},{sol[6]:.0f} · rms={rms:.1f}")
for tag, kw in (("sense LROC", dict(with_lroc=False)), ("sense pla", dict(with_plane=False))):
    Amat, bvec = design(k1, k2, **kw); s2, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
    log(f"   control {tag}: rms={float(np.sqrt(np.mean((bvec-Amat@s2)**2))):.1f}")
halo8 = {n: A1*CONV[(k1, n)] + A2*CONV[(k2, n)] for n in CIENCIA["8s"]}
log(f"pedestal de halo al centre del disc: {np.mean([halo8[n][N//2-5:N//2+5, N//2-5:N//2+5].mean() for n in CIENCIA['8s']]):.0f} ADU16 · a r=250 (plena): {np.mean([halo8[n][(rr>123)&(rr<127)].mean() for n in CIENCIA['8s']]):.0f}")
log(f"earthshine mitja al disc (8 s): b*mean(LROC)= {bL:.0f} ADU16  (positiu = fisic)")
KF1, KF2 = kernel_fft(*k1), kernel_fft(*k2)
plane = sol[3]*X1 + sol[4]*Y1

def emap(name):
    b, _ = crop(name)
    src, ref_exp, _ = source_map(GROUP_OF[name])
    scaled = src*(expo[name]/ref_exp)
    halo = A1*convolve(scaled, KF1) + A2*convolve(scaled, KF2)
    E = (b - halo - plane*(expo[name]/8.0))/expo[name]
    E[~disc] = 0
    E[disc] -= np.median(E[inner])
    return E
def hf_noise(E):
    d = E - gaussian_filter(E, 2.5); return float(d[inner].std())
def ncc(a, b, m):
    a = a[m]-a[m].mean(); b = b[m]-b[m].mean()
    return float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b)))
gate_mask = rr < 120
LROCz = LROCn.copy(); LROCz[~disc] = 0
def hp(img, sg=25): return gaussian_filter(img, 1.5) - gaussian_filter(img, sg)
def r_full(Emap): return ncc(gaussian_filter(Emap, 1.5), gaussian_filter(LROCz, 1.5), gate_mask)
def r_hp(Emap): return ncc(hp(Emap), hp(LROCz), gate_mask)
E, sig = {}, {}
for lay in ("8s", "2s", "1s"):
    for n in CIENCIA[lay]:
        E[n] = emap(n); sig[n] = hf_noise(E[n])
ref = (E["DSC06987"]/sig["DSC06987"]**2 + E["DSC06993"]/sig["DSC06993"]**2)/(1/sig["DSC06987"]**2 + 1/sig["DSC06993"]**2)
def r_ref(Emap): return ncc(hp(Emap), hp(ref), gate_mask)
log("porta per capa:")
num = np.zeros((N, N)); den = 0.0; stacks = {}
for lay in ("8s", "2s", "1s"):
    for n in CIENCIA[lay]:
        log(f"  {lay} {n}: sigma={sig[n]:.1f} ADU16/s · r_hp(ref8)={r_ref(E[n]) if lay!='8s' else float('nan'):.3f} · r_hp(LROC)={r_hp(E[n]):.3f} · r_full(LROC)={r_full(E[n]):.3f}")
    for n in CIENCIA[lay]:
        num += E[n]/sig[n]**2; den += 1/sig[n]**2
    stk = num/den; stacks[lay] = stk.copy()
    log(f"  => pila fins {lay}: r_hp(LROC)={r_hp(stk):.3f} · r_full(LROC)={r_full(stk):.3f} · soroll={hf_noise(stk):.2f}")
np.savez(f"{S}/halo_sony_result.npz", A1=A1, A2=A2, k1=k1, k2=k2, b=bL, plane=sol[3:5], rms=rms,
         E=np.stack([E[n] for lay in CIENCIA for n in CIENCIA[lay]]), names=[n for lay in CIENCIA for n in CIENCIA[lay]],
         sig=np.array([sig[n] for lay in CIENCIA for n in CIENCIA[lay]]), stack8=stacks["8s"], stack2=stacks["2s"], stack1=stacks["1s"],
         LROCn=LROCn, ref=ref, halo8=np.stack([halo8[n] for n in CIENCIA["8s"]]), obs8=np.stack([obs8[n] for n in CIENCIA["8s"]]))
tifffile.imwrite(f"{OUT}/earthshine_SONY_halo_model_stack_ADU16_per_s.tif", stacks["1s"].astype(np.float32))
log("etapa 1 (2 nuclis) acabada")
