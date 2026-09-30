"""Extreu els canals de les dues capes a .npy (uint16), a partir de layers_index.json."""
import json, mmap, sys
import numpy as np

path = '/Users/USUARI/Downloads/NoEncaixa.tif'
idx = json.load(open('layers_index.json'))
f = open(path, 'rb')
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

for r in idx:
    top, left, bottom, right = r['bbox']
    h, w = bottom - top, right - left
    tagname = 'vixen' if r['idx'] == 0 else 'sony'
    for c in r['channel_data']:
        cid, comp, off, ln = c['id'], c['compression'], c['offset'], c['length']
        if cid == -2:
            m = r['mask']
            hh, ww = m['bottom'] - m['top'], m['right'] - m['left']
        else:
            hh, ww = h, w
        assert comp == 0, comp
        assert ln == hh * ww * 2, (ln, hh, ww)
        arr = np.frombuffer(mm, dtype='>u2', count=hh * ww, offset=off).reshape(hh, ww)
        name = {-2: 'mask', -1: 'alpha', 0: 'R', 1: 'G', 2: 'B'}[cid]
        out = f'{tagname}_{name}.npy'
        np.save(out, arr)
        print(out, arr.shape, arr.dtype, 'min', arr.min(), 'max', arr.max(), 'p50', np.percentile(arr[::16, ::16], 50))
