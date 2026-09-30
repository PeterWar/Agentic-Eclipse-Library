"""C4 (V38) · V38.psb PROJECTE COMPLET (ordre de Pere, 08-09 nit): totes les capes de la V32 (les 13 de Pere, Fons per raig, earthshine ×4,
les dues bases V32, Estrelles, Reflex, NAFE/precursors/SWAP/C01) + la base lineal V38 + els filtres V38 (01/02/04/05/06, 03 r0/r4/07 recuperades,
P01–P05 i P01b amb μ/σ extrapolats) amb LA LLUNA A L'INICI (t 15 s): les cinc capes fixes a la Lluna (earthshine ×4 i Reflex) desplaçades
(+15, +1) px (centre lunar mesurat a (+14,8, +0,9) del Sol) i TOTES les capes de base i de filtre amb màscara nova = fora del disc de la
Lluna a l'inici (R 455,5 px + 2 px de guarda, vora suau de 2 px). Les capes de Pere (01–13), Fons per raig i Estrelles: byte a byte.
Compost per defecte: les capes visibles (12, 11, Earthshine V24e, base V38, 03 r4, 01, 02, Estrelles, Reflex) com a la V32.
Ús: build | verify | gate | publish."""
from comu38 import *
import copy, gc, subprocess, shutil, datetime
sys.path.insert(0, str(ROOT / 'research/tools/v29')); sys.path.insert(0, str(ROOT / 'research/tools/encaix_sony'))
from inspect_inputs import channel
from psb_utils import finalize_lr16
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression, BlendMode, ChannelID
from psd_tools.psd.layer_and_mask import LayerRecord, ChannelInfo, ChannelData, ChannelDataList, MaskData, MaskFlags
from psd_tools.psd.tagged_blocks import TaggedBlocks
from psd_tools.psd.image_data import ImageData
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
FONT = CT / 'V32.psb'; FONT_SHA = 'dcfc8f531e286bfdf529d20880c9772785a38a4e6d0c09094883a7c8f7743c7d'
STAGING = HERE38 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'V38.psb'; FINAL = CT / 'V38.psb'
PC38 = HERE38 / 'purs/cau'; FW, FH = W, H
DESPL = (15, 1)                       # (dx, dy) enters: centre lunar a l'INICI = Sol + (14,8, 0,9)
CXL, CYL = CX + 14.8, CY + 0.9; RL_PX = 455.5018; GUARDA = 2.0
CLAIM = 'CLAUDE_V38_FRANJA_20260908'
# (tipus, nom a V32, nom nou, ruta u16 | None, visible | None=com V32)
PLA = [
    ('copy', '12 1/3200 perles', None, None, None), ('copy', '11 1/500 limbe', None, None, None), ('copy', '10 1/125', None, None, None), ('copy', '09 1/60 x2', None, None, None),
    ('copy', '08 1/30 x4 quar', None, None, None), ('copy', '07 1/15 x2 quar', None, None, None), ('copy', '06 1/8 x4 quar', None, None, None), ('copy', '05 1/4 x2 quar', None, None, None),
    ('copy', '04 1/2 x4 quar', None, None, None), ('copy', '03 1s x2 quar', None, None, None), ('copy', '02 2s x3 quar', None, None, None), ('copy', '01 10.3s x3 quar', None, None, None),
    ('copy', '13 Sony >1s', None, None, None), ('copy', 'Fons per raig', None, None, None),
    ('moon', 'Earthshine v2', None, None, None), ('moon', 'Compara D87', None, None, None), ('moon', 'Compara LROC', None, None, None), ('moon', 'Earthshine V24e', None, None, None),
    ('copy_newmask', '00 Base amb cel', '00 Base amb cel · V32', None, False), ('copy_newmask', '00 Base (cel/4)', '00 Base (cel/4) · V32', None, False),
    ('base', None, '00 Base lineal · V38', None, True),
    ('u16', '03 ACHF azimutal 8-128 r0 · V32', '03 ACHF azimutal 8-128 r0 · V38', CAU38 / '03_v38_u16.npy', None),
    ('u16', '03 ACHF azimutal 8-128 r4 · V32', '03 ACHF azimutal 8-128 r4 · V38', CAU38 / '03v30_v38_u16.npy', None),
    ('u16', '07 ACHF azimutal suau r8 · V32', '07 ACHF azimutal suau r8 · V38', CAU38 / '07_v38_u16.npy', None),
    ('u16', '01 ACHF fi 2-32 · V32', '01 ACHF fi 2-32 · V38', CAU38 / '01_v38_u16.npy', None), ('u16', '02 Passa-alt 24 · V32', '02 Passa-alt 24 · V38', CAU38 / '02_v38_u16.npy', None),
    ('u16', '04 ACHF micro 1-16 · V32', '04 ACHF micro 1-16 · V38', CAU38 / '04_v38_u16.npy', None), ('u16', '05 ACHF fi 2-48 · V32', '05 ACHF fi 2-48 · V38', CAU38 / '05_v38_u16.npy', None),
    ('u16', '06 ACHF estructura 4-64 · V32', '06 ACHF estructura 4-64 · V38', CAU38 / '06_v38_u16.npy', None),
    ('copy', 'Estrelles', None, None, None), ('moon', 'Reflex', None, None, None),
    ('u16', 'P01 NRGF · V32', 'P01 NRGF · V38', PC38 / 'P01_NRGF_u16.npy', None), ('u16', 'P01 NRGF · V32', 'P01b NRGF (μσ dels anells parcials extrapolats) · V38', PC38 / 'P01_NRGF_extrap_u16.npy', False),
    ('u16', 'P02 RHEF · comparacio amb anells · V32', 'P02 RHEF · V38', PC38 / 'P02_RHEF_u16.npy', None), ('u16', 'P03 MGN · V32', 'P03 MGN · V38', PC38 / 'P03_MGN_u16.npy', None),
    ('u16', 'P04 WOW sense denoise · V32', 'P04 WOW · V38', PC38 / 'P04_WOW_u16.npy', None), ('u16', 'P05 WOW bilateral sense denoise · V32', 'P05 WOW bilateral · V38', PC38 / 'P05_WOW_bilateral_u16.npy', None),
    ('copy_newmask', 'P06 NAFE n65 · V32', None, None, None), ('copy_newmask', 'P07 ACHF precursor sigma16 · V32', None, None, None), ('copy_newmask', 'P08 ACHF precursor sigma32 · V32', None, None, None),
    ('copy_newmask', 'P09 SWAP · pilot llum blanca · V32', None, None, None), ('copy_newmask', 'C01 Passa-alt24 lineal · control · V32', None, None, None),
]
_MASK = {}


