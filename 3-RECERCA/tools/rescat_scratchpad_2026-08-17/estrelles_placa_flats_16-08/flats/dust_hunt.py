#!/usr/bin/env python3
"""Cerca de taques de pols sobre el fons de cel de les exposicions llargues.

Amb el Sol a 9 graus i massa d'aire 6,4 el cel de dins la totalitat es prou
brillant per fer de "flat de cel" a tot el quadre. Dividint el fotograma per
una versio molt suavitzada de si mateix, tot el que quedi es pols, PRNU o
soroll. Nomes lectura.
"""
import os, sys, glob
import numpy as np
import rawpy
from scipy import ndimage

OUTDIR = os.path.dirname(os.path.abspath(__file__))


def plane(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
    return v[0::2, 1::2] - ped


def analyse(path, ped, label, moon_r_raw, sigma_raw=260.0):
    a = plane(path, ped)
    H, W = a.shape
    sg = sigma_raw / 2.0        # el pla G1 va a mitja resolucio
    # localitza la corona per excloure-la
    sm = ndimage.uniform_filter(a, 31)
    k = np.unravel_index(np.argmax(sm), sm.shape)
    yy, xx = np.mgrid[:H, :W]
    rr = np.hypot(yy - k[0], xx - k[1])
    corona = rr < (3.2 * moon_r_raw / 2)
    print(f"\n--- {label}: {os.path.basename(path)} ---")
    print(f"  nivell del cel (mediana fora de la corona): {np.median(a[~corona]):.1f} ADU")
    print(f"  saturats (>=16000): {(a>=16000).sum()}")
    # substitueix la corona per la mediana del cel abans de suavitzar
    b = a.copy()
    b[corona] = np.median(a[~corona])
    base = ndimage.gaussian_filter(b, sg)
    ratio = a / np.maximum(base, 1e-6)
    m = (~corona) & (base > 20)
    # marge del sensor fora
    edge = np.zeros_like(m); edge[60:-60, 60:-60] = True
    m &= edge
    if m.sum() < 100000:
        print("  poc cel util"); return None
    r = ratio.copy(); r[~m] = np.nan
    # suavitza a l'escala de la taca de pols per treure soroll de fotons
    rs = ndimage.gaussian_filter(np.nan_to_num(r, nan=1.0), 12)
    rs[~m] = np.nan
    vals = rs[m]
    p = np.nanpercentile(vals, [0.1, 1, 50, 99, 99.9])
    print(f"  quocient imatge/suavitzat  P0,1={p[0]:.4f} P1={p[1]:.4f} "
          f"med={p[2]:.4f} P99={p[3]:.4f} P99,9={p[4]:.4f}")
    print(f"  sigma del quocient (suavitzat a ~24 px raw): {np.nanstd(vals)*100:.3f} %")
    print(f"  DEFICIT maxim local (taca mes fosca): {(1-np.nanmin(vals))*100:.2f} %")
    # troba minims locals prou marcats
    lo = np.nan_to_num(rs, nan=1.0)
    mn = ndimage.minimum_filter(lo, 60)
    cand = (lo == mn) & (lo < 1 - 0.004) & m
    ys, xs = np.nonzero(cand)
    order = np.argsort(lo[ys, xs])
    print(f"  candidats a taca (deficit > 0,4 %): {len(ys)}")
    for i in order[:8]:
        print(f"    x={xs[i]*2:5d} y={ys[i]*2:5d} raw   deficit={(1-lo[ys[i],xs[i]])*100:.2f} %")
    # soroll pixel a pixel (PRNU + fotons) en una finestra de cel net
    return dict(sigma=float(np.nanstd(vals)), worst=float(1 - np.nanmin(vals)),
                sky=float(np.median(a[~corona])), ratio=rs, mask=m, raw=a)


if __name__ == "__main__":
    S = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
    V = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered"
    print("=== A7RIIIA (f/2,8) : exposicions llargues de dins la totalitat ===")
    for n in ["DSC06987", "DSC06993", "DSC06984", "DSC06996"]:
        analyse(f"{S}/{n}.ARW", 512.0, "Sony", 587.0)
    print("\n=== R6 III (f/5,5) : exposicions llargues de dins la totalitat ===")
    import subprocess
    fs = sorted(glob.glob(f"{V}/*.CR3"))
    out = subprocess.run(["exiftool", "-T", "-FileName", "-ExposureTime", *fs],
                         capture_output=True, text=True)
    longs = [l.split("\t")[0] for l in out.stdout.strip().splitlines()
             if l.split("\t")[1] in ("10.3", "10", "2", "1")]
    for n in longs[:6]:
        analyse(f"{V}/{n}", 511.5, "R6", 883.0)
