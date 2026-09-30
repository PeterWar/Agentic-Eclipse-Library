"""CapesInteriorsV5.psb = el V4 editat de Pere amb NOMÉS les màscares de 04_1-2s i 03_1s substituïdes, i la merged recomposta.
Tota la resta (capes, màscares, ordre, noms, visibilitats) es conserva byte a byte via round-trip de psd-tools."""
import os, time, numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Compression, ChannelID, Tag
from psb_utils import set_merged
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:5.0f} s]', *a, flush=True)
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
OUT = D + 'CapesInteriorsV5.psb'
assert not os.path.exists(OUT), 'ja existeix'
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
layers = list(psd)
FRAME = (457, 463, 7417, 5103)
for idx, nm in ((10, '04'), (11, '03')):
    l = layers[idx]; rec = l._record; md = rec.mask_data
    W_m, H_m = md.right - md.left, md.bottom - md.top
    full = np.zeros((H_m, W_m), np.uint16)
    m = np.load(f'v5out/mask_{nm}.npy')
    full[FRAME[1] - md.top:FRAME[3] - md.top, FRAME[0] - md.left:FRAME[2] - md.left] = m
    # substitueix el canal de la màscara (mateixa posició del channel_info)
    for k, ci in enumerate(rec.channel_info):
        if ci.id == ChannelID.USER_LAYER_MASK:
            cd = l._channels[k]
            cd.compression = Compression.ZIP_WITH_PREDICTION
            cd.set_data(full.astype('>u2').tobytes(), W_m, H_m, hdr.depth, hdr.version)
            ci.length = len(cd.data) + 2
            log('màscara substituïda a', l.name[:30], 'bbox màscara', (md.left, md.top, md.right, md.bottom))
            break
merged = np.load('v5out/compost_rgb16.npy')
set_merged(psd, np.ascontiguousarray(merged), compression=Compression.RAW)
lm = psd._record.layer_and_mask_information
if lm.tagged_blocks is not None and Tag.SAVING_MERGED_TRANSPARENCY16 in lm.tagged_blocks:
    del lm.tagged_blocks[Tag.SAVING_MERGED_TRANSPARENCY16]; log('tret el bloc Mt16')
psd._record.header.channels = 3
psd._updated = False
psd.save(OUT)
log('desat', OUT, os.path.getsize(OUT) / 1e9, 'GB')
