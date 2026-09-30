"""Prova de consistència: apilat Sony aplanat (lineal, llenç) contra l'apilat lineal de 10,3 s de la
Vixen (HDR4, DNG LinearRaw, reixa 6960×4640 → llenç [87:4640, 143:6891]). Quocient a baixa freqüència
sobre el camp llunyà: si el flat és bo, el quocient és llis i només hi queda el vinyetatge de la Vixen
(radial) i les diferències de cel."""
import os, numpy as np, rawpy
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
DNG = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/apilats/01_10.3s_572A2982_apilat3.dng')
with rawpy.imread(DNG) as r:
    raw = r.raw_image_visible.copy()
    print('DNG: forma', raw.shape, raw.dtype, 'black', r.black_level_per_channel, 'white', r.white_level, 'colors', r.num_colors)
    try:
        cols = r.raw_colors_visible.copy(); print('  raw_colors únics', np.unique(cols)[:8])
    except Exception as e:
        cols = None; print('  sense raw_colors:', e)
if raw.ndim == 3:
    vixl = raw[..., :3].astype(np.float32) - 512.0
else:
    # Bayer: plans per convolució normalitzada senzilla (mitjana 2×2 → mitja resolució → zoom)
    Hh, Ww = raw.shape
    vixl = np.zeros((Hh, Ww, 3), np.float32)
    for c, ks in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        m = np.isin(cols, ks).astype(np.float32)
        num = ndi.gaussian_filter((raw.astype(np.float32) - 512.0) * m, 1.0); den = ndi.gaussian_filter(m, 1.0)
        vixl[..., c] = num / np.maximum(den, 1e-6)
vixl = vixl[87:4640, 143:6891]
print('Vixen lineal al llenç:', vixl.shape, ' mediana per canal', np.median(vixl.reshape(-1, 3), axis=0))

sony_raw = np.load(os.path.join(SP, 'sony_stack_ext_rgb.npy'), mmap_mode='r')[sl]
sony_flat = np.load(os.path.join(SP, 'sony_stack_ext_rgb_FLAT.npy'), mmap_mode='r')[sl]
cov = np.load(os.path.join(SP, 'sony_stack_ext_cov.npy'))[sl]
r = np.load(os.path.join(SP, 'r_rsol.npy'))
Hc, Wc = r.shape

def low(a, m, s=60):
    num = ndi.gaussian_filter(np.where(m, a, 0.0), s); den = ndi.gaussian_filter(m.astype(np.float32), s)
    return np.where(den > 0.05, num / np.maximum(den, 1e-6), np.nan)

m = cov & (r > 3.8) & np.isfinite(np.asarray(sony_raw)).all(-1)
res = {}
for nom, sny in (('sense flat', sony_raw), ('amb flat', sony_flat)):
    G = np.asarray(sny[..., 1]).astype(np.float32); V = vixl[..., 1]
    q = low(G, m) / np.maximum(low(V, m), 1e-3)
    qn = q / np.nanmedian(q[(r > 4) & (r < 5)])
    res[nom] = qn
    print(f'== {nom}: quocient Sony/Vixen (verd, σ60, normalitzat a 4–5 R☉)')
    for rr in (4.0, 5.0, 6.0, 7.0, 8.0, 8.8):
        mm = np.abs(r - rr) < 0.15
        print(f'   r={rr}: mediana {np.nanmedian(qn[mm]):.3f}  p10 {np.nanpercentile(qn[mm], 10):.3f}  p90 {np.nanpercentile(qn[mm], 90):.3f}')
    for tag, (y, x) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, Wc - 150)), ('baix-esq', (Hc - 150, 150)), ('baix-dreta', (Hc - 150, Wc - 150)),
                        ('dalt', (150, Wc // 2)), ('baix', (Hc - 150, Wc // 2)), ('esq', (Hc // 2, 150)), ('dreta', (Hc // 2, Wc - 150))):
        print(f'   {tag:11s} q={np.nanmedian(qn[y-100:y+100, x-100:x+100]):.3f}')
def to8(a, lo, hi):
    v = np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1); v[r < 3.5] = 0.5
    return (v[::4, ::4] * 255).astype(np.uint8)
Image.fromarray(np.concatenate([to8(res['sense flat'], 0.6, 1.4), to8(res['amb flat'], 0.6, 1.4)], 1)).save(os.path.join(SP, 'test_flat_vs_vixen.png'))
print('PNG: quocient sense flat | amb flat (0,6–1,4)')
np.save(os.path.join(SP, 'vixen_lineal_10s_canvas_G.npy'), vixl[..., 1].astype(np.float32))
