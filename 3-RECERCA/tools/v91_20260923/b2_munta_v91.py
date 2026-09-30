"""b2 · Munta V91_stage.psb a partir de la V90 de Pere (desada a les 22:06, amb la seva màscara nova de la 56; la de les 21:43 va donar el primer desament, retirat; Photoshop la desarà de manera nativa com a 1-PHOTOSHOP/V91.psb).
Encàrrec de Pere (23-09, nit; capa «Artefactes V90»; resposta «Sí, les dues coses»):
  (1) 16 capes de filtre «· V91»: ràsters de la V88 amb el suavitzat radial prop del limbe NOMÉS on hi havia les línies, 104–228° (a5c;
      el primer criteri, a5b, l'alçada del limbe, encara suavitzava a 230–258°, on hi ha la lent);
      a la V90 s'aplicava a tot el voltant i a dalt, a baix i a la dreta feia una «lent» (marques roses);
  (2) capa nova «Protuberància esquerra · guspires de la foto 76» (Sobreexposició lineal, 100 %; p1) just a sobre de la 224 (a sobre de les fotos
      de Pere): les guspires de la 76 que la 76 i la 266 en «Aclarir» no podien mostrar sobre la corona (marques liles);
  la capa de marques «Artefactes V90» (264) queda OCULTA. Tota la resta (266 inclosa) byte a byte. 40 capes. Mai sobreescriu."""
