"""C4 (V40) · V40.psb: NOMÉS les capes que Pere va deixar a `V39_Artefactes.psb` (dues bases V39, 03 r0/r4/07 de la V38, 01/04/05/06 ACHF, P01, P01b,
P02, P03, P04, P05) més les seves capes no linealitzades 06 a 12 (byte a byte), tot pres de `V39.psb` (modes, opacitats, visibilitats i màscares de
lliurament), amb els set filtres regenerats amb la regla V40 (guany per banda max(Wiener regional, garrote k=3), soroll a totes les vores, dues
particions, sense terme creuat): 01/04/05/06 i P03/P04/P05 → «· V40». Res del que Pere va treure (01–05 seves, 13 Sony, Fons per raig, earthshine,
Reflex, Estrelles, bases V32 i lineal V38). Ús: build | verify | gate | publish."""
from comu40 import *
import importlib.util as _iu
_sp = _iu.spec_from_file_location('c4_v39', HERE39 / 'c4_projecte_v39.py'); C = _iu.module_from_spec(_sp); _sp.loader.exec_module(C)   # add_layer, source_arrays, channel, finalize_lr16, compressed, PSDImage…
import copy, gc, subprocess, shutil, datetime, os
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
CT = C.CT; FONT = CT / 'V39.psb'; STAGING = HERE40 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'V40.psb'; FINAL = CT / 'V40.psb'; CLAIM = 'CLAUDE_V40_20260909'
FW, FH = W, H
KEEP = ['12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar',
        '00 Base (cel/4) · V39', '00 Base corba (total) · V39', '03 ACHF azimutal 8-128 r0 · V38', '03 ACHF azimutal 8-128 r4 · V38', '07 ACHF azimutal suau r8 · V38',
        '01 ACHF fi 2-32 · V39', '04 ACHF micro 1-16 · V39', '05 ACHF fi 2-48 · V39', '06 ACHF estructura 4-64 · V39',
        'P01 NRGF · V39', 'P01b NRGF (μσ dels anells parcials extrapolats en ln r) · V39', 'P02 RHEF · V39', 'P03 MGN · V39', 'P04 WOW · V39', 'P05 WOW bilateral · V39']
REGEN = {'01 ACHF fi 2-32 · V39': (CAU39 / '01_v39_u16.npy', '01 ACHF fi 2-32 · V40'), '04 ACHF micro 1-16 · V39': (CAU39 / '04_v39_u16.npy', '04 ACHF micro 1-16 · V40'),
         '05 ACHF fi 2-48 · V39': (CAU39 / '05_v39_u16.npy', '05 ACHF fi 2-48 · V40'), '06 ACHF estructura 4-64 · V39': (CAU39 / '06_v39_u16.npy', '06 ACHF estructura 4-64 · V40'),
         'P03 MGN · V39': (PC39 / 'P03_MGN_u16.npy', 'P03 MGN · V40'), 'P04 WOW · V39': (PC39 / 'P04_WOW_u16.npy', 'P04 WOW · V40'), 'P05 WOW bilateral · V39': (PC39 / 'P05_WOW_bilateral_u16.npy', 'P05 WOW bilateral · V40')}


def pla(src):
    """(tipus, capa font, nom nou, ruta u16 | None) de baix a dalt, només KEEP, en l'ordre de V39.psb."""
    noms = [l.name for l in src]; assert all(k in noms for k in KEEP), [k for k in KEEP if k not in noms]
    out = []
    for l in src:
        if l.name not in KEEP: continue
        if l.name in REGEN: out.append(('u16', l, REGEN[l.name][1], REGEN[l.name][0]))
        else: out.append(('copy', l, l.name, None))
    return out


