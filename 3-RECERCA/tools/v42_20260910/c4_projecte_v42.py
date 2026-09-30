"""C4 (V42) · V42.psb: la recomposició V42 sencera (apuntament B de la Sony amb rotació +8,10′ i registre dels seus fotogrames llargs), filtres calculats sobre la base
SENSE ESTRELLES, capa `Estrelles (llum mesurada)`, bases de pantalla V42, quatre RHEF (P02 + υ 0,35 + local 60° + local 30°), els MODES, OPACITATS i VISIBILITATS que
Pere va desar a la seva V41.psb (Superposar als ACHF, Multiplicar a les RHEF/NRGF, Llum suau al MGN), les seves capes 06–12 (V39.psb byte a byte), la capa `Compara LROC`
(V39.psb byte a byte; cara de la Lluna de la NASA, alineada al forat) i el POWAAAH3 de Pere alineat (P2: escala 1,3066, rotació +44,0°, disc al forat V38) amb màscara de disc.
Màscara lunar (Lluna a l'inici, R 455,5 + 2 px) a totes les capes de base, filtre i estrelles. Ús: build | verify | gate | publish."""
from comu42 import *
import importlib.util as _iu, gc, subprocess, shutil, datetime, os
_sp = _iu.spec_from_file_location('c4_v39', HERE39 / 'c4_projecte_v39.py'); C = _iu.module_from_spec(_sp); _sp.loader.exec_module(C)   # add_layer, source_arrays, channel, finalize_lr16, mascara_lluna_inici, ImageData, Compression
from psd_tools import PSDImage
from psd_tools.constants import BlendMode
CT = C.CT; F39 = CT / 'V39.psb'; F41 = CT / 'V41.psb'; STAGING = HERE42 / 'staging'; STAGING.mkdir(exist_ok=True); TARGET = STAGING / 'V42.psb'; FINAL = CT / 'V42.psb'; CLAIM = 'CLAUDE_V42_20260910'
FW, FH = W, H; PC42 = HERE42 / 'purs/cau'
# (nom, tipus, font, mode, opacitat 0–255, visible)  · tipus 'copy' = capa de V39.psb byte a byte; 'u16' = matriu nova + màscara lunar; 'u16m' = matriu nova + màscara pròpia
# modes/opacitats/visibilitats: els de la V41 desada per Pere (10-09 00:50); les capes noves, declarades.
PLA = [('12 1/3200 perles', 'copy', '12 1/3200 perles', None, None, None), ('11 1/500 limbe', 'copy', '11 1/500 limbe', None, None, None), ('10 1/125', 'copy', '10 1/125', None, None, None), ('09 1/60 x2', 'copy', '09 1/60 x2', None, None, None),
       ('08 1/30 x4 quar', 'copy', '08 1/30 x4 quar', None, None, None), ('07 1/15 x2 quar', 'copy', '07 1/15 x2 quar', None, None, None), ('06 1/8 x4 quar', 'copy', '06 1/8 x4 quar', None, None, None),
       ('00 Base (cel/4) · V42', 'u16', CAU42 / 'base_cel4_v42_u16.npy', BlendMode.NORMAL, 255, True), ('00 Base corba (total) · V42', 'u16', CAU42 / 'base_corba_total_v42_u16.npy', BlendMode.NORMAL, 255, True),
       ('Estrelles (llum mesurada) · V42', 'u16', CAU42 / 'estrelles_llum_mesurada_v42_u16.npy', BlendMode.LINEAR_DODGE, 255, True),
       ('P01 NRGF · V42', 'u16', PC42 / 'P01_NRGF_u16.npy', BlendMode.MULTIPLY, 255, False), ('P01b NRGF (μσ dels anells parcials extrapolats) · V42', 'u16', PC42 / 'P01_NRGF_extrap_u16.npy', BlendMode.MULTIPLY, 26, True),
       ('P02 RHEF · V42', 'u16', PC42 / 'P02_RHEF_u16.npy', BlendMode.MULTIPLY, 94, True), ('P02b RHEF υ 0,35 · V42', 'u16', CAU42 / 'P02b_RHEF_ups0.35_u16.npy', BlendMode.MULTIPLY, 56, True),
       ('P02c RHEF local 60° · V42', 'u16', CAU42 / 'P02c_RHEF_local60_u16.npy', BlendMode.MULTIPLY, 94, False), ('P02d RHEF local 30° · V42', 'u16', CAU42 / 'P02d_RHEF_local30_u16.npy', BlendMode.MULTIPLY, 94, False),
       ('03 ACHF azimutal 8-128 r0 · V42', 'u16', CAU42 / '03_v42_u16.npy', BlendMode.OVERLAY, 13, True), ('03 ACHF azimutal 8-128 r4 · V42', 'u16', CAU42 / '03v30_v42_u16.npy', BlendMode.OVERLAY, 46, False), ('07 ACHF azimutal suau r8 · V42', 'u16', CAU42 / '07_v42_u16.npy', BlendMode.OVERLAY, 56, False),
       ('01 ACHF fi 2-32 · V42', 'u16', CAU42 / '01_v42_u16.npy', BlendMode.OVERLAY, 56, True), ('04 ACHF micro 1-16 · V42', 'u16', CAU42 / '04_v42_u16.npy', BlendMode.OVERLAY, 23, True), ('05 ACHF fi 2-48 · V42', 'u16', CAU42 / '05_v42_u16.npy', BlendMode.OVERLAY, 18, False), ('06 ACHF estructura 4-64 · V42', 'u16', CAU42 / '06_v42_u16.npy', BlendMode.OVERLAY, 18, True),
       ('P03 MGN · V42', 'u16', PC42 / 'P03_MGN_u16.npy', BlendMode.SOFT_LIGHT, 54, False), ('P04 WOW · V42', 'u16', PC42 / 'P04_WOW_u16.npy', BlendMode.OVERLAY, 8, False), ('P05 WOW bilateral · V42', 'u16', PC42 / 'P05_WOW_bilateral_u16.npy', BlendMode.OVERLAY, 26, False),
       ('POWAAAH3 (HDR de Pere 16-08) · earthshine · V42', 'u16m', CAU42 / 'powaaah3_rgb_u16.npy', BlendMode.NORMAL, 255, True),
       ('Earthshine V42 lineal (corba) · mesurat, gra inclòs', 'u16m', CAU42 / 'earthshine_v42_lineal_u16.npy', BlendMode.NORMAL, 255, False, CAU42 / 'earthshine_v42_mascara_u16.npy'),
       ('Earthshine V42 relleu 12 % · gra tal qual', 'u16m', CAU42 / 'earthshine_v42_relleu12_gra_u16.npy', BlendMode.NORMAL, 255, False, CAU42 / 'earthshine_v42_mascara_u16.npy'),
       ('Earthshine V42 relleu 12 % · suau σ3', 'u16m', CAU42 / 'earthshine_v42_relleu12_suau_u16.npy', BlendMode.NORMAL, 255, False, CAU42 / 'earthshine_v42_mascara_u16.npy'),
       ('Earthshine V42 relleu 24 % · suau σ3', 'u16m', CAU42 / 'earthshine_v42_relleu24_suau_u16.npy', BlendMode.NORMAL, 255, False, CAU42 / 'earthshine_v42_mascara_u16.npy'),
       ('Compara LROC', 'copy', 'Compara LROC', BlendMode.NORMAL, 255, False)]