from v91_comu import *
from psd_tools.constants import BlendMode
from psb69 import PSB, BIG_KEYS, _rf
from v86_operadors import smoothstep
import struct, zlib, io, copy, logging, cv2
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim(); OPCIO = 'B'
SRC = ARREL / '1-PHOTOSHOP/V90.psb'; SHA_SRC = '5a9233ac85554321ac75c0d43d1c43ab69e86b1861c7f488aef4369fba9ac70d'
DST = SORT / 'V91_stage.psb'; assert not DST.exists(), 'no-clobber'
FIL = SORT / 'filtres_radial_c'; CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True)
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
ID_LLUNA, ID_BASE, ID_LLUNA_NOVA, ID_BASE_NOVA = 258, 3, 268, 269   # (no s'usen a la V91; 264 és la capa de marques de Pere)
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
assert sha(SRC) == SHA_SRC, 'la V90 de Pere ha canviat des de les 22:06: cal tornar a mirar-la'
p = PSB(str(SRC)); S = llegeix_registres(SRC); ids = [rid(r) for r, _ in S['recs']]
assert ID_LLUNA_NOVA not in ids and ID_BASE_NOVA not in ids and all(k in ids for k in FILTRES)
rep = dict(opcio=OPCIO, font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), capes=[])
# ---- opció A: alfa de l'instant, base omplerta, màscares
if OPCIO == 'A':
    geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
    a258, org = p.channel(ID_LLUNA, -1); a258 = a258.astype(np.float32) / 65535; lx0, ly0 = org; lh, lw = a258.shape
    yl, xl = np.mgrid[ly0:ly0 + lh, lx0:lx0 + lw]; dl = np.hypot(xl - cx, yl - cy) - R; tl = (np.degrees(np.arctan2(-(yl - cy), xl - cx)) + 360) % 360
    selc = (((tl >= 60) & (tl <= 120)) | ((tl >= 240) & (tl <= 300))) & (np.abs(dl) < 8); bins = np.arange(-8, 8.01, 0.25)
    prof = np.array([np.median(a258[selc & (np.abs(dl - b) < 0.125)]) for b in bins]); prof = np.maximum.accumulate(prof[::-1])[::-1]
    a_new = np.minimum(a258, np.interp(dl, bins, prof, left=1.0, right=0.0)).astype(np.float32)
    rep['alfa_nova'] = dict(perfil_d=bins.tolist(), perfil_alfa=np.round(prof, 4).tolist(), px_que_baixen=int((a_new < a258 - 1 / 255).sum()))
    op_old = np.zeros((H, W), bool); op_new = np.zeros((H, W), bool); op_old[ly0:ly0 + lh, lx0:lx0 + lw] = a258 >= 0.999; op_new[ly0:ly0 + lh, lx0:lx0 + lw] = a_new >= 0.999
    allib = op_old & ~op_new; rep['px_opacs_que_deixen_de_ser_ho'] = int(allib.sum())
    g = np.load(SORT / 'A2_geometria.npz'); by0, by1, bx0, bx1 = [int(v) for v in g['box']]; rb = g['rb_s']; NB = len(rb); MU = 6.0
    yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
    ib = (th / 360 * NB).astype(int) % NB; RB = rb[ib]; zona = rL <= RB + 3 * MU; anell_ext = (rL > RB + 3 * MU + 2) & (rL <= RB + 3 * MU + 8)
    def full_mask(lid):
        L = p.layer(lid); m, (ox, oy) = p.channel(lid, -2); full = np.full((H, W), 65535 if L['mask']['background'] == 255 else 0, np.uint16); h_, w_ = m.shape
        full[max(oy, 0):min(oy + h_, H), max(ox, 0):min(ox + w_, W)] = m[max(oy, 0) - oy:min(oy + h_, H) - oy, max(ox, 0) - ox:min(ox + w_, W) - ox]; return full
    MASC = {}; rep['mascares'] = {}
    for lid in FILTRES:
        L = p.layer(lid); assert L['mask'] is not None and (L['mask']['left'], L['mask']['top'], L['mask']['right'], L['mask']['bottom']) == (0, 0, W, H), (lid, L['mask'])
        full = full_mask(lid); box = full[by0:by1, bx0:bx1].astype(np.float32) / 65535; ext = np.full(NB, np.nan)
        for k in range(NB):
            v = box[anell_ext & (ib == k)]
            if v.size: ext[k] = np.median(v)
        ok = np.isfinite(ext); ext[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), ext[ok], period=NB); ext = gaussian_filter1d(ext, 2, mode='wrap')
        dz = zona & ~op_old[by0:by1, bx0:bx1]; dev = float(np.abs(box[dz] - ext[ib][dz]).max()) if dz.any() else 0.0
        new = np.where(allib[by0:by1, bx0:bx1], ext[ib], box); full[by0:by1, bx0:bx1] = np.round(np.clip(new, 0, 1) * 65535).astype(np.uint16); MASC[lid] = full
        rep['mascares'][lid] = dict(desviacio_max_de_la_recepta_a6_a_la_zona=round(dev, 4), mitjana_ext=round(float(ext.mean()), 4))
    L3 = p.layer(ID_BASE); assert (L3['mask']['left'], L3['mask']['top'], L3['mask']['right'], L3['mask']['bottom']) == (0, 0, W, H)
    m3 = full_mask(ID_BASE); m3n = np.where(allib, 65535, m3).astype(np.uint16)
    # base: forat de dades arran del limbe → continuació radial des de 1,5 px fora de la seva vora (per azimut, 0,25°)
    bb = (by0, by1, bx0, bx1); base = np.stack([p.channel_box(ID_BASE, c, (bx0, by0, bx1, by1)) for c in range(3)], -1).astype(np.float32) / 65535
    dL = rL - R; lum = 0.3 * base[..., 0] + 0.59 * base[..., 1] + 0.11 * base[..., 2]; forat = (lum < 0.02) & (dL > -12) & (dL < 10)
    NBZ = 1440; ibz = (th / 360 * NBZ).astype(int) % NBZ; crua = np.full(NBZ, -12.0)
    for k in range(NBZ):
        s = forat & (ibz == k)
        if s.any(): crua[k] = dL[s].max()
    vora = gaussian_filter1d(maximum_filter1d(crua, 5, mode='wrap'), 4, mode='wrap'); vora = np.maximum(vora, maximum_filter1d(crua, 3, mode='wrap'))   # llisa i mai per sota d'un píxel del forat
    rref = R + vora[ibz] + 1.5; ang = np.radians(th)
    MX = (cx + rref * np.cos(ang) - bx0).astype(np.float32); MY = (cy - rref * np.sin(ang) - by0).astype(np.float32)
    w_ = smoothstep(dL, vora[ibz], vora[ibz] + 1.5).astype(np.float32); omple = (dL > -12) & (dL < vora[ibz] + 1.5)
    base_n = base.copy()
    for c in range(3):
        ref = cv2.remap(base[..., c], MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); base_n[..., c] = np.where(omple, w_ * base[..., c] + (1 - w_) * ref, base[..., c])
    BASE_RGB = {c: np.asarray(p.channel(ID_BASE, c)[0]).copy() for c in range(3)}; assert p.channel(ID_BASE, 0)[1] == (0, 0)
    for c in range(3): BASE_RGB[c][by0:by1, bx0:bx1] = np.round(np.clip(base_n[..., c], 0, 1) * 65535).astype(np.uint16)
    rep['base'] = dict(vora_forat_px_per_sector={f'{a}-{a + 30}': round(float(np.mean(vora[int(a * 4):int((a + 30) * 4)])), 2) for a in range(0, 360, 30)}, px_omplerts=int((omple & (w_ < 0.999)).sum()))
    np.savez_compressed(SORT / f'B2P_A_dades.npz', a_new=np.round(a_new * 65535).astype(np.uint16), org=np.array(org), vora_forat=vora)
