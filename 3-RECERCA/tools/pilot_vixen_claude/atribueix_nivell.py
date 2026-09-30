"""Separa una dependència amb el NIVELL d'una dependència amb el RADI.

## El problema que resol

El desacord entre esglaons d'exposició veïns depèn del nivell, i això té dues
explicacions amb la mateixa signatura:

| causa | de què depèn de veritat |
|---|---|
| no-linealitat del pou | del **nivell**: és una propietat del senyal |
| error del flat | de la **posició al camp**: és una propietat del detector |

Es confonen perquè el nivell de la corona **cau amb el radi**, o sigui que
qualsevol cosa que depengui del radi sembla que depengui del nivell.

## Com les separa

La corona **no és circular**: a un radi fix hi ha serpentines brillants i forats
foscos, o sigui un rang de nivells. Aquell rang és la palanca. Es mira:

- **efecte del nivell A RADI FIX**: dins de cada calaix de radi, mediana del
  desacord al tercil alt menys la del tercil baix de nivell;
- **efecte del radi A NIVELL FIX**: dins de cada calaix de nivell, mediana del
  desacord al tercil exterior menys la del tercil interior de radi.

Si el primer sobreviu i el segon s'esvaeix, és el **sensor**. Si passa al revés,
és **el camp** —flat, vinyetatge o qualsevol cosa fixa al detector—.

⛔ Cap dels dos efectes no es llegeix tot sol: es comparen **entre ells**, i
amb la seva pròpia incertesa treta d'un bootstrap per sectors angulars, perquè
els píxels veïns no són independents.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402

R_SOL = C.R_SOL_PX


def _terciles(v: np.ndarray) -> tuple[float, float]:
    return float(np.quantile(v, 1 / 3)), float(np.quantile(v, 2 / 3))


def decompon(q: np.ndarray, radi: np.ndarray, nivell: np.ndarray,
             sector: np.ndarray, *, n_calaixos: int = 12,
             n_bootstrap: int = 200, llavor: int = 20260825) -> dict:
    """Efecte del nivell a radi fix i efecte del radi a nivell fix.

    `q` és el desacord relatiu, `radi` en R☉, `nivell` en ADU crus i `sector`
    l'índex de sector angular, que és la unitat del bootstrap.
    """
    def _sense_tendencia(qq: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Treu la tendència LINEAL del confusor dins del calaix.

        ⛔ Sense això la prova s'enganya i ho vaig comprovar: un calaix de radi
        té amplada, i dins seu el nivell continua caient amb el radi, o sigui
        que triar el tercil alt de nivell **també tria el radi petit**. Una
        dependència purament radial passava per SENSOR a més de 3 σ.
        """
        if x.size < 20:
            return qq - np.median(qq)
        # ⚠️ aritmètica explícita, no `A @ coef`: el BLAS del sistema hi
        # emetia avisos d'overflow sobre buffers no inicialitzats.
        xc = np.ascontiguousarray(x, np.float64) - float(np.mean(x))
        qc = np.ascontiguousarray(qq, np.float64)
        var = float(np.dot(xc, xc))
        pend = float(np.dot(xc, qc)) / var if var > 0 else 0.0
        return qc - (float(np.mean(qc)) + pend * xc)

    def _un_cop(sel: np.ndarray) -> tuple[float, float]:
        qq, rr, nn = q[sel], radi[sel], nivell[sel]
        ln = np.log(np.maximum(nn, 1e-6))
        # efecte del NIVELL, a radi fix (i sense la tendència radial de dins)
        vores_r = np.quantile(rr, np.linspace(0, 1, n_calaixos + 1))
        ef_niv = []
        for a, b in zip(vores_r[:-1], vores_r[1:]):
            m = (rr >= a) & (rr < b)
            if m.sum() < 300:
                continue
            qs = _sense_tendencia(qq[m], rr[m])
            nm = nn[m]
            lo, hi = _terciles(nm)
            baix, alt = qs[nm <= lo], qs[nm >= hi]
            if baix.size > 50 and alt.size > 50:
                ef_niv.append(float(np.median(alt) - np.median(baix)))
        # efecte del RADI, a nivell fix (i sense la tendència de nivell de dins)
        vores_n = np.quantile(nn, np.linspace(0, 1, n_calaixos + 1))
        ef_rad = []
        for a, b in zip(vores_n[:-1], vores_n[1:]):
            m = (nn >= a) & (nn < b)
            if m.sum() < 300:
                continue
            qs = _sense_tendencia(qq[m], ln[m])
            rm = rr[m]
            lo, hi = _terciles(rm)
            dins, fora = qs[rm <= lo], qs[rm >= hi]
            if dins.size > 50 and fora.size > 50:
                ef_rad.append(float(np.median(fora) - np.median(dins)))
        return (float(np.median(ef_niv)) if ef_niv else np.nan,
                float(np.median(ef_rad)) if ef_rad else np.nan)

    tot = np.ones(q.size, bool)
    niv, rad = _un_cop(tot)
    rng = np.random.default_rng(llavor)
    secs = np.unique(sector)
    bn, br = [], []
    for _ in range(n_bootstrap):
        tria = rng.choice(secs, secs.size, replace=True)
        sel = np.isin(sector, tria)          # ⚠️ sense repetició: cota inferior
        a, b = _un_cop(sel)
        if np.isfinite(a):
            bn.append(a)
        if np.isfinite(b):
            br.append(b)
    return {"efecte_nivell_a_radi_fix": niv,
            "sigma_nivell": float(np.std(bn)) if bn else np.nan,
            "efecte_radi_a_nivell_fix": rad,
            "sigma_radi": float(np.std(br)) if br else np.nan,
            "n_pixels": int(q.size), "n_sectors": int(secs.size)}


