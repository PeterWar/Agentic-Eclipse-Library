"""v6 · retall del compost real (RGB del render natiu), costat a costat, amb el MATEIX estirament (percentils 1–99,5 del primer) i un suavitzat
opcional σ px (per veure l'estructura de 100–500 px com la veu l'ull a pantalla). Ús: v6_retall_real.py SORTIDA.png x0 y0 x1 y1 sigma A.tif B.tif [...]"""
import sys
from pathlib import Path
import numpy as np, tifffile
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[3]
out = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; sg = float(sys.argv[6]); fs = sys.argv[7:]
mq = np.load(R / '4-RESULTATS/v112_20260928/marques412.npz'); al = mq['alpha'] > 0; org = mq['origin']
full = np.zeros((7506, 10551), bool); full[org[1]:org[1] + al.shape[0], org[0]:org[0] + al.shape[1]] = al
m = full[y0:y1, x0:x1]; vora = m & ~ndi.binary_erosion(m, iterations=4)
lo = hi = None; cols = []
for f in fs:
    a = np.asarray(tifffile.memmap(f)[y0:y1, x0:x1], np.float32)
    if sg > 0: a = np.stack([ndi.gaussian_filter(a[..., c], sg) for c in range(3)], -1)
    if lo is None: lo, hi = np.percentile(a, 1), np.percentile(a, 99.5)
    g = np.clip((a - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8); g[vora] = (255, 0, 255); cols += [g, np.full((g.shape[0], 8, 3), 255, np.uint8)]
im = Image.fromarray(np.concatenate(cols[:-1], 1)); z = min(1.0, 1990 / im.width, 1400 / im.height); im = im.resize((int(im.width * z), int(im.height * z)), Image.LANCZOS)
ImageDraw.Draw(im).text((6, 6), ' | '.join(Path(f).parent.name for f in fs) + f'  σ{sg}', fill=(255, 255, 0)); im.save(out); print(out)
