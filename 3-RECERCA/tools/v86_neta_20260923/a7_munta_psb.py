"""a7 · Munta V86_stage.psb a partir de la V85 (Photoshop el desarà després de manera nativa com a 1-PHOTOSHOP/V86.psb).
Canvis, cadascun en una capa pròpia (norma de Pere del 23-09: la torre de Pisa també a la pila):
  · 17 capes de filtre: ràsters nous d'a3+a4 (mateix ordre, mode, opacitat i visibilitat que la V84), màscares d'a6. Nom «… · V86».
  · Base (capa 3): els píxels de la V85 (verd corregit, decisió C) amb la màscara d'a6.
  · Nova, oculta, just a sota: «00 Base V84 · referència oculta» (la base i la màscara originals de Pere a la V84).
  · 225 (Correccions Earthshine V77 de Pere): l'original sense màscara, OCULTA (conté la seva interpolació dels filtres antics a la
    franja, ara substituïda per a4) + nova «Correccions V77 · només la Lluna» visible al 70 % amb la màscara del suport lunar.
  · Nova «Cantonada del logo · es regenera» (a5) entre les estrelles i les capes d'ajust.
  · 234 (PixInsight): oculta, amb la màscara original de Pere (V84); 252 (placa de Codex): oculta.
Les capes de Pere (Lluna, fotos, estrelles, ajustos, marques, referències) es copien byte a byte."""
from v86_comu import *
from psb69 import PSB, BIG_KEYS, _rf
from v86_compost import comp, capa_box
import a5_cantonada as A5
import struct, zlib, io, copy, logging, os
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim()
SRC = ARREL / '1-PHOTOSHOP/V85.psb'; SRC84 = ARREL / '1-PHOTOSHOP/V84.psb'; DST = SORT / 'V86_stage.psb'; assert not DST.exists(), 'no-clobber'
FIL = SORT / 'filtres_finals'; MAS = SORT / 'mascares'; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True)
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral', 250: 'P05_WOW_bilateral'}
NOMS = {48: '03 ACHF azimutal 8-128 r4 · V86 · sense estrelles', 50: '01 ACHF fi 2-32 · V86 · sense estrelles', 52: '05 ACHF fi 2-48 · V86 · sense estrelles',
        53: '06 ACHF estructura 4-64 · V86 · sense estrelles', 54: 'P03 MGN · V86 · sense estrelles', 43: 'P02 RHEF · V86 · sense estrelles',
        44: 'P02b RHEF υ 0,35 · V86 · sense estrelles', 41: 'P01 NRGF · V86 · sense estrelles', 42: 'P01b NRGF estès cap endins · V86',
        47: '03 ACHF azimutal 8-128 r0 · V86 · sense estrelles', 49: '07 ACHF azimutal suau r8 · V86', 51: '04 ACHF micro 1-16 · V86 · sense estrelles',
        45: 'P02c RHEF local 60° · V86 · sense estrelles', 46: 'P02d RHEF local 30° · V86 · sense estrelles', 55: 'P04 WOW · V86 · sense estrelles',
        56: 'P05 WOW bilateral · V86 · sense estrelles', 250: 'P05 WOW bilateral · V86 · sense estrelles', 3: '00 Base corba · verd corregit V85'}
ID_BASE84, ID_225LL, ID_CANT = 253, 254, 255
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
p = PSB(str(SRC)); p84 = PSB(str(SRC84)); S = llegeix_registres(SRC); S84 = llegeix_registres(SRC84)
rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID))
rec85 = {rid(r): (r, raw) for r, raw in S['recs']}; rec84 = {rid(r): (r, raw) for r, raw in S84['recs']}
src_chan = lambda psb, lid, cid: ('fitxer', psb.path, *psb.layer(lid)['chans'][cid])
def cau_bytes(nom, fn):
    # el nom de la cau porta l'empremta del CONTINGUT (23-09, 3 h): amb el nom sol, un segon muntatge reutilitzava els canals dels filtres vells
    q = CAU / nom
    if not q.exists(): q.write_bytes(fn())
    return ('fitxer', str(q), 0, q.stat().st_size)
