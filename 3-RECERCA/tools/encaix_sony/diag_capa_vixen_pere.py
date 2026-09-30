"""Què fa la capa Vixen de Pere al camp llunyà més enllà d'una corba de to global?
LUT per canal (quantils) de la Vixen lineal (10,3 s, HDR4) → capa de Pere, ajustada a r > 3,6 fora de
les bandes de dalt (400) i dreta (500); quocient capa/LUT(lineal) a baixa freqüència. Desa
vixen_lineal_canvas_rgb.npy i vix_ref_rgb.npy (= LUT(lineal), la Vixen «sense enfosquiment»)."""
import os, numpy as np, rawpy
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
DNG = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/apilats/01_10.3s_572A2982_apilat3.dng')
with rawpy.imread(DNG) as rr:
    raw = rr.raw_image_visible.copy()
vl = (raw[..., :3].astype(np.float32) - 512.0)[87:4640, 143:6891]
np.save(os.path.join(SP, 'vixen_lineal_canvas_rgb.npy'), vl)
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy')).astype(np.float32)   # 0–1
r = np.load(os.path.join(SP, 'r_rsol.npy'))
H, W = r.shape
yy, xx = np.mgrid[0:H, 0:W]
trust = (yy >= 400) & (xx <= W - 1 - 500)
O = (r > 3.6) & trust
qs = np.linspace(0, 1, 2001)
ref = np.empty_like(vix)
for c in range(3):
    xs = np.quantile(vl[..., c][O], qs); ys = np.quantile(vix[..., c][O], qs)
    xs, idx = np.unique(xs, return_index=True); ys = ys[idx]
    ref[..., c] = np.interp(vl[..., c], xs, ys)
np.save(os.path.join(SP, 'vix_ref_rgb.npy'), ref.astype(np.float32))

def low(a, s=30):
    return ndi.gaussian_filter(a, s)
L = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
q = low(L(vix)) / np.maximum(low(L(ref)), 1e-6)
print('quocient capa Pere / LUT(Vixen lineal), luminància σ30:')
print('  files de dalt y=0..700 cada 50 (x 1000–6000):', [round(float(np.median(q[y, 1000:6000])), 3) for y in range(0, 701, 50)])
print('  columnes de la dreta x=W-1..W-800 cada 50 (y 800–3800):', [round(float(np.median(q[800:3800, W - 1 - x])), 3) for x in range(0, 801, 50)])
print('  files de baix:', [round(float(np.median(q[H - 1 - y, 1000:6000])), 3) for y in range(0, 401, 50)])
print('  columnes de l\'esquerra:', [round(float(np.median(q[800:3800, x])), 3) for x in range(0, 401, 50)])
for rr_ in (4, 5, 6, 7, 8, 8.8):
    mm = (np.abs(r - rr_) < 0.15) & trust
    print(f'  r={rr_}: mediana {np.median(q[mm]):.3f} p10 {np.percentile(q[mm],10):.3f} p90 {np.percentile(q[mm],90):.3f}')
for tag, (y, x) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W - 150)), ('baix-esq', (H - 150, 150)), ('baix-dreta', (H - 150, W - 150))):
    print(f'  canto {tag}: {np.median(q[y-100:y+100, x-100:x+100]):.3f}')
# per canal, als cantons de baix-esquerra i dalt-dreta
for c, nom in enumerate('RGB'):
    qc = low(vix[..., c]) / np.maximum(low(ref[..., c]), 1e-6)
    print(f'  canal {nom}: baix-esq {np.median(qc[H-250:H-50, 50:250]):.3f}  dalt-dreta {np.median(qc[50:250, W-250:W-50]):.3f}  centre-esq {np.median(qc[2100:2300, 200:400]):.3f}  r 4–5 {np.median(qc[(r>4)&(r<5)&trust]):.3f}')
v = np.clip((q - 0.5) / 1.0, 0, 1); v[r < 3.4] = 0.5
Image.fromarray((v[::4, ::4] * 255).astype(np.uint8)).save(os.path.join(SP, 'diag_capa_vixen_pere.png'))
print('PNG: quocient 0,5–1,5')