def mascara_lluna_inici():
    """Màscara u16 de tot el llenç: 0 dins del disc de la Lluna a l'inici (R + guarda), rampa de 2 px, 65535 fora."""
    if 'm' not in _MASK:
        yy, xx = np.mgrid[0:FH, 0:FW]; d = np.hypot(xx - CXL, yy - CYL); _MASK['m'] = np.round(np.clip((d - (RL_PX + GUARDA - 1.0)) / 2.0, 0, 1) * 65535).astype(np.uint16)
    return _MASK['m']


def roll_mask(mk):
    """Desplaça una màscara de tot el llenç (+dx, +dy); el que entra pels marges és 0 (les màscares fixes a la Lluna són 0 lluny del disc)."""
    out = np.zeros_like(mk); dx, dy = DESPL; out[dy:, dx:] = mk[:FH - dy, :FW - dx]; return out


def compressed(u, w, h):
    cd = ChannelData(Compression.ZIP); cd.set_data(np.ascontiguousarray(np.asarray(u).astype('>u2')).tobytes(), w, h, 16, 2); return cd


def add_layer(s, rgb_u16, name, alpha_u16, mask_u16, mask_box, mask_bg, blend, opacity, visible, box):
    l0, t0, r0, b0 = box; w, h = r0 - l0, b0 - t0
    rec = LayerRecord(top=t0, left=l0, bottom=b0, right=r0, channel_info=[]); rec.tagged_blocks = TaggedBlocks(); rec.name = name
    chans = ChannelDataList(); alpha = compressed(np.full((h, w), 65535, np.uint16) if alpha_u16 is None else alpha_u16, w, h)
    cols = [compressed(rgb_u16, w, h)] * 3 if rgb_u16.ndim == 2 else [compressed(rgb_u16[..., c], w, h) for c in range(3)]
    pairs = [(-1, alpha), (0, cols[0]), (1, cols[1]), (2, cols[2])]
    if mask_u16 is not None:
        ml, mt, mr, mb = mask_box; mcd = compressed(mask_u16, mr - ml, mb - mt); pairs.append((-2, mcd)); rec.mask_data = MaskData(top=mt, left=ml, bottom=mb, right=mr, background_color=mask_bg, flags=MaskFlags())
    for cid, cd in pairs:
        rec.channel_info.append(ChannelInfo(ChannelID(cid), len(cd.data) + 2)); chans.append(copy.copy(cd))
    l = PixelLayer(s, rec, chans); s.append(l); l.name = name; l.blend_mode = blend; l.opacity = opacity; l.visible = visible
    return l


