#!/usr/bin/env python3
"""Caça d'anells: quina part de cada filtre es pot explicar amb NOMES el radi.

Un anell es una excursio de la MEDIANA AZIMUTAL a un radi concret. La corona no
te cap radi preferit, o sigui que tot el que la mediana azimutal ensenya per
damunt del soroll es artefacte.

⛔ Es declara la COBERTURA de cada anell. Per damunt del radi on l'anell deixa
de caure sencer dins del rectangle, l'estadistica azimutal es de CANTONS i no
val (es la trampa del research/100 §E i de l'NRGF).
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu


def perfil(v, rad_rs, m, nb=420, rmin=1.02, rmax=None):
    rmax = rmax or float(rad_rs[m].max())
    lo, hi = np.log10(rmin), np.log10(rmax)
    idx = np.clip(((np.log10(np.maximum(rad_rs, 1e-3)) - lo) / (hi - lo) * nb).astype(np.int32), 0, nb - 1)
    r = 10 ** (lo + (np.arange(nb) + 0.5) / nb * (hi - lo))
    med = np.full(nb, np.nan); dis = np.full(nb, np.nan); cob = np.zeros(nb)
    tot = np.bincount(idx.ravel(), None, nb)
    n = np.bincount(idx[m], None, nb)
    for k in range(nb):
        if n[k] < 400:
            continue
        s = v[m][idx[m] == k]
        med[k] = np.median(s)
        dis[k] = 1.4826 * np.median(np.abs(s - med[k]))
        cob[k] = n[k] / max(tot[k], 1)
    return r, med, dis, cob, n


def caça(run_dir: str) -> dict:
    run = comu.Run.obre(run_dir)
    LL = run.llegeix_rebut("F1.2_sol_llenc.json")["llenc"]
    W, H, RS = LL["W"], LL["H"], LL["R_sol_px"]
    m = np.load(os.path.join(run_dir, "3-filtres", "MASCARA.npy"))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = (np.hypot(yy - H / 2.0, xx - W / 2.0) / RS).astype(np.float32); del yy, xx
    r_ple = min(H, W) / 2.0 / RS
    print(f"anell sencer dins del rectangle fins a {r_ple:.2f} R☉ "
          f"(mes enlla, l'estadistica azimutal es de CANTONS)\n")
    out = {}
    for k in ("PASSA_ALT", "RADIAL", "NRGF", "MGN"):
        p = os.path.join(run_dir, "3-filtres", f"DETALL_{k}.npy")
        if not os.path.exists(p):
            continue
        v = np.load(p).astype(np.float32)
        if v.ndim == 3:
            v = v.mean(axis=2)
        r, med, dis, cob, n = perfil(v, rad, m)
        bo = np.isfinite(med) & (cob > 0.999)
        # el que la mediana azimutal explica: amplitud contra la dispersio
        amp = float(np.nanmax(med[bo]) - np.nanmin(med[bo]))
        dm = float(np.nanmedian(dis[bo]))
        # anells: excursions locals de la mediana contra una versio suau
        ker = np.exp(-0.5 * (np.arange(-25, 26) / 9.0) ** 2); ker /= ker.sum()
        w = bo.astype(float)
        sm = np.convolve(np.where(bo, med, 0.0), ker, "same") / np.maximum(np.convolve(w, ker, "same"), 1e-9)
        res = np.where(bo, med - sm, np.nan)
        sr = 1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res)))
        pics = []
        for i in range(2, len(r) - 2):
            if not bo[i] or not np.isfinite(res[i]):
                continue
            if abs(res[i]) > 4.0 * sr and abs(res[i]) >= max(abs(res[i-1]), abs(res[i+1])):
                pics.append((float(r[i]), float(res[i]), float(res[i] / max(dis[i], 1e-9))))
        pics = sorted(pics, key=lambda t: -abs(t[1]))[:6]
        out[k] = {"amplitud_mediana_azimutal": amp, "dispersio_tipica": dm,
                  "quocient_anell_senyal": amp / max(dm, 1e-9),
                  "r_cobertura_plena": float(r_ple),
                  "anells": [{"r_Rsol": a, "salt": b, "salt_sobre_dispersio": c} for a, b, c in pics]}
        print(f"=== {k} ===")
        print(f"   amplitud de la mediana azimutal {amp:.4f} · dispersio tipica {dm:.4f} "
              f"· quocient {amp/max(dm,1e-9):.3f}")
        for a, b, c in pics:
            print(f"     anell a {a:5.2f} R☉  salt {b:+.4f}  ({c:+.3f} de la dispersio)")
        if not pics:
            print("     cap anell per damunt de 4 sigma")
        print()
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else \
        (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T153314Z*")) + [""])[0] + ""
    o = caça(d)
    json.dump(o, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "anells.json"), "w"), indent=1)
