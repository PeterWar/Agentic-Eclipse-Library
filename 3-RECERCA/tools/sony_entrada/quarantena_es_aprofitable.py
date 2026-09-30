"""Els cinc fotogrames exclosos de la Sony: quant estan moguts, de veritat?

El criteri d'exclusio d'avui es l'**ovalitat del limbe lunar** (`apuntaments.py`).
⛔ Aquest criteri **no es pot aplicar als fotogrames de 8 s**: alli la corona
interior esta saturada i el que l'ajust troba no es el limbe, es la frontera de
saturacio. El fotograma de 8 s BO (DSC06987) ni tan sols hi surt, i el DSC06990
hi surt amb R = 163 px en lloc de 304. O sigui que dos dels cinc exclosos ho han
estat per una mesura que alli no vol dir res.

Aqui es mesura la **moguda de veritat**, amb un instrument que funciona a
qualsevol exposicio: l'**autocorrelacio de l'estructura fina**. Un fotograma
mogut te l'autocorrelacio eixamplada EN LA DIRECCIO de la moguda i intacta
perpendicularment. Es compara cada exclos amb un fotograma BO de la MATEIXA
exposicio i a la MATEIXA regio.

⛔ PRIMER INTENT, DESCARTAT: mesurar l'autocorrelacio de cada fotograma per
separat. No serveix — la corona **ja es anisotropa** (els plomalls son radials) i
la regio seleccionada canvia de fotograma a fotograma, o sigui que el fotograma
BO de 1/8 s sortia MES anisotrop (4,78) que l'exclos (4,20). Es la mateixa
malaltia de sempre: comparar dues coses que no miren el mateix.

⏭️ EL BO: **ajustar la moguda**. S'alinea l'exclos amb el seu company bo per
correlacio de fase i despres es busca **quin desenfoc direccional aplicat al BO
el fa igual a l'EXCLOS**. La resposta surt en pixels i en graus, i es
interpretable directament: «aquest fotograma es el bo escombrat 6 px a 87°».
Amb un escalar lliure, perque la transparencia va canviar entre els dos.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import cv2
import rawpy

ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")
ENT = os.path.join(ARREL, "0-ENTRADES", "SONY-A7RIIIA")
RUNS = os.path.join(ARREL, "1-RUNS")
AQUI = os.path.dirname(os.path.abspath(__file__))

# exclos -> company BO de la mateixa exposicio
PARELLES = [("DSC06988.ARW", "DSC06985.ARW", "1 s"),
            ("DSC06991.ARW", "DSC06985.ARW", "1 s"),
            ("DSC06989.ARW", "DSC06986.ARW", "1/8 s"),
            ("DSC06990.ARW", "DSC06987.ARW", "8 s"),
            ("DSC06993.ARW", "DSC06987.ARW", "8 s")]


def ruta(n):
    for c in ("quarantena", "totalitat"):
        p = os.path.join(ENT, c, n)
        if os.path.exists(p):
            return p
    raise SystemExit(f"no trobo {n}")


def pla_g(run, f0, comu, n, dk):
    with rawpy.imread(ruta(n)) as r:
        raw = r.raw_image.astype(np.float32)
        mc = comu.mapa_colors(r)
        g = comu.geometria(r)
    e = float(subprocess.run(["exiftool", "-s3", "-ExposureTime", ruta(n)],
                             capture_output=True, text=True).stdout.strip()
              .replace("1/", "") or 1)
    ex = EXP[n]
    if ex not in dk:
        dk[ex] = f0.dark_de(run, ex)
    ys, xs = np.nonzero(mc == 1); oy, ox = int(ys.min()), int(xs.min())
    sub = (raw[oy::2, ox::2] - dk[ex][oy::2, ox::2])
    sat = raw[oy::2, ox::2] >= 0.85 * 16383.0
    return sub, sat, g


EXP = {"DSC06985.ARW": 1.0, "DSC06986.ARW": 0.125, "DSC06987.ARW": 8.0,
       "DSC06988.ARW": 1.0, "DSC06989.ARW": 0.125, "DSC06990.ARW": 8.0,
       "DSC06991.ARW": 1.0, "DSC06993.ARW": 8.0}


def ajusta_moguda(G, X, m):
    """Quin desenfoc direccional sobre G el fa igual a X? (px i graus)"""
    G = G.astype(np.float32); X = X.astype(np.float32)
    best = (1e30, 0.0, 0.0, 0.0)
    for th in np.arange(0, 180, 10.0):
        for sig in np.arange(0.0, 6.01, 0.25):
            if sig == 0:
                Gb = G
            else:
                k = int(6 * sig) | 1
                x = np.arange(k) - k // 2
                ker = np.exp(-0.5 * (x / sig) ** 2); ker /= ker.sum()
                # nucli 2-D d'una linia orientada theta
                K = np.zeros((k, k), np.float32)
                for i, v in zip(x, ker):
                    yy = int(round(k // 2 + i * np.sin(np.radians(th))))
                    xx = int(round(k // 2 + i * np.cos(np.radians(th))))
                    if 0 <= yy < k and 0 <= xx < k:
                        K[yy, xx] += v
                K /= K.sum()
                Gb = cv2.filter2D(G, -1, K)
            a = float(np.sum(Gb[m] * X[m]) / max(np.sum(Gb[m] ** 2), 1e-20))
            r = float(np.mean((a * Gb[m] - X[m]) ** 2))
            if r < best[0]:
                best = (r, sig, th, a)
    r0 = float(np.mean(((np.sum(G[m] * X[m]) / max(np.sum(G[m]**2), 1e-20)) * G[m]
                        - X[m]) ** 2))
    return best[1], best[2], best[3], 100 * (1 - best[0] / max(r0, 1e-30))


def amplada_autocorr(z, m):
    """Amplada de l'autocorrelacio de l'estructura fina, per direccions."""
    b = cv2.GaussianBlur(z, (0, 0), 1.0) - cv2.GaussianBlur(z, (0, 0), 4.0)
    b = np.where(m, b, 0.0).astype(np.float32)
    b -= b[m].mean()
    b = np.where(m, b, 0.0)
    n = 512
    ys, xs = np.nonzero(m)
    cy, cx = int(np.median(ys)), int(np.median(xs))
    y0, x0 = max(cy - n // 2, 0), max(cx - n // 2, 0)
    t = b[y0:y0 + n, x0:x0 + n]
    if t.shape != (n, n):
        return None
    t = t * np.hanning(n)[:, None] * np.hanning(n)[None, :]
    F = np.fft.fft2(t)
    ac = np.fft.fftshift(np.real(np.fft.ifft2(F * np.conj(F))))
    ac /= ac.max()
    # amplada a mitja alcada per direccions
    c = n // 2
    ang = np.linspace(0, np.pi, 72, endpoint=False)
    w = []
    for a in ang:
        rr = np.arange(0, 25, 0.25)
        yy = c + rr * np.sin(a); xx = c + rr * np.cos(a)
        v = cv2.remap(ac.astype(np.float32), xx.astype(np.float32)[None, :],
                      yy.astype(np.float32)[None, :], cv2.INTER_LINEAR)[0]
        k = np.nonzero(v < 0.5)[0]
        w.append(rr[k[0]] if len(k) else np.nan)
    w = np.array(w)
    i = int(np.nanargmax(w)); j = int(np.nanargmin(w))
    return float(w[i]), float(w[j]), float(np.degrees(ang[i]))


if __name__ == "__main__":
    import re as _re
    _p = _re.compile(r"^(\d{3,})_")
    _c = [x for x in os.listdir(RUNS)
          if _p.sub("", x).startswith("SONYTOT_CIENCIA_")
          and not x.endswith(("_FALLIT", "_AVORTAT"))]
    d = sorted(_c, key=lambda x: (int(_p.match(x).group(1)) if _p.match(x) else -1, x))[-1]
    d = os.path.join(RUNS, d)
    sys.path.insert(0, os.path.join(d, "codi"))
    import comu, f0
    run = comu.Run.obre(d)
    print(f"calibratge del run {os.path.basename(d)}\n")
    dk = {}
    print(f"{'exclòs':>15s} {'contra':>15s} {'exp':>6s} {'moguda':>8s} "
          f"{'direcció':>9s} {'transp.':>8s} {'residu':>8s}")
    CACHE = {}
    for exclos, bo, et in PARELLES:
        for n in (bo, exclos):
            if n not in CACHE:
                CACHE[n] = pla_g(run, f0, comu, n, dk)
        Gs, Gsat, g = CACHE[bo]
        Xs, Xsat, _ = CACHE[exclos]
        # alinea per correlacio de fase (la moguda inclou un desplacament)
        win = np.hanning(Gs.shape[0])[:, None] * np.hanning(Gs.shape[1])[None, :]
        (dx, dy), _ = cv2.phaseCorrelate(np.nan_to_num(Gs) * win,
                                         np.nan_to_num(Xs) * win)
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        Gw = cv2.warpAffine(Gs, M, (Gs.shape[1], Gs.shape[0]))
        Gsw = cv2.warpAffine(Gsat.astype(np.float32), M,
                             (Gs.shape[1], Gs.shape[0])) > 0.01
        m = (~Xsat) & (~Gsw) & (Xs > np.percentile(Xs, 80)) & (Gw > 0)
        m = cv2.erode(m.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
        if m.sum() < 50000:
            print(f"{exclos:>15s} {bo:>15s} {et:>6s}   (regió comuna massa petita: "
                  f"{m.sum():,})")
            continue
        # ⚠️ finestra de treball: aixo es una MESURA interna, no una vista.
        #    Es retalla nomes per poder fer 450 convolucions en un temps
        #    raonable, i es centra al gruix de la mascara.
        ys, xs = np.nonzero(m)
        cy_, cx_ = int(np.median(ys)), int(np.median(xs))
        H2 = 750
        y0 = max(cy_ - H2, 0); x0 = max(cx_ - H2, 0)
        sl = (slice(y0, y0 + 2 * H2), slice(x0, x0 + 2 * H2))
        if m[sl].sum() < 30000:
            print(f"{exclos:>15s} {bo:>15s} {et:>6s}   (finestra sense prou dada)")
            continue
        sig, th, a, gua = ajusta_moguda(Gw[sl], Xs[sl], m[sl])
        esc = 3.2020 * 2      # px de subpla CFA -> arcsec
        print(f"{exclos:>15s} {bo:>15s} {et:>6s} {sig:6.2f}px {th:8.1f}° "
              f"{a:8.3f} {gua:7.1f}%   ({sig*esc:.0f}\u2033, desplaçament "
              f"{np.hypot(dx,dy):.1f} px)")
    print("\n  moguda = quant s'ha d'escombrar el fotograma BO perquè s'assembli\n"
          "  a l'EXCLÒS · residu = quant baixa l'error en fer-ho (si és ~0, no hi\n"
          "  ha moguda direccional i el que passa és una altra cosa)")
