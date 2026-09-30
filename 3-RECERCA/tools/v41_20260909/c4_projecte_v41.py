"""C4 (V41) · V41.psb: les 22 capes de la V40 (ordre, modes, opacitats i visibilitats de `V40.psb`; píxels, alfa i MÀSCARA de la capa font), però amb els set filtres SENSE cap
tractament de soroll: 01/04/05/06 ACHF i P03/P04/P05 es prenen BYTE A BYTE de `V38.psb` (recepta V38 = la mateixa que dona el codi V39/V40 amb
τ = 0: identitat provada 4e-9 ACHF, 8e-5 MGN), i la resta (capes 06–12 de Pere, dues bases V39, 03 r0/r4/07 V38, P01, P01b, P02 V39) de `V39.psb`.
Cap píxel nou: reassemblatge amb verificació exacta contra les fonts. Nota (verificador 09-09): les màscares dels set filtres són les de V38.psb (numpy original); les de V39/V40 són
la mateixa màscara requantitzada pel re-desat de Photoshop (2.852 px de la rampa del forat lunar a ±1 nivell u16, 0,004 %): efecte nul, declarat. La capa U16 nova es verifica
en RGB, màscara, mode, opacitat i visibilitat (alfa i caixa comprovades a mà pel verificador: alfa uniforme 65535, caixa sencera). Ordre de Pere (09-09, nit): «oblidem-nos de moment de reduir el soroll, hi ha el
que hi ha; V41 partint de V39 sense artefactes i només amb les capes de la V40, però sense la reducció de soroll». Ús: build | verify | gate | publish."""
from comu41 import *
import importlib.util as _iu
_sp = _iu.spec_from_file_location('c4_v39', HERE39 / 'c4_projecte_v39.py'); C = _iu.module_from_spec(_sp); _sp.loader.exec_module(C)   # add_layer, source_arrays, channel, finalize_lr16, ImageData…
import gc, subprocess, shutil, datetime, os
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
CT = C.CT; F39 = CT / 'V39.psb'; F38 = CT / 'V38.psb'; F40 = CT / 'V40.psb'; STAGING = HERE41 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'V41.psb'; FINAL = CT / 'V41.psb'; CLAIM = 'CLAUDE_V41_20260909'
FW, FH = W, H
U16 = {'P02b RHEF υ 0,35 · V41': dict(u16=CAU39 / 'P02b_RHEF_ups0.35_u16.npy', mascara_de='P02 RHEF · V39', blend=None, opacity=13, visible=False)}   # capes noves des d'u16 (blend None = el de la capa de la màscara)
# (nom a la V40, font, nom de la capa a la font). Els modes/opacitats/visibilitats es prenen de la V40 (l'estat de lliurament que Pere coneix); els píxels i màscares, de la font.
PLA = [('12 1/3200 perles', 'V39', '12 1/3200 perles'), ('11 1/500 limbe', 'V39', '11 1/500 limbe'), ('10 1/125', 'V39', '10 1/125'), ('09 1/60 x2', 'V39', '09 1/60 x2'),
       ('08 1/30 x4 quar', 'V39', '08 1/30 x4 quar'), ('07 1/15 x2 quar', 'V39', '07 1/15 x2 quar'), ('06 1/8 x4 quar', 'V39', '06 1/8 x4 quar'),
       ('00 Base (cel/4) · V39', 'V39', '00 Base (cel/4) · V39'), ('00 Base corba (total) · V39', 'V39', '00 Base corba (total) · V39'),
       ('03 ACHF azimutal 8-128 r0 · V38', 'V39', '03 ACHF azimutal 8-128 r0 · V38'), ('03 ACHF azimutal 8-128 r4 · V38', 'V39', '03 ACHF azimutal 8-128 r4 · V38'), ('07 ACHF azimutal suau r8 · V38', 'V39', '07 ACHF azimutal suau r8 · V38'),
       ('01 ACHF fi 2-32 · V40', 'V38', '01 ACHF fi 2-32 · V38'), ('04 ACHF micro 1-16 · V40', 'V38', '04 ACHF micro 1-16 · V38'), ('05 ACHF fi 2-48 · V40', 'V38', '05 ACHF fi 2-48 · V38'), ('06 ACHF estructura 4-64 · V40', 'V38', '06 ACHF estructura 4-64 · V38'),
       ('P01 NRGF · V39', 'V39', 'P01 NRGF · V39'), ('P01b NRGF (μσ dels anells parcials extrapolats en ln r) · V39', 'V39', 'P01b NRGF (μσ dels anells parcials extrapolats en ln r) · V39'), ('P02 RHEF · V39', 'V39', 'P02 RHEF · V39'),
       ('P02b RHEF υ 0,35 · V41', 'U16', 'P02b RHEF υ 0,35 · V41'),   # capa NOVA (petició de Pere 09-09 nit): RHEF V38 + upsilon 0,35 de la referència; màscara i caixa de la P02 V39; Superposar 13 %, OCULTA (per comparar amb la P02)
       ('P03 MGN · V40', 'V38', 'P03 MGN · V38'), ('P04 WOW · V40', 'V38', 'P04 WOW · V38'), ('P05 WOW bilateral · V40', 'V38', 'P05 WOW bilateral · V38')]


def fonts():
    s39, s38, s40 = PSDImage.open(F39), PSDImage.open(F38), PSDImage.open(F40); n39 = {l.name: l for l in s39}; n38 = {l.name: l for l in s38}; n40 = [l for l in s40]
    assert [l.name for l in n40] == [p[0] for p in PLA if p[1] != 'U16'], 'la V40 no té l\'ordre esperat'
    for _, f, n in PLA: assert f == 'U16' and U16[n]['u16'].exists() or n in (n39 if f == 'V39' else n38), (f, n)
    return s39, s38, n40, n39, n38


