#!/usr/bin/env python3
"""FASE 0 · pas 1 — mesura del PEDESTAL i del NIVELL DE BLANC de la R6 III.

Mesura, no llegeix. Els dos números surten dels píxels:

- **pedestal**: mediana per canal CFA a la zona EMMASCARADA de cada fotograma
  (marge esquerre i superior de `raw_image`), que no rep llum mai.
  ⛔ Mai `black_level_per_channel` de libraw, que a aquest cos és fals.
- **nivell de blanc efectiu**: on s'amunteguen els píxels a dalt de tot de
  l'histograma de la zona visible, per canal. ⛔ Mai `white_level`.

Escriu un rebut JSON + text a `4-REBUTS/`. No modifica cap RAW.

Ús:
    python3 f0_pedestal_blanc.py [--max-darks N] [--nomes-llums]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict

import numpy as np
import rawpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

LLINDAR_ALT = 12000  # per sota d'això no busquem saturació


def exposicions(carpeta: str) -> dict[str, float]:
    """Temps NOMINALS de l'EXIF (menú). No són els reals: es mesuren després."""
    try:
        out = subprocess.run(
            ["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime",
             "-ISO", "-CameraTemperature", carpeta],
            capture_output=True, text=True, timeout=600, check=False,
        ).stdout
    except FileNotFoundError:
        return {}
    d: dict[str, float] = {}
    for lin in out.splitlines():
        parts = lin.split("\t")
        if len(parts) >= 2:
            try:
                d[parts[0]] = float(parts[1])
            except ValueError:
                pass
    return d


def mesura(ruta: str) -> dict:
    with rawpy.imread(ruta) as r:
        g = comu.geometria(r)
        mc = comu.mapa_colors(r)
        ri = r.raw_image
        negre_libraw = list(r.black_level_per_channel)
        blanc_libraw = int(r.white_level)
        fosc, _ = comu.zona_fosca(g)
        vis = np.zeros_like(fosc)
        vis[g.visible] = True

        fila: dict = {
            "fitxer": os.path.basename(ruta),
            "negre_libraw": negre_libraw,
            "blanc_libraw": blanc_libraw,
            "canals": {},
        }
        for i in range(4):
            nom = comu.nom_canal(i, g.desc)
            d = ri[fosc & (mc == i)].astype(np.float64)
            v = ri[vis & (mc == i)]
            alts = v[v >= LLINDAR_ALT]
            pic = None
            if alts.size:
                c = Counter(alts.tolist())
                pic = max(c.items(), key=lambda kv: kv[1])
            fila["canals"][nom] = {
                "pedestal_mediana": float(np.median(d)),
                "pedestal_mitjana": float(d.mean()),
                "pedestal_sigma": float(d.std()),
                "n_fosc": int(d.size),
                "max_visible": int(v.max()),
                "pic_alt_valor": None if pic is None else int(pic[0]),
                "pic_alt_compte": 0 if pic is None else int(pic[1]),
                "n_alts": int(alts.size),
            }
        return fila


