"""m5 · V114 (Claude, 28-09-2026, nit): treu de la capa 202 (estrelles pintades amb la recepta V65, s24_star_package.py: cada estrella és una
caixa de 25×25 px assignada al llenç, i la màscara és el suport dels píxels pintats) les estrelles de --treu, posant a 0 la seva caixa a RGB i a la
màscara. Comprova abans que cap altra estrella pintada no toqui aquella caixa. La resta de la capa queda byte a byte igual a la V113.
Sortida: npz (R, G, B, A, M) del llenç sencer per a m3_munta_v114.py --c202, i un rebut JSON amb la llum treta per estrella."""
import sys, json, argparse
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--treu', nargs='+', required=True); A = ap.parse_args()
cat = {s['id']: s for s in json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text())['stars']}
p = PSB(str(R / '1-PHOTOSHOP/V113.psb'))
ch = {k: p.channel(202, c)[0].copy() for k, c in (('R', 0), ('G', 1), ('B', 2), ('A', -1), ('M', -2))}
rebut = dict(font='1-PHOTOSHOP/V113.psb capa 202', tretes=[])
for sid in A.treu:
    s = cat[sid]; x, y = int(round(s['x'])), int(round(s['y'])); y0, y1, x0, x1 = y - 12, y + 13, x - 12, x + 13
    for oid, o in cat.items():
        if oid in A.treu: continue
        ox, oy = int(round(o['x'])), int(round(o['y']))
        assert not (abs(ox - x) <= 24 and abs(oy - y) <= 24), f'{sid}: la caixa toca la de {oid}'
    llum = {k: int(ch[k][y0:y1, x0:x1].astype(np.int64).sum()) for k in 'RGB'}
    for k in 'RGB': ch[k][y0:y1, x0:x1] = 0
    ch['M'][y0:y1, x0:x1] = 0
    veinat = (slice(y - 30, y + 31), slice(x - 30, x + 31))            # cap resta de l'estrella fora de la caixa
    assert not ch['M'][veinat].any() and not any(ch[k][veinat].any() for k in 'RGB'), f'{sid}: queda llum o màscara fora de la caixa'
    rebut['tretes'].append(dict(id=sid, x=s['x'], y=s['y'], V=s['V'], caixa=[x0, y0, x1, y1], llum_treta=llum, pic_display=s['display_peak']))
np.savez_compressed(A.sortida, **ch)
Path(A.sortida).with_suffix('.json').write_text(json.dumps(rebut, indent=1, ensure_ascii=False)); print(json.dumps(rebut, ensure_ascii=False))
