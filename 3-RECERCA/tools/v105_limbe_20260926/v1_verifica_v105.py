"""v1 (V105) · Verificació del PSB desat pel Photoshop contra la V104 de Pere (1-PHOTOSHOP/V104.psb, SHA da2b0792…) i la capa nova:
  · les 41 capes de la V104: mateix ordre, mode, opacitat, caixa i píxels BYTE A BYTE, llevat de la 303 (només la visibilitat: oculta), de la
    cantonada del logo (301, derivada: |dif| ≤ 2) i de la 56 (RGB = el canal nou de c0, |dif| ≤ 2; alfa, màscara i la resta, byte a byte);
  · la capa nova 305 (Superposar, visible, 100 %, entre la 302 i la 258) = el ràster de c3 llevat de la quantització a 15 bits del Photoshop (|dif| ≤ 2).
Ús: v1_verifica_v105.py <psb V105> <CAPA_V105.npz> <sortida.json> [<L56_G_V105_psb.npy>]. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
a = PSB(str(ARREL / '1-PHOTOSHOP/V104.psb')); b = PSB(sys.argv[1]); Z = np.load(sys.argv[2]); OUT = Path(sys.argv[3]); G56 = np.load(sys.argv[4]) if len(sys.argv) > 4 else None
ida = [L['id'] for L in a.layers]; idb = [L['id'] for L in b.layers]; i302 = ida.index(302)
rep = dict(capes_V104=len(a.layers), capes_V105=len(b.layers), ordre_ok=idb == ida[:i302 + 1] + [305] + ida[i302 + 1:], iguals=[], diferents=[], derivades={})
LB = {L['id']: L for L in b.layers}
for La in a.layers:
    lid = La['id']; Lb = LB.get(lid)
    if Lb is None: rep['diferents'].append(dict(id=lid, motiu='falta')); continue
    meta_eq = all(La.get(k) == Lb.get(k) for k in ('blend', 'opacity', 'left', 'top', 'right', 'bottom')) and (La.get('visible') == Lb.get('visible') if lid != 303 else (La.get('visible') and not Lb.get('visible')))
    if lid == 301:
        dm = max(int(np.abs(a.channel(lid, c)[0].astype(np.int32) - b.channel(lid, c)[0].astype(np.int32)).max()) for c in La['chans'])
        rep['derivades'][lid] = dict(nom=La.get('name'), dif_max=dm, meta_igual=meta_eq); continue
    if lid == 56 and G56 is not None:
        dmax = max(int(np.abs(b.channel(56, c)[0].astype(np.int32) - G56.astype(np.int32)).max()) for c in (0, 1, 2))
        igual_resta = all(np.array_equal(a.channel(56, c)[0], b.channel(56, c)[0]) for c in La['chans'] if c not in (0, 1, 2))
        rep['capa_56'] = dict(nom_V104=La.get('name'), nom_V105=Lb.get('name'), rgb_dif_max_contra_c0=dmax, alfa_mascara_iguals=igual_resta, meta_igual=meta_eq, passa=bool(dmax <= 2 and igual_resta and meta_eq))
        (rep['iguals'] if rep['capa_56']['passa'] else rep['diferents']).append(dict(id=56, nom=Lb.get('name'), canvi='RGB nou (c0)')); continue
    ok = meta_eq and set(La['chans']) == set(Lb['chans']) and all(np.array_equal(a.channel(lid, c)[0], b.channel(lid, c)[0]) for c in La['chans'])
    (rep['iguals'] if ok else rep['diferents']).append(dict(id=lid, nom=La.get('name')))
    if not ok: print('DIFERENT', lid, La.get('name'), flush=True)
N = LB.get(305)
if N:
    difs = {c: int(np.abs(b.channel(305, c)[0].astype(np.int32) - (Z['A16'] if c == -1 else Z['RGB16'][..., c]).astype(np.int32)).max()) for c in (-1, 0, 1, 2)}
    rep['capa_305'] = dict(nom=N.get('name'), mode=N.get('blend'), opacitat=N.get('opacity'), visible=N.get('visible'), caixa=[N['left'], N['top'], N['right'], N['bottom']], dif_max=difs,
                           passa=N.get('blend') == 'OVERLAY' and N.get('opacity') == 255 and bool(N.get('visible')) and max(difs.values()) <= 2)
rep['capa_303'] = dict(visible_V104=bool(next(L for L in a.layers if L['id'] == 303).get('visible')), visible_V105=bool(LB[303].get('visible')))
rep['veredicte'] = 'PASSA' if (rep['ordre_ok'] and not rep['diferents'] and rep.get('capa_305', {}).get('passa') and all(v['dif_max'] <= 2 and v['meta_igual'] for v in rep['derivades'].values())) else 'FALLA'
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str)); print(rep['veredicte'], 'iguals', len(rep['iguals']), 'diferents', rep['diferents'], 'capa_305', rep.get('capa_305'))
