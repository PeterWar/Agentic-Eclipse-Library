"""Rellegeix el PSB nou i comprova estructura, profunditat de màscares i el compost (finestres al Sol i al creixent)."""
import os, numpy as np, json
from psd_tools import PSDImage
from psd_tools.constants import ChannelID, Tag
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
print('capçalera', hdr.width, hdr.height, 'depth', hdr.depth, 'channels', hdr.channels, 'version', hdr.version)
lm = psd._record.layer_and_mask_information
print('Lr16:', lm.tagged_blocks is not None and Tag.LAYER_16 in lm.tagged_blocks)
layers = list(psd)
for l in layers:
    m = l.mask; rec = l._record; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    mi = ''
    if m is not None:
        mw, mh = m.bbox[2] - m.bbox[0], m.bbox[3] - m.bbox[1]
        raw = chans[ChannelID.USER_LAYER_MASK].get_data(mw, mh, hdr.depth, hdr.version)
        bits = 16 if len(raw) == mw * mh * 2 else 8
        arr = np.frombuffer(raw, dtype='>u2').reshape(mh, mw)
        mi = f' | màscara {bits} bits mitjana {arr.mean()/65535:.3f}'
    print(f'"{l.name[:44]}" bbox={l.bbox} vis={l.visible}{mi}')
for (y0, y1, x0, x1, lab) in ((2300, 3200, 3500, 4600, 'Sol'), (2450, 3050, 3480, 3780, 'creixent')):
    C = np.zeros((y1 - y0, x1 - x0, 3))
    for l in layers:
        if not l.visible: continue
        rec = l._record; L0, T0, R0, B0 = l.bbox; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
        rgb = np.zeros((y1 - y0, x1 - x0, 3))
        for c in range(3):
            full = np.frombuffer(chans[ChannelID(c)].get_data(R0 - L0, B0 - T0, hdr.depth, hdr.version), dtype='>u2').reshape(B0 - T0, R0 - L0)
            rgb[..., c] = full[y0 - T0:y1 - T0, x0 - L0:x1 - L0] / 65535.
        if l.mask is not None:
            mb = l.mask.bbox
            full = np.frombuffer(chans[ChannelID.USER_LAYER_MASK].get_data(mb[2] - mb[0], mb[3] - mb[1], hdr.depth, hdr.version), dtype='>u2').reshape(mb[3] - mb[1], mb[2] - mb[0])
            a = (full[y0 - mb[1]:y1 - mb[1], x0 - mb[0]:x1 - mb[0]] / 65535.)[..., None]
        else:
            a = 1.0
        C = C * (1 - a) + rgb * a
    mine = np.load('v5/compost_rgb16.npy', mmap_mode='r')
    M = np.asarray(mine[y0 - 463:y1 - 463, x0 - 457:x1 - 457], np.float64) / 65535.
    print(f'{lab}: compost rellegit − meu: abs mitjana {np.abs(C - M).mean():.2e} màx {np.abs(C - M).max():.2e}')
