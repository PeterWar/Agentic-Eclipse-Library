"""És soroll nostre? Dos fotogrames INDEPENDENTS, entre si, al mateix anell.

Si dos fotogrames de la mateixa exposició presos a 60 s de distància es posen
d'acord al 0,95 a 1,07 R☉, la nostra dada allà és bona i el desacord amb Brno
és SISTEMÀTIC. Si es posen d'acord al 0,5, allà només hi ha soroll i no hi ha
cap defecte a curar: hi ha una limitació.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
from astropy.io import fits

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402
from tancament_px import frame_al_llenc  # noqa: E402

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.03), np.log(1.60), 40))
PARELLES = [("572A2969.CR3", "572A2987.CR3"),    # 8 ms, t=22 i t=84
            ("572A2975.CR3", "572A2993.CR3"),    # 16,7 ms, t=28 i t=90
            ("572A2970.CR3", "572A2988.CR3")]    # 33 ms, t=23 i t=85


def anells(im, sm, n, RS, radis, nth=NTH):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    rr = radis[:, None] * RS
    yy = n + rr * np.sin(th)[None, :]; xx = n + rr * np.cos(th)[None, :]
    y0 = yy.astype(int); x0 = xx.astype(int)
    ok = (y0 >= 0) & (x0 >= 0) & (y0 < 2 * n - 1) & (x0 < 2 * n - 1)
    y0 = np.clip(y0, 0, 2 * n - 2); x0 = np.clip(x0, 0, 2 * n - 2)
    v = im[y0, x0]; s = sm[y0, x0]
    return np.where(ok, v, np.nan), np.where(ok, s, 1.0)


if __name__ == "__main__":
    S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]; RS = LL["R_sol_px"]; RL = S["contactes"]["R_lluna_px"]
    ped = comu.TRENS["VIXEN"]["pedestal_dn"]
    fr = S["fotogrames"]
    a = math.radians(LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)

    res = {}
    for na, nb in PARELLES:
        V = []
        for nom in (na, nb):
            v = fr[nom]
            im, sm, n, rad = frame_al_llenc(nom, v, LL, ped, LL["W"], LL["H"])
            p, s = anells(im, sm, n, RS, RADIS)
            mx = ca * v["lluna_dx"] - sa * v["lluna_dy"]
            my = sa * v["lluna_dx"] + ca * v["lluna_dy"]
            th = np.linspace(0, 2 * np.pi, NTH, endpoint=False)
            xx = RADIS[:, None] * RS * np.cos(th)[None, :]
            yy = RADIS[:, None] * RS * np.sin(th)[None, :]
            dl = np.hypot(xx - mx, yy - my) - RL
            V.append((p, np.isfinite(p) & (s < 0.01) & (p > 40) & (dl > 4)))
        m = V[0][1] & V[1][1]
        e0 = N.estructura_mask(V[0][0], m); e1 = N.estructura_mask(V[1][0], m)
        c, nn = N.corr_per_anell_mask(e0, e1, m, minim=200)
        res[(na, nb)] = (c, nn)
        print(f"{na} × {nb}   exp {fr[na]['exp']:g} s")

    print(f"\n{'R☉':>6s} " + "  ".join(f"{fr[a]['exp']:>8.4g}s" for a, b in PARELLES)
          + "     arc")
    for i in range(0, len(RADIS), 2):
        fila = "  ".join(f"{res[p][0][i]:9.3f}" for p in PARELLES)
        arc = np.max([res[p][1][i] for p in PARELLES]) * 360 // NTH
        print(f"{RADIS[i]:6.3f} {fila}  {arc:6.0f}°")
