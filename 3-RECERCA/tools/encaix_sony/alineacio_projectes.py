"""Mesura d'alineació entre capes dels dos projectes de Pere (CapesInteriors.psb 6961×4641 i
CapesExteriors.psb 7648×5353) per correlació de fase d'un retall passa-alt de la corona, en
coordenades de document. Només lectura."""
import os, numpy as np, tifffile
from scipy import ndimage as ndi
from psd_tools import PSDImage

DI = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
DE = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/')
SP = os.path.dirname(os.path.abspath(__file__))
psdI = PSDImage.open(DI + 'CapesInteriors.psb')
psdE = PSDImage.open(DE + 'CapesExteriors.psb')
LI = {l.name: l for l in psdI}; LE = {l.name[:12]: l for l in psdE}
cache = {}
def lum(layer):
    key = id(layer)
    if key not in cache:
        a = layer.numpy()
        cache[key] = (a[..., :3].mean(-1).astype(np.float32), layer.bbox)
    return cache[key]

def patch(layer, x0, y0, s):
    """retall s×s del document (coordenades doc) de la luminància de la capa; NaN fora de la capa"""
    L, (lx0, ly0, lx1, ly1) = lum(layer)
    out = np.full((s, s), np.nan, np.float32)
    ix0, iy0, ix1, iy1 = max(x0, lx0), max(y0, ly0), min(x0 + s, lx1), min(y0 + s, ly1)
    if ix1 > ix0 and iy1 > iy0:
        out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = L[iy0 - ly0:iy1 - ly0, ix0 - lx0:ix1 - lx0]
    return out

def shift(a, b, tag):
    """desplaçament (dx, dy) de b respecte d'a per correlació de fase del passa-alt (subpíxel per centroide)"""
    m = np.isfinite(a) & np.isfinite(b)
    A = np.where(m, a, np.nanmedian(a)); B = np.where(m, b, np.nanmedian(b))
    A = A - ndi.gaussian_filter(A, 6); B = B - ndi.gaussian_filter(B, 6)
    A *= m; B *= m
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B)); F /= np.abs(F) + 1e-9
    pc = np.real(np.fft.ifft2(F))
    iy, ix = np.unravel_index(np.argmax(pc), pc.shape)
    dy = iy if iy <= pc.shape[0] // 2 else iy - pc.shape[0]; dx = ix if ix <= pc.shape[1] // 2 else ix - pc.shape[1]
    # subpíxel: centroide 3×3 al voltant del pic
    ys, xs = np.mgrid[-1:2, -1:2]
    w = np.array([[pc[(iy + i) % pc.shape[0], (ix + j) % pc.shape[1]] for j in (-1, 0, 1)] for i in (-1, 0, 1)])
    w = np.clip(w - w.min(), 0, None)
    sx = (w * xs).sum() / max(w.sum(), 1e-9); sy = (w * ys).sum() / max(w.sum(), 1e-9)
    print(f'  {tag:70s}: b està desplaçat (dx, dy) = ({dx + sx:+.2f}, {dy + sy:+.2f}) px respecte d\'a   (pic {pc.max():.3f})')
    return dx + sx, dy + sy

S = 1024
# Sol: a Exteriors, l'astromètric del llenç (3420,89+600, 2187,66+550); a Interiors, (3563,9+1, 2274,7+1) si raw = doc−1
sunE = (4020.9, 2737.7); sunI = (3564.9, 2275.7)
# retalls a ~2 R☉ a l'esquerra del Sol (corona, sense saturació a 1–2 s) i a dalt
offs = [(-1400, -512), (400, -1500), (-1400, 500)]
print('== CapesExteriors: capes de Pere entre elles (referència: 02_2s a (457,463))')
for (ox, oy) in offs:
    a = patch(LE['02_2s_572A29'], int(sunE[0] + ox), int(sunE[1] + oy), S)
    for nm in ('03_1s_572A29', '01_10.3s_572', 'EDITAT PERE:'):
        b = patch(LE[nm], int(sunE[0] + ox), int(sunE[1] + oy), S)
        shift(a, b, f'E: {nm} vs 02_2s @({ox},{oy})')
print('== CapesInteriors: capes entre elles (referència: 05_1-4s a (1,1))')
for (ox, oy) in offs:
    a = patch(LI['05_1-4s_572A2977_apilat2.dng'], int(sunI[0] + ox), int(sunI[1] + oy), S)
    for nm in ('03_1s_572A2978_apilat2.dng', '06_1-8s_572A2971_apilat4.dng', '10_1-125s_572A2969.CR3', '12_1-3200s_572A2956.CR3', 'Capa 1'):
        b = patch(LI[nm], int(sunI[0] + ox), int(sunI[1] + oy), S)
        shift(a, b, f'I: {nm} vs 05_1-4s @({ox},{oy})')
print('== Entre projectes: la mateixa capa 03_1s (I a (1,1); E rasteritzada a (456,462)) → desplaçament esperat 0 si Interiors + (456,462) = Exteriors')
for (ox, oy) in offs:
    a = patch(LE['03_1s_572A29'], int(sunE[0] + ox), int(sunE[1] + oy), S)
    b = patch(LI['03_1s_572A2978_apilat2.dng'], int(sunI[0] + ox), int(sunI[1] + oy), S)   # mateix punt del cel si I+(456,462)=E
    shift(a, b, f'03_1s: Interiors(+456,+462) vs Exteriors @({ox},{oy})')
print('== Capa 1 d\'Interiors contra el TIFF v4b (ESTESA) i contra EDITAT PERE d\'Exteriors')
tif = tifffile.imread(os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif')).astype(np.float32).mean(-1) / 65535
for (ox, oy) in offs:
    x0, y0 = int(sunE[0] + ox), int(sunE[1] + oy)
    a = tif[y0:y0 + S, x0:x0 + S]
    b = patch(LI['Capa 1'], x0 - 457, y0 - 463, S)   # Capa 1 està a (−457,−463) a Interiors: el seu píxel (x,y) = doc I (x−457, y−463)
    shift(a, b, f'Capa 1 (píxels propis) vs TIFF ESTESA @({ox},{oy})')
    c = patch(LE['EDITAT PERE:'], x0, y0, S)
    shift(a, c, f'EDITAT PERE (E) vs TIFF ESTESA @({ox},{oy})')
