"""Centre i el·lipse del limbe lunar per capa, al LLENÇ, amb la mateixa eina que V3b (lluna2.halfedges + lluna3.ellipse_fit)."""
import json, numpy as np
from v3c_lib import *
from lluna2 import halfedges
from lluna3 import ellipse_fit
out = {}
for i in (3, 4, 5, 7, 8, 9, 10):
    G = layer_channel_canvas(i, 1)
    c = (4036.0, 2738.0)
    for it in range(3):
        az, rad, ins, outs = halfedges(G, c)
        ok = np.isfinite(rad)
        px = c[0] + rad[ok]*np.cos(az[ok]); py = c[1] - rad[ok]*np.sin(az[ok])
        e = ellipse_fit(px, py); c = (e['cx'], e['cy'])
    e['R_eq'] = float(np.sqrt(e['a']*e['b'])); e['contrast_med'] = float(np.nanmedian(outs-ins))
    out[str(i)] = e
    print(i, {k: round(v, 3) if isinstance(v, float) else v for k, v in e.items()}, flush=True)
jdump(out, f'{SCR}/lluna_ellipse_llenc.json')
