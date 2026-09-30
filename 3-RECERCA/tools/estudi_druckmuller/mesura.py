"""Mesura els composts de Brno del 12-08-2026: color, corba de to i cel.

Tres mesures independents per anell de radi:
  1. color TOTAL (mitjana lineal) -> inclou el cel, que Brno NO resta a zero;
  2. color de l'ESTRUCTURA (brillants menys foscos del mateix anell) -> el cel
     s'hi cancel.la perque a un radi donat es gairebe uniforme;
  3. nivell MOSTRAT (sRGB 0-1) -> comparable amb la taula del research/108.

Norma del rectangle: cap anell no es retalla. Es mesura la COBERTURA de cada
anell i es declara; per sobre del radi on l'anell surt del rectangle, les
estadistiques son de cantonada i no valen com a absolut.
"""
import json
import os
import numpy as np
from geometria import CARPETA, carrega, retalla_marc, srgb_a_lineal

AQUI = os.path.dirname(os.path.abspath(__file__))
RATIO_LLUNA_SOL = 1.0335          # efemeride a Trigaza, C2 18:28:24 UT

# Perfil B/B_sol mesurat sobre el NOSTRE compost calibrat del mateix eclipsi
# (research/108 §3). S'hi inclou el cel, igual que als composts de Brno.
R108 = np.array([1.09, 1.62, 2.15, 2.68, 3.74, 5.33, 8.51])
B108 = np.array([1.61e-6, 7.28e-8, 1.96e-8, 1.25e-8, 9.26e-9, 8.11e-9, 7.56e-9])


def b_de_r(r):
    return np.exp(np.interp(np.log(r), np.log(R108), np.log(B108)))


def perfil(nom):
    rgb = carrega(nom)
    f0, f1, c0, c1 = retalla_marc(rgb)
    sub = rgb[f0:f1, c0:c1]
    lin = srgb_a_lineal(sub)
    g = json.load(open(os.path.join(AQUI, "geometria.json")))[nom]
    cy, cx, Rll = g["cy"], g["cx"], g["R_lluna_px"]
    Rsol = Rll / RATIO_LLUNA_SOL

    ny, nx = sub.shape[:2]
    yy, xx = np.mgrid[0:ny, 0:nx]
    r = np.hypot(yy - cy, xx - cx) / Rsol
    r_ple = min(cy, cx, ny - cy, nx - cx) / Rsol      # ultim anell sencer
    r_max = float(r.max())

    lum_sr = sub.mean(axis=2)                          # nivell mostrat
    files = []
    vores = np.geomspace(1.02, r_max, 60)
    for a, b in zip(vores[:-1], vores[1:]):
        m = (r >= a) & (r < b)
        n = int(m.sum())
        if n < 300:
            continue
        rc = float(np.sqrt(a * b))
        v = lin[m]                                     # (n,3) lineal
        L = lum_sr[m]
        # cobertura azimutal real de l'anell
        th = np.arctan2((yy - cy)[m], (xx - cx)[m])
        cob = np.unique(((th + np.pi) / (2 * np.pi) * 360).astype(int)).size / 360.0

        tot = v.mean(axis=0)
        # estructura: brillants menys foscos del MATEIX anell (el cel s'hi va)
        lv = v @ np.array([0.2126, 0.7152, 0.0722])
        alt = lv >= np.percentile(lv, 85)
        baix = lv <= np.percentile(lv, 35)
        est = v[alt].mean(axis=0) - v[baix].mean(axis=0)
        files.append(dict(r=rc, n=n, cobertura=cob,
                          nivell_sRGB=float(np.median(L)),
                          tot=[float(x) for x in tot],
                          est=[float(x) for x in est]))
    return dict(nom=nom, Rsol_px=Rsol, r_ple=float(r_ple), r_max=r_max,
                mida=[ny, nx], centre=[cx, cy], files=files)


if __name__ == "__main__":
    out = {}
    for nom in sorted(json.load(open(os.path.join(AQUI, "geometria.json")))):
        p = perfil(nom)
        out[nom] = p
        print(f"\n=== {nom}   R_sol {p['Rsol_px']:.1f} px   "
              f"anell sencer fins a {p['r_ple']:.2f} R_sol   cantonada {p['r_max']:.2f} ===")
        print(f"{'r':>6} {'cob':>5} {'nivell':>7} | {'TOT R/G':>8} {'TOT B/G':>8} "
              f"| {'EST R/G':>8} {'EST B/G':>8}")
        for f in p["files"]:
            t, e = f["tot"], f["est"]
            tr, tb = t[0] / t[1], t[2] / t[1]
            er = e[0] / e[1] if e[1] > 1e-6 else float("nan")
            eb = e[2] / e[1] if e[1] > 1e-6 else float("nan")
            if f["r"] < 1.3 or abs(np.log(f["r"]) % 0.25) < 0.06 or f["r"] > 0.9 * p["r_max"]:
                print(f"{f['r']:6.2f} {f['cobertura']*100:4.0f}% {f['nivell_sRGB']:7.3f} "
                      f"| {tr:8.3f} {tb:8.3f} | {er:8.3f} {eb:8.3f}")
    json.dump(out, open(os.path.join(AQUI, "perfils.json"), "w"), indent=1)
