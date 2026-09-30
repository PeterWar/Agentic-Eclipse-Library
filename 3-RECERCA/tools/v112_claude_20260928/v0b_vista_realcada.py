"""V112 (Claude, 28-09-2026): vista realçada del llenç sencer per veure artefactes de gran escala (arcs, costures, taques).
L = (R+2G+B)/4 del render natiu; mitjana en blocs de 6×6 (treu el soroll de píxel); log; es resta una gaussiana gran
(σ 40 blocs ≈ 240 px, amb normalització per la màscara de dada) i s'estira igual a totes les imatges.
Ús: v0b_vista_realcada.py SORTIDA.png TIFF1 [TIFF2 …]  (una columna per TIFF, amb el contorn de les marques 412)."""
from pathlib import Path
import sys
import numpy as np
import tifffile
from scipy import ndimage as ndi
from PIL import Image, ImageDraw

R = Path(__file__).resolve().parents[3]
C = R / '4-RESULTATS/v112_20260928'
B = 6
SIG = 40


def realca(tif):
    a = tifffile.memmap(tif)
    H, W = a.shape[:2]
    h, w = H // B, W // B
    L = np.zeros((h, w), np.float64)
    for c, k in ((0, 1), (1, 2), (2, 1)):
        L += k * np.asarray(a[:h * B, :w * B, c], np.float64).reshape(h, B, w, B).mean((1, 3))
    L /= 4
    val = L > 400
    lg = np.where(val, np.log(np.maximum(L, 1)), 0)
    num = ndi.gaussian_filter(lg, SIG); den = ndi.gaussian_filter(val.astype(float), SIG)
    hp = np.where(val, lg - num / np.maximum(den, 1e-3), 0)
    # banda: es treu també el soroll de píxel (σ 3 blocs ≈ 18 px), normalitzat per la màscara de dada
    n2 = ndi.gaussian_filter(hp, 3); d2 = ndi.gaussian_filter(val.astype(float), 3)
    hp = np.where(val, n2 / np.maximum(d2, 1e-3), 0)
    return hp, val


def main():
    out = Path(sys.argv[1]); tifs = sys.argv[2:]
    mq = np.load(C / 'marques412.npz'); al = mq['alpha'] > 0; org = mq['origin']
    full = np.zeros((7506, 10551), bool)
    full[org[1]:org[1] + al.shape[0], org[0]:org[0] + al.shape[1]] = al
    h, w = 7506 // B, 10551 // B
    mb = full[:h * B, :w * B].reshape(h, B, w, B).any((1, 3))
    vora = mb & ~ndi.binary_erosion(mb, iterations=1)
    cols = []
    s = None
    for t in tifs:
        hp, val = realca(t)
        if s is None:
            yy, xx = np.mgrid[0:hp.shape[0], 0:hp.shape[1]]
            rr = np.hypot(xx * B + B / 2 - 5375.8, yy * B + B / 2 - 3776.0)
            s = np.percentile(np.abs(hp[val & (rr > 1800)]), 99.5)
        g = np.clip((hp / s + 1) * 127.5, 0, 255).astype(np.uint8)
        g[~val] = 0
        rgb = np.stack([g] * 3, -1)
        rgb[vora] = (255, 0, 255)
        cols.append(rgb)
        print(t, 'escala ±', round(float(s), 4))
    im = Image.fromarray(np.concatenate(cols, 1))
    d = ImageDraw.Draw(im)
    for i, t in enumerate(tifs):
        d.text((i * w + 10, 10), Path(t).parent.name + '/' + Path(t).name, fill=(255, 255, 0))
    im.save(out)


if __name__ == '__main__':
    main()
