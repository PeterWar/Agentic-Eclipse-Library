"""f8 (V120, 29-09-2026) · LES ESTRELLES A LA GEOMETRIA NOVA: el catàleg, la capa 202 (llum mesurada) i el mapa 203.
Amb la Sony deformada a la geometria de la Vixen, cada estrella del llenç es mou u = fA·u_A + (1 − fA)·u_B (la Sony combinada és fA·A + (1 − fA)·B; fA,
la fracció d'A congelada del control, a la posició vella). Les estrelles de la base ja són fora (la base és la linealitzada SENSE estrelles): la seva
llum només és a la 202.
  1. CATALEG_ACCEPTAT_V120.json: el de la V114 amb x, y transformats (x_V114, y_V114 i el desplaçament es conserven).
  2. La 202: cada segell (la caixa de 25 × 25 px de la recepta V65, amb la seva màscara; res de fora de la caixa, que als parells propers seria
     la veïna) es trasllada amb el SEU desplaçament, subpíxel (interpolació cúbica); la resta del llenç, a 0 (com a la V119). Comprovacions: la llum de cada estrella (suma RGB) es
     conserva dins de l'1 %; cap segell no en toca cap altre; fora dels segells, res.
  3. El mapa 203: m6_mapa_203_v2.py (V114) amb el catàleg nou i la mateixa llegenda.
Ús: f8_estrelles_v120.py <carpeta_f1 amb CAMP_V120.json> <carpeta_sortida>"""
import sys, json, subprocess, importlib.util, numpy as np, cv2
from pathlib import Path
F1, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
R = Path(__file__).resolve().parents[3]; H, W = 7506, 10551
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)
MODEL = json.load(open(F1 / 'CAMP_V120.json')); FA = np.load(R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_fA_v42.npy', mmap_mode='r')
def u_sony(x, y):
    f = float(np.clip(FA[int(np.clip(round(y), 0, H - 1)), int(np.clip(round(x), 0, W - 1))], 0, 1))
    a = cv.camp(MODEL, 'A', np.array([x]), np.array([y])); b = cv.camp(MODEL, 'B', np.array([x]), np.array([y]))
    return f * a[0][0] + (1 - f) * b[0][0], f * a[1][0] + (1 - f) * b[1][0]
# 1. el catàleg
CAT = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))
for s in CAT['stars']:
    ux, uy = u_sony(s['x'], s['y']); s['x_V114'], s['y_V114'] = s['x'], s['y']; s['x'], s['y'] = s['x'] + ux, s['y'] + uy; s['desplacament_V120_px'] = [round(ux, 3), round(uy, 3)]
