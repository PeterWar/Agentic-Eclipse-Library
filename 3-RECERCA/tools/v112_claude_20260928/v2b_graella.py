"""Graella de retalls de les vistes de banda per capa (de v2), cadascuna amb la seva escala (p99.5 de |banda| al retall),
amb el contorn de les marques 412. Ús: v2b_graella.py DIR SORTIDA.png x0 y0 x1 y1 [ids…]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[3]; C = R / '4-RESULTATS/v112_20260928'
sys.path.insert(0, str(R / '3-RECERCA/tools/v73_marques_v71_20260917'))
D = Path(sys.argv[1]); out = sys.argv[2]; x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]]
ids = [int(v) for v in sys.argv[7:]] or [3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56]
B = 6
mq = np.load(C / 'marques412.npz'); al = mq['alpha'] > 0; org = mq['origin']
full = np.zeros((7506, 10551), bool); full[org[1]:org[1] + al.shape[0], org[0]:org[0] + al.shape[1]] = al
h, w = 7506 // B, 10551 // B
mb = full[:h*B, :w*B].reshape(h, B, w, B).any((1, 3)); vora = mb & ~ndi.binary_erosion(mb, iterations=1)
bx0, by0, bx1, by1 = x0 // B, y0 // B, x1 // B, y1 // B
tiles = []
for lid in ids:
    a = np.load(D / f'L{lid}.npy')[by0:by1, bx0:bx1]
    s = np.nanpercentile(np.abs(a), 99.5) if np.isfinite(a).any() else 1
    g = np.clip((np.nan_to_num(a) / s + 1) * 127.5, 0, 255).astype(np.uint8); g[~np.isfinite(a)] = 0
    rgb = np.stack([g] * 3, -1); rgb[vora[by0:by1, bx0:bx1]] = (255, 0, 255)
    im = Image.fromarray(rgb); d = ImageDraw.Draw(im); d.text((4, 4), f'L{lid} ±{s:.3g}', fill=(255, 255, 0))
    tiles.append(im)
n = len(tiles); cols = 4 if n > 6 else 3; rows = (n + cols - 1) // cols
tw, th = tiles[0].size
G = Image.new('RGB', (cols * (tw + 4), rows * (th + 4)), (40, 40, 40))
for k, t in enumerate(tiles):
    G.paste(t, ((k % cols) * (tw + 4), (k // cols) * (th + 4)))
z = min(2.0, 1990 / G.width, 1990 / G.height)
G = G.resize((int(G.width * z), int(G.height * z)), Image.LANCZOS)
G.save(out); print(out, G.size)
