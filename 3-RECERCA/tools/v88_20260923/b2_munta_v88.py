"""b2 · Munta V88_stage.psb a partir de la V87 de Pere (Photoshop el desarà després de manera nativa com a 1-PHOTOSHOP/V88.psb).
Canvis, cadascun en una capa pròpia (torre de Pisa a la pila):
  · 17 capes de filtre: ràsters nous (a3a amb la vora llisa + a3 + a4 amb la fosa suau i la continuació radial). Canals d'alfa i màscara, mode,
    opacitat i visibilitat: els de la V87, byte a byte. Nom «… · V88».
  · Nova «Earthshine V88» (e2) just a sobre de la 225 de Pere («Earthshine V86»), amb l'alfa de la 225 byte a byte. La 225 queda OCULTA, intacta.
  · «Cantonada del logo · es regenera»: regenerada (a5) amb el compost emulat de les capes de sota de la V88 (inclosos els canvis de Pere a la
    V87: la 76 en «Aclarir» i amb màscara nova, la 96 al 100 %, el pedaç 224).
  · «Artefactes V87» (marques de Pere): oculta, intacta.
Totes les altres capes es copien byte a byte."""
from v88_comu import *
from psb69 import PSB, BIG_KEYS, _rf
from v88_compost import comp, capa_box
import a5_cantonada as A5
import struct, zlib, io, copy, logging
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim()
SRC = ARREL / '1-PHOTOSHOP/V87.psb'; DST = SORT / 'V88_stage.psb'; assert not DST.exists(), 'no-clobber'
FIL = SORT / 'filtres_finals'; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True)
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral', 250: 'P05_WOW_bilateral'}
ID_LLUNA, ID_ES88, ID_CANT, ID_MARQUES = 225, 258, 255, 257
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
        else: raise RuntimeError('sense Lr16')
        count = _rf(f, 'h')[0]; recs = []
        for _ in range(abs(count)):
            pos = f.tell(); r = LayerRecord.read(f, version=2); end = f.tell(); f.seek(pos); raw = f.read(end - pos); recs.append((r, raw))
    return dict(lmpos=lmpos, lmlen=lmlen, lmend=lmend, lenpos=lenpos, lrstart=start, lrlen=n, lrpadend=start + (n + 3) // 4 * 4, count=count, recs=recs)
p = PSB(str(SRC)); S = llegeix_registres(SRC)
rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID))
src_chan = lambda psb, lid, cid: ('fitxer', psb.path, *psb.layer(lid)['chans'][cid])
emp = lambda path: sha(path)[:16]
def cau_bytes(nom, fn):
    q = CAU / nom
    if not q.exists(): q.write_bytes(fn())
    return ('fitxer', str(q), 0, q.stat().st_size)
def renomena(r, nom, lid=None):
    r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
    if lid is not None: r.tagged_blocks.set_data(Tag.LAYER_ID, lid)
def nom_de(r): return str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))
# ---- Earthshine V88 (e2): RGB nou, alfa de la 225 (comprovada byte a byte)
E2 = np.load(SORT / 'E2_earthshine_v88.npz'); L225 = p.layer(ID_LLUNA)
assert tuple(int(v) for v in E2['caixa']) == (L225['left'], L225['top'], L225['right'], L225['bottom'])
assert np.array_equal(E2['alfa'], p.channel(ID_LLUNA, -1)[0])
# ---- cantonada: compost emulat de les capes visibles de sota de la cantonada a la V88
box = A5.caixa_cantonada(); log(f'cantonada: caixa {box}')
sota_ids = []
for L in p.layers:
    if L['id'] == ID_CANT: break
    vis = L['visible'] if L['id'] != ID_LLUNA else False
    if vis: sota_ids.append(L['id'])
    if L['id'] == ID_LLUNA: sota_ids.append(ID_ES88)       # la capa nova, visible, just a sobre de la 225 oculta
capes_sota = []
for lid in sota_ids:
    if lid == ID_ES88:
        x0, y0, x1, y1 = box; lx0, ly0, lx1, ly1 = (int(v) for v in E2['caixa'])
        if lx1 <= x0 or lx0 >= x1 or ly1 <= y0 or ly0 >= y1: continue       # la Lluna no arriba a la caixa de la cantonada
        raise RuntimeError('la Lluna toca la caixa de la cantonada')
    rgb = np.load(FIL / f'{FILTRES[lid]}_u16.npy', mmap_mode='r') if lid in FILTRES else None
    capes_sota.append(capa_box(p, lid, box, rgb=None if rgb is None else np.asarray(rgb)))
