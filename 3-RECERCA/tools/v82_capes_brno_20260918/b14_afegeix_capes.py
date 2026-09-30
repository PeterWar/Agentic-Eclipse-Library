"""B14: PSB nou = PSB font + N capes noves a dalt de la pila (normal, 100 %, sense màscara, OCULTES), cadascuna amb
la seva caixa. Generalitza b13 (v75_marques_v74_20260917): plantilla = una capa ràster simple sense màscara
(canals −1,0,1,2); canals nous en ZIP amb predicció; la resta del fitxer byte a byte. Com que les capes noves
van ocultes, la imatge fusionada NO canvia i es copia tal qual (raw) de la font.
Paràmetres JSON: src, dst, rebut, plantilla (id), capes: [{npz, nom, nom_curt, id}], on npz té R,G,B,A uint16 i bbox.
"""
import sys, os, io, json, struct, zlib, time, hashlib, copy, logging, numpy as np
sys.path.insert(0, '/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/v73_marques_v71_20260917')
from psb69 import PSB
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
BIG = {x.value for x in TaggedBlock._BIG_KEYS}
P = json.load(open(sys.argv[1])); SRC = P['src']; DST = P['dst']; assert not os.path.exists(DST), 'no-clobber'
p = PSB(SRC); t0 = time.time()

def codifica(arr):
    a = arr.astype(np.uint16); d = a.copy(); d[:, 1:] = (a[:, 1:].astype(np.int32) - a[:, :-1].astype(np.int32)) & 0xFFFF
    return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)

def rf(f, fmt): n = struct.calcsize('>' + fmt); return struct.unpack('>' + fmt, f.read(n))

noves = []
for c in P['capes']:
    v = np.load(c['npz']); x0, y0, x1, y1 = [int(t) for t in v['bbox']]
    ch = {-1: codifica(v['A']), 0: codifica(v['R']), 1: codifica(v['G']), 2: codifica(v['B'])}
    for cid, b in ch.items(): assert np.array_equal(p._decode(b, x1 - x0, y1 - y0), v[{-1: 'A', 0: 'R', 1: 'G', 2: 'B'}[cid]])
    noves.append(dict(id=int(c['id']), nom=c['nom'], nom_curt=c['nom_curt'], bbox=(x0, y0, x1, y1), ch=ch))
    print(f"capa {c['id']} {c['nom']!r} caixa {(x0, y0, x1, y1)} canals {[len(b) for b in ch.values()]}", flush=True)

with open(SRC, 'rb') as f:
    f.seek(26); n = rf(f, 'I')[0]; f.seek(n, 1); n = rf(f, 'I')[0]; f.seek(n, 1)
    lm_start = f.tell(); lm_len = rf(f, 'Q')[0]; lm_end = lm_start + 8 + lm_len
    n = rf(f, 'Q')[0]; assert n == 0, 'les capes no són al bloc Lr16'; f.seek(n, 1)
    if f.tell() + 4 <= lm_end: n = rf(f, 'I')[0]; f.seek(n, 1)
    lr = None
    while f.tell() + 12 <= lm_end:
        pos = f.tell(); sig, key = rf(f, '4s4s'); fmt = 'Q' if key in BIG else 'I'; n = rf(f, fmt)[0]; start = f.tell()
        if key == b'Lr16': lr = (pos, f.tell() - (8 if fmt == 'Q' else 4), start, n); break
        f.seek(start + (n + 3) // 4 * 4)
    assert lr, 'sense Lr16'; lr_pos, lr_lenpos, lr_data, lr_len = lr; lr_end_pad = lr_data + (lr_len + 3) // 4 * 4
    f.seek(lr_data); count = rf(f, 'h')[0]; recs = [LayerRecord.read(f, version=2) for _ in range(abs(count))]; rec_end = f.tell()
    assert rec_end == min(vv[0] for l in p.layers for vv in l['chans'].values())
    ids = [int(r.tagged_blocks.get_data(Tag.LAYER_ID)) for r in recs]
    tpl = recs[ids.index(int(P['plantilla']))]
    assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None, 'la plantilla ha de ser una capa sense màscara amb canals -1,0,1,2'
    for c in noves:
        assert c['id'] not in ids, 'id ja existeix'; ids.append(c['id'])
        nr = copy.deepcopy(tpl); x0, y0, x1, y1 = c['bbox']
        nr.top, nr.left, nr.bottom, nr.right = y0, x0, y1, x1
        for ci in nr.channel_info: ci.length = len(c['ch'][int(ci.id)])
        nr.name = c['nom_curt']; nr.opacity = 255; nr.clipping = 0; nr.flags.visible = False
        nr.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, c['nom']); nr.tagged_blocks.set_data(Tag.LAYER_ID, c['id'])
        recs.append(nr)
    buf = io.BytesIO()
    for r in recs: r.write(buf, version=2)
    recbytes = buf.getvalue(); total_ch = sum(ci.length for r in recs for ci in r.channel_info); new_lr_len = 2 + len(recbytes) + total_ch; new_lr_pad = (new_lr_len + 3) // 4 * 4
    new_lm_len = lm_len + (new_lr_pad - (lr_end_pad - lr_data)); k = len(noves); newcount = count - k if count < 0 else count + k
    print('Lr16 %d → %d; L&M %d → %d; capes %d → %d' % (lr_len, new_lr_len, lm_len, new_lm_len, abs(count), abs(newcount)), flush=True)
    with open(DST, 'wb') as g:
        f.seek(0); g.write(f.read(lm_start)); g.write(struct.pack('>Q', new_lm_len)); f.seek(lm_start + 8); g.write(f.read(lr_lenpos - (lm_start + 8)))
        g.write(struct.pack('>Q', new_lr_len)); g.write(struct.pack('>h', newcount)); g.write(recbytes)
        for L in p.layers:
            for cid, (off, n) in L['chans'].items():
                f.seek(off); rem = n
                while rem > 0: b = f.read(min(rem, 64 << 20)); g.write(b); rem -= len(b)
        for c in noves:
            for cid in (-1, 0, 1, 2): g.write(c['ch'][cid])
        g.write(b'\0' * (new_lr_pad - new_lr_len)); f.seek(lr_end_pad); rem = lm_end - lr_end_pad
        while rem > 0: b = f.read(min(rem, 64 << 20)); g.write(b); rem -= len(b)
        img_off = g.tell(); f.seek(lm_end); rem = os.path.getsize(SRC) - lm_end   # imatge fusionada tal qual
        while rem > 0: b = f.read(min(rem, 64 << 20)); g.write(b); rem -= len(b)
print('escrit; imatge fusionada copiada a', img_off, 'mida', os.path.getsize(DST), '(%.0fs)' % (time.time() - t0))
with open(DST, 'rb') as g: sha = hashlib.file_digest(g, 'sha256').hexdigest()
with open(SRC, 'rb') as g: sha0 = hashlib.file_digest(g, 'sha256').hexdigest()
json.dump(dict(font=dict(path=SRC, sha256=sha0, bytes=os.path.getsize(SRC)), nou=dict(path=DST, sha256=sha, bytes=os.path.getsize(DST)),
               capes=[dict(id=c['id'], nom=c['nom'], bbox=list(c['bbox']), visible=False, canals={str(k): len(b) for k, b in c['ch'].items()}) for c in noves],
               plantilla=int(P['plantilla']), quan=time.strftime('%Y-%m-%dT%H:%M:%S')), open(P['rebut'], 'w'), indent=1, ensure_ascii=False)
print('SHA font', sha0); print('SHA nou', sha)
