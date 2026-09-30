"""x7 (verificador adversari 3) · VISTES DEL LLENÇ SENCER (a 1/4) amb el cel anul·lat, a l'escala de la pols (DoG σ6 − σ60 del ln G):
  X7_AmenysB: ln A − ln B de la Sony (control | v3 | v2): el que va fix al sensor; les taques de pols hi surten dues vegades (A i, desplaçada, B amb signe −).
  X7_VmenysS: ln V − S (S = Sony del control) (control | v3 | v2): la pols de la Vixen.
Escala ±0,15 % (Sony) i ±0,4 % (Vixen). Gris = sense dada. Blau = negatiu.
Sortida: 4-RESULTATS/v108_20260926/verifica3_flat2d/X7_*.png"""
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica3_flat2d'
CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
AP = {'control': dict(V=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'),
      'v3': dict(V=F3 / 'apilats/vixen_total.npy', A=F3 / 'apilats/sony_A_total.npy', B=F3 / 'apilats/cau/sony_B_total_v42.npy'),
      'v2': dict(V=F2 / 'apilats/vixen_total.npy', A=F2 / 'apilats/sony_A_total.npy', B=F2 / 'apilats/cau/sony_B_total_v42.npy')}
def lnG(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); ok = np.isfinite(x) & (x > 0)
    return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
a, oa = lnG(AP['control']['A']); b, ob = lnG(AP['control']['B']); S = np.where(oa & ob, 0.5 * (a + b), np.where(oa, a, b)).astype(np.float32); oS = oa | ob; del a, b
for nom, lim in (('AmenysB', 0.0015), ('VmenysS', 0.004)):
    pan = []
    for v in ('control', 'v3', 'v2'):
        if nom == 'AmenysB':
            a, oa = lnG(AP[v]['A']); b, ob = lnG(AP[v]['B']); m = (oa & ob).astype(np.float32); z = a - b; del a, b
        else:
            a, oa = lnG(AP[v]['V']); m = (oa & oS).astype(np.float32); z = a - S; del a
        z = np.where(m > 0, z, 0).astype(np.float32)
        g = lambda s: cv2.GaussianBlur(z * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        ok = cv2.erode(m, np.ones((61, 61), np.uint8)) > 0
        pan.append((np.where(ok, g(6) - g(60), np.nan)[::4, ::4], v)); del z, m
    h, w = pan[0][0].shape; cap = 60
    fig = plt.figure(figsize=(3 * w / 100, (h + cap) / 100), dpi=100); cm = plt.get_cmap('bwr').copy(); cm.set_bad('0.85')
    for i, (x, sub) in enumerate(pan):
        ax = fig.add_axes([i / 3, 0, 1 / 3 - 0.002, h / (h + cap)]); ax.imshow(x, cmap=cm, vmin=-lim, vmax=lim, interpolation='nearest'); ax.axis('off')
        fig.text(i / 3 + 0.004, h / (h + cap) + 0.004, sub, va='bottom', fontsize=16)
    fig.text(0.5, 0.995, f'{nom} · ln G, DoG σ6−σ60 · ±{lim*100:g} % (cel anul·lat: només el que va fix al sensor)', va='top', ha='center', fontsize=17, weight='bold')
    fig.savefig(OUT / f'X7_{nom}.png'); plt.close(fig); print('FET', nom, flush=True)
