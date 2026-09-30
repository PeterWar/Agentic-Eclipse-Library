import numpy as np, os
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriors.psb'); hdr = psd._record.header
def read_rgb(l):
    rec = l._record; l0, t0, r0, b0 = l.bbox; h, w = b0 - t0, r0 - l0
    chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    return np.stack([np.frombuffer(chans[ChannelID(c)].get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w) for c in range(3)], -1), (l0, t0)
orig = {l.name[:2]: l for l in psd}
c4 = np.load('v3/01_Capa_4_rgb.npy', mmap_mode='r'); c5 = np.load('v3/02_Capa_5_rgb.npy', mmap_mode='r')
# finestra de prova al voltant del Sol (coordenades de document V3)
y0, y1, x0, x1 = 2200, 3300, 3400, 4700
for key, cand in (('11', c4), ('10', c5)):
    a, (l0, t0) = read_rgb(orig[key])
    print(key, orig[key].name, 'bbox', orig[key].bbox)
    best = None
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            # capa original a (l0,t0) en coords del document original; V3 té les capes 1 px més avall/dreta
            sub = a[y0 - t0 + dy:y1 - t0 + dy, x0 - l0 + dx:x1 - l0 + dx].astype(np.float32)
            ref = np.asarray(cand[y0:y1, x0:x1], np.float32)
            diff = np.abs(sub - ref).mean()
            if best is None or diff < best[0]: best = (diff, dx, dy)
    print('   millor coincidència: diff mitjana', best[0], 'a desplaçament (dx,dy)=', best[1:], ' (0 = mateixa posició de document que la capa vella)')
    sub = a[y0 - t0 + best[2]:y1 - t0 + best[2], x0 - l0 + best[1]:x1 - l0 + best[1]].astype(np.float32)
    ref = np.asarray(cand[y0:y1, x0:x1], np.float32)
    m = ref[..., 1] > 2000
    print('   quocient mediana (V3/original) per canal on G>2000:', [float(np.median(ref[..., c][m] / np.maximum(sub[..., c][m], 1))) for c in range(3)], ' píxels idèntics:', float((sub == ref).all(-1).mean()))
