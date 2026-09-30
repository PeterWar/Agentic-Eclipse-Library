"""On apunta cada fotograma de la Sony, i quins van moguts.

La pregunta que decideix el pla: la «quarantena» són fotogrames DOLENTS o són
l'ALTRE APUNTAMENT? Si són l'altre apuntament, treure'ls és llençar la meitat
de la dada per una cosa que la cadena ja sap fer (registra fotograma a
fotograma), i a més es perd el bloc de contacte de C2 sencer.

El centre es mesura pel LIMBE LUNAR (màxim de gradient), que és la norma del
projecte, i la moguda per l'el·lipticitat del mateix limbe.
"""
from __future__ import annotations
import glob, os
import numpy as np
import rawpy

DIR = os.path.expanduser("~/Desktop/Eclipse determinista/0-ENTRADES/SONY-A7RIIIA")


def centre_limbe(lum):
    """Centre i radi pel màxim de gradient radial; retorna també l'ovalitat."""
    llind = np.percentile(lum, 99.5)
    ys, xs = np.nonzero(lum >= llind)
    if ys.size < 50:
        return None
    cy, cx = float(ys.mean()), float(xs.mean())
    th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    for _ in range(10):
        rmax = min(cy, cx, lum.shape[0] - cy, lum.shape[1] - cx) - 2
        if rmax < 30:
            return None
        rs = np.arange(10.0, rmax, 1.0)
        rad = []
        for t in th:
            Y = np.clip((cy + rs * np.sin(t)).astype(int), 0, lum.shape[0] - 1)
            X = np.clip((cx + rs * np.cos(t)).astype(int), 0, lum.shape[1] - 1)
            v = lum[Y, X].astype(np.float64)
            kp = int(np.argmax(v))
            rad.append(rs[int(np.argmax(np.gradient(v)[:max(kp, 3)]))])
        rad = np.asarray(rad); md = np.median(rad)
        bo = np.abs(rad - md) < 0.08 * md
        if bo.sum() < 60:
            return None
        A = np.column_stack([np.cos(th[bo]), np.sin(th[bo]), np.ones(int(bo.sum()))])
        dx, dy, R = np.linalg.lstsq(A, rad[bo], rcond=None)[0]
        cx += dx; cy += dy
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            break
    # ovalitat: el limbe d'un fotograma mogut deixa de ser un cercle
    res = rad[bo] - R
    A2 = np.column_stack([np.cos(2 * th[bo]), np.sin(2 * th[bo])])
    c2 = np.linalg.lstsq(A2, res, rcond=None)[0]
    return cy, cx, R, float(np.hypot(*c2)), float(np.std(res))


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(DIR, "quarantena", "*.ARW"))) + \
            sorted(glob.glob(os.path.join(DIR, "totalitat", "*.ARW")))
    print(f"{'fitxer':>13s} {'carpeta':>10s} {'exp':>8s} | {'cx':>8s} {'cy':>8s} "
          f"{'R_px':>7s} | {'ovalitat':>8s} {'rms':>6s}")
    out = []
    for f in files:
        with rawpy.imread(f) as r:
            raw = r.raw_image_visible.astype(np.float32)
            exp = float(r.raw_image.shape[0])  # placeholder
        # verd binat 2×2, prou per al limbe
        g = 0.5 * (raw[0::2, 1::2] + raw[1::2, 0::2])
        c = centre_limbe(g)
        carp = os.path.basename(os.path.dirname(f))
        nom = os.path.basename(f)
        if c is None:
            print(f"{nom:>13s} {carp:>10s} {'':>8s} |   (limbe no mesurable)")
            continue
        cy, cx, R, ov, rms = c
        out.append((nom, carp, cx * 2, cy * 2, R * 2, ov * 2, rms * 2))
        print(f"{nom:>13s} {carp:>10s} {'':>8s} | {cx*2:8.1f} {cy*2:8.1f} "
              f"{R*2:7.1f} | {ov*2:8.2f} {rms*2:6.2f}")
    if out:
        import json
        a = np.array([[o[2], o[3]] for o in out])
        print(f"\nrecorregut del centre: x {np.ptp(a[:,0]):.0f} px, "
              f"y {np.ptp(a[:,1]):.0f} px")
        # ⏭️ La classificació que decideix quins fotogrames entren: l'ovalitat
        #    del limbe separa els nets dels que es van moure durant l'exposició.
        # El DSC06990 fa 0,52 d'ovalitat i esta TRENCAT: l'ajust del limbe li
        # dona R = 163 px en lloc de 304. Un radi que no es el radi vol dir que
        # el que s'ha ajustat no es el limbe.
        ov = np.array([o[5] for o in out]); RR = np.array([o[4] for o in out])
        net = (ov < 2.0) & (np.abs(RR - np.median(RR)) < 6.0)
        d = {"fotogrames": {o[0]: {"carpeta": o[1], "cx": o[2], "cy": o[3],
                                   "R_px": o[4], "ovalitat_px": o[5],
                                   "rms_px": o[6], "net": bool(net[i])}
                            for i, o in enumerate(out)},
             "recorregut_px": [float(np.ptp(a[:, 0])), float(np.ptp(a[:, 1]))],
             "criteri_net": "ovalitat < 2,0 px i |R - mediana(R)| < 6 px"}
        with open("apuntaments.json", "w") as fh:
            json.dump(d, fh, indent=1)
        print(f"nets {int(net.sum())} de {len(out)} · moguts: "
              + ", ".join(o[0] for i, o in enumerate(out) if not net[i]))
