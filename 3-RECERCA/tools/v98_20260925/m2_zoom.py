"""m2 (V98) · Retalls ampliats (vei més proper) d'una capa d'un PSB: m2_zoom.py <psb> <id_capa> x0 y0 x1 y1 <factor> <sortida.png> [--marca id]"""
import sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
p, lid, x0, y0, x1, y1, f, out = sys.argv[1:9]; lid, x0, y0, x1, y1, f = int(lid), int(x0), int(y0), int(x1), int(y1), int(f)
s = PSB(p); box = (x0, y0, x1, y1)
ch = np.dstack([s.channel_box(lid, c, box) for c in (0, 1, 2)]).astype(np.float32) / 65535
al = s.channel_box(lid, -1, box); al = np.ones(ch.shape[:2], np.float32) if al is None else al.astype(np.float32) / 65535
im = ch * al[..., None] + 0.5 * (1 - al[..., None])
if '--estira' in sys.argv:
    lo, hi = np.percentile(im[al > 0.5], [1, 99]); im = (im - lo) / (hi - lo)
if '--marca' in sys.argv:
    mid = int(sys.argv[sys.argv.index('--marca') + 1]); mk = np.dstack([s.channel_box(mid, c, box) for c in (0, 1, 2)]).astype(np.float32) / 65535
    ma = s.channel_box(mid, -1, box).astype(np.float32) / 65535; ma = np.clip(ma / max(ma.max(), 1e-6), 0, 1) * 0.35
    im = im * (1 - ma[..., None]) + mk * ma[..., None]
u8 = (np.clip(im, 0, 1) * 255).astype(np.uint8)[..., ::-1]; u8 = cv2.resize(u8, None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
cv2.imwrite(out, u8); print(out, u8.shape)
