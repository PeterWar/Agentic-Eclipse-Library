"""Els cinc fotogrames exclosos de la Sony, per mirar-los.

Cada un al costat d'un fotograma BO de la MATEIXA exposicio, tots dos amb el
MATEIX calibratge i la MATEIXA escala de to, i **el fotograma sencer**: cap
retall, que es on viuen les coses que no s'esperen.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import cv2
import rawpy
from PIL import Image, ImageDraw

ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")
ENT = os.path.join(ARREL, "0-ENTRADES", "SONY-A7RIIIA")
RUNS = os.path.join(ARREL, "1-RUNS")
SORTIDA = os.path.join(ARREL, "2-OUTPUT", "DOS_TRENS")
K = 6

EXP = {"DSC06985.ARW": (1.0, "1 s"), "DSC06986.ARW": (0.125, "1/8 s"),
       "DSC06987.ARW": (8.0, "8 s"), "DSC06988.ARW": (1.0, "1 s"),
       "DSC06989.ARW": (0.125, "1/8 s"), "DSC06990.ARW": (8.0, "8 s"),
       "DSC06991.ARW": (1.0, "1 s"), "DSC06993.ARW": (8.0, "8 s")}
FILES = [("DSC06987.ARW", "DSC06990.ARW", "DSC06993.ARW"),
         ("DSC06985.ARW", "DSC06988.ARW", "DSC06991.ARW"),
         ("DSC06986.ARW", "DSC06989.ARW", None)]
ETIQ = {"DSC06985.ARW": "BO", "DSC06986.ARW": "BO", "DSC06987.ARW": "BO"}


def ruta(n):
    for c in ("quarantena", "totalitat"):
        p = os.path.join(ENT, c, n)
        if os.path.exists(p):
            return p, c
    raise SystemExit(n)


def pla(comu, f0, run, n, dk):
    p, _ = ruta(n)
    with rawpy.imread(p) as r:
        raw = r.raw_image.astype(np.float32)
        mc = comu.mapa_colors(r)
    e = EXP[n][0]
    if e not in dk:
        dk[e] = f0.dark_de(run, e)
    ys, xs = np.nonzero(mc == 1); oy, ox = int(ys.min()), int(xs.min())
    g = (raw[oy::2, ox::2] - dk[e][oy::2, ox::2]) / e
    h, w = g.shape
    return cv2.resize(g, (w // K * 2, h // K * 2), interpolation=cv2.INTER_AREA)


def to(a, lo, hi):
    v = np.clip((np.log10(np.maximum(a, lo)) - np.log10(lo))
                / (np.log10(hi) - np.log10(lo)), 0, 1)
    return (v * 255).astype(np.uint8)


if __name__ == "__main__":
    import re as _re
    _p = _re.compile(r"^(\d{3,})_")
    _c = [x for x in os.listdir(RUNS)
          if _p.sub("", x).startswith("SONYTOT_CIENCIA_")
          and not x.endswith(("_FALLIT", "_AVORTAT"))]
    d = sorted(_c, key=lambda x: (int(_p.match(x).group(1)) if _p.match(x) else -1, x))[-1]
    sys.path.insert(0, os.path.join(RUNS, d, "codi"))
    import comu, f0
    run = comu.Run.obre(os.path.join(RUNS, d))
    dk = {}
    IM = {}
    for fila in FILES:
        for n in fila:
            if n:
                IM[n] = pla(comu, f0, run, n, dk)
                print(f"  {n} llegit", flush=True)
    h, w = next(iter(IM.values())).shape
    MG, TOP = 8, 34
    tela = np.full(((h + TOP + MG) * 3, (w + MG) * 3, 3), 18, np.uint8)
    im = Image.fromarray(tela); dr = ImageDraw.Draw(im)
    for i, fila in enumerate(FILES):
        ref = IM[fila[0]]
        lo = max(float(np.percentile(ref, 40)), 1.0)
        hi = float(np.percentile(ref, 99.9))
        for j, n in enumerate(fila):
            if not n:
                continue
            g = to(IM[n], lo, hi)
            y = i * (h + TOP + MG) + TOP; x = j * (w + MG)
            im.paste(Image.fromarray(np.dstack([g] * 3)), (x, y))
            _, carp = ruta(n)
            et = ETIQ.get(n, "EXCLÒS")
            dr.text((x + 4, y - 26), f"{n}  ·  {EXP[n][1]}  ·  {carp}  ·  {et}",
                    fill=(255, 220, 120) if et == "EXCLÒS" else (150, 255, 150))
    p = os.path.join(SORTIDA, "QUARANTENA_els_cinc_exclosos.png")
    os.makedirs(SORTIDA, exist_ok=True)
    im.save(p)
    print(f"\ndesat a {p}\n  fotograma SENCER, reduït ×{K//2}; cada fila amb la "
          f"mateixa escala de to que el seu BO")
