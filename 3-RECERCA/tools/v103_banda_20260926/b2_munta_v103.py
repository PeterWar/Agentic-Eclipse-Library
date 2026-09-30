"""b2 (V103 banda) · Munta V103_stage.psb a partir de la V101 (1-PHOTOSHOP/V101.psb, SHA 3a95a581…; el Photoshop la desarà com a 1-PHOTOSHOP/V103.psb),
igual que la V99 (b2_munta_v99.py), amb els filtres de la V103 (franja a3d: règim de banda al costat d'avanç de la Lluna). Canvis respecte de la V101
(la resta, byte a byte):
  · capes 41–56 (els 16 filtres): el ràster nou i l'alfa nova (f3_filtres_v98.py sobre la linealitzada V103), i la màscara de Pere amb ZERO dins
    del disc de presentació (r3_estat_v98.py; fora del disc, byte a byte la de Pere); el mode, l'opacitat i la visibilitat, els de la V101;
    al nom, «· V9x/V10x» → «· V103»;
  · la base (3): si el ràster de l'estat és idèntic al de la V101 (ho és: la banda és a 2–6 px i la base arran del limbe és la de la V96), la capa
    queda byte a byte; si no, el ràster nou i el nom «00 Base · linealitzada V103»;
  · la capa 302 («Detall real de la banda · V100»): OCULTA (superada pel règim de banda dels filtres; es conserva per comparar). Res més no canvia.
Ús: b2_munta_v103.py <estat_v103> (la carpeta de r3; la sortida va a la carpeta de la variant, la mare de l'estat). Mai sobreescriu."""
import sys, json, hashlib, struct, zlib, io, copy, logging, time, re
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB, BIG_KEYS, _rf
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
EST = Path(sys.argv[1]).resolve(); SORT = EST.parent; SRC = ARREL / '1-PHOTOSHOP/V101.psb'; SHA_SRC = '3a95a5814e337c09339e05c1f44b0a603bac6a8f688acc8296732165b6d2cc54'
DST = SORT / 'V103_stage.psb'; assert not DST.exists(); assert sha(SRC) == SHA_SRC
CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True); W_, H_ = 10551, 7506; FILTRES = list(range(41, 57)); ID_REF = 300
def enc(a):
    a = np.ascontiguousarray(a, np.uint16); d = a.copy(); d[:, 1:] = a[:, 1:] - a[:, :-1]; return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)
def llegeix_registres(path):
    with open(path, 'rb') as f:
        f.seek(26)
        for _ in range(2): n = _rf(f, 'I')[0]; f.seek(n, 1)
        lmpos = f.tell(); lmlen = _rf(f, 'Q')[0]; lmend = f.tell() + lmlen; n = _rf(f, 'Q')[0]; assert n == 0; n = _rf(f, 'I')[0]; f.seek(n, 1)
        while f.tell() + 12 <= lmend:
            sig, key = _rf(f, '4s4s'); fmt = 'Q' if key in BIG_KEYS else 'I'; lenpos = f.tell(); n = _rf(f, fmt)[0]; start = f.tell()
            if key == b'Lr16': break
            f.seek(start + (n + 3) // 4 * 4)
        count = _rf(f, 'h')[0]; recs = []
        for _ in range(abs(count)):
            pos = f.tell(); r = LayerRecord.read(f, version=2); end = f.tell(); f.seek(pos); recs.append((r, f.read(end - pos)))
    return dict(lmpos=lmpos, lmlen=lmlen, lenpos=lenpos, lrstart=start, lrpadend=start + (n + 3) // 4 * 4, count=count, recs=recs)
rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID)); nom_de = lambda r: str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))
def renomena(r, nom): r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
def cau_bytes(nom, fn):
    q = CAU / nom
    if not q.exists(): q.write_bytes(fn())
    return ('fitxer', str(q), 0, q.stat().st_size)
