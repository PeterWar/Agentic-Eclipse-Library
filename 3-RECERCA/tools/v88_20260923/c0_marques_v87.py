"""c0 · Les marques de Pere a la capa «Artefactes V87» (257) de la V87: extracció, classes de color i geometria respecte del limbe.
Classes per to (HSV) i alfa > 0,2: verd (45–90°; Pere: «massa pixelades, cosit de cremallera»), lila (270–320°; «llimb llunar més exterior
amb massa textures»), blau clar (150–200°; «origen desconegut»), marró (< 45° o > 345°, R < 0,8; «NRGF a la corona més interior») i taronja
(R ≥ 0,8: punts vora la protuberància, que Pere no descriu). Per a cada component: píxels, caixa, azimuts (p2–p98) i distància al limbe de la
Lluna de presentació (p5/p50/p95; negatiu = dins del disc).
Sortida: 4-RESULTATS/v88_20260923/MARQUES_V87.json, marques_v87_crues.npz i marques_v87_classes.npz."""
from v88_comu import *
from psb69 import PSB
import cv2
claim()
p = PSB(str(ARREL / '1-PHOTOSHOP/V87.psb')); L = p.layer(257)
ch = {c: p.channel(257, c) for c in L['chans']}; a, org = ch[-1]; x0, y0 = org
rgb = np.stack([ch[c][0] for c in range(3)], -1).astype(np.float32) / 65535; al = a.astype(np.float32) / 65535
np.savez_compressed(SORT / 'marques_v87_crues.npz', rgb=np.round(rgb * 65535).astype(np.uint16), alpha=a, origin=np.array(org))
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
hue = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[..., 0]; m = al > 0.2
classes = {'verd': m & (hue > 45) & (hue < 90), 'lila': m & (hue > 270) & (hue < 320), 'blau_clar': m & (hue > 150) & (hue < 200),
           'marro': m & ((hue < 45) | (hue > 345)) & (rgb[..., 0] < 0.8), 'taronja': m & ((hue < 30) | (hue > 345)) & (rgb[..., 0] >= 0.8)}
yy, xx = np.mgrid[y0:y0 + rgb.shape[0], x0:x0 + rgb.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
out = {}
for nom, c in classes.items():
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(c.astype(np.uint8), np.ones((9, 9), np.uint8)), 8); comps = []
    for k in range(1, n):
        s = (lab == k) & c
        if s.sum() < 10: continue
        comps.append(dict(px=int(s.sum()), caixa=[int(xx[s].min()), int(yy[s].min()), int(xx[s].max()), int(yy[s].max())],
                          azimut=[round(float(np.percentile(th[s], 2)), 1), round(float(np.percentile(th[s], 98)), 1)],
                          d_limbe_px=[round(float(np.percentile(d[s], 5)), 1), round(float(np.median(d[s])), 1), round(float(np.percentile(d[s], 95)), 1)]))
    out[nom] = comps
desa_json('MARQUES_V87.json', out)
np.savez_compressed(SORT / 'marques_v87_classes.npz', origin=np.array([x0, y0]), **classes)
log('C0 fet · ' + json.dumps({k: sum(c['px'] for c in v) for k, v in out.items()}))
