"""b2 (V106, Claude, 26-09-2026) · Munta el PSB de pas de la V106 = la V105 (1-PHOTOSHOP/V105.psb, SHA 7b41181a…, 42 capes) SENCERA, byte a byte,
més UNA capa nova (norma de Pere: cada canvi, una capa): «Detall arran del limbe · V106», mode Superposar, visible, opacitat 100 %, id 306,
just damunt de la 305 i sota la Lluna de Pere (258). Contingut: gris R = G = B, 32768 = neutre; alfa 65535 on actua i 0 a la resta. Caixa: la caixa lunar.
La 306 SUBSTITUEIX la 305 (porta tot el detall arran del limbe, el de la V105 més el nou): la 305 passa a OCULTA (només la visibilitat; píxels intactes),
llevat que V106_OCULTA_305=0. Plantilla del registre: la 305. Ús: b2_munta_v106.py <capa.npz> <sortida.psb> (mai sobreescriu)."""
import sys, os, io, json, struct, zlib, time, hashlib, copy, logging
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock
from psd_tools.constants import Tag, BlendMode
logging.getLogger('psd_tools').setLevel(logging.ERROR)
BIG = {x.value for x in TaggedBlock._BIG_KEYS}
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD' and o.get('claim_id') == 'CLAUDE_V106_INVERSIO_LOLA_20260926'
NPZ = Path(sys.argv[1]); DST = Path(sys.argv[2]); G56 = None; OCULTA = os.environ.get('V106_OCULTA_305', '1') == '1'
SRC = ARREL / '1-PHOTOSHOP/V105.psb'; SHA_SRC = '7b41181aa8e3ff01c5e230f122eb0cbda3a737f093971ec469fad4c65d4269de'
assert not DST.exists(), 'no-clobber'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert sha(SRC) == SHA_SRC, 'la V105 ha canviat: atura'
def codifica(a):
    a = np.ascontiguousarray(a, np.uint16); d = a.copy(); d[:, 1:] = (a[:, 1:].astype(np.int32) - a[:, :-1].astype(np.int32)) & 0xFFFF
    return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)
def rf(f, fmt): n = struct.calcsize('>' + fmt); return struct.unpack('>' + fmt, f.read(n))
Z = np.load(NPZ); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; RGB16 = Z['RGB16']; A16 = Z['A16']
ID_NOU, NOM = 306, 'Detall arran del limbe · V106'
p = PSB(str(SRC)); t0 = time.time()
ch = {-1: codifica(A16), 0: codifica(RGB16[..., 0]), 1: codifica(RGB16[..., 1]), 2: codifica(RGB16[..., 2])}
for cid, b in ch.items(): assert np.array_equal(p._decode(b, bx1 - bx0, by1 - by0), A16 if cid == -1 else RGB16[..., cid])
if G56 is not None:
    L56 = p.layer(56); assert (L56['left'], L56['top'], L56['right'], L56['bottom']) == (0, 0, p.width, p.height) and G56.shape == (p.height, p.width) and G56.dtype == np.uint16
    b56 = codifica(G56); assert np.array_equal(p._decode(b56, p.width, p.height), G56)
    for c in (0, 1, 2): assert np.array_equal(p.channel(56, 0)[0], p.channel(56, c)[0])   # a la V104 la 56 és grisa
    n56_dif = int((p.channel(56, 1)[0] != G56).sum())
