#!/usr/bin/env python3
"""Cerca de pols sobre el DISC SOLAR filtrat: la font mes brillant i mes llisa
de tot el material.

De cada fotograma es treu el perfil azimutal (l'enfosquiment del limbe) i es
mira el residu. Una taca de pols es un clot local i FIX AL SENSOR; una taca
solar es fixa al SOL. Amb dos fotogrames del disc a llocs diferents del sensor
els dos casos es distingeixen.

Nomes lectura. Escriu PNG estirats al directori de treball.
"""
import os, sys
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))


def plane(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
    return v[0::2, 1::2] - ped


def fit_disc(a, R):
    lo = np.percentile(a, 99.7)
    ys, xs = np.nonzero(a > 0.35 * lo)
    cy, cx = ys.mean(), xs.mean()
    H, W = a.shape
    th = np.linspace(-np.pi, np.pi, 720, endpoint=False)
    rs = np.arange(0.80 * R, 1.10 * R, 0.4)
    for _ in range(8):
        yq = cy + rs[None, :] * np.sin(th)[:, None]
        xq = cx + rs[None, :] * np.cos(th)[:, None]
        prof = ndimage.map_coordinates(a, [yq.ravel(), xq.ravel()], order=1).reshape(yq.shape)
        lv = 0.5 * lo
        gt, gr = [], []
        for i in range(len(th)):
            p = prof[i]
            idx = np.nonzero(p > lv)[0]
            if len(idx) == 0 or idx[0] != 0:
                continue
            j = idx[-1]
            if j + 1 >= len(rs):
                continue
            f = (p[j] - lv) / max(p[j] - p[j + 1], 1e-9)
            gt.append(th[i]); gr.append(rs[j] + f * (rs[1] - rs[0]))
        gt = np.array(gt); gr = np.array(gr)
        A = np.stack([np.ones_like(gt), np.cos(gt), np.sin(gt)], 1)
        sol, *_ = np.linalg.lstsq(A, gr, rcond=None)
        cx += sol[1]; cy += sol[2]
        if abs(sol[1]) < 0.01 and abs(sol[2]) < 0.01:
            break
    return cy, cx, sol[0], len(gt), float(np.std(gr - A @ sol))


def residual(a, cy, cx, R, rho_max=0.86, nrho=400):
    H, W = a.shape
    r0 = int(R * rho_max)
    y0, y1 = int(cy) - r0 - 1, int(cy) + r0 + 2
    x0, x1 = int(cx) - r0 - 1, int(cx) + r0 + 2
    sub = a[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    rr = np.hypot(yy - cy, xx - cx) / R
    ins = rr < rho_max
    # perfil azimutal robust, iterat per treure la mossegada de la Lluna
    ib = (rr / rho_max * nrho).astype(int).clip(0, nrho - 1)
    use = ins.copy()
    for _ in range(4):
        prof = np.array([np.median(sub[use & (ib == k)]) if (use & (ib == k)).sum() > 30 else np.nan
                         for k in range(nrho)])
        good = np.isfinite(prof)
        if good.sum() < 10:
            break
        prof = np.interp(np.arange(nrho), np.nonzero(good)[0], prof[good])
        model = np.interp(rr.ravel() / rho_max * nrho, np.arange(nrho), prof).reshape(rr.shape)
        use = ins & (sub > 0.90 * model) & (sub < 1.10 * model)
    res = np.where(use, sub / np.maximum(model, 1e-6) - 1.0, np.nan)
    return res, (y0, x0), use, float(np.median(sub[use]))


def png(arr, path, lim=0.02):
    v = np.nan_to_num(arr, nan=0.0)
    im = np.clip((v + lim) / (2 * lim), 0, 1)
    im = (im * 255).astype(np.uint8)
    Image.fromarray(im).save(path)


def report(name, path, ped, R, tag):
    a = plane(path, ped)
    cy, cx, Rf, n, rms = fit_disc(a, R)
    res, off, ins, lvl = residual(a, cy, cx, R)
    print(f"\n--- {name} ---")
    print(f"  centre (raw) = ({cx*2:.1f}, {cy*2:.1f})  R ajustat = {Rf*2:.1f} px raw "
          f"({n} punts de vora, rms {rms*2:.2f} px)")
    print(f"  nivell de la fotosfera: {lvl:.0f} ADU")
    for sc in (24, 60, 120, 260):
        s = ndimage.gaussian_filter(np.nan_to_num(res, nan=0.0), sc / 2 / 2.355)
        w = ndimage.gaussian_filter(ins.astype(float), sc / 2 / 2.355)
        s = s / np.maximum(w, 1e-6)
        core = ndimage.binary_erosion(ins, iterations=int(sc / 2) + 4)
        if core.sum() < 500:
            continue
        v = s[core]
        print(f"    escala {sc:>3} px raw: sigma={np.std(v)*100:.3f} %  "
              f"min={np.min(v)*100:+.2f} %  max={np.max(v)*100:+.2f} %")
    png(res, os.path.join(OUT, f"res_{tag}.png"), 0.02)
    return res, off, ins, (cy, cx)


if __name__ == "__main__":
    S = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
    print("=== A7RIIIA : disc filtrat sencer, dos llocs del sensor ===")
    r1 = report("DSC06928 (19:38)", f"{S}/DSC06928.ARW", 512.0, 146.4, "sony_a")
    r2 = report("DSC06931 (19:43)", f"{S}/DSC06931.ARW", 512.0, 146.4, "sony_b")
    # comparacio: el residu es fix al SENSOR o al SOL?
    A, oA, iA, cA = r1
    B, oB, iB, cB = r2
    dy = int(round(oB[0] - oA[0])); dx = int(round(oB[1] - oA[1]))
    print(f"\n  desplacament del disc entre els dos: ({dx*2}, {dy*2}) px raw")
    sA = ndimage.gaussian_filter(np.nan_to_num(A, nan=0.0), 60 / 2 / 2.355)
    sB = ndimage.gaussian_filter(np.nan_to_num(B, nan=0.0), 60 / 2 / 2.355)
    h = min(sA.shape[0], sB.shape[0]); w = min(sA.shape[1], sB.shape[1])
    mA = ndimage.binary_erosion(iA, iterations=34)[:h, :w]
    mB = ndimage.binary_erosion(iB, iterations=34)[:h, :w]
    m = mA & mB
    cs = np.corrcoef(sA[:h, :w][m], sB[:h, :w][m])[0, 1]
    print(f"  correlacio dels residus alineats al SOL   : {cs:+.3f}  ({m.sum()} px)")
    print("  (si fossin taques de pols, alineats al sol NO correlacionarien;")
    print("   alineats al sensor SI. Aqui el desplacament els treu de la zona comuna.)")
    if len(sys.argv) > 1:
        V = "/Users/USUARI/Desktop/Eclipse 2026/Vixen"
        print("\n=== R6 III : disc filtrat sencer ===")
        for f in sys.argv[1:]:
            report(f, f"{V}/{f}", 511.5, 219.4, "r6_" + f.split(".")[0][-4:])
