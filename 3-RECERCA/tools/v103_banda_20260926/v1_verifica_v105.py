"""v1 (V105) · Verificació del PSB desat pel Photoshop (1-PHOTOSHOP/V105.psb) contra la V104: totes les capes de la V104 byte a byte (píxels, mode,
opacitat, visibilitat), llevat de la cantonada 301 (derivada, |dif| ≤ 2); la capa nova 303 = la capa.npz (|dif| ≤ 2 per la quantització), Normal,
100 %, visible, entre la 302 i la 258. Ús: v1_verifica_v105.py <capa.npz> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
Z = np.load(sys.argv[1]); OUT = Path(sys.argv[2])
a = PSB(str(ARREL / '1-PHOTOSHOP/V104.psb')); b = PSB(str(ARREL / '1-PHOTOSHOP/V105.psb')); rep = dict(capes_V104=len(a.layers), capes_V105=len(b.layers), diferents=[], derivades={})
ida = [L['id'] for L in a.layers]; idb = [L['id'] for L in b.layers]; rep['ordre_ok'] = (idb == ida[:ida.index(302) + 1] + [303] + ida[ida.index(302) + 1:])
for La in a.layers:
    lid = La['id']; Lb = b.layer(lid); meta_eq = all(La.get(k) == Lb.get(k) for k in ('blend', 'opacity', 'visible', 'left', 'top', 'right', 'bottom') if k in La)
    if lid == 301:
        dm = max(int(np.abs(a.channel(lid, c)[0].astype(np.int32) - b.channel(lid, c)[0].astype(np.int32)).max()) for c in La['chans']); rep['derivades'][lid] = dict(dif_max=dm, meta_igual=meta_eq); continue
    ok = meta_eq and set(La['chans']) == set(Lb['chans']) and all(np.array_equal(a.channel(lid, c)[0], b.channel(lid, c)[0]) for c in La['chans'])
    if not ok: rep['diferents'].append(dict(id=lid, nom=La.get('name')))
L3 = b.layer(303); r = dict(nom=L3.get('name'), mode=str(L3.get('blend')), opacitat=L3.get('opacity'), visible=bool(L3.get('visible')), caixa=[L3['left'], L3['top'], L3['right'], L3['bottom']])
for c in (0, 1, 2): r[f'dif_max_canal_{c}'] = int(np.abs(b.channel(303, c)[0].astype(np.int32) - Z['RGB16'][..., c].astype(np.int32)).max())
r['dif_max_alfa'] = int(np.abs(b.channel(303, -1)[0].astype(np.int32) - Z['A16'].astype(np.int32)).max()); rep['capa_303'] = r
rep['veredicte'] = 'PASSA' if (rep['ordre_ok'] and not rep['diferents'] and all(v['dif_max'] <= 2 and v['meta_igual'] for v in rep['derivades'].values()) and r['visible'] and 'NORMAL' in r['mode'].upper() and r['opacitat'] == 255 and max(r[f'dif_max_canal_{c}'] for c in (0, 1, 2)) <= 2 and r['dif_max_alfa'] <= 2) else 'FALLA'
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str)); print(rep['veredicte'], 'diferents', rep['diferents'], 'capa 303', r)
