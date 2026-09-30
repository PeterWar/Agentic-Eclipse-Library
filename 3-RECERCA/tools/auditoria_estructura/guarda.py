"""Quanta guarda necessita la màscara lunar? Ho diu la Lluna mateixa.

La Lluna llisca 28,5 px durant la totalitat, o sigui que un MATEIX píxel del
llenç és a distàncies molt diferents del limbe segons el fotograma. Si el
quocient fotograma/compost depèn d'aquesta distància, la proximitat del limbe
contamina, i la distància on el quocient es fa pla ÉS la guarda que cal.

⛔ La guarda actual és 2 px i el comentari del codi diu «PSF del limbe + error
d'ajust»: mai no s'havia mesurat.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import cv2
from astropy.io import fits

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402
from tancament_px import frame_al_llenc  # noqa: E402


if __name__ == "__main__":
    S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]; RL = S["contactes"]["R_lluna_px"]; RS = LL["R_sol_px"]
    G = fits.getdata(os.path.join(N.RUN, "2-ldic", "CORONA_G.fits")).astype(np.float32)
    cy, cx = int(LL["H"] // 2), int(LL["W"] // 2)
    ped = comu.TRENS["VIXEN"]["pedestal_dn"]
    fr = {k: v for k, v in S["fotogrames"].items() if v.get("coronal")}
    a = math.radians(LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)

    vores = np.arange(-6, 64, 4.0)
    acu = {k: [] for k in range(len(vores) - 1)}
    usats = 0
    for nom, v in sorted(fr.items(), key=lambda kv: kv[1]["t"]):
        if not (1e-3 <= v["exp"] <= 0.05):
            continue
        p = os.path.join(comu.TRENS["VIXEN"]["dir"], "totalitat", nom)
        if not os.path.exists(p):
            continue
        im, sm, n, rad = frame_al_llenc(nom, v, LL, ped, LL["W"], LL["H"])
        sub = G[cy - n:cy + n, cx - n:cx + n]
        # distància al limbe lunar D'AQUEST fotograma, en píxels del llenç
        yy, xx = np.mgrid[-n:n, -n:n].astype(np.float32)
        mx = ca * v["lluna_dx"] - sa * v["lluna_dy"]
        my = sa * v["lluna_dx"] + ca * v["lluna_dy"]
        dl = np.hypot(xx - mx, yy - my) - RL
        k = (np.isfinite(im) & (sm < 0.01) & (im > 60) & (sub > 0)
             & (rad > 1.02) & (rad < 1.45) & (dl > -6) & (dl < 60))
        if k.sum() < 5000:
            continue
        q = sub[k] / im[k]
        q = q / np.median(q[dl[k] > 40]) if (dl[k] > 40).sum() > 1000 else None
        if q is None:
            continue
        usats += 1
        idx = np.clip(np.digitize(dl[k], vores) - 1, 0, len(vores) - 2)
        for j in range(len(vores) - 1):
            m = idx == j
            if m.sum() > 200:
                acu[j].append(np.median(q[m]))

    print(f"{usats} fotogrames.  Quocient compost/fotograma, normalitzat a"
          f" > 40 px del limbe.\n")
    print(f"{'distància al limbe':>20s} {'n':>4s} {'quocient':>10s} {'excés':>9s}")
    for j in range(len(vores) - 1):
        if not acu[j]:
            continue
        v_ = np.median(acu[j])
        print(f"{vores[j]:8.0f}–{vores[j+1]:<5.0f} px {len(acu[j]):5d} "
              f"{v_:10.4f} {(v_-1)*100:+8.2f}%")
    print("\nsi el quocient puja prop del limbe, el FOTOGRAMA hi és massa FLUIX"
          "\n(la Lluna li ha xuclat llum) i la guarda ha d'arribar on es fa pla.")
