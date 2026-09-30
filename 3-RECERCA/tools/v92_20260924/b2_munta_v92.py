"""b2 · Munta V92_stage.psb a partir de la V91 de Pere tal com l'hagi desada (Photoshop la desarà de manera nativa com a 1-PHOTOSHOP/V92.psb).
Encàrrec de Pere (24-09, matinada: «encara veig una mica d'efecte lent … més o menys en el mateix lloc que la marca d'Artefactes V90, però més
subtil»; «artefactes grisos en la protuberància esquerra», marcats a la 264):
  (1) 16 capes de filtre «· V92»: la continuació dels píxels sense dada plena tocant la Lluna es fa amb MIRALL DE LA TEXTURA (a4m) en lloc de
      copiar-la al llarg del radi (a4 de la V88), i després el suavitzat radial de la V91 a 104–228° (a5c). Treu la vora fina de lent;
  (2) capa 267 «Protuberància esquerra · guspires de la foto 76»: el mateix detall pintat amb el COLOR REAL de les guspires a la 76 (p1b)
      en lloc del rosa del cos, que destenyia la corona cap al gris. L'alfa és la de Pere (ell n'havia esborrat un tros), byte a byte.
Tota la resta de la V91 de Pere, byte a byte (màscares, modes, opacitats, visibilitats; la 264 tal com la tingui). Mai sobreescriu."""
from pathlib import Path
import sys, json, hashlib, struct, zlib, io, copy, logging, time
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB, BIG_KEYS, _rf
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
SRC = ARREL / '1-PHOTOSHOP/V91.psb'; DST = SORT / 'V92_stage.psb'; assert not DST.exists(), 'no-clobber'
FIL = SORT / 'filtres_v92'; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True); H, W = 7506, 10551
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
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
SHA_SRC = sha(SRC); log(f'font: V91 de Pere, SHA {SHA_SRC[:16]}…, {time.strftime("%F %T", time.localtime(SRC.stat().st_mtime))}')
p = PSB(str(SRC)); S = llegeix_registres(SRC); ids = [rid(r) for r, _ in S['recs']]; assert all(k in ids for k in FILTRES) and 267 in ids, ids
src_chan = lambda lid, cid: ('fitxer', str(SRC), *p.layer(lid)['chans'][cid])
Z = np.load(SORT / 'P1B_GUSPIRES.npz'); zb = [int(v) for v in Z['caixa']]; L267 = p.layer(267); b267 = (L267['left'], L267['top'], L267['right'], L267['bottom'])
assert zb[0] <= b267[0] and zb[1] <= b267[1] and b267[2] <= zb[2] and b267[3] <= zb[3], (zb, b267)
rgb267 = Z['rgb'][b267[1] - zb[1]:b267[3] - zb[1], b267[0] - zb[0]:b267[2] - zb[0]]; h267 = hashlib.sha256(rgb267.tobytes()).hexdigest()[:16]
rep = dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), capes=[]); sortida = []
def afegeix(r, fonts):
    for c, f in zip(r.channel_info, fonts): c.length = f[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in FILTRES:
        r = copy.deepcopy(r0); nom = nom_de(r0).replace('· V91', '· V92'); renomena(r, nom); tag = FILTRES[lid]
        rgb = cau_bytes(f'F_{tag}_{sha(FIL / f"{tag}_u16.npy")[:16]}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy')))
        afegeix(r, [rgb if int(c.id) in (0, 1, 2) else src_chan(lid, int(c.id)) for c in r.channel_info])
        rep['capes'].append(dict(id=lid, nom=nom, canvi='ràster V88 amb la continuació amb mirall (a4m) i el suavitzat radial a 104–228° (a5c); màscara, alfa, mode, opacitat i visibilitat de Pere')); continue
    if lid == 267:
        r = copy.deepcopy(r0); fonts = [cau_bytes(f'G_{int(c.id)}_{h267}.bin', (lambda cc: (lambda: enc(rgb267[..., cc])))(int(c.id))) if int(c.id) in (0, 1, 2) else src_chan(lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='RGB amb el color real de les guspires (p1b); alfa de Pere byte a byte')); continue
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
assert sha(SRC) == SHA_SRC, 'la V91 de Pere ha canviat durant el muntatge: cal tornar-hi'
q = PSB(str(DST)); assert (q.width, q.height) == (W, H) and len(q.layers) == len(p.layers)
for lid, tag in FILTRES.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(FIL / f'{tag}_u16.npy')), lid
assert np.array_equal(q.channel(267, 0)[0], rgb267[..., 0]) and np.array_equal(q.channel(267, -1)[0], p.channel(267, -1)[0])
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers))
(SORT / 'B2_MUNTATGE.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log(f'{DST.name} escrit: {len(q.layers)} capes, {DST.stat().st_size / 1e9:.2f} GB')
