"""El bony de θ≈133°, r≈1,07 R☉: hi és a CADA fotograma o el fabrica el compost?

Un tret de la corona hi ha de ser a tots els fotogrames on el píxel no està
tapat ni saturat, i sempre al mateix lloc respecte del SOL. Si només hi és a
uns quants, o si es mou, no és corona.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import rawpy

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402

TH0, R0 = 133.5, 1.070          # el bony
CTRL = [(40.0, 1.070), (220.0, 1.070), (300.0, 1.070)]   # controls al mateix radi


def del_llenc_al_sensor(th_deg, r, v, LL):
    """Del (θ, r) del llenç a píxels del sensor d'aquest fotograma."""
    pa = math.radians(LL["pa_north_deg"])          # invers del gir del llenç
    ca, sa = math.cos(pa), math.sin(pa)
    X = r * LL["R_sol_px"] * math.cos(math.radians(th_deg))
    Y = r * LL["R_sol_px"] * math.sin(math.radians(th_deg))
    return v["sol_x"] + ca * X - sa * Y, v["sol_y"] + sa * X + ca * Y


def mitjana_disc(raw, mc, x, y, rad=9.0):
    y0, y1 = int(y - rad) & ~1, int(y + rad) | 1
    x0, x1 = int(x - rad) & ~1, int(x + rad) | 1
    sub = raw[y0:y1 + 1, x0:x1 + 1]; cm = mc[y0:y1 + 1, x0:x1 + 1]
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    k = (np.hypot(xx - x, yy - y) <= rad) & ((cm == 1) | (cm == 3))
    if k.sum() < 20:
        return np.nan, 0.0
    v = sub[k]
    return float(np.median(v)), float((v >= 16000).mean())


if __name__ == "__main__":
    S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]; RL = S["contactes"]["R_lluna_px"]
    cfg = comu.TRENS["VIXEN"]; ped = cfg["pedestal_dn"]
    fr = {k: v for k, v in S["fotogrames"].items() if v.get("coronal")}
    d = os.path.join(cfg["dir"], "totalitat")

    tri = sorted(fr.items(), key=lambda kv: kv[1]["t"])
    print(f"{'fotograma':>14s} {'t':>6s} {'exp':>9s}  {'bony':>9s} "
          f"{'c40°':>9s} {'c220°':>9s} {'c300°':>9s}   bony/mediana")
    vals = []
    for nom, v in tri:
        if v["exp"] < 5e-4 or v["exp"] > 0.5:
            continue                       # els que no veuen bé aquest radi
        p = os.path.join(d, nom)
        if not os.path.exists(p):
            continue
        with rawpy.imread(p) as r:
            raw = r.raw_image.astype(np.float32)
            mc = comu.mapa_colors(r)
        xs = [del_llenc_al_sensor(TH0, R0, v, LL)] + \
             [del_llenc_al_sensor(t, rr, v, LL) for t, rr in CTRL]
        m = []
        for (x, y) in xs:
            val, sat = mitjana_disc(raw, mc, x, y)
            m.append((val - ped) if np.isfinite(val) else np.nan)
        # tapat per la Lluna?
        mlx = v["sol_x"] + v["lluna_dx"]; mly = v["sol_y"] + v["lluna_dy"]
        tapat = math.hypot(xs[0][0] - mlx, xs[0][1] - mly) < RL + 2
        ctrl = np.nanmedian(m[1:])
        vals.append(m[0] / ctrl if ctrl and np.isfinite(ctrl) else np.nan)
        print(f"{nom:>14s} {v['t']:6.1f} {v['exp']:9.5f}  {m[0]:9.1f} "
              f"{m[1]:9.1f} {m[2]:9.1f} {m[3]:9.1f}   "
              f"{vals[-1]:6.2f}{'  LLUNA' if tapat else ''}")
    vals = np.array(vals, float)
    print(f"\nbony / controls:  mediana {np.nanmedian(vals):.2f}   "
          f"min {np.nanmin(vals):.2f}   max {np.nanmax(vals):.2f}   "
          f"n={np.isfinite(vals).sum()}")
