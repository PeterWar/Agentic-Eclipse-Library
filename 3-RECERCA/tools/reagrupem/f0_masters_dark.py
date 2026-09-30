#!/usr/bin/env python3
"""FASE 0 · pas 2 — màsters de dark propis, un per exposició (Canon R6 III).

Es fabriquen des dels CR3 crus. ⛔ No es fa servir cap màster d'AstroPixel-
Processor ni de cap altra eina: un màster forà ja porta a dins el nivell de
negre que aquella eina va decidir, i a la R6 III la metadada és falsa.

Decisions, totes al rebut:

- **mediana** per píxel (robusta a raigs còsmics i a píxels calents aïllats);
- **fotograma sencer amb marges** (7144x4760). No es retalla res;
- **el pedestal NO es resta aquí**: el màster el porta a dins i s'endú tot
  junt quan es resta al fotograma. El 512,00 mesurat és l'àncora que serveix
  per comprovar que el màster és bo, no un número que s'apliqui a part;
- **sostre de fotogrames per màster** (`--sostre`): amb una mediana el guany
  va com sqrt(n) i el cas de 494 fotogrames és justament el menys informatiu.
  ⚠️ El que es deixa fora es DIU al rebut, mai en silenci.

Ús:
    python3 f0_masters_dark.py [--sostre 128] [--nomes 10.0]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

BANDA = 512  # files per banda en calcular la mediana


def per_exposicio(carpeta: str) -> dict[float, list[str]]:
    out = subprocess.run(
        ["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime", carpeta],
        capture_output=True, text=True, timeout=900, check=False,
    ).stdout
    d: dict[float, list[str]] = {}
    for lin in out.splitlines():
        p = lin.split("\t")
        if len(p) >= 2:
            try:
                d.setdefault(float(p[1]), []).append(os.path.join(carpeta, p[0]))
            except ValueError:
                pass
    for k in d:
        d[k].sort()
    return d


def tria(rutes: list[str], sostre: int) -> tuple[list[str], int]:
    """Subconjunt repartit uniformement; retorna també quants es deixen fora."""
    if len(rutes) <= sostre:
        return rutes, 0
    idx = np.linspace(0, len(rutes) - 1, sostre).round().astype(int)
    return [rutes[i] for i in sorted(set(idx.tolist()))], len(rutes) - sostre


def master(rutes: list[str]) -> tuple[np.ndarray, dict]:
    n = len(rutes)
    with rawpy.imread(rutes[0]) as r:
        g = comu.geometria(r)
        mc = comu.mapa_colors(r)
    pila = np.empty((n, g.alt, g.ample), dtype=np.uint16)
    for i, p in enumerate(rutes):
        with rawpy.imread(p) as r:
            pila[i] = r.raw_image
    med = np.empty((g.alt, g.ample), dtype=np.float32)
    for y0 in range(0, g.alt, BANDA):
        y1 = min(y0 + BANDA, g.alt)
        med[y0:y1] = np.median(pila[:, y0:y1].astype(np.float32), axis=0)
    del pila

    fosc, desc = comu.zona_fosca(g)
    info = {
        "n": n,
        "zona_fosca": desc,
        "forma": [int(g.alt), int(g.ample)],
        "pedestal_master": {},
        "senyal_visible": {},
    }
    for i in range(4):
        nom = comu.nom_canal(i, g.desc)
        d = med[fosc & (mc == i)]
        v = med[g.visible][mc[g.visible] == i]
        info["pedestal_master"][nom] = {
            "mediana": float(np.median(d)), "sigma": float(d.std()),
        }
        info["senyal_visible"][nom] = {
            "mediana": float(np.median(v)),
            "p99_9": float(np.percentile(v, 99.9)),
            "max": float(v.max()),
        }
    return med, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sostre", type=int, default=128)
    ap.add_argument("--nomes", type=float, default=None)
    args = ap.parse_args()

    sortida = os.path.join(comu.F0, "masters_dark")
    os.makedirs(sortida, exist_ok=True)
    os.makedirs(comu.REBUTS, exist_ok=True)
    t0 = time.time()

    grups = per_exposicio(comu.VIXEN_DARKS)
    exps = sorted(grups) if args.nomes is None else [args.nomes]
    rebut: dict = {
        "generat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cos": "Canon EOS R6 Mark III",
        "origen": comu.VIXEN_DARKS,
        "sostre_per_master": args.sostre,
        "metode": "mediana per pixel, fotograma sencer amb marges",
        "masters": {},
    }
    for e in exps:
        rutes, fora = tria(grups[e], args.sostre)
        print(f"[{time.time()-t0:6.0f}s] exp {e:<14} n={len(rutes):3d}"
              + (f"  (deixats fora {fora} de {len(grups[e])})" if fora else ""), flush=True)
        med, info = master(rutes)
        info["exposicio_exif"] = e
        info["deixats_fora"] = fora
        info["disponibles"] = len(grups[e])
        info["fitxers"] = [os.path.basename(p) for p in rutes]
        nom = f"MD_R6III_E{e:.6g}s.fits".replace("+", "")
        hdu = fits.PrimaryHDU(med)
        hdu.header["EXPTIME"] = (e, "s, NOMINAL de l EXIF (no mesurat)")
        hdu.header["NFRAMES"] = (len(rutes), "fotogrames a la mediana")
        hdu.header["NDISPON"] = (len(grups[e]), "fotogrames disponibles")
        hdu.header["METODE"] = "mediana"
        hdu.header["PEDESTAL"] = (float(info["pedestal_master"]["G1"]["mediana"]),
                                  "DN mesurat a la zona emmascarada")
        hdu.header["COMMENT"] = "Fotograma SENCER amb marges. Pedestal NO restat."
        hdu.writeto(os.path.join(sortida, nom), overwrite=True)
        info["fitxer"] = nom
        rebut["masters"][f"{e:.6g}"] = info
        p = info["pedestal_master"]
        print(f"          pedestal R/G1/B/G2 = "
              + " / ".join(f"{p[c]['mediana']:.2f}" for c in ("R", "G1", "B", "G2"))
              + f"   visible G1 mediana={info['senyal_visible']['G1']['mediana']:.2f}"
              + f"  p99,9={info['senyal_visible']['G1']['p99_9']:.1f}", flush=True)

    with open(os.path.join(comu.REBUTS, "F0_masters_dark.json"), "w") as fh:
        json.dump(rebut, fh, indent=1)
    print(f"\nfet en {time.time()-t0:.0f} s -> {sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
