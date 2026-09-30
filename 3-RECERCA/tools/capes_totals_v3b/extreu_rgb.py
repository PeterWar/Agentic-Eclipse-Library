"""Extreu R i B (G ja és a ../v2b) de les capes 3,4,5,7 (Corretgint2) i 8,9,10 (CT1), i la màscara crua de 7 i 8,9,10."""
import sys, json, numpy as np, hashlib
sys.path.insert(0, '/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v2')
import build_capes_totals_v2 as B
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
out = {}
for path, ids in (('/Users/USUARI/Downloads/Corretgint2.psb', (3,4,5,7)),
                  ('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV1.psb', (8,9,10))):
    psd = PSDImage.open(path); h = psd._record.header
    by = {l.layer_id: l for l in psd}
    for i in ids:
        l = by[i]
        for cid, nm in ((ChannelID.CHANNEL_0,'R'), (ChannelID.CHANNEL_2,'B')):
            a = B._decoded_channel_u16(l, cid, h); np.save(f'src_id{i}_{nm}.npy', a)
        m, md = B._decoded_mask_u16(l, h)
        np.save(f'src_id{i}_mask.npy', m)
        out[i] = dict(bbox=list(l.bbox), mask_bbox=[md.left, md.top, md.right, md.bottom], mask_sha=B.sha256_u16_be(np.asarray(m)))
        print(i, out[i], flush=True)
    del psd
json.dump(out, open('extreu_rgb.json','w'), indent=1)
print('FET')
