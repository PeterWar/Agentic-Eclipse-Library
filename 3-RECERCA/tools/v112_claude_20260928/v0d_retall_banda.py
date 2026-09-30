"""Retall de les vistes de banda (.npy de v0c) en coordenades del llenç, costat a costat, amb el contorn de les marques 412.
Ús: v0d_retall_banda.py SORTIDA.png x0 y0 x1 y1 escala_log A.npy [B.npy …]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[3]
C = R / '4-RESULTATS/v112_20260928'
B = 6
out = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; s = float(sys.argv[6]); fs = sys.argv[7:]
mq = np.load(C / 'marques412.npz'); al = mq['alpha'] > 0; org = mq['origin']
full = np.zeros((7506, 10551), bool); full[org[1]:org[1] + al.shape[0], org[0]:org[0] + al.shape[1]] = al
h, w = 7506 // B, 10551 // B
mb = full[:h * B, :w * B].reshape(h, B, w, B).any((1, 3)); vora = mb & ~ndi.binary_erosion(mb, iterations=1)
bx0, by0, bx1, by1 = x0 // B, y0 // B, x1 // B, y1 // B
cols = []
for f in fs:
    a = np.load(f)[by0:by1, bx0:bx1]
    g = np.clip((np.nan_to_num(a) / s + 1) * 127.5, 0, 255).astype(np.uint8); g[np.isnan(a)] = 0
    rgb = np.stack([g] * 3, -1); rgb[vora[by0:by1, bx0:bx1]] = (255, 0, 255)
    cols.append(rgb); cols.append(np.full((rgb.shape[0], 4, 3), 255, np.uint8))
im = Image.fromarray(np.concatenate(cols[:-1], 1))
z = min(3.0, 1900 / im.width, 1400 / im.height)
im = im.resize((int(im.width * z), int(im.height * z)), Image.NEAREST if z >= 1 else Image.LANCZOS)
d = ImageDraw.Draw(im); d.text((6, 6), f"{' | '.join(Path(f).stem for f in fs)}  caixa {x0},{y0}-{x1},{y1}  ±{s}", fill=(255, 255, 0))
im.save(out); print(out, im.size)
