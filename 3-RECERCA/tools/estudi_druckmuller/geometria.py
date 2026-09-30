"""Detecta marc, centre lunar i radi als composts de Brno del 12-08-2026.

Cap llindar absolut: el limbe es mesura pel MAXIM DE GRADIENT radial, que es
la norma del projecte (el llindar falla perque la Lluna porta earthshine a
tres dels quatre composts i es mes clara que el cel de les cantonades).
"""
import json
import os
import numpy as np
from PIL import Image

CARPETA = "/Users/USUARI/Desktop/Eclipse 2026/Drukmuller fotos finals"


def srgb_a_lineal(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def carrega(nom):
    im = Image.open(os.path.join(CARPETA, nom)).convert("RGB")
    return np.asarray(im, dtype=np.float64) / 255.0


def retalla_marc(rgb):
    """El marc gris i el peu de foto son uniformes per fila/columna."""
    lum = rgb.mean(axis=2)
    sf = lum.std(axis=1)
    sc = lum.std(axis=0)
    llind_f = 0.15 * sf.max()
    llind_c = 0.15 * sc.max()
    f = np.where(sf > llind_f)[0]
    c = np.where(sc > llind_c)[0]
    return int(f[0]), int(f[-1]) + 1, int(c[0]), int(c[-1]) + 1


def centre_i_radi(lum):
    """Centre pel centroide de la corona interior; radi pel maxim de gradient."""
    llind = np.percentile(lum, 99.7)
    m = lum >= llind
    ys, xs = np.nonzero(m)
    w = lum[m]
    cy, cx = float((ys * w).sum() / w.sum()), float((xs * w).sum() / w.sum())

    ny, nx = lum.shape
    for volta in range(10):
        rmax = min(cy, cx, ny - cy, nx - cx)
        rs = np.arange(5.0, rmax, 0.5)
        th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
        radis = []
        for t in th:
            yy = cy + rs * np.sin(t)
            xx = cx + rs * np.cos(t)
            v = lum[np.clip(yy.astype(int), 0, ny - 1), np.clip(xx.astype(int), 0, nx - 1)]
            # el limbe es la pujada mes forta ABANS del maxim de brillantor:
            # la corona interior fa cim just al limbe, i aixo no te escala.
            kpic = int(np.argmax(v))
            g = np.gradient(v)
            k = int(np.argmax(g[:max(kpic, 3)]))
            radis.append(rs[k])
        radis = np.asarray(radis)
        med = np.median(radis)
        bo = np.abs(radis - med) < 0.06 * med
        # reajusta el centre amb els punts bons (cercle robust)
        tb, rb = th[bo], radis[bo]
        A = np.column_stack([np.cos(tb), np.sin(tb), np.ones(tb.size)])
        # r ~ R + dx*cos + dy*sin
        sol, *_ = np.linalg.lstsq(A, rb, rcond=None)
        dx, dy, R = sol
        cx += dx
        cy += dy
        if volta >= 2 and abs(dx) < 0.02 and abs(dy) < 0.02 and bo.mean() > 0.9:
            break
    return cy, cx, float(R), float(bo.mean())


if __name__ == "__main__":
    out = {}
    for nom in sorted(os.listdir(CARPETA)):
        if not nom.lower().endswith(".png"):
            continue
        rgb = carrega(nom)
        f0, f1, c0, c1 = retalla_marc(rgb)
        sub = rgb[f0:f1, c0:c1]
        lum = sub.mean(axis=2)
        cy, cx, R, frac = centre_i_radi(lum)
        out[nom] = dict(marc=[f0, f1, c0, c1], mida=[sub.shape[0], sub.shape[1]],
                        cy=cy, cx=cx, R_lluna_px=R, frac_bons=frac)
        print(f"{nom:32s} contingut {sub.shape[1]}x{sub.shape[0]}  "
              f"centre ({cx:7.2f},{cy:7.2f})  R_lluna {R:6.2f} px  bons {frac*100:.0f}%")
    with open(os.path.join(os.path.dirname(__file__), "geometria.json"), "w") as fh:
        json.dump(out, fh, indent=2)
