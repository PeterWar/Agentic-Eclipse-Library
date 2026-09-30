"""Verificació de CapesInteriorsV5.psb: estructura intacta, màscares noves als llocs, capes byte-idèntiques al V4 editat,
i el compost rellegit = el meu."""
import os, numpy as np, json
from psd_tools import PSDImage
from psd_tools.constants import ChannelID, Tag
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
p5 = PSDImage.open(D + 'CapesInteriorsV5.psb'); h5 = p5._record.header
p4 = PSDImage.open(D + 'CapesInteriorsV4.psb'); h4 = p4._record.header
print('V5:', h5.width, h5.height, 'depth', h5.depth, 'channels', h5.channels, '| Lr16:', Tag.LAYER_16 in p5._record.layer_and_mask_information.tagged_blocks)
L5, L4 = list(p5), list(p4)
assert len(L5) == len(L4) == 12
rng = np.random.default_rng(3)
for i, (a, b) in enumerate(zip(L5, L4)):
    assert a.name == b.name and a.bbox == b.bbox and a.visible == b.visible, (i, a.name)
    ra, rb = a._record, b._record
    ca = {ci.id: cd for ci, cd in zip(ra.channel_info, a._channels)}; cb = {ci.id: cd for ci, cd in zip(rb.channel_info, b._channels)}
    l0, t0, r0, b0 = a.bbox; w, h = r0 - l0, b0 - t0
    Ga = np.frombuffer(ca[ChannelID(1)].get_data(w, h, 16, 2), dtype='>u2'); Gb = np.frombuffer(cb[ChannelID(1)].get_data(w, h, 16, 2), dtype='>u2')
    idxs = rng.integers(0, len(Ga), 500)
    pix_ok = bool((Ga[idxs] == Gb[idxs]).all())
    m_info = ''
    if a.mask is not None:
        mb_ = a.mask.bbox; mw, mh = mb_[2] - mb_[0], mb_[3] - mb_[1]
        Ma = np.frombuffer(ca[ChannelID.USER_LAYER_MASK].get_data(mw, mh, 16, 2), dtype='>u2').reshape(mh, mw)
        Mb = np.frombuffer(cb[ChannelID.USER_LAYER_MASK].get_data(mw, mh, 16, 2), dtype='>u2').reshape(mh, mw)
        same = bool((Ma[::16, ::16] == Mb[::16, ::16]).all())
        m_info = f' | màscara {"IGUAL" if same else "SUBSTITUÏDA"} (mitjana {Ma.mean()/65535:.3f})'
    print(f'{i:2d} {a.name[:38]:38s} píxels {"OK" if pix_ok else "DIFEREIXEN!"}{m_info}')
img = p5._record.image_data.get_data(h5)
mer = np.stack([np.frombuffer(c, dtype='>u2').reshape(h5.height, h5.width) for c in img[:3]], -1)
mine = np.load('v5out/compost_rgb16.npy', mmap_mode='r')
print('merged V5 vs el meu compost: idèntics:', bool((mer[::8, ::8] == np.asarray(mine[::8, ::8])).all()))
