"""b4 · Proves de la V92 desada per Photoshop contra la V91 de Pere (00:23, SHA d035946a…; la font del muntatge): P2 capes que no són filtre ni la 267:
píxels idèntics i propietats iguals; P3 filtres = ràsters de a4m+a5c (±1; Photoshop desa el 16 bits a 15 bits), alfa i màscara de Pere (0);
P4 on canvien els filtres respecte de la V91 (NRGF 41 i WOW bilateral 56): a d ≤ 6,5 px fora de 99–232° i a d ≤ 14,5 px a dins; P5 la 267: RGB = p1b
(±1) on l'alfa > 0 i alfa de Pere (0). Sortida: B4_QA.json."""
from pathlib import Path
import json, sys, hashlib
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
SRC = ARREL / '1-PHOTOSHOP/V91.psb'; SHA_SRC = json.loads((SORT / 'B2_MUNTATGE.json').read_text())['font']['sha256']; assert sha(SRC) == SHA_SRC, 'la V91 de Pere ha canviat'
GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
p = PSB(str(SRC)); q = PSB(str(ARREL / '1-PHOTOSHOP/V92.psb')); assert [L['id'] for L in q.layers] == [L['id'] for L in p.layers]
res = dict(font=dict(path='1-PHOTOSHOP/V91.psb', sha256=SHA_SRC), P2={}, P3={}, props_diferents=[])
for L0 in p.layers:
    lid = L0['id']; L1 = q.layer(lid)
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k]: res['props_diferents'].append([lid, k, str(L0[k]), str(L1[k])])
    if L0['right'] <= L0['left']: continue
    if lid in FILTRES:
        ref = np.load(SORT / f'filtres_v92/{FILTRES[lid]}_u16.npy', mmap_mode='r'); r = {'rgb_vs_calculat': int(np.abs(q.channel(lid, 0)[0].astype(np.int32) - np.asarray(ref).astype(np.int32)).max())}
        for c in (-1, -2):
            if c in L0['chans']: r[f'canal{c}_vs_V91'] = int(np.abs(q.channel(lid, c)[0].astype(np.int32) - p.channel(lid, c)[0].astype(np.int32)).max())
        res['P3'][lid] = r
    elif lid != 267:
        mx = 0
        for c in L0['chans']:
            a0 = p.channel(lid, c)[0]
            if a0 is None or a0.size == 0: continue
            mx = max(mx, int(np.abs(a0.astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
        res['P2'][lid] = mx
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not res['props_diferents']
res['P3_PASS'] = all(v['rgb_vs_calculat'] <= 1 and v.get('canal-1_vs_V91', 0) == 0 and v.get('canal-2_vs_V91', 0) == 0 for v in res['P3'].values())
res['P4'] = {}; ok4 = True
for lid in (41, 56):
    a91 = p.channel(lid, 0)[0].astype(np.int32); a92 = q.channel(lid, 0)[0].astype(np.int32); ys, xs = np.nonzero(np.abs(a91 - a92) > 1)
    dd = np.hypot(xs - cx, ys - cy) - R; az = (np.degrees(np.arctan2(-(ys - cy), xs - cx)) + 360) % 360; dins = (az >= 98.5) & (az <= 232.5)
    res['P4'][lid] = dict(px=int(xs.size), d_max_dins_99_232=round(float(dd[dins].max()), 2) if dins.any() else None, d_max_fora=round(float(dd[~dins].max()), 2) if (~dins).any() else None)
    ok4 &= (not dins.any() or dd[dins].max() <= 14.5) and (not (~dins).any() or dd[~dins].max() <= 6.5)
res['P4_PASS'] = bool(ok4)
Z = np.load(SORT / 'P1B_GUSPIRES.npz'); zb = [int(v) for v in Z['caixa']]; L = q.layer(267); b = (L['left'], L['top'], L['right'], L['bottom'])
al = q.channel(267, -1)[0]; rgbq = np.stack([q.channel(267, c)[0] for c in range(3)], -1).astype(np.int32); rgbz = Z['rgb'][b[1] - zb[1]:b[3] - zb[1], b[0] - zb[0]:b[2] - zb[0]].astype(np.int32)
res['P5'] = dict(rgb_on_alfa=int(np.abs(rgbq - rgbz)[al > 0].max()), alfa_vs_V91=int(np.abs(al.astype(np.int32) - p.channel(267, -1)[0].astype(np.int32)).max()), mode=L['blend'])
res['P5_PASS'] = res['P5']['rgb_on_alfa'] <= 1 and res['P5']['alfa_vs_V91'] == 0
res['V92'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V92.psb'), bytes=(ARREL / '1-PHOTOSHOP/V92.psb').stat().st_size, capes=len(q.layers))
(SORT / 'B4_QA.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P4_PASS', 'P5_PASS', 'P4', 'P5', 'props_diferents')}, ensure_ascii=False))
