"""Tires polars per MIRAR-HO: nosaltres, Brno i el residu, al mateix marc."""
from __future__ import annotations
import json, os
import numpy as np
from PIL import Image
import nucli as N
from registra import a_la_resolucio

NTH = 1800
NR = 620
R0, R1 = 1.00, 2.20
BRNO = "TSE2026_Trigaza_800mm.png"


def a_png(a, m, lo=-2.5, hi=2.5):
    v = np.clip((a - lo) / (hi - lo), 0, 1)
    rgb = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
    rgb[~m] = np.array([120, 40, 140], np.uint8)   # lila = sense dada
    return rgb


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(R0), np.log(R1), NR))
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))[BRNO]
    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0

    br, _, _, _ = N.carrega_brno(BRNO)
    pb = N.mostreja(br, reg["cy"], reg["cx"], reg["R_sol_px"], radis, NTH,
                    ang0=np.deg2rad(reg["gir_deg"]))
    mb = N.mascara_brno(BRNO, reg, radis, NTH)
    pn = a_la_resolucio(N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, NTH),
                        radis, reg["R_sol_px"], NTH)
    wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], radis, NTH)
    ref = np.nanpercentile(wp, 90, axis=1, keepdims=True)
    mn = np.isfinite(pn) & (wp > 0.05 * np.maximum(ref, 1e-12))

    en = N.estructura_mask(pn, mn); eb = N.estructura_mask(pb, mb)
    mk = mn & mb
    res = np.where(mk, en - eb, np.nan)

    files = [("NOSALTRES", a_png(en, mn)), ("BRNO 800mm", a_png(eb, mb)),
             ("RESIDU N−B", a_png(np.nan_to_num(res), mk, -3, 3))]
    alt = NR + 16
    tela = np.full((alt * 3, NTH, 3), 30, np.uint8)
    for k, (nom, im) in enumerate(files):
        tela[k * alt:k * alt + NR] = im
    # marques de radi
    for rr, gruix in ((1.0338, 2), (1.10, 1), (1.20, 1), (1.50, 1), (2.00, 1)):
        j = int(np.argmin(np.abs(radis - rr)))
        for k in range(3):
            tela[k * alt + j, ::30] = np.array([255, 90, 90], np.uint8)
    Image.fromarray(tela).save(os.path.join(N.AQUI, "tires.png"))
    print("tires.png:  files = nosaltres / Brno / residu")
    print(f"  horitzontal θ 0→360° ({NTH} px), vertical log r {R0}→{R1} R☉ ({NR} px)")
    print(f"  lila = sense dada. ratlles vermelles a 1,0338 / 1,10 / 1,20 / 1,50 / 2,00 R☉")
    for rr in (1.0338, 1.10, 1.20, 1.50, 2.0):
        print(f"    r={rr:.4f} → fila {int(np.argmin(np.abs(radis-rr)))}")
