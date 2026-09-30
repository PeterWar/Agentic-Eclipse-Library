"""Mesura el detall AL LLARG de cada frontera de fusió, seguint la isofota.

⛔ Per què no serveix un perfil radial: les fronteres de fusió **són isofotes**,
no circumferències. Mesurat al pilot, la del fotograma llarg va de 1,60 a
2,35 R☉ mentre que la vall que hi deixa el colze fa 0,034 R☉: un calaix radial
de l'amplada de la vall n'agafa el **4,3 %**, o sigui que un estadístic radial la
dilueix per un factor ~23. Per això la porta E2 diu que està bé i l'ull hi veu
l'arc.

Aquí es fa el que toca: per a cada azimut, es troba el radi on el compost creua
el nivell de la frontera, es mostreja el detall transversalment, s'hi treu una
base local ajustada als extrems de la finestra, i es promedia sobre azimuts.

⛔ I la prova que decideix si un arc és artefacte o corona: **els dos trens tenen
jocs d'exposicions diferents**, o sigui que les seves fronteres cauen a radis
diferents. Un arc que segueix les fronteres de cada tren és artefacte; un que
apareix als dos al mateix radi és corona.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def al_contorn(comp: np.ndarray, detall: np.ndarray, pes: np.ndarray, nivell: float,
               *, n_az: int = 720, mig: int = 60, nucli: int = 6, vora: int = 18,
               r0: float = 1.05, r1: float = 5.5,
               az: tuple[float, float] | None = None,
               desplacament: int = 0) -> dict:
    """`az` en graus, mesurat des de dalt i cap a la dreta (0 = nord, 90 = est
    de la imatge). ⛔ Cal, perquè un artefacte de frontera pot ser azimutalment
    variable i promediar els 720 azimuts el dilueix."""
    H, W = comp.shape
    cy, cx = H / 2.0, W / 2.0
    perfils, radis = [], []
    for k in range(n_az):
        graus = 360.0 * k / n_az
        if az is not None:
            lo, hi = az
            dins = (lo <= graus <= hi) if lo <= hi else (graus >= lo or graus <= hi)
            if not dins:
                continue
        ang = np.deg2rad(graus)
        sy, sx = -np.cos(ang), np.sin(ang)      # 0 graus = amunt a la imatge
        rad = np.arange(r0 * C.R_SOL_PX, r1 * C.R_SOL_PX, 1.0)
        yy = cy + sy * rad; xx = cx + sx * rad
        ok = (yy > mig + 2) & (yy < H - mig - 2) & (xx > mig + 2) & (xx < W - mig - 2)
        if ok.sum() < 200:
            continue
        yy, xx, rad = yy[ok], xx[ok], rad[ok]
        v = ndi.map_coordinates(comp, [yy, xx], order=1, mode="nearest")
        j = np.flatnonzero(v < nivell)          # primer creuament cap enfora
        if j.size == 0 or j[0] < mig or j[0] + mig >= len(rad):
            continue
        # ⛔ `desplacament` és el CONTROL APARELLAT: el mateix contorn, amb la
        # mateixa forma i la mateixa llargada, mogut radialment fora de la zona
        # de fusió. Cal perquè amb una escala d'1 EV **no existeix cap nivell
        # que estigui lluny d'una frontera** —els nivells de frontera van de
        # ×1,25 en ×1,25—, o sigui que un «control» triat per nivell cau dins
        # la zona de fusió i mesura el mateix que la frontera. Mesurat el
        # 24-08-2026: a 1,97 R☉ el control per nivell donava 0,1472 % i la
        # frontera 0,1471 %, i el gate quedava sense dents.
        i0 = j[0] + desplacament
        if i0 < mig or i0 + mig >= len(rad):
            continue
        idx = np.arange(i0 - mig, i0 + mig + 1)
        y2 = cy + sy * rad[idx]; x2 = cx + sx * rad[idx]
        pd = ndi.map_coordinates(detall, [y2, x2], order=1, mode="nearest")
        pw = ndi.map_coordinates(pes, [y2, x2], order=1, mode="nearest")
        if (pw <= 0).any() or not np.isfinite(pd).all():
            continue
        perfils.append(pd); radis.append(rad[i0] / C.R_SOL_PX)
    if len(perfils) < 30:
        return {"estat": "sense mostra", "n_azimuts": len(perfils)}
    P = np.stack(perfils)
    x = np.arange(-mig, mig + 1)
    ext = np.abs(x) > mig - vora
    A = np.vstack([np.ones(ext.sum()), x[ext]]).T
    coef, *_ = np.linalg.lstsq(A, P[:, ext].T, rcond=None)
    R = P - (coef[0][:, None] + coef[1][:, None] * x[None, :])
    prof = R[:, np.abs(x) <= nucli].mean(axis=1)
    mitj = float(prof.mean()); err = float(prof.std(ddof=1) / np.sqrt(len(prof)))
    radis = np.array(radis)
    return {"nivell": float(f"{nivell:.6g}"), "n_azimuts": int(len(perfils)),
            "radi_median_rsol": round(float(np.median(radis)), 3),
            "radi_min_rsol": round(float(radis.min()), 3),
            "radi_max_rsol": round(float(radis.max()), 3),
            "profunditat_ln": round(mitj, 8),
            "amplitud_percent": round(100 * abs(np.expm1(mitj)), 5),
            "error_percent": round(100 * abs(np.expm1(err)), 5),
            "sigma": round(abs(mitj) / err, 2) if err else None,
            "perfil_transversal": [round(float(v), 8) for v in R.mean(axis=0)],
            "estat": "FRONTERA VISTA" if err and abs(mitj) / err > 3 else "no detectada"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--comp", type=Path, required=True)
    ap.add_argument("--detall", type=Path, required=True)
    ap.add_argument("--sostre", type=float, required=True)
    ap.add_argument("--exposicions", type=float, nargs="+", required=True)
    ap.add_argument("--fb", type=float, default=None,
                    help="si el compost és en B/B☉, el factor per tornar a ADU/s")
    ap.add_argument("--etiqueta", default="tren")
    ap.add_argument("--az", type=float, nargs=2, default=None,
                    help="rang azimutal en graus, 0 = amunt a la imatge")
    # ⛔ Sense CONTROLS això no és una porta, és un detector d'isofotes. El 24-08
    # quatre isofotes que NO són frontera van donar de 2,7 a 3,8 σ, els mateixos
    # valors que les fronteres: el que es mesurava era el mètode. El límit se'l
    # calibren els controls.
    ap.add_argument("--controls", type=float, nargs="+", default=None,
                    help="nivells (ADU/s) extra; per defecte NO se'n fan servir "
                         "perquè amb una escala d'1 EV no n'hi ha cap de lliure")
    ap.add_argument("--desplacament", type=int, default=110,
                    help="px del control aparellat: el mateix contorn, mogut")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    comp = np.load(a.comp, mmap_mode="r")
    g = np.asarray(comp[..., 1] if comp.ndim == 3 else comp, np.float32)
    if a.fb:
        g = g / np.float32(a.fb)
    d = np.asarray(np.load(a.detall / "DETALL_ln.npy", mmap_mode="r"), np.float32)
    w = np.asarray(np.load(a.detall / "PES.npy", mmap_mode="r"), np.float32)
    out = {"tren": a.etiqueta, "sostre": a.sostre, "fronteres": []}
    print(f"{a.etiqueta}:")
    print("   nivell(ADU/s)  radi (R☉)          amplitud    ±        σ    veredicte")
    for t in sorted(a.exposicions):
        for nom, niv in (("pes→0", a.sostre / t), ("pes→1", 0.2 * a.sostre / t)):
            r = al_contorn(g, d, w, niv, az=tuple(a.az) if a.az else None)
            if r.get("estat") == "sense mostra":
                continue
            if not (1.06 < r["radi_median_rsol"] < 5.2):
                continue
            r["t_s"] = t; r["quin"] = nom
            out["fronteres"].append(r)
            print(f"  {niv:12.1f}  {r['radi_median_rsol']:5.3f} "
                  f"({r['radi_min_rsol']:.2f}-{r['radi_max_rsol']:.2f})  "
                  f"{r['amplitud_percent']:7.4f} % {r['error_percent']:7.4f} % "
                  f"{str(r['sigma']):>6s}  {r['estat']}  [t={t:g} s, {nom}]")
    # ── CONTROLS APARELLATS: el mateix contorn de cada frontera, desplaçat
    # ⛔ No es trien per nivell. Amb l'escala d'1 EV els nivells de frontera van
    # de ×1,25 en ×1,25 i **no queda cap nivell lliure**: un control per nivell
    # cau dins la zona de fusió del veí i mesura exactament el mateix.
    out["controls"] = []
    print(f"  controls APARELLATS (el mateix contorn, {a.desplacament:+d} px):")
    for fr in list(out["fronteres"]):
        for dp in (a.desplacament, -a.desplacament):
            r = al_contorn(g, d, w, fr["nivell"], az=tuple(a.az) if a.az else None,
                           desplacament=dp)
            if r.get("estat") == "sense mostra" or not (1.06 < r.get("radi_median_rsol", 0) < 5.2):
                continue
            r["de_la_frontera"] = f"t={fr['t_s']:g}s {fr['quin']}"; r["desplacament_px"] = dp
            out["controls"].append(r)
            print(f"  {fr['nivell']:12.1f}  {r['radi_median_rsol']:5.3f} "
                  f"({r['radi_min_rsol']:.2f}-{r['radi_max_rsol']:.2f})  "
                  f"{r['amplitud_percent']:7.4f} % {r['error_percent']:7.4f} % "
                  f"{str(r['sigma']):>6s}  CONTROL {dp:+d} px de {r['de_la_frontera']}")
    for niv in (a.controls or []):
        r = al_contorn(g, d, w, niv, az=tuple(a.az) if a.az else None)
        if r.get("estat") != "sense mostra" and 1.06 < r.get("radi_median_rsol", 0) < 5.2:
            out["controls"].append(r)

    import portes as P
    dades = ([{"nom": f"t={x['t_s']:g}s {x['quin']} r={x['radi_median_rsol']:.2f}",
               "es_frontera": True, "contrast": x["profunditat_ln"],
               "sigma": abs(x["profunditat_ln"]) / x["sigma"] if x.get("sigma") else float("nan")}
              for x in out["fronteres"] if x.get("sigma")]
             + [{"nom": f"control {x.get('desplacament_px', 0):+d}px r={x['radi_median_rsol']:.2f}",
                 "es_frontera": False,
                 "contrast": x["profunditat_ln"],
                 "sigma": abs(x["profunditat_ln"]) / x["sigma"] if x.get("sigma") else float("nan")}
                for x in out["controls"] if x.get("sigma")])
    out["porta_h_costures"] = P.porta_h_costures(dades)
    g_ = out["porta_h_costures"]
    print(f"\n  H2 (costures) {g_['estat']}"
          + (f"  ·  pitjor {g_.get('pitjor_frontera')} a {g_.get('pitjor_sigmes')} σ "
             f"contra un terra de control de {g_.get('terra_dels_controls')} σ"
             if "pitjor_frontera" in g_ else f"  ·  {g_.get('motiu','')}"))
    if a.json:
        C.desa_json(a.json, out)
        print(f"  → {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
