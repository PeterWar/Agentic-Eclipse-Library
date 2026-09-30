"""C4 · V33.psb LLEUGER (norma de Pere 07-09): UNA capa base lineal + les 10 capes de filtre iterades.
Base: fusió lineal V32 escalada per un únic factor declarat (màxim dins del suport → 65535), alfa = suport.
Capes: RGB = u16 V33; alfa, màscara, mode, opacitat i visibilitat copiats de la capa homònima de V32.psb.
No hi entren les azimutals (03/03/07), NAFE, precursors, SWAP ni C01 (cap marca de Pere): es queden a la V32.
Ús: build | verify | gate | publish."""
from comu33 import *
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
STAGING = HERE33 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'V33.psb'; FINAL = CT / 'V33.psb'
PC33 = HERE33 / 'purs/cau'
LAYERS = [  # (nom a V32.psb, u16 V33, nom nou)
    ('01 ACHF fi 2-32 · V32', CAU33 / '01_v33_u16.npy', '01 ACHF fi 2-32 · V33 S/N'),
    ('02 Passa-alt 24 · V32', CAU33 / '02_v33_u16.npy', '02 Passa-alt 24 · V33 S/N'),
    ('04 ACHF micro 1-16 · V32', CAU33 / '04_v33_u16.npy', '04 ACHF micro 1-16 · V33 S/N'),
    ('05 ACHF fi 2-48 · V32', CAU33 / '05_v33_u16.npy', '05 ACHF fi 2-48 · V33 S/N'),
    ('06 ACHF estructura 4-64 · V32', CAU33 / '06_v33_u16.npy', '06 ACHF estructura 4-64 · V33 S/N'),
    ('P01 NRGF · V32', PC33 / 'P01_NRGF_u16.npy', 'P01 NRGF · V33 S/N vora'),
    ('P02 RHEF · comparacio amb anells · V32', PC33 / 'P02_RHEF_u16.npy', 'P02 RHEF · V33 S/N vora'),
    ('P03 MGN · V32', PC33 / 'P03_MGN_u16.npy', 'P03 MGN · V33 S/N'),
    ('P04 WOW sense denoise · V32', PC33 / 'P04_WOW_u16.npy', 'P04 WOW · V33 S/N'),
    ('P05 WOW bilateral sense denoise · V32', PC33 / 'P05_WOW_bilateral_u16.npy', 'P05 WOW bilateral · V33 S/N'),
]
FW, FH = W, H


def compressed(u):
    cd = ChannelData(Compression.ZIP); cd.set_data(np.ascontiguousarray(np.asarray(u).astype('>u2')).tobytes(), FW, FH, 16, 2); return cd


def add_layer(s, rgb_u16, name, alpha_u16, mask_u16, mask_box, blend, opacity, visible):
    rec = LayerRecord(top=0, left=0, bottom=FH, right=FW, channel_info=[]); rec.tagged_blocks = TaggedBlocks(); rec.name = name
    chans = ChannelDataList(); alpha = compressed(np.full((FH, FW), 65535, np.uint16) if alpha_u16 is None else alpha_u16)
    cols = [compressed(rgb_u16)] * 3 if rgb_u16.ndim == 2 else [compressed(rgb_u16[..., c]) for c in range(3)]
    pairs = [(-1, alpha), (0, cols[0]), (1, cols[1]), (2, cols[2])]
    if mask_u16 is not None:
        l0, t0, r0, b0 = mask_box; mcd = ChannelData(Compression.ZIP); mcd.set_data(np.ascontiguousarray(np.asarray(mask_u16).astype('>u2')).tobytes(), r0 - l0, b0 - t0, 16, 2)
        pairs.append((-2, mcd)); rec.mask_data = MaskData(top=t0, left=l0, bottom=b0, right=r0, background_color=0, flags=MaskFlags())
    for cid, cd in pairs:
        rec.channel_info.append(ChannelInfo(ChannelID(cid), len(cd.data) + 2)); chans.append(copy.copy(cd))
    l = PixelLayer(s, rec, chans); s.append(l); l.name = name; l.blend_mode = blend; l.opacity = opacity; l.visible = visible
    return l


