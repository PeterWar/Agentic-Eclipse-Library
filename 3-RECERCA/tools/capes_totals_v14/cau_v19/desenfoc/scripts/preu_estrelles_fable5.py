# -*- coding: utf-8 -*-
"""El preu del metode de Pere: supervivencia de les estrelles a F.

Deteccio a capa1 (canal G, resolucio completa, r > 2.5 Rsol), i per a cada
estrella mirem si sobreviu a F = capa1*(1-m)+capa2*m (pic i flux sobre fons
local). Tambe el perfil radial de la mascara m.
"""
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
print('carregat', g1.shape)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.hypot(xx - SX, yy - SY) / RS
del xx, yy

# perfil radial de la mascara
perf_m = []
for r0 in np.arange(0.0, 12.0, 0.25):
    an = (rr >= r0) & (rr < r0 + 0.25)
    if an.sum() > 1000:
        perf_m.append(dict(r=round(float(r0) + 0.125, 3),
                           m_med=float(np.median(m[an])),
                           m_p05=float(np.percentile(m[an], 5)),
                           frac_m_lt_05=float((m[an] < 0.5).mean())))

# fons per obertura morfologica + gaussiana
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
def fons(img):
    op = cv2.morphologyEx(img, cv2.MORPH_OPEN, ker)
    return cv2.GaussianBlur(op, (0, 0), 5.0)

det1 = g1 - fons(g1)
detF = gF - fons(gF)

zona = rr > 2.5
samp = det1[zona][::37]
sig1 = 1.4826 * np.median(np.abs(samp - np.median(samp)))
sampF = detF[zona][::37]
sigF = 1.4826 * np.median(np.abs(sampF - np.median(sampF)))
print('sigma det1 %.6f  detF %.6f' % (sig1, sigF))

llindar = max(6.0 * sig1, 0.004)
dil = cv2.dilate(det1, np.ones((5, 5), np.uint8))
pics = (det1 >= dil) & (det1 > llindar) & zona
pics[:8, :] = pics[-8:, :] = False
pics[:, :8] = pics[:, -8:] = False
ys, xs = np.where(pics)
print('candidats:', len(ys), 'llindar %.5f' % llindar)

def flux5(det, y, x):
    return float(det[y - 2:y + 3, x - 2:x + 3].sum())

stars = []
for y, x in zip(ys, xs):
    a1 = float(det1[y, x])
    f1 = flux5(det1, y, x)
    if f1 <= 0:
        continue
    # a F el pic es pot haver mogut radialment: busca el maxim local en 7x7
    w = detF[y - 3:y + 4, x - 3:x + 4]
    iy, ix = np.unravel_index(np.argmax(w), w.shape)
    yF, xF = y + iy - 3, x + ix - 3
    aF = float(detF[yF, xF])
    fF = flux5(detF, yF, xF)
    sobreviu = (aF > 3.0 * sigF) and (fF > 0.3 * f1)
    stars.append((float(rr[y, x]), float(m[y, x]), a1, f1, aF, fF, bool(sobreviu)))

stars = np.array(stars, dtype=object)
r_s = np.array([s[0] for s in stars])
m_s = np.array([s[1] for s in stars])
viu = np.array([s[6] for s in stars])
rat = np.array([min(s[5] / s[3], 3.0) if s[3] > 0 else 0.0 for s in stars])

taula_r = []
for r0 in np.arange(2.5, 11.0, 0.5):
    sel = (r_s >= r0) & (r_s < r0 + 0.5)
    if sel.sum() >= 5:
        taula_r.append(dict(r=float(r0) + 0.25, n=int(sel.sum()),
                            frac_viu=float(viu[sel].mean()),
                            flux_ratio_med=float(np.median(rat[sel])),
                            m_med=float(np.median(m_s[sel]))))
taula_m = []
for m0 in np.arange(0.0, 1.0, 0.1):
    sel = (m_s >= m0) & (m_s < m0 + 0.1 + (0.001 if m0 > 0.85 else 0))
    if m0 >= 0.9:
        sel = m_s >= 0.9
    if sel.sum() >= 5:
        taula_m.append(dict(m=float(m0) + 0.05, n=int(sel.sum()),
                            frac_viu=float(viu[sel].mean()),
                            flux_ratio_med=float(np.median(rat[sel]))))
    if m0 >= 0.9:
        break

print('estrelles: %d  viuen %.1f%%  flux ratio med %.3f' %
      (len(stars), 100 * viu.mean(), np.median(rat)))
for t in taula_r:
    print('r %.2f n %4d viu %.2f fluxratio %.3f m %.2f' %
          (t['r'], t['n'], t['frac_viu'], t['flux_ratio_med'], t['m_med']))
for t in taula_m:
    print('m %.2f n %4d viu %.2f fluxratio %.3f' %
          (t['m'], t['n'], t['frac_viu'], t['flux_ratio_med']))

json.dump(dict(sigma_det_capa1=float(sig1), sigma_det_F=float(sigF),
               llindar_deteccio=float(llindar), n_estrelles=len(stars),
               frac_viu_total=float(viu.mean()),
               flux_ratio_median=float(np.median(rat)),
               per_radi=taula_r, per_m=taula_m, perfil_mascara=perf_m),
          open(OUT + 'preu_estrelles_fable5.json', 'w'), indent=1,
          default=float)

# PNG de diagnostic: estrelles mortes en vermell, vives en verd, sobre F (::4)
vis = np.clip(gF[::4, ::4] * 255, 0, 255).astype(np.uint8)
vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
for (rv, mv, a1, f1, aF, fF, sv), y, x in zip(stars, ys, xs):
    col = (0, 200, 0) if sv else (0, 0, 255)
    cv2.circle(vis, (int(x) // 4, int(y) // 4), 3, col, 1)
cv2.imwrite(OUT + 'estrelles_supervivencia.png', vis)
print('FET')