p = PSB(str(SRC)); S = llegeix_registres(SRC); src_chan = lambda lid, cid: ('fitxer', str(SRC), *p.layer(lid)['chans'][cid])
assert all(int(p.layer(l)['left']) == 0 and int(p.layer(l)['right']) == W_ for l in [3] + FILTRES), 'capes que no ocupen el llenç sencer'
assert all(p.layer(l)['mask'] and (p.layer(l)['mask']['left'], p.layer(l)['mask']['top'], p.layer(l)['mask']['right'], p.layer(l)['mask']['bottom']) == (0, 0, W_, H_) for l in FILTRES), 'màscares que no ocupen el llenç sencer'
rep = dict(font=dict(path='1-PHOTOSHOP/V101.psb', sha256=SHA_SRC), estat=str(EST.relative_to(ARREL)), capes=[]); sortida = []
def afegeix(r, fonts):
    for c, f in zip(r.channel_info, fonts): c.length = f[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
def nom_v99(n): return re.sub(r'· V(9\d|10\d)', '· V103', n) if re.search(r'· V(9\d|10\d)', n) else n + ' · V103'
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid == 302:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, [src_chan(lid, int(c.id)) for c in r.channel_info]); rep['capes'].append(dict(id=302, nom=nom_de(r0), canvi='OCULTA (superada pel règim de banda dels filtres); ràster i alfa byte a byte')); continue
    if lid == 3:
        B = np.load(EST / 'L3_RGB.npy', mmap_mode='r'); hB = sha(EST / 'L3_RGB.npy')[:16]
        if all(np.array_equal(p.channel(3, k)[0], np.asarray(B[..., k])) for k in (0, 1, 2)):
            sortida.append((raw0, [src_chan(lid, int(c.id)) for c in r0.channel_info])); rep['capes'].append(dict(id=3, nom=nom_de(r0), canvi='cap (el ràster de l\'estat és idèntic al de la V101): byte a byte')); BASE_NOVA = False; continue
        BASE_NOVA = True; r = copy.deepcopy(r0); nom = '00 Base · linealitzada V103'; renomena(r, nom)
        fonts = [cau_bytes(f'B3_{int(c.id)}_{hB}.bin', lambda k=int(c.id): enc(np.asarray(B[..., k]))) if int(c.id) in (0, 1, 2) else src_chan(3, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=3, nom=nom, canvi='ràster RGB nou (recepta b4e sobre la linealitzada V103); alfa i màscara de la V101')); continue
    if lid in FILTRES:
        r = copy.deepcopy(r0); nom = nom_v99(nom_de(r0)); renomena(r, nom)
        G = EST / f'L{lid}_G.npy'; Al = EST / f'L{lid}_alfa.npy'; Mk = EST / f'L{lid}_mascara.npy'; hG = sha(G)[:16]; hA = sha(Al)[:16]; hM = sha(Mk)[:16]
        gb = cau_bytes(f'F{lid}_{hG}.bin', lambda: enc(np.load(G))); ab = cau_bytes(f'A{lid}_{hA}.bin', lambda: enc(np.load(Al))); mb = cau_bytes(f'M{lid}_{hM}.bin', lambda: enc(np.load(Mk)))
        assert {int(c.id) for c in r.channel_info} == {0, 1, 2, -1, -2}, (lid, [int(c.id) for c in r.channel_info])
        fonts = [gb if int(c.id) in (0, 1, 2) else (ab if int(c.id) == -1 else mb) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=nom, canvi='ràster i alfa nous (f3 V98 sobre la linealitzada V103 amb la franja a3d: règim de banda); màscara de Pere amb zero dins del disc de la Lluna; mode, opacitat i visibilitat de la V101')); continue
    sortida.append((raw0, [src_chan(lid, int(c.id)) for c in r0.channel_info]))
count = S['count']
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[3] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])
def copia(g_, f, a, b):
    f.seek(a)
    while f.tell() < b: g_.write(f.read(min(64 << 20, b - f.tell())))
obert = {}
with open(SRC, 'rb') as f, open(DST, 'xb') as g_:
    copia(g_, f, 0, S['lmpos']); g_.write(struct.pack('>Q', newlmlen)); copia(g_, f, S['lmpos'] + 8, S['lenpos']); g_.write(struct.pack('>Q', newlen))
    g_.write(struct.pack('>h', count)); g_.write(recbytes)
    for raw, fonts in sortida:
        for kind, path, off, n in fonts:
            if path not in obert: obert[path] = open(path, 'rb')
            copia(g_, obert[path], off, off + n)
    g_.write(b'\0' * (newpad - newlen)); copia(g_, f, S['lrpadend'], SRC.stat().st_size)
for fh in obert.values(): fh.close()
assert sha(SRC) == SHA_SRC; q = PSB(str(DST)); assert len(q.layers) == len(p.layers)
assert np.array_equal(q.channel(3, 0)[0], np.load(EST / 'L3_RGB.npy', mmap_mode='r')[..., 0]); assert not q.layer(302)['visible'] and p.layer(302)['visible']
for lid in FILTRES: assert np.array_equal(q.channel(lid, 1)[0], np.load(EST / f'L{lid}_G.npy')) and np.array_equal(q.channel(lid, -2)[0], np.load(EST / f'L{lid}_mascara.npy')) and np.array_equal(q.channel(lid, -1)[0], np.load(EST / f'L{lid}_alfa.npy')), lid
for L in p.layers:
    if L['id'] not in FILTRES + [3]:   # la 302 només canvia la visibilitat: els canals són iguals
        for cid in L['chans']: assert np.array_equal(q.channel(L['id'], cid)[0], p.channel(L['id'], cid)[0]), (L['id'], cid)
rep['base_nova'] = BASE_NOVA; rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers)); (SORT / 'B2_MUNTATGE_V103.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log(f'{DST.name} escrit: {len(q.layers)} capes')
