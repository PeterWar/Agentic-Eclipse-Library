"""s12 · T1 i T2 (sencers i per trams) i la textura fina, a cada VARIANT dels apilats de la Sony, amb la geometria fixa i el nul a la mateixa
imatge (com s1). Variants: control (flat radial), pilot (flat 2D σ 2–60), wiener (f0w), wiener_nul (f0w desplaçat 84 × 58 px RAW).
Textura fina: MAD del residu relatiu σ 2/20 px a 3–9,5 R☉ (patró fix + soroll; el soroll de fotó és el mateix a totes les variants).
Ús: s12_mesura_variants.py [variant=carpeta_apilats ...] → S12_VARIANTS.json"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
VAR = {'control': {'A': (CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 1), 'B': (CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1)},
       'pilot': {'A': (PIL / 'flat2d/sony_A_total.npy', 1), 'B': (PIL / 'flat2d/cau/sony_B_total_v42.npy', 1)}}
for arg in sys.argv[1:]:
    n, _, d = arg.partition('='); d = Path(d); VAR[n] = {'A': (d / 'sony_A_total.npy', 1), 'B': (d / 'cau/sony_B_total_v42.npy', 1)}
S1 = json.loads((OUT / 'S1_PERFILS.json').read_text()); TRAMS = {int(k): v for k, v in S1['trams'].items()}
res = {}
yy, xx = np.mgrid[0:H:4, 0:W:4]; rs4 = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del xx, yy
for vn, fonts in VAR.items():
    for ap_, (p, ch) in fonts.items():
        a = np.load(p, mmap_mode='r'); row = {}
        for k, tr in TRACOS.items():
            if ap_ == 'B' and k == 2: continue
            box = caixa_tr(tr, 700); r = rel_map(retall(a, ch, box))
            for tn, (s0, s1) in TRAMS[k].items():
                m, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'], s0, s1)
                row[f'T{k}_{tn}'] = m
        # textura fina (per rajoles de 2000 px, la meitat de dalt i la de baix)
        vals = []
        for y0 in range(0, H, 1500):
            for x0 in range(0, W, 1500):
                b = (x0, y0, min(W, x0 + 1500), min(H, y0 + 1500)); img = retall(a, ch, b); rr = rel_map(img, 20.0, 2.0, 61)
                ys, xs = np.mgrid[b[1]:b[3], b[0]:b[2]]; rsl = np.hypot(xs - SOL[0], ys - SOL[1]) / RSOL; k_ = np.isfinite(rr) & (rsl > 3) & (rsl < 9.5)
                if k_.sum() > 1e5: vals.append(rr[k_] - np.median(rr[k_]))
        v = np.concatenate(vals); row['textura_fina_MAD'] = float(1.4826 * np.median(np.abs(v)))
        res.setdefault(vn, {})[ap_] = row
        print(f"{vn:11s} {ap_}: " + ' · '.join(f"{kk} {m['D']*1e4:+.2f}‱ (z {m.get('z', np.nan):+.1f}, p {m.get('p', np.nan):.3f})" for kk, m in row.items() if isinstance(m, dict)) + f" · textura fina {row['textura_fina_MAD']*1e4:.2f}‱", flush=True)
desa(OUT / 'S12_VARIANTS.json', res)
