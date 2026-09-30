"""On és el defecte, en (radi, azimut), i amb què coincideix.

La sospita que cal descartar o confirmar: la Lluna llisca 0,065 R☉ durant la
totalitat, o sigui que a cada azimut hi ha una corona de radis on la Lluna tapa
NOMÉS ALGUNS fotogrames. Allà el compost es fa amb els fotogrames on el píxel
just acaba de sortir del limbe, que és on la cua de la PSF lunar encara hi és.
Si el forat coincideix amb aquesta zona, la causa està trobada.
"""
from __future__ import annotations

import json
import os

import numpy as np

import nucli as N
from registra import a_la_resolucio

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.000), np.log(1.60), 200))


def fraccio_tapada(S, LL, radis, nth=NTH):
    """Fracció de fotogrames CORONALS que tenen la Lluna damunt de cada (r,θ)."""
    fr = [v for v in S["fotogrames"].values() if v.get("coronal")]
    RL = S["contactes"]["R_lluna_px"]; RS = LL["R_sol_px"]
    th = np.linspace(0.0, 2 * np.pi, nth, endpoint=False)
    yy = radis[:, None] * RS * np.sin(th)[None, :]
    xx = radis[:, None] * RS * np.cos(th)[None, :]
    n = np.zeros_like(xx)
    for v in fr:
        # el llenç està centrat al Sol: el vector Lluna−Sol ja és relatiu, però
        # el llenç va GIRAT a nord amunt i el vector del rebut és en píxels de
        # sensor. El gir és el mateix que aplica f2.
        import math
        a = math.radians(-LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)
        dx, dy = v["lluna_dx"], v["lluna_dy"]
        mx, my = ca * dx - sa * dy, sa * dx + ca * dy
        n += (np.hypot(xx - mx, yy - my) <= RL)
    return n / len(fr), len(fr)


if __name__ == "__main__":
    lum, pes, LL, S = N.carrega_nostre()
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0

    nom = "TSE2026_Trigaza_800mm.png"
    r = reg[nom]
    br, _, _, _ = N.carrega_brno(nom)
    bro = N.estructura(N.mostreja(br, r["cy"], r["cx"], r["R_sol_px"], RADIS,
                                  NTH, ang0=np.deg2rad(r["gir_deg"])))
    nos_cru = N.mostreja(lum, cy, cx, LL["R_sol_px"], RADIS, NTH)
    nos = N.estructura(a_la_resolucio(nos_cru, RADIS, r["R_sol_px"], NTH))
    pol_pes = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)

    tap, nfr = fraccio_tapada(S, LL, RADIS)
    print(f"{nfr} fotogrames coronals\n")

    print(f"{'R☉':>6s} {'corr':>7s} {'tapada mitj':>12s} {'tapada max':>11s}"
          f" {'pes rel':>9s} {'|dif| rms':>10s}")
    for i in range(0, len(RADIS), 6):
        c = N.corr_per_anell(nos[i:i+1], bro[i:i+1])[0]
        d = np.sqrt(np.nanmean((nos[i] - bro[i]) ** 2))
        pr = np.nanmedian(pol_pes[i]) / np.nanmedian(pol_pes[-1])
        print(f"{RADIS[i]:6.3f} {c:7.3f} {tap[i].mean()*100:11.1f}%"
              f" {tap[i].max()*100:10.1f}% {pr:9.2f} {d:10.3f}")

    # on comença i on acaba la zona d'ombra parcial
    parcial = (tap > 0.0) & (tap < 1.0)
    rs = RADIS[parcial.any(axis=1)]
    print(f"\nzona on la Lluna tapa NOMÉS ALGUNS fotogrames:"
          f" {rs.min():.4f} – {rs.max():.4f} R☉")
    tot = RADIS[(tap >= 1.0).any(axis=1)]
    print(f"zona on la Lluna els tapa TOTS (en algun azimut): fins a {tot.max():.4f} R☉")
    np.savez(os.path.join(N.AQUI, "mapes.npz"), radis=RADIS, nos=nos, bro=bro,
             tap=tap, pes=pol_pes)
