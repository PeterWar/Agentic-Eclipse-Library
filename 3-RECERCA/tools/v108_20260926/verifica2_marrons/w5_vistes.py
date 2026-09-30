"""w5 (verificador adversari 2) · Vistes pròpies del LLENÇ SENCER (a 1/4) per buscar anells, línies, costures, discos i canvis de color.
  1 · base_G: després/abans − 1 suavitzat σ6 (±0,15 %) — escala mitjana, on es veurien anells, discos de pols i línies.
  2 · base_G: després/abans − 1 suavitzat σ40 (±0,04 %) — gran escala (nivell).
  3 · color de fusion_starless: Δ ln(R/G) i Δ ln(B/G) suavitzats σ20 (±0,1 %).
  4 · compost: després/abans − 1 suavitzat σ6 (±0,6 %).
  5 · apilat Vixen G: després/abans − 1 suavitzat σ3 (±0,5 %).   6 · apilat Sony A G i 7 · Sony B G: σ3 (±0,15 %).
Sortida: W5_VISTA_<n>_*.png (blau = més fosc després, vermell = més clar)."""
import sys
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
quins = sys.argv[1:] or list('1234567')
def ld(p, ch=None):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def ratio(pa, pb, ch, s):
    a = ld(pa, ch); b = ld(pb, ch); m = ((a > 0) & (b > 0) & np.isfinite(a) & np.isfinite(b)).astype(np.float32)
    l = np.where(m > 0, np.log(np.maximum(b, 1e-12)) - np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); del a, b
    g = cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    return np.where(m > 0, g, np.nan)[::4, ::4]
def pinta(x, lim, nom, tit):
    fig = plt.figure(figsize=(x.shape[1] / 100, x.shape[0] / 100 + 0.4), dpi=100); ax = fig.add_axes([0, 0, 1, x.shape[0] / (x.shape[0] + 40)])
    cm = plt.get_cmap('bwr').copy(); cm.set_bad('0.85'); ax.imshow(x, cmap=cm, vmin=-lim, vmax=lim, interpolation='nearest'); ax.axis('off')
    fig.text(0.005, 0.995, tit, va='top', fontsize=14); fig.savefig(OUT / f'W5_VISTA_{nom}.png'); plt.close(fig); print('FET', nom, flush=True)
if '1' in quins: pinta(ratio(CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy', None, 6), 0.0015, '1_base_sigma6', 'base_G · ln(després/abans) σ6 · ±0,15 % · llenç sencer a 1/4')
if '2' in quins: pinta(ratio(CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy', None, 40), 0.0004, '2_base_sigma40', 'base_G · ln(després/abans) σ40 · ±0,04 % · llenç sencer a 1/4')
if '3' in quins:
    a = np.load(CAD / 'control/lineal/fusion_starless.npy', mmap_mode='r'); b = np.load(CAD / 'flat2d_v2/lineal/fusion_starless.npy', mmap_mode='r')
    for nm, c in (('RG', 0), ('BG', 2)):
        xa = np.asarray(a[..., c], np.float32) / np.maximum(np.asarray(a[..., 1], np.float32), 1e-12); xb = np.asarray(b[..., c], np.float32) / np.maximum(np.asarray(b[..., 1], np.float32), 1e-12)
        m = ((xa > 0) & (xb > 0) & np.isfinite(xa) & np.isfinite(xb) & (np.asarray(a[..., 1]) > 0)).astype(np.float32)
        l = np.where(m > 0, np.log(np.maximum(xb, 1e-12)) - np.log(np.maximum(xa, 1e-12)), 0).astype(np.float32); del xa, xb
        g = cv2.GaussianBlur(l * m, (0, 0), 20) / np.maximum(cv2.GaussianBlur(m, (0, 0), 20), 1e-6)
        pinta(np.where(m > 0, g, np.nan)[::4, ::4], 0.001, f'3_color_{nm}_sigma20', f'fusion_starless · Δ ln({nm[0]}/{nm[1]}) σ20 · ±0,1 % · llenç sencer a 1/4'); del l, g, m
if '4' in quins: pinta(ratio(F2 / 'compost_control.npy', F2 / 'compost_flat2d_v2.npy', None, 6), 0.006, '4_compost_sigma6', 'compost (màscares V107) · ln(després/abans) σ6 · ±0,6 % · llenç sencer a 1/4')
if '5' in quins: pinta(ratio(CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', F2 / 'apilats/vixen_total.npy', 1, 3), 0.005, '5_vixen_sigma3', 'apilat Vixen G · ln(després/abans) σ3 · ±0,5 % · llenç sencer a 1/4')
if '6' in quins: pinta(ratio(CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', F2 / 'apilats/sony_A_total.npy', 1, 3), 0.0015, '6_sonyA_sigma3', 'apilat Sony A G · ln(després/abans) σ3 · ±0,15 % · llenç sencer a 1/4')
if '7' in quins: pinta(ratio(CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', F2 / 'apilats/cau/sony_B_total_v42.npy', 1, 3), 0.0015, '7_sonyB_sigma3', 'apilat Sony B G · ln(després/abans) σ3 · ±0,15 % · llenç sencer a 1/4')