MOVIMENTS = json.loads((CAU42 / 'moviments_capes_pere.json').read_text())['moviments'] if (CAU42 / 'moviments_capes_pere.json').exists() else {}   # ordre de Pere (10-09): capes 06-12 mogudes un vector ENTER (byte a byte) per coincidir amb la base
def mou_mascara(m, dx, dy):
    out = np.zeros_like(m); H_, W_ = m.shape; ys, yd = (slice(0, H_ - dy), slice(dy, H_)) if dy >= 0 else (slice(-dy, H_), slice(0, H_ + dy)); xs, xd = (slice(0, W_ - dx), slice(dx, W_)) if dx >= 0 else (slice(-dx, W_), slice(0, W_ + dx)); out[yd, xd] = m[ys, xs]; return out
MASK_DESC = {'powaaah3_mascara_disc_u16.npy': 'disc POWAAAH3 (R+6, ploma 8)', 'earthshine_v42_mascara_u16.npy': 'disc earthshine V42 (1 fins a R 453,5, 0 a R 457,5 = vora del forat)'}
MASK_POW = CAU42 / 'powaaah3_mascara_disc_u16.npy'


def pla_ok():
    for nom, kind, src, *_ in PLA:
        if kind != 'copy': assert Path(src).exists(), src
    return True


