"""f0 · Prova ràpida (blocs 4×4, canal G) de la cura a la fusió: a la Sony A, les escales mitjanes (DoG σ 25 → 500 px) es prenen de la B
al solapament, ln A' = ln A − BP[ln A_g − ln B]. Compara la vista de banda de la Sony fusionada abans/després. Dades: la fusió de control V98."""
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; V98 = R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau'
O = R / '4-RESULTATS/v112_claude_20260928/prova_fusio'; O.mkdir(parents=True, exist_ok=True)
B_ = 4; H, W = 7506, 10551; h, w = H // B_, W // B_
def binq(a): return np.asarray(a[:h*B_, :w*B_], np.float64).reshape(h, B_, w, B_).mean((1, 3))
Ag = binq(np.load(V98 / 'sony_A_corr_v42.npy', mmap_mode='r')[..., 1])
Bb = binq(np.load(R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', mmap_mode='r')[..., 1])
S = binq(np.load(V98 / 'sony_corrected_total_v42.npy', mmap_mode='r')[..., 1])
fA = binq(np.load(V98 / 'sony_fA_v42.npy', mmap_mode='r'))
st = binq(np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/fusio/d4/products/sources/star_footprints.npy', mmap_mode='r').astype(np.float32)) > 0
yy, xx = np.mgrid[0:h, 0:w]; X = xx * B_ + 2; Y = yy * B_ + 2
rsun = np.hypot(X - 5375.8, Y - 3776.0) / 453.0
ov = (Ag > 0) & (Bb > 0) & np.isfinite(Ag) & np.isfinite(Bb)
use = ov & ~ndi.binary_dilation(st, iterations=2) & (np.hypot(X - 4853, Y - 2531) > 260) & (rsun > 2.5)
dlog = np.where(use, np.log(np.maximum(Ag, 1e-9)) - np.log(np.maximum(Bb, 1e-9)), 0)
def ng(a, m, s): return ndi.gaussian_filter(a * m, s) / np.maximum(ndi.gaussian_filter(m.astype(float), s), 1e-6)
C = ng(dlog, use, 25 / B_) - ng(dlog, use, 500 / B_)
# afebliment: cap a 0 on el solapament s'acaba (distància dins del solapament 0 → 800 px) i prop del Sol (r 3 → 4 R)
dov = ndi.distance_transform_edt(ov) * B_
tap = np.clip(dov / 800, 0, 1) * np.clip(rsun - 3, 0, 1)
tap = ndi.gaussian_filter(tap, 50 / B_)
C = np.where(ov, C * tap, 0)
S2 = np.where(ov, S - fA * Ag * (1 - np.exp(-C)), S)
np.save(O / 'C_bin4.npy', C.astype(np.float32)); np.save(O / 'S_bin4.npy', S.astype(np.float32)); np.save(O / 'S2_bin4.npy', S2.astype(np.float32))
print('C p1/p50/p99 al solapament', np.percentile(C[ov], [1, 50, 99]))
