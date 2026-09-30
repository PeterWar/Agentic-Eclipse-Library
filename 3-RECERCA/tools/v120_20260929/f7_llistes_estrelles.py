"""f7 (V120, 29-09-2026) · LES LLISTES D'ESTRELLES DE LA D4, A LA GEOMETRIA NOVA (la Sony deformada a la Vixen).
La D4 extreu les estrelles de tres fonts (fusió, Vixen, Sony) a les posicions de tres llistes, totes en la geometria VELLA (la de la Sony):
  · D3_empirical_pilot.json (53 files; se'n seleccionen les que repeteixen a A i B, les independents als dos trens o les brillants a < 6 px del catàleg);
  · estrelles_v42.json (les 21 confirmades de la V42);
  · EXTRA_ESTRELLES_V114.json (45: 17 canòniques i 28 «còpies Vixen», les estrelles que la Vixen, girada respecte de la Sony, posava 10–12 px al costat).
Transformació: posició nova = vella + u(vella), amb u = fA·u_A + (1 − fA)·u_B (la Sony combinada és fA·A + (1 − fA)·B; fA, la fracció d'A congelada del
control, a la posició vella). Les mesures pròpies d'A i de B van amb el seu camp; les de la Vixen no es mouen (ja són a la geometria de la Vixen).
Les 28 còpies Vixen VELLES es treuen (amb la Sony a la geometria de la Vixen, cada una cau damunt de la seva canònica). PERÒ la D4 no aplica les
canòniques noves a la font Vixen («còpies Vixen no a la Sony; canòniques noves no a la Vixen»): a la V114 la Vixen les perdia a través de les còpies. Per
mantenir aquesta lògica, cada canònica nova porta ara la seva còpia Vixen a la MATEIXA posició transformada (la fusió en fa dues extraccions
seqüencials; la segona no troba res).
Ús: f7_llistes_estrelles.py <carpeta_f1 amb CAMP_V120.json> <carpeta_sortida>"""
import sys, json, importlib.util, numpy as np
from pathlib import Path
F1, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
R = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)
MODEL = json.load(open(F1 / 'CAMP_V120.json'))
H_ = R / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
FA = np.load(R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_fA_v42.npy', mmap_mode='r')
def u_de(X, x, y):
    ux, uy = cv.camp(MODEL, X, np.array([x], float), np.array([y], float)); return float(ux[0]), float(uy[0])
def u_sony(x, y):
    xi, yi = int(np.clip(round(x), 0, FA.shape[1] - 1)), int(np.clip(round(y), 0, FA.shape[0] - 1)); f = float(np.clip(FA[yi, xi], 0, 1))
    a, b = u_de('A', x, y), u_de('B', x, y); return f * a[0] + (1 - f) * b[0], f * a[1] + (1 - f) * b[1]
def mou(d, u, clau_x='x', clau_y='y', enter=True):
    x, y = float(d[clau_x]), float(d[clau_y]); ux, uy = u(x, y); d['x_vella'], d['y_vella'] = x, y
    d[clau_x], d[clau_y] = (int(round(x + ux)), int(round(y + uy))) if enter else (x + ux, y + uy); return (ux, uy)
rep = dict(guio=str(Path(__file__).relative_to(R)), camp=str((F1 / 'CAMP_V120.json').relative_to(R)), moviments_px={})
# 1. D3_empirical_pilot
D3 = json.load(open(H_ / 'star_models_round1/products/D3_empirical_pilot.json')); mov = []
for row in D3:
    s = row['star']; mov.append(np.hypot(*mou(s, u_sony)))
    if 'pred' in s: x, y = s['pred']; ux, uy = u_sony(x, y); s['pred'] = [x + ux, y + uy]
    if isinstance(s.get('sony'), dict): mou(s['sony'], u_sony)
    for k, X in (('sonyA', 'A'), ('sonyB', 'B')):
        if isinstance(row.get(k), dict): mou(row[k], lambda x, y, X=X: u_de(X, x, y))
json.dump(D3, open(OUT / 'D3_empirical_pilot.json', 'w'), ensure_ascii=False, indent=0); rep['moviments_px']['D3'] = [round(float(np.median(mov)), 2), round(float(np.max(mov)), 2)]
# 2. estrelles_v42
V42 = json.load(open(H_ / 'star_catalog_round1/products/estrelles_v42.json')); mov = [np.hypot(*mou(s, u_sony)) for s in V42['estrelles']]
json.dump(V42, open(OUT / 'estrelles_v42.json', 'w'), ensure_ascii=False, indent=0); rep['moviments_px']['estrelles_v42'] = [round(float(np.median(mov)), 2), round(float(np.max(mov)), 2)]
# 3. EXTRA_ESTRELLES_V114: fora les còpies Vixen; les canòniques, transformades
EX = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/fantasmes/EXTRA_ESTRELLES_V114.json')); nou = []; mov = []
for e in EX:
    if e.get('vixen_copy'): continue
    ux, uy = u_sony(float(e.get('xf', e['x'])), float(e.get('yf', e['y']))); mov.append(np.hypot(ux, uy))
    e2 = dict(e, x_vella=e['x'], y_vella=e['y']); e2['x'], e2['y'] = int(round(e['x'] + ux)), int(round(e['y'] + uy))
    if 'xf' in e: e2['xf'], e2['yf'] = e['xf'] + ux, e['yf'] + uy
    nou.append(e2); nou.append(dict(e2, vixen_copy=True, copia_de=e.get('copia_de', e.get('id', 'canònica nova')), nota='còpia Vixen V120: la mateixa posició que la canònica'))
json.dump(nou, open(OUT / 'EXTRA_ESTRELLES_V120.json', 'w'), ensure_ascii=False, indent=0)
rep['EXTRA'] = dict(abans=len(EX), copies_vixen_velles_tretes=sum(1 for e in EX if e.get('vixen_copy')), canoniques=sum(1 for e in nou if not e.get('vixen_copy')), copies_vixen_noves=sum(1 for e in nou if e.get('vixen_copy'))); rep['moviments_px']['EXTRA'] = [round(float(np.median(mov)), 2), round(float(np.max(mov)), 2)]
json.dump(rep, open(OUT / 'F7_REBUT.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(rep, ensure_ascii=False))
