"""Hipòtesi: llum difosa de l'instrument. Model d'un sol paràmetre, i JUTGE RETINGUT.

`ours − α·(ours ⊛ K_σ)`, renormalitzat per anell. Si el desacord interior és un
halo, hi ha d'haver un (α, σ) que el redueixi molt.

⛔ AJUSTAR CONTRA BRNO I DESPRÉS DIR QUE BRNO HO CONFIRMA SERIA FER TRAMPA
(és el parany del `research/94`: amb prou llibertat l'acord s'imposa). Per això
(α, σ) es tria amb UNA sola imatge —la de 530 mm— i es jutja amb les altres
TRES, i a més es mira si fa mal on no hi havia problema (1,3–2,0 R☉).
"""
from __future__ import annotations
import itertools, json, os
import numpy as np
import cv2
from astropy.io import fits

import nucli as N
from registra import a_la_resolucio

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.04), np.log(2.00), 60))
AJUST = "TSE_2026_530mm_DHS.png"


if __name__ == "__main__":
    lum, pes, LL, S = N.carrega_nostre()
    RS = LL["R_sol_px"]
    cy, cx = int(LL["H"] // 2), int(LL["W"] // 2)
    n = int(3.2 * RS)
    sub = np.ascontiguousarray(lum[cy - n:cy + n, cx - n:cx + n], np.float32)
    wsub = np.ascontiguousarray(pes[cy - n:cy + n, cx - n:cx + n], np.float32)
    del lum, pes

    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    noms = sorted(reg); R_ref = min(reg[k]["R_sol_px"] for k in noms)
    B, MB = {}, {}
    for k in noms:
        br, _, _, _ = N.carrega_brno(k)
        B[k] = N.estructura_mask(
            N.mostreja(br, reg[k]["cy"], reg[k]["cx"], reg[k]["R_sol_px"],
                       RADIS, NTH, ang0=np.deg2rad(reg[k]["gir_deg"])),
            N.mascara_brno(k, reg[k], RADIS, NTH, 0.030))
        MB[k] = N.mascara_brno(k, reg[k], RADIS, NTH, 0.030)

    wpol = N.mostreja(wsub, n, n, RS, RADIS, NTH)
    ref = np.nanpercentile(wpol, 90, axis=1, keepdims=True)
    mn = np.isfinite(wpol) & (wpol > 0.05 * np.maximum(ref, 1e-12))

    # ⛔ El compost porta NaN al disc lunar i un desenfoc normal els escampa
    #    per tot arreu: cal convolució NORMALITZADA (dividir pel desenfoc de la
    #    validesa). Sense això surt NaN a σ ≥ 120 px i «no es pot provar».
    val = np.isfinite(sub).astype(np.float32)
    net = np.where(val > 0, np.nan_to_num(sub), 0.0).astype(np.float32)

    def prova(alfa, sig):
        if alfa == 0:
            y = sub
        else:
            num = cv2.GaussianBlur(net, (0, 0), sig, borderType=cv2.BORDER_REPLICATE)
            den = cv2.GaussianBlur(val, (0, 0), sig, borderType=cv2.BORDER_REPLICATE)
            h = np.where(den > 1e-4, num / np.maximum(den, 1e-9), 0.0)
            y = np.where(val > 0, (sub - alfa * h) / (1.0 - alfa), np.nan)
        y = np.ascontiguousarray(y, np.float32)
        p = a_la_resolucio(N.mostreja(y, n, n, RS, RADIS, NTH), RADIS, R_ref, NTH)
        e = N.estructura_mask(p, mn)
        out = {}
        for k in noms:
            m = mn & MB[k]
            out[k] = N.corr_per_anell_mask(e, B[k], m)[0]
        return out

    din = (RADIS >= 1.05) & (RADIS <= 1.18)
    fora = (RADIS >= 1.30) & (RADIS <= 2.00)
    base = prova(0.0, 1.0)
    print(f"{'α':>6s} {'σ px':>6s} | {'AJUST (530mm)':>16s} | "
          f"{'JUTGE (3 altres)':>18s} | {'fora 1,3-2,0':>13s}")
    print(f"{'':>6s} {'':>6s} | {'1,05-1,18':>16s} | {'1,05-1,18':>18s} |")
    b_in = np.nanmean(base[AJUST][din])
    b_ju = np.nanmean([np.nanmean(base[k][din]) for k in noms if k != AJUST])
    b_fo = np.nanmean([np.nanmean(base[k][fora]) for k in noms])
    print(f"{0:6.2f} {'—':>6s} | {b_in:16.4f} | {b_ju:18.4f} | {b_fo:13.4f}"
          f"   ← sense tocar res")
    for sig in (20.0, 50.0, 120.0, 300.0):
        for alfa in (0.05, 0.12, 0.25):
            r = prova(alfa, sig)
            i_ = np.nanmean(r[AJUST][din])
            j_ = np.nanmean([np.nanmean(r[k][din]) for k in noms if k != AJUST])
            f_ = np.nanmean([np.nanmean(r[k][fora]) for k in noms])
            print(f"{alfa:6.2f} {sig:6.0f} | {i_:16.4f} | {j_:18.4f} | {f_:13.4f}"
                  f"   {'':2s}{'⏭️' if j_ > b_ju + 0.02 and f_ > b_fo - 0.005 else ''}")
