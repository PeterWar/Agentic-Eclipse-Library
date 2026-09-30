"""Refà les previsualitzacions d'un compost ja fet, amb el perfil radial
INTERPOLAT i el balanç de blancs posat. Només llegeix el TIFF float del compost:
no torna a compondre res.

⛔ Per què existeix: el 24-08-2026 Pere va veure anells concèntrics **de colors**
a `*_normalitzat_radialment.png`. La causa era que aquella vista divideix per un
perfil radial calculat **per calaix i per canal**: 700 esglaons, un joc per
canal, i per això els anells sortien verds i blaus. Mesurat al llenç del pilot,
l'ondulació radial del resultat passa d'**1,62 % a 0,064 %** amb la interpolació.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import tifffile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def previsualitza(tif: Path, dst: Path, etiqueta: str, nb: int = 700) -> dict:
    im = tifffile.imread(tif)
    H, W = im.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(yy, xx) / C.R_SOL_PX

    # el pipeline no aplica balanç de blancs a propòsit: el lineal surt verd.
    an = (rr > 2.0) & (rr < 3.0) & np.isfinite(im[..., 1])
    wb = [float(np.nanmedian(im[..., 1][an]) / np.nanmedian(im[..., i][an]))
          for i in range(3)]
    neutre = im * np.array(wb, np.float32)

    dst.mkdir(parents=True, exist_ok=True)
    ref = float(np.nanpercentile(neutre[..., 1], 99.9))
    g = np.log1p(np.clip(neutre / ref, 0, 1) * 2000.0) / math.log1p(2000.0)
    cv2.imwrite(str(dst / f"{etiqueta}_lineal.png"), cv2.cvtColor(
        (np.clip(np.nan_to_num(g), 0, 1) * 65535).astype(np.uint16), cv2.COLOR_RGB2BGR))

    centres = (np.arange(nb) + 0.5) * float(rr.max()) / nb
    ib = np.clip((rr / rr.max() * nb).astype(np.int32), 0, nb - 1)
    vis = np.empty_like(neutre)
    ondulacio = {}
    for ch in range(3):
        v = neutre[..., ch]
        bo = np.isfinite(v)
        med = np.full(nb, np.nan)
        o = np.argsort(ib[bo]); ii = ib[bo][o]; vv = v[bo][o]
        talls = np.searchsorted(ii, np.arange(nb + 1))
        for a in range(nb):
            seg = vv[talls[a]:talls[a + 1]]
            if seg.size > 200:
                med[a] = np.median(seg)
        bons = np.isfinite(med)
        med = np.interp(np.arange(nb), np.flatnonzero(bons), med[bons])
        # ⛔ interpolació contínua en r, mai `med[ib]`
        vis[..., ch] = v / np.maximum(np.interp(rr, centres, med), 1e-30)
        ondulacio["RGB"[ch]] = float(np.nanstd(np.diff(med) / np.maximum(med[:-1], 1e-30)))
    lo, hi = np.nanpercentile(vis[..., 1], [1, 99.5])
    cv2.imwrite(str(dst / f"{etiqueta}_normalitzat_radialment.png"), cv2.cvtColor(
        (np.clip(np.nan_to_num((vis - lo) / max(hi - lo, 1e-9)), 0, 1) * 65535
         ).astype(np.uint16), cv2.COLOR_RGB2BGR))
    return {"font": str(tif), "balanc_de_blancs_rgb": wb, "calaixos": nb,
            "ondulacio_relativa_del_perfil": ondulacio,
            "nota": "perfil radial per interpolació contínua; el pintat NO és el producte"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tif", type=Path)
    ap.add_argument("etiqueta")
    ap.add_argument("--dst", type=Path,
                    default=C.DESK / "IA" / "output" / "pilot_vixen_claude_20260824")
    a = ap.parse_args()
    import json
    print(json.dumps(previsualitza(a.tif, a.dst, a.etiqueta), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
