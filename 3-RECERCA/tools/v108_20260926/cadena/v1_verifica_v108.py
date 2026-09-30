"""v1 (V108, cadena) · Verificació independent d'un PSB de la V108 (el de pas de b2_munta_v108.py o el que desi el Photoshop) contra la V107 de
Pere (1-PHOTOSHOP/V107.psb, SHA 5927342e…) i l'estat de la cadena que s'hi ha muntat:
  · les 41 capes de la V107, en el mateix ordre, amb el mateix mode, opacitat, visibilitat, retall, caixa i màscara (geometria i PÍXELS: les
    màscares de Pere no es toquen mai);
  · les capes que no són la base ni els filtres (3, 41–56): tots els canals iguals a la V107 (bytes crus iguals, o, si el Photoshop els ha
    recomprimit, els píxels descodificats);
  · la base i els filtres: cada canal (R, G, B, alfa) ha de ser o el de la V107 o q(ràster de l'estat) (q = la quantització del Photoshop;
    als filtres, el G de l'estat als tres canals). Si algun canal no és el de la V107, la capa «ha canviat» i el nom ha de portar «V108»;
    si és igual a la V107, el nom pot ser el de Pere o el de V108 (muntatge forçat);
  · els noms de les capes que no canvien, els de Pere.
Ús: v1_verifica_v108.py <psb> <estat> <sortida.json> [--fils 4]. Només lectura (fora del json). Veredicte PASSA / FALLA."""
import sys, json, time, argparse, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_v108 import PSB, V107, SHA_V107, CAPES, q_blocs, sha, rel, llegeix_registres, rid, nom_de, nom_v108
ap = argparse.ArgumentParser(); ap.add_argument('psb'); ap.add_argument('estat'); ap.add_argument('sortida'); ap.add_argument('--fils', type=int, default=4); A = ap.parse_args(); t0 = time.time()
assert sha(V107) == SHA_V107, 'la V107 ha canviat'
a = PSB(str(V107)); b = PSB(A.psb); EST = Path(A.estat)
na = {rid(r): nom_de(r) for r, _ in llegeix_registres(V107)['recs']}; nb = {rid(r): nom_de(r) for r, _ in llegeix_registres(A.psb)['recs']}
ida = [L['id'] for L in a.layers]; idb = [L['id'] for L in b.layers]
rep = dict(psb=rel(A.psb), sha256_psb=sha(A.psb), estat=rel(EST), referencia=dict(path=rel(V107), sha256=SHA_V107), capes_V107=len(ida), capes_psb=len(idb), ordre_ok=ida == idb,
           geometria=dict(amplada=b.width, alcada=b.height, canals=b.channels, bits=b.depth, igual=(a.width, a.height, a.channels, a.depth) == (b.width, b.height, b.channels, b.depth)))


def estat_de(lid, k):
    if lid == 3: f = EST / ('L3_alfa.npy' if k == -1 else 'L3_RGB.npy')
    else: f = EST / (f'L{lid}_alfa.npy' if k == -1 else f'L{lid}_G.npy')
    x = np.load(f, mmap_mode='r'); return x[..., k] if (lid == 3 and k != -1) else x


def bytes_iguals(La, Lb, cid):
    (oa, n1), (ob, n2) = La['chans'][cid], Lb['chans'][cid]
    if n1 != n2: return False
    with open(a.path, 'rb') as fa, open(b.path, 'rb') as fb:
        fa.seek(oa); fb.seek(ob); rem = n1
        while rem > 0:
            m = min(rem, 64 << 20)
            if hashlib.sha256(fa.read(m)).digest() != hashlib.sha256(fb.read(m)).digest(): return False
            rem -= m
    return True


def capa(La):
    lid = La['id']; Lb = next((x for x in b.layers if x['id'] == lid), None); o = dict(id=lid, nom_V107=na[lid])
    if Lb is None: return dict(o, errors=['falta'])
    o['nom'] = nb[lid]; errs = []
    for k in ('blend', 'opacity', 'visible', 'clipping', 'left', 'top', 'right', 'bottom', 'mask'):
        if La.get(k) != Lb.get(k): errs.append(f'{k}: {La.get(k)} → {Lb.get(k)}')
    if set(La['chans']) != set(Lb['chans']): errs.append('conjunt de canals'); return dict(o, errors=errs)
    canals = {}; canvia = False
    for cid in sorted(La['chans']):
        if bytes_iguals(La, Lb, cid): canals[cid] = 'V107 (bytes)'; continue
        cb = b.channel(lid, cid)[0]
        if np.array_equal(a.channel(lid, cid)[0], cb): canals[cid] = 'V107 (píxels)'; continue
        if lid in CAPES and cid != -2:
            e = q_blocs(estat_de(lid, cid)); d = np.abs(cb.astype(np.int32) - e.astype(np.int32))
            if not d.any():
                canals[cid] = 'q(estat)'; canvia = True
                v = a.channel(lid, cid)[0]; dv = v != cb; yy, xx = np.nonzero(dv.any(1))[0], np.nonzero(dv.any(0))[0]
                o.setdefault('canvi', {})[cid] = dict(px=int(dv.sum()), dif_max=int(np.abs(v.astype(np.int32) - cb.astype(np.int32)).max()), caixa=[int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]); continue
            errs.append(f'canal {cid}: ni V107 ni q(estat) (|dif| màx contra q(estat) {int(d.max())})')
        else: errs.append(f'canal {cid} diferent de la V107' + (' (MÀSCARA DE PERE)' if cid == -2 else ''))
    o['canals'] = {str(k): v for k, v in canals.items()}; o['ha_canviat'] = canvia
    if canvia and nb[lid] != nom_v108(na[lid]): errs.append(f'ha canviat i el nom no és {nom_v108(na[lid])!r}')
    if not canvia and nb[lid] not in (na[lid], nom_v108(na[lid]) if lid in CAPES else na[lid]): errs.append('nom canviat')
    o['errors'] = errs; return o


with ThreadPoolExecutor(A.fils) as ex: res = list(ex.map(capa, a.layers))
rep['capes'] = res; rep['capes_canviades'] = [r['id'] for r in res if r.get('ha_canviat')]; rep['capes_renomenades'] = [r['id'] for r in res if r.get('nom') and r['nom'] != r['nom_V107']]
rep['errors'] = {str(r['id']): r['errors'] for r in res if r['errors']}
rep['veredicte'] = 'PASSA' if (rep['ordre_ok'] and rep['geometria']['igual'] and not rep['errors']) else 'FALLA'; rep['segons'] = round(time.time() - t0)
Path(A.sortida).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
print(rep['veredicte'], '· capes', len(idb), '· canviades', rep['capes_canviades'] or 'CAP', '· renomenades', rep['capes_renomenades'] or 'CAP', '· errors', rep['errors'] or 'cap', '·', rep['segons'], 's')
