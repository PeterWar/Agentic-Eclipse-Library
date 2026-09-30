#!/usr/bin/env python3
"""Flat sintetic de cel: apila el quocient imatge/suavitzat de diversos
fotogrames llargs de dins la totalitat. El que es fix al SENSOR (pols, PRNU)
s'hi suma; el que segueix el cel (corona, estructura del cel) es dilueix.

Nomes lectura sobre els originals.
"""
import os, sys, glob, subprocess
import numpy as np
import rawpy
from scipy import ndimage

MARGIN = 190          # px del pla G1 que es descarten a cada vora


def plane(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
    return v[0::2, 1::2] - ped


def ratio_map(a, moon_r_g, sg):
    H, W = a.shape
    sm = ndimage.uniform_filter(a, 31)
    k = np.unravel_index(np.argmax(sm), sm.shape)
    yy, xx = np.mgrid[:H, :W]
    rr = np.hypot(yy - k[0], xx - k[1])
    corona = rr < 3.2 * moon_r_g
    b = a.copy()
    sky = np.median(a[~corona])
    b[corona] = sky
    base = ndimage.gaussian_filter(b, sg)
    r = a / np.maximum(base, 1e-6)
    m = (~corona) & (base > 20)
    m[:MARGIN] = m[-MARGIN:] = False
    m[:, :MARGIN] = m[:, -MARGIN:] = False
    return r, m, sky, (k[1], k[0])


def run(label, files, ped, moon_r_g, sigma_g=130.0):
    acc = None; cnt = None; skies = []
    for f in files:
        a = plane(f, ped)
        r, m, sky, cen = ratio_map(a, moon_r_g, sigma_g)
        skies.append(sky)
        if acc is None:
            acc = np.zeros_like(a); cnt = np.zeros_like(a)
        acc[m] += r[m]; cnt[m] += 1
        print(f"   {os.path.basename(f):<16} cel={sky:8.1f} ADU  centre corona "
              f"(raw) = ({cen[0]*2}, {cen[1]*2})", flush=True)
    good = cnt >= max(2, len(files) - 1)
    stack = np.where(good, acc / np.maximum(cnt, 1), np.nan)
    print(f"\n  {label}: {len(files)} fotogrames, {good.sum()} px del pla G1 util")
    # 1) estructura a l'escala d'una taca de pols (desenfocada)
    for scale_raw, name in [(50, "50 px raw"), (120, "120 px raw"), (300, "300 px raw")]:
        s = ndimage.gaussian_filter(np.nan_to_num(stack, nan=1.0), scale_raw / 2 / 2.355)
        v = s[good]
        print(f"    escala {name:>10}: sigma={np.std(v)*100:.3f} %   "
              f"min={np.min(v):.4f}  max={np.max(v):.4f}   "
              f"(deficit maxim {(1-np.min(v))*100:.2f} %)")
    # 2) soroll pixel a pixel = PRNU + fotons
    hp = np.nan_to_num(stack, nan=1.0) - ndimage.uniform_filter(np.nan_to_num(stack, nan=1.0), 9)
    print(f"    dispersio pixel a pixel (alta frequencia): {np.std(hp[good])*100:.3f} %")
    return stack, good


if __name__ == "__main__":
    S = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
    V = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered"
    print("=== A7RIIIA + 300 GM a f/2,8 : 8 s i 2 s de dins la totalitat ===")
    sony = [f"{S}/DSC0698{n}.ARW" for n in (4, 7)] + [f"{S}/DSC0699{n}.ARW" for n in (3, 6, 9)]
    st_s, gd_s = run("Sony", sony, 512.0, 587 / 2 / 2)
    np.save("dust_sony.npy", st_s)

    print("\n=== R6 III + VSD90SS a f/5,5 : 10,3 s, 2 s i 1 s de dins la totalitat ===")
    fs = sorted(glob.glob(f"{V}/*.CR3"))
    o = subprocess.run(["exiftool", "-T", "-FileName", "-ExposureTime", *fs],
                       capture_output=True, text=True)
    longs = [f"{V}/" + l.split("\t")[0] for l in o.stdout.strip().splitlines()
             if l.split("\t")[1] in ("10.3", "10", "2")]
    st_r, gd_r = run("R6", longs, 511.5, 883 / 2 / 2)
    np.save("dust_r6.npy", st_r)
