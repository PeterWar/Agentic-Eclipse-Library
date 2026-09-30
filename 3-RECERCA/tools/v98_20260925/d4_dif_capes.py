"""d4 (V98) · Diferència d'una mateixa capa entre dos PSB (p. ex. la 49 de la V93 a Artefactes_V95 i la de la V97), en una caixa, reduïda:
d4_dif_capes.py <psbA> <psbB> <id> x0 y0 x1 y1 <reduccio> <sortida.png> [--sigma s]  (pas alt opcional de la diferència)"""
import sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
pa, pb, lid, x0, y0, x1, y1, red, out = sys.argv[1:10]; lid, x0, y0, x1, y1, red = int(lid), int(x0), int(y0), int(x1), int(y1), int(red)
box = (x0, y0, x1, y1)
def g(p):
    s = PSB(p); v = s.channel_box(lid, 1, box).astype(np.float32) / 65535; a = s.channel_box(lid, -1, box); a = np.ones_like(v) if a is None else a.astype(np.float32) / 65535; return v, a
A, aA = g(pa); B, aB = g(pb); ok = (aA > 0.99) & (aB > 0.99); D = np.where(ok, A - B, 0).astype(np.float32)
if '--sigma' in sys.argv:
    s_ = float(sys.argv[sys.argv.index('--sigma') + 1]); w = ok.astype(np.float32); D = D - cv2.GaussianBlur(D, (0, 0), s_) / np.maximum(cv2.GaussianBlur(w, (0, 0), s_), 1e-6) * w
D = cv2.resize(D, None, fx=1 / red, fy=1 / red, interpolation=cv2.INTER_AREA); s = np.percentile(np.abs(D), 99.5) + 1e-9
cv2.imwrite(out, (np.clip(0.5 + 0.5 * D / s, 0, 1) * 255).astype(np.uint8)); print(out, 'escala ±', round(float(s), 4))
