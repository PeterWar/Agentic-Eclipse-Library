"""n0 (V108 · negres) · L'estat de la V107 llegit DEL PSB (només lectura): ràsters, alfes i màscares de totes les capes ràster visibles per sota
de la 239 (les capes d'ajust no s'emulen), en el format de jutge_comu.Estat (L{id}_G|RGB.npy, _alfa, _mascara, CAPES_V107.json).
Els filtres (R = G = B, comprovat) es desen com a G. La màscara es desa a la caixa de la capa (fora de la caixa de la màscara, el seu fons).
També compara els ràsters de 3 i 41–56 amb els de l'estat V105 (han de ser idèntics o diferir només per la quantificació del Photoshop).
Ús: n0_estat_v107.py  → 4-RESULTATS/v108_20260926/negres/estat_v107/"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
PSBP = R0 / '1-PHOTOSHOP/V107.psb'; E5 = R0 / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'
DST = R0 / '4-RESULTATS/v108_20260926/negres/estat_v107'; DST.mkdir(parents=True, exist_ok=True)
W, H = 10551, 7506
p = PSB(str(PSBP))
ordre = [l['id'] for l in p.layers]
AJUST = 239
capes = {}; rep = {}
FILTRES = (54, 41, 42, 47, 49, 51, 45, 46, 55, 56, 43, 44, 48, 50, 52, 53)
for l in p.layers:
    lid = l['id']
    if lid == AJUST: break
    box = (l['left'], l['top'], l['right'], l['bottom'])
    c = dict(nom=l['name'], visible=l['visible'], opacitat=l['opacity'], mode=l['blend'], bbox=list(box), mascara=l['mask'],
             canals='G' if lid in FILTRES else 'RGB', caixa_desada=list(box))
    capes[str(lid)] = c
    if not l['visible'] or box[2] <= box[0]: continue
    if lid in (3,) + FILTRES or lid in (305, 306, 258, 76, 224, 267):
        x0, y0, x1, y1 = box
        if lid in FILTRES:
            g = p.channel(lid, 1)[0]; r_ = p.channel(lid, 0)[0][::7, ::7]; b_ = p.channel(lid, 2)[0][::7, ::7]
            rep.setdefault(str(lid), {})['R=G=B'] = bool(np.array_equal(r_, g[::7, ::7]) and np.array_equal(b_, g[::7, ::7]))
            np.save(DST / f'L{lid}_G.npy', g)
            if (E5 / f'L{lid}_G.npy').exists():
                e = np.load(E5 / f'L{lid}_G.npy', mmap_mode='r'); d = np.abs(np.asarray(e, np.int32) - g.astype(np.int32))
                rep[str(lid)]['vs_estat_v105'] = dict(px_diferents=int((d > 0).sum()), dif_max=int(d.max()))
            del g
        else:
            rgb = np.stack([p.channel(lid, k)[0] for k in range(3)], -1); np.save(DST / f'L{lid}_RGB.npy', rgb)
            if (E5 / f'L{lid}_RGB.npy').exists():
                e = np.load(E5 / f'L{lid}_RGB.npy', mmap_mode='r')
                if e.shape == rgb.shape:
                    d = np.abs(np.asarray(e, np.int32) - rgb.astype(np.int32)); rep.setdefault(str(lid), {})['vs_estat_v105'] = dict(px_diferents=int((d > 0).sum()), dif_max=int(d.max()))
                else: rep.setdefault(str(lid), {})['vs_estat_v105'] = dict(forma_diferent=[list(e.shape), list(rgb.shape)])
            del rgb
        a = p.channel(lid, -1)[0]
        if a is not None: np.save(DST / f'L{lid}_alfa.npy', a)
        if l['mask'] is not None and not l['mask']['disabled'] and -2 in l['chans']:
            m = p.channel_box(lid, -2, box, fill=int(l['mask']['background']) * 257)
            np.save(DST / f'L{lid}_mascara.npy', m)
            q = E5 / f'L{lid}_mascara.npy'
            if q.exists():
                e = np.load(q, mmap_mode='r')
                if e.shape == m.shape:
                    d = np.abs(np.asarray(e, np.int32) - m.astype(np.int32)); rep.setdefault(str(lid), {})['mascara_vs_v105'] = dict(px_diferents=int((d > 0).sum()), dif_max=int(d.max()), mitjana_v105=float(np.asarray(e).mean() / 65535), mitjana_v107=float(m.mean() / 65535))
            c['mascara'] = dict(l['mask'], background=255 if l['mask']['background'] else 0)
            del m
        elif l['mask'] is not None: c['mascara'] = dict(l['mask'], background=255)   # desactivada: equival a 1
        print(lid, l['name'][:40], rep.get(str(lid)), flush=True)
meta = dict(font=f'{PSBP.name} (llegit amb psb69, només lectura)', llenc=[W, H], ordre_de_baix_a_dalt=[i for i in ordre if i < 10**6], capes=capes, comparacio=rep)
with open(PSBP, 'rb') as f: pass
(DST / 'CAPES_V107.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
print('FET')