# ---- registres i canals de sortida
sortida = []
def afegeix(r, fonts):
    for c, f in zip(r.channel_info, fonts): c.length = f[3]
    b = io.BytesIO(); r.write(b, version=2); sortida.append((b.getvalue(), fonts))
def fonts_de(psb, lid, rec): return [src_chan(psb, lid, int(c.id)) for c in rec.channel_info]
for r0, raw0 in S['recs']:
    lid = rid(r0)
    if lid in FILTRES:
        r = copy.deepcopy(r0); nom = nom_de(r0).replace('· V90', '· V91'); renomena(r, nom); tag = FILTRES[lid]
        rgb = cau_bytes(f'F_{tag}_{emp(FIL / f"{tag}_u16.npy")}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy')))
        if OPCIO == 'A':
            mk = cau_bytes(f'M_{lid}_{hashlib.sha256(MASC[lid].tobytes()).hexdigest()[:16]}.bin', lambda: enc(MASC[lid]))
            fonts = [{0: rgb, 1: rgb, 2: rgb, -2: mk}[int(c.id)] if int(c.id) in (0, 1, 2, -2) else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        else: fonts = [rgb if int(c.id) in (0, 1, 2) else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=nom, canvi='ràster V88 amb suavitzat radial prop del limbe només on hi havia les línies, 104–228° (a5c); màscara, mode, opacitat i visibilitat de Pere')); continue
    if OPCIO == 'A' and lid == ID_BASE:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, lid, r)); rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='intacta, OCULTA'))
        r = copy.deepcopy(r0); renomena(r, "00 Base · vora de l'instant · prova V89", ID_BASE_NOVA); r.flags.visible = True
        hb = hashlib.sha256(b''.join(BASE_RGB[c].tobytes() for c in range(3)) + m3n.tobytes()).hexdigest()[:16]
        ch = {0: lambda: enc(BASE_RGB[0]), 1: lambda: enc(BASE_RGB[1]), 2: lambda: enc(BASE_RGB[2]), -2: lambda: enc(m3n)}
        fonts = [cau_bytes(f'B_{int(c.id)}_{hb}.bin', ch[int(c.id)]) if int(c.id) in ch else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=ID_BASE_NOVA, nom=nom_de(r), canvi='nova: base amb el forat arran del limbe omplert i màscara oberta on la Lluna nova no és opaca')); continue
    if OPCIO == 'A' and lid == ID_LLUNA:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, lid, r)); rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='intacta, OCULTA'))
        r = copy.deepcopy(r0); renomena(r, "Lluna a l'instant · prova V89", ID_LLUNA_NOVA); r.flags.visible = True
        an = np.round(a_new * 65535).astype(np.uint16); ha = hashlib.sha256(an.tobytes()).hexdigest()[:16]
        fonts = [cau_bytes(f'L_{ha}.bin', lambda: enc(an)) if int(c.id) == -1 else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=ID_LLUNA_NOVA, nom=nom_de(r), canvi="nova: RGB de la 258; alfa de l'instant (vora de dalt i de baix de Pere a tots els azimuts)")); continue
    if lid == 264:
        r = copy.deepcopy(r0); r.flags.visible = False; afegeix(r, fonts_de(p, lid, r)); rep['capes'].append(dict(id=lid, nom=nom_de(r0), canvi='marques de Pere, intactes i OCULTES')); continue
    sortida.append((raw0, fonts_de(p, lid, r0)))
    if lid == 224:
        P1 = np.load(SORT / 'P1_PROTUBERANCIA.npz'); bx = [int(v) for v in P1['caixa']]; rgbP, alP = P1['rgb'], P1['alfa']
        r = copy.deepcopy(dict((rid(rr), rr) for rr, _ in S['recs'])[258]); renomena(r, 'Protuberància esquerra · guspires de la foto 76', 267)
        r.left, r.top, r.right, r.bottom = bx[0], bx[1], bx[2], bx[3]; r.blend_mode = BlendMode.LINEAR_DODGE; r.opacity = 255; r.clipping = 0; r.flags.visible = True
        assert [int(c.id) for c in r.channel_info] == [-1, 0, 1, 2] and r.mask_data is None, [int(c.id) for c in r.channel_info]
        hp = hashlib.sha256(rgbP.tobytes() + alP.tobytes()).hexdigest()[:16]; ch = {-1: lambda: enc(alP), 0: lambda: enc(rgbP[..., 0]), 1: lambda: enc(rgbP[..., 1]), 2: lambda: enc(rgbP[..., 2])}
        afegeix(r, [cau_bytes(f'P_{int(c.id)}_{hp}.bin', ch[int(c.id)]) for c in r.channel_info])
        rep['capes'].append(dict(id=267, nom='Protuberància esquerra · guspires de la foto 76', canvi='nova: top-hat de la 76 amb realç ×3 fora del cos (p1), Sobreexposició lineal 100 %, a sobre de la 224'))
