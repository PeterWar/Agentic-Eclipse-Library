"""Zoom a la corona interior, amb el PES i la COBERTURA LUNAR al costat.

Quatre files al mateix marc perquè es puguin llegir juntes: què tenim, què
tenen ells, quant pes hi ha i quants fotogrames hi tapa la Lluna. Si un
artefacte nostre segueix la cobertura, la causa és la màscara.
"""
from __future__ import annotations
import json, math, os
import numpy as np
from PIL import Image
import nucli as N
from registra import a_la_resolucio
from mapes import fraccio_tapada

NTH = 1800
NR = 420
R0, R1 = 1.00, 1.40
BRNO = "TSE2026_Trigaza_800mm.png"


def gris(a, m, lo, hi, color=(120, 40, 140)):
    v = np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1)
    rgb = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
    rgb[~m] = np.array(color, np.uint8)
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
    tap, nfr = fraccio_tapada(S, LL, radis, NTH)

    en = N.estructura_mask(pn, mn); eb = N.estructura_mask(pb, mb)
    tot = np.ones_like(mn, bool)
    files = [gris(en, mn, -2.5, 2.5), gris(eb, mb, -2.5, 2.5),
             gris(np.log10(np.maximum(wp, 1e-6)), tot, -2.0, 1.6),
             gris(tap, tot, 0.0, 1.0, (200, 60, 60))]
    sep = 10
    tela = np.full(((NR + sep) * 4, NTH, 3), 25, np.uint8)
    for k, im in enumerate(files):
        tela[k * (NR + sep):k * (NR + sep) + NR] = im
    for rr in (1.0338, 1.0658, 1.10, 1.15, 1.20, 1.30):
        j = int(np.argmin(np.abs(radis - rr)))
        for k in range(4):
            tela[k * (NR + sep) + j, ::40] = np.array([255, 80, 80], np.uint8)
    Image.fromarray(tela).save(os.path.join(N.AQUI, "tires_interior.png"))
    print("tires_interior.png · files: NOSALTRES / BRNO / log10(pes) / fracció tapada")
    print(f"  θ 0→360° a l'horitzontal, r {R0}→{R1} R☉ a la vertical (log)")
    for rr in (1.0338, 1.0658, 1.10, 1.15, 1.20, 1.30):
        print(f"    r={rr:.4f} → fila {int(np.argmin(np.abs(radis-rr))):3d}")
    print(f"  θ: 0°=x+ (dreta del llenç, nord amunt);"
          f" 90°=avall; 180°=esquerra; 270°=amunt")