def build():
    assert not TARGET.exists(); font_sha = sha(FONT); src = PSDImage.open(FONT); P = pla(src); assert all(p.exists() for _, _, _, p in P if p is not None)
    s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2
    rep = {'font': str(FONT), 'font_sha256': font_sha, 'capes': [], 'fora_per_ordre_de_pere': [l.name for l in src if l.name not in KEEP], 'tau': json.loads((CAU39 / 'tau.json').read_text())}
    for kind, o, name, path in P:
        if kind == 'u16':
            u = np.asarray(np.load(path, mmap_mode='r')); assert u.shape == (FH, FW) and u.dtype == np.uint16; md = o._record.mask_data
            mask = C.channel(o, -2) if md is not None else None; box = (md.left, md.top, md.right, md.bottom) if md is not None else None; bg = md.background_color if md is not None else 0
            C.add_layer(s, u, name, C.channel(o, -1), mask, box, bg, o.blend_mode, o.opacity, o.visible, tuple(o.bbox) if o.bbox != (0, 0, FW, FH) else (0, 0, FW, FH))
            rep['capes'].append({'name': name, 'kind': kind, 'from': o.name, 'u16': str(path), 'u16_sha256': sha(path), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': o.visible}); del u
        else:
            rgb, alpha, mask, box, bg = C.source_arrays(o); l0, t0, r0, b0 = o.bbox
            C.add_layer(s, rgb, name, alpha, mask, box, bg, o.blend_mode, o.opacity, o.visible, (l0, t0, r0, b0)); rep['capes'].append({'name': name, 'kind': kind, 'bbox': list(o.bbox), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': o.visible}); del rgb, alpha, mask
        gc.collect(); log('capa ' + name)
    C.finalize_lr16(s)
    comp = np.zeros((FH, FW, 3), np.float32)
    for l in s:
        if not l.visible: continue
        rec = l._record; l0, t0, r0, b0 = rec.left, rec.top, rec.right, rec.bottom
        a = np.stack([C.channel(l, c) for c in range(3)], axis=-1).astype(np.float32) / 65535; al = C.channel(l, -1); al = np.ones(a.shape[:2], np.float32) if al is None else al.astype(np.float32) / 65535; md = rec.mask_data
        if md is not None:
            mk = np.full((FH, FW), md.background_color / 255, np.float32); mm = C.channel(l, -2).astype(np.float32) / 65535
            mt, mb, ml, mr = max(md.top, 0), min(md.bottom, FH), max(md.left, 0), min(md.right, FW); mk[mt:mb, ml:mr] = mm[mt - md.top:mt - md.top + (mb - mt), ml - md.left:ml - md.left + (mr - ml)]; al = al * mk[t0:b0, l0:r0]; del mm
        wgt = (al * l.opacity / 255)[..., None]; b = comp[t0:b0, l0:r0]
        if l.blend_mode == BlendMode.OVERLAY: f = np.where(b <= .5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f * wgt
        elif l.blend_mode == BlendMode.HARD_LIGHT: f = np.where(a <= .5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f * wgt
        elif l.blend_mode == BlendMode.LINEAR_DODGE: comp[t0:b0, l0:r0] = np.clip(b + a * wgt, 0, 1)
        else: comp[t0:b0, l0:r0] = b * (1 - wgt) + a * wgt
        del a, al, wgt; gc.collect(); log('compost + ' + l.name)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = C.ImageData(compression=C.Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    from PIL import Image; Image.fromarray(np.uint8(np.clip(comp[::4, ::4], 0, 1) * 255)).save(VIS40 / 'C4_compost_V40_llenc_sencer.png'); del comp, data
    with open(TARGET, 'xb'):
        pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB40 / 'C4_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    rep = json.loads((REB40 / 'C4_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); src = PSDImage.open(FONT); assert sha(FONT) == rep['font_sha256']
    P = pla(src); assert len(ls) == len(P) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16; rows = []
    for l, (kind, o, name, path) in zip(ls, P):
        assert l.name == name, (l.name, name); md = l._record.mask_data; mo = o._record.mask_data; okp = l.visible == o.visible and l.blend_mode == o.blend_mode and l.opacity == o.opacity
        if kind == 'u16':
            u = np.load(path, mmap_mode='r'); ok = okp and all(np.array_equal(C.channel(l, c), u) for c in (0, 1, 2)) and ((C.channel(l, -1) is None and C.channel(o, -1) is None) or np.array_equal(C.channel(l, -1), C.channel(o, -1))) and ((mo is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == (mo.left, mo.top, mo.right, mo.bottom) and np.array_equal(C.channel(l, -2), C.channel(o, -2))))
        else:
            rgb, alpha, mask, box, bg = C.source_arrays(o)
            ok = okp and (l._record.left, l._record.top, l._record.right, l._record.bottom) == tuple(o.bbox) and all(np.array_equal(C.channel(l, c)[::3, ::3], rgb[::3, ::3, c]) for c in range(3)) and ((alpha is None and C.channel(l, -1) is None) or np.array_equal(C.channel(l, -1), alpha)) and ((mask is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == box and np.array_equal(C.channel(l, -2), mask)))
            del rgb, alpha, mask
        assert ok, name; rows.append({'name': name, 'kind': kind, 'exact': True}); log('verificada ' + name); gc.collect()
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB40 / 'C4_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB40 / 'C4_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB40 / 'C4_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB40 / 'C4_verification.json').read_text()); g = json.loads((REB40 / 'C4_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM
    tmp = CT / 'V40_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_:
        shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL)
    savejson(REB40 / 'C4_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
