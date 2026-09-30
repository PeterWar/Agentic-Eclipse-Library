#!/usr/bin/env python3
"""PROVA D'ASPECTE — la dada calibrada del pilot amb l'ordre d'operacions del 93.

⛔ **No és una mesura ni un lliurable.** És la prova de si la dada bona pot fer
l'aspecte de la maqueta de Pere. Cap fitxer del projecte s'hi toca: només llegeix.

Què fa, i per què (`research/108`):

1. retalla el llenç comú a l'enquadrament de la maqueta (3:2, ±7,55 × ±5,03 R☉);
2. **iguala els dos trens PER CANAL** —guany i pedestal per mínims quadrats a
   l'anell de solapament—, que és la regla de `research/93` §B. ⛔ L'escalar
   únic de luminància que fa servir `munta_photoshop.py --igualar-trens` deixa
   un graó de color del 19 al 35 % a la costura;
3. cus la costura amb una rampa des de la vora de la petjada Vixen, **amb els
   forats interiors plens abans** (la trampa canònica del `distanceTransform`);
4. **neutralitza** a 1,8–2,2 R☉: la dispersió Thomson és acromàtica, o sigui
   que la corona hi ha de sortir neutra (`research/93` §«el que sí que és
   calibratge»);
5. modela el **cel** amb una quàdrica 2-D **per canal** ajustada al camp
   llunyà, i el lliura com a component que es pot dosar —no com una constant—;
6. mapa de to **logarítmic de pendent declarat**, per omissió el **0,17 de
   nivell per dècada de B/B☉ mesurat a la maqueta**, ancorat a l'anell
   1,05–1,15 R☉. ⛔ `estira_log` fa servir percentils [0,5, 99,7] i això dona
   0,50/dècada: crema 1,67 dècades i deixa el limbe a 0,998 fins a 1,45 R☉.

Ús:

    python3 prova_aspecte.py --sortida ~/Desktop/prova.png [--calid] [--detall 55]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from scipy.ndimage import binary_fill_holes, distance_transform_edt

Image.MAX_IMAGE_PIXELS = None

ARREL = Path("/Users/USUARI/Downloads/Eclipse 2026/output/pilot_vixen_fable_20260825_lliurament")
SONY = Path("/Users/USUARI/Downloads/Eclipse 2026/output/pilot_vixen_claude_20260824/sony_llenc_comu_coh")
RSOL_PX, CX, CY = 440.603031451995, 5225.0, 6439.0     # llenç comú, `comu.py`


def retall(mig_costat_rsol: float) -> tuple[slice, slice]:
    hw = int(round(mig_costat_rsol * RSOL_PX))
    hh = int(round(hw * 2 / 3))                         # 3:2, com la maqueta
    return (slice(int(CY) - hh, int(CY) + hh), slice(int(CX) - hw, int(CX) + hw))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sortida", required=True, type=Path)
    p.add_argument("--camp", type=float, default=7.55, help="mig costat en R☉")
    p.add_argument("--pendent", type=float, default=0.175, help="nivell per dècada de B/B☉")
    p.add_argument("--cel", type=float, default=0.94, help="fracció del model de cel que es treu")
    p.add_argument("--ancora", type=float, default=0.68, help="nivell a 1,05-1,15 R☉")
    p.add_argument("--negre", type=float, default=0.045, help="terra de nivell")
    p.add_argument("--detall", type=float, default=55.0, help="guany del detall de la fase 3")
    p.add_argument("--calid", action="store_true",
                   help="tebior de la maqueta: NOMÉS estètica, decisió de Pere sota D1")
    a = p.parse_args()

    sl = retall(a.camp)
    V = np.asarray(tifffile.memmap(str(ARREL / "dos_trens" / "VIXEN_al_llenc_BBsol_float32.tif"),
                                   mode="r")[sl], np.float32)
    S = np.asarray(np.load(SONY / "SONY_LLENC_BBsol.npy", mmap_mode="r")[sl], np.float32)
    cob = np.asarray(np.load(SONY / "SONY_COBERTURA.npy", mmap_mode="r")[sl][..., 1])
    h, w = V.shape[:2]
    yy = np.arange(h, dtype=np.float32)[:, None] + sl[0].start - CY
    xx = np.arange(w, dtype=np.float32)[None, :] + sl[1].start - CX
    rr = (np.hypot(xx, yy) / np.float32(RSOL_PX)).astype(np.float32)

    hv = np.isfinite(V).all(2) & (V[..., 1] > 0)
    hs = np.isfinite(S).all(2) & (S[..., 1] > 0) & (cob >= 3)
    rebut: dict = {"camp_rsol": a.camp, "retall_px": [w, h],
                   "cobertura": {"vixen": float(hv.mean()), "sony": float(hs.mean()),
                                 "unio": float((hv | hs).mean())}}

    # 2 · igualació entre trens PER CANAL a l'anell de solapament
    anell = hv & hs & (rr > 1.5) & (rr < 2.8)
    gain = np.zeros(3)
    off = np.zeros(3)
    for i in range(3):
        x = S[..., i][anell].astype(np.float64)
        A = np.stack([x, np.ones_like(x)], 1)
        (gain[i], off[i]), *_ = np.linalg.lstsq(A, V[..., i][anell].astype(np.float64), rcond=None)
    S = np.where(hs[..., None], S * gain.astype(np.float32) + off.astype(np.float32), np.nan).astype(np.float32)
    rebut["igualacio_per_canal"] = {"guany": gain.tolist(), "pedestal": off.tolist()}

    # 3 · costura: rampa des de la vora de la petjada Vixen, forats plens abans
    u = np.clip(distance_transform_edt(binary_fill_holes(hv)).astype(np.float32) / 200.0, 0, 1)
    pv = np.where(hv, u * u * (3 - 2 * u), 0.0).astype(np.float32)
    num = pv[..., None] * np.nan_to_num(V) + ((1 - pv) * hs)[..., None] * np.nan_to_num(S)
    den = pv + (1 - pv) * hs
    I = np.where(den[..., None] > 0, num / np.maximum(den[..., None], 1e-9), np.nan).astype(np.float32)
    ok = np.isfinite(I).all(2) & (I[..., 1] > 0)
    del num, den, V, S

    # 4 · neutralització: Thomson és acromàtica
    neu = ok & (rr > 1.8) & (rr < 2.2)
    wb = np.array([np.median(I[..., 1][neu]) / np.median(I[..., i][neu]) for i in range(3)], np.float32)
    I *= wb
    rebut["neutralitzacio_rgb"] = wb.tolist()

    # 5 · el cel: quàdrica 2-D PER CANAL al camp llunyà
    Yb, Xb = np.broadcast_arrays((np.arange(h, dtype=np.float32)[:, None] - h / 2) / h,
                                 (np.arange(w, dtype=np.float32)[None, :] - w / 2) / w)
    T = [np.ones_like(Xb), Xb, Yb, Xb * Xb, Xb * Yb, Yb * Yb]
    fit = ok & (rr > 0.8 * a.camp)
    CEL = np.zeros_like(I)
    for i in range(3):
        A = np.stack([t[fit] for t in T], 1).astype(np.float64)
        c, *_ = np.linalg.lstsq(A, I[..., i][fit].astype(np.float64), rcond=None)
        CEL[..., i] = sum(ci * ti for ci, ti in zip(c, T))
    rebut["cel_al_centre_rgb"] = [float(CEL[h // 2, w // 2, i]) for i in range(3)]

    # 6 · mapa de to de pendent declarat
    D = np.nan_to_num(np.asarray(np.load(ARREL / "dos_trens_filtrats" / "DETALL_ln.npy",
                                         mmap_mode="r")[sl], np.float32)) if a.detall else 0.0
    k = a.pendent / np.log(10.0)
    K = np.maximum(I - a.cel * CEL, 1e-13)
    an = ok & (rr > 1.05) & (rr < 1.15)
    b = a.ancora - k * np.log(float(np.median(K[..., 1][an])))
    out = k * (np.log(K) + (a.detall * D[..., None] if a.detall else 0.0)) + b
    if a.calid:
        out *= np.array([1.045, 1.0, 0.90], np.float32)
    out = np.clip(np.where(ok[..., None], np.maximum(out, a.negre), 0.0), 0, 1)
    rebut["mapa_de_to"] = {"pendent_per_decada": a.pendent, "ancora_1.1_rsol": a.ancora,
                           "negre": a.negre, "cel_tret": a.cel, "detall": a.detall,
                           "calid_NOMES_estetica": bool(a.calid)}

    a.sortida.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(a.sortida)
    a.sortida.with_suffix(".json").write_text(json.dumps(rebut, indent=1, ensure_ascii=False))
    print(json.dumps(rebut, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
