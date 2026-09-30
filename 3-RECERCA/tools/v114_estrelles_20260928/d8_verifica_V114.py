"""d8 (còpia de d6 per a la V114: «V112» = 1-PHOTOSHOP/V114.psb, «candidata» = el pas final v114, «V111» = 1-PHOTOSHOP/V113.psb; les capes de Brno també protegides) · Verificació de 1-PHOTOSHOP/V112.psb (Claude, 28-09-2026). Només lectura.
1. Mateix inventari i ordre de capes que la candidata del Codex; mateixos modes, opacitats, visibilitat, clipping, marcs i màscares;
   noms iguals llevat de 41/42/45/46 (V112).
2. Tots els canals (RGB, alfa, màscara) de totes les capes idèntics als de la candidata.
3. Les capes manuals i protegides de Pere (234, 308, 202, 96, 224, 258, 76, 267, 305, 306, 239–244, 412 i les referències) idèntiques a la V111.
4. El compost desat (ImageData) idèntic al render natiu visible_complet.tif i al de la candidata desada pel Codex.
Escriu 4-RESULTATS/v112_claude_20260928/VERIFICACIO_V112.json."""
from pathlib import Path
import sys, json, hashlib
import numpy as np, tifffile
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()

V112 = R / '1-PHOTOSHOP/V114.psb'; CAND = R / '4-RESULTATS/v114_estrelles_20260928/stage_final_c.psb'; V111 = R / '1-PHOTOSHOP/V113.psb'
out = dict(fitxer=str(V112.relative_to(R)), sha256=sha(V112), bytes=V112.stat().st_size,
           candidata=dict(fitxer=str(CAND.relative_to(R)), sha256=sha(CAND)), v111=dict(fitxer=str(V111.relative_to(R)), sha256=sha(V111)))
a, c, v = PSB(str(V112)), PSB(str(CAND)), PSB(str(V111))
out['mida'] = [a.width, a.height, a.depth, a.channels]
ids_a = [l['id'] for l in a.layers]; ids_c = [l['id'] for l in c.layers]
out['ordre_igual_a_la_candidata'] = ids_a == ids_c
REN = set()
props = []
for la, lc in zip(a.layers, c.layers):
    for k in ('left', 'top', 'right', 'bottom', 'visible', 'opacity', 'blend', 'clipping', 'mask'):
        if la[k] != lc[k]: props.append(dict(id=la['id'], camp=k, v112=la[k], candidata=lc[k]))
    if la['name'] != lc['name'] and la['id'] not in REN: props.append(dict(id=la['id'], camp='name', v112=la['name'], candidata=lc['name']))
out['propietats_diferents'] = props
out['noms_nous'] = {l['id']: l['name'] for l in a.layers if l['id'] in REN}
dif = []; n = 0
for la in a.layers:
    lc = c.layer(la['id'])
    if sorted(la['chans']) != sorted(lc['chans']): dif.append(dict(id=la['id'], problema='canals', v112=sorted(la['chans']), cand=sorted(lc['chans']))); continue
    for cid in la['chans']:
        x, _ = a.channel(la['id'], cid); y, _ = c.channel(la['id'], cid); n += 1
        if x is None or y is None or x.shape != y.shape or not np.array_equal(x, y): dif.append(dict(id=la['id'], canal=cid))
out['canals_comprovats'] = n; out['canals_diferents_de_la_candidata'] = dif
PROT = [234, 308, 96, 224, 258, 76, 267, 305, 306, 239, 240, 241, 242, 243, 244, 412, 62, 233, 230, 231, 232]   # 202 i 203 canvien (S57–S60 retirades; mapa refet)
pd = []; m = 0
for lid in PROT:
    la, lv = a.layer(lid), v.layer(lid)
    for k in ('left', 'top', 'right', 'bottom', 'opacity', 'blend', 'clipping', 'mask'):
        if la[k] != lv[k]: pd.append(dict(id=lid, camp=k))
    if la['visible'] != lv['visible'] and lid != 412: pd.append(dict(id=lid, camp='visible'))
    for cid in lv['chans']:
        x, _ = a.channel(lid, cid); y, _ = v.channel(lid, cid); m += 1
        if x is None or y is None or x.shape != y.shape or not np.array_equal(x, y): pd.append(dict(id=lid, canal=cid))
out['protegides_comprovades'] = dict(capes=PROT, canals=m, diferencies_amb_V111=pd)
_ids_v = {l['id'] for l in v.layers}
out['capes_noves'] = sorted(l['id'] for l in a.layers if l['id'] not in _ids_v)
out['canviades_respecte_V111'] = sorted({l['id'] for l in a.layers if l['id'] in _ids_v for cid in l['chans']
                                         if not np.array_equal(a.channel(l['id'], cid)[0], v.channel(l['id'], cid)[0])})
comp = a.composite()[..., :3]
tif = tifffile.imread(R / '4-RESULTATS/v114_estrelles_20260928/V114_natiu/visible_complet.tif')
cand_tif = tifffile.imread(R / '4-RESULTATS/v114_estrelles_20260928/V114_natiu/visible_complet.tif')
out['compost_igual_al_render_natiu'] = bool(np.array_equal(comp, tif))
out['compost_igual_al_render_de_la_candidata'] = bool(np.array_equal(comp, cand_tif))
out['dif_max_compost_vs_render'] = int(np.abs(comp.astype(np.int32) - tif.astype(np.int32)).max())
out['veredicte'] = 'PASSA' if (out['ordre_igual_a_la_candidata'] and not props and not dif and not pd and out['compost_igual_al_render_natiu']) else 'FALLA'
(R / '4-RESULTATS/v114_estrelles_20260928/VERIFICACIO_V114.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({k: out[k] for k in out if k not in ('protegides_comprovades',)}, indent=1, ensure_ascii=False)[:4000])
print('protegides:', len(PROT), 'capes,', m, 'canals, diferències:', pd)
