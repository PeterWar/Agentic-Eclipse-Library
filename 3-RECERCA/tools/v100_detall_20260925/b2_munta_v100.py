"""b2 (V100 detall) · Munta el PSB de pas de la V100 = la V99 (1-PHOTOSHOP/V99.psb, SHA bb91bd13…) SENCERA, byte a byte, més UNA capa nova
(norma de Pere: cada canvi, una capa): «Detall real de la banda · V100», mode Superposar, visible, opacitat 100 %, inserida just damunt de la
WOW bilateral (56) i sota la Lluna de Pere (258). Contingut (gris, R = G = B): 0,5 + k·δ on hi ha dada (0,5 és neutre en Superposar); alfa = la
zona de la banda (CAPA_DETALL_BANDA.npz de d35; δ = detall TANGENCIAL real ponderat pel seu senyal corroborat). Caixa: la caixa lunar.
Plantilla del registre: la capa 267 (ràster sense màscara, canals −1, 0, 1, 2). Els canals s'escriuen en l'ordre dels registres.
Ús: b2_munta_v100.py <k> <sortida.psb> [<capa.npz>]   (mai sobreescriu)"""
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
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
K = float(sys.argv[1]); DST = Path(sys.argv[2]); NPZ = Path(sys.argv[3]) if len(sys.argv) > 3 else ARREL / '4-RESULTATS/v100_detall_20260925/CAPA_DETALL_BANDA.npz'
SRC = ARREL / '1-PHOTOSHOP/V99.psb'; SHA_SRC = 'bb91bd13ff60e6b1f10bcf463f94d1651cd733ce9afef95b4ad42009d1884169'
assert not DST.exists(), 'no-clobber'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert sha(SRC) == SHA_SRC
def codifica(a):
    a = np.ascontiguousarray(a, np.uint16); d = a.copy(); d[:, 1:] = (a[:, 1:].astype(np.int32) - a[:, :-1].astype(np.int32)) & 0xFFFF
    return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)
def rf(f, fmt): n = struct.calcsize('>' + fmt); return struct.unpack('>' + fmt, f.read(n))
Z = np.load(NPZ); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; delta = Z['delta']; alfa = Z['alfa']
g = np.clip(0.5 + K * delta * (alfa > 0), 0, 1); G16 = np.round(g * 65535).astype(np.uint16); G16[alfa <= 0] = 32768
A16 = np.round(np.clip(alfa, 0, 1) * 65535).astype(np.uint16)
ID_NOU, NOM = 302, 'Detall real de la banda · V100'
p = PSB(str(SRC)); t0 = time.time()
ch = {-1: codifica(A16), 0: codifica(G16), 1: codifica(G16), 2: codifica(G16)}
for cid, b in ch.items(): assert np.array_equal(p._decode(b, bx1 - bx0, by1 - by0), A16 if cid == -1 else G16)
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
    tpl = recs[ids.index(267)]; assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None
    nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = by0, bx0, by1, bx1
    for ci in nr.channel_info: ci.length = len(ch[int(ci.id)])
    nr.name = 'Detall real de la banda V100'[:31]; nr.opacity = 255; nr.clipping = 0; nr.flags.visible = True; nr.blend_mode = BlendMode.OVERLAY
    nr.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, NOM); nr.tagged_blocks.set_data(Tag.LAYER_ID, ID_NOU)
    pos56 = ids.index(56); recs2 = recs[:pos56 + 1] + [nr] + recs[pos56 + 1:]; ordre = ids[:pos56 + 1] + [ID_NOU] + ids[pos56 + 1:]
    assert ordre[pos56 + 2] == 258, ordre[pos56 - 1:pos56 + 4]
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
    for cid in L['chans']: assert np.array_equal(q.channel(L['id'], cid)[0], p.channel(L['id'], cid)[0]), (L['id'], cid)
assert np.array_equal(q.channel(ID_NOU, 0)[0], G16) and np.array_equal(q.channel(ID_NOU, -1)[0], A16)
rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), desti=str(DST), k=K, capa=dict(id=ID_NOU, nom=NOM, mode='Superposar', caixa=[bx0, by0, bx1, by1], sobre=56, sota=258, npz=str(NPZ)),
           capes_total=len(q.layers), quan=time.strftime('%Y-%m-%dT%H:%M:%S'), segons=round(time.time() - t0))
(DST.parent / (DST.stem + '_MUNTATGE.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print('escrit', DST, len(q.layers), 'capes;', rep['segons'], 's')
