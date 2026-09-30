"""b2 (V108, cadena) · Munta un PSB de pas a partir de la V107 DE PERE (1-PHOTOSHOP/V107.psb, SHA 5927342e…, 41 capes), BYTE A BYTE,
substituint NOMÉS els canals de color (i l'alfa, si cal) de la base (3) i dels 16 filtres (41–56) pels ràsters d'un estat de la cadena V108.
Regles:
  · una capa «canvia» si q(ràster nou) ≠ canal de la V107 (q = la quantització del Photoshop, comu_v108.q): els canals que no canvien
    es copien BYTE A BYTE de la V107; els que canvien s'hi escriuen JA QUANTITZATS (q), de manera que el PSB de pas és exactament el que
    el Photoshop desarà (q és idempotent);
  · els filtres de la V107 són grisos (R = G = B): el ràster nou (L{id}_G) va als tres canals; la base, L3_RGB canal a canal;
    l'alfa: L{id}_alfa / L3_alfa de l'estat, amb la mateixa regla;
  · de cada capa es conserven la MÀSCARA DE PERE (bytes de la V107), el mode, l'opacitat, la visibilitat, el retall, les etiquetes i la
    resta de blocs; només a les capes que canvien, el nom passa a «· V108» (el primer «V9x/V10x» del nom; comu_v108.nom_v108);
  · cap altra capa no es toca; el compost fusionat (Image Data) és el de la V107 fins que el Photoshop el recompongui en desar COM A CÒPIA.
Si cap capa no canvia, el PSB de pas és idèntic a la V107 (es verifica el SHA). Després d'escriure, es verifica amb psb69 capa per capa.
Ús: b2_munta_v108.py <estat> <sortida.psb> [--forca 3,41,…|totes] [--capes 3,41-56] [--sense-renomenar]
  --forca   escriu els canals d'aquestes capes encara que q(nou) = V107 (per provar el camí de la substitució; el contingut no canvia)
  --capes   només aquestes capes poden canviar (per defecte, 3 i 41–56).
La sortida ha de ser dins de 4-RESULTATS/v108_20260926/ i no pot existir (mai no sobreescriu). Escriu també <sortida>_MUNTATGE.json i la
memòria cau dels canals codificats a <carpeta de la sortida>/canals_b2/."""
import sys, os, io, json, copy, struct, time, argparse, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_v108 import (ARREL, PSB, V107, SHA_V107, FILTRES, CAPES, q_blocs, sha, rel, claim, enc, llegeix_registres, rid, nom_de, nom_v108, renomena)


def llista(s):
    if s in (None, ''): return []
    if s == 'totes': return list(CAPES)
    out = []
    for p in s.split(','):
        a, _, b = p.partition('-'); out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out


ap = argparse.ArgumentParser(); ap.add_argument('estat'); ap.add_argument('sortida'); ap.add_argument('--forca', default=''); ap.add_argument('--capes', default='3,41-56')
ap.add_argument('--sense-renomenar', action='store_true'); ap.add_argument('--fils', type=int, default=4); A = ap.parse_args(); t0 = time.time()
claim(); EST = Path(A.estat).resolve(); DST = Path(A.sortida).resolve(); FORCA = set(llista(A.forca)); CAN = set(llista(A.capes))
assert str(DST).startswith(str(ARREL / '4-RESULTATS/v108_20260926') + os.sep), 'la sortida ha de ser dins de 4-RESULTATS/v108_20260926/'
assert DST.suffix == '.psb' and not DST.exists(), 'no-clobber: la sortida ja existeix'
assert CAN <= set(CAPES) and FORCA <= CAN, 'capes fora de 3 i 41–56'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
log('SHA de la V107…'); assert sha(V107) == SHA_V107, 'la V107 ha canviat: atura'
CAU = DST.parent / 'canals_b2'; CAU.mkdir(exist_ok=True)
p = PSB(str(V107)); S = llegeix_registres(V107); ids = [rid(r) for r, _ in S['recs']]; assert ids == [L['id'] for L in p.layers]
for lid in CAN:
    L = p.layer(lid); assert (L['left'], L['top'], L['right'], L['bottom']) == (0, 0, p.width, p.height), (lid, 'no ocupa el llenç sencer')
    assert set(L['chans']) == {-2, -1, 0, 1, 2}, (lid, sorted(L['chans']))
