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
CAL = "/Users/USUARI/Desktop/Eclipse 2026/300mm/calibrated"
OUT = "/Users/USUARI/Desktop/Eclipse 2026/300mm/Earthshine_Claude"
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