def build():
    assert not TARGET.exists(); assert sha(FONT) == FONT_SHA
    src = PSDImage.open(FONT); by = {l.name: l for l in src}
    fus = np.load(CAU32 / 'fusion_total_v32.npy', mmap_mode='r'); sup = np.load(CAU32 / 'support_v32.npy')
    scale = float(np.nanmax(np.where(sup[..., None], np.asarray(fus), 0)))
    base = np.round(np.clip(np.nan_to_num(np.asarray(fus)) / scale, 0, 1) * 65535).astype(np.uint16); base[~sup] = 0
    s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2
    rep = {'font_modes': str(FONT), 'font_sha256': FONT_SHA, 'base': 'fusion_total_v32 lineal (sRGB lineal, matriu i guany del run); escala única declarada; cap corba', 'escala_lineal': scale, 'capes': []}
    add_layer(s, base, '00 Base lineal · V32', sup.astype(np.uint16) * 65535, None, None, BlendMode.NORMAL, 255, True); rep['capes'].append({'name': '00 Base lineal · V32'}); del base
    for oldname, path, newname in LAYERS:
        o = by[oldname]; u = np.load(path, mmap_mode='r'); assert u.shape == (FH, FW) and u.dtype == np.uint16
        md = o._record.mask_data; mask = channel(o, -2) if md is not None else None; box = (md.left, md.top, md.right, md.bottom) if md is not None else None
        add_layer(s, np.asarray(u), newname, channel(o, -1), mask, box, o.blend_mode, o.opacity, o.visible)
        rep['capes'].append({'name': newname, 'from': oldname, 'u16_sha256': sha(path), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': o.visible}); log('capa ' + newname); gc.collect()
    finalize_lr16(s)
    sys.path.insert(0, str(ROOT / 'research/tools/v29')); from build_canvas import over
    comp = np.zeros((FH, FW, 3), np.float32)
    for l in s:
        if not l.visible:
            continue
        a = np.stack([channel(l, c) for c in range(3)], axis=-1).astype(np.float32) / 65535 if l.name.startswith('00') else np.repeat(channel(l, 0)[..., None].astype(np.float32) / 65535, 3, axis=2)
        al = channel(l, -1); al = np.ones((FH, FW), np.float32) if al is None else al.astype(np.float32) / 65535; md = l._record.mask_data
        if md is not None:
            mk = np.full((FH, FW), md.background_color / 255, np.float32); mk[md.top:md.bottom, md.left:md.right] = channel(l, -2).astype(np.float32) / 65535; al = al * mk
        comp = over(comp, a, al, l.opacity / 255, 'overlay' if l.blend_mode == BlendMode.OVERLAY else 'normal'); del a, al
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = ImageData(compression=Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    with open(TARGET, 'xb'):
        pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB33 / 'C4_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    rep = json.loads((REB33 / 'C4_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); assert len(ls) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16
    src = PSDImage.open(FONT); by = {l.name: l for l in src}
    fus = np.load(CAU32 / 'fusion_total_v32.npy', mmap_mode='r'); sup = np.load(CAU32 / 'support_v32.npy'); scale = rep['escala_lineal']; b = ls[0]
    for c in range(3):
        exp = np.round(np.clip(np.nan_to_num(np.asarray(fus[..., c])) / scale, 0, 1) * 65535).astype(np.uint16); exp[~sup] = 0; assert np.array_equal(channel(b, c)[::5, ::5], exp[::5, ::5]), c
    rows = []
    for l, (oldname, path, newname) in zip(ls[1:], LAYERS):
        o = by[oldname]; u = np.load(path, mmap_mode='r'); assert l.name == newname
        ok = all(np.array_equal(channel(l, c), u) for c in (0, 1, 2)) and np.array_equal(channel(l, -1), channel(o, -1)); mo, ml = o._record.mask_data, l._record.mask_data
        okm = (mo is None and ml is None) or (mo is not None and ml is not None and (mo.left, mo.top, mo.right, mo.bottom) == (ml.left, ml.top, ml.right, ml.bottom) and np.array_equal(channel(l, -2), channel(o, -2)))
        assert ok and okm and l.blend_mode == o.blend_mode and l.opacity == o.opacity and l.visible == o.visible, newname; rows.append({'name': newname, 'exact': True})
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB33 / 'C4_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB33 / 'C4_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB33 / 'C4_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB33 / 'C4_verification.json').read_text()); g = json.loads((REB33 / 'C4_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_V33_20260907'
    tmp = CT / 'V33_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_:
        shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL); assert sha(FONT) == FONT_SHA
    savejson(REB33 / 'C4_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
