"""c1 · Les marques de Pere a la capa «Artefactes V92» (269) de la V92 desada a les 01:34: grups de to, components i geometria respecte del limbe.
Pere: línia grisa que «actua com a mirall» («vertical mirror flip along the line»); verd: hi falta detall (queda el color però no la textura);
marró: parts lleugerament més fosques; restes de màscares a la zona de l'earthshine. Sortida: MARQUES_V92.json, marques_v92.npz."""
from v93_comu import *
from psb69 import PSB
import cv2
claim(); p = PSB(str(PSB_PERE)); L = p.layer(269); a, org = p.channel(269, -1); x0, y0 = org
rgb = np.stack([p.channel(269, c)[0] for c in range(3)], -1).astype(np.float32) / 65535; al = a.astype(np.float32) / 65535
np.savez_compressed(SORT / 'marques_v92.npz', rgb=np.round(rgb * 65535).astype(np.uint16), alpha=a, origin=np.array(org))
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV); hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]; m = al > 0.2
yy, xx = np.mgrid[y0:y0 + rgb.shape[0], x0:x0 + rgb.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
hist = np.histogram(hue[m & (sat > 0.2)], bins=36, range=(0, 360))[0]; log('marcats %d; to (10°): %s; sense color %d' % (m.sum(), hist.tolist(), (m & (sat <= 0.2)).sum()))
grups = [('gris', m & (sat <= 0.2))]
pics = [i for i in range(36) if hist[i] > 0.0005 * max(hist.sum(), 1)]; gg = []
for i in pics:
    if gg and i - gg[-1][-1] <= 1: gg[-1].append(i)
    else: gg.append([i])
for g in gg: grups.append((f'to_{g[0] * 10}_{g[-1] * 10 + 10}', m & (sat > 0.2) & (hue >= g[0] * 10) & (hue < g[-1] * 10 + 10)))
out = {'origen': [int(x0), int(y0)], 'mida': list(rgb.shape[:2]), 'grups': []}; classes = {}
for nom, c in grups:
    if c.sum() == 0: continue
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(c.astype(np.uint8), np.ones((9, 9), np.uint8)), 8); comps = []
    for k in range(1, n):
        s = (lab == k) & c
        if s.sum() < 10: continue
        comps.append(dict(px=int(s.sum()), caixa=[int(xx[s].min()), int(yy[s].min()), int(xx[s].max()), int(yy[s].max())],
                          azimut=[round(float(np.percentile(th[s], 2)), 1), round(float(np.median(th[s])), 1), round(float(np.percentile(th[s], 98)), 1)],
                          d_limbe_px=[round(float(np.percentile(d[s], 5)), 1), round(float(np.median(d[s])), 1), round(float(np.percentile(d[s], 95)), 1)]))
    comps.sort(key=lambda c: c['azimut'][1]); classes[nom] = c
    out['grups'].append(dict(nom=nom, rgb_mitja=(rgb[c].mean(0) * 255).round().astype(int).tolist(), px=int(c.sum()), components=comps))
desa_json('MARQUES_V92.json', out); np.savez_compressed(SORT / 'marques_v92_classes.npz', origin=np.array([x0, y0]), **classes)
for g in out['grups']:
    log('%s rgb %s px %d' % (g['nom'], g['rgb_mitja'], g['px']))
    for c in g['components']: log('   caixa %s az %s d %s px %d' % (c['caixa'], c['azimut'], c['d_limbe_px'], c['px']))
