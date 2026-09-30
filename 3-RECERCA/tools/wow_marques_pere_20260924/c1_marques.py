"""c1 · Marques de Pere a 1-PHOTOSHOP/WOW.psb (24-09-2026, 15:26): capa 270 «Capa 1» (sobre la 55, P04 WOW) i capa 272 «Capa 2» (sobre la 56,
P05 WOW bilateral). Grups de color, components i posició respecte del limbe; les 55/56 del fitxer contra les de la V94. Sortida: MARQUES.json i marques.npz."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/wow_marques_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v92_20260924/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
p = PSB(str(ARREL / '1-PHOTOSHOP/WOW.psb')); v94 = PSB(str(ARREL / '1-PHOTOSHOP/V94.psb')); out = {'capes': {}}; guard = {}
for lid in (55, 56):
    a = p.channel(lid, 0)[0]; b = v94.channel(lid, 0)[0]; al = p.channel(lid, -1)[0]; bl = v94.channel(lid, -1)[0]
    out['capes'][lid] = dict(rgb_vs_V94_max=int(np.abs(a.astype(np.int32) - b.astype(np.int32)).max()), alfa_vs_V94_max=int(np.abs(al.astype(np.int32) - bl.astype(np.int32)).max()),
                             mascara_vs_V94_max=int(np.abs(p.channel(lid, -2)[0].astype(np.int32) - v94.channel(lid, -2)[0].astype(np.int32)).max()))
for lid, sobre in ((270, 'P04 WOW (55)'), (272, 'P05 WOW bilateral (56)')):
    a, (x0, y0) = p.channel(lid, -1); rgb = np.stack([p.channel(lid, c)[0] for c in range(3)], -1).astype(np.float32) / 65535; al = a.astype(np.float32) / 65535; m = al > 0.2
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV); hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    yy, xx = np.mgrid[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
    grups = [('gris_o_negre', m & (sat <= 0.2))]; hist = np.histogram(hue[m & (sat > 0.2)], bins=36, range=(0, 360))[0]
    pics = [i for i in range(36) if hist[i] > 0.0005 * max(hist.sum(), 1)]; gg = []
    for i in pics:
        if gg and i - gg[-1][-1] <= 1: gg[-1].append(i)
        else: gg.append([i])
    for g in gg: grups.append((f'to_{g[0] * 10}_{g[-1] * 10 + 10}', m & (sat > 0.2) & (hue >= g[0] * 10) & (hue < g[-1] * 10 + 10)))
    info = dict(sobre=sobre, origen=[int(x0), int(y0)], px=int(m.sum()), grups=[])
    for nom, c in grups:
        if c.sum() == 0: continue
        n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(c.astype(np.uint8), np.ones((9, 9), np.uint8)), 8); comps = []
        for k in range(1, n):
            s = (lab == k) & c
            if s.sum() < 10: continue
            comps.append(dict(px=int(s.sum()), caixa=[int(xx[s].min()), int(yy[s].min()), int(xx[s].max()), int(yy[s].max())], azimut=[round(float(np.percentile(th[s], q)), 1) for q in (2, 50, 98)],
                              d_limbe_px=[round(float(np.percentile(d[s], q)), 1) for q in (5, 50, 95)]))
        comps.sort(key=lambda z: -z['px']); info['grups'].append(dict(nom=nom, rgb_mitja=(rgb[c].mean(0) * 255).round().astype(int).tolist(), val_mitja=round(float(val[c].mean()), 3), px=int(c.sum()), components=comps))
        guard[f'{lid}_{nom}'] = c; guard[f'{lid}_origen'] = np.array([x0, y0])
    out['capes'][lid] = info
    print(lid, sobre, 'px', info['px'])
    for g in info['grups']:
        print('  ', g['nom'], g['rgb_mitja'], 'px', g['px'], 'components', len(g['components']))
        for c in g['components'][:14]: print('      caixa', c['caixa'], 'az', c['azimut'], 'd', c['d_limbe_px'], 'px', c['px'])
print('55/56 contra la V94:', {k: v for k, v in out['capes'].items() if k in (55, 56)})
(SORT / 'MARQUES.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n'); np.savez_compressed(SORT / 'marques.npz', **guard)
