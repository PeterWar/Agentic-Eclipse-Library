"""b4 · Proves de la V93 desada per Photoshop contra la V92 de Pere (01:34, SHA 2850f1bd…): P2 capes que no es toquen: píxels idèntics i propietats
iguals (la 269 només passa a oculta); P3 filtres = ràsters calculats (±1), alfa de Pere, màscara de Pere (la 56, neta a la zona); P4 on canvien els
filtres respecte de la V92 (fora del disc): d ≤ 6,5 px a tot arreu i ≤ 14,5 px a 99–232°; P5 màscares 56/76/96/224 = les de Pere amb la zona a 0
i idèntiques fora. Sortida: B4_QA.json."""
from v93_comu import *
from psb69 import PSB
claim(); assert sha(PSB_PERE) == '2850f1bd39a5d8a64a2ce610088977d9a92ce69297acdec6f2c8ab3ba3ab1077'
p = PSB(str(PSB_PERE)); q = PSB(str(ARREL / '1-PHOTOSHOP/V93.psb')); assert [L['id'] for L in q.layers] == [L['id'] for L in p.layers]
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; NETEJA = (56, 76, 96, 224); Z = np.load(SORT / 'zona_earthshine.npz'); zona = Z['zona']; zx, zy = [int(v) for v in Z['origen']]
res = dict(P2={}, P3={}, P5={}, props_diferents=[])
for L0 in p.layers:
    lid = L0['id']; L1 = q.layer(lid)
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k] and not (lid == 269 and k == 'visible'): res['props_diferents'].append([lid, k, str(L0[k]), str(L1[k])])
    if L0['right'] <= L0['left'] and not L0['mask']: continue
    if lid in FILTRES:
        ref = np.load(SORT / f'filtres_v93/{FILTRES[lid]}_u16.npy', mmap_mode='r'); r = {'rgb_vs_calculat': int(np.abs(q.channel(lid, 0)[0].astype(np.int32) - np.asarray(ref).astype(np.int32)).max()),
                                                                               'alfa_vs_V92': int(np.abs(q.channel(lid, -1)[0].astype(np.int32) - p.channel(lid, -1)[0].astype(np.int32)).max())}
        if lid not in NETEJA: r['mascara_vs_V92'] = int(np.abs(q.channel(lid, -2)[0].astype(np.int32) - p.channel(lid, -2)[0].astype(np.int32)).max())
        res['P3'][lid] = r
    if lid in NETEJA:
        m0, (ox, oy) = p.channel(lid, -2); m1 = q.channel(lid, -2)[0]; zm = np.zeros(m0.shape, bool); ys, xs = np.nonzero(zona); X, Y = xs + zx - ox, ys + zy - oy; ok = (X >= 0) & (Y >= 0) & (X < m0.shape[1]) & (Y < m0.shape[0]); zm[Y[ok], X[ok]] = True
        res['P5'][lid] = dict(zona_max=int(m1[zm].max()), fora_zona_dif_max=int(np.abs(m1[~zm].astype(np.int32) - m0[~zm].astype(np.int32)).max()))
        if lid not in FILTRES:
            mx = 0
            for c in L0['chans']:
                if c != -2 and L0['right'] > L0['left']: mx = max(mx, int(np.abs(p.channel(lid, c)[0].astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
            res['P2'][lid] = mx
    elif lid not in FILTRES and L0['right'] > L0['left']:
        mx = 0
        for c in L0['chans']:
            a0 = p.channel(lid, c)[0]
            if a0 is None or a0.size == 0: continue
            mx = max(mx, int(np.abs(a0.astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
        res['P2'][lid] = mx
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not res['props_diferents']
res['P3_PASS'] = all(v['rgb_vs_calculat'] <= 1 and v['alfa_vs_V92'] == 0 and v.get('mascara_vs_V92', 0) == 0 for v in res['P3'].values())
res['P5_PASS'] = all(v['zona_max'] == 0 and v['fora_zona_dif_max'] == 0 for v in res['P5'].values())
res['P4'] = {}; ok4 = True
for lid in (41, 56, 55):
    a92 = p.channel(lid, 0)[0].astype(np.int32); a93 = q.channel(lid, 0)[0].astype(np.int32); ys, xs = np.nonzero(np.abs(a92 - a93) > 1)
    dd = np.hypot(xs - cx, ys - cy) - R; az = (np.degrees(np.arctan2(-(ys - cy), xs - cx)) + 360) % 360; fora_disc = dd > -6; dins = (az >= 98.5) & (az <= 232.5)
    res['P4'][lid] = dict(px_fora_disc=int(fora_disc.sum()), d_max_99_232=round(float(dd[fora_disc & dins].max()), 2) if (fora_disc & dins).any() else None, d_max_resta=round(float(dd[fora_disc & ~dins].max()), 2) if (fora_disc & ~dins).any() else None)
    ok4 &= (not (fora_disc & dins).any() or dd[fora_disc & dins].max() <= 14.5) and (not (fora_disc & ~dins).any() or dd[fora_disc & ~dins].max() <= 6.5)
res['P4_PASS'] = bool(ok4); res['V93'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V93.psb'), bytes=(ARREL / '1-PHOTOSHOP/V93.psb').stat().st_size, capes=len(q.layers))
desa_json('B4_QA.json', res); print(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P4_PASS', 'P5_PASS', 'P4', 'P5', 'props_diferents')}, ensure_ascii=False))
