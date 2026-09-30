"""V21b: NOMÉS estrelles del catàleg (l'ordre de Pere: la resta són fake).

Predicció: cat2_sony.csv (ξ,η = xh_as,yh_as del pla tangent horitzontal
refractat centrat al Sol, l'època de DSC06993) → model de placa sony_radial
(final_solution.json) → px del sensor de DSC06993 (LA NOSTRA BASE) → llenç
V19 per la cadena geomètrica de sempre. Matching contra les 1.263 deteccions
de l'apilat registrat; es queden NOMÉS les aparellades.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17

DERIV = ("/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/"
         "Estrelles/")
SOLU = DERIV + "Resultats_acceptacio_2026-08-17/final_solution.json"
CAT2 = None  # es resol sota (Work o Proves)
TOL_PX = 6.0
VLIM = 11.5


def cerca_cat2():
    for c in (DERIV + "Work_2026-08-17/xmatch/cat2_sony.csv",
              DERIV + "Proves_2026-08-17/Estrelles_work_xmatch_fotometria/"
                      "xmatch/cat2_sony.csv"):
        if os.path.exists(c):
            return c
    raise FileNotFoundError("cat2_sony.csv")


def main():
    import pandas as pd
    sol = json.load(open(SOLU))["sony_radial"]
    px, py = np.array(sol["px"]), np.array(sol["py"])
    cat = pd.read_csv(cerca_cat2())
    print(f"catàleg: {len(cat)} files · columnes amb xh_as: "
          f"{'xh_as' in cat.columns}")
    vus = cat["Vuse"] if "Vuse" in cat.columns else cat["Vmag"]
    cat = cat[np.isfinite(cat["xh_as"]) & np.isfinite(cat["yh_as"])
              & (vus <= VLIM)].reset_index(drop=True)
    print(f"amb V ≤ {VLIM}: {len(cat)}")
    xi = cat["xh_as"].to_numpy(float)
    eta = cat["yh_as"].to_numpy(float)

    def aplica(p, xi, eta):
        cols = [np.ones_like(xi), xi, eta]
        if len(p) == 5:
            r2 = xi * xi + eta * eta
            cols += [xi * r2, eta * r2]
        A = np.column_stack(cols)
        return A @ p

    Xs = aplica(px, xi, eta)     # px del sensor de DSC06993
    Ys = aplica(py, xi, eta)

    # sensor DSC06993 → llenç V19 (la cadena de sempre, amb el sol de S13)
    sv = F17.SV16()
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    vb = S13["DSC06993.ARW"]
    solb = (vb["sol_x"], vb["sol_y"])
    x15, y15 = geo15.raw_sony_a_v15(Xs, Ys, solb)
    xc, yc = sv.endavant(x15, y15)
    # el sol de S13 vs el de la placa: mateix fotograma, dues mesures
    print(f"sol de la placa (radial): ({sol['sun_x']:.1f}, {sol['sun_y']:.1f})"
          f" · sol de S13: ({solb[0]:.1f}, {solb[1]:.1f}) · "
          f"dif ({sol['sun_x']-solb[0]:+.1f}, {sol['sun_y']-solb[1]:+.1f}) px")

    dins = (xc > 20) & (xc < sv.W16 - 20) & (yc > 20) & (yc < sv.H16 - 20)
    cat = cat[dins].reset_index(drop=True)
    xc, yc = xc[dins], yc[dins]
    print(f"dins del llenç: {len(cat)}")

    est = np.load(os.path.join(CAU, "estrelles_v21.npy"))
    print(f"deteccions de l'apilat registrat: {len(est)}")
    t = cKDTree(np.c_[xc, yc])
    d, j = t.query(est[:, :2], k=1)
    prop = d < 25.0
    # correcció fina global (mediana de les diferències de les parelles clares)
    if prop.sum() >= 10:
        ddx = np.median(est[prop, 0] - xc[j[prop]])
        ddy = np.median(est[prop, 1] - yc[j[prop]])
        print(f"correcció fina predicció→detecció: ({ddx:+.2f}, {ddy:+.2f}) px")
        xc += ddx
        yc += ddy
        t = cKDTree(np.c_[xc, yc])
        d, j = t.query(est[:, :2], k=1)
    bo = d < TOL_PX
    # una detecció per estrella (la més propera)
    tria = {}
    for i in np.where(bo)[0]:
        jj = int(j[i])
        if jj not in tria or d[i] < d[tria[jj]]:
            tria[jj] = i
    idx_det = np.array(sorted(tria.values()), int)
    print(f"APARELLADES (≤{TOL_PX} px): {len(idx_det)} "
          f"(de {len(est)} deteccions; {100*len(idx_det)/len(est):.0f} % "
          f"de les deteccions eren fake o sota el llindar del catàleg)")
    res = d[idx_det]
    print(f"residus px: mediana {np.median(res):.2f} · p90 {np.percentile(res,90):.2f}")

    files = []
    for i in idx_det:
        jj = int(j[i])
        r = cat.iloc[jj]
        files.append({
            "x": float(est[i, 0]), "y": float(est[i, 1]),
            "flux": float(est[i, 2]), "area": float(est[i, 3]),
            "resid_px": float(d[i]),
            "V": float(r.get("Vuse", r.get("Vmag", np.nan))),
            "HIP": None if pd.isna(r.get("HIP_n", r.get("HIP"))) else
                   int(r.get("HIP_n", r.get("HIP"))),
            "TYC": str(r.get("TYC", "")),
            "HD": None if pd.isna(r.get("HD")) else int(r.get("HD")),
            "Sp": str(r.get("Sp", "")),
        })
    files.sort(key=lambda z: z["V"])
    json.dump(files, open(os.path.join(CAU, "estrelles_cataleg.json"), "w"),
              indent=1, ensure_ascii=False)
    est_bo = est[idx_det]
    np.save(os.path.join(CAU, "estrelles_v21_cataleg.npy"), est_bo)
    print("les 12 més brillants aparellades:")
    for z in files[:12]:
        nom = f"HIP {z['HIP']}" if z["HIP"] else (f"HD {z['HD']}" if z["HD"]
                                                  else z["TYC"])
        print(f"  V {z['V']:.2f} · {nom} · ({z['x']:.0f},{z['y']:.0f}) · "
              f"resid {z['resid_px']:.2f} px · {z['Sp']}")
    # les brillants del catàleg NO detectades (completesa)
    td = cKDTree(est[:, :2])
    d2, _ = td.query(np.c_[xc, yc], k=1)
    brill = (cat["Vuse"] if "Vuse" in cat.columns else cat["Vmag"]) <= 8.0
    perd = (d2 > TOL_PX) & brill.to_numpy()
    print(f"catàleg V≤8 dins del llenç: {int(brill.sum())} · no detectades: "
          f"{int(perd.sum())}")


if __name__ == "__main__":
    import pandas as pd  # noqa: F401
    main()
