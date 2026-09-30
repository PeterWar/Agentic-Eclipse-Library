"""B6b · PSB LLEUGER d'una versió de filtres: UNA capa base lineal + les capes de filtre.

Norma de Pere (07-09-2026): mentre quedin artefactes als filtres, cada versió nova itera
només sobre els filtres amb una sola capa base linealitzada; no s'arrossega el projecte
no-linealitzat sencer.

Contingut: `00 Base lineal` = fusió lineal RGB (sRGB lineal, matriu i guany del run) escalada
per un únic factor declarat (el màxim de la dada dins del suport → 65535), alfa = suport
físic; i les capes de filtre amb el MATEIX alfa, màscara, mode, opacitat i visibilitat que
tenen al PSB complet de la versió (es llegeixen d'allà, no s'inventen). Cap altra capa.

Ús: `b6b_psb_lleuger.py build|verify|gate [--font V32.psb] [--out V32_lleuger.psb]`.
"""
import os, sys, json, copy, gc, subprocess, argparse
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'research/tools/v29')); sys.path.insert(0, str(ROOT / 'research/tools/encaix_sony'))
from common import *
from inspect_inputs import sha, channel
from psb_utils import finalize_lr16
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression, BlendMode, ChannelID
from psd_tools.psd.layer_and_mask import LayerRecord, ChannelInfo, ChannelData, ChannelDataList, MaskData, MaskFlags
from psd_tools.psd.tagged_blocks import TaggedBlocks
from psd_tools.psd.image_data import ImageData
HERE = Path(__file__).resolve().parent
CAU32 = HERE / 'cau'; STAGING = HERE / 'staging'; STAGING.mkdir(exist_ok=True)
REB = ROOT / 'output/v32_arcs_20260907/4-rebuts'
ap = argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('--font', default=str(CT / 'V32.psb')); ap.add_argument('--out', default=str(STAGING / 'V32_lleuger.psb'))
ap.add_argument('--fusio', default=str(CAU32 / 'fusion_total_v32.npy')); ap.add_argument('--suport', default=str(CAU32 / 'support_v32.npy'))
A = ap.parse_args(); FONT = Path(A.font); OUT = Path(A.out)
FILTRES = ('03 ACHF azimutal 8-128', '07 ACHF azimutal suau r8', '01 ACHF fi 2-32', '02 Passa-alt 24', '04 ACHF micro 1-16', '05 ACHF fi 2-48', '06 ACHF estructura 4-64',
           'P01 NRGF', 'P02 RHEF', 'P03 MGN', 'P04 WOW', 'P05 WOW bilateral', 'P06 NAFE', 'P07 ACHF', 'P08 ACHF', 'P09 SWAP', 'C01 Passa-alt24')


def compressed(u):
    cd = ChannelData(Compression.ZIP); cd.set_data(np.ascontiguousarray(np.asarray(u).astype('>u2')).tobytes(), FW, FH, 16, 2); return cd


def add_layer(s, rgb_u16, name, alpha_u16, mask_u16, mask_box, blend, opacity, visible):
    """rgb_u16: (H,W) gris o (H,W,3); alpha (H,W) o None (=opac); mask (h,w) amb la seva caixa o None."""
    rec = LayerRecord(top=0, left=0, bottom=FH, right=FW, channel_info=[]); rec.tagged_blocks = TaggedBlocks(); rec.name = name
    chans = ChannelDataList()
    alpha = compressed(np.full((FH, FW), 65535, np.uint16) if alpha_u16 is None else alpha_u16)
    if rgb_u16.ndim == 2:
        color = compressed(rgb_u16); cols = [color, color, color]
    else:
        cols = [compressed(rgb_u16[..., c]) for c in range(3)]
    pairs = [(-1, alpha), (0, cols[0]), (1, cols[1]), (2, cols[2])]
    if mask_u16 is not None:
        l0, t0, r0, b0 = mask_box; m = ChannelData(Compression.ZIP); m.set_data(np.ascontiguousarray(np.asarray(mask_u16).astype('>u2')).tobytes(), r0 - l0, b0 - t0, 16, 2)
        pairs.append((-2, m)); rec.mask_data = MaskData(top=t0, left=l0, bottom=b0, right=r0, background_color=0, flags=MaskFlags())
    for cid, cd in pairs:
        rec.channel_info.append(ChannelInfo(ChannelID(cid), len(cd.data) + 2)); chans.append(copy.copy(cd))
    l = PixelLayer(s, rec, chans); s.append(l); l.name = name; l.blend_mode = blend; l.opacity = opacity; l.visible = visible
    return l


