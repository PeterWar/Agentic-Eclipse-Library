#!/usr/bin/env python3
"""Mesura directa del vinyetatge amb els SALTS de muntura de dins la totalitat.

La mateixa corona, a dues posicions del sensor separades per centenars de
pixels. Alineant al CEL (vora lunar) i dividint, el quocient val
V(x+d)/V(x) x (factor global): es una mesura del vinyetatge sense cap model
d'atmosfera ni d'enfosquiment del limbe.

Nomes lectura.
"""
import os, sys, json
import numpy as np
import rawpy
from scipy import ndimage

SONY = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
VIXEN = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered"


def plane(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
    return v[0::2, 1::2] - ped          # pla G1, mig de resolucio


def fit_moon(a, Rmoon):
    """Centre del disc lunar: la vora es el salt brutal corona/fosc."""
    # el nucli lunar es la zona fosca envoltada de corona brillant
    sm = ndimage.uniform_filter(a, 25)
    lvl = np.percentile(sm, 99.9)
    bright = sm > 0.05 * lvl
    lab, n = ndimage.label(bright)
    if n == 0:
        return None
    sizes = ndimage.sum(bright, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    ys, xs = np.nonzero(lab == k)
    cy, cx = ys.mean(), xs.mean()
    H, W = a.shape
    th = np.linspace(-np.pi, np.pi, 360, endpoint=False)
    rs = np.arange(0.75 * Rmoon, 1.30 * Rmoon, 0.5)
    for _ in range(6):
        yq = cy + rs[None, :] * np.sin(th)[:, None]
        xq = cx + rs[None, :] * np.cos(th)[:, None]
        if yq.min() < 1 or xq.min() < 1 or yq.max() > H - 2 or xq.max() > W - 2:
            return None
        prof = ndimage.map_coordinates(sm, [yq.ravel(), xq.ravel()], order=1).reshape(yq.shape)
        # la vora: primer creuament ascendent de la meitat del maxim del perfil
        gt, gr = [], []
        for i in range(len(th)):
            p = prof[i]
            lv = 0.5 * (p.min() + p.max())
            idx = np.nonzero(p > lv)[0]
            if len(idx) == 0 or idx[0] == 0:
                continue
            j = idx[0]
            f = (lv - p[j - 1]) / max(p[j] - p[j - 1], 1e-9)
            gt.append(th[i]); gr.append(rs[j - 1] + f * (rs[1] - rs[0]))
        if len(gt) < 100:
            return None
        gt = np.array(gt); gr = np.array(gr)
        A = np.stack([np.ones_like(gt), np.cos(gt), np.sin(gt)], 1)
        sol, *_ = np.linalg.lstsq(A, gr, rcond=None)
        cx += sol[1]; cy += sol[2]
        if abs(sol[1]) < 0.02 and abs(sol[2]) < 0.02:
            break
    return cy, cx, float(sol[0]), float(np.std(gr - A @ sol))


def analyse(pa, pb, ped, Rmoon, label, exp_a, exp_b):
    a = plane(pa, ped); b = plane(pb, ped)
    fa = fit_moon(a, Rmoon); fb = fit_moon(b, Rmoon)
    if fa is None or fb is None:
        print(f"  {label}: no s'ha pogut ajustar la vora lunar"); return None
    dy = fa[0] - fb[0]; dx = fa[1] - fb[1]
    # desplaca B fins a la posicio de cel de A
    bs = ndimage.shift(b, (dy, dx), order=1, mode="nearest")
    sa = ndimage.uniform_filter(a, 41)
    sb = ndimage.uniform_filter(bs, 41)
    H, W = a.shape
    yy, xx = np.mgrid[:H, :W]
    rr = np.hypot(yy - fa[0], xx - fa[1])
    # anell d'analisi: corona de gradient suau, lluny del limbe i sense saturar
    ok = (rr > 1.6 * Rmoon) & (rr < 4.5 * Rmoon) & (sa > 30) & (sb > 30) & (a < 15000) & (bs < 15000)
    if ok.sum() < 20000:
        print(f"  {label}: pocs pixels utils ({ok.sum()})"); return None
    ratio = np.full_like(a, np.nan)
    ratio[ok] = sa[ok] / sb[ok]
    med = np.nanmedian(ratio)
    rn = ratio / med
    # ajust d'un pla + quadratic radial sobre el quocient normalitzat
    ys, xs = np.nonzero(ok)
    vals = rn[ok]
    good = np.abs(vals - 1) < 0.35
    ys, xs, vals = ys[good], xs[good], vals[good]
    X = (xs - W / 2) / 1000.0; Y = (ys - H / 2) / 1000.0
    M = np.stack([np.ones_like(X), X, Y, X * X + Y * Y], 1)
    sol, *_ = np.linalg.lstsq(M, np.log2(vals), rcond=None)
    resid = np.log2(vals) - M @ sol
    print(f"  {label}: {os.path.basename(pa)}({exp_a}) / {os.path.basename(pb)}({exp_b})")
    print(f"    desplacament al sensor: dx={dx*2:+.1f} dy={dy*2:+.1f} px raw   "
          f"|d|={np.hypot(dx, dy)*2:.1f} px")
    print(f"    R lluna ajustat: {fa[2]*2:.1f} / {fb[2]*2:.1f} px raw (rms {fa[3]*2:.2f}/{fb[3]*2:.2f})")
    print(f"    quocient median = {med:.4f}  (esperat {exp_ratio(exp_a, exp_b):.4f} per exposicio)")
    print(f"    pendent del quocient: {sol[1]*2:+.4f} EV / 1000 px raw en x, "
          f"{sol[2]*2:+.4f} EV / 1000 px raw en y ; quadratic {sol[3]*4:+.4f} EV/(1000px)^2")
    p16, p84 = np.percentile(vals, [16, 84])
    print(f"    dispersio del quocient (16-84 %): {(p84-p16)/2*100:.2f} %   "
          f"rms residual despres del pla: {np.std(resid)*100*0.693:.2f} % ")
    return dict(label=label, dx=dx * 2, dy=dy * 2, med=med,
                gx=sol[1] * 2, gy=sol[2] * 2, q=sol[3] * 4,
                spread=(p84 - p16) / 2, resid=float(np.std(resid)),
                cx_a=fa[1] * 2, cy_a=fa[0] * 2, cx_b=fb[1] * 2, cy_b=fb[0] * 2)


def exp_ratio(ea, eb):
    def val(s):
        return eval(s.replace("/", "/")) if "/" in s else float(s)
    return val(ea) / val(eb)


if __name__ == "__main__":
    out = []
    print("=== A7RIIIA + Sony 300 GM : parelles a banda i banda del salt de muntura ===")
    for ea, na, nb in [("1", "DSC06985", "DSC06991"),
                       ("1/8", "DSC06986", "DSC06992"),
                       ("8", "DSC06987", "DSC06993"),
                       ("1/4", "DSC06982", "DSC06994"),
                       ("1/30", "DSC06983", "DSC06995"),
                       ("2", "DSC06984", "DSC06996"),
                       ("1/4", "DSC06982", "DSC06997"),
                       ("2", "DSC06984", "DSC06999")]:
        r = analyse(f"{SONY}/{na}.ARW", f"{SONY}/{nb}.ARW", 512.0, 613 / 2 / 2, f"Sony {ea}s", ea, ea)
        if r: out.append(r)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "corona_pairs.json"), "w"), indent=1)
