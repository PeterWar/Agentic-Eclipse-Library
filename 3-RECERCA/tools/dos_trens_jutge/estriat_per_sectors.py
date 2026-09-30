"""Tasca 4, tercera peca: la familia fina, es CORONA o es la GRAELLA DEL LLENC?

Fins aqui: la familia de lambda 6-10 px surt als TRES canals (no es la quincunx
del verd), surt als DOS trens (mes forta a la Vixen) i **al mateix angle del
llenc**, 163-175°. Pel discriminador de `estriat_dos_trens.py`, mateixa
direccio als dos = CEL. Pero hi ha un confusor que aquell discriminador no
cobreix: **els dos trens comparteixen la MATEIXA graella de llenc**, o sigui
que un artefacte de remostreig tambe sortiria al mateix angle als dos.

La prova que els separa: **l'estructura fina de la corona es RADIAL**, o sigui
que la seva direccio ha de GIRAR amb l'azimut. Un artefacte de graella es queda
clavat al mateix angle a tot arreu.

Es mesura per sectors de 45° i es compara la direccio del pic amb la direccio
radial del sector.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from astropy.io import fits

import nucli as N
from estriat import normalitza_radi, espectre, pics

R0, R1 = 1.40, 2.60
LAM = (6.0, 10.0)
NSEC = 8


def dang(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


if __name__ == "__main__":
    TRENS = sys.argv[1:] or ["VIXEN", "SONYTOT"]
    for tren in TRENS:
        d = N.darrer_run(tren)
        S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
        LL = S["llenc"]; RS = LL["R_sol_px"]
        a = fits.getdata(os.path.join(d, "2-ldic", "CORONA_G.fits")).astype(np.float32)
        w = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
        H, W = a.shape
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        rad = np.hypot(yy - H / 2.0, xx - W / 2.0)
        th = (np.degrees(np.arctan2(yy - H / 2.0, xx - W / 2.0)) % 360.0)
        del yy, xx
        base = (w > 0.05 * np.nanpercentile(w[w > 0], 90)) & (rad >= R0 * RS) \
            & (rad <= R1 * RS) & np.isfinite(a)
        z = normalitza_radi(a.astype(np.float64), base, rad)
        print(f"\n{tren}: {os.path.basename(d)}   (anell {R0}-{R1} R☉, "
              f"sectors de {360//NSEC}°)")
        print(f"{'sector':>10s} {'radial':>8s} {'pic':>8s} {'exces':>7s} "
              f"{'|pic−radial|':>13s} {'|pic−169°|':>11s}")
        dr, df = [], []
        for s in range(NSEC):
            a0, a1 = s * 360.0 / NSEC, (s + 1) * 360.0 / NSEC
            k = base & (th >= a0) & (th < a1)
            if k.sum() < 60000:
                print(f"{a0:5.0f}-{a1:<4.0f}   (poca dada: {k.sum():,})"); continue
            ys, xs = np.nonzero(k)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            zz = np.where(k, z, 0.0)[y0:y1, x0:x1]
            kk = k[y0:y1, x0:x1]
            M, lams, angs = pics(espectre(zz, kk), LL["escala_arcsec_px"])
            Mn = M / np.nanmedian(M, axis=1, keepdims=True)
            bl = (lams >= LAM[0]) & (lams <= LAM[1])
            sub = np.nan_to_num(Mn[bl])
            i, j = np.unravel_index(int(np.argmax(sub)), sub.shape)
            radial = ((a0 + a1) / 2.0) % 180.0
            dr.append(dang(angs[j], radial)); df.append(dang(angs[j], 169.5))
            print(f"{a0:5.0f}-{a1:<4.0f} {radial:8.1f} {angs[j]:8.1f} "
                  f"{sub[i,j]:7.2f} {dr[-1]:13.1f} {df[-1]:11.1f}")
        if dr:
            print(f"{'MITJANA':>10s} {'':>8s} {'':>8s} {'':>7s} {np.mean(dr):13.1f} "
                  f"{np.mean(df):11.1f}")
        del a, w, rad, th, z, base
    print("\n  Si |pic−radial| és petit i |pic−169°| és gran → l'estructura GIRA amb\n"
          "  l'azimut: és CORONA. Si passa el contrari, està clavada al llenç:\n"
          "  és la GRAELLA. (Un valor mitjà de 45° als dos vol dir cap dels dos.)")
