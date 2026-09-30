#!/usr/bin/env python3
"""FASE 0 · pas 4 — màster de FLAT radial i prova de LINEALITAT.

Els flats fan dues feines alhora perquè l'escena és uniforme:

1. **Linealitat**: els 125 flats són a quatre exposicions (1/320, 1/100, 1/40,
   1/25). El quocient entre dos màsters de flat ha de ser CONSTANT amb el
   nivell si la resposta és lineal. Aquí no hi ha estructura d'escena que
   confongui el resultat, que és el que va espatllar la prova sobre la corona.
2. **Flat**: només el component **RADIAL** (`research/100`). El 2D porta la
   pols —que s'ha pogut moure— i amaga un pla que falsificaria l'extincio.
   El centre del model radial s'AJUSTA, no se suposa al mig del sensor.

Validació: els **28 flats invertits** (cos girat 173,5°) donen un segon perfil
radial independent. Si el flat és del sensor i radial, els dos han de coincidir.

⛔ Tot per canal CFA.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

import numpy as np
import rawpy
from astropy.io import fits
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402


def exp_de(carpeta: str) -> dict[str, float]:
    out = subprocess.run(["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime", carpeta],
                         capture_output=True, text=True, timeout=900).stdout
    d = {}
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) >= 2:
            try: d[p[0]] = float(p[1])
            except ValueError: pass
    return d


def dark_mes_proper(e: float) -> str:
    fs = glob.glob(os.path.join(comu.F0, "masters_dark", "*.fits"))
    return min(fs, key=lambda p: abs(float(p.split("_E")[1].rstrip("s.fits")) - e))


def master_flat(rutes: list[str], e: float, sostre: int = 40) -> np.ndarray:
    if len(rutes) > sostre:
        idx = np.linspace(0, len(rutes) - 1, sostre).round().astype(int)
        rutes = [rutes[i] for i in sorted(set(idx.tolist()))]
    n = len(rutes)
    with rawpy.imread(rutes[0]) as r:
        h, w = r.raw_image.shape
    pila = np.empty((n, h, w), np.uint16)
    for i, p in enumerate(rutes):
        with rawpy.imread(p) as r:
            pila[i] = r.raw_image
    med = np.empty((h, w), np.float32)
    for y0 in range(0, h, 512):
        y1 = min(y0 + 512, h)
        med[y0:y1] = np.median(pila[:, y0:y1].astype(np.float32), axis=0)
    del pila
    med -= fits.getdata(dark_mes_proper(e)).astype(np.float32)
    return med


def perfil_radial(pla: np.ndarray, yy: np.ndarray, xx: np.ndarray,
                  cy: float, cx: float, nb: int = 220):
    r = np.hypot(yy - cy, xx - cx)
    rmax = r.max()
    idx = np.clip((r / rmax * nb).astype(np.int32), 0, nb - 1)
    s = np.bincount(idx, pla, nb); c = np.bincount(idx, None, nb)
    bo = c > 200
    return (np.arange(nb) + 0.5) / nb * rmax, np.where(bo, s / np.maximum(c, 1), np.nan), bo


def ajusta_centre(pla: np.ndarray, yy, xx):
    """Centre que fa el model radial més bo (residu mínim)."""
    def resid(p):
        cy, cx = p
        rr, prof, bo = perfil_radial(pla, yy, xx, cy, cx, 160)
        r = np.hypot(yy - cy, xx - cx)
        idx = np.clip((r / r.max() * 160).astype(np.int32), 0, 159)
        mod = np.where(bo[idx], prof[idx], np.nan)
        d = pla - mod
        return d[np.isfinite(d)][::37]
    h, w = pla.shape
    out = least_squares(resid, [h / 2, w / 2], diff_step=8.0, xtol=1e-3, max_nfev=40)
    return float(out.x[0]), float(out.x[1])


def main() -> int:
    t0 = time.time()
    os.makedirs(os.path.join(comu.F0, "flat"), exist_ok=True)
    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)

    grups: dict[float, list[str]] = {}
    for c in (comu.VIXEN_FLATS,):
        ex = exp_de(c)
        for n, e in ex.items():
            if n.upper().endswith(".CR3"):
                grups.setdefault(e, []).append(os.path.join(c, n))
    for k in grups: grups[k].sort()
    print("flats normals:", {f"{k:g}": len(v) for k, v in sorted(grups.items())}, flush=True)

    masters = {}
    for e in sorted(grups):
        if len(grups[e]) < 8:
            print(f"  {e:g}s: només {len(grups[e])}, el deixo fora"); continue
        masters[e] = master_flat(grups[e], e)
        print(f"  [{time.time()-t0:5.0f}s] màster flat {e:g}s  n={min(len(grups[e]),40)}", flush=True)

    # ---- LINEALITAT: quocient entre màsters contra el nivell
    print("\n=== LINEALITAT (quocient normalitzat contra el nivell del flat baix) ===")
    lin = {}
    es = sorted(masters)
    baix = es[0]
    for e in es[1:]:
        A = masters[baix]; B = masters[e]
        for i, cn in ((1, "G1"), (0, "R"), (2, "B")):
            sel = np.zeros((g.alt, g.ample), bool); sel[g.visible] = True
            sel &= (mc == i)
            a = A[sel]; b = B[sel]
            bo = (a > 60) & (b > 60) & (b < 15800)
            a, b = a[bo], b[bo]
            if a.size < 10000: continue
            q = b / a
            ref = np.median(q[(a > np.percentile(a, 20)) & (a < np.percentile(a, 40))])
            fila = []
            pcts = [10, 30, 50, 70, 85, 95, 99]
            for p_ in pcts:
                lo, hi = np.percentile(a, max(0, p_ - 4)), np.percentile(a, min(100, p_ + 4))
                m = (a >= lo) & (a <= hi)
                fila.append(float(np.median(q[m]) / ref) if m.sum() > 500 else np.nan)
            niv = [float(np.percentile(b, p_)) for p_ in pcts]
            lin[f"{baix:g}->{e:g}-{cn}"] = {"q": float(ref), "nivells_B": niv, "norm": fila}
            print(f"  {baix:g}->{e:g}s {cn:>2}  raó={ref:6.3f} | nivell B: "
                  + " ".join(f"{n:5.0f}" for n in niv))
            print(f"  {'':>14}          | norm.   : "
                  + " ".join(f"{x:5.3f}" for x in fila))

    # ---- FLAT RADIAL, per canal, centre ajustat
    print("\n=== FLAT RADIAL ===", flush=True)
    e_ref = max(masters, key=lambda k: len(grups[k]))
    M = masters[e_ref]
    yy, xx = np.mgrid[0:g.alt, 0:g.ample].astype(np.float32)
    flat = np.ones((g.alt, g.ample), np.float32)
    info = {"exposicio_referencia": e_ref, "canals": {}}
    for i in range(4):
        cn = comu.nom_canal(i, g.desc)
        sel = np.zeros((g.alt, g.ample), bool); sel[g.visible] = True
        sel &= (mc == i)
        ys, xs, vs = yy[sel], xx[sel], M[sel]
        cy, cx = ajusta_centre_ligero(vs, ys, xs, g)
        rr, prof, bo = perfil_radial(vs, ys, xs, cy, cx, 220)
        norm = np.nanmax(prof[np.isfinite(prof)])
        prof_n = prof / norm
        r_tot = np.hypot(yy - cy, xx - cx)
        idx = np.clip((r_tot / rr[-1] * 220).astype(np.int32), 0, 219)
        pr = np.where(np.isfinite(prof_n), prof_n, np.nanmedian(prof_n))
        flat[mc == i] = pr[idx][mc == i]
        info["canals"][cn] = {
            "centre_yx": [cy, cx], "vinyetatge_vora_pct": float(100 * (1 - np.nanmin(prof_n))),
            "perfil_r": rr.tolist(), "perfil": np.where(np.isfinite(prof_n), prof_n, -1).tolist(),
        }
        print(f"  {cn:>2}  centre=({cy:7.1f},{cx:7.1f})  "
              f"vinyetatge a la vora = {100*(1-np.nanmin(prof_n)):5.2f} %", flush=True)

    fits.PrimaryHDU(flat).writeto(os.path.join(comu.F0, "flat", "FLAT_RADIAL_R6III.fits"),
                                  overwrite=True)
    with open(os.path.join(comu.REBUTS, "F0_flat_linealitat.json"), "w") as fh:
        json.dump({"linealitat": lin, "flat": info}, fh, indent=1)
    print(f"\nfet en {time.time()-t0:.0f} s")
    return 0


def ajusta_centre_ligero(vs, ys, xs, g):
    """Centre per graella gruixuda + refinament: barat i prou precís."""
    def cost(cy, cx):
        r = np.hypot(ys - cy, xs - cx)
        idx = np.clip((r / r.max() * 120).astype(np.int32), 0, 119)
        s = np.bincount(idx, vs, 120); c = np.bincount(idx, None, 120)
        prof = s / np.maximum(c, 1)
        return float(np.nanstd(vs - prof[idx]))
    cy, cx = g.alt / 2, g.ample / 2
    pas = 256.0
    while pas >= 8.0:
        millor = (cost(cy, cx), cy, cx)
        for dy in (-pas, 0, pas):
            for dx in (-pas, 0, pas):
                c = cost(cy + dy, cx + dx)
                if c < millor[0]: millor = (c, cy + dy, cx + dx)
        _, cy, cx = millor
        pas /= 2
    return cy, cx


if __name__ == "__main__":
    raise SystemExit(main())
