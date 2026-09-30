"""f9 (V120, 29-09-2026) · LES CAPES DE BRNO ENCAIXADES PER ESTRELLES (230, 231, 232; ocultes) A LA GEOMETRIA NOVA.
Es van encaixar a les NOSTRES estrelles (V113/V114), que eren a la geometria de la Sony. Amb la Sony deformada a la de la Vixen, les estrelles es
mouen u = fA·u_A + (1 − fA)·u_B; perquè Brno continuï encaixant amb les nostres estrelles, cada capa es deforma amb el mateix camp:
Brno'(q) = Brno(q − u(q)) (bilineal; l'alfa es remostreja igual). Mateix marc de capa que a la V119. La 233 (Trigaza, «alineada») i la 62 (LROC)
no es toquen.
Sortides: <carpeta>/L{230,231,232}.npz (R, G, B, A, bbox) per al muntatge, i F9_REBUT.json.
Ús: f9_brno_v120.py <carpeta_f1 amb CAMP_V120.json> <carpeta_sortida>"""
import sys, json, importlib.util, numpy as np, cv2
from pathlib import Path
F1, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
R = Path(__file__).resolve().parents[3]; H, W = 7506, 10551
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)
MODEL = json.load(open(F1 / 'CAMP_V120.json')); FA = np.load(R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_fA_v42.npy', mmap_mode='r')
mx = np.empty((H, W), np.float32); my = np.empty((H, W), np.float32); xs = np.arange(W, dtype=np.float64)
for y0 in range(0, H, 256):
    yy = np.arange(y0, min(H, y0 + 256), dtype=np.float64)[:, None] * np.ones((1, W)); xx = np.ones((len(yy), 1)) * xs[None, :]
    f = np.clip(np.asarray(FA[y0:y0 + len(yy)], np.float64), 0, 1)
    ua = cv.camp(MODEL, 'A', xx, yy); ub = cv.camp(MODEL, 'B', xx, yy); ux = f * ua[0] + (1 - f) * ub[0]; uy = f * ua[1] + (1 - f) * ub[1]
    mx[y0:y0 + len(yy)] = xx - ux; my[y0:y0 + len(yy)] = yy - uy
p = PSB(str(R / '1-PHOTOSHOP/V119.psb')); rep = dict(guio=str(Path(__file__).relative_to(R)), capes={})
for lid in (230, 231, 232):
    L = p.layer(lid); x0, y0, x1, y1 = L['left'], L['top'], L['right'], L['bottom']; out = {}
    for k, c in (('R', 0), ('G', 1), ('B', 2), ('A', -1)):
        a, org = p.channel(lid, c); assert org == (x0, y0) and a.shape == (y1 - y0, x1 - x0), (lid, c, org, a.shape)
        full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = a
        wv = cv2.remap(full, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[y0:y1, x0:x1]
        out[k] = np.clip(np.round(wv), 0, np.iinfo(a.dtype).max).astype(a.dtype)
    np.savez_compressed(OUT / f'L{lid}.npz', **out, bbox=np.array([x0, y0, x1, y1]))
    rep['capes'][str(lid)] = dict(bbox=[x0, y0, x1, y1], alfa_mitjana_abans=float(p.channel(lid, -1)[0].mean()), alfa_mitjana_despres=float(out['A'].mean()))
    print(lid, rep['capes'][str(lid)], flush=True)
json.dump(rep, open(OUT / 'F9_REBUT.json', 'w'), ensure_ascii=False, indent=1)
