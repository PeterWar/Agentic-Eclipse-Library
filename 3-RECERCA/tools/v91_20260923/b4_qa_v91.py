"""b4 · Proves de la V91 desada per Photoshop contra la V90 de Pere (22:06, SHA 5a9233ac…; la font del muntatge): P2 capes que no són filtre (llevat de la 264, ara oculta): píxels
idèntics i propietats iguals; P3 filtres = ràsters de a5b (±1), alfa i màscara de Pere; P4 canvis dels filtres respecte de la V88 només a
98,5–232,5° i d ≤ 14 px (tolerància ±1: Photoshop desa el 16 bits a 15 bits); P5 la capa nova 267 = p1 (±1). Sortida: B4_QA.json."""
from v91_comu import *
from psb69 import PSB
claim(); assert sha(ARREL / '1-PHOTOSHOP/V90.psb') == '5a9233ac85554321ac75c0d43d1c43ab69e86b1861c7f488aef4369fba9ac70d', 'la V90 de Pere ha canviat'; GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
p = PSB(str(ARREL / '1-PHOTOSHOP/V90.psb')); q = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); ids_p = [L['id'] for L in p.layers]; ids_q = [L['id'] for L in q.layers]
assert [i for i in ids_q if i != 267] == ids_p and ids_q.index(267) == ids_q.index(224) + 1
res = dict(P2={}, P3={}, props_diferents=[])
for L0 in p.layers:
    lid = L0['id']; L1 = q.layer(lid)
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k] and not (lid == 264 and k == 'visible'): res['props_diferents'].append([lid, k, str(L0[k]), str(L1[k])])
    if L0['right'] <= L0['left']: continue
    if lid in FILTRES:
        ref = np.load(SORT / f'filtres_radial_c/{FILTRES[lid]}_u16.npy', mmap_mode='r'); r = {'rgb_vs_calculat': int(np.abs(q.channel(lid, 0)[0].astype(np.int32) - np.asarray(ref).astype(np.int32)).max())}
        for c in (-1, -2):
            if c in L0['chans']: r[f'canal{c}_vs_V90'] = int(np.abs(q.channel(lid, c)[0].astype(np.int32) - p.channel(lid, c)[0].astype(np.int32)).max())
        res['P3'][lid] = r
    else:
        mx = 0
        for c in L0['chans']:
            a0 = p.channel(lid, c)[0]
            if a0 is None or a0.size == 0: continue
            mx = max(mx, int(np.abs(a0.astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
        res['P2'][lid] = mx
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not [x for x in res['props_diferents'] if x[0] not in FILTRES]
res['P3_PASS'] = all(v['rgb_vs_calculat'] <= 1 and v.get('canal-1_vs_V90', 0) == 0 and v.get('canal-2_vs_V90', 0) == 0 for v in res['P3'].values())
v88 = np.load(ARREL / '4-RESULTATS/v88_20260923/filtres_finals/P01_NRGF_u16.npy', mmap_mode='r'); a91 = q.channel(41, 0)[0]
ys, xs = np.nonzero(np.abs(np.asarray(v88).astype(np.int32) - a91.astype(np.int32)) > 1); dd = np.hypot(xs - cx, ys - cy) - R; az = (np.degrees(np.arctan2(-(ys - cy), xs - cx)) + 360) % 360
res['P4_NRGF_vs_V88'] = dict(px=int(xs.size), d_max=round(float(dd.max()), 2), az_min=round(float(az.min()), 1), az_max=round(float(az.max()), 1)); res['P4_PASS'] = bool(dd.max() < 14.5 and az.min() >= 98.5 and az.max() <= 232.5)
P1 = np.load(SORT / 'P1_PROTUBERANCIA.npz'); res['P5_capa_nova'] = dict(rgb=int(np.abs(q.channel(267, 0)[0].astype(np.int32) - P1['rgb'][..., 0].astype(np.int32)).max()), alfa=int(np.abs(q.channel(267, -1)[0].astype(np.int32) - P1['alfa'].astype(np.int32)).max()), mode=q.layer(267)['blend'])
res['P5_PASS'] = res['P5_capa_nova']['rgb'] <= 1 and res['P5_capa_nova']['alfa'] <= 1
res['V91'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V91.psb'), bytes=(ARREL / '1-PHOTOSHOP/V91.psb').stat().st_size, capes=len(q.layers))
desa_json('B4_QA.json', res); log(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P4_PASS', 'P5_PASS', 'P4_NRGF_vs_V88', 'P5_capa_nova', 'props_diferents')}, ensure_ascii=False))