for r, raw in S['recs']:          # els registres que es poden reescriure han de fer el viatge d'anada i tornada byte a byte amb psd_tools
    if rid(r) in CAN: b = io.BytesIO(); r.write(b, version=2); assert b.getvalue() == raw, (rid(r), 'psd_tools no reescriu el registre byte a byte')


def font_de(lid, k):
    """El ràster de l'estat per a (capa, canal): base → L3_RGB[..., k] / L3_alfa; filtre → L{id}_G (qualsevol canal de color) / L{id}_alfa."""
    if lid == 3: f = EST / ('L3_alfa.npy' if k == -1 else 'L3_RGB.npy')
    else: f = EST / (f'L{lid}_alfa.npy' if k == -1 else f'L{lid}_G.npy')
    a = np.load(f, mmap_mode='r'); a = a[..., k] if (lid == 3 and k != -1) else a
    assert a.shape == (p.height, p.width) and a.dtype == np.uint16, (lid, k, a.shape, a.dtype)
    return f, a


def feina(lid, k):
    """(capa, canal) → (capa, canal, canvia o forçat, fitxer de bytes codificats o None, info). k = 0/1/2 (color) o −1 (alfa)."""
    font, a = font_de(lid, k)
    nou = q_blocs(a); vell = p.channel(lid, k)[0]; dif = nou != vell; n = int(dif.sum())
    info = dict(font=rel(font), px_diferents_de_la_V107=n, dif_max=int(np.abs(nou.astype(np.int32) - vell.astype(np.int32)).max()) if n else 0)
    if n:
        yy, xx = np.nonzero(dif.any(1))[0], np.nonzero(dif.any(0))[0]; info['caixa'] = [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
    del vell, dif
    if not (n or lid in FORCA): return lid, k, False, None, info
    h = hashlib.sha256(nou.tobytes()).hexdigest()[:20]; f = CAU / f'L{lid}_c{k}_q_{h}.bin'
    if not f.exists():
        tmp = f.with_suffix('.tmp'); tmp.write_bytes(enc(nou)); os.replace(tmp, f)
    info['bytes'] = f.stat().st_size; return lid, k, True, f, info


def canals_a_mirar(lid): return [0, 1, 2, -1] if lid == 3 else [1, -1]
jobs = [(lid, k) for lid in sorted(CAN) for k in canals_a_mirar(lid)]
log(f'{len(jobs)} canals per comparar amb la V107 ({A.fils} fils)…')
with ThreadPoolExecutor(A.fils) as ex: res = list(ex.map(lambda jk: feina(*jk), jobs))
NOU = {}; INFO = {}
for lid, k, canvia, f, info in res:
    INFO.setdefault(lid, {})[k] = dict(info, substituit=canvia, forcat=lid in FORCA)
    if canvia: NOU[(lid, k)] = f
for lid in CAN:                   # filtres grisos: el canal G nou va a R, G i B
    if lid != 3 and (lid, 1) in NOU:
        for k in (0, 2): assert np.array_equal(p.channel(lid, k)[0], p.channel(lid, 1)[0]), (lid, 'la V107 no és grisa: no es pot posar el G als tres canals')
        NOU[(lid, 0)] = NOU[(lid, 2)] = NOU[(lid, 1)]
CANVIADES = sorted({lid for lid, _ in NOU}); log(f'capes que canvien: {CANVIADES or "CAP"}')
src_chan = lambda lid, cid: (str(V107), *p.layer(lid)['chans'][cid])
sortida = []; rep = dict(font=dict(path=rel(V107), sha256=SHA_V107), estat=rel(EST), desti=rel(DST), forcades=sorted(FORCA), capes={})
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid not in CANVIADES:
        sortida.append((raw0, [src_chan(lid, int(c.id)) for c in r0.channel_info])); continue
    r = copy.deepcopy(r0); nom0 = nom_de(r0); nom = nom0 if A.sense_renomenar else nom_v108(nom0)
    if nom != nom0: renomena(r, nom)
    fonts = []
    for c in r.channel_info:
        cid = int(c.id); f = NOU.get((lid, cid))
        fonts.append((str(f), 0, f.stat().st_size) if f is not None else src_chan(lid, cid)); c.length = fonts[-1][2]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
    rep['capes'][str(lid)] = dict(nom_V107=nom0, nom=nom, canals={str(k): v for k, v in INFO[lid].items()},
                                  canals_substituits=sorted(int(c.id) for c in r.channel_info if (lid, int(c.id)) in NOU), mascara='la de Pere, byte a byte')
rep['sense_canvis'] = {str(lid): {str(k): v for k, v in INFO[lid].items()} for lid in sorted(CAN) if lid not in CANVIADES}
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[2] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])


