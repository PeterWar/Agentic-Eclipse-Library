"""Tasca 2: el blau. Es CALIBRATGE o es la CAMERA?

Els dos trens discrepen un −8,5 % de B/G sobre la corona (espai de camera, amb
el balanc de dia posat) i **coincideixen al 0,08 % sobre el cel**. Dues
explicacions possibles:

  CALIBRATGE  → un error de flat, de pedestal o de linealitat. Aleshores el
                color ha de dependre de **quina exposicio** el mesura, perque
                cada exposicio cau a un tros diferent de la corba del sensor i
                a un tros diferent del camp.
  CAMERA      → les dues respostes espectrals son diferents i el balanc de dia
                nomes iguala un espectre de llum de dia. Aleshores **totes** les
                exposicions d'un mateix cos han de dir el MATEIX color, i el que
                canvia es d'un cos a l'altre.

Aixo les separa sense cap suposicio nova: es mesura el color de la corona
fotograma a fotograma, a un anell on el cel encara no mana (1,3-1,7 R☉:
cel/corona val −0,005 a la Vixen i −0,017 a la Sony).

⛔ **LA TRAMPA, i va picar DUES vegades.** Primer, mesurant cada fotograma als
seus propis pixels valids: el tall per baix es un tall en DN i el canal B es el
mes feble, o sigui que a les exposicions curtes nomes hi sobreviuen els pixels
amb mes blau i el B/G puja sol (dispersio del 127 % DINS d'un mateix tren, que
no es una mesura sino la seleccio). I despres, agafant la INTERSECCIO dels
pixels valids: la interseccio hereta el tall del fotograma mes curt i torna a
triar els blaus (B/G 1,05, mes blau que el cel).

⏭️ **La cura de debo: cap tall per baix.** La mascara es NOMES geometria i
no-saturacio, i s'agafa la **mitjana**, no la mediana, perque una mitjana sobre
300.000 pixels de soroll simetric es insesgada encara que cada pixel sigui
soroll. Un tall per baix mai no ho pot ser.

⛔ **I la tercera trampa: la INTERSECCIO era en pixels de SENSOR.** Amb el salt
de muntura de 749 px, el mateix pixel del sensor mira **un tros de corona
diferent** a cada apuntament, o sigui que la interseccio comparava dues zones
del cel i sortia un factor 1,6 de brillantor i un B/G de 0,69 contra 0,43 que
NO son de la camera: son de la corona. La mascara ja esta ancorada al CEL
(radi des del Sol de cada fotograma); el que sobrava era la interseccio. Amb el
tall per baix fora, cada fotograma pot mesurar el seu anell SENCER, que es el
mateix tros de cel a tots.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import rawpy
from astropy.io import fits

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/"
                   "eclipse_determinista")
import comu   # noqa: E402
import f0     # noqa: E402

import nucli as N   # noqa: E402

R0, R1 = 1.30, 1.70    # es pot canviar amb --anell r0 r1
COBERTURA_MIN = 0.95      # de l'anell SENSE saturar (l'unic tall que hi ha)
# ⛔ res d'interseccio: l'anell ja esta ancorat al Sol de CADA fotograma


def valid_frame(run, flat, nom, v, dk):
    """Mascara de validesa i dada calibrada d'un fotograma, a l'anell."""
    with rawpy.imread(comu.ruta_llum(run.tren, nom)) as r:
        raw = r.raw_image.astype(np.float32)
        mc = comu.mapa_colors(r)
        g = comu.geometria(r)
    e = float(v["exp"])
    if e not in dk:
        dk[e] = f0.dark_de(run, e)
    wb = comu.balanc_dia(comu.entrades(run.tren, "totalitat")[0])
    esc = run.cfg["escala_arcsec_px"]
    RS = run.cfg["rsol_arcsec"] / esc                 # R☉ en px de SENSOR
    sat = run.cfg["saturacio_dn"]
    cal = ((raw - dk[e]) / flat / e).astype(np.float32)
    yy, xx = np.mgrid[0:g.alt, 0:g.ample].astype(np.float32)
    rad = np.hypot(yy - float(v["sol_y"]), xx - float(v["sol_x"])); del yy, xx
    vis = np.zeros((g.alt, g.ample), bool); vis[g.visible] = True
    anell = vis & (rad > R0 * RS) & (rad < R1 * RS)   # R0/R1: globals del modul
    #  ⛔ cap tall per baix: nomes saturacio. Un tall en DN tria per color.
    bo = anell & (raw < 0.85 * sat)
    return cal, anell, bo, mc, g, wb


def color_amb_mascara(cal, mc, g, wb, msk):
    out, err = {}, {}
    for i in range(4):
        k = msk & (mc == i)
        if k.sum() < 2000:
            return None
        v = cal[k].astype(np.float64)
        out[comu.nom_canal(i, g.desc)] = float(v.mean()) * wb[comu.IDX_CANAL[i]]
        err[comu.nom_canal(i, g.desc)] = float(v.std() / np.sqrt(len(v))) * wb[comu.IDX_CANAL[i]]
    G = 0.5 * (out["G1"] + out["G2"])
    eG = 0.5 * np.hypot(err["G1"], err["G2"])
    rg, bg = out["R"] / G, out["B"] / G
    e_rg = abs(rg) * np.hypot(err["R"] / abs(out["R"]), eG / abs(G))
    e_bg = abs(bg) * np.hypot(err["B"] / abs(out["B"]), eG / abs(G))
    return rg, bg, G, e_rg, e_bg


if __name__ == "__main__":
    av = sys.argv[1:]
    if "--anell" in av:
        i = av.index("--anell")
        globals()["R0"], globals()["R1"] = float(av[i + 1]), float(av[i + 2])
        R0, R1 = globals()["R0"], globals()["R1"]
        av = av[:i] + av[i + 3:]
    TRENS = av or ["VIXEN", "SONYTOT"]
    print(f"### ANELL {R0}-{R1} R☉ ###")
    RES = {}
    for tren in TRENS:
        d = N.darrer_run(tren)
        run = comu.Run.obre(d)
        S = json.load(open(os.path.join(d, "4-rebuts", "F1.3_registre.json")))["fotogrames"]
        flat = fits.getdata(os.path.join(d, "0-calibracio", "FLAT_RADIAL.fits")).astype(np.float32)
        dk = {}
        print(f"\n{tren}: {os.path.basename(d)}")
        print(f"  {'fotograma':>16s} {'exp (s)':>9s} {'R/G':>15s} {'B/G':>15s} "
              f"{'G a 1,3-1,7':>13s} {'px':>9s}")
        # ---- passada 1: quins fotogrames cobreixen prou anell, i la interseccio
        DAT, INT, anell0 = {}, None, None
        for nom in sorted(S):
            cal, anell, bo, mc, g, wb = valid_frame(run, flat, nom, S[nom], dk)
            cob = bo.sum() / max(anell.sum(), 1)
            if cob < COBERTURA_MIN:
                print(f"  {nom:>16s} {S[nom]['exp']:9g}   (fora: {100*(1-cob):.0f} % "
                      f"de l'anell SATURAT)")
                continue
            DAT[nom] = (cal, bo, mc, g, wb, float(S[nom]["exp"]))
            anell0 = anell
        if not DAT:
            continue
        print(f"  → {len(DAT)} fotogrames · anell de {anell0.sum():,} px ancorat al "
              f"SOL de cada fotograma: tots miren el MATEIX tros de cel")
        files = []
        for nom, (cal, bo, mc, g, wb, e) in sorted(DAT.items(), key=lambda t: t[1][5]):
            c = color_amb_mascara(cal, mc, g, wb, bo)
            if c is None:
                continue
            files.append((e, nom, c))
            print(f"  {nom:>16s} {e:9g} {c[0]:8.4f}±{c[3]:.4f} {c[1]:8.4f}±{c[4]:.4f} "
                  f"{c[2]:13.1f} {bo.sum():9,d}")
        if not files:
            continue
        rg = np.array([f[2][0] for f in files]); bg = np.array([f[2][1] for f in files])
        RES[tren] = (rg, bg, files)
        print(f"  {'MEDIANA':>16s} {'':>9s} {np.median(rg):8.4f} {np.median(bg):8.4f}")
        gg = np.array([f[2][2] for f in files])
        print(f"  {'dispersio':>16s} {'':>9s} {100*(rg.max()/rg.min()-1):7.2f}% "
              f"{100*(bg.max()/bg.min()-1):7.2f}%   (entre exposicions, DINS del tren)")
        print(f"  {'nivell G':>16s} {'':>9s} dispersio {100*(gg.max()/gg.min()-1):6.2f} % "
              f"entre exposicions  ⏭️ tancament HDR de la DADA CRUA")

    if len(RES) == 2:
        a, b = TRENS[0], TRENS[1]
        ra, ba, _ = RES[a]; rb, bb, _ = RES[b]
        print("\n" + "=" * 74)
        print(f"{'':>22s} {'DINS de ' + a:>14s} {'DINS de ' + b:>14s} {'ENTRE trens':>14s}")
        print(f"{'dispersio de R/G':>22s} {100*(ra.max()/ra.min()-1):13.2f}% "
              f"{100*(rb.max()/rb.min()-1):13.2f}% "
              f"{100*(np.median(rb)/np.median(ra)-1):+13.2f}%")
        print(f"{'dispersio de B/G':>22s} {100*(ba.max()/ba.min()-1):13.2f}% "
              f"{100*(bb.max()/bb.min()-1):13.2f}% "
              f"{100*(np.median(bb)/np.median(ba)-1):+13.2f}%")
        print("\nSi la dispersio DINS de cada tren es petita i la de ENTRE trens es "
              "gran,\nel calibratge queda exculpat i el que discrepa son les dues "
              "CAMERES.")
