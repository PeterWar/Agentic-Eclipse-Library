#!/usr/bin/env python3
"""FLAT SINTETIC a partir de les parcials filtrades, alineades al CEL.

La fotosfera filtrada es una font enorme, brillant i llisa. De cada fotograma
en traiem el model del propi Sol -- enfosquiment del limbe S(rho), comu a tots,
mes un zero i un gradient lineal per fotograma, que absorbeixen l'exposicio i
l'extincio-- i el que queda es divideix. El residu s'apila en coordenades del
SENSOR: el que no es mou amb el cel (pols, PRNU, vinyetatge no simetric) s'hi
suma, i el Sol es diluteix perque cada fotograma el te a un altre lloc.

Nomes lectura sobre els originals.
"""
import os, sys
import numpy as np
import rawpy
from scipy import ndimage

RHO_MAX = 0.93


def plane(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
    return v[0::2, 1::2] - ped


def main(npz, src, ped, label, out_prefix):
    Z = np.load(npz, allow_pickle=True)
    names = [str(x) for x in Z["names"]]
    cx, cy, R = Z["cx"], Z["cy"], float(Z["R"])
    maps, cnts = Z["maps"], Z["cnts"]
    N, NRHO, NTH = maps.shape
    mean = maps / np.maximum(cnts, 1)
    valid = cnts > 20
    rho = (np.arange(NRHO) + 0.5) / NRHO * RHO_MAX

    # S(rho) comu
    ref = np.array([np.percentile(mean[i][valid[i]], 97) if valid[i].any() else 1 for i in range(N)])
    lit = valid & (mean > 0.45 * ref[:, None, None]) & (rho[None, :, None] < 0.88)
    L = np.where(lit, np.log2(np.maximum(mean, 1e-3)), np.nan)
    S = np.zeros(NRHO)
    for _ in range(4):
        zf = np.nanmedian((L - S[None, :, None]).reshape(N, -1), axis=1)
        S = np.nanmedian((L - zf[:, None, None]), axis=(0, 2))
        S = np.where(np.isfinite(S), S, 0.0)

    acc = None
    used = 0
    for i in range(N):
        a = plane(os.path.join(src, names[i]), ped)
        H, W = a.shape
        if acc is None:
            acc = np.zeros((H, W)); cnt = np.zeros((H, W), np.int32)
        r0 = int(R * 0.88)
        y0, y1 = int(cy[i]) - r0, int(cy[i]) + r0 + 1
        x0, x1 = int(cx[i]) - r0, int(cx[i]) + r0 + 1
        if y0 < 0 or x0 < 0 or y1 > H or x1 > W:
            continue
        sub = a[y0:y1, x0:x1]
        yy, xx = np.mgrid[y0:y1, x0:x1]
        uy = yy - cy[i]; ux = xx - cx[i]
        rr = np.hypot(uy, ux) / R
        ins = (rr < 0.86) & (sub > 0)
        if ins.sum() < 20000:
            continue
        # model del Sol: interpola S(rho) i ajusta zero + gradient lineal
        Sv = np.interp(rr, rho, S)
        y = np.log2(np.maximum(sub, 1e-3)) - Sv
        good = ins & (y > np.nanpercentile(y[ins], 20) - 1.2)   # treu la Lluna
        if good.sum() < 20000:
            continue
        A = np.stack([np.ones(good.sum()), ux[good], uy[good]], 1)
        sol, *_ = np.linalg.lstsq(A, y[good], rcond=None)
        model = Sv + sol[0] + sol[1] * ux + sol[2] * uy
        res = np.log2(np.maximum(sub, 1e-3)) - model
        m = good & (np.abs(res) < 0.12)
        acc[y0:y1, x0:x1][m] += res[m]
        cnt[y0:y1, x0:x1][m] += 1
        used += 1
        print(f"   {names[i]:<16} n={m.sum():7d}  rms={np.std(res[m])*100*0.693:.2f} %", flush=True)

    ok = cnt >= 6
    flat = np.where(ok, acc / np.maximum(cnt, 1), np.nan)
    print(f"\n  {label}: {used} fotogrames apilats; "
          f"{ok.sum()} px del pla G1 amb 6 o mes mesures "
          f"({100*ok.sum()/ok.size:.1f} % del sensor)")
    ys, xs = np.nonzero(ok)
    print(f"  regio coberta (px raw): x {xs.min()*2}-{xs.max()*2}, y {ys.min()*2}-{ys.max()*2}")
    v = flat[ok]
    print(f"  mediana del comptador: {np.median(cnt[ok]):.0f} fotogrames/px")
    print(f"  residu pixel a pixel: sigma = {np.std(v)*69.3:.3f} %")
    for sc, nm in [(24, "24 px raw"), (60, "60 px raw"), (120, "120 px raw"), (260, "260 px raw")]:
        f2 = np.nan_to_num(flat, nan=0.0)
        w = ndimage.gaussian_filter(ok.astype(float), sc / 2 / 2.355)
        s = ndimage.gaussian_filter(f2, sc / 2 / 2.355) / np.maximum(w, 1e-6)
        core = ndimage.binary_erosion(ok, iterations=int(sc / 2))
        if core.sum() < 1000:
            continue
        vv = s[core]
        print(f"    escala {nm:>10}: sigma={np.std(vv)*69.3:.3f} %  "
              f"min={np.min(vv)*69.3:+.2f} %  max={np.max(vv)*69.3:+.2f} %")
    np.save(out_prefix + "_flat.npy", flat)
    np.save(out_prefix + "_cnt.npy", cnt)
    return flat, cnt


if __name__ == "__main__":
    print("=== A7RIIIA + Sony 300 GM ===")
    main("sony_maps.npz", "/Users/USUARI/Desktop/Eclipse 2026/300mm", 512.0,
         "Sony", "flat_sony")
    if len(sys.argv) > 1 and sys.argv[1] == "r6":
        print("\n=== R6 III + VSD90SS ===")
        main("r6_maps.npz", "/Users/USUARI/Desktop/Eclipse 2026/Vixen", 511.5,
             "R6", "flat_r6")
