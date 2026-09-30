"""L'estructura fina, va enganxada al CEL o al SENSOR?

La muntura va derivar 27 px durant la totalitat. Si el que veiem a 1,8° (21 px)
fos del sensor, dues preses separades 20 px al sensor s'haurien de
descorrelacionar gairebé del tot; si va enganxat al cel, la correlació no ha de
dependre de la separació. Els quatre fotogrames de 0,5 s donen sis parelles amb
separacions d'1,6 a 21,7 px: és un experiment complet amb la dada que ja hi ha.
"""
from __future__ import annotations
import itertools, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402
from tancament_px import frame_al_llenc  # noqa: E402
from soroll import anells  # noqa: E402
from detall3 import banda  # noqa: E402

NTH = 2880
RADIS = np.exp(np.linspace(np.log(1.30), np.log(2.40), 36))
BANDES = [(13, 30), (31, 80), (81, 200), (201, 500)]

S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
LL = S["llenc"]; RS = LL["R_sol_px"]; RL = S["contactes"]["R_lluna_px"]
ped = comu.TRENS["VIXEN"]["pedestal_dn"]; fr = S["fotogrames"]
a = math.radians(LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)
th = np.linspace(0, 2 * np.pi, NTH, endpoint=False)

noms = [k for k, v in fr.items() if v.get("coronal") and abs(v["exp"] - 0.5) < 1e-6]
P = {}
for nom in noms:
    v = fr[nom]
    im, sm, n, rad = frame_al_llenc(nom, v, LL, ped, 0, 0)
    p, s = anells(im, sm, n, RS, RADIS, NTH)
    mx = ca * v["lluna_dx"] - sa * v["lluna_dy"]
    my = sa * v["lluna_dx"] + ca * v["lluna_dy"]
    xx = RADIS[:, None] * RS * np.cos(th)[None, :]
    yy = RADIS[:, None] * RS * np.sin(th)[None, :]
    dl = np.hypot(xx - mx, yy - my) - RL
    P[nom] = (p, np.isfinite(p) & (s < 0.01) & (p > 30) & (dl > 4))

print(f"{'parella':>13s} {'Δt':>6s} {'Δsensor':>8s} | "
      + " ".join(f"m{lo}-{hi:<3d}" for lo, hi in BANDES))
files = []
for x, y in itertools.combinations(noms, 2):
    m = P[x][1] & P[y][1]; ple = m.all(axis=1)
    if ple.sum() < 8:
        continue
    e0 = N.estructura_mask(P[x][0], m)[ple]; e1 = N.estructura_mask(P[y][0], m)[ple]
    ok = np.ones((int(ple.sum()), NTH), bool)
    cs = [np.nanmean(N.corr_per_anell_mask(banda(e0, lo, hi), banda(e1, lo, hi),
                                           ok)[0]) for lo, hi in BANDES]
    ds = math.hypot(fr[x]["sol_x"] - fr[y]["sol_x"], fr[y]["sol_y"] - fr[x]["sol_y"])
    dt = abs(fr[x]["t"] - fr[y]["t"])
    files.append((ds, dt, x, y, cs))
for ds, dt, x, y, cs in sorted(files):
    print(f"{x[4:8]}×{y[4:8]:>8s} {dt:6.1f} {ds:7.2f}px | "
          + " ".join(f"{c:7.3f}" for c in cs))
print("\nsi la correlació NO cau amb Δsensor, l'estructura va enganxada al CEL")
