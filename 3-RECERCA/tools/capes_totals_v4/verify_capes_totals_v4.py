"""Verificació de CapesTotalsV4.psb reobert:
- canals RGB de cada capa == revelat V4 (TIFF pinada per SHA) dins del seu rectangle; marges d'ID4/ID5
  i canals alfa == fonts (V2b) byte a byte;
- màscares noves decodificades == mask_<id>.npy amb bbox al llenç; ID3 sense màscara declarada (blanca de la font);
- visibilitat declarada; Normal/100 %/farciment; bbox de capa igual a V2b (offsets V2b);
- merged del PSB == compost offline (≤1 DN) i == compost de la cadena (states/S<top>.npy) a ≤1 DN.
Ús: verify_capes_totals_v4.py <V4.psb> <V2b.psb> <mask_dir> <visible_ids> <state_top.npy> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
import tifffile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'capes_totals_v2'))
import build_capes_totals_v2 as B
from psd_tools import PSDImage
from psd_tools.constants import ChannelID

REVELAT = Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'
LAYER_PREFIX = {3: '12', 4: '11', 5: '10', 7: '09', 8: '08', 9: '07', 10: '06',
                11: '05', 12: '04', 13: '03', 16: '02', 17: '01'}
IMG_RECT = {4: (458, 464, 6960, 4640), 5: (458, 464, 6960, 4640)}

def main():
    v4, v2b, mask_dir = map(Path, sys.argv[1:4])
    visible = {int(x) for x in sys.argv[4].split(',')}
    state_top = Path(sys.argv[5])
    out = Path(sys.argv[6])
    if out.parent.is_symlink():
        raise SystemExit(f'NO-CLOBBER VERIFICACIÓ: pare simbòlic no autoritzat: {out.parent}')
    if out.exists() or out.is_symlink():
        raise SystemExit(f'NO-CLOBBER VERIFICACIÓ: ja existeix: {out}')
    rep = {'v4': str(v4), 'sha256_v4': B.sha256_file(v4), 'size_v4': v4.stat().st_size, 'layers': {}, 'ok': True}
    a = PSDImage.open(v4)
    c = PSDImage.open(v2b)
    ha = a._record.header
    la = {l.layer_id: l for l in a}
    lc = {l.layer_id: l for l in c}
    assert list(la) == list(B.OUTPUT_LAYER_IDS)
    for i in B.OUTPUT_LAYER_IDS:
        x = la[i]
        new = tifffile.imread(str(REVELAT / 'out' / f'v4_{LAYER_PREFIX[i]}.tif'))
        r = {'name': x.name, 'visible': x.visible, 'opacity': x.opacity, 'blend': x.blend_mode.value.decode(),
             'fill': x.fill_opacity, 'bbox': list(x.bbox), 'bbox_v2b': list(lc[i].bbox)}
        alpha_eq = (B.raw_channel_fingerprints(x).get(str(int(ChannelID.TRANSPARENCY_MASK)))
                    == B.raw_channel_fingerprints(lc[i]).get(str(int(ChannelID.TRANSPARENCY_MASK))))
        r['alpha_equal_v2b'] = bool(alpha_eq)
        rect = IMG_RECT.get(i)
        rgb_ok = True
        for k, cid in enumerate((ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)):
            back = B._decoded_channel_u16(x, cid, ha)
            if rect is None:
                ok = np.array_equal(back, new[..., k])
            else:
                x0, y0, w, h = rect
                ok = np.array_equal(back[y0:y0 + h, x0:x0 + w], new[..., k])
                old = B._decoded_channel_u16(lc[i], cid, c._record.header)
                marge_old = old.copy(); marge_old[y0:y0 + h, x0:x0 + w] = 0
                marge_new = back.copy(); marge_new[y0:y0 + h, x0:x0 + w] = 0
                ok = ok and np.array_equal(marge_new, marge_old)
            rgb_ok &= bool(ok)
        r['raster_equal_render_v4'] = bool(rgb_ok)
        if (mask_dir / f'mask_{i}.npy').exists():
            m, md = B._decoded_mask_u16(x, ha)
            ref = np.load(mask_dir / f'mask_{i}.npy', mmap_mode='r')
            r['mask_equal_new'] = bool(m.shape == ref.shape and np.array_equal(np.asarray(m), np.asarray(ref)))
            r['mask_sha256_u16'] = B.sha256_u16_be(np.asarray(m))
            r['mask_bbox_llenc'] = [md.left, md.top, md.right, md.bottom] == [0, 0, B.WIDTH, B.HEIGHT]
            ok_i = rgb_ok and r['mask_equal_new'] and r['mask_bbox_llenc']
        else:
            r['mask_equal_v2b'] = (B.raw_channel_fingerprints(x).get(str(int(ChannelID.USER_LAYER_MASK)))
                                   == B.raw_channel_fingerprints(lc[i]).get(str(int(ChannelID.USER_LAYER_MASK))))
            ok_i = rgb_ok and r['mask_equal_v2b']
        ok_i = (ok_i and alpha_eq and (x.visible == (i in visible)) and x.blend_mode == B.BlendMode.NORMAL
                and x.opacity == 255 and x.fill_opacity == 255 and list(x.bbox) == list(lc[i].bbox))
        r['ok'] = bool(ok_i)
        rep['layers'][str(i)] = r
        rep['ok'] &= bool(ok_i)
        print(i, 'OK' if ok_i else 'KO', x.name[:70], 'vis', x.visible, flush=True)
    work = out.parent / f'verify_work_{out.stem}'
    if work.exists() or work.is_symlink():
        raise SystemExit(f'NO-CLOBBER VERIFICACIÓ: ja existeix: {work}')
    work.mkdir()
    fp, rp = work / 'merged_float32.npy', work / 'merged_rgba16.npy'
    rgba = B.compose_normal_rgba4_to_npy(a, ha, fp, rp)
    merged = a._record.image_data.get_data(ha, split=True)
    W, H = ha.width, ha.height
    chans = [np.frombuffer(merged[k], dtype='>u2').reshape(H, W) for k in range(len(merged))]
    dif = {}
    for k in range(min(4, len(chans))):
        d = np.abs(chans[k].astype(np.int32) - np.asarray(rgba[..., k]).astype(np.int32))
        dif[str(k)] = {'max': int(d.max()), 'n_gt0': int((d > 0).sum())}
    rep['merged_vs_offline_DN'] = dif
    rep['merged_ok'] = all(v['max'] <= 1 for v in dif.values())
    rep['ok'] &= rep['merged_ok']
    st = np.load(state_top, mmap_mode='r')
    y0, y1, x0, x1 = 465, 5101, 461, 7415
    difs = {}
    for k in range(3):
        d = np.abs(chans[k][y0:y1, x0:x1].astype(np.int32) - np.asarray(st[y0:y1, x0:x1, k]).astype(np.int32))
        difs[str(k)] = {'max': int(d.max()), 'n_gt1': int((d > 1).sum())}
    rep['merged_vs_cadena_DN'] = difs
    rep['cadena_ok'] = all(v['max'] <= 1 for v in difs.values())
    rep['ok'] &= rep['cadena_ok']
    rep['merged_rgba16_offline_sha256'] = B.sha256_file(rp)
    with open(out, 'x') as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print('merged vs offline:', dif, '\nmerged vs cadena:', difs, '\nOK GLOBAL:', rep['ok'])

if __name__ == '__main__':
    main()
