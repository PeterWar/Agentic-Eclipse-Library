#!/usr/bin/env python3
"""⛔ HISTÒRIC des del 27-08-2026. Pere ha DEPRECAT el mode MEMORIA i el projecte
segueix amb CIENCIA. Aquest script és la **proveniència de la decisió**: el que
es va mirar per prendre-la. No es pot tornar a executar tal com és, perquè
`cadena.py` ja no arrenca cap run MEMORIA; funciona sobre els runs que ja hi ha.

Comparativa dels dos modes de color, contra el testimoni i contra Brno.

    python3 comparativa_modes.py

⛔ Norma del rectangle i norma dels retalls: els dos panells nostres son el
LLENC SENCER. Cap retall, ni de diagnostic.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu

BRNO = "/Users/USUARI/Desktop/Eclipse 2026/Drukmuller fotos finals/TSE_2026_400mm_DHS.png"
PERE = "/Users/USUARI/Downloads/GraduantColor.tif"
DEST = os.path.join(comu.OUTPUT, "COMPARATIVA_DELS_DOS_MODES.png")


def ultim(mode):
    ds = [d for d in sorted(os.listdir(comu.RUNS))
          if d.startswith(f"VIXEN_{mode}_") and not d.endswith(("_FALLIT", "_ASSAIG"))]
    if not ds:
        return None
    return os.path.join(comu.RUNS, ds[-1])


def ov(a, b):
    return np.where(a < 0.5, 2 * a * b, 1.0 - 2.0 * (1.0 - a) * (1.0 - b))


def panell(run_dir):
    base = np.load(os.path.join(run_dir, "3-filtres", "BASE_rgb.npy")).astype(np.float32)
    det = np.load(os.path.join(run_dir, "3-filtres", "DETALL_PASSA_ALT.npy")).astype(np.float32)
    if det.ndim == 3:
        det = det.mean(axis=2)
    im = np.clip(ov(base, det[:, :, None]), 0, 1)
    H, W = im.shape[:2]
    return np.asarray(Image.fromarray((im * 255 + 0.5).astype(np.uint8))
                      .resize((W // 8, H // 8), Image.LANCZOS))


def carrega_pere():
    import tifffile
    P3 = np.array([[0.48657095, 0.26566769, 0.19821728],
                   [0.22897456, 0.69173852, 0.07928691],
                   [0.0, 0.04511338, 1.04394437]])
    M = (comu.XYZ_SRGB @ P3).astype(np.float32)
    a = tifffile.imread(PERE)[:, :, :3][::6, ::6].astype(np.float32) / 65535.0
    return (comu.a_srgb(np.einsum("ij,hwj->hwi", M, comu.a_lineal(a))) * 255 + 0.5).astype(np.uint8)


def main():
    pans = []
    if os.path.exists(PERE):
        pans.append((carrega_pere(), "0. EL TEU TESTIMONI · GraduantColor.tif  (centre cremat)"))
    for mode, tit in (("MEMORIA", "1. MODE MEMORIA · el color del DSC06991"),
                      ("CIENCIA", "2. MODE CIENCIA · blanc sobre el Sol (AM0)")):
        d = ultim(mode)
        if d:
            f3 = json.load(open(os.path.join(d, "4-rebuts", "F3_filtres.json")))
            c = f3.get("color_renderitzat_sRGB_lineal", {}).get("2Rsol", {})
            extra = f"  ·  a 2 R☉: R/G {c.get('R/G', float('nan')):.2f} B/G {c.get('B/G', float('nan')):.2f}" if c else ""
            pans.append((panell(d), tit + "  ·  LLENC SENCER" + extra))
    if os.path.exists(BRNO):
        b = np.asarray(Image.open(BRNO).convert("RGB"))
        pans.append((b, "3. DRUCKMULLER 400 mm  (blanc sobre la corona)"))
    if not pans:
        raise SystemExit("no hi ha res per comparar")
    alt = max(p.shape[0] for p, _ in pans)
    ims = []
    for p, t in pans:
        im = Image.fromarray(p)
        ims.append((im.resize((int(im.width * alt / im.height), alt), Image.LANCZOS), t))
    mg, cap = 24, 46
    li = Image.new("RGB", (sum(i.width for i, _ in ims) + mg * (len(ims) + 1),
                           alt + cap + mg * 2), (12, 12, 14))
    d = ImageDraw.Draw(li)
    try:
        fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 19)
    except Exception:
        fo = ImageFont.load_default()
    x = mg
    for im, t in ims:
        li.paste(im, (x, cap)); d.text((x, cap - 28), t, fill=(232, 232, 236), font=fo)
        x += im.width + mg
    d.text((mg, alt + cap + 8),
           "1 i 2 son la MATEIXA dada, la mateixa geometria i la MATEIXA corba de to. "
           "L'unica diferencia es el blanc adoptat.", fill=(150, 150, 158), font=fo)
    li.save(DEST)
    print("desat", DEST, li.size)


if __name__ == "__main__":
    main()
