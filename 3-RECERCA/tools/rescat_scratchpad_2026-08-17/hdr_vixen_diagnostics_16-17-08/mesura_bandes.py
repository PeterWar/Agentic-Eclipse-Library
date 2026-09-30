"""Contrast rms per banda angular d'una FOTO, contra el compost lineal."""
import os, sys, math
import numpy as np, cv2, tifffile
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M

OUT = M.OUT; NA = 4096
BANDES = [(5,20),(20,60),(60,180),(180,400),(400,900),(900,2000)]

def polar(img, cy, cx, nr):
    return cv2.warpPolar(np.nan_to_num(img, nan=0.0).astype(np.float32),
                         (nr, NA), (cx, cy), float(nr),
                         cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR)

def bandes(pol, rr, r0, r1):
    sel = (rr > r0) & (rr < r1)
    b = pol[:, sel].astype(np.float64)
    b = b / np.maximum(b.mean(0, keepdims=True), 1e-12) - 1.0
    F = np.fft.rfft(b * np.hanning(NA)[:, None], axis=0)
    P = (np.abs(F)**2).mean(1)
    esc = 2.0 / (NA * (np.hanning(NA)**2).sum())
    return {(lo,hi): math.sqrt(max(P[lo:hi].sum()*esc, 0.0)) for lo,hi in BANDES}

hdr = np.load(OUT / "hdr_vixen_countss.npy")
H, W, _ = hdr.shape; cy, cx = H/2.0, W/2.0
L = hdr[...,1]; valid = np.all(np.isfinite(hdr), axis=2)
r = M.anells(H, W, cy, cx)
base, _ = M.perfil_azimutal(np.where(valid, L, np.nan), r, min(H,W)/2.0)
norm = np.where(valid, L/np.maximum(base,1e-9), 1.0)
del hdr, L

capes = {"LINEAL": norm}
for nom in sys.argv[1:]:
    f = tifffile.imread(OUT / nom)
    f = f.astype(np.float64)/65535.0 if f.dtype == np.uint16 else f.astype(np.float64)
    g = np.full((H, W), np.nan)
    g[M.RETALL[0]:M.RETALL[1]+1, M.RETALL[2]:M.RETALL[3]+1] = f[...,1]
    capes[nom.replace("corona_vixen_","").replace(".tif","")] = g
    del f

nr = int(min(H,W)/2)
pols = {k: polar(v, cy, cx, nr) for k, v in capes.items()}
rr = np.arange(nr)/M.R_SOL_PX
for r0, r1 in [(1.35,1.65),(2.05,2.55),(3.15,3.85)]:
    print(f"\n=== anell {r0}–{r1} R☉ ===")
    res = {k: bandes(v, rr, r0, r1) for k, v in pols.items()}
    print(f"{'banda m':>12} {'amplada':>13} " + " ".join(f"{k:>12}" for k in capes)
          + "   " + " ".join(f"{k[:8]+' ×':>11}" for k in list(capes)[1:]))
    for lo,hi in BANDES:
        v = " ".join(f"{res[k][(lo,hi)]:12.5f}" for k in capes)
        g = " ".join(f"{res[k][(lo,hi)]/max(res['LINEAL'][(lo,hi)],1e-12):10.1f}×"
                     for k in list(capes)[1:])
        print(f"{lo:5d}–{hi:5d} {360/hi:5.2f}°–{360/lo:5.2f}° {v}   {g}")
    for k in list(capes)[1:]:
        j = res[k][(5,20)]/max(res[k][(900,2000)],1e-12)
        print(f"  jerarquia gran:fina de {k} = {j:.0f} : 1")
    print(f"  jerarquia gran:fina LINEAL = "
          f"{res['LINEAL'][(5,20)]/max(res['LINEAL'][(900,2000)],1e-12):.0f} : 1")
