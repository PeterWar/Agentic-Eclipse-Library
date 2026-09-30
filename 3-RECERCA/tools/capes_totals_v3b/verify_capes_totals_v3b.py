"""Verificació de CapesTotalsV3b.psb contra V2b i contra les màscares noves.
- ràsters (RGB + alfa) de les 12 capes: SHA dels canals crus idèntics a V2b (és a dir, a les fonts pinades);
- màscares de 3,4,5,7,11,12,13,16,17: canal cru idèntic a V2b; màscares de 8,9,10: decodificades == mask_<id>.npy (u16);
- visibilitat, noms, Normal/100 %/farciment 100 %, bbox i offsets iguals a V2b;
- merged del PSB == compost offline (recomposició Normal en float32 de les capes visibles) a ≤1 DN.
Ús: verify_capes_totals_v3b.py <V3b.psb> <V2b.psb> <mask_dir> <sortida.json>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'capes_totals_v2'))
import build_capes_totals_v2 as B
from psd_tools import PSDImage
from psd_tools.constants import ChannelID

def main():
    v3b, v2b, mask_dir, out = map(Path, sys.argv[1:5])
    rep = {'v3b': str(v3b), 'v2b': str(v2b), 'sha256_v3b': B.sha256_file(v3b), 'size_v3b': v3b.stat().st_size, 'layers': {}, 'ok': True}
    a = PSDImage.open(v3b); b = PSDImage.open(v2b)
    ha, hb = a._record.header, b._record.header
    la = {l.layer_id: l for l in a}; lb = {l.layer_id: l for l in b}
    assert list(la) == list(lb) == list(B.OUTPUT_LAYER_IDS), (list(la), list(lb))
    for i in B.OUTPUT_LAYER_IDS:
        x, y = la[i], lb[i]
        fa = B.raw_nonmask_fingerprints(x); fb = B.raw_nonmask_fingerprints(y)
        r = {'name': x.name, 'visible': x.visible, 'opacity': x.opacity, 'blend': x.blend_mode.value.decode(), 'fill': x.fill_opacity,
             'bbox': list(x.bbox), 'bbox_v2b': list(y.bbox), 'raster_equal_v2b': fa == fb,
             'mask_bbox': [x._record.mask_data.left, x._record.mask_data.top, x._record.mask_data.right, x._record.mask_data.bottom]}
        if (mask_dir / f"mask_{i}.npy").exists():
            m, md = B._decoded_mask_u16(x, ha)
            ref = np.load(mask_dir / f'mask_{i}.npy', mmap_mode='r')
            r['mask_equal_new'] = bool(m.shape == ref.shape and np.array_equal(np.asarray(m), np.asarray(ref)))
            r['mask_sha256_u16'] = B.sha256_u16_be(np.asarray(m))
            r['mask_new_sha256_u16'] = B.sha256_u16_be(np.asarray(ref))
            ok_i = r['raster_equal_v2b'] and r['mask_equal_new'] and x.visible
        else:
            ma = B.raw_channel_fingerprints(x); mb = B.raw_channel_fingerprints(y)
            r['mask_equal_v2b'] = ma == mb
            ok_i = r["raster_equal_v2b"] and r["mask_equal_v2b"] and (x.visible == (i in (3, 4, 5, 7)))
        ok_i = ok_i and x.blend_mode == B.BlendMode.NORMAL and x.opacity == 255 and x.fill_opacity == 255 and list(x.bbox) == list(y.bbox)
        r['ok'] = bool(ok_i); rep['layers'][str(i)] = r; rep['ok'] &= bool(ok_i)
        print(i, 'OK' if ok_i else 'KO', x.name[:60], 'vis', x.visible, flush=True)
    # merged contra compost offline
    work = out.parent / 'verify_work'; work.mkdir(exist_ok=True)
    fp, rp = work / 'merged_float32.npy', work / 'merged_rgba16.npy'
    for p in (fp, rp):
        if p.exists(): p.unlink()
    rgba = B.compose_normal_rgba4_to_npy(a, ha, fp, rp)
    merged = a._record.image_data.get_data(ha, split=True)
    W, H = ha.width, ha.height
    chans = [np.frombuffer(merged[k], dtype='>u2').reshape(H, W) for k in range(len(merged))]
    dif = {}
    for k in range(min(4, len(chans))):
        d = np.abs(chans[k].astype(np.int32) - np.asarray(rgba[..., k]).astype(np.int32))
        dif[str(k)] = {'max': int(d.max()), 'n_gt0': int((d > 0).sum())}
    rep['merged_vs_offline_DN'] = dif; rep['merged_ok'] = all(v['max'] <= 1 for v in dif.values()); rep['ok'] &= rep['merged_ok']
    rep['merged_rgba16_offline_sha256'] = B.sha256_file(rp)
    json.dump(rep, open(out, 'w'), indent=1, ensure_ascii=False)
    print('merged vs offline:', dif, '\nOK GLOBAL:', rep['ok'])

if __name__ == '__main__':
    main()