def build():
    assert not TARGET.exists() and pla_ok(); s39 = PSDImage.open(F39); n39 = {l.name: l for l in s39}; s41 = PSDImage.open(F41); n41 = {l.name: l for l in s41}
    mk = C.mascara_lluna_inici(); mbox = (0, 0, FW, FH); s = PSDImage.new('RGB', (FW, FH), depth=16); s._record.header.version = 2; rep = {'fonts': {'V39.psb': sha(F39), 'V41.psb (modes de Pere)': sha(F41)}, 'capes': []}
    for nom, kind, src, blend, op, vis, *ext in PLA:
        mpath = Path(ext[0]) if ext else MASK_POW
        if kind == 'copy':
            o = n39[src]; ref = n41.get(src, o); rgb, alpha, mask, box, bg = C.source_arrays(o); mv = MOVIMENTS.get(nom); bbox = tuple(o.bbox)
            if mv:
                dx, dy = int(mv[0]), int(mv[1]); bbox = (bbox[0] + dx, bbox[1] + dy, bbox[2] + dx, bbox[3] + dy); assert 0 <= bbox[0] and 0 <= bbox[1] and bbox[2] <= FW and bbox[3] <= FH, (nom, bbox)
                if mask is not None: assert tuple(box) == (0, 0, FW, FH), (nom, box); mask = mou_mascara(mask, dx, dy)
            C.add_layer(s, rgb, nom, alpha, mask, box, bg, ref.blend_mode if blend is None else blend, ref.opacity if op is None else op, ref.visible if vis is None else vis, bbox)
            rep['capes'].append({'name': nom, 'kind': 'copy', 'font': 'V39.psb', 'bbox': list(bbox), 'bbox_V39': list(o.bbox), 'moviment_px': list(mv) if mv else None, 'blend': str(ref.blend_mode if blend is None else blend), 'opacity': ref.opacity if op is None else op, 'visible': ref.visible if vis is None else vis}); del rgb, alpha, mask
        else:
            u = np.asarray(np.load(src, mmap_mode='r')); assert u.shape[:2] == (FH, FW) and u.dtype == np.uint16, (nom, u.shape, u.dtype)
            m_ = np.asarray(np.load(mpath, mmap_mode='r')) if kind == 'u16m' else mk
            C.add_layer(s, u, nom, None, m_, mbox, 0, blend, op, vis, (0, 0, FW, FH))
            rep['capes'].append({'name': nom, 'kind': kind, 'u16': str(src), 'u16_sha256': sha(Path(src)), 'blend': str(blend), 'opacity': op, 'visible': vis, 'mascara': MASK_DESC[mpath.name] if kind == 'u16m' else 'forat lunar a l\'inici (R 455,5 + 2 px)', 'mascara_fitxer': str(mpath) if kind == 'u16m' else None}); del u
        gc.collect(); log('capa ' + nom)
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
        if l.blend_mode == BlendMode.OVERLAY: f_ = np.where(b <= .5, 2 * b * a, 1 - 2 * (1 - b) * (1 - a)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.HARD_LIGHT: f_ = np.where(a <= .5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.SOFT_LIGHT: f_ = np.where(a <= .5, b - (1 - 2 * a) * b * (1 - b), b + (2 * a - 1) * (np.where(b <= .25, ((16 * b - 12) * b + 4) * b, np.sqrt(b)) - b)); comp[t0:b0, l0:r0] = b * (1 - wgt) + f_ * wgt
        elif l.blend_mode == BlendMode.MULTIPLY: comp[t0:b0, l0:r0] = b * (1 - wgt) + (a * b) * wgt
        elif l.blend_mode == BlendMode.LINEAR_DODGE: comp[t0:b0, l0:r0] = np.clip(b + a * wgt, 0, 1)
        else: comp[t0:b0, l0:r0] = b * (1 - wgt) + a * wgt
        del a, al, wgt; gc.collect(); log('compost + ' + l.name)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = C.ImageData(compression=C.Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    from PIL import Image; Image.fromarray(np.uint8(np.clip(comp[::4, ::4], 0, 1) * 255)).save(VIS42 / 'C4_compost_V42_llenc_sencer.png'); del comp, data
    with open(TARGET, 'xb'): pass
    s.save(TARGET); rep['target'] = str(TARGET); rep['layers'] = len(s); savejson(REB42 / 'C4_packaging.json', rep); log(f'desat {TARGET} ({len(s)} capes)')


def verify():
    rep = json.loads((REB42 / 'C4_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s); s39 = PSDImage.open(F39); n39 = {l.name: l for l in s39}; mk = C.mascara_lluna_inici(); mpow = np.load(MASK_POW)
    assert len(ls) == len(PLA) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16; rows = []
    for l, (nom, kind, src, blend, op, vis, *ext), rc in zip(ls, PLA, rep['capes']):
        mref = (np.load(ext[0]) if ext else mpow) if kind == 'u16m' else mk
        assert l.name == nom, (l.name, nom); okp = str(l.blend_mode) == rc['blend'] and l.opacity == rc['opacity'] and l.visible == rc['visible']; md = l._record.mask_data
        if kind == 'copy':
            o = n39[src]; rgb, alpha, mask, box, bg = C.source_arrays(o); mv = MOVIMENTS.get(nom); bbox = tuple(o.bbox)
            if mv: dx, dy = int(mv[0]), int(mv[1]); bbox = (bbox[0] + dx, bbox[1] + dy, bbox[2] + dx, bbox[3] + dy); mask = mou_mascara(mask, dx, dy) if mask is not None else None
            ok = okp and (l._record.left, l._record.top, l._record.right, l._record.bottom) == bbox and (rc.get('moviment_px') == (list(mv) if mv else None)) and all(np.array_equal(C.channel(l, c), rgb[..., c]) for c in range(3)) and ((alpha is None and (C.channel(l, -1) is None or bool(np.all(C.channel(l, -1) == 65535)))) or np.array_equal(C.channel(l, -1), alpha))
            ok = ok and ((mask is None and md is None) or (md is not None and (md.left, md.top, md.right, md.bottom) == tuple(box) and np.array_equal(C.channel(l, -2), mask))); del rgb, alpha, mask
        else:
            u = np.load(src, mmap_mode='r'); ok = okp and all(np.array_equal(C.channel(l, c), u[..., c] if u.ndim == 3 else u) for c in range(3)) and md is not None and np.array_equal(C.channel(l, -2), mref) and bool(np.all(C.channel(l, -1) == 65535)) and (l._record.left, l._record.top, l._record.right, l._record.bottom) == (0, 0, FW, FH)
        assert ok, nom; rows.append({'name': nom, 'kind': kind, 'exact': True}); log('verificada ' + nom); gc.collect()
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': len(ls), 'rows': rows}; savejson(REB42 / 'C4_verification.json', out); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB42 / 'C4_verification.json').read_text()); assert v['PASS']
    def jsx(js): return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally: jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    savejson(REB42 / 'C4_photoshop_gate.json', {'result': res.stdout.strip(), 'file': str(TARGET), 'sha256': v['sha256']}); log(res.stdout.strip())


def publish():
    v = json.loads((REB42 / 'C4_verification.json').read_text()); g = json.loads((REB42 / 'C4_photoshop_gate.json').read_text())
    assert v['PASS'] and g['sha256'] == v['sha256'] and g['result'].startswith('OBRE') and sha(TARGET) == v['sha256'] and not FINAL.exists()
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] in (CLAIM, 'CLAUDE_V42_ALINEA_20260910')
    tmp = CT / 'V42_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_: shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL)
    savejson(REB42 / 'C4_publish.json', {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'layers': v['layers']}); log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
