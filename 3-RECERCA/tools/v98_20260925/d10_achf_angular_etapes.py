"""d10 (V98) · On neix el vorell fosc dels ACHF azimutals (47–49) arran del limbe a baix (240–330°)? Refà l'etapa E4 de f3_filtres_v98 per
a la Vixen (a la caixa el pes de la Vixen és 1) i en dona el perfil per distància al limbe a cada pas: ln V, pas alt a l'arc (ordre 1),
suavitzat radial r8, /escala, tanh, sn_smooth, centre_rings."""
import sys, os, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('V97_SORT', str(ARREL / '4-RESULTATS/v98_20260925/_scratch_d10'))
from v97_comu import *
from v86_operadors import sn_smooth, centre_rings, back
from angular_polar1 import angular_polar1
from scipy.ndimage import gaussian_filter1d
R = ARREL / '4-RESULTATS/v98_20260925'; Q = np.load(R / 'lineal_v98_franja/A3B_franja_neta.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
V85D = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
mv = np.load(V85D / 'sources_v29/vixen_support.npy'); z4 = np.load(V85D / 's4_baseline/cau/s4_recomposicio_box.npz'); y0, y1, x0, x1 = z4['box'].astype(int); mv[y0:y1, x0:x1] |= np.load(V85D / 's4_baseline/cau/s4_support_new_box.npy')
V = np.array(np.load(R / 'lineal_v98/vixen_starless.npy', mmap_mode='r')[..., 1]); mv[BOXQ] = Q['domini']; m = mv & np.isfinite(V) & (V > 0)
r, t = coords()
p_, valid, r0, nt = angular_polar1(np.log(np.maximum(V, 1e-8)), m, r, t, CX, CY)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
bx = (slice(3900, 4300), slice(5300, 5900)); yy, xx = np.mgrid[3900:4300, 5300:5900]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
sec = (th >= 250) & (th < 320) & m[bx]
def prof(img, nom):
    v = img[bx]; print(f'{nom:22s}', ' '.join(f'{np.median(v[sec & (d >= k) & (d < k + 1)]):+.4f}' for k in range(0, 16)), flush=True)
lnV = np.log(np.maximum(V, 1e-8)); prof(lnV - np.median(lnV[bx][sec]), 'ln V (relatiu)')
hp0 = back(p_, m, r, t, r0, nt); prof(hp0, 'pas alt arc r0')
q8 = gaussian_filter1d(p_ * valid, 8, axis=0, mode='constant', cval=0) / np.maximum(gaussian_filter1d(valid, 8, axis=0, mode='constant', cval=0), 1e-8); hp8 = back(q8, m, r, t, r0, nt); prof(hp8, 'pas alt arc r8')
old = json.loads((ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v29_profiles_round1/cau/gran_azimuthal_receipt.json').read_text()); pr = old['post_contrast_profiles']['vixen']
scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), pr['lnr_centres'], pr['robust_contrast']).astype('float32')
dd = np.where(m, hp0 / np.maximum(scale, .002), 0).astype('float32'); mapped = (.5 * np.tanh(dd / old['scale_tanh'])).astype('float32'); prof(mapped, 'mapat (tanh) r0')
sigmamap = np.load(ARREL / '4-RESULTATS/v85_regeneracio_20260922/fixed_inputs/resolution_sigma.npy', mmap_mode='r'); prof(np.asarray(sigmamap), 'sigmamap (px)')
sm = sn_smooth(mapped, m, sigmamap); prof(sm, 'sn_smooth r0')
cen, hist = centre_rings(sm, m, r); prof(cen, 'centre_rings r0')
