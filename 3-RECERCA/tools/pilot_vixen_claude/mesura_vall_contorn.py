"""La vall del colze, mesurada AL CONTORN i amb base local per azimut.

⛔ Per què no serveix binar el passa-alt per `ln g`: al llindar canvia el
CONJUNT d'exposicions que hi contribueixen, o sigui que hi canvia la variància,
i la mitjana condicional del passa-alt a `ln g` fix té un biaix d'Eddington que
fa un esglaó allà **tant si la rampa és llisa com si no**. Mesurat, aquell
estadístic dona −0,077 % amb rampa lineal i −0,087 % amb smoothstep: no
distingeix res.

El que sí que distingeix: seguir el contorn a l'espai, mirar el perfil del
detall **transversalment** al contorn, i treure-hi una base local ajustada als
extrems de la finestra. La vall és una depressió estreta damunt d'aquesta base.
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


def mesura(comp: Path, detall: Path, t_llarga: float = 10.079368399159,
           n_az: int = 720, mig: int = 45, vora: int = 15) -> dict:
    g = np.asarray(np.load(comp / "HDR_adu_s.npy", mmap_mode="r")[..., 1], np.float32)
    d = np.load(detall / "DETALL_ln.npy", mmap_mode="r")
    w = np.load(detall / "PES.npy", mmap_mode="r")
    H, W = g.shape
    cy, cx = H / 2.0, W / 2.0
    llind = C.SOSTRE / t_llarga

    perfils = []
    for k in range(n_az):
        ang = 2 * np.pi * k / n_az
        sy, sx = np.sin(ang), np.cos(ang)
        rad = np.arange(0.5 * C.R_SOL_PX, 4.5 * C.R_SOL_PX, 1.0)
        yy = cy + sy * rad; xx = cx + sx * rad
        ok = (yy > 1) & (yy < H - 2) & (xx > 1) & (xx < W - 2)
        if ok.sum() < 200:
            continue
        yy, xx, rad = yy[ok], xx[ok], rad[ok]
        v = ndi.map_coordinates(g, [yy, xx], order=1, mode="nearest")
        # el creuament més EXTERN de v amb el llindar
        s = np.sign(v - llind)
        creua = np.flatnonzero(np.diff(s) != 0)
        if creua.size == 0:
            continue
        i0 = creua[-1]
        j = np.arange(i0 - mig, i0 + mig + 1)
        if j[0] < 0 or j[-1] >= len(rad):
            continue
        yy2 = cy + sy * rad[j]; xx2 = cx + sx * rad[j]
        pd = ndi.map_coordinates(np.asarray(d), [yy2, xx2], order=1, mode="nearest")
        pw = ndi.map_coordinates(np.asarray(w, np.float32), [yy2, xx2], order=1, mode="nearest")
        if (pw <= 0).any() or not np.isfinite(pd).all():
            continue
        perfils.append(pd)
    if len(perfils) < 50:
        return {"estat": "sense mostra", "n_azimuts": len(perfils)}

    P = np.stack(perfils)                       # (n_az, 2*mig+1)
    x = np.arange(-mig, mig + 1)
    # base local: els extrems de la finestra
    ext = np.abs(x) > mig - vora
    A = np.vstack([np.ones(ext.sum()), x[ext]]).T
    coef, *_ = np.linalg.lstsq(A, P[:, ext].T, rcond=None)
    base = coef[0][:, None] + coef[1][:, None] * x[None, :]
    R = P - base
    nucli = np.abs(x) <= 8
    prof = R[:, nucli].mean(axis=1)             # una mesura per azimut
    mitj = float(prof.mean())
    err = float(prof.std(ddof=1) / np.sqrt(len(prof)))
    return {"n_azimuts": int(len(perfils)),
            "profunditat_ln": round(mitj, 8),
            "profunditat_percent": round(100 * abs(np.expm1(mitj)), 5),
            "error_percent": round(100 * abs(np.expm1(err)), 5),
            "sigma": round(abs(mitj) / err, 2) if err else None,
            "perfil_transversal_ln": [round(float(v), 8) for v in R.mean(axis=0)],
            "veredicte": "VALL" if err and abs(mitj) / err > 3 else "sense vall (<3 sigma)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parells", nargs="+", help="compost:detall")
    a = ap.parse_args()
    out = {}
    for p in a.parells:
        comp, det = p.split(":")
        r = mesura(Path(comp), Path(det))
        et = Path(comp).parts[-2]
        out[et] = r
        print(f"{et:32s} profunditat {r.get('profunditat_percent')} % "
              f"± {r.get('error_percent')} %  ({r.get('sigma')} sigma)  {r.get('veredicte')}")
    print()
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'perfil_transversal_ln'}
                      for k, v in out.items()}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
