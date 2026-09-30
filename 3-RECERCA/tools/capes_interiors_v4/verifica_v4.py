"""Rellegeix CapesInteriorsV4.psb i comprova: estructura, màscares 16 bits, compost reproduït vs el meu, fusionada."""
import os, numpy as np, json
from psd_tools import PSDImage
from psd_tools.constants import ChannelID, Tag
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
print('capçalera', hdr.width, hdr.height, 'depth', hdr.depth, 'channels', hdr.channels, 'version', hdr.version, 'mode', hdr.color_mode)
lm = psd._record.layer_and_mask_information
print('Lr16 present:', lm.tagged_blocks is not None and Tag.LAYER_16 in lm.tagged_blocks, '; capes a la secció clàssica:', lm.layer_info.layer_count if lm.layer_info else None)
layers = list(psd)
for l in layers:
    m = l.mask; rec = l._record
    chans = {ci.id: (ci, cd) for ci, cd in zip(rec.channel_info, l._channels)}
    mi = ''
    if m is not None:
        ci, cd = chans[ChannelID.USER_LAYER_MASK]; mw, mh = m.bbox[2] - m.bbox[0], m.bbox[3] - m.bbox[1]
        raw = cd.get_data(mw, mh, hdr.depth, hdr.version); bits = 16 if len(raw) == mw * mh * 2 else 8
        arr = np.frombuffer(raw, dtype='>u2').reshape(mh, mw) if bits == 16 else None
        mi = f' | màscara bbox={m.bbox} {bits} bits, min {arr.min()} max {arr.max()} mitjana {arr.mean()/65535:.3f}'
    print(f'[{l.kind}] "{l.name[:58]}" bbox={l.bbox} blend={l.blend_mode.name} op={l.opacity} vis={l.visible}{mi}')
# compost reproduït en una finestra i comparat amb el meu compost_gain
y0, y1, x0, x1 = 2300, 3200, 3500, 4600
C = np.zeros((y1 - y0, x1 - x0, 3), np.float64)
def read_rgb_win(l):
    rec = l._record; L0, T0, R0, B0 = l.bbox; h, w = B0 - T0, R0 - L0
    chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    out = np.zeros((y1 - y0, x1 - x0, 3)); 
    for c in range(3):
        full = np.frombuffer(chans[ChannelID(c)].get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w)
        out[..., c] = full[y0 - T0:y1 - T0, x0 - L0:x1 - L0] / 65535.
    return out
def read_mask_win(l):
    m = l.mask; rec = l._record; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    L0, T0, R0, B0 = m.bbox; w, h = R0 - L0, B0 - T0
    full = np.frombuffer(chans[ChannelID.USER_LAYER_MASK].get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w)
    return full[y0 - T0:y1 - T0, x0 - L0:x1 - L0] / 65535.
for l in layers:
    if not l.visible: continue
    if l.blend_mode.name == 'COLOR_DODGE':
        L0, T0, R0, B0 = l.bbox
        V = np.zeros((y1 - y0, x1 - x0)); rec = l._record; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
        full = np.frombuffer(chans[ChannelID(0)].get_data(R0 - L0, B0 - T0, hdr.depth, hdr.version), dtype='>u2').reshape(B0 - T0, R0 - L0) / 65535.
        ys0, ys1 = max(y0, T0), min(y1, B0); xs0, xs1 = max(x0, L0), min(x1, R0)
        V[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] = full[ys0 - T0:ys1 - T0, xs0 - L0:xs1 - L0]
        C = np.clip(C / np.maximum(1 - V[..., None], 1e-6), 0, 1)
        continue
    rgb = read_rgb_win(l); a = read_mask_win(l)[..., None] if l.mask is not None else 1.0
    C = C * (1 - a) + rgb * a
mine = np.load('v4/compost_gain_rgb16.npy', mmap_mode='r')
M = np.asarray(mine[y0 - 463:y1 - 463, x0 - 457:x1 - 457], np.float64) / 65535.
print('compost rellegit − meu: abs mitjana', np.abs(C - M).mean(), 'màx', np.abs(C - M).max())
img = psd._record.image_data.get_data(hdr)
mer = np.stack([np.frombuffer(c, dtype='>u2').reshape(hdr.height, hdr.width) for c in img[:3]], -1)
print('fusionada: canals', len(img), 'finestra vs meu:', np.abs(mer[y0:y1, x0:x1] / 65535. - M).max())