def build():
    assert not TARGET.exists(); shas = {'V39.psb': sha(F39), 'V38.psb': sha(F38), 'V40.psb': sha(F40)}; s39, s38, n40, n39, n38 = fonts()
    s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2; rep = {'fonts': shas, 'capes': []}
    it40 = iter(n40)
    for nom40, f, nfont in PLA:
        if f == 'U16':
            spec = U16[nfont]; om = n39[spec['mascara_de']]; u = np.asarray(np.load(spec['u16'], mmap_mode='r')); assert u.shape == (FH, FW) and u.dtype == np.uint16
            md = om._record.mask_data; mask = C.channel(om, -2) if md is not None else None; box = (md.left, md.top, md.right, md.bottom) if md is not None else None; bg = md.background_color if md is not None else 0
            C.add_layer(s, u, nfont, C.channel(om, -1), mask, box, bg, spec['blend'] or om.blend_mode, spec['opacity'], spec['visible'], (0, 0, FW, FH))
            rep['capes'].append({'name': nfont, 'font': 'u16', 'u16': str(spec['u16']), 'u16_sha256': sha(spec['u16']), 'mascara_i_alfa_de': spec['mascara_de'], 'blend': str(spec['blend'] or om.blend_mode), 'opacity': spec['opacity'], 'visible': spec['visible']}); del u, mask; gc.collect(); log(f'capa {nfont}  ← u16 (nova)'); continue
        l40 = next(it40); o = (n39 if f == 'V39' else n38)[nfont]; rgb, alpha, mask, box, bg = C.source_arrays(o); assert tuple(o.bbox) == tuple(l40.bbox), (nom40, o.bbox, l40.bbox)
        C.add_layer(s, rgb, nfont, alpha, mask, box, bg, l40.blend_mode, l40.opacity, l40.visible, tuple(o.bbox))   # el nom és el de la FONT (procedència honesta: «· V38» als filtres sense soroll)
        rep['capes'].append({'name': nfont, 'nom_a_la_V40': nom40, 'font': f, 'bbox': list(o.bbox), 'blend': str(l40.blend_mode), 'opacity': l40.opacity, 'visible': l40.visible, 'pixels_i_mascara_de': f})
        del rgb, alpha, mask; gc.collect(); log(f'capa {nfont}  ← {f}')
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
        if l.blend_mode == BlendMode.OVERLAY: f_ = np.where(b <= .5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.HARD_LIGHT: f_ = np.where(a <= .5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.LINEAR_DODGE: comp[t0:b0, l0:r0] = np.clip(b + a * wgt, 0, 1)
        else: comp[t0:b0, l0:r0] = b * (1 - wgt) + a * wgt
        del a, al, wgt; gc.collect(); log('compost + ' + l.name)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = C.ImageData(compression=C.Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    from PIL import Image; Image.fromarray(np.uint8(np.clip(comp[::4, ::4], 0, 1) * 255)).save(VIS41 / 'C4_compost_V41_llenc_sencer.png'); del comp, data
    with open(TARGET, 'xb'):
        pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB41 / 'C4_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    """Exacta: cada capa de la V41 = píxels, alfa, màscara i caixa de la capa font (V39 o V38) i mode/opacitat/visibilitat de la V40."""
    rep = json.loads((REB41 / 'C4_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); s39, s38, n40, n39, n38 = fonts()
    assert {k: sha(CT / k) for k in rep['fonts']} == rep['fonts']; assert len(ls) == len(PLA) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16; rows = []
    it40 = iter(n40)
    for l, (nom40, f, nfont) in zip(ls, PLA):
        assert l.name == nfont, (l.name, nfont)
        if f == 'U16':
            spec = U16[nfont]; om = n39[spec['mascara_de']]; u = np.load(spec['u16'], mmap_mode='r'); md = l._record.mask_data; mo = om._record.mask_data
            ok = l.visible == spec['visible'] and l.opacity == spec['opacity'] and l.blend_mode == (spec['blend'] or om.blend_mode) and all(np.array_equal(C.channel(l, c), u) for c in (0, 1, 2))
            ok = ok and ((mo is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == (mo.left, mo.top, mo.right, mo.bottom) and np.array_equal(C.channel(l, -2), C.channel(om, -2))))
            assert ok, nfont; rows.append({'name': nfont, 'font': 'u16', 'exact': True}); log('verificada ' + nfont + ' (u16)'); gc.collect(); continue
        l40 = next(it40); o = (n39 if f == 'V39' else n38)[nfont]
        okp = l.visible == l40.visible and l.blend_mode == l40.blend_mode and l.opacity == l40.opacity
        rgb, alpha, mask, box, bg = C.source_arrays(o); md = l._record.mask_data
        ok = okp and (l._record.left, l._record.top, l._record.right, l._record.bottom) == tuple(o.bbox) and all(np.array_equal(C.channel(l, c), rgb[..., c]) for c in range(3))
        ok = ok and ((alpha is None and C.channel(l, -1) is None) or np.array_equal(C.channel(l, -1), alpha) or (alpha is None and bool(np.all(C.channel(l, -1) == 65535))))
        ok = ok and ((mask is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == tuple(box) and md.background_color == bg and np.array_equal(C.channel(l, -2), mask)))
        del rgb, alpha, mask; assert ok, nfont; rows.append({'name': nfont, 'font': f, 'exact': True}); log('verificada ' + nfont); gc.collect()
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB41 / 'C4_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB41 / 'C4_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB41 / 'C4_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB41 / 'C4_verification.json').read_text()); g = json.loads((REB41 / 'C4_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM
    tmp = CT / 'V41_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_:
        shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL)
    savejson(REB41 / 'C4_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