def build():
    assert not OUT.exists(), OUT
    src = PSDImage.open(FONT); ls = list(src); assert src.size == (FW, FH) and src.depth == 16
    fus = np.load(A.fusio, mmap_mode='r'); sup = np.load(A.suport)
    scale = float(np.nanmax(np.where(sup[..., None], np.asarray(fus), 0)))
    base = np.round(np.clip(np.nan_to_num(np.asarray(fus)) / scale, 0, 1) * 65535).astype(np.uint16); base[~sup] = 0
    s = PSDImage.new('RGB', (FW, FH), depth=16)
    s._record.header.version = 2               # PSB: el llenç passa de 30000 px de límit PSD i el fitxer de 2 GB
    rep = {'font': str(FONT), 'font_sha256': sha(FONT), 'fusio': A.fusio, 'suport': A.suport, 'escala_lineal': scale, 'escala_definicio': 'màxim de la fusió lineal dins del suport → 65535; ln no aplicat; cap corba', 'capes': []}
    add_layer(s, base, '00 Base lineal · V32', (sup.astype(np.uint16) * 65535), None, None, BlendMode.NORMAL, 255, True); rep['capes'].append({'name': '00 Base lineal · V32', 'role': 'base lineal RGB, alfa = suport'})
    del base
    for l in ls:
        if not any(l.name.startswith(f) for f in FILTRES):
            continue
        rgb = np.stack([channel(l, c) for c in range(3)], axis=-1) if not all(np.array_equal(channel(l, 0), channel(l, c)) for c in (1, 2)) else channel(l, 0)
        alpha = channel(l, -1); md = l._record.mask_data; mask = channel(l, -2) if md is not None else None
        box = (md.left, md.top, md.right, md.bottom) if md is not None else None
        add_layer(s, rgb, l.name, alpha, mask, box, l.blend_mode, l.opacity, l.visible)
        rep['capes'].append({'name': l.name, 'blend': str(l.blend_mode), 'opacity': l.opacity, 'visible': l.visible, 'mask_box': box, 'rgb_sha256_from_font': True}); log('capa ' + l.name); gc.collect()
    finalize_lr16(s)
    # compost per defecte: base + capes visibles (Superposar), com a previsualització
    sys.path.insert(0, str(ROOT / 'research/tools/v29')); from build_canvas import over
    comp = np.zeros((FH, FW, 3), np.float32)
    for l in s:
        if not l.visible:
            continue
        a = np.stack([channel(l, c) for c in range(3)], axis=-1).astype(np.float32) / 65535 if l.name.startswith('00') else np.repeat(channel(l, 0)[..., None].astype(np.float32) / 65535, 3, axis=2)
        al = channel(l, -1); al = np.ones((FH, FW), np.float32) if al is None else al.astype(np.float32) / 65535
        md = l._record.mask_data
        if md is not None:
            mk = np.full((FH, FW), md.background_color / 255, np.float32); mk[md.top:md.bottom, md.left:md.right] = channel(l, -2).astype(np.float32) / 65535; al = al * mk
        comp = over(comp, a, al, l.opacity / 255, 'overlay' if l.blend_mode == BlendMode.OVERLAY else 'normal'); del a, al
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)]
    merged = ImageData(compression=Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    with open(OUT, 'xb'):
        pass
    s.save(OUT); rep['out'] = str(OUT); rep['layers'] = len(s)
    (REB / f'B6b_{OUT.stem}_packaging.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); log(f'desat {OUT} ({len(s)} capes)')


def verify():
    rep = json.loads((REB / f'B6b_{OUT.stem}_packaging.json').read_text()); s = PSDImage.open(OUT); src = PSDImage.open(FONT); by = {l.name: l for l in src}
    ls = list(s); assert len(ls) == len(rep['capes']) and s.size == (FW, FH) and s.depth == 16
    fus = np.load(A.fusio, mmap_mode='r'); sup = np.load(A.suport); scale = rep['escala_lineal']
    b = ls[0]; assert b.name.startswith('00 Base lineal')
    for c in range(3):
        exp = np.round(np.clip(np.nan_to_num(np.asarray(fus[..., c])) / scale, 0, 1) * 65535).astype(np.uint16); exp[~sup] = 0
        assert np.array_equal(channel(b, c)[::5, ::5], exp[::5, ::5]), c
    assert np.array_equal(channel(b, -1)[::5, ::5], (sup.astype(np.uint16) * 65535)[::5, ::5])
    rows = []
    for l in ls[1:]:
        o = by[l.name]; ok = all(np.array_equal(channel(l, c), channel(o, c)) for c in (0, 1, 2)) and np.array_equal(channel(l, -1), channel(o, -1))
        mo = o._record.mask_data; ml = l._record.mask_data
        okm = (mo is None and ml is None) or (mo is not None and ml is not None and (mo.left, mo.top, mo.right, mo.bottom) == (ml.left, ml.top, ml.right, ml.bottom) and np.array_equal(channel(l, -2), channel(o, -2)))
        assert ok and okm and l.blend_mode == o.blend_mode and l.opacity == o.opacity and l.visible == o.visible, l.name
        rows.append({'name': l.name, 'exact_vs_font': True})
    out = {'PASS': True, 'path': str(OUT), 'sha256': sha(OUT), 'bytes': OUT.stat().st_size, 'layers': len(ls), 'base_exact': True, 'filters_exact_vs_font': rows}
    (REB / f'B6b_{OUT.stem}_verification.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n'); log(f"verificat {out['sha256']} · {out['bytes']:,} bytes · {len(ls)} capes")


def gate():
    v = json.loads((REB / f'B6b_{OUT.stem}_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();')
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(OUT)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr; assert res.stdout.strip() == f'OBRE 10551 px x 7506 px · {v["layers"]} capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    (REB / f'B6b_{OUT.stem}_photoshop_gate.json').write_text(json.dumps({'result': res.stdout.strip(), 'file': str(OUT), 'sha256': v['sha256']}, indent=1) + '\n'); log(res.stdout.strip())


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate}[A.mode]()
