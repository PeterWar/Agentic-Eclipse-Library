import rawpy, numpy as np
from functools import lru_cache

BASE="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
PED=512.0
SCALE=3.234  # arcsec/px full-res

@lru_cache(maxsize=4)
def planes(name):
    """Return dict of Bayer planes (half-res each) in float64, pedestal removed.
    Pattern RGGB: R at (0,0), G1 at (0,1), G2 at (1,0), B at (1,1)."""
    with rawpy.imread(BASE+name) as r:
        raw=r.raw_image_visible.astype(np.float64)-PED
        col=r.raw_colors_visible
    out={}
    out['R']=raw[0::2,0::2]
    out['G1']=raw[0::2,1::2]
    out['G2']=raw[1::2,0::2]
    out['B']=raw[1::2,1::2]
    # sanity on colors
    assert col[0,0]==0 and col[0,1]==1 and col[1,1]==2
    return out

def plane(name, ch='G1'):
    return planes(name)[ch]
