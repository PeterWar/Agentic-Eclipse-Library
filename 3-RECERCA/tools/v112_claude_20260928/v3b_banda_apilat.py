"""v3b · vista de banda (perfil radial solar tret, 18–240 px) del canal G d'un apilat qualsevol. Ús: v3b_banda_apilat.py APILAT.npy DEN.npy NOM"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v112_claude_20260928/apilats_banda'
B = 6; H, W = 7506, 10551; h, w = H // B, W // B
img = np.load(sys.argv[1], mmap_mode='r'); den = np.load(sys.argv[2], mmap_mode='r'); nom = sys.argv[3]
g = np.asarray(img[..., 1], np.float64); d = np.asarray(den if den.ndim == 2 else den[..., 1])
g = np.where(d > 0, g, 0)
gb = g[:h*B, :w*B].reshape(h, B, w, B).mean((1, 3)); vb = (d[:h*B, :w*B] > 0).reshape(h, B, w, B).all((1, 3)) & (gb > 0)
lg = np.where(vb, np.log(np.maximum(gb, 1e-9)), 0)
yy, xx = np.mgrid[0:h, 0:w]; rb = np.round(np.hypot(xx*B + B/2 - 5375.79, yy*B + B/2 - 3775.98) / B).astype(int)
prof = np.full(rb.max() + 1, np.nan)
for k in np.unique(rb[vb]):
    m = vb & (rb == k)
    if m.sum() > 20: prof[k] = np.median(lg[m])
ok = np.isfinite(prof); prof = np.interp(np.arange(prof.size), np.nonzero(ok)[0], prof[ok]); lg = np.where(vb, lg - prof[rb], 0)
n = ndi.gaussian_filter(lg, 40); dd = ndi.gaussian_filter(vb.astype(float), 40); hp = np.where(vb, lg - n / np.maximum(dd, 1e-3), 0)
n2 = ndi.gaussian_filter(hp, 3); d2 = ndi.gaussian_filter(vb.astype(float), 3)
np.save(O / f'L_{nom}.npy', np.where(vb, n2 / np.maximum(d2, 1e-3), np.nan).astype(np.float32)); print('fet', nom)