def source_arrays(o):
    rgb = np.stack([channel(o, c) for c in range(3)], axis=-1); alpha = channel(o, -1); md = o._record.mask_data
    mask = channel(o, -2) if md is not None else None; box = (md.left, md.top, md.right, md.bottom) if md is not None else None; bg = md.background_color if md is not None else 0
    return rgb, alpha, mask, box, bg


def base_u16():
    fus = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); sup = np.load(CAU38 / 'support_v38.npy')
    scale = float(np.nanmax(np.where(sup[..., None], np.asarray(fus), 0)))
    base = np.round(np.clip(np.nan_to_num(np.asarray(fus)) / scale, 0, 1) * 65535).astype(np.uint16); base[~sup] = 0
    return base, sup, scale


def build():
    assert not TARGET.exists(); assert sha(FONT) == FONT_SHA
    for kind, old, new, path, vis in PLA:
        if kind == 'u16': assert path.exists(), path
    src = PSDImage.open(FONT); by = {l.name: l for l in src}; assert len(list(src)) == 40
    s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2
    rep = {'font': str(FONT), 'font_sha256': FONT_SHA, 'lluna_inici': {'desplacament_px': DESPL, 'centre_mesurat': [14.8, 0.9], 'RL_px': RL_PX, 'guarda_px': GUARDA, 't_s': 15.0}, 'capes': []}
    mk_new = mascara_lluna_inici(); FULL = (0, 0, FW, FH)
    for kind, old, new, path, vis in PLA:
        if kind == 'base':
            base, sup, scale = base_u16(); rep['escala_lineal'] = scale
            add_layer(s, base, new, (sup.astype(np.uint16) * 65535), mk_new, FULL, 0, BlendMode.NORMAL, 255, True, FULL); rep['capes'].append({'name': new, 'kind': kind, 'visible': True}); del base; gc.collect(); log('capa ' + new); continue
        o = by[old]; name = new or old; visible = o.visible if vis is None else vis
        if kind == 'u16':
            u = np.asarray(np.load(path, mmap_mode='r')); assert u.shape == (FH, FW) and u.dtype == np.uint16
            add_layer(s, u, name, channel(o, -1), mk_new, FULL, 0, o.blend_mode, o.opacity, visible, FULL); rep['capes'].append({'name': name, 'kind': kind, 'from': old, 'u16_sha256': sha(path), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': visible}); del u
        else:
            rgb, alpha, mask, box, bg = source_arrays(o); l0, t0, r0, b0 = o.bbox
            if kind == 'copy':
                add_layer(s, rgb, name, alpha, mask, box, bg, o.blend_mode, o.opacity, visible, (l0, t0, r0, b0))
            elif kind == 'copy_newmask':
                add_layer(s, rgb, name, alpha, mk_new, FULL, 0, o.blend_mode, o.opacity, visible, (l0, t0, r0, b0))
            elif kind == 'moon':
                assert box == FULL, (old, box); dx, dy = DESPL
                add_layer(s, rgb, name, alpha, roll_mask(mask), FULL, bg, o.blend_mode, o.opacity, visible, (l0 + dx, t0 + dy, r0 + dx, b0 + dy))
            rep['capes'].append({'name': name, 'kind': kind, 'from': old, 'bbox_v32': list(o.bbox), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': visible}); del rgb, alpha, mask
        gc.collect(); log('capa ' + name)
    finalize_lr16(s)
    # compost per defecte: capes visibles (normal / overlay / linear dodge), amb alfa × màscara, a la posició de cada capa
    comp = np.zeros((FH, FW, 3), np.float32)
    for l in s:
        if not l.visible: continue
        rec = l._record; l0, t0, r0, b0 = rec.left, rec.top, rec.right, rec.bottom
        a = np.stack([channel(l, c) for c in range(3)], axis=-1).astype(np.float32) / 65535; al = channel(l, -1); al = np.ones(a.shape[:2], np.float32) if al is None else al.astype(np.float32) / 65535
        md = rec.mask_data
        if md is not None:
            mk = np.full((FH, FW), md.background_color / 255, np.float32); mk[md.top:md.bottom, md.left:md.right] = channel(l, -2).astype(np.float32) / 65535; al = al * mk[t0:b0, l0:r0]
        wgt = (al * l.opacity / 255)[..., None]; b = comp[t0:b0, l0:r0]
        if l.blend_mode == BlendMode.OVERLAY: f = np.where(b <= .5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f * wgt
        elif l.blend_mode == BlendMode.LINEAR_DODGE: comp[t0:b0, l0:r0] = np.clip(b + a * wgt, 0, 1)
        else: comp[t0:b0, l0:r0] = b * (1 - wgt) + a * wgt
        del a, al, wgt; gc.collect(); log('compost + ' + l.name)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = ImageData(compression=Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    from PIL import Image; im = Image.fromarray(np.uint8(np.clip(comp[::4, ::4], 0, 1) * 255)); im.save(VIS38 / 'C4_compost_V38_llenc_sencer.png'); del comp, data
    with open(TARGET, 'xb'):
        pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB38 / 'C4_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    rep = json.loads((REB38 / 'C4_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); assert len(ls) == len(PLA) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16
    src = PSDImage.open(FONT); by = {l.name: l for l in src}; mk_new = mascara_lluna_inici(); rows = []
    for l, (kind, old, new, path, vis) in zip(ls, PLA):
        name = new or old; assert l.name == name, (l.name, name); md = l._record.mask_data
        if kind == 'base':
            base, sup, scale = base_u16(); assert abs(scale - rep['escala_lineal']) < 1e-9
            ok = all(np.array_equal(channel(l, c)[::3, ::3], base[::3, ::3, c]) for c in range(3)) and np.array_equal(channel(l, -1), sup.astype(np.uint16) * 65535) and np.array_equal(channel(l, -2), mk_new) and l.visible; del base
        else:
            o = by[old]; visible = o.visible if vis is None else vis; okp = l.blend_mode == o.blend_mode and l.opacity == o.opacity and l.visible == visible
            if kind == 'u16':
                u = np.load(path, mmap_mode='r'); ok = okp and all(np.array_equal(channel(l, c), u) for c in (0, 1, 2)) and np.array_equal(channel(l, -2), mk_new) and (channel(l, -1) is None and channel(o, -1) is None or np.array_equal(channel(l, -1), channel(o, -1)))
            else:
                rgb, alpha, mask, box, bg = source_arrays(o); l0, t0, r0, b0 = o.bbox; dx, dy = DESPL if kind == 'moon' else (0, 0)
                okg = (l._record.left, l._record.top, l._record.right, l._record.bottom) == (l0 + dx, t0 + dy, r0 + dx, b0 + dy) and all(np.array_equal(channel(l, c)[::3, ::3], rgb[::3, ::3, c]) for c in range(3)) and ((alpha is None and channel(l, -1) is None) or np.array_equal(channel(l, -1), alpha))
                if kind == 'copy': okm = (mask is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == box and md.background_color == bg and np.array_equal(channel(l, -2), mask))
                elif kind == 'copy_newmask': okm = md is not None and (md.left, md.top, md.right, md.bottom) == (0, 0, FW, FH) and np.array_equal(channel(l, -2), mk_new)
                else: okm = md is not None and np.array_equal(channel(l, -2), roll_mask(mask))
                ok = okp and okg and okm; del rgb, alpha, mask
        assert ok, name; rows.append({'name': name, 'kind': kind, 'exact': True}); log('verificada ' + name); gc.collect()
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB38 / 'C4_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB38 / 'C4_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB38 / 'C4_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB38 / 'C4_verification.json').read_text()); g = json.loads((REB38 / 'C4_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM
    tmp = CT / 'V38_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_:
        shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL); assert sha(FONT) == FONT_SHA
    savejson(REB38 / 'C4_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