# ---- escriptura
extra = 1
recbytes = b''.join(raw for raw, _ in sortida); total = sum(f[3] for _, fs in sortida for f in fs)
newlen = 2 + len(recbytes) + total; newpad = (newlen + 3) // 4 * 4; newlmlen = S['lmlen'] + newpad - (S['lrpadend'] - S['lrstart'])
count = S['count']; newcount = (abs(count) + extra) * (1 if count > 0 else -1)
def copia(g_, f, a, b):
    f.seek(a)
    while f.tell() < b: g_.write(f.read(min(64 << 20, b - f.tell())))
obert = {}
def llegeix_font(g_, font):
    kind, path, off, n = font
    if path not in obert: obert[path] = open(path, 'rb')
    copia(g_, obert[path], off, off + n)
with open(SRC, 'rb') as f, open(DST, 'xb') as g_:
    copia(g_, f, 0, S['lmpos']); g_.write(struct.pack('>Q', newlmlen)); copia(g_, f, S['lmpos'] + 8, S['lenpos']); g_.write(struct.pack('>Q', newlen))
    g_.write(struct.pack('>h', newcount)); g_.write(recbytes)
    for raw, fonts in sortida:
        for font in fonts: llegeix_font(g_, font)
    g_.write(b'\0' * (newpad - newlen)); copia(g_, f, S['lrpadend'], SRC.stat().st_size)
for fh in obert.values(): fh.close()
q = PSB(str(DST)); assert (q.width, q.height) == (W, H) and len(q.layers) == len(p.layers) + extra, (len(q.layers), len(p.layers))
for lid, tag in FILTRES.items(): assert np.array_equal(q.channel(lid, 1)[0], np.load(FIL / f'{tag}_u16.npy')), lid
if OPCIO == 'A':
    assert np.array_equal(q.channel(ID_LLUNA_NOVA, -1)[0], np.round(a_new * 65535).astype(np.uint16)) and np.array_equal(q.channel(ID_BASE_NOVA, -2)[0], m3n)
    for lid in FILTRES: assert np.array_equal(q.channel(lid, -2)[0], MASC[lid]), lid
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers), compost_fusionat='PROVISIONAL (el de la V88 de Pere) fins al desament natiu de Photoshop')
desa_json('B2_MUNTATGE.json', rep); log(f'{DST.name} escrit: {len(q.layers)} capes, {DST.stat().st_size / 1e9:.2f} GB')
