"""Bolca cada capa de CapesInteriorsV3.psb: RGB uint16 (npy) + màscara (uint16 npy, a la profunditat del document)
+ metadades (json), i una previsualització a 1/4 (PNG 8 bits amb gamma) per mirar-s'ho."""
import os, json, numpy as np
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
from PIL import Image
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
OUT = 'v3/'
psd = PSDImage.open(D + 'CapesInteriorsV3.psb')
hdr = psd._record.header
W, H = hdr.width, hdr.height
meta = {'W': W, 'H': H, 'layers': []}
for i, l in enumerate(psd):
    rec = l._record
    l0, t0, r0, b0 = l.bbox
    # canals de color per psd-tools (uint16)
    arr = l.numpy()  # float32 0..1, (h, w, c) amb alfa?
    # millor llegir els canals crus per evitar conversions
    chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    h, w = b0 - t0, r0 - l0
    rgb = np.zeros((h, w, 3), np.uint16)
    for c in range(3):
        cd = chans[ChannelID(c)]
        rgb[..., c] = np.frombuffer(cd.get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w)
    name = f'{i:02d}_' + ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in l.name)[:60]
    np.save(OUT + name + '_rgb.npy', rgb)
    info = {'idx': i, 'name': l.name, 'bbox': [l0, t0, r0, b0], 'blend': str(l.blend_mode), 'opacity': l.opacity, 'visible': l.visible, 'mask': None}
    md = rec.mask_data
    if md is not None and ChannelID.USER_LAYER_MASK in chans:
        ml, mt, mr, mb = md.left, md.top, md.right, md.bottom
        mh, mw = mb - mt, mr - ml
        cd = chans[ChannelID.USER_LAYER_MASK]
        raw = cd.get_data(mw, mh, hdr.depth, hdr.version)
        nb = len(raw)
        if nb == mw * mh * 2:
            mask = np.frombuffer(raw, dtype='>u2').reshape(mh, mw)
        elif nb == mw * mh:
            mask = (np.frombuffer(raw, dtype='u1').reshape(mh, mw).astype(np.uint16) * 257)
            print('  (màscara a 8 bits)')
        else:
            raise RuntimeError(f'mida de màscara inesperada {nb} per {mw}x{mh}')
        np.save(OUT + name + '_mask.npy', mask)
        info['mask'] = {'bbox': [ml, mt, mr, mb], 'bg': md.background_color, 'bits': 16 if nb == mw*mh*2 else 8}
        print(i, l.name, l.bbox, 'mask', (ml, mt, mr, mb), 'bg', md.background_color, 'mask range', int(mask.min()), int(mask.max()), 'vis', l.visible, flush=True)
    else:
        print(i, l.name, l.bbox, 'sense màscara', 'vis', l.visible, flush=True)
    meta['layers'].append(info)
    # previsualització 1/4
    sm = rgb[::4, ::4].astype(np.float32) / 65535.
    Image.fromarray((np.clip(sm, 0, 1) ** (1/2.2) * 255).astype(np.uint8)).save(OUT + name + '_prev.png')
    if info['mask']:
        Image.fromarray((mask[::4, ::4] // 257).astype(np.uint8)).save(OUT + name + '_mask_prev.png')
json.dump(meta, open(OUT + 'meta.json', 'w'), indent=1, ensure_ascii=False)
# fusionada del document
try:
    idata = psd._record.image_data
    dat = idata.get_data(hdr)
    merged = np.stack([np.frombuffer(c, dtype='>u2').reshape(H, W) for c in dat[:3]], -1)
    np.save(OUT + 'merged_rgb.npy', merged)
    sm = merged[::4, ::4].astype(np.float32) / 65535.
    Image.fromarray((np.clip(sm, 0, 1) ** (1/2.2) * 255).astype(np.uint8)).save(OUT + 'merged_prev.png')
    print('fusionada', merged.shape, merged.min(), merged.max())
except Exception as e:
    print('fusionada: no llegida', e)
