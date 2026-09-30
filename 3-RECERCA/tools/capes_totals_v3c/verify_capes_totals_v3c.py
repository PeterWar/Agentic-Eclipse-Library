"""Verificació de CapesTotalsV3c.psb reobert: ràsters (RGB+alfa) de les 12 capes byte-idèntics a V3b (= fonts pinades);
màscares noves decodificades == mask_<id>.npy i amb bbox al llenç; la resta de màscares byte-idèntiques a V3b; visibilitat
declarada; Normal/100 %/farciment; bbox de capa igual a V3b; merged del PSB == compost offline (≤1 DN) i == compost de la
cadena (states/S<top>.npy) a ≤1 DN.
Les màscares no noves es comparen amb V2b (màscares CRUES de les fonts: ID9 torna a la crua de CT1 perquè a V3c és REBUTJADA).
Ús: verify_capes_totals_v3c.py <V3c.psb> <V3b.psb> <V2b.psb> <mask_dir> <visible_ids: 3,4,5,7,8> <state_top.npy> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'capes_totals_v2'))
import build_capes_totals_v2 as B
from psd_tools import PSDImage

def main():
    v3c, v3b, v2b, mask_dir = map(Path, sys.argv[1:5]); visible = {int(x) for x in sys.argv[5].split(',')}; state_top = Path(sys.argv[6]); out = Path(sys.argv[7])
    rep = {'v3c': str(v3c), 'sha256_v3c': B.sha256_file(v3c), 'size_v3c': v3c.stat().st_size, 'layers': {}, 'ok': True}
    a = PSDImage.open(v3c); b = PSDImage.open(v3b); c = PSDImage.open(v2b); ha = a._record.header
    la = {l.layer_id: l for l in a}; lb = {l.layer_id: l for l in b}; lc = {l.layer_id: l for l in c}
    assert list(la) == list(lb) == list(B.OUTPUT_LAYER_IDS)
    for i in B.OUTPUT_LAYER_IDS:
        x, y = la[i], lb[i]
        r = {'name': x.name, 'visible': x.visible, 'opacity': x.opacity, 'blend': x.blend_mode.value.decode(), 'fill': x.fill_opacity, 'bbox': list(x.bbox), 'bbox_v3b': list(y.bbox),
             'raster_equal_v3b': B.raw_nonmask_fingerprints(x) == B.raw_nonmask_fingerprints(y),
             'mask_bbox': [x._record.mask_data.left, x._record.mask_data.top, x._record.mask_data.right, x._record.mask_data.bottom]}
        if (mask_dir / f'mask_{i}.npy').exists():
            m, md = B._decoded_mask_u16(x, ha); ref = np.load(mask_dir / f'mask_{i}.npy', mmap_mode='r')
            r['mask_equal_new'] = bool(m.shape == ref.shape and np.array_equal(np.asarray(m), np.asarray(ref)))
            r['mask_sha256_u16'] = B.sha256_u16_be(np.asarray(m)); r['mask_bbox_llenc'] = r['mask_bbox'] == [0, 0, B.WIDTH, B.HEIGHT]
            ok_i = r['raster_equal_v3b'] and r['mask_equal_new'] and r['mask_bbox_llenc']
        else:
            r['mask_equal_v2b_crua'] = B.raw_channel_fingerprints(x) == B.raw_channel_fingerprints(lc[i]); ok_i = r['raster_equal_v3b'] and r['mask_equal_v2b_crua']
        ok_i = ok_i and (x.visible == (i in visible)) and x.blend_mode == B.BlendMode.NORMAL and x.opacity == 255 and x.fill_opacity == 255 and list(x.bbox) == list(y.bbox)
        r['ok'] = bool(ok_i); rep['layers'][str(i)] = r; rep['ok'] &= bool(ok_i)
        print(i, 'OK' if ok_i else 'KO', x.name[:70], 'vis', x.visible, flush=True)
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
        d = np.abs(chans[k].astype(np.int32) - np.asarray(rgba[..., k]).astype(np.int32)); dif[str(k)] = {'max': int(d.max()), 'n_gt0': int((d > 0).sum())}
    rep['merged_vs_offline_DN'] = dif; rep['merged_ok'] = all(v['max'] <= 1 for v in dif.values()); rep['ok'] &= rep['merged_ok']
    st = np.load(state_top, mmap_mode='r'); top_frame = (463, 5103, 457, 7417)  # el compost de la cadena només és vàlid dins del marc d'ID3..ID9 (la resta és fons)
    y0, y1, x0, x1 = 465, 5101, 461, 7415  # interior comú dels marcs (ID3 a 459,461)
    difs = {}
    for k in range(3):
        d = np.abs(chans[k][y0:y1, x0:x1].astype(np.int32) - np.asarray(st[y0:y1, x0:x1, k]).astype(np.int32)); difs[str(k)] = {'max': int(d.max()), 'n_gt1': int((d > 1).sum())}
    rep['merged_vs_cadena_DN'] = difs; rep['cadena_ok'] = all(v['max'] <= 1 for v in difs.values()); rep['ok'] &= rep['cadena_ok']
    rep['merged_rgba16_offline_sha256'] = B.sha256_file(rp)
    json.dump(rep, open(out, 'w'), indent=1, ensure_ascii=False)
    print('merged vs offline:', dif, '\nmerged vs cadena:', difs, '\nOK GLOBAL:', rep['ok'])

if __name__ == '__main__':
    main()
