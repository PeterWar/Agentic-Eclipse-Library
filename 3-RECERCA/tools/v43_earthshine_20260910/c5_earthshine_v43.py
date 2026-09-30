"""C5 (V43) · Earthshine_V43.psb (FITXER NOU a `Capes interiors`, al costat de l'Earthshine_V42.psb de Pere, que no es toca): les 9 capes del seu Earthshine_V42.psb
BYTE A BYTE (píxels, alfa, màscares, modes, opacitats, visibilitats tal com ell les va deixar) + les capes noves de l'apilat lunar HDR V43 (f2) A DALT de tot:
 · `Earthshine V43 disc pla fosc + relleu 12 % · limbe net` (VISIBLE, Normal): l'ala de la PSF del limbe (el glow) modelada per sector i restada fins a 0,995 R, disc pla fosc
   (×0,3 el vel; sRGB ≈ 0,16 com el disc de Brno) amb el relleu de l'earthshine a 12 %, vora de 2 px mesurada i la corona de l'instant fora (f2c);
 · `… disc pla POWAAAH3 + relleu` (oculta): el mateix amb el disc al nivell del POWAAAH3; `… vel ×0,3 + relleu` i `… nivell POWAAAH3 + relleu` (ocultes): amb el glow
   mesurat ×1 al limbe (f2); `HDR lineal (corba)` (oculta): el disc tal com el van veure els sensors, limbe sense saturar;
 · `… màscara àmplia (R+40)` (oculta): la capa visible amb la màscara fins a R+40 px (la corona de l'instant declarat just fora del limbe), per si Pere vol.
Màscara de les capes noves: 1 fins a R 457,5 (vora del forat de la base), 0 a R 461,5 (ploma 4 px); la dada de píxel arriba fins a R+40 px.
Ús: build | verify | gate | publish."""
from comu43 import *
import importlib.util as _iu, gc, subprocess, shutil, datetime, os, copy
_sp = _iu.spec_from_file_location('c4_v39', HERE42.parent / 'v39_20260909' / 'c4_projecte_v39.py'); C = _iu.module_from_spec(_sp); _sp.loader.exec_module(C)
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
CI = C.CT.parent / 'Capes interiors'; F42P = CI / 'Earthshine_V42.psb'; STAGING = HERE43 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'Earthshine_V43.psb'; FINAL = CI / 'Earthshine_V43.psb'; CLAIM = 'CLAUDE_EARTHSHINE_BRNO_20260910'
FW, FH = W, H; MASK = CAU43 / 'e43_mascara_u16.npy'; MASK_AMPLA = CAU43 / 'e43_mascara_ampla_u16.npy'
NOVES = [('Earthshine V43 HDR lineal (corba) · totes les exposicions, limbe sense saturar', CAU43 / 'e43_lineal_u16.npy', MASK, False),
         ('Earthshine V43 vel ×0,3 + relleu 12 % · glow mesurat al limbe', CAU43 / 'e43_vel03_relleu12_u16.npy', MASK, False),
         ('Earthshine V43 nivell POWAAAH3 + relleu 12 % · glow mesurat al limbe', CAU43 / 'e43_powaaah3_relleu12_u16.npy', MASK, False),
         ('Earthshine V43 disc pla POWAAAH3 + relleu 12 % · limbe net', CAU43 / 'e43_pla_powaaah3_relleu12_u16.npy', MASK, False),
         ('Earthshine V43 disc pla fosc + relleu 12 % · limbe net · màscara àmplia (R+40)', CAU43 / 'e43_pla_fosc_relleu12_u16.npy', MASK_AMPLA, False),
         ('Earthshine V43 disc pla fosc + relleu 12 % · limbe net', CAU43 / 'e43_pla_fosc_relleu12_u16.npy', MASK, True)]
MASK_DESC = {MASK.name: 'disc earthshine V43: 1 fins a R 457,5 (vora del forat de la base), 0 a R 461,5', MASK_AMPLA.name: 'disc + anell: 1 fins a R+32, 0 a R+40 (corona de l\'instant declarat just fora del limbe)'}


