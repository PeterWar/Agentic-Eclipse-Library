"""v1 (V106, Claude, 26-09-2026) · Verificació del PSB desat pel Photoshop contra la V105 (1-PHOTOSHOP/V105.psb, SHA 7b41181a…) i la capa nova:
  · les 42 capes de la V105: mateix ordre, mode, opacitat, caixa i píxels BYTE A BYTE, llevat de la 305 (només la visibilitat: oculta) i de la
    cantonada del logo (301, derivada: |dif| ≤ 2);
  · la capa nova 306 (Superposar, visible, 100 %, entre la 305 i la 258) = el ràster de c3 llevat de la quantització a 15 bits del Photoshop (|dif| ≤ 2).
Ús: v1_verifica_v106.py <psb V106> <CAPA_V106.npz> <sortida.json>. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
a = PSB(str(ARREL / '1-PHOTOSHOP/V105.psb')); b = PSB(sys.argv[1]); Z = np.load(sys.argv[2]); OUT = Path(sys.argv[3])
ida = [L['id'] for L in a.layers]; idb = [L['id'] for L in b.layers]; i305 = ida.index(305)
rep = dict(capes_V105=len(a.layers), capes_V106=len(b.layers), ordre_ok=idb == ida[:i305 + 1] + [306] + ida[i305 + 1:], iguals=[], diferents=[], derivades={})
LB = {L['id']: L for L in b.layers}
for La in a.layers:
    lid = La['id']; Lb = LB.get(lid)
    if Lb is None: rep['diferents'].append(dict(id=lid, motiu='falta')); continue
    meta_eq = all(La.get(k) == Lb.get(k) for k in ('blend', 'opacity', 'left', 'top', 'right', 'bottom')) and (La.get('visible') == Lb.get('visible') if lid != 305 else (not Lb.get('visible')))
    if lid == 301:
        dm = max(int(np.abs(a.channel(lid, c)[0].astype(np.int32) - b.channel(lid, c)[0].astype(np.int32)).max()) for c in La['chans'])
        rep['derivades'][lid] = dict(nom=La.get('name'), dif_max=dm, meta_igual=meta_eq); continue
    ok = meta_eq and set(La['chans']) == set(Lb['chans']) and all(np.array_equal(a.channel(lid, c)[0], b.channel(lid, c)[0]) for c in La['chans'])
    (rep['iguals'] if ok else rep['diferents']).append(dict(id=lid, nom=La.get('name')))
    if not ok: print('DIFERENT', lid, La.get('name'), flush=True)
N = LB.get(306)
if N:
    difs = {c: int(np.abs(b.channel(306, c)[0].astype(np.int32) - (Z['A16'] if c == -1 else Z['RGB16'][..., c]).astype(np.int32)).max()) for c in (-1, 0, 1, 2)}
    rep['capa_306'] = dict(nom=N.get('name'), mode=N.get('blend'), opacitat=N.get('opacity'), visible=N.get('visible'), caixa=[N['left'], N['top'], N['right'], N['bottom']], dif_max=difs,
                           passa=N.get('blend') == 'OVERLAY' and N.get('opacity') == 255 and bool(N.get('visible')) and max(difs.values()) <= 2)
rep['capa_305'] = dict(visible_V105=bool(next(L for L in a.layers if L['id'] == 305).get('visible')), visible_V106=bool(LB[305].get('visible')))
rep['veredicte'] = 'PASSA' if (rep['ordre_ok'] and not rep['diferents'] and rep.get('capa_306', {}).get('passa') and all(v['dif_max'] <= 2 and v['meta_igual'] for v in rep['derivades'].values())) else 'FALLA'
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str)); print(rep['veredicte'], 'iguals', len(rep['iguals']), 'diferents', rep['diferents'], 'capa_306', rep.get('capa_306'))
