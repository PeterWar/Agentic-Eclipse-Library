"""m3 (V98) · Vista reduïda d'una capa (RGB sobre gris on és transparent), amb estirament percentil opcional:
m3_vista_capa.py <psb> <id> <x0> <y0> <x1> <y1> <reduccio> <sortida.png> [--estira]"""
import sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
p, lid, x0, y0, x1, y1, red, out = sys.argv[1:9]; lid, x0, y0, x1, y1, red = int(lid), int(x0), int(y0), int(x1), int(y1), int(red)
s = PSB(p); box = (x0, y0, x1, y1)
ch = np.dstack([s.channel_box(lid, c, box) for c in (0, 1, 2)]).astype(np.float32) / 65535
al = s.channel_box(lid, -1, box); al = np.ones(ch.shape[:2], np.float32) if al is None else al.astype(np.float32) / 65535
im = ch * al[..., None] + 0.5 * (1 - al[..., None])
im = cv2.resize(im, None, fx=1 / red, fy=1 / red, interpolation=cv2.INTER_AREA)
if '--estira' in sys.argv:
    lo, hi = np.percentile(im, [0.5, 99.5]); im = (im - lo) / (hi - lo)
cv2.imwrite(out, (np.clip(im, 0, 1) * 255).astype(np.uint8)[..., ::-1]); print(out, im.shape)