def veredicte(d: dict, *, sigmes: float = 3.0) -> dict:
    n, sn = d["efecte_nivell_a_radi_fix"], d["sigma_nivell"]
    r, sr = d["efecte_radi_a_nivell_fix"], d["sigma_radi"]
    hi_ha_n = np.isfinite(n) and np.isfinite(sn) and abs(n) > sigmes * sn
    hi_ha_r = np.isfinite(r) and np.isfinite(sr) and abs(r) > sigmes * sr
    if hi_ha_n and not hi_ha_r:
        v, per = "SENSOR", "el nivell sobreviu a radi fix i el radi no a nivell fix"
    elif hi_ha_r and not hi_ha_n:
        v, per = "CAMP", "el radi sobreviu a nivell fix i el nivell no a radi fix"
    elif hi_ha_n and hi_ha_r:
        v, per = "TOTS_DOS", "les dues dependències sobreviuen al condicionament"
    else:
        v, per = "CAP", "cap de les dues no arriba al llindar"
    return {"veredicte": v, "perque": per, "llindar_sigmes": sigmes,
            "nivell_sigmes": float(abs(n) / sn) if np.isfinite(sn) and sn > 0 else None,
            "radi_sigmes": float(abs(r) / sr) if np.isfinite(sr) and sr > 0 else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("esglaons", type=Path, help="directori amb num_XX.npy i den_XX.npy")
    ap.add_argument("--r-min", type=float, default=1.05)
    ap.add_argument("--r-max", type=float, default=2.40)
    ap.add_argument("--salt", type=int, default=3, help="submostreig de píxels")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()

    exps = {int(k): v for k, v in
            json.loads((a.esglaons / "exposicions.json").read_text())
            .get("exposicions", json.loads((a.esglaons / "exposicions.json").read_text())).items()}
    idx = sorted(exps)
    reixa = json.loads((C.REPO / "output" / "pilot_vixen_claude_20260824"
                        / "fase2_fisiques_flat-si_coh.json").read_text())["reixa"]
    cx, cy = reixa["sol"]
    H, W = reixa["h"], reixa["w"]
    yy = (np.arange(0, H, a.salt) - cy)[:, None]
    xx = (np.arange(0, W, a.salt) - cx)[None, :]
    rr = np.sqrt(yy ** 2 + xx ** 2) / R_SOL
    az = np.degrees(np.arctan2(yy * np.ones_like(xx), xx * np.ones_like(yy))) % 360.0
    sec = (az // 10).astype(np.int16)
    dins = (rr >= a.r_min) & (rr <= a.r_max)

    def taxa(i: int) -> np.ndarray:
        n = np.load(a.esglaons / f"num_{i:02d}.npy", mmap_mode="r")[::a.salt, ::a.salt]
        d = np.load(a.esglaons / f"den_{i:02d}.npy", mmap_mode="r")[::a.salt, ::a.salt]
        n, d = np.asarray(n, np.float64), np.asarray(d, np.float64)
        out = np.full(n.shape, np.nan)
        bo = d > 0
        out[bo] = n[bo] / d[bo]
        return out

    parells = []
    ant = None
    for i in idx:
        t = taxa(i)
        if ant is not None:
            ia, ta = ant
            bo = dins & np.isfinite(t) & np.isfinite(ta) & (t > 0) & (ta > 0)
            if bo.sum() >= 5000:
                q = (t[bo] / ta[bo]) - 1.0
                nivell = ta[bo] * exps[i]          # ADU crus a la llarga
                d = decompon(q, rr[bo], nivell, sec[bo])
                d.update({"esglao_curt": ia, "esglao_llarg": i,
                          "t_curt_s": exps[ia], "t_llarg_s": exps[i],
                          "desacord_median_percent": float(np.median(q) * 100)})
                d.update(veredicte(d))
                parells.append(d)
                print(f"  {exps[ia]:.6g}→{exps[i]:.6g} s  "
                      f"nivell {d['efecte_nivell_a_radi_fix']*100:+.3f}±"
                      f"{d['sigma_nivell']*100:.3f} %   "
                      f"radi {d['efecte_radi_a_nivell_fix']*100:+.3f}±"
                      f"{d['sigma_radi']*100:.3f} %   → {d['veredicte']}", flush=True)
        ant = (i, t)

    vots = {}
    for p in parells:
        vots[p["veredicte"]] = vots.get(p["veredicte"], 0) + 1
    out = {"parells": parells, "vots": vots, "r_min": a.r_min, "r_max": a.r_max,
           "salt": a.salt}
    print("\n  vots:", vots)
    if a.json:
        C.desa_json(a.json, out)
        print(f"  → {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