def build():
    assert not TARGET.exists() and F42P.exists(); s42 = PSDImage.open(F42P); mbox = (0, 0, FW, FH); s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2
    assert s42.size == (FW, FH) and s42.depth == 16, (s42.size, s42.depth); rep = {'fonts': {'Earthshine_V42.psb (Pere)': sha(F42P), 'bytes': F42P.stat().st_size, 'mtime': datetime.datetime.fromtimestamp(F42P.stat().st_mtime).isoformat()}, 'capes': []}
    for o in s42:
        assert o.kind == 'pixel', (o.name, o.kind); rgb, alpha, mask, box, bg = C.source_arrays(o); bbox = tuple(o.bbox)
        C.add_layer(s, rgb, o.name, alpha, mask, box, bg, o.blend_mode, o.opacity, o.visible, bbox)
        rep['capes'].append({'name': o.name, 'kind': 'copy', 'font': 'Earthshine_V42.psb', 'bbox': list(bbox), 'blend': str(o.blend_mode), 'opacity': o.opacity, 'visible': o.visible}); del rgb, alpha, mask; gc.collect(); log('capa (Pere, byte a byte) ' + o.name)
    for nom, src, mpath, vis in NOVES:
        u = np.asarray(np.load(src, mmap_mode='r')); assert u.shape[:2] == (FH, FW) and u.dtype == np.uint16, (nom, u.shape, u.dtype); m_ = np.asarray(np.load(mpath, mmap_mode='r'))
        C.add_layer(s, u, nom, None, m_, mbox, 0, BlendMode.NORMAL, 255, vis, (0, 0, FW, FH))
        rep['capes'].append({'name': nom, 'kind': 'u16m', 'u16': str(src), 'u16_sha256': sha(Path(src)), 'blend': str(BlendMode.NORMAL), 'opacity': 255, 'visible': vis, 'mascara': MASK_DESC[mpath.name], 'mascara_fitxer': str(mpath)}); del u, m_; gc.collect(); log('capa ' + nom)
    C.finalize_lr16(s)
    comp = np.zeros((FH, FW, 3), np.float32)
    for l in s:
        if not l.visible: continue
        rec = l._record; l0, t0, r0, b0 = rec.left, rec.top, rec.right, rec.bottom
        a = np.stack([C.channel(l, c) for c in range(3)], axis=-1).astype(np.float32) / 65535; al = C.channel(l, -1); al = np.ones(a.shape[:2], np.float32) if al is None else al.astype(np.float32) / 65535; md = rec.mask_data
        if md is not None:
            mk_ = np.full((FH, FW), md.background_color / 255, np.float32); mm = C.channel(l, -2).astype(np.float32) / 65535
            mt, mb, ml, mr = max(md.top, 0), min(md.bottom, FH), max(md.left, 0), min(md.right, FW); mk_[mt:mb, ml:mr] = mm[mt - md.top:mt - md.top + (mb - mt), ml - md.left:ml - md.left + (mr - ml)]; al = al * mk_[t0:b0, l0:r0]; del mm
        wgt = (al * l.opacity / 255)[..., None]; b = comp[t0:b0, l0:r0]
        if l.blend_mode == BlendMode.LIGHTEN: comp[t0:b0, l0:r0] = b * (1 - wgt) + np.maximum(a, b) * wgt
        elif l.blend_mode == BlendMode.OVERLAY: f_ = np.where(b <= .5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.MULTIPLY: comp[t0:b0, l0:r0] = b * (1 - wgt) + (a * b) * wgt
        elif l.blend_mode == BlendMode.LINEAR_DODGE: comp[t0:b0, l0:r0] = np.clip(b + a * wgt, 0, 1)
        else: comp[t0:b0, l0:r0] = b * (1 - wgt) + a * wgt
        del a, al, wgt; gc.collect(); log('compost + ' + l.name)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = C.ImageData(compression=C.Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    from PIL import Image; Image.fromarray(np.uint8(np.clip(comp[::4, ::4], 0, 1) * 255)).save(VIS43 / 'C5_compost_Earthshine_V43_llenc_quart.png')
    x0, y0 = int(round(CX + 14.8)) - 700, int(round(CY + 0.9)) - 700; Image.fromarray(np.uint8(np.clip(comp[y0:y0 + 1400, x0:x0 + 1400], 0, 1) * 255)).save(VIS43 / 'C5_compost_Earthshine_V43_lluna_1a1.png'); del comp, data
    with open(TARGET, 'xb'): pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB43 / 'C5_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    rep = json.loads((REB43 / 'C5_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); s42 = list(PSDImage.open(F42P)); assert len(ls) == len(s42) + len(NOVES) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16; rows = []
    for i, (l, rc) in enumerate(zip(ls, rep['capes'])):
        md = l._record.mask_data; okp = str(l.blend_mode) == rc['blend'] and l.opacity == rc['opacity'] and l.visible == rc['visible'] and l.name == rc['name']
        if i < len(s42):
            o = s42[i]; rgb, alpha, mask, box, bg = C.source_arrays(o); assert l.name == o.name
            ok = okp and (l._record.left, l._record.top, l._record.right, l._record.bottom) == tuple(o.bbox) and all(np.array_equal(C.channel(l, c), rgb[..., c]) for c in range(3)) and ((alpha is None and (C.channel(l, -1) is None or bool(np.all(C.channel(l, -1) == 65535)))) or np.array_equal(C.channel(l, -1), alpha))
            ok = ok and ((mask is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == tuple(box) and md.background_color == bg and np.array_equal(C.channel(l, -2), mask))); del rgb, alpha, mask
        else:
            nom, src, mpath, vis = NOVES[i - len(s42)]; u = np.load(src, mmap_mode='r'); mref = np.load(mpath, mmap_mode='r')
            ok = okp and l.name == nom and all(np.array_equal(C.channel(l, c), u[..., c]) for c in range(3)) and md is not None and np.array_equal(C.channel(l, -2), mref) and bool(np.all(C.channel(l, -1) == 65535)) and (l._record.left, l._record.top, l._record.right, l._record.bottom) == (0, 0, FW, FH)
        assert ok, l.name; rows.append({'name': l.name, 'exact': True}); log('verificada ' + l.name); gc.collect()
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB43 / 'C5_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB43 / 'C5_verification.json').read_text()); assert v['PASS']
    def jsx(js): return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally: jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB43 / 'C5_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB43 / 'C5_verification.json').read_text()); g = json.loads((REB43 / 'C5_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM
    assert sha(F42P) == json.loads((REB43 / 'C5_packaging.json').read_text())['fonts']['Earthshine_V42.psb (Pere)'], 'Earthshine_V42.psb de Pere ha canviat des del build'
    tmp = CI / 'Earthshine_V43_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_: shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL)
    savejson(REB43 / 'C5_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
