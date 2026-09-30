#!/usr/bin/env python3
"""Extreu, de cada parcial filtrada, un mapa polar (rho, theta) de la fotosfera.

Nomes lectura sobre els originals. Guarda un .npz petit amb:
  cx, cy (centre del disc solar, pixels del pla G1), R (radi ajustat),
  maps[n, nrho, nth] amb la mitjana per cel.la, i counts.
El centre del disc s'ajusta amb radi FIX (el Sol te radi conegut), maximitzant
l'encaix amb la vora lluminosa, de manera que la Lluna no el desplaci.
"""
import glob, os, subprocess, sys
import numpy as np
import rawpy
from scipy import optimize, ndimage

PEDESTAL = 512.0
NRHO, NTH = 40, 72
RHO_MAX = 0.93


def load_plane(path, kind):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
        bl = r.black_level_per_channel
    if kind == "sony":       # patro [[0,1],[3,2]] -> G1 = fila parell, col senar
        return v[0::2, 1::2] - 512.0
    else:                     # Canon CR3: pedestal real pla 511-512 (metadata falsa)
        return v[0::2, 1::2] - 511.5


def fit_center(a, R):
    """Ajusta el centre del disc solar per la VORA SOLAR, amb radi fix R.

    Recorre radialment des d'un centre de prova en 360 azimuts i busca l'ultim
    creuament del 50 % del nivell interior. Els punts de la vora LUNAR cauen a
    r << R i es descarten; nomes s'ajusten els de la vora solar.
    """
    lo = np.percentile(a, 99.7)
    m = a > 0.35 * lo
    ys, xs = np.nonzero(m)
    if len(xs) < 3000:
        return None
    cy, cx = ys.mean(), xs.mean()
    H, W = a.shape
    th = np.linspace(-np.pi, np.pi, 360, endpoint=False)
    rs = np.arange(0.70 * R, 1.12 * R, 0.5)
    last = None
    for it in range(6):
        yq = cy + rs[None, :] * np.sin(th)[:, None]
        xq = cx + rs[None, :] * np.cos(th)[:, None]
        if yq.min() < 1 or xq.min() < 1 or yq.max() > H - 2 or xq.max() > W - 2:
            return None
        prof = ndimage.map_coordinates(a, [yq.ravel(), xq.ravel()], order=1).reshape(yq.shape)
        lvl = 0.5 * lo
        good_th, good_r = [], []
        for i in range(len(th)):
            p = prof[i]
            idx = np.nonzero(p > lvl)[0]
            if len(idx) == 0:
                continue
            j = idx[-1]
            if j + 1 >= len(rs):
                continue
            # interpolacio lineal del creuament
            f = (p[j] - lvl) / max(p[j] - p[j + 1], 1e-9)
            rc = rs[j] + f * (rs[1] - rs[0])
            # exigeix un tram continu illuminat just abans del creuament:
            # aixi la vora LUNAR (que deixa fosc a fora i a dins) queda fora
            run = 0
            k = j
            while k >= 0 and p[k] > lvl:
                run += 1; k -= 1
            if abs(rc - R) < 0.06 * R and run * (rs[1] - rs[0]) > 0.08 * R:
                good_th.append(th[i]); good_r.append(rc)
        if len(good_th) < 30:
            return None
        gt = np.array(good_th); gr = np.array(good_r)
        span = np.ptp(np.unwrap(np.sort(gt)))
        A = np.stack([np.ones_like(gt), np.cos(gt), np.sin(gt)], 1)
        sol, *_ = np.linalg.lstsq(A, gr, rcond=None)
        cx += sol[1]; cy += sol[2]
        last = (len(gt), span, float(np.std(gr - A @ sol)))
        if abs(sol[1]) < 0.02 and abs(sol[2]) < 0.02:
            break
    if last is None or last[0] < 30 or last[1] < 0.9:
        return None
    return cy, cx, last


def polar_map(a, cy, cx, R):
    H, W = a.shape
    r0 = int(np.ceil(R * RHO_MAX)) + 2
    y0, y1 = int(cy) - r0, int(cy) + r0 + 1
    x0, x1 = int(cx) - r0, int(cx) + r0 + 1
    if y0 < 0 or x0 < 0 or y1 > H or x1 > W:
        return None, None
    sub = a[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dy, dx = yy - cy, xx - cx
    rr = np.hypot(dy, dx) / R
    th = np.arctan2(dy, dx)
    sel = rr < RHO_MAX
    ir = (rr[sel] / RHO_MAX * NRHO).astype(int).clip(0, NRHO - 1)
    it = ((th[sel] + np.pi) / (2 * np.pi) * NTH).astype(int).clip(0, NTH - 1)
    idx = ir * NTH + it
    val = sub[sel]
    s = np.bincount(idx, weights=val, minlength=NRHO * NTH).reshape(NRHO, NTH)
    n = np.bincount(idx, minlength=NRHO * NTH).reshape(NRHO, NTH)
    return s, n


def main():
    kind = sys.argv[1]
    src = sys.argv[2]
    exp_want = sys.argv[3]
    iso_want = sys.argv[4]
    R = float(sys.argv[5])      # radi solar en pixels del pla mitjat
    out = sys.argv[6]
    files = sorted(glob.glob(os.path.join(src, "*.ARW")) + glob.glob(os.path.join(src, "*.CR3")))
    p = subprocess.run(["exiftool", "-T", "-FileName", "-ExposureTime", "-ISO",
                        "-DateTimeOriginal", *files], capture_output=True, text=True)
    meta = {}
    for line in p.stdout.strip().splitlines():
        q = line.split("\t")
        if len(q) >= 4:
            meta[q[0]] = q[1:]
    names, cxs, cys, maps, cnts, dts = [], [], [], [], [], []
    for f in files:
        b = os.path.basename(f)
        m = meta.get(b)
        if not m or m[0] != exp_want or m[1] != iso_want:
            continue
        a = load_plane(f, kind)
        c = fit_center(a, R)
        if c is None:
            print("SKIP-vora-insuficient", b, flush=True); continue
        cy, cx, q = c
        s, n = polar_map(a, cy, cx, R)
        if s is None:
            print("SKIP-fora-del-sensor", b, flush=True); continue
        names.append(b); cxs.append(cx); cys.append(cy)
        maps.append(s); cnts.append(n); dts.append(m[2])
        mean = s / np.maximum(n, 1)
        frac = float((mean > 0.3 * np.percentile(a, 99.7)).mean())
        print(f"{b} {m[2]} cx={cx:.1f} cy={cy:.1f} il={frac:.2f} "
              f"nvora={q[0]} span={np.degrees(q[1]):.0f}deg rms={q[2]:.2f}px", flush=True)
    np.savez_compressed(out, names=np.array(names), cx=np.array(cxs), cy=np.array(cys),
                        maps=np.array(maps), cnts=np.array(cnts), dts=np.array(dts), R=R)
    print("guardat", out, len(names))


if __name__ == "__main__":
    main()
