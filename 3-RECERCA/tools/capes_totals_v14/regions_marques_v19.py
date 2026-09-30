"""Classifica els traços per DIRECCIÓ del canvi i extreu regions (r, az).

Verd (lluminància): ΔG domina i ΔR≈ΔB moderats — tint verd.
Taronja (to): ΔR > 0 > ΔB o ΔR >> ΔB — tint taronja.
Centre del Sol al llenç V16/V18: mesurat al cau_v17 (sol_v16).
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2
from psd_tools import PSDImage
from psd_tools.compression import decompress

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19")
CAU17 = os.path.join(AQUI, "cau_v17")
B = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
     "1-Unint Capes/Capes Totals/")
PSB = B + "CapesTotalsV18.psb"

# escala del llenç V16/V18: R☉ en px (del rebut de la V17)
REB = json.load(open(os.path.join(CAU17, "rebut_v17.json")))
SOL = REB["sol_v16"]          # (x, y)
RSOL = 455.5                  # px per R☉ (la mateixa RS que fes_v18.py)


def canal(layer, cid, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w = rec.right - rec.left
            h = rec.bottom - rec.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            return np.frombuffer(arr, ">u2" if depth == 16 else "u1").reshape(h, w)
    return None


def main():
    print("claus del rebut v17:", sorted(REB.keys()))
    print(f"sol_v16 = {SOL} · R☉ = {RSOL} px")
    psd = PSDImage.open(PSB)
    depth, version = psd.depth, psd.version
    capes = list(psd)
    base, marc = capes[12], capes[13]
    d = []
    for cid in (0, 1, 2):
        a = canal(base, cid, depth, version).astype(np.int32)
        b = canal(marc, cid, depth, version).astype(np.int32)
        d.append(b - a)
    dR, dG, dB = d
    tra = (np.abs(dR) > 655) | (np.abs(dG) > 655) | (np.abs(dB) > 655)
    # direcció del tint
    verd = tra & (dG > dR + 327) & (dG > dB + 327)
    taronja = tra & (dR > dG + 327) & (dG > dB - 327)
    resta = tra & ~verd & ~taronja
    print(f"verd {verd.sum()} · taronja {taronja.sum()} · resta {resta.sum()}")
    if resta.sum():
        i = np.argwhere(resta)[::max(1, resta.sum() // 5)]
        for y, x in i[:5]:
            print(f"  resta ({y},{x}): ΔR {dR[y, x]/655.35:+.1f}% "
                  f"ΔG {dG[y, x]/655.35:+.1f}% ΔB {dB[y, x]/655.35:+.1f}%")

    H, W = tra.shape
    yy, xx = np.mgrid[0:H:4, 0:W:4]
    rad = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL
    az = np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0]))

    resum = {}
    for nom, m in (("verd", verd), ("taronja", taronja)):
        m4 = m[::4, ::4].astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m4, 8)
        regs = []
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] < 200:   # px a 1/4 = 3200 px reals
                continue
            mk = lab == k
            regs.append({
                "area_px": int(st[k, cv2.CC_STAT_AREA] * 16),
                "r_med": round(float(np.median(rad[mk])), 2),
                "r_min": round(float(rad[mk].min()), 2),
                "r_max": round(float(rad[mk].max()), 2),
                "az_med": round(float(np.median(az[mk])), 1),
                "cx": int(cen[k][0] * 4), "cy": int(cen[k][1] * 4),
            })
        regs.sort(key=lambda z: -z["area_px"])
        resum[nom] = regs
        print(f"\n{nom.upper()}: {len(regs)} regions")
        for z in regs:
            print(f"  r {z['r_min']:.2f}-{z['r_max']:.2f} (med {z['r_med']:.2f}) "
                  f"az {z['az_med']:+.1f}° · {z['area_px']} px · "
                  f"centre ({z['cx']},{z['cy']})")

    np.save(os.path.join(CAU, "marques_verd.npy"), verd)
    np.save(os.path.join(CAU, "marques_taronja.npy"), taronja)
    json.dump(resum, open(os.path.join(CAU, "regions_v19.json"), "w"), indent=1)
    print(f"\ndesat a {CAU}")


if __name__ == "__main__":
    main()
