"""Identifica cada capa del V4 editat comparant mostres de píxels amb les capes conegudes de V3 (tenint en compte desplaçaments 0/±1)."""
import numpy as np, json, glob
meta4 = json.load(open('v5in/meta.json')); meta3 = json.load(open('v3/meta.json'))
files3 = sorted(glob.glob('v3/*_rgb.npy')); files3 = [f for f in files3 if 'merged' not in f]
import os
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
rng = np.random.default_rng(42)
for i, l in enumerate(psd):
    rec = l._record; chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    l0, t0, r0, b0 = l.bbox; h, w = b0 - t0, r0 - l0
    G = np.frombuffer(chans[ChannelID(1)].get_data(w, h, hdr.depth, hdr.version), dtype='>u2').reshape(h, w)
    rng2 = np.random.default_rng(7); ys = rng2.integers(50, h - 50, 300); xs = rng2.integers(50, w - 50, 300)
    best = None
    for j, f in enumerate(files3):
        a = np.load(f, mmap_mode='r'); j0, jt = meta3['layers'][j]['bbox'][:2]; hh, ww = a.shape[:2]
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                # el píxel (ys,xs) de la capa i és al document (l0+xs, t0+ys); a la capa j: (l0+xs-j0+dx, t0+ys-jt+dy)
                yy = t0 + ys - jt + dy; xx = l0 + xs - j0 + dx
                ok = (yy >= 0) & (yy < hh) & (xx >= 0) & (xx < ww)
                if ok.sum() < 100: continue
                diff = np.abs(np.asarray(a[yy[ok], xx[ok], 1], np.int64) - G[ys[ok], xs[ok]]).mean()
                if best is None or diff < best[0]: best = (diff, meta3['layers'][j]['name'][:20], dx, dy)
    print(f'{i:2d} "{l.name[:40]:40s}" bbox=({l0},{t0}) vis={l.visible} → més a prop de {best[1]:22s} (dx,dy)=({best[2]},{best[3]}) diff mitjana {best[0]:.1f}', flush=True)
