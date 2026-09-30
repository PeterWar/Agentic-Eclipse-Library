"""La pregunta que ho decideix: la nostra DADA té estructura fina real?

Dos fotogrames independents (60 s de diferència), banda a banda. Si a 1,8° es
posen d'acord, la dada hi és i el que la perd és el pipeline —defecte—. Si no
s'hi posen, allà només hi ha soroll i cel: és una LIMITACIÓ, i llavors tot el
que les nostres capes de detall hi pinten és inventat.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402
from tancament_px import frame_al_llenc  # noqa: E402
from soroll import anells  # noqa: E402
from detall3 import banda  # noqa: E402

NTH = 2880
RADIS = np.exp(np.linspace(np.log(1.15), np.log(2.40), 40))
BANDES = [(1, 4), (5, 12), (13, 30), (31, 80), (81, 200), (201, 500)]
PARELLES = [("572A2970.CR3", "572A2988.CR3"),      # 33 ms
            ("572A2971.CR3", "572A2989.CR3"),      # 125 ms
            ("572A2972.CR3", "572A2990.CR3")]      # 500 ms

S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
LL = S["llenc"]; RS = LL["R_sol_px"]; RL = S["contactes"]["R_lluna_px"]
ped = comu.TRENS["VIXEN"]["pedestal_dn"]; fr = S["fotogrames"]
a = math.radians(LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)
th = np.linspace(0, 2 * np.pi, NTH, endpoint=False)

print(f"{'banda m':>10s} {'tret de':>8s} {'px@1,5R☉':>9s} | "
      + " ".join(f"{fr[p[0]]['exp']*1000:>7.0f} ms" for p in PARELLES))
res = {}
for na, nb in PARELLES:
    V = []
    for nom in (na, nb):
        v = fr[nom]
        im, sm, n, rad = frame_al_llenc(nom, v, LL, ped, 0, 0)
        p, s = anells(im, sm, n, RS, RADIS, NTH)
        mx = ca * v["lluna_dx"] - sa * v["lluna_dy"]
        my = sa * v["lluna_dx"] + ca * v["lluna_dy"]
        xx = RADIS[:, None] * RS * np.cos(th)[None, :]
        yy = RADIS[:, None] * RS * np.sin(th)[None, :]
        dl = np.hypot(xx - mx, yy - my) - RL
        V.append((p, np.isfinite(p) & (s < 0.01) & (p > 30) & (dl > 4)))
    m = V[0][1] & V[1][1]
    ple = m.all(axis=1)
    res[(na, nb)] = (N.estructura_mask(V[0][0], m)[ple],
                     N.estructura_mask(V[1][0], m)[ple], ple)

for lo, hi in BANDES:
    fila = []
    for p in PARELLES:
        e0, e1, ple = res[p]
        ok = np.ones((int(ple.sum()), NTH), bool)
        fila.append(np.nanmean(N.corr_per_anell_mask(
            banda(e0, lo, hi), banda(e1, lo, hi), ok)[0]))
    px = 1.5 * RS * 2 * np.pi / hi
    print(f"{lo:4d}–{hi:<5d} {360/hi:6.1f}° {px:9.0f} | "
          + " ".join(f"{v:10.3f}" for v in fila))
print("\n(px@1,5R☉ és al NOSTRE llenç: R☉ = 440,6 px)")
