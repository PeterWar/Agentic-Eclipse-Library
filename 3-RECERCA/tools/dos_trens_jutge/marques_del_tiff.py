#!/usr/bin/env python3
"""On són les marques que Pere ha pintat al TIFF, i què hi ha a sota.

Es detecten pel color: **magenta és el verd com a mínim clar**, que ni la
corona (taronja) ni el cel (blau fluix) fan mai. Després es dibuixen sobre el
lliurament, al LLENÇ SENCER.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import cv2
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
SORTIDA = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/DOS_TRENS")
TIFF = os.path.expanduser("~/Downloads/Eclipsi_2026_SONYTOT_CIENCIA_capes_LDIC.tif")
BASE = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/"
                          "016_SONYTOT_CIENCIA/vistes/LLIURAMENT_x8.png")
K = 8
RS = 440.60304883027544


def marques(p):
    a = np.asarray(Image.open(p)).astype(np.int16)
    mag = (a[..., 0] - a[..., 1] > 40) & (a[..., 2] - a[..., 1] > 40)
    n, lab, st, ce = cv2.connectedComponentsWithStats(mag.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 500:
            continue
        out.append((st[i, cv2.CC_STAT_AREA], ce[i][1], ce[i][0],
                    st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]))
    return sorted(out, reverse=True), a.shape[:2]


if __name__ == "__main__":
    ms, (H, W) = marques(TIFF)
    im = Image.open(BASE).convert("RGB")
    dr = ImageDraw.Draw(im)
    print(f"{len(ms)} marques\n")
    for ar, y, x, w, h in ms:
        r = math.hypot(y - H / 2, x - W / 2) / RS
        th = math.degrees(math.atan2(x - W / 2, H / 2 - y)) % 360
        vertical = h > 4 * w
        if vertical:
            dr.line([(x / K, 0), (x / K, im.height)], fill=(255, 60, 255), width=2)
            et = f"línia vertical a {(x - W/2)/RS:+.2f} R☉"
        else:
            R = max(w, h) / K * 1.8
            dr.ellipse([x / K - R, y / K - R, x / K + R, y / K + R],
                       outline=(255, 60, 255), width=3)
            et = f"taca de {w}×{h} px a r={r:.2f} R☉ θ={th:.0f}°"
        dr.text((x / K + 8, y / K - 14), et, fill=(255, 160, 255))
        print(f"  {et}   ({ar:,} px pintats)")
    os.makedirs(SORTIDA, exist_ok=True)
    p = os.path.join(SORTIDA, "MARQUES_PERE_SONYTOT_localitzades.png")
    im.save(p)
    print(f"\ndesat a {p}\n  llenç sencer ×{K}, sobre el lliurament del run 016")
