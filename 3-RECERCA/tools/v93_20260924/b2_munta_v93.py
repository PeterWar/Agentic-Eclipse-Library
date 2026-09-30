"""b2 · Munta V93_stage.psb a partir de la V92 de Pere desada a les 01:34 (Photoshop la desarà de manera nativa com a 1-PHOTOSHOP/V93.psb).
Encàrrec de Pere (24-09, nit: capa «Artefactes V92», /goal «fes V93», de manera desatesa):
  (1) 16 capes de filtre «· V93»: als píxels sense dada tocant la Lluna, NOMÉS EL NIVELL (a4v; la V92 hi feia mirall de la textura i Pere hi
      va veure el mirall, línia grisa), i a l'esquerra (104–228°) es treuen només les línies coherents al llarg del limbe (a5d) en lloc del
      suavitzat radial, que s'enduia la textura (marques verdes);
  (2) restes de màscares a la zona de l'Earthshine: les màscares de la 56 (WOW bilateral), la 76, la 96 i la 224 queden a 0 NOMÉS on la 258
      és del tot opaca i a més de 8 px dins del limbe (zona_earthshine.npz). Fora d'aquesta zona, byte a byte;
  la capa de marques «Artefactes V92» (269) queda OCULTA. Tota la resta, byte a byte. Mai sobreescriu."""
from v93_comu import *
from psb69 import PSB, BIG_KEYS, _rf
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
import struct, zlib, io, copy, logging
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim(); SRC = PSB_PERE; SHA_SRC = '2850f1bd39a5d8a64a2ce610088977d9a92ce69297acdec6f2c8ab3ba3ab1077'; DST = SORT / 'V93_stage.psb'; assert not DST.exists(), 'no-clobber'
assert sha(SRC) == SHA_SRC, 'la V92 de Pere ha canviat des de les 01:34'
FIL = SORT / 'filtres_v93'; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True); NETEJA = (56, 76, 96, 224)
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
            pos = f.tell(); r = LayerRecord.read(f, version=2); end = f.tell(); f.seek(pos); recs.append((r, f.read(end - pos)))
    return dict(lmpos=lmpos, lmlen=lmlen, lenpos=lenpos, lrstart=start, lrpadend=start + (n + 3) // 4 * 4, count=count, recs=recs)
rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID)); nom_de = lambda r: str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))
def renomena(r, nom): r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
def cau_bytes(nom, fn):
    q = CAU / nom
    if not q.exists(): q.write_bytes(fn())
    return ('fitxer', str(q), 0, q.stat().st_size)
p = PSB(str(SRC)); S = llegeix_registres(SRC); ids = [rid(r) for r, _ in S['recs']]; assert all(k in ids for k in FILTRES) and 269 in ids
src_chan = lambda lid, cid: ('fitxer', str(SRC), *p.layer(lid)['chans'][cid])
Z = np.load(SORT / 'zona_earthshine.npz'); zona = Z['zona']; zx, zy = [int(v) for v in Z['origen']]
MASC = {}
for lid in NETEJA:
    m, (ox, oy) = p.channel(lid, -2); m = m.copy(); hz, wz = zona.shape
    ys, xs = np.nonzero(zona); X, Y = xs + zx - ox, ys + zy - oy; ok = (X >= 0) & (Y >= 0) & (X < m.shape[1]) & (Y < m.shape[0]); abans = int((m[Y[ok], X[ok]] > 0).sum())
    m[Y[ok], X[ok]] = 0; MASC[lid] = (m, abans); log(f'màscara {lid}: {abans} px de la zona passen a 0')
rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), capes=[]); sortida = []
def afegeix(r, fonts):
    for c, f in zip(r.channel_info, fonts): c.length = f[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in FILTRES or lid in NETEJA or lid == 269:
        r = copy.deepcopy(r0); fonts = []
        if lid in FILTRES: nom = nom_de(r0).replace('· V92', '· V93'); renomena(r, nom); tag = FILTRES[lid]; rgb = cau_bytes(f'F_{tag}_{sha(FIL / f"{tag}_u16.npy")[:16]}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy')))
        if lid == 269: r.flags.visible = False
        for c in r.channel_info:
            cid = int(c.id)
            if lid in FILTRES and cid in (0, 1, 2): fonts.append(rgb)
            elif lid in NETEJA and cid == -2: m = MASC[lid][0]; fonts.append(cau_bytes(f'M_{lid}_{hashlib.sha256(m.tobytes()).hexdigest()[:16]}.bin', lambda: enc(m)))
            else: fonts.append(src_chan(lid, cid))
        afegeix(r, fonts)
        canvi = []
        if lid in FILTRES: canvi.append('ràster V88 amb continuació només de nivell (a4v) i línies coherents fora a 104–228° (a5d)')
        if lid in NETEJA: canvi.append(f'màscara a 0 a la zona opaca de l\'Earthshine ({MASC[lid][1]} px que no ho eren)')
        if lid == 269: canvi.append('marques de Pere, intactes i OCULTES')
        rep['capes'].append(dict(id=lid, nom=nom_de(r), canvi='; '.join(canvi))); continue
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
assert sha(SRC) == SHA_SRC
q = PSB(str(DST)); assert (q.width, q.height) == (W, H) and len(q.layers) == len(p.layers)
for lid, tag in FILTRES.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(FIL / f'{tag}_u16.npy')), lid
for lid in NETEJA: assert np.array_equal(q.channel(lid, -2)[0], MASC[lid][0]), lid
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers)); desa_json('B2_MUNTATGE.json', rep); log(f'{DST.name} escrit: {len(q.layers)} capes, {DST.stat().st_size / 1e9:.2f} GB')
