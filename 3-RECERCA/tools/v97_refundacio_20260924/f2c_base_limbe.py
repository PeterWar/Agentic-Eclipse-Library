"""f2c (V97) · La base final: la base nova (f2b, recepta b4e sobre la linealitzada V97) LLUNY del limbe, i la base de la V96 ARRAN del limbe.
Per què (làmina LAMINA_V97_1, 24-09 nit): la recepta sobre la linealitzada V97 dona, a menys de ~120 px del limbe, una base més clara
(0,705 contra 0,619 a d 0–3 px) i blanquinosa/rosada (l'espatlla s75c90 hi comprimeix els tres canals cap al blanc). A la V96, aquesta zona
porta les correccions del limbe de la V53–V56 (una recomposició a la caixa lunar), que Pere ha vist i aprovat al llarg de la V86–V96.
La recomposició nova del limbe no està validada: es conserva la de la V96 i es declara com a deute (vegeu RESULTAT.md).
Regla: w = smoothstep(d, 150, 250) (d = distància al limbe de presentació); base = (1 − w)·V96 + w·nova. A 150–250 px, les dues bases
difereixen menys de l'1 % (p99), de manera que la fosa no fa cap costura. Ús: f2c_base_limbe.py <base_nova_u16.npy> <sortida_u16.npy>"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import RES, dist_limbe, desa
def smoothstep(x, lo, hi): t = np.clip((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)
NOVA, OUT = Path(sys.argv[1]), Path(sys.argv[2])
N = np.load(NOVA, mmap_mode='r'); V = np.load(RES / 'v96_ref/L3_RGB.npy', mmap_mode='r'); out = np.empty(N.shape, np.uint16); rep = dict(nova=str(NOVA), v96='v96_ref/L3_RGB.npy', fosa_px=[150, 250], files={})
for y0 in range(0, N.shape[0], 512):
    y1 = min(N.shape[0], y0 + 512); d = dist_limbe((0, y0, N.shape[1], y1)); w = smoothstep(d, 150.0, 250.0)[..., None]
    out[y0:y1] = np.rint((1 - w) * np.asarray(V[y0:y1], np.float32) + w * np.asarray(N[y0:y1], np.float32)).astype(np.uint16)
np.save(OUT, out)
d = dist_limbe(pas=4); z = (d > 150) & (d < 250); dif = np.abs(np.asarray(N[::4, ::4], np.float32) - np.asarray(V[::4, ::4], np.float32)) / 65535
rep['dif_nova_V96_a_la_fosa'] = dict(mediana=float(np.median(dif[z])), p99=float(np.percentile(dif[z], 99)))
desa(str(OUT).replace('.npy', '_REBUT.json'), rep); print(json.dumps(rep['dif_nova_V96_a_la_fosa']))
