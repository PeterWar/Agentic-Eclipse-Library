"""r2 (V97) · Extreu de la V96 els ràsters de referència a 4-RESULTATS/v97_refundacio_20260924/v96_ref/ (uint16, llenç sencer o caixa de la capa):
- per capa: RGB (o G si els tres canals són iguals), alfa (-1) i màscara de capa (-2), amb les propietats a CAPES_V96.json;
- la base (3) i les capes de Brno (230–233) en RGB; els filtres en un canal.
Només llegeix la V96. Serveix per al jutge (F0), per ajustar la corba de la base nova i per comparar cada filtre nou amb el seu antecessor."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
SORT = ARREL / '4-RESULTATS/v97_refundacio_20260924/v96_ref'; SORT.mkdir(parents=True, exist_ok=True)
p = PSB(str(ARREL / '1-PHOTOSHOP/V96.psb')); W, H = p.width, p.height
props = {}
for L in p.layers:
    lid = L['id']; bbox = (L['left'], L['top'], L['right'], L['bottom'])
    props[lid] = dict(nom=L['name'], visible=L['visible'], opacitat=L['opacity'], mode=L['blend'], bbox=bbox,
                      mascara=None if L['mask'] is None else {k: (v if isinstance(v, (int, float, str, bool)) or v is None else str(v)) for k, v in L['mask'].items()})
    if bbox[2] <= bbox[0] or lid in (269, 203, 62): continue  # capes d'ajust (buides), marques i referències que no calen
    box = (0, 0, W, H) if (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) > 0.5 * W * H else bbox
    rgb = [p.channel_box(lid, c, box) for c in range(3)]
    if np.array_equal(rgb[0], rgb[1]) and np.array_equal(rgb[1], rgb[2]): np.save(SORT / f'L{lid}_G.npy', rgb[1]); props[lid]['canals'] = 'G'
    else: np.save(SORT / f'L{lid}_RGB.npy', np.stack(rgb, -1)); props[lid]['canals'] = 'RGB'
    if -1 in L['chans']: np.save(SORT / f'L{lid}_alfa.npy', p.channel_box(lid, -1, box))
    if L['mask'] is not None and -2 in L['chans']:
        np.save(SORT / f'L{lid}_mascara.npy', p.channel_box(lid, -2, box, fill=65535 if L['mask']['background'] == 255 else 0))
    props[lid]['caixa_desada'] = box; print(lid, props[lid]['canals'], box, flush=True)
(SORT / 'CAPES_V96.json').write_text(json.dumps(dict(font='1-PHOTOSHOP/V96.psb', llenc=[W, H], ordre_de_baix_a_dalt=[L['id'] for L in p.layers], capes=props), ensure_ascii=False, indent=1) + '\n')
print('FET')
