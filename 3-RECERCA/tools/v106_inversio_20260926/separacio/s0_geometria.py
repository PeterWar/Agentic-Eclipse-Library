"""s0 · Geometria: centre de la Lluna de cada fotograma al llenç (gradient de distance_model), desplaçament respecte de la Lluna de presentació,
components radial i tangencial per angle de posició."""
import json, numpy as np
from pathlib import Path
R0 = Path.home() / 'Desktop/Eclipse 2026'
LF = R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar'
meta = json.loads((LF/'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
Dm = np.load(LF/'distance_model.npy', mmap_mode='r'); Rm = float(meta['radius_model'])
hb, wb = by1 - by0, bx1 - bx0
cx, cy, R = 5375.786804312011, 3775.9774911631, 452.9785129274736
C = []
for j in range(len(fr)):
    D = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    C.append((ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]))
C = np.array(C); t = np.array([f['time'] for f in fr]); e = np.array([f['exposure'] for f in fr])
np.savez('GEOM.npz', C=C, t=t, e=e)
for j in range(len(fr)):
    dx, dy = C[j, 0] - cx, C[j, 1] - cy
    print(j, round(t[j], 1), e[j], 'dx %+.2f dy(avall) %+.2f' % (dx, dy))
# desplaçament: angle del moviment (0 = dreta, 90 = amunt)
v = C[-1] - C[0]; print('moviment total', v, np.hypot(*v), 'angle', np.degrees(np.arctan2(-v[1], v[0])) % 360)