x0, y0, x1, y1 = box; C, Acob = comp(capes_sota, y1 - y0, x1 - x0); assert Acob.min() > 0.999, f'forats a la caixa de la cantonada ({Acob.min()})'
crgb, calpha, crebut = A5.calcula(C); crebut.update(caixa=list(box), origen='compost emulat de les capes de sota de la V88 (b2)', capes=sota_ids)
np.savez_compressed(SORT / 'B2_cantonada.npz', rgb=np.round(crgb * 65535).astype(np.uint16), alpha=np.round(calpha * 65535).astype(np.uint16), box=np.array(box))
desa_json('B2_CANTONADA.json', crebut); log('cantonada calculada: ' + json.dumps({k: crebut[k] for k in ['triangle_px', 'nivell_cel_RGB']}))
# ---- registres i canals de sortida (de baix a dalt)
sortida = []; rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=sha(SRC)), capes=[])
def afegeix(r, fonts, modificat=True, raw=None):
    if modificat:
        for c, f in zip(r.channel_info, fonts): c.length = f[3]
        b = io.BytesIO(); r.write(b, version=2); raw = b.getvalue()
    sortida.append((raw, fonts))
def fonts_de(psb, lid, rec): return [src_chan(psb, lid, int(c.id)) for c in rec.channel_info]
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in FILTRES:
        r = copy.deepcopy(r0); nom = nom_de(r0).replace('· V86', '· V88'); renomena(r, nom); tag = FILTRES[lid]
        rgb = cau_bytes(f'F_{tag}_{emp(FIL / f"{tag}_u16.npy")}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy')))
        fonts = [rgb if int(c.id) in (0, 1, 2) else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=nom, canvi='ràster V88 (vora llisa + fosa suau); alfa, màscara, mode, opacitat i visibilitat de la V87', visible=bool(r.flags.visible), opacitat=r.opacity)); continue
    if lid == ID_LLUNA:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, lid, r))
        rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='capa de Pere intacta, OCULTA (la substitueix Earthshine V88)', visible=False))
        r = copy.deepcopy(r0); renomena(r, 'Earthshine V88', ID_ES88); r.flags.visible = True
        ch = {c: ('bytes', enc(E2['rgb'][..., c])) for c in range(3)}; ee = emp(SORT / 'E2_earthshine_v88.npz')
        fonts = [src_chan(p, ID_LLUNA, -1) if int(c.id) == -1 else cau_bytes(f'E_{int(c.id)}_{ee}.bin', lambda cid=int(c.id): ch[cid][1]) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=ID_ES88, nom='Earthshine V88', canvi="nova: l'earthshine de Pere a l'interior; anell de la vora sense l'estructura fina no lunar (e2); alfa de la 225 byte a byte", visible=True)); continue
    if lid == ID_CANT:
        r = copy.deepcopy(r0); cr = np.load(SORT / 'B2_cantonada.npz'); assert (r.left, r.top, r.right, r.bottom) == tuple(box)
        ch = {0: ('bytes', enc(cr['rgb'][..., 0])), 1: ('bytes', enc(cr['rgb'][..., 1])), 2: ('bytes', enc(cr['rgb'][..., 2])), -1: ('bytes', enc(cr['alpha']))}
        ec = emp(SORT / 'B2_cantonada.npz'); fonts = [cau_bytes(f'C_{int(c.id)}_{ec}.bin', lambda cid=int(c.id): ch[cid][1]) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=ID_CANT, nom=nom_de(r0), canvi='regenerada (a5) amb les capes de sota de la V88', visible=bool(r.flags.visible))); continue
    if lid == ID_MARQUES:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, lid, r))
        rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='marques de Pere, intactes i ocultes', visible=False)); continue
    sortida.append((raw0, fonts_de(p, lid, r0)))       # capa intacta: registre i canals byte a byte
# ---- escriptura
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[3] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])
count = S['count']; newcount = (abs(count) + 1) * (1 if count > 0 else -1)
def copia(g, f, a, b):
    f.seek(a)
    while f.tell() < b: g.write(f.read(min(64 << 20, b - f.tell())))
obert = {}
def llegeix_font(g, font):
    kind, path, off, n = font
    if path not in obert: obert[path] = open(path, 'rb')
    copia(g, obert[path], off, off + n)
with open(SRC, 'rb') as f, open(DST, 'xb') as g:
    copia(g, f, 0, S['lmpos']); g.write(struct.pack('>Q', newlmlen)); copia(g, f, S['lmpos'] + 8, S['lenpos']); g.write(struct.pack('>Q', newlen))
    g.write(struct.pack('>h', newcount)); g.write(recbytes)
    for raw, fonts in sortida:
        for font in fonts: llegeix_font(g, font)
    g.write(b'\0' * (newpad - newlen)); copia(g, f, S['lrpadend'], SRC.stat().st_size)
for fh in obert.values(): fh.close()
q = PSB(str(DST)); assert (q.width, q.height) == (W, H) and len(q.layers) == len(p.layers) + 1, (q.width, q.height, len(q.layers))
for lid, tag in FILTRES.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(FIL / f'{tag}_u16.npy')), lid
assert np.array_equal(q.channel(ID_ES88, 0)[0], E2['rgb'][..., 0]) and np.array_equal(q.channel(ID_ES88, -1)[0], p.channel(ID_LLUNA, -1)[0])
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers), compost_fusionat='PROVISIONAL (el de la V87) fins al desament natiu de Photoshop')
desa_json('B2_MUNTATGE.json', rep); log(f'V88_stage.psb escrit: {len(q.layers)} capes, {DST.stat().st_size/1e9:.2f} GB')
