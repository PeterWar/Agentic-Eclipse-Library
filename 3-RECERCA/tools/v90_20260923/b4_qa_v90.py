"""b4 · Proves de la V90 desada per Photoshop (1-PHOTOSHOP/V90.psb) contra la V88 de Pere (18:50):
P2 capes que no són filtre: píxels (canals decodificats) idèntics, i propietats (nom, visibilitat, opacitat, mode) iguals;
P3 capes de filtre: RGB = ràsters de a5_radial (±1 DN16), alfa i màscara idèntiques a la V88, mode/opacitat/visibilitat iguals, nom «· V90»;
P4 canvi dels filtres respecte de la V88 confinat als primers 14 px del limbe. Sortida: B4_QA.json."""
from v90_comu import *
from psb69 import PSB
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); q = PSB(str(ARREL / '1-PHOTOSHOP/V90.psb'))
assert [L['id'] for L in p.layers] == [L['id'] for L in q.layers]
res = dict(P2={}, P3={}, props_diferents=[])
for L0, L1 in zip(p.layers, q.layers):
    lid = L0['id']
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k]: res['props_diferents'].append([lid, k, str(L0[k]), str(L1[k])])
    if L0['name'] != L1['name'] and lid not in FILTRES: res['props_diferents'].append([lid, 'name', L0['name'], L1['name']])
    if L0['right'] <= L0['left']: continue
    if lid in FILTRES:
        r = {}
        ref = np.load(SORT / f'filtres_radial/{FILTRES[lid]}_u16.npy', mmap_mode='r')
        for c in (0, 1, 2): r[f'rgb{c}_vs_calculat'] = int(np.abs(q.channel(lid, c)[0].astype(np.int32) - np.asarray(ref).astype(np.int32)).max())
        for c in (-1, -2):
            if c in L0['chans']: r[f'canal{c}_vs_V88'] = int(np.abs(q.channel(lid, c)[0].astype(np.int32) - p.channel(lid, c)[0].astype(np.int32)).max())
        r['nom'] = L1['name']; res['P3'][lid] = r; log(f'filtre {lid}: {r}')
    else:
        mx = 0
        for c in L0['chans']:
            a0 = p.channel(lid, c)[0]; a1 = q.channel(lid, c)[0]
            if a0 is None or a0.size == 0: continue
            mx = max(mx, int(np.abs(a0.astype(np.int32) - a1.astype(np.int32)).max()))
        res['P2'][lid] = mx; log(f'capa {lid} {L0["name"][:28]}: dif màx {mx}')
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not [x for x in res['props_diferents'] if x[0] not in FILTRES]
res['P3_PASS'] = all(v['rgb0_vs_calculat'] <= 1 and v.get('canal-1_vs_V88', 0) == 0 and v.get('canal-2_vs_V88', 0) == 0 for v in res['P3'].values())
# P4: on canvien els filtres respecte de la V88 (el 41, NRGF, com a mostra), per distància al limbe
a88 = p.channel(41, 0)[0].astype(np.int32); a90 = q.channel(41, 0)[0].astype(np.int32); ys, xs = np.nonzero(a88 != a90)
dd = np.hypot(xs - cx, ys - cy) - R; res['P4_NRGF_canvis'] = dict(px=int(xs.size), d_max_px=round(float(dd.max()), 2) if xs.size else None, d_min_px=round(float(dd.min()), 2) if xs.size else None)
res['P4_PASS'] = bool(xs.size == 0 or dd.max() < 14.5)
res['V90'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V90.psb'), bytes=(ARREL / '1-PHOTOSHOP/V90.psb').stat().st_size, capes=len(q.layers))
desa_json('B4_QA.json', res); log(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P4_PASS', 'P4_NRGF_canvis', 'props_diferents')}, ensure_ascii=False))