def resum(files: list[dict], titol: str) -> list[str]:
    if not files:
        return [f"{titol}: cap fitxer"]
    ln = [f"### {titol}  ({len(files)} fotogrames)", ""]
    ln.append("| canal | pedestal mediana | mín–màx | mitjana de mitjanes | sigma llegida |")
    ln.append("|---|---:|---:|---:|---:|")
    for nom in ("R", "G1", "B", "G2"):
        med = np.array([f["canals"][nom]["pedestal_mediana"] for f in files])
        mit = np.array([f["canals"][nom]["pedestal_mitjana"] for f in files])
        sig = np.array([f["canals"][nom]["pedestal_sigma"] for f in files])
        ln.append(
            f"| {nom} | {np.median(med):.2f} | {med.min():.1f} – {med.max():.1f} "
            f"| {mit.mean():.3f} | {sig.mean():.3f} |"
        )
    return ln + [""]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-darks", type=int, default=6, help="darks per exposició")
    ap.add_argument("--nomes-llums", action="store_true")
    args = ap.parse_args()

    os.makedirs(comu.REBUTS, exist_ok=True)
    t0 = time.time()

    llums = comu.llista(comu.VIXEN, ".CR3")
    exp_llums = exposicions(comu.VIXEN)
    print(f"llums: {len(llums)} fotogrames", flush=True)
    files_llum = []
    for i, p in enumerate(llums, 1):
        f = mesura(p)
        f["exposicio_exif"] = exp_llums.get(f["fitxer"])
        files_llum.append(f)
        if i % 20 == 0 or i == len(llums):
            print(f"  {i}/{len(llums)}  ({time.time()-t0:.0f} s)", flush=True)

    files_dark: list[dict] = []
    if not args.nomes_llums:
        darks = comu.llista(comu.VIXEN_DARKS, ".CR3")
        exp_darks = exposicions(comu.VIXEN_DARKS)
        per_exp: dict[float, list[str]] = defaultdict(list)
        for p in darks:
            per_exp[exp_darks.get(os.path.basename(p), -1.0)].append(p)
        tria = [p for e in sorted(per_exp) for p in per_exp[e][: args.max_darks]]
        print(f"darks: {len(darks)} en total, {len(per_exp)} exposicions, "
              f"en mesuro {len(tria)}", flush=True)
        for i, p in enumerate(tria, 1):
            f = mesura(p)
            f["exposicio_exif"] = exp_darks.get(f["fitxer"])
            files_dark.append(f)
            if i % 20 == 0 or i == len(tria):
                print(f"  {i}/{len(tria)}  ({time.time()-t0:.0f} s)", flush=True)

    dades = {
        "generat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cos": "Canon EOS R6 Mark III",
        "llums": files_llum,
        "darks": files_dark,
        "llindar_alt": LLINDAR_ALT,
    }
    rj = os.path.join(comu.REBUTS, "F0_pedestal_blanc.json")
    with open(rj, "w") as fh:
        json.dump(dades, fh, indent=1)

    ln = [
        "# FASE 0 · pas 1 — pedestal i nivell de blanc (Canon R6 Mark III)",
        "",
        f"Generat {dades['generat_utc']} · {len(files_llum)} llums, "
        f"{len(files_dark)} darks mesurats.",
        "",
        "Mesurat a la zona EMMASCARADA de `raw_image` (marge esquerre i "
        "superior), que no rep llum mai. Cap número surt de la metadada.",
        "",
    ]
    ln += resum(files_llum, "Llums de totalitat")
    ln += resum(files_dark, "Darks")

    lib = files_llum[0]["negre_libraw"]
    ln += [
        "### El que en diu libraw, i per què no es fa servir",
        "",
        f"`black_level_per_channel` = `{lib}` · `white_level` = "
        f"`{files_llum[0]['blanc_libraw']}`",
        "",
    ]

    # nivell de blanc: pic superior agregat
    ln += ["### Nivell de blanc efectiu", "",
           "| canal | pic dominant | fotogrames amb pic | màxim vist |",
           "|---|---:|---:|---:|"]
    for nom in ("R", "G1", "B", "G2"):
        pics = Counter(
            f["canals"][nom]["pic_alt_valor"] for f in files_llum
            if f["canals"][nom]["pic_alt_valor"] is not None
            and f["canals"][nom]["n_alts"] > 1000
        )
        mx = max(f["canals"][nom]["max_visible"] for f in files_llum)
        if pics:
            v, n = pics.most_common(1)[0]
            ln.append(f"| {nom} | {v} | {n} | {mx} |")
        else:
            ln.append(f"| {nom} | — | 0 | {mx} |")
    ln.append("")

    rt = os.path.join(comu.REBUTS, "F0_pedestal_blanc.md")
    with open(rt, "w") as fh:
        fh.write("\n".join(ln) + "\n")
    print(f"\nrebut: {rt}\n       {rj}\n({time.time()-t0:.0f} s)")
    print("\n".join(ln))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
