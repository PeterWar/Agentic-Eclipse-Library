# -*- coding: utf-8 -*-
"""Segona passada: separa gra fi d'estrelles per amplitud (a1) i deteccio
mes estricta (maxim local 9x9), amb estadistica per nivell."""
import json
import numpy as np
import cv2

D = '/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc/'
OUT = D + 'fable5/'
geo = json.load(open(D + 'geometria.json'))
SX, SY = geo['sol_crop']
RS = geo['rs']

g1 = np.load(D + 'capa1_rgb16.npy', mmap_mode='r')[:, :, 1].astype(np.float32) / 65535.0
g2 = np.load(D + 'capa2_rgb16.npy', mmap_mode='r')[:, :, 1].astype(np.float32) / 65535.0
m = np.load(D + 'capa2_mask16.npy', mmap_mode='r')[:].astype(np.float32) / 65535.0
gF = g1 * (1.0 - m) + g2 * m
H, W = g1.shape
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.hypot(xx - SX, yy - SY) / RS
del xx, yy

ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
def fons(img):
    return cv2.GaussianBlur(cv2.morphologyEx(img, cv2.MORPH_OPEN, ker), (0, 0), 5.0)

det1 = g1 - fons(g1)
detF = gF - fons(gF)
zona = rr > 2.5
sampF = detF[zona][::37]
sigF = 1.4826 * np.median(np.abs(sampF - np.median(sampF)))

dil = cv2.dilate(det1, np.ones((9, 9), np.uint8))
pics = (det1 >= dil) & (det1 > 0.008) & zona
pics[:8, :] = pics[-8:, :] = False
pics[:, :8] = pics[:, -8:] = False
ys, xs = np.where(pics)
print('candidats 9x9 > 0.008:', len(ys))

n = len(ys)
r_s = rr[ys, xs]
m_s = m[ys, xs]
a1 = det1[ys, xs]
f1 = np.zeros(n, np.float32)
aF = np.zeros(n, np.float32)
fF = np.zeros(n, np.float32)
for i, (y, x) in enumerate(zip(ys, xs)):
    f1[i] = det1[y - 2:y + 3, x - 2:x + 3].sum()
    w = detF[y - 3:y + 4, x - 3:x + 4]
    iy, ix = np.unravel_index(np.argmax(w), w.shape)
    aF[i] = w[iy, ix]
    fF[i] = detF[y + iy - 5:y + iy - 0, x + ix - 5:x + ix - 0].sum()  # 5x5 al pic
ok = f1 > 0
r_s, m_s, a1, f1, aF, fF = (v[ok] for v in (r_s, m_s, a1, f1, aF, fF))
ys, xs = ys[ok], xs[ok]
rat = np.clip(fF / f1, 0, 3)
viu = (aF > 3 * sigF) & (rat > 0.3)
np.savez_compressed(OUT + 'estrelles_fable5.npz', y=ys, x=xs, r=r_s, m=m_s,
                    a1=a1, f1=f1, aF=aF, fF=fF, viu=viu)

nivells = [('gra_i_estrelles a1>0.008', 0.008, 0.02),
           ('estrelles_febles a1 0.02-0.05', 0.02, 0.05),
           ('estrelles_brillants a1>0.05', 0.05, 99.0)]
res = dict(sigma_det_F=float(sigF), nivells=[])
for nom, lo, hi in nivells:
    sel = (a1 >= lo) & (a1 < hi)
    ns = int(sel.sum())
    if ns == 0:
        continue
    niv = dict(nom=nom, n=ns, frac_viu=float(viu[sel].mean()),
               flux_ratio_med=float(np.median(rat[sel])), per_radi=[], per_m=[])
    for r0 in np.arange(2.5, 8.0, 0.5):
        s2 = sel & (r_s >= r0) & (r_s < r0 + 0.5)
        if s2.sum() >= 5:
            niv['per_radi'].append(dict(r=float(r0) + 0.25, n=int(s2.sum()),
                                        frac_viu=float(viu[s2].mean()),
                                        flux_ratio_med=float(np.median(rat[s2])),
                                        m_med=float(np.median(m_s[s2]))))
    for m0 in np.arange(0.0, 1.01, 0.1):
        s2 = sel & (m_s >= m0) & (m_s < (m0 + 0.1 if m0 < 0.89 else 1.01))
        if s2.sum() >= 5:
            niv['per_m'].append(dict(m=float(m0) + 0.05, n=int(s2.sum()),
                                     frac_viu=float(viu[s2].mean()),
                                     flux_ratio_med=float(np.median(rat[s2]))))
        if m0 >= 0.89:
            break
    res['nivells'].append(niv)
    print('%s: n=%d viu %.1f%% fluxratio med %.3f' %
          (nom, ns, 100 * niv['frac_viu'], niv['flux_ratio_med']))
    for t in niv['per_radi']:
        print('  r %.2f n %5d viu %.2f rat %.3f m %.2f' %
              (t['r'], t['n'], t['frac_viu'], t['flux_ratio_med'], t['m_med']))
    for t in niv['per_m']:
        print('  m %.2f n %5d viu %.2f rat %.3f' %
              (t['m'], t['n'], t['frac_viu'], t['flux_ratio_med']))

json.dump(res, open(OUT + 'preu_estrelles_nivells_fable5.json', 'w'),
          indent=1, default=float)
print('FET')
