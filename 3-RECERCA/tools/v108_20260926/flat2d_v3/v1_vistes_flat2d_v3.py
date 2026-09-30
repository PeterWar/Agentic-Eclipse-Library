"""v1_vistes_flat2d_v3 (V108, flat2d_v3) · VISTES DEL LLENÇ SENCER (a 1/4), abans/després, a la lluminància i al color. Cada vista porta DOS panells
amb la mateixa escala: esquerra = v3 respecte del control (la V107), dreta = v2 respecte del control (el que el verificador va trobar).
  1 · base_G, ln(després/abans) σ6, ±0,15 %            2 · base_G σ40, ±0,04 % (nivell)
  3 · color: Δ ln(R/G) de fusion_starless σ20, ±0,1 %   4 · Δ ln(B/G) σ20, ±0,1 %
  5 · compost (màscares de la V107) σ6, ±0,6 %          6 · apilats (Vixen σ3 ±0,5 %; Sony A i B σ3 ±0,15 %): v3 | v2
  7 · ABANS i DESPRÉS de la imatge mateixa: el compost en contrast fi (σ4/σ40, ±3 %), control | v3
  8 · ABANS i DESPRÉS del color mateix: ln(R/G) de fusion_starless en banda σ20–200 (±0,3 %), control | v3 (els anells i les bandes de la v2
      s'hi veurien com a estructura nova)
Gris = sense dada. Blau = més fosc (o menys vermell) després.   Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/VISTA_<n>_*.png
Ús: v1_vistes_flat2d_v3.py [1..8]"""
import sys
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v3'
CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'
quins = sys.argv[1:] or list('12345678')
AP = {'control': dict(vixen=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', sony_A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', sony_B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v2': dict(vixen=F2 / 'apilats/vixen_total.npy', sony_A=F2 / 'apilats/sony_A_total.npy', sony_B=F2 / 'apilats/cau/sony_B_total_v42.npy'),
      'v3': dict(vixen=OUT / 'apilats/vixen_total.npy', sony_A=OUT / 'apilats/sony_A_total.npy', sony_B=OUT / 'apilats/cau/sony_B_total_v42.npy')}
CMP = {'control': F2 / 'compost_control.npy', 'v2': F2 / 'compost_flat2d_v2.npy', 'v3': OUT / 'compost_flat2d_v3.npy'}
CADV = {'control': CAD / 'control', 'v2': CAD / 'flat2d_v2', 'v3': CAD / 'flat2d_v3'}
def ld(p, ch=None):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def ratio(pa, pb, ch, s):
    a = ld(pa, ch); b = ld(pb, ch); m = ((a > 0) & (b > 0) & np.isfinite(a) & np.isfinite(b)).astype(np.float32)
    l = np.where(m > 0, np.log(np.maximum(b, 1e-12)) - np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); del a, b
    g = cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    return np.where(m > 0, g, np.nan)[::4, ::4]
def croma(p, c):
    f = np.load(p, mmap_mode='r'); x = np.asarray(f[..., c], np.float32); g = np.asarray(f[..., 1], np.float32)
    m = ((x > 0) & (g > 0) & np.isfinite(x) & np.isfinite(g)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(x, 1e-12) / np.maximum(g, 1e-12)), 0).astype(np.float32), m
def dcroma(v, c, s):
    la, ma = croma(CADV['control'] / 'lineal/fusion_starless.npy', c); lb, mb = croma(CADV[v] / 'lineal/fusion_starless.npy', c); m = ma * mb; l = (lb - la) * m; del la, lb
    g = cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6); return np.where(m > 0, g, np.nan)[::4, ::4]
def pinta(panells, lim, nom, tit):
    h, w = panells[0][0].shape; n = len(panells); cap = 90
    fig = plt.figure(figsize=(n * w / 100, (h + cap) / 100), dpi=100); cm = plt.get_cmap('bwr').copy(); cm.set_bad('0.85')
    for i, (x, sub) in enumerate(panells):
        ax = fig.add_axes([i / n, 0, 1 / n - 0.002, h / (h + cap)]); ax.imshow(x, cmap=cm, vmin=-lim, vmax=lim, interpolation='nearest'); ax.axis('off')
        fig.text(i / n + 0.004, h / (h + cap) + 0.004, sub, va='bottom', fontsize=16)
    fig.text(0.5, 0.995, tit + '   (blau = més fosc o menys vermell/blau després; gris = sense dada)', va='top', ha='center', fontsize=17, weight='bold')
    fig.savefig(OUT / f'VISTA_{nom}.png'); plt.close(fig); print('FET', nom, flush=True)
if '1' in quins:
    pinta([(ratio(CADV['control'] / 'lineal/base_G.npy', CADV[v] / 'lineal/base_G.npy', None, 6), f'{v} / control') for v in ('v3', 'v2')], 0.0015, '1_base_sigma6', 'base_G · ln(després/abans) σ6 · ±0,15 %')
if '2' in quins:
    pinta([(ratio(CADV['control'] / 'lineal/base_G.npy', CADV[v] / 'lineal/base_G.npy', None, 40), f'{v} / control') for v in ('v3', 'v2')], 0.0004, '2_base_sigma40', 'base_G · ln(després/abans) σ40 · ±0,04 %')
if '3' in quins: pinta([(dcroma(v, 0, 20), f'{v} − control') for v in ('v3', 'v2')], 0.001, '3_color_RG_sigma20', 'fusion_starless · Δ ln(R/G) σ20 · ±0,1 %')
if '4' in quins: pinta([(dcroma(v, 2, 20), f'{v} − control') for v in ('v3', 'v2')], 0.001, '4_color_BG_sigma20', 'fusion_starless · Δ ln(B/G) σ20 · ±0,1 %')
if '5' in quins: pinta([(ratio(CMP['control'], CMP[v], None, 6), f'{v} / control') for v in ('v3', 'v2')], 0.006, '5_compost_sigma6', 'compost (màscares de la V107) · ln(després/abans) σ6 · ±0,6 %')
if '6' in quins:
    for g, lim in (('vixen', 0.005), ('sony_A', 0.0015), ('sony_B', 0.0015)):
        pinta([(ratio(AP['control'][g], AP[v][g], 1, 3), f'{v} / control') for v in ('v3', 'v2')], lim, f'6_apilat_{g}_sigma3', f'apilat {g} G · ln(després/abans) σ3 · ±{lim*100:g} %')
if '7' in quins:
    def fi(p):
        x = ld(p); m = ((x > 0) & np.isfinite(x)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32)
        g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        return np.where(m > 0, g(4) - g(40), np.nan)[::4, ::4]
    pinta([(fi(CMP[v]), {'control': 'ABANS (control = V107)', 'v3': 'DESPRÉS (v3)'}[v]) for v in ('control', 'v3')], 0.03, '7_compost_contrast_fi_abans_despres', 'compost · contrast fi ln σ4 − σ40 · ±3 %')
if '8' in quins:
    def cb(v):
        l, m = croma(CADV[v] / 'lineal/fusion_starless.npy', 0); g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        return np.where(m > 0, g(20) - g(200), np.nan)[::4, ::4]
    pinta([(cb(v), {'control': 'ABANS (control = V107)', 'v3': 'DESPRÉS (v3)', 'v2': 'v2'}[v]) for v in ('control', 'v3', 'v2')], 0.003, '8_color_RG_banda_abans_despres', 'fusion_starless · ln(R/G) en banda σ20–200 · ±0,3 %')