def copia(g_, f, a, b):
    f.seek(a)
    while f.tell() < b: g_.write(f.read(min(64 << 20, b - f.tell())))


log('escrivint…'); obert = {}
with open(V107, 'rb') as f, open(DST, 'xb') as g_:
    copia(g_, f, 0, S['lmpos']); g_.write(struct.pack('>Q', newlmlen)); copia(g_, f, S['lmpos'] + 8, S['lenpos']); g_.write(struct.pack('>Q', newlen))
    g_.write(struct.pack('>h', S['count'])); g_.write(recbytes)
    for raw, fonts in sortida:
        for path, off, n in fonts:
            if path not in obert: obert[path] = open(path, 'rb')
            copia(g_, obert[path], off, off + n)
    g_.write(b'\0' * (newpad - newlen)); copia(g_, f, S['lrpadend'], V107.stat().st_size)
for fh in obert.values(): fh.close()
assert sha(V107) == SHA_V107, 'la V107 ha canviat durant el muntatge'
# ---- verificació amb psb69: capa per capa ----
log('verificant…'); qq = PSB(str(DST)); assert [L['id'] for L in qq.layers] == ids, 'ordre de capes'
Sq = llegeix_registres(DST); noms_q = {rid(r): nom_de(r) for r, _ in Sq['recs']}; noms_p = {rid(r): nom_de(r) for r, _ in S['recs']}
def verifica(L):
    lid = L['id']; Lq = qq.layer(lid); errs = []
    for k in ('blend', 'opacity', 'visible', 'clipping', 'left', 'top', 'right', 'bottom', 'mask'):
        if Lq.get(k) != L.get(k): errs.append(k)
    if set(Lq['chans']) != set(L['chans']): errs.append('canals')
    esperat = nom_v108(noms_p[lid]) if (lid in CANVIADES and not A.sense_renomenar) else noms_p[lid]
    if noms_q[lid] != esperat: errs.append(f'nom {noms_q[lid]!r} ≠ {esperat!r}')
    with open(V107, 'rb') as fa, open(DST, 'rb') as fb:
        for cid in L['chans']:
            if (lid, cid) in NOU:
                if not np.array_equal(qq.channel(lid, cid)[0], q_blocs(font_de(lid, cid)[1])): errs.append(f'canal {cid} ≠ q(estat)')
            else:   # copiat: els bytes crus han de ser els mateixos
                oa, na = L['chans'][cid]; ob, nb = Lq['chans'][cid]
                if na != nb: errs.append(f'canal {cid} mida'); continue
                fa.seek(oa); fb.seek(ob); ha = hashlib.sha256(); hb = hashlib.sha256(); rem = na
                while rem > 0:
                    m = min(rem, 64 << 20); ha.update(fa.read(m)); hb.update(fb.read(m)); rem -= m
                if ha.digest() != hb.digest(): errs.append(f'canal {cid} bytes')
    return lid, errs
with ThreadPoolExecutor(A.fils) as ex: ver = dict(ex.map(verifica, p.layers))
dolents = {k: v for k, v in ver.items() if v}; assert not dolents, dolents
rep['verificacio'] = dict(capes=len(qq.layers), capes_iguals_a_la_V107=[l for l in ids if l not in CANVIADES], capes_substituides=CANVIADES, errors=dolents or None)
rep['mida'] = DST.stat().st_size; rep['sha256'] = sha(DST); rep['identic_a_la_V107'] = rep['sha256'] == SHA_V107
if not CANVIADES: assert rep['identic_a_la_V107'], 'cap capa no canvia i el PSB de pas no és idèntic a la V107'
rep['quan'] = time.strftime('%Y-%m-%dT%H:%M:%S'); rep['segons'] = round(time.time() - t0)
(DST.parent / (DST.stem + '_MUNTATGE.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
log(f'{DST.name} escrit i verificat: {len(qq.layers)} capes · substituïdes {CANVIADES or "CAP"} · idèntic a la V107: {rep["identic_a_la_V107"]} · {rep["segons"]} s')
