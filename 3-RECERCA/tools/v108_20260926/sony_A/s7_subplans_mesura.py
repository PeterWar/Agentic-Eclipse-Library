"""s7 · Mesura de T1 i T2 a cada subplà de Bayer (R, G1, G2, B, en espai de càmera) dels apilats de s6, amb el nul a la mateixa imatge.
Sortida: S7_SUBPLANS.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
S1 = json.loads((OUT / 'S1_PERFILS.json').read_text()); TRAMS = {int(k): v for k, v in S1['trams'].items()}
NOMS = {0: 'R', 1: 'G1', 2: 'B', 3: 'G2'}; res = {}
for var in ('control', 'flat2d'):
    D = OUT / f'subplans_{var}'; rb = json.loads((D / 'REBUT.json').read_text())
    for gn in rb['grups']:
        for k, tr in TRACOS.items():
            tn = f'T{k}'; x0, y0, x1, y1 = rb['caixes'][tn]; z = np.load(D / f'{tn}_{gn}.npz'); nu, de = z['num'], z['den']
            imgs = {NOMS[i]: np.where(de[i] > 0.02 * de[i].max(), nu[i] / np.maximum(de[i], 1e-20), 0).astype(np.float32) for i in range(4) if de[i].max() > 0}
            if 'G1' in imgs and 'G2' in imgs: imgs['G1+G2'] = np.where((imgs['G1'] > 0) & (imgs['G2'] > 0), 0.5 * (imgs['G1'] + imgs['G2']), 0).astype(np.float32)
            for sn, img in imgs.items():
                if (img > 0).mean() < 0.2: continue
                r = rel_map(img)
                for tram, (s0, s1) in TRAMS[k].items():
                    m, t, pr = mesura_amb_nul(r, (x0, y0), tr['centre'], tr['d'], tr['llarg'], s0, s1, girs=(-6, 6))
                    if not np.isfinite(m.get('D', np.nan)) or 'z' not in m: continue
                    res.setdefault(var, {}).setdefault(gn, {}).setdefault(f'{tn}_{tram}', {})[sn] = m
            row = res.get(var, {}).get(gn, {})
            for key in [q for q in row if q.startswith(tn)]:
                print(f"{var:7s} {gn:9s} {key:11s} " + ' · '.join(f"{sn} {m['D']*1e4:+6.1f}‱ (z {m['z']:+4.1f})" for sn, m in row[key].items()), flush=True)
desa(OUT / 'S7_SUBPLANS.json', res)