CAT['geometria'] = 'V120: la Sony deformada a la geometria de la Vixen (camp_v120, u = fA·u_A + (1 − fA)·u_B); x_V114, y_V114 = les posicions de la V114'
json.dump(CAT, open(OUT / 'CATALEG_ACCEPTAT_V120.json', 'w'), ensure_ascii=False, indent=1)
# 2. la 202
p = PSB(str(R / '1-PHOTOSHOP/V119.psb')); L = p.layer(202); assert (L['left'], L['top'], L['right'], L['bottom']) == (0, 0, W, H)
CH = {k: p.channel(202, c)[0] for k, c in (('R', 0), ('G', 1), ('B', 2), ('A', -1), ('M', -2))}
for k, a in CH.items(): assert a.shape == (H, W), (k, a.shape)
NOU = {k: np.zeros((H, W), a.dtype) for k, a in CH.items()}; ocupat = np.zeros((H, W), bool); rep = dict(guio=str(Path(__file__).relative_to(R)), estrelles=[])
suport_vell = (CH['M'] > 0) | (CH['R'] > 0) | (CH['G'] > 0) | (CH['B'] > 0); cobert = np.zeros((H, W), bool)
for s in CAT['stars']:
    xo, yo = s['x_V114'], s['y_V114']; xn, yn = s['x'], s['y']; xi, yi = int(round(xo)), int(round(yo)); hw = 14
    ys, xs = slice(yi - hw, yi + hw + 1), slice(xi - hw, xi + hw + 1); cobert[yi - 12:yi + 13, xi - 12:xi + 13] = True
    caixa = np.zeros((2 * hw + 1, 2 * hw + 1), bool); caixa[hw - 12:hw + 13, hw - 12:hw + 13] = True     # el segell: la caixa de 25 × 25 px de la V65 (res de les veïnes)
    # la finestra vella, traslladada: el centre vell (xo, yo) va a (xn, yn); es pinta a la finestra nova centrada a round(xn), round(yn)
    xj, yj = int(round(xn)), int(round(yn)); dx, dy = (xn - xj) - (xo - xi), (yn - yj) - (yo - yi)      # translació subpíxel residual
    Mt = np.float32([[1, 0, dx], [0, 1, dy]]); ysn, xsn = slice(yj - hw, yj + hw + 1), slice(xj - hw, xj + hw + 1)
    llum_abans = {k: float(np.where(caixa, CH[k][ys, xs], 0).astype(np.float64).sum()) for k in 'RGB'}
    for k, a in CH.items():
        w = np.where(caixa, a[ys, xs], 0).astype(np.float32); interp = cv2.INTER_CUBIC if k in 'RGB' else cv2.INTER_LINEAR
        t = cv2.warpAffine(w, Mt, (w.shape[1], w.shape[0]), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if k in 'RGB': t = np.clip(t, 0, None)
        if k == 'M': t = np.where(t >= 0.5 * (w.max() if w.max() > 0 else 1), w.max(), 0)
        tq = np.clip(np.round(t), 0, np.iinfo(a.dtype).max).astype(a.dtype)
        zona = (tq > 0) if k in 'RGBM' else (tq > 0)
        assert not (ocupat[ysn, xsn] & zona).any() or k != 'R', f"l'estrella {s.get('id', s.get('TYC'))} en toca una altra"
        NOU[k][ysn, xsn] = np.where(zona, tq, NOU[k][ysn, xsn])
    ocupat[ysn, xsn] |= NOU['R'][ysn, xsn] > 0
    llum_despres = {k: float(NOU[k][ysn, xsn].astype(np.float64).sum()) for k in 'RGB'}
    rep['estrelles'].append(dict(id=s.get('id'), TYC=s.get('TYC'), de=[round(xo, 2), round(yo, 2)], a=[round(xn, 2), round(yn, 2)], desplacament_px=s['desplacament_V120_px'],
                                 llum_relativa={k: round(llum_despres[k] / max(llum_abans[k], 1), 4) for k in 'RGB'}))
# fora dels segells no hi havia res (si no, s'ha de saber)
fora = suport_vell & ~cobert; rep['pixels_fora_dels_segells_a_la_V119'] = int(fora.sum())
# l'alfa de la capa: la de la V119 fora dels segells (si era plena, plena)
alfa_plena = bool((CH['A'] == CH['A'].max()).mean() > 0.999); rep['alfa_V119_plena'] = alfa_plena
if alfa_plena: NOU['A'][:] = CH['A'].max()
llums = np.array([[e['llum_relativa'][k] for k in 'RGB'] for e in rep['estrelles']]); rep['llum_relativa_min_max'] = [round(float(llums.min()), 4), round(float(llums.max()), 4)]
np.savez_compressed(OUT / 'estrelles_202_V120.npz', **NOU); json.dump(rep, open(OUT / 'ESTRELLES_202_V120.json', 'w'), ensure_ascii=False, indent=1)
print('202:', len(rep['estrelles']), 'estrelles · llum relativa', rep['llum_relativa_min_max'], '· píxels fora dels segells a la V119', rep['pixels_fora_dels_segells_a_la_V119'], '· alfa plena', alfa_plena)
# 3. el mapa 203
r = subprocess.run([sys.executable, str(R / '3-RECERCA/tools/v114_estrelles_20260928/m6_mapa_203_v2.py'), str(OUT / 'mapa_203_V120.npz'), '--cataleg', str(OUT / 'CATALEG_ACCEPTAT_V120.json'),
                    '--llegenda', str(R / '4-RESULTATS/v114_estrelles_20260928/mapa/llegenda_V114.json')], capture_output=True, text=True)
print('203:', r.returncode, r.stdout[-600:], r.stderr[-600:])
