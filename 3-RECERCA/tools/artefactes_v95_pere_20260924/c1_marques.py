"""c1 · Marques de Pere a 1-PHOTOSHOP/Artefactes_V95.psb (24-09-2026): una capa de marques just a sobre de cada filtre (a la MGN, pintades sobre el filtre).
Filtres del fitxer contra la V95 (què ha canviat, i les marques de la MGN com a diferència). Per a cada capa: grups de color, components, azimut, distància al
limbe i caixa. Sortida: MARQUES.json i marques.npz (màscara retallada + origen per capa i grup). No toca cap PSB."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
cx, cy, R = 5375.787, 3775.977, 452.979
FILTRES = {48: '03 ACHF r4', 50: '01 ACHF fi', 52: '05 ACHF fi 2-48', 53: '06 ACHF estructura', 54: 'P03 MGN', 43: 'P02 RHEF', 44: 'P02b RHEF 0,35', 41: 'P01 NRGF', 42: 'P01b NRGF estès',
           47: '03 ACHF r0', 49: '07 ACHF suau r8', 51: '04 ACHF micro', 45: 'P02c RHEF 60°', 46: 'P02d RHEF 30°', 55: 'P04 WOW', 56: 'P05 WOW bilateral'}
p = PSB(str(ARREL / '1-PHOTOSHOP/Artefactes_V95.psb')); v95 = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); out = {'filtres': {}, 'marques': {}}; guard = {}
ordre = [L['id'] for L in p.layers]; noms = {L['id']: L['name'] for L in p.layers}
for lid in FILTRES:
    L0, L1 = v95.layer(lid), p.layer(lid); dif = {}
    for c in (0, 1, 2, -1, -2):
        a, b = p.channel(lid, c)[0], v95.channel(lid, c)[0]
        dif[c] = None if (a is None or b is None or a.shape != b.shape) else int(np.abs(a.astype(np.int32) - b.astype(np.int32)).max())
    out['filtres'][lid] = dict(nom=FILTRES[lid], rgb_alfa_mascara_vs_V95=dif, blend_V95=str(L0['blend']), opacitat_V95=round(L0['opacity'] * 100 / 255), visible_V95=bool(L0['visible']))
def grups_de(rgb, m, x0, y0, clau, sobre):
    hsv = cv2.cvtColor(rgb.astype(np.float32), cv2.COLOR_RGB2HSV); hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    yy, xx = np.mgrid[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
    grups = [('gris_o_negre', m & (sat <= 0.2))]; hist = np.histogram(hue[m & (sat > 0.2)], bins=36, range=(0, 360))[0]; gg = []
    for i in [i for i in range(36) if hist[i] > 0.0005 * max(hist.sum(), 1)]:
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
        comps.sort(key=lambda z: -z['px']); info['grups'].append(dict(nom=nom, rgb_mitja=(rgb[c].mean(0) * 255).round().astype(int).tolist(), px=int(c.sum()), components=comps))
        guard[f'{clau}_{nom}'] = c; guard[f'{clau}_origen'] = np.array([x0, y0])
    return info
for lid in ordre:
    if lid in FILTRES or noms[lid].startswith('00 Base') or lid == 269: continue
    idx = ordre.index(lid); sota = next((ordre[j] for j in range(idx - 1, -1, -1) if ordre[j] in FILTRES), None)
    a, (x0, y0) = p.channel(lid, -1); rgb = np.stack([p.channel(lid, c)[0] for c in range(3)], -1).astype(np.float32) / 65535; m = a.astype(np.float32) / 65535 > 0.2
    out['marques'][lid] = grups_de(rgb, m, x0, y0, str(lid), f'{sota} {FILTRES.get(sota)}'); out['marques'][lid]['nom_capa'] = noms[lid]
# MGN: marques pintades sobre el filtre = diferència contra la V95
a = np.stack([p.channel(54, c)[0] for c in range(3)], -1).astype(np.int32); b = np.stack([v95.channel(54, c)[0] for c in range(3)], -1).astype(np.int32)
dm = np.abs(a - b).max(-1) > 256
if dm.any():
    ys, xs = np.nonzero(dm); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out['marques']['54_pintat'] = grups_de(a[y0:y1, x0:x1].astype(np.float32) / 65535, dm[y0:y1, x0:x1], x0, y0, '54', '54 P03 MGN (pintat sobre el filtre)')
(SORT / 'MARQUES.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n'); np.savez_compressed(SORT / 'marques.npz', **guard)
print('FILTRES contra V95 (max dif rgb0,1,2,alfa,màscara):'); [print(' ', k, v['nom'], v['rgb_alfa_mascara_vs_V95'], v['blend_V95'], v['opacitat_V95'], 'vis' if v['visible_V95'] else 'ocult') for k, v in out['filtres'].items()]
for k, v in out['marques'].items():
    cl = {'<15': 0, '15-150': 0, '150-600': 0, '>600': 0}
    for g in v['grups']:
        for c in g['components']:
            dd = c['d_limbe_px'][1]; cl['<15' if dd < 15 else '15-150' if dd < 150 else '150-600' if dd < 600 else '>600'] += 1
    print(f"MARQUES {k} ({v.get('nom_capa', '')}) sobre {v['sobre']}: {v['px']} px · grups {[(g['nom'], g['rgb_mitja'], g['px'], len(g['components'])) for g in v['grups']]} · components per d mediana {cl}")
# 52 (05 ACHF fi 2-48): també difereix de la V95 → marques pintades sobre el filtre
a = np.stack([p.channel(52, c)[0] for c in range(3)], -1).astype(np.int32); b = np.stack([v95.channel(52, c)[0] for c in range(3)], -1).astype(np.int32)
dm = np.abs(a - b).max(-1) > 256
if dm.any():
    ys, xs = np.nonzero(dm); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out['marques']['52_pintat'] = grups_de(a[y0:y1, x0:x1].astype(np.float32) / 65535, dm[y0:y1, x0:x1], x0, y0, '52', '52 05 ACHF fi 2-48 (pintat sobre el filtre)')
    (SORT / 'MARQUES.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n'); np.savez_compressed(SORT / 'marques.npz', **guard)
    v = out['marques']['52_pintat']; print('MARQUES 52_pintat:', v['px'], [(g['nom'], g['rgb_mitja'], g['px'], len(g['components'])) for g in v['grups']])
for k, v in out['marques'].items():
    print(f"== {k} sobre {v['sobre']}")
    for g in v['grups']:
        for c in g['components'][:10]: print(f"   {g['nom']:12s} px {c['px']:7d} caixa {c['caixa']} az {c['azimut']} d {c['d_limbe_px']}")
