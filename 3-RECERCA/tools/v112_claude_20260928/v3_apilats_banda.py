"""V112 (Claude): vista de banda (18–240 px) del canal G dels apilats per tren (Sony A, Sony B, Vixen) del flat 2D v5 (V108),
en coordenades del llenç. Desa L_sonyA.npy, L_sonyB.npy, L_vixen.npy (log − gaussiana σ40 blocs, σ3 blocs) i els suports."""
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; F = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
O = R / '4-RESULTATS/v112_claude_20260928/apilats_banda'; O.mkdir(parents=True, exist_ok=True)
B = 6; H, W = 7506, 10551; h, w = H // B, W // B
def banda(img, den, nom):
    # «total» ja és la imatge normalitzada (num/den, b2_v97.py); den només diu on hi ha dada
    g = np.where(den > 0, img, 0).astype(np.float64)
    gb = g[:h*B, :w*B].reshape(h, B, w, B).mean((1, 3))
    vb = (den[:h*B, :w*B] > 0).reshape(h, B, w, B).all((1, 3)) & (gb > 0)
    lg = np.where(vb, np.log(np.maximum(gb, 1e-9)), 0)
    # es treu el perfil radial (mediana per anell de 1 bloc) abans de la banda: si no, la corba del perfil ho domina tot
    yy, xx = np.mgrid[0:h, 0:w]; rb = np.round(np.hypot(xx*B + B/2 - 5375.79, yy*B + B/2 - 3775.98) / B).astype(int)
    prof = np.full(rb.max() + 1, np.nan)
    for k in np.unique(rb[vb]):
        m = vb & (rb == k)
        if m.sum() > 20: prof[k] = np.median(lg[m])
    ok = np.isfinite(prof); prof = np.interp(np.arange(prof.size), np.nonzero(ok)[0], prof[ok])
    lg = np.where(vb, lg - prof[rb], 0)
    num_ = ndi.gaussian_filter(lg, 40); d_ = ndi.gaussian_filter(vb.astype(float), 40)
    hp = np.where(vb, lg - num_ / np.maximum(d_, 1e-3), 0)
    n2 = ndi.gaussian_filter(hp, 3); d2 = ndi.gaussian_filter(vb.astype(float), 3)
    hp = np.where(vb, n2 / np.maximum(d2, 1e-3), np.nan).astype(np.float32)
    np.save(O / f'L_{nom}.npy', hp); np.save(O / f'val_{nom}.npy', vb); np.save(O / f'lin_{nom}.npy', np.where(vb, gb, np.nan).astype(np.float32))
    print(nom, 'cobertura', round(float(vb.mean()), 3), 'p99|banda|', float(np.nanpercentile(np.abs(hp), 99)))
A = np.load(F / 'sony_A_total.npy', mmap_mode='r'); Ad = np.load(F / 'sony_A_den.npy', mmap_mode='r')
banda(np.asarray(A[..., 1]), np.asarray(Ad), 'sonyA'); del A, Ad
Bt = np.load(F / 'cau/sony_B_total_v42.npy', mmap_mode='r'); Bw = np.load(R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy', mmap_mode='r')
banda(np.asarray(Bt[..., 1]), np.asarray(Bw[..., 1]), 'sonyB'); del Bt, Bw
V = np.load(F / 'vixen_total.npy', mmap_mode='r'); Vd = np.load(F / 'vixen_den.npy', mmap_mode='r')
banda(np.asarray(V[..., 1]), np.asarray(Vd), 'vixen')
