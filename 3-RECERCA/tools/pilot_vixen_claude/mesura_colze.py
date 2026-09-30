"""Mesura la vall que la rampa de saturació deixa a la frontera de fusió.

⛔ L'entrada dolenta coneguda: una rampa LINEAL arriba a zero amb pendent no nul,
o sigui que el pes d'una exposició desapareix amb un colze C⁰ i un passa-alt el
pinta com una vall fosca que segueix una isofota. Una `smoothstep` el fa C¹.

Aquí es mesura la vall directament: mitjana del passa-alt a la banda de la
frontera contra la mitjana als mateixos radis fora de la banda, amb l'error
estàndard de cada mitjana perquè el número tingui σ.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def mesura(dirc: Path, t_llarga: float = 10.079368399159, nb: int = 220) -> dict:
    """El passa-alt en funció de la distància al llindar de saturació.

    ⛔ La frontera NO es troba per la cobertura: el drizzle la fa saltar 60
    valors entre píxels veïns. Es troba per on és de veritat: la **isofota** on
    l'exposició més llarga toca el sostre, `SOSTRE / t`. I es mesura com un
    perfil en `ln(g / llindar)`, que és una coordenada on el colze cau
    exactament a 0 i el radi no hi entra.
    """
    hdr = np.load(dirc / "HDR_adu_s.npy", mmap_mode="r")
    g = np.asarray(hdr[..., 1], np.float32)
    H, W = g.shape
    m = np.isfinite(g) & (g > 0)

    ln = np.where(m, np.log(np.maximum(g, 1e-30)), 0.0).astype(np.float32)
    pes = m.astype(np.float32)
    num = cv2.GaussianBlur(ln * pes, (0, 0), 10.0)
    den = cv2.GaussianBlur(pes, (0, 0), 10.0)
    hp = np.where(den > 1e-6, ln - num / np.maximum(den, 1e-6), 0.0)

    llindars = {"sortida_del_pes": C.SOSTRE / t_llarga,
                "entrada_a_la_rampa": (1.0 - C.RAMPA_SOSTRE) * C.SOSTRE / t_llarga}
    out = {"dir": str(dirc), "t_llarga_s": t_llarga}
    for nom, llind in llindars.items():
        u = np.where(m, np.log(np.maximum(g, 1e-30) / llind), np.nan)
        sel = m & (np.abs(u) < 0.45)
        if sel.sum() < 10000:
            out[nom] = {"estat": "sense mostra"}
            continue
        vores = np.linspace(-0.45, 0.45, nb + 1)
        ctr = 0.5 * (vores[:-1] + vores[1:])
        idx = np.clip(np.digitize(u[sel], vores) - 1, 0, nb - 1)
        v = hp[sel]
        o = np.argsort(idx); ii = idx[o]; vv = v[o]
        t = np.searchsorted(ii, np.arange(nb + 1))
        perfil = np.array([vv[t[a]:t[a + 1]].mean() if t[a + 1] - t[a] > 200 else np.nan
                           for a in range(nb)])
        err = np.array([vv[t[a]:t[a + 1]].std() / np.sqrt(max(t[a + 1] - t[a], 1))
                        if t[a + 1] - t[a] > 200 else np.nan for a in range(nb)])
        b = np.isfinite(perfil)
        # base local: els calaixos de |u| entre 0,25 i 0,45
        lluny = b & (np.abs(ctr) > 0.25)
        a_prop = b & (np.abs(ctr) < 0.06)
        if lluny.sum() < 10 or a_prop.sum() < 3:
            out[nom] = {"estat": "sense mostra"}
            continue
        base = float(np.nanmean(perfil[lluny]))
        vall = float(np.nanmin(perfil[a_prop]) - base)
        e = float(np.hypot(np.nanmean(err[a_prop]), np.nanstd(perfil[lluny])))
        out[nom] = {"llindar_adu_s": round(float(llind), 2),
                    "n_px": int(sel.sum()),
                    "vall_ln": round(vall, 8),
                    "vall_percent": round(100 * abs(np.expm1(vall)), 5),
                    "sigma": round(abs(vall) / e, 2) if e else None,
                    "veredicte": ("VALL" if e and abs(vall) / e > 3 else "sense vall (<3 sigma)")}
    return out

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dirs", type=Path, nargs="+")
    a = ap.parse_args()
    out = [mesura(d) for d in a.dirs]
    for o in out:
        print(f"{Path(o['dir']).parts[-2]:32s} vall {o['vall_percent']:7.4f} %  "
              f"({o['sigma']} σ)  {o['veredicte']}")
    print()
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
