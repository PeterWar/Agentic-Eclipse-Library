#!/usr/bin/env python3
"""Fotometria del disc solar filtrat (1/400, ISO100) a les parcials de l'A7RIIIA.

Nomes lectura. Treballa amb el pla de Bayer G1 (color 1), sense desbayerar.
Per a cada fotograma: centroide del disc i flux integrat dins una obertura fixa.
"""
import glob, json, os, sys
import numpy as np
import rawpy

SRC = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sony_partials.json")

PEDESTAL = 512.0
# escala 3,234"/px (raw). Disc solar ~1900" -> ~588 px raw -> ~294 px al pla G1
R_AP = 210      # radi d'obertura, en pixels del pla G1 (= 420 px raw)
R_BG0, R_BG1 = 240, 300


def load_g1(path):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
        c = r.raw_colors_visible
    # Sony pattern [[0,1],[3,2]] -> G1 es color 1 (fila parell, col senar)
    g1 = v[0::2, 1::2]
    g2 = v[1::2, 0::2]
    return g1, g2


def measure(path, exif_exp):
    g1, g2 = load_g1(path)
    a = g1 - PEDESTAL
    H, W = a.shape
    # llindar generos per trobar el disc
    thr = 0.25 * np.percentile(a, 99.9)
    if thr <= 0:
        return None
    mask = a > thr
    if mask.sum() < 5000:
        return None
    ys, xs = np.nonzero(mask)
    # centroide pesat per intensitat (iterat un cop)
    cy, cx = ys.mean(), xs.mean()
    for _ in range(3):
        yy, xx = np.ogrid[:H, :W]
        d2 = (yy - cy) ** 2 + (xx - cx) ** 2
        m = (d2 < R_AP ** 2) & mask
        w = a[m]
        cy = (np.nonzero(m)[0] * w).sum() / w.sum()
        cx = (np.nonzero(m)[1] * w).sum() / w.sum()
    yy, xx = np.ogrid[:H, :W]
    d2 = (yy - cy) ** 2 + (xx - cx) ** 2
    ap = d2 < R_AP ** 2
    bg = (d2 >= R_BG0 ** 2) & (d2 < R_BG1 ** 2)
    # comprova que l'obertura i l'anell caben dins el sensor
    inside = (cx - R_BG1 > 0) and (cx + R_BG1 < W) and (cy - R_BG1 > 0) and (cy + R_BG1 < H)
    sky = np.median(a[bg]) if bg.sum() > 0 else 0.0
    flux = float((a[ap] - sky).sum())
    npix = int(ap.sum())
    sat = int((g1 >= 16000).sum())
    # radi equivalent del disc (per detectar canvi de mida / nuvols)
    half = a[ap] - sky
    peak = np.percentile(half, 99)
    area = float((half > 0.5 * peak).sum())
    return dict(
        file=os.path.basename(path), exp=exif_exp,
        cx=float(cx), cy=float(cy), flux=flux, sky=float(sky),
        npix=npix, sat=sat, peak=float(peak), area=area, inside=bool(inside),
        g2mean=float(np.median(g2[ap] - PEDESTAL)),
    )


def main():
    import subprocess
    files = sorted(glob.glob(os.path.join(SRC, "*.ARW")))
    # llegeix exposicions
    out = subprocess.run(["exiftool", "-T", "-FileName", "-ExposureTime", "-ISO",
                          "-DateTimeOriginal", *files], capture_output=True, text=True)
    meta = {}
    for line in out.stdout.strip().splitlines():
        p = line.split("\t")
        if len(p) >= 4:
            meta[p[0]] = dict(exp=p[1], iso=p[2], dt=p[3])
    res = []
    for f in files:
        b = os.path.basename(f)
        m = meta.get(b, {})
        if m.get("exp") != "1/400" or m.get("iso") != "100":
            continue
        try:
            r = measure(f, m["exp"])
        except Exception as e:
            print("ERR", b, e, file=sys.stderr)
            continue
        if r is None:
            print("SKIP", b, file=sys.stderr)
            continue
        r["dt"] = m["dt"]
        res.append(r)
        print(f"{b} {r['dt']} cx={r['cx']:.1f} cy={r['cy']:.1f} flux={r['flux']:.4g} "
              f"sky={r['sky']:.1f} area={r['area']:.0f} inside={r['inside']}", flush=True)
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print("guardat", OUT, len(res))


if __name__ == "__main__":
    main()