with open(SRC, 'rb') as f:
    f.seek(26); n = rf(f, 'I')[0]; f.seek(n, 1); n = rf(f, 'I')[0]; f.seek(n, 1)
    lm_start = f.tell(); lm_len = rf(f, 'Q')[0]; lm_end = lm_start + 8 + lm_len
    n = rf(f, 'Q')[0]; assert n == 0; f.seek(n, 1)
    if f.tell() + 4 <= lm_end: n = rf(f, 'I')[0]; f.seek(n, 1)
    lr = None
    while f.tell() + 12 <= lm_end:
        pos = f.tell(); sig, key = rf(f, '4s4s'); fmt = 'Q' if key in BIG else 'I'; n = rf(f, fmt)[0]; start = f.tell()
        if key == b'Lr16': lr = (pos, f.tell() - (8 if fmt == 'Q' else 4), start, n); break
        f.seek(start + (n + 3) // 4 * 4)
    assert lr; lr_pos, lr_lenpos, lr_data, lr_len = lr; lr_end_pad = lr_data + (lr_len + 3) // 4 * 4
    f.seek(lr_data); count = rf(f, 'h')[0]; recs = [LayerRecord.read(f, version=2) for _ in range(abs(count))]
    ids = [int(r.tagged_blocks.get_data(Tag.LAYER_ID)) for r in recs]; assert ID_NOU not in ids
    assert [L['id'] for L in p.layers] == ids, 'ordre de capes diferent entre psb69 i els registres'
    tpl = recs[ids.index(305)]; assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None
    nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = by0, bx0, by1, bx1
    for ci in nr.channel_info: ci.length = len(ch[int(ci.id)])
    nr.name = 'Detall arran del limbe V106'[:31]; nr.opacity = 255; nr.clipping = 0; nr.flags.visible = True; nr.blend_mode = BlendMode.OVERLAY
    nr.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, NOM); nr.tagged_blocks.set_data(Tag.LAYER_ID, ID_NOU)
    i305 = ids.index(305); vis305_abans = bool(recs[i305].flags.visible)
    if OCULTA: recs[i305].flags.visible = False
    if G56 is not None:
        r56 = recs[ids.index(56)]
        for ci in r56.channel_info:
            if int(ci.id) in (0, 1, 2): ci.length = len(b56)
        nom56 = str(r56.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)); nom56n = nom56.replace('· V104', '· V105'); r56.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom56n)
    pos305 = ids.index(305); recs2 = recs[:pos305 + 1] + [nr] + recs[pos305 + 1:]; ordre = ids[:pos305 + 1] + [ID_NOU] + ids[pos305 + 1:]
    assert ordre[pos305] == 305 and ordre[pos305 + 2] == 258, ordre[pos305 - 1:pos305 + 4]
    buf = io.BytesIO()
    for r in recs2: r.write(buf, version=2)
    recbytes = buf.getvalue(); total_ch = sum(ci.length for r in recs2 for ci in r.channel_info)
    new_lr_len = 2 + len(recbytes) + total_ch; new_lr_pad = (new_lr_len + 3) // 4 * 4; new_lm_len = lm_len + (new_lr_pad - (lr_end_pad - lr_data)); newcount = count - 1 if count < 0 else count + 1
    capes = {L['id']: L for L in p.layers}
    with open(DST, 'xb') as g_:
        f.seek(0); g_.write(f.read(lm_start)); g_.write(struct.pack('>Q', new_lm_len)); f.seek(lm_start + 8); g_.write(f.read(lr_lenpos - (lm_start + 8)))
        g_.write(struct.pack('>Q', new_lr_len)); g_.write(struct.pack('>h', newcount)); g_.write(recbytes)
        for lid, r in zip(ordre, recs2):
            if lid == ID_NOU:
                for ci in r.channel_info: g_.write(ch[int(ci.id)])
                continue
            L = capes[lid]
            if lid == 56 and G56 is not None:
                for ci in r.channel_info:
                    if int(ci.id) in (0, 1, 2): g_.write(b56); continue
                    off, n = L['chans'][int(ci.id)]; f.seek(off); rem = n
                    while rem > 0: b = f.read(min(rem, 64 << 20)); g_.write(b); rem -= len(b)
                continue
            for ci in r.channel_info:
                off, n = L['chans'][int(ci.id)]; f.seek(off); rem = n
                while rem > 0: b = f.read(min(rem, 64 << 20)); g_.write(b); rem -= len(b)
        g_.write(b'\0' * (new_lr_pad - new_lr_len)); f.seek(lr_end_pad); rem = lm_end - lr_end_pad
        while rem > 0: b = f.read(min(rem, 64 << 20)); g_.write(b); rem -= len(b)
        f.seek(lm_end); rem = os.path.getsize(SRC) - lm_end
        while rem > 0: b = f.read(min(rem, 64 << 20)); g_.write(b); rem -= len(b)
assert sha(SRC) == SHA_SRC
q = PSB(str(DST)); assert len(q.layers) == len(p.layers) + 1 and [L['id'] for L in q.layers] == ordre
for L in p.layers:
    for cid in L['chans']:
        if L['id'] == 56 and G56 is not None and cid in (0, 1, 2): assert np.array_equal(q.channel(56, cid)[0], G56); continue
        assert np.array_equal(q.channel(L['id'], cid)[0], p.channel(L['id'], cid)[0]), (L['id'], cid)
    Lq = next(x for x in q.layers if x['id'] == L['id'])
    for k in ('blend', 'opacity', 'left', 'top', 'right', 'bottom'): assert Lq.get(k) == L.get(k), (L['id'], k)
    assert Lq.get('visible') == (L.get('visible') if (L['id'] != 305 or not OCULTA) else False), (L['id'], 'visible')
assert all(np.array_equal(q.channel(ID_NOU, c)[0], RGB16[..., c]) for c in (0, 1, 2)) and np.array_equal(q.channel(ID_NOU, -1)[0], A16)
rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), desti=str(DST), capa=dict(id=ID_NOU, nom=NOM, mode='Superposar', caixa=[bx0, by0, bx1, by1], sobre=305, sota=258, npz=str(NPZ)),
           capa_305=dict(visible_abans=vis305_abans, visible_despres=not OCULTA), capa_56=(dict(nom_nou=nom56n, px_diferents_de_la_V104=n56_dif, font=sys.argv[3]) if G56 is not None else None), capes_total=len(q.layers), quan=time.strftime('%Y-%m-%dT%H:%M:%S'), segons=round(time.time() - t0))
(DST.parent / (DST.stem + '_MUNTATGE.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print('escrit', DST, len(q.layers), 'capes;', rep['segons'], 's')
