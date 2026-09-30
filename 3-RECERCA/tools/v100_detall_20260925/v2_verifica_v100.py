"""v2 (V100 detall) · Verificació del PSB desat pel Photoshop: totes les capes de la V99 (1-PHOTOSHOP/V99.psb) hi han de ser BYTE A BYTE (mateix
ordre, mode, opacitat i visibilitat), més la capa nova 302 (mode Superposar, visible, just damunt de la 56 i sota la 258) amb el contingut de la
font (CAPA_…npz) llevat de la quantització a 15 bits (|dif| ≤ 2). Ús: v2_verifica_v100.py <V100.psb> <capa.npz> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
V100, NPZ, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
a = PSB(str(ARREL / '1-PHOTOSHOP/V99.psb')); b = PSB(str(V100)); ia = [L['id'] for L in a.layers]; ib = [L['id'] for L in b.layers]
rep = dict(ordre_ok=(ib == ia[:ia.index(56) + 1] + [302] + ia[ia.index(56) + 1:]), iguals=0, diferents=[])
for La in a.layers:
    Lb = [x for x in b.layers if x['id'] == La['id']][0]; meta = all(La.get(k) == Lb.get(k) for k in ('blend', 'opacity', 'visible', 'left', 'top', 'right', 'bottom'))
    ok = meta and set(La['chans']) == set(Lb['chans']) and all(np.array_equal(a.channel(La['id'], c)[0], b.channel(La['id'], c)[0]) for c in La['chans'])
    if ok: rep['iguals'] += 1
    else: rep['diferents'].append(dict(id=La['id'], nom=La.get('name'))); print('DIFERENT', La['id'], La.get('name'), flush=True)
Z = np.load(NPZ); g = np.clip(0.5 + Z['delta'] * (Z['alfa'] > 0), 0, 1); G16 = np.round(g * 65535).astype(np.int32); G16[Z['alfa'] <= 0] = 32768; A16 = np.round(np.clip(Z['alfa'], 0, 1) * 65535).astype(np.int32)
L = [x for x in b.layers if x['id'] == 302][0]; rep['capa_nova'] = dict(nom=L.get('name'), mode=str(L.get('blend')), opacitat=L.get('opacity'), visible=L.get('visible'), caixa=[L['left'], L['top'], L['right'], L['bottom']],
    dif_max_G=int(np.abs(b.channel(302, 1)[0].astype(np.int32) - G16).max()), dif_max_alfa=int(np.abs(b.channel(302, -1)[0].astype(np.int32) - A16).max()))
rep['veredicte'] = 'PASSA' if (rep['ordre_ok'] and not rep['diferents'] and rep['capa_nova']['dif_max_G'] <= 2 and rep['capa_nova']['dif_max_alfa'] <= 2 and rep['capa_nova']['visible']) else 'FALLA'
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str)); print(json.dumps(rep, ensure_ascii=False, default=str))
