"""Extreu el CapesInteriorsV4.psb EDITAT PER PERE (només lectura): capes (només si difereixen de les conegudes: comprovem SHA per canal? massa car — bolquem màscares senceres i mostregem els píxels), màscares senceres + metadades."""
import os, json, numpy as np
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
from PIL import Image
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
meta = {'W': hdr.width, 'H': hdr.height, 'layers': []}
for i, l in enumerate(psd):
    rec = l._record; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    info = {'idx': i, 'name': l.name, 'bbox': list(l.bbox), 'visible': l.visible, 'opacity': l.opacity, 'blend': str(l.blend_mode), 'mask': None}
    md = rec.mask_data
    if md is not None and ChannelID.USER_LAYER_MASK in chans:
        mw, mh = md.right - md.left, md.bottom - md.top
        raw = chans[ChannelID.USER_LAYER_MASK].get_data(mw, mh, hdr.depth, hdr.version)
        mask = np.frombuffer(raw, dtype='>u2').reshape(mh, mw) if len(raw) == mw * mh * 2 else np.frombuffer(raw, dtype='u1').reshape(mh, mw).astype(np.uint16) * 257
        np.save(f'v5in/{i:02d}_mask.npy', mask)
        info['mask'] = {'bbox': [md.left, md.top, md.right, md.bottom], 'bg': md.background_color, 'bits': 16 if len(raw) == mw * mh * 2 else 8}
        Image.fromarray((mask[::4, ::4] // 257).astype(np.uint8)).save(f'v5in/{i:02d}_mask_prev.png')
    # mostreig ràpid dels píxels per detectar si la capa ha canviat (100 posicions fixes del canal G)
    l0, t0, r0, b0 = l.bbox; h, w = b0 - t0, r0 - l0
    G = np.frombuffer(chans[ChannelID(1)].get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w)
    rng = np.random.default_rng(42); ys = rng.integers(0, h, 200); xs = rng.integers(0, w, 200)
    info['g_sample'] = [int(v) for v in G[ys, xs]]
    meta['layers'].append(info)
    print(i, l.name[:46], l.bbox, 'vis', l.visible, 'màscara', info['mask'] is not None, flush=True)
json.dump(meta, open('v5in/meta.json', 'w'), ensure_ascii=False, indent=1)
