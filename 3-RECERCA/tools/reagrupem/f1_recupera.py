#!/usr/bin/env python3
"""FASE 1 · pas 3 — recuperar els fotogrames PROFUNDS per correlació.

Els de 2 s i 10 s són els més profunds i havien quedat fora: amb la corona
interior cremada, la vora que el detector de limbe troba és la de la
SATURACIÓ i no la de la Lluna (R sortia 489,8 px en lloc de 452,4).

La cura no és afinar el detector de limbe —allà no hi ha limbe— sinó
registrar-los **contra el compost que ja tenim**, per correlació de fase en
una corona **exterior** on ni ells ni el compost estan saturats. El punt de
partida és el model de punteria interpolat.
"""

from __future__ import annotations

import glob, json, math, os, sys, time
import numpy as np, cv2, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

RS = 440.60
R_IN, R_OUT = 2.2, 5.5      # R☉: banda de correlació


def main():
    t0 = time.time()
    S = json.load(open(os.path.join(comu.REBUTS, "F1_sol_llenc.json")))
    LL = S["llenc"]; W, H = LL["vixen"]["W"], LL["vixen"]["H"]
    CXc, CYc = W/2.0, H/2.0
    PA = math.radians(-LL["pa_north_deg_origen"]); ca, sa = math.cos(PA), math.sin(PA)
    C = fits.getdata(os.path.join(comu.F2, "LDIC_cel_restat_G.fits")).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy-CYc, xx-CXc); del yy, xx
    banda = (rad > R_IN*RS) & (rad < R_OUT*RS) & np.isfinite(C) & (C > 0)
    ref = np.where(banda, np.log10(np.maximum(C, 1e-3)), 0.0).astype(np.float32)
    ref -= ref[banda].mean(); ref *= banda

    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    FLAT = fits.getdata(os.path.join(comu.F0, "flat", "FLAT_RADIAL_R6III.fits")).astype(np.float32)
    darks = {round(float(p.split("_E")[1].rstrip("s.fits")), 8): p
             for p in glob.glob(os.path.join(comu.F0, "masters_dark", "*.fits"))}
    ys, xs = np.where(mc == 1); oy, ox = int(ys.min()), int(xs.min())

    cand = [n for n, v in S["fotogrames"].items()
            if not v["coronal"] and v["exp"] >= 0.4]
    print(f"candidats profunds sense limbe: {len(cand)}  "
          + " ".join(sorted(f"{S['fotogrames'][n]['exp']:g}s" for n in cand)), flush=True)
    win = cv2.createHanningWindow((W, H), cv2.CV_32F)
    canvis = {}
    for n in sorted(cand):
        v = S["fotogrames"][n]; e = v["exp"]
        dk = fits.getdata(darks[min(darks, key=lambda q: abs(q-e))]).astype(np.float32)
        with rawpy.imread(os.path.join(comu.VIXEN, n)) as r:
            raw = r.raw_image.astype(np.float32)
        cal = ((raw - dk)/FLAT)[oy::2, ox::2]/e
        sat = (raw[oy::2, ox::2] - 512.0) > 0.85*(16382.0-512.0)
        sx, sy = v["sol_x"], v["sol_y"]
        XX, YY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        dX = XX-CXc; dY = YY-CYc
        mx = (((ca*dX+sa*dY)+sx-ox)*0.5).astype(np.float32)
        my = (((-sa*dX+ca*dY)+sy-oy)*0.5).astype(np.float32)
        im = cv2.remap(cal, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        bad = cv2.remap(sat.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=1.0)
        ok = banda & (bad < 0.05) & (im > 0)
        if ok.sum() < 200000:
            print(f"  {n}: massa poca banda neta ({int(ok.sum())})"); continue
        cur = np.where(ok, np.log10(np.maximum(im, 1e-3)), 0.0).astype(np.float32)
        cur -= cur[ok].mean(); cur *= ok
        (dx, dy), resp = cv2.phaseCorrelate(ref.astype(np.float64)*win,
                                            cur.astype(np.float64)*win)
        # cur(x) = ref(x - d)  =>  el Sol del fotograma és a sol - d girat enrere
        rx = ca*dx - sa*dy; ry = sa*dx + ca*dy      # rotació inversa cap al sensor
        canvis[n] = {"dx_llenc": dx, "dy_llenc": dy, "resposta": float(resp),
                     "sol_x": sx + rx, "sol_y": sy + ry}
        print(f"  {n} {e:>6g}s  desplaçament ({dx:+7.2f},{dy:+7.2f}) px  "
              f"resposta {resp:.3f}  banda neta {100*ok.sum()/banda.sum():5.1f} %",
              flush=True)
    # aplica
    n_ok = 0
    for n, c in canvis.items():
        if c["resposta"] < 0.02 or abs(c["dx_llenc"]) > 40 or abs(c["dy_llenc"]) > 40:
            print(f"  ⛔ {n} refusat (resposta {c['resposta']:.3f})"); continue
        S["fotogrames"][n].update(sol_x=c["sol_x"], sol_y=c["sol_y"],
                                  coronal=True, font="correlacio_amb_el_compost")
        n_ok += 1
    S["n_coronals"] = sum(1 for v in S["fotogrames"].values() if v["coronal"])
    S["recuperats_per_correlacio"] = {n: canvis[n] for n in canvis}
    json.dump(S, open(os.path.join(comu.REBUTS, "F1_sol_llenc.json"), "w"), indent=1)
    print(f"\nrecuperats {n_ok} · coronals ara {S['n_coronals']}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
