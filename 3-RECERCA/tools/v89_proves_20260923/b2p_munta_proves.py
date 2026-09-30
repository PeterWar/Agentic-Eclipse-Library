"""b2p · Les proves de la vora esquerra, muntades a partir de la V88 de Pere (desada a les 18:50). Ús: python b2p_munta_proves.py A|B|C
  C · com la B, amb els filtres de la prova C (a3d: a més, el domini dels filtres comença on acaba la Lluna de Pere). 38 capes.
  B · «Només filtres»: les 17 capes de filtre amb els ràsters nous (a3c: els filtres no veuen la pujada dels primers px arran del limbe; a3 i a4
      de la V88). Alfa, màscara, mode, opacitat i visibilitat de Pere, byte a byte. Tota la resta, byte a byte. 38 capes.
  A · «Lluna de l'instant + filtres»: B, i a més (cada canvi en una capa nova; les originals queden OCULTES, intactes):
      · «Lluna a l'instant · prova V89» (just a sobre de la 258): RGB de la 258; alfa = mín(alfa de la 258, perfil radial mitjà de la mateixa alfa
        a dalt i a baix, 60–120° i 240–300°), és a dir, la vora que Pere ja té allà, a tots els azimuts: treu el tros que sobresurt (la Lluna
        sumada al llarg del temps) i respecta els seus retalls (p. ex. la protuberància de dalt);
      · «00 Base · vora de l'instant · prova V89» (just a sobre de la 3): la base amb el forat de dades arran del limbe omplert per continuació
        radial des de 1,5 px fora de la seva vora (la base és cremada allà: el valor és pla) i la màscara oberta on la Lluna ja no és opaca;
      · màscares de les 17 capes de filtre: on la Lluna de la V88 era opaca i la nova no, el valor de la màscara de Pere de just a fora de la
        franja (recepta a6 de la V86). 40 capes.
Sortida: 4-RESULTATS/v89_proves_20260923/V89_prova_<A|B>.psb i B2P_<A|B>.json. Mai sobreescriu."""
from v89_comu import *
from psb69 import PSB, BIG_KEYS, _rf
from v86_operadors import smoothstep
import struct, zlib, io, copy, logging, cv2
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim(); OPCIO = sys.argv[1]; assert OPCIO in ('A', 'B', 'C')
SRC = ARREL / '1-PHOTOSHOP/V88.psb'; SHA_SRC = '04f7adedc28c41b89e15b35dbd71d1819ff34983407cfc0bbe2458ea9e6cfc78'
DST = SORT / f'V89_prova_{OPCIO}.psb'; assert not DST.exists(), 'no-clobber'
FIL = SORT / ('C/filtres_finals' if OPCIO == 'C' else 'filtres_finals'); CAU = SORT / 'canals_psb'; CAU.mkdir(exist_ok=True)
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
ID_LLUNA, ID_BASE, ID_LLUNA_NOVA, ID_BASE_NOVA = 258, 3, 263, 264
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
assert sha(SRC) == SHA_SRC, 'la V88 de Pere ha canviat des de les 18:50: cal tornar a mirar-la'
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
        r = copy.deepcopy(r0); nom = nom_de(r0).replace('· V88', '· V89 prova' + (' C' if OPCIO == 'C' else '')); renomena(r, nom); tag = FILTRES[lid]
        rgb = cau_bytes(f'F_{tag}_{emp(FIL / f"{tag}_u16.npy")}.bin', lambda: enc(np.load(FIL / f'{tag}_u16.npy')))
        if OPCIO == 'A':
            mk = cau_bytes(f'M_{lid}_{hashlib.sha256(MASC[lid].tobytes()).hexdigest()[:16]}.bin', lambda: enc(MASC[lid]))
            fonts = [{0: rgb, 1: rgb, 2: rgb, -2: mk}[int(c.id)] if int(c.id) in (0, 1, 2, -2) else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        else: fonts = [rgb if int(c.id) in (0, 1, 2) else src_chan(p, lid, int(c.id)) for c in r.channel_info]
        afegeix(r, fonts); rep['capes'].append(dict(id=lid, nom=nom, canvi='ràster nou (a3c) ' + ('i màscara oberta on la Lluna nova ja no és opaca' if OPCIO == 'A' else '; màscara de Pere'))); continue
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
    sortida.append((raw0, fonts_de(p, lid, r0)))
# ---- escriptura
extra = 2 if OPCIO == 'A' else 0
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
rep.update(desti=str(DST.relative_to(ARREL)), mida=DST.stat().st_size, capes_total=len(q.layers), compost_fusionat='el de la V88 de Pere (Photoshop el refà en obrir)')
desa_json(f'B2P_{OPCIO}.json', rep); log(f'{DST.name} escrit: {len(q.layers)} capes, {DST.stat().st_size / 1e9:.2f} GB')
