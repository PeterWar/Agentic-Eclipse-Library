"""c1 · Les marques de Pere a la capa «Artefactes V90» (264) de la V88: extracció, histograma de to, classes i geometria respecte del limbe.
Sortida: MARQUES_V90.json, marques_v90_crues.npz i marques_v90_classes.npz."""
from vm_comu import *
from psb69 import PSB
import cv2
claim()
p = PSB(str(PSB_PERE)); L = p.layer(264)
ch = {c: p.channel(264, c) for c in L['chans']}; a, org = ch[-1]; x0, y0 = org
rgb = np.stack([ch[c][0] for c in range(3)], -1).astype(np.float32) / 65535; al = a.astype(np.float32) / 65535
np.savez_compressed(SORT / 'marques_v90_crues.npz', rgb=np.round(rgb * 65535).astype(np.uint16), alpha=a, origin=np.array(org))
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV); hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]; m = al > 0.2
hist = np.histogram(hue[m & (sat > 0.25)], bins=36, range=(0, 360))[0]
log('píxels marcats %d; histograma de to (10°): %s' % (m.sum(), hist.tolist()))
# colors dominants: agrupa per to en calaixos de 10° amb prou píxels
pics = [i for i in range(36) if hist[i] > 0.01 * hist.sum()]
log('calaixos amb >1 %%: %s' % [(i * 10, int(hist[i])) for i in pics])
grups = []
for i in pics:
    if grups and i - grups[-1][-1] <= 1: grups[-1].append(i)
    else: grups.append([i])
yy, xx = np.mgrid[y0:y0 + rgb.shape[0], x0:x0 + rgb.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
out = {'origen': [int(x0), int(y0)], 'mida': list(rgb.shape[:2]), 'grups_de_to': []}; classes = {}
for g in grups:
    h0, h1 = g[0] * 10, g[-1] * 10 + 10; c = m & (sat > 0.25) & (hue >= h0) & (hue < h1)
    mitja = (rgb[c].mean(0) * 255).round().astype(int).tolist(); nom = f'to_{h0}_{h1}'
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(c.astype(np.uint8), np.ones((9, 9), np.uint8)), 8); comps = []
    for k in range(1, n):
        s = (lab == k) & c
        if s.sum() < 10: continue
        comps.append(dict(px=int(s.sum()), caixa=[int(xx[s].min()), int(yy[s].min()), int(xx[s].max()), int(yy[s].max())],
                          azimut=[round(float(np.percentile(th[s], 2)), 1), round(float(np.median(th[s])), 1), round(float(np.percentile(th[s], 98)), 1)],
                          d_limbe_px=[round(float(np.percentile(d[s], 5)), 1), round(float(np.median(d[s])), 1), round(float(np.percentile(d[s], 95)), 1)]))
    comps.sort(key=lambda c: c['azimut'][1]); classes[nom] = c
    out['grups_de_to'].append(dict(nom=nom, rgb_mitja=mitja, px=int(c.sum()), components=comps))
grisos = m & (sat <= 0.25); out['sense_color_px'] = int(grisos.sum())
desa_json('MARQUES_V90.json', out)
np.savez_compressed(SORT / 'marques_v90_classes.npz', origin=np.array([x0, y0]), **classes)
for g in out['grups_de_to']:
    log('%s rgb %s px %d' % (g['nom'], g['rgb_mitja'], g['px']))
    for c in g['components']: log('   az %s  d %s  px %d' % (c['azimut'], c['d_limbe_px'], c['px']))
