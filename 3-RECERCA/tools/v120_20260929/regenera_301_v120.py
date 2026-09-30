"""regenera_301_v120 (V120, 29-09-2026): la 301 («Cantonada del logo · es regenera») amb la mateixa recepta (v86 a5_cantonada.calcula, sense canvis)
sobre el render natiu de la pila de sota de la V120. Diferència amb regenera_301_v117: l'ALFA pot canviar, perquè el triangle buit de la cantonada
ha crescut (la Sony deformada a la geometria de la Vixen perd uns 5–8 px de marge a la vora del camp); amb l'alfa vella hi quedaria una tira buida
al llarg de la hipotenusa. Garantia que l'alfa no és un retoc de Pere: la recepta aplicada al render de la pila de sota de la V119
(4-RESULTATS/v119_20260929/render_stage1_sota301) ha de reproduir EXACTAMENT l'alfa de la 301 de la V119 (i la de la V115 de Pere); si no, s'atura.
Sortida: <carpeta>/L301_c{0,1,2}.npy, L301_alfa.npy (q_blocs), RECEIPT.json. Ús: regenera_301_v120.py <render_sota301.tif> <carpeta_sortida>"""
from pathlib import Path
import sys, json, numpy as np, tifffile, importlib.util
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs, sha
ROOT = Path(__file__).resolve().parents[3]
inp = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve(); out.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('corner', ROOT / '3-RECERCA/tools/v86_neta_20260923/a5_cantonada.py'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
box = (7356, 4320, 9348, 6263); x0, y0, x1, y1 = box
def recepta(tif):
    im = tifffile.memmap(tif, mode='r'); assert im.shape == (7506, 10551, 3) and im.dtype.kind == 'u' and im.dtype.itemsize == 2
    rgb, alpha, rec = mod.calcula(im[y0:y1, x0:x1].astype(np.float32) / 65535.)
    raw = np.round(alpha * 65535).astype('uint16'); raw[0, 0] = max(raw[0, 0], 1); raw[-1, -1] = max(raw[-1, -1], 1); return rgb, q_blocs(raw), rec
# 1 · la prova: la recepta sobre el render de la V119 torna l'alfa de la V119 i la de la V115
TIF119 = ROOT / '4-RESULTATS/v119_20260929/render_stage1_sota301/visible_complet.tif'
_, a119, _ = recepta(TIF119)
prova = {}
for nom in ('V119', 'V115'):
    p = PSB(str(ROOT / f'1-PHOTOSHOP/{nom}.psb')); orig, org = p.channel(301, -1); assert org == (x0, y0)
    prova[nom] = dict(sha256=sha(ROOT / f'1-PHOTOSHOP/{nom}.psb'), alfa_igual_a_la_recepta=bool(np.array_equal(a119, orig)))
assert all(v['alfa_igual_a_la_recepta'] for v in prova.values()), prova
# 2 · la recepta sobre el render de la V120
rgb, alpha, receipt = recepta(inp)
p = PSB(str(ROOT / '1-PHOTOSHOP/V119.psb')); orig, _ = p.channel(301, -1); ad = alpha.astype('int32') - orig.astype('int32')
receipt.update(input_native=str(inp.relative_to(ROOT)), input_sha256=sha(inp), producer_sha256=sha(Path(mod.__file__)), box=list(box),
               prova_recepta_V119=dict(render=str(TIF119.relative_to(ROOT)), render_sha256=sha(TIF119), **prova),
               alpha_exact=bool(np.array_equal(alpha, orig)), alpha_different=int(np.count_nonzero(ad)), alpha_max_abs_DN=int(abs(ad).max()),
               alpha_font='recepta sobre el render de la V120 (el triangle buit ha crescut amb la vora del camp de la Sony deformada)',
               meaning='Presentation-only sky continuation; the alpha is the recipe output, proven equal to the V119/V115 alpha on the V119 render.')
(out / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
for cid in (0, 1, 2):
    raw = np.round(np.clip(rgb[..., cid], 0, 1) * 65535).astype('uint16'); np.save(out / f'raw_c{cid}.npy', raw); np.save(out / f'L301_c{cid}.npy', q_blocs(raw))
np.save(out / 'L301_alfa.npy', alpha)
print(json.dumps({k: receipt[k] for k in ('hipotenusa', 'triangle_px', 'alpha_exact', 'alpha_different', 'alpha_max_abs_DN', 'prova_recepta_V119')}, ensure_ascii=False), flush=True)
