"""f1 · Prova F (23-09-2026, vespre): la V88 de Pere (18:50) EXACTA, amb un sol canvi: la màscara de la capa d'ajust 241 «Claridad y borrar
neblina 1» (blanca, a tot el llenç) passa a ser radial: 0 dins de la Lluna i fins a 18 px del limbe de presentació, fosa smoothstep fins a 1 a 36 px.
Per què: la claredat fa un halo a la vora de contrast fort (aclareix la Lluna per dins fins a +0,012 i fa un anell fosc de −0,005..−0,008 a 3–20 px),
que és el que converteix el residu petit dels filtres arran del limbe en les línies marcades per Pere (prova D). Pere va triar provar-ho amb una
màscara radial («Prova amb màscara radial»). El registre de la capa d'ajust es reescriu byte a byte igual (comprovat), llevat de la mida del canal
de màscara i del nom («… · màscara radial (prova)»).
Sortida: 4-RESULTATS/v89_claredat_20260923/V89_prova_F.psb, mascara_radial.npy i F1_CLAREDAT.json."""
from pathlib import Path
import sys, json, hashlib, struct, zlib, io, copy, logging
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v89_claredat_20260923'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from psb69 import PSB, BIG_KEYS, _rf
from v86_operadors import smoothstep
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
SRC = ARREL / '1-PHOTOSHOP/V88.psb'; SHA_SRC = '04f7adedc28c41b89e15b35dbd71d1819ff34983407cfc0bbe2458ea9e6cfc78'; DST = SORT / 'V89_prova_F.psb'
assert not DST.exists() and sha(SRC) == SHA_SRC
D0, D1 = 18.0, 36.0; ID = 241; H, W = 7506, 10551
geo = json.loads((ARREL / '4-RESULTATS/v88_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
yy, xx = np.ogrid[:H, :W]; d = np.hypot(xx - cx, yy - cy) - R
m = np.round(smoothstep(d, D0, D1) * 65535).astype(np.uint16); np.save(SORT / 'mascara_radial.npy', m)
def enc(a):
    a = np.ascontiguousarray(a, np.uint16); dd = a.copy(); dd[:, 1:] = a[:, 1:] - a[:, :-1]; return struct.pack('>H', 3) + zlib.compress(dd.astype('>u2').tobytes(), 6)
menc = enc(m); (SORT / 'mascara_radial.bin').write_bytes(menc)
with open(SRC, 'rb') as f:
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
lrpadend = start + (n + 3) // 4 * 4
p = PSB(str(SRC)); L = p.layer(ID); assert (L['mask']['left'], L['mask']['top'], L['mask']['right'], L['mask']['bottom']) == (0, 0, W, H)
src_chan = lambda lid, cid: ('fitxer', str(SRC), *p.layer(lid)['chans'][cid])
sortida = []
for r0, raw0 in recs:
    lid = int(r0.tagged_blocks.get_data(Tag.LAYER_ID)); fonts = [src_chan(lid, int(c.id)) for c in r0.channel_info]
    if lid != ID: sortida.append((raw0, fonts)); continue
    r = copy.deepcopy(r0); nom = str(r0.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)) + ' · màscara radial (prova)'
    r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
    fonts = [('fitxer', str(SORT / 'mascara_radial.bin'), 0, len(menc)) if int(c.id) == -2 else f_ for c, f_ in zip(r.channel_info, fonts)]
    for c, f_ in zip(r.channel_info, fonts): c.length = f_[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f_[3] for _, fs in sortida for f_ in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = lmlen + newpad - (lrpadend - start)
def copia(g, fh, a, b_):
    fh.seek(a)
    while fh.tell() < b_: g.write(fh.read(min(64 << 20, b_ - fh.tell())))
obert = {}
with open(SRC, 'rb') as f, open(DST, 'xb') as g:
    copia(g, f, 0, lmpos); g.write(struct.pack('>Q', newlmlen)); copia(g, f, lmpos + 8, lenpos); g.write(struct.pack('>Q', newlen)); g.write(struct.pack('>h', count)); g.write(recbytes)
    for raw, fonts in sortida:
        for kind, path, off, nn in fonts:
            if path not in obert: obert[path] = open(path, 'rb')
            copia(g, obert[path], off, off + nn)
    g.write(b'\0' * (newpad - newlen)); copia(g, f, lrpadend, SRC.stat().st_size)
for fh in obert.values(): fh.close()
q = PSB(str(DST)); assert len(q.layers) == len(p.layers) and np.array_equal(q.channel(ID, -2)[0], m)
for Lq in q.layers:
    if Lq['id'] != ID:
        for cid in (0, -1):
            if cid in Lq['chans'] and Lq['right'] > Lq['left']: assert Lq['chans'][cid][1] == p.layer(Lq['id'])['chans'][cid][1]
(SORT / 'F1_CLAREDAT.json').write_text(json.dumps(dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size,
    canvi="capa 241: màscara radial (0 dins la Lluna i fins a 18 px del limbe; smoothstep fins a 1 a 36 px); nom «… · màscara radial (prova)»; la resta, byte a byte",
    limbe=dict(cx=cx, cy=cy, R=R), fosa_px=[D0, D1]), ensure_ascii=False, indent=2) + '\n')
print(f'V89_prova_F.psb escrit: {len(q.layers)} capes, {DST.stat().st_size / 1e9:.2f} GB')
