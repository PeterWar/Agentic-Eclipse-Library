"""02 — Centre i el·lipse del limbe lunar per a les 12 capes, al LLENÇ, mesurats sobre els
revelats V4 (proposta §4.2: P3/P4 i centres es re-mesuren; la geometria és la mateixa que V2b
—mateixos frames, cap remostreig— i ho ha de confirmar el residu)."""
import sys, numpy as np
from v4_lib import *
HERE_V3B = Path(__file__).resolve().parent.parent / 'capes_totals_v3b'
sys.path.insert(0, str(HERE_V3B))
from lluna2 import halfedges
from lluna3 import ellipse_fit

ids = [int(s) for s in sys.argv[1:]] or list(ORDER)
out = {}
for i in ids:
    G = layer_channel_canvas(i, 1)
    c = (4036.0, 2738.0)
    for it in range(3):
        az, rad, ins, outs = halfedges(G, c)
        ok = np.isfinite(rad)
        px = c[0] + rad[ok] * np.cos(az[ok])
        py = c[1] - rad[ok] * np.sin(az[ok])
        e = ellipse_fit(px, py)
        c = (e['cx'], e['cy'])
    e['R_eq'] = float(np.sqrt(e['a'] * e['b']))
    e['contrast_med'] = float(np.nanmedian(outs - ins))
    e['n_ok'] = int(ok.sum())
    out[str(i)] = e
    print(i, {k: round(v, 3) if isinstance(v, float) else v for k, v in e.items()}, flush=True)
    del G
jdump(out, V4W / 'lluna_ellipse_v4.json')
