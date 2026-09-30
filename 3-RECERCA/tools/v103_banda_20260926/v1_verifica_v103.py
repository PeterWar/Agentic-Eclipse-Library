"""v1 (V103 banda) · Verificació del PSB desat pel Photoshop (1-PHOTOSHOP/V103.psb) contra la V101 (1-PHOTOSHOP/V101.psb) i l'estat de la V103:
  · capes fora dels 16 filtres: byte a byte iguals a la V101 (inclosa la base 3, que és idèntica), llevat de la cantonada del logo (301), que és
    DERIVADA i es regenera en desar: se n'informa a part (mostres de canal diferents i diferència màxima; passa si |dif| ≤ 2);
  · filtres 41–56: G, alfa i màscara = els de l'estat, llevat de la quantització a 15 bits del Photoshop (|dif| ≤ 2 en u16);
  · noms: «· V9x/V10x» → «· V103»; la 302 passa a oculta (només la visibilitat); mode, opacitat i visibilitat iguals a la V101.
Ús: v1_verifica_v99.py <estat_v99> <sortida.json>. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
EST = Path(sys.argv[1]); OUT = Path(sys.argv[2])
a = PSB(str(ARREL / '1-PHOTOSHOP/V101.psb')); b = PSB(str(ARREL / '1-PHOTOSHOP/V103.psb')); FILTRES = list(range(41, 57)); DERIVADES = {301}; rep = dict(derivades={}, capes_V101=len(a.layers), capes_V103=len(b.layers), iguals=[], diferents=[], filtres={})
ida = [L['id'] for L in a.layers]; idb = [L['id'] for L in b.layers]; rep['mateix_ordre_ids'] = ida == idb
for La, Lb in zip(a.layers, b.layers):
    lid = La['id']; meta_eq = all(La.get(k) == Lb.get(k) for k in ('blend', 'opacity', 'visible', 'left', 'top', 'right', 'bottom') if k in La and not (lid == 302 and k == 'visible'))
    if lid == 302: rep['capa_302'] = dict(visible_V101=bool(La.get('visible')), visible_V103=bool(Lb.get('visible')), passa=bool(La.get('visible')) and not Lb.get('visible'))
    if lid in FILTRES:
        r = dict(nom_V101=La.get('name'), nom_V103=Lb.get('name'), meta_igual=meta_eq)
        for cid, fn in ((1, f'L{lid}_G.npy'), (-1, f'L{lid}_alfa.npy'), (-2, f'L{lid}_mascara.npy')):
            q = b.channel(lid, cid)[0].astype(np.int32); e = np.load(EST / fn).astype(np.int32); dif = np.abs(q - e); r[f'canal_{cid}_dif_max'] = int(dif.max()); r[f'canal_{cid}_px_dif'] = int((dif > 0).sum())
        rep['filtres'][lid] = r; print(lid, r, flush=True); continue
    if lid in DERIVADES:
        dm = {int(c): np.abs(a.channel(lid, c)[0].astype(np.int32) - b.channel(lid, c)[0].astype(np.int32)) for c in La['chans']}
        rep['derivades'][lid] = dict(nom=La.get('name'), meta_igual=meta_eq, mostres_de_canal_diferents=int(sum((v > 0).sum() for v in dm.values())), dif_max=int(max(v.max() for v in dm.values())))
        print('DERIVADA', lid, rep['derivades'][lid], flush=True); continue
    ok = meta_eq and set(La['chans']) == set(Lb['chans']) and all(np.array_equal(a.channel(lid, c)[0], b.channel(lid, c)[0]) for c in La['chans'])
    (rep['iguals'] if ok else rep['diferents']).append(dict(id=lid, nom=La.get('name')))
    if not ok: print('DIFERENT', lid, La.get('name'), flush=True)
rep['veredicte'] = 'PASSA' if (rep['mateix_ordre_ids'] and not rep['diferents'] and rep.get('capa_302', {}).get('passa') is True and all(v['dif_max'] <= 2 and v['meta_igual'] for v in rep['derivades'].values()) and all(v['canal_1_dif_max'] <= 2 and v['canal_-1_dif_max'] <= 2 and v['canal_-2_dif_max'] <= 2 and v['meta_igual'] for v in rep['filtres'].values())) else 'FALLA'
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str)); print(rep['veredicte'], 'iguals', len(rep['iguals']), 'diferents', rep['diferents'])