emp = lambda path: sha(path)[:16]
# ---- cantonada: compost de les capes de sota (emulat) a la caixa de l'enquadrament final
box = A5.caixa_cantonada(); log(f'cantonada: caixa {box}')
masks = {lid: np.load(MAS / f'L{lid}_mask.npy', mmap_mode='r') for lid in list(FILTRES) + [3]}
sota = [capa_box(p, 3, box, mask=masks[3])]
for lid in [41, 42, 47, 49, 51, 45, 46, 55, 56]: sota.append(capa_box(p, lid, box, rgb=np.load(FIL / f'{FILTRES[lid]}_u16.npy', mmap_mode='r'), mask=masks[lid]))
for lid in [30, 225, 76, 96, 204, 206, 224, 202]: sota.append(capa_box(p, lid, box))
x0, y0, x1, y1 = box; C, A = comp(sota, y1 - y0, x1 - x0); assert A.min() > 0.999, f'la pila de sota té forats a la caixa de la cantonada ({A.min()})'
crgb, calpha, crebut = A5.calcula(C); crebut.update(caixa=list(box), origen='compost emulat de les capes de sota (a7)')
np.savez_compressed(SORT / 'A7_cantonada.npz', rgb=np.round(crgb * 65535).astype(np.uint16), alpha=np.round(calpha * 65535).astype(np.uint16), box=np.array(box)); desa_json('A7_CANTONADA.json', crebut); log('cantonada calculada: ' + json.dumps({k: crebut[k] for k in ['triangle_px', 'nivell_cel_RGB']}))
# ---- registres i canals de sortida (de baix a dalt)
sortida = []   # (registre serialitzat, [fonts de canal en l'ordre de channel_info])
def afegeix(r, fonts, modificat=True, raw=None):
    if modificat:
        for c, f in zip(r.channel_info, fonts): c.length = f[3]
        b = io.BytesIO(); r.write(b, version=2); raw = b.getvalue()
    sortida.append((raw, fonts))
def fonts_de(psb, lid, rec): return [src_chan(psb, lid, int(c.id)) for c in rec.channel_info]
def renomena(r, nom, lid=None):
    r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
    if lid is not None: r.tagged_blocks.set_data(Tag.LAYER_ID, lid)
rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=sha(SRC)), font_V84=dict(path=str(SRC84.relative_to(ARREL)), sha256=sha(SRC84)), capes=[])
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in FILTRES:
        r = copy.deepcopy(r0); renomena(r, NOMS[lid]); tag = FILTRES[lid]
        rgb = cau_bytes(f'F_{tag}_{emp(FIL / f"{tag}_u16.npy")}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy'))); msk = cau_bytes(f'M_{lid}_{emp(MAS / f"L{lid}_mask.npy")}.bin', lambda: enc(masks[lid]))
        fonts = [{-1: src_chan(p, lid, -1), 0: rgb, 1: rgb, 2: rgb, -2: msk}[int(c.id)] for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=NOMS[lid], canvi='ràster V86 (a3+a4) i màscara A (a6)', visible=bool(r.flags.visible), opacitat=r.opacity)); log(f'capa {lid} {tag}'); continue
    if lid == 3:
        rb_, rawb = rec84[3]; r = copy.deepcopy(rb_); renomena(r, '00 Base V84 · referència oculta', ID_BASE84); r.flags.visible = False
        afegeix(r, fonts_de(p84, 3, r)); rep['capes'].append(dict(id=ID_BASE84, nom='00 Base V84 · referència oculta', canvi='nova: base i màscara originals de la V84', visible=False))
        r = copy.deepcopy(r0); renomena(r, NOMS[3]); msk = cau_bytes(f'M_3_{emp(MAS / "L3_mask.npy")}.bin', lambda: enc(masks[3]))
        fonts = [msk if int(c.id) == -2 else src_chan(p, 3, int(c.id)) for c in r.channel_info]; r.flags.visible = True
        afegeix(r, fonts); rep['capes'].append(dict(id=3, nom=NOMS[3], canvi='píxels de la V85 (verd corregit), màscara A (a6)', visible=True)); continue
    if lid == 225:
        r = copy.deepcopy(r0); r.channel_info = [c for c in r.channel_info if int(c.id) != -2]; r.mask_data = None; r.flags.visible = False
        afegeix(r, fonts_de(p, 225, r)); rep['capes'].append(dict(id=225, nom='Correccions Earthshine V77 17-09', canvi='original de Pere (sense màscara), oculta', visible=False))
        r = copy.deepcopy(r0); renomena(r, 'Correccions V77 · només la Lluna', ID_225LL); r.flags.visible = True
        afegeix(r, fonts_de(p, 225, r)); rep['capes'].append(dict(id=ID_225LL, nom='Correccions V77 · només la Lluna', canvi='nova: la 225 amb la màscara del suport lunar (només la correcció del disc)', visible=True, opacitat=r.opacity)); continue
    if lid == 202:
        afegeix(r0, None, modificat=False, raw=raw0); sortida[-1] = (raw0, fonts_de(p, 202, r0))
        r = copy.deepcopy(rec85[246][0]); renomena(r, 'Cantonada del logo · es regenera', ID_CANT); r.flags.visible = True; r.opacity = 255; r.clipping = 0
        r.left, r.top, r.right, r.bottom = box; cr = np.load(SORT / 'A7_cantonada.npz')
        ch = {0: ('bytes', enc(cr['rgb'][..., 0])), 1: ('bytes', enc(cr['rgb'][..., 1])), 2: ('bytes', enc(cr['rgb'][..., 2])), -1: ('bytes', enc(cr['alpha']))}
        ec = emp(SORT / 'A7_cantonada.npz'); fonts = [cau_bytes(f'C_{int(c.id)}_{ec}.bin', lambda cid=int(c.id): ch[cid][1]) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=ID_CANT, nom='Cantonada del logo · es regenera', canvi='nova: cel continuat (a5), caixa ' + str(list(box)), visible=True)); continue
    if lid == 234:
        r = copy.deepcopy(r0); r.flags.visible = False; md84 = rec84[234][0].mask_data; md85 = r0.mask_data
        assert (md84.left, md84.top, md84.right, md84.bottom, md84.background_color) == (md85.left, md85.top, md85.right, md85.bottom, md85.background_color)
        fonts = [src_chan(p84, 234, -2) if int(c.id) == -2 else src_chan(p, 234, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=234, nom='Pixinisight', canvi='oculta; màscara original de Pere (V84)', visible=False)); continue
    if lid == 252:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, 252, r)); rep['capes'].append(dict(id=252, canvi='placa de Codex, oculta', visible=False)); continue
    sortida.append((raw0, fonts_de(p, lid, r0)))       # capa intacta: registre i canals byte a byte
# ---- escriptura
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[3] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])
count = S['count']; newcount = (abs(count) + 3) * (1 if count > 0 else -1)
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
q = PSB(str(DST)); assert (q.width, q.height) == (W, H) and len(q.layers) == len(p.layers) + 3, (q.width, q.height, len(q.layers))
for lid, tag in FILTRES.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(FIL / f'{tag}_u16.npy')), lid
assert np.array_equal(q.channel(3, -2)[0], np.asarray(masks[3]))
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers), compost_fusionat='PROVISIONAL (el de la V85) fins al desament natiu de Photoshop')
desa_json('A7_MUNTATGE.json', rep); log(f'V86_stage.psb escrit: {len(q.layers)} capes, {DST.stat().st_size/1e9:.2f} GB')
