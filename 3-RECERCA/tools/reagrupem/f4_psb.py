#!/usr/bin/env python3
"""FASE 4 · el projecte de Photoshop, amb totes les capes.

⛔ **La BASE és l'única capa amb sentit fotomètric.** La resta són maneres de
veure: cap no conserva la fotometria i cap no s'ha de mesurar.

⛔ **Norma del rectangle**: cap capa es retalla a cap circumferència. El que
limita cada capa és el seu **mapa de dada**, i prou.

⚠️ Les capes de detall van en **Superposar** i apagades menys la primera: són
per dosar-les d'una en una, que és com treballa Pere.
"""

from __future__ import annotations

import json, os, sys, time
import numpy as np
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
import comu  # noqa: E402

RS = 440.60


def u16(a):
    return np.clip(np.rint(np.asarray(a, np.float64)*65535.0), 0, 65535).astype(np.uint16)


def gris(a):
    return np.dstack([a, a, a])


def main():
    t0 = time.time()
    base = np.load(os.path.join(comu.F3, "BASE_rgb.npy"))
    m = np.load(os.path.join(comu.F3, "MASCARA.npy"))
    H, W = m.shape
    F3 = json.load(open(os.path.join(comu.REBUTS, "F3_filtres.json")))
    anc = F3["corba_to"]["valor_ancora"]

    # color neutralitzat: la corona a 1,05–1,15 R☉ es fa neutra.
    # ⚠️ Correcció de PRESENTACIÓ, no una calibració d'extinció: el camp abasta
    # X = 4,29 a 10,18 i el gradient cromàtic que hi queda és el deute obert.
    mult = {c: anc["G"]/anc[c] for c in ("R", "G", "B")}
    print("neutralització del color (escalars): " +
          "  ".join(f"{c} x{mult[c]:.4f}" for c in mult))
    C = {c: fits.getdata(os.path.join(comu.F2, f"COLOR_cel_restat_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy-H/2.0, xx-W/2.0); del yy, xx
    import f3_filtres as F
    neu = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(("R", "G", "B")):
        neu[..., i], _ = F.corba_to(C[c]*mult[c], rad, m)

    P = fits.getdata(os.path.join(comu.F2, "LDIC_pes_G.fits")).astype(np.float32)
    pes = np.where(m, P/np.nanmax(P), 0.0).astype(np.float32)
    cel = fits.getdata(os.path.join(comu.F2, "CEL_G.fits")).astype(np.float32)
    cel = np.where(m, (cel-np.nanmin(cel[m]))/max(float(np.nanmax(cel[m])-np.nanmin(cel[m])), 1e-9), 0.0).astype(np.float32)

    sim = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(("R", "G", "B")):
        Cs = fits.getdata(os.path.join(comu.F2, f"LDIC_cel_restat_{c}.fits")).astype(np.float32)
        sim[..., i], _ = F.corba_to(Cs*mult[c], rad, m)

    capes = [
        ("00 BASE corona · CALIBRADA", base, "NORMAL", True),
        ("01 BASE corona · color neutralitzat", neu, "NORMAL", True),
        ("02 DETALL passa-alt (mediana RGB)", gris(np.load(os.path.join(comu.F3, "DETALL_PASSA_ALT.npy"))), "OVERLAY", True),
        ("03 DETALL radial · plomalls", gris(np.load(os.path.join(comu.F3, "DETALL_RADIAL.npy"))), "OVERLAY", False),
        ("04 DETALL NRGF", gris(np.load(os.path.join(comu.F3, "DETALL_NRGF.npy"))), "OVERLAY", False),
        ("05 DETALL MGN", gris(np.load(os.path.join(comu.F3, "DETALL_MGN.npy"))), "OVERLAY", False),
        ("06 CONTRAST · cel tret per SIMETRIA (l'altre mètode)", sim, "NORMAL", False),
        ("07 diagnòstic · CEL restat", gris(cel), "NORMAL", False),
        ("08 diagnòstic · MAPA DE PES", gris(pes), "NORMAL", False),
    ]

    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    BM = {"NORMAL": BlendMode.NORMAL, "OVERLAY": BlendMode.OVERLAY}
    psd = new_psb(W, H)
    mask8 = (m.astype(np.uint8)*255)
    for nom, arr, bl, vis in capes:
        add_pixel_layer(psd, u16(arr), nom[:250], mask8=mask8, blend=BM[bl], visible=vis)
        print(f"  capa {nom}   [{time.time()-t0:.0f}s]", flush=True)
    # capes d'AJUST de veritat, a dalt de tot i amb valors d'identitat
    from ajust_utils import afegeix_ajust
    for nom, mena in (("AJUST · Exposició", "Exposició"),
                      ("AJUST · Nivells", "Nivells"),
                      ("AJUST · Corbes", "Corbes")):
        afegeix_ajust(psd, nom, mena, visible=True)
        print(f"  {nom}   [{time.time()-t0:.0f}s]", flush=True)
    finalize_lr16(psd)
    set_merged(psd, u16(neu))
    if getattr(psd, "_updated", False): psd._updated = False
    dst = comu.lliurable("Eclipsi_2026_VIXEN_R6III.psb")
    psd.save(dst)
    n = os.path.getsize(dst)
    print(f"\nPSB: {dst}\n     {n/1e9:.2f} GB · {W}x{H} · {len(capes)} capes  "
          f"({time.time()-t0:.0f}s)")
    json.dump({"fitxer": dst, "bytes": n, "llenc": [W, H],
               "capes": [c[0] for c in capes] + ["AJUST · Exposició", "AJUST · Nivells", "AJUST · Corbes"],
               "neutralitzacio_color": mult,
               "nota": "la BASE calibrada és l'única capa amb sentit fotomètric"},
              open(os.path.join(comu.REBUTS, "F4_psb.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
