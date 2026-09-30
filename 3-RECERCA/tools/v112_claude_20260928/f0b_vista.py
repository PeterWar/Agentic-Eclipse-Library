"""f0b · vista de banda (perfil radial solar tret, σ 18–240 px) de dues imatges en blocs 4×4 i retalls costat a costat amb les marques."""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v112_claude_20260928/prova_fusio'
B_ = 4; H, W = 7506, 10551; h, w = H // B_, W // B_
yy, xx = np.mgrid[0:h, 0:w]; X = xx * B_ + 2; Y = yy * B_ + 2
rb = np.round(np.hypot(X - 5375.8, Y - 3776.0) / B_).astype(int)
def banda(a):
    v = np.isfinite(a) & (a > 0); lg = np.where(v, np.log(np.maximum(a, 1e-9)), 0)
    prof = ndi.median(lg, labels=np.where(v, rb + 1, 0), index=np.arange(1, rb.max() + 2))
    prof = np.nan_to_num(np.asarray(prof)); lg = np.where(v, lg - prof[rb], 0)
    n = ndi.gaussian_filter(lg, 60); d = ndi.gaussian_filter(v.astype(float), 60); hp = np.where(v, lg - n / np.maximum(d, 1e-3), 0)
    n2 = ndi.gaussian_filter(hp, 4.5); d2 = ndi.gaussian_filter(v.astype(float), 4.5)
    return np.where(v, n2 / np.maximum(d2, 1e-3), np.nan)
A = banda(np.load(O / sys.argv[1])); Bb = banda(np.load(O / sys.argv[2]))
mq = np.load(R / '4-RESULTATS/v112_20260928/marques412.npz'); al = mq['alpha'] > 0; org = mq['origin']
full = np.zeros((H, W), bool); full[org[1]:org[1] + al.shape[0], org[0]:org[0] + al.shape[1]] = al
mb = full[:h*B_, :w*B_].reshape(h, B_, w, B_).any((1, 3)); vora = mb & ~ndi.binary_erosion(mb, iterations=1)
s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.003
for nom, (x0, y0, x1, y1) in {'dalt': (4200, 0, 7600, 2400), 'dreta': (7800, 1800, 10551, 4600), 'tot': (0, 0, 10551, 7506)}.items():
    cols = []
    for a in (A, Bb):
        c = a[y0 // B_:y1 // B_, x0 // B_:x1 // B_]
        g = np.clip((np.nan_to_num(c) / s + 1) * 127.5, 0, 255).astype(np.uint8); g[~np.isfinite(c)] = 0
        rgb = np.stack([g] * 3, -1); rgb[vora[y0 // B_:y1 // B_, x0 // B_:x1 // B_]] = (255, 0, 255); cols += [rgb, np.full((rgb.shape[0], 4, 3), 255, np.uint8)]
    im = Image.fromarray(np.concatenate(cols[:-1], 1)); z = min(1.0, 1990 / im.width); im = im.resize((int(im.width * z), int(im.height * z)), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), f'{sys.argv[1]} | {sys.argv[2]}  ±{s}', fill=(255, 255, 0)); im.save(R / f'4-RESULTATS/v112_claude_20260928/vistes/prova_fusio_{nom}.png')
print('fet')
