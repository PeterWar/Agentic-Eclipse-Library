"""b2 (V96) · Munta V96_stage.psb a partir de la V95 (1-PHOTOSHOP/V95.psb, SHA cb038bfc…; Photoshop la desarà com a 1-PHOTOSHOP/V96.psb).
Encàrrec de Pere (24-09, vespre): «refent P01 NRGF» (marques a Artefactes_V95.psb, capa 277). Canvi NOMÉS al RÀSTER de la capa 41 (P01 NRGF):
anells interiors parcials completats (w1) i, al buit sense dada, només el nivell (w2, opció B de Pere). Alfa, màscara, mode, opacitat i visibilitat de Pere,
byte a byte (de la V95). Nom «· V96». Tota la resta, byte a byte. Mai sobreescriu."""
import sys, json, hashlib, struct, zlib, io, copy, logging, time
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB, BIG_KEYS, _rf
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
SRC = ARREL / '1-PHOTOSHOP/V95.psb'; SHA_SRC = 'cb038bfcf08ede218041699c72a4f12e2ec8c77c2789b68819eca81f763400c1'; DST = SORT / 'V96_stage.psb'; assert not DST.exists(); assert sha(SRC) == SHA_SRC
NOU = {41: 'P01_NRGF_V96'}; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True); W_, H_ = 10551, 7506
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
rep = dict(font=dict(path='1-PHOTOSHOP/V95.psb', sha256=SHA_SRC), capes=[]); sortida = []
def afegeix(r, fonts):
    for c, f in zip(r.channel_info, fonts): c.length = f[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in NOU:
        tag = NOU[lid]; r = copy.deepcopy(r0); nom = nom_de(r0).replace('· V93', '· V96'); renomena(r, nom)
        fr = SORT / f'{tag}_u16.npy'
        rgb = cau_bytes(f'N_{tag}_{sha(fr)[:16]}.bin', lambda: enc(np.load(fr)))
        afegeix(r, [rgb if int(c.id) in (0, 1, 2) else src_chan(lid, int(c.id)) for c in r.channel_info])
        rep['capes'].append(dict(id=lid, nom=nom, canvi='NRGF amb els anells interiors parcials completats (patró azimutal, com els exteriors de la V36); sense a4v ni a5d; al buit sense dada només el nivell (decisió de Pere, opció B); alfa i màscara de la V95')); continue
    sortida.append((raw0, [src_chan(lid, int(c.id)) for c in r0.channel_info]))
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[3] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])
def copia(g_, f, a, b):
    f.seek(a)
    while f.tell() < b: g_.write(f.read(min(64 << 20, b - f.tell())))
obert = {}
with open(SRC, 'rb') as f, open(DST, 'xb') as g_:
    copia(g_, f, 0, S['lmpos']); g_.write(struct.pack('>Q', newlmlen)); copia(g_, f, S['lmpos'] + 8, S['lenpos']); g_.write(struct.pack('>Q', newlen))
    g_.write(struct.pack('>h', S['count'])); g_.write(recbytes)
    for raw, fonts in sortida:
        for kind, path, off, n in fonts:
            if path not in obert: obert[path] = open(path, 'rb')
            copia(g_, obert[path], off, off + n)
    g_.write(b'\0' * (newpad - newlen)); copia(g_, f, S['lrpadend'], SRC.stat().st_size)
for fh in obert.values(): fh.close()
assert sha(SRC) == SHA_SRC; q = PSB(str(DST)); assert len(q.layers) == len(p.layers)
for lid, tag in NOU.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(SORT / f'{tag}_u16.npy')) and np.array_equal(q.channel(lid, -1)[0], p.channel(lid, -1)[0]) and np.array_equal(q.channel(lid, -2)[0], p.channel(lid, -2)[0]), lid
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers)); (SORT / 'B2_MUNTATGE.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log(f'{DST.name} escrit: {len(q.layers)} capes')
