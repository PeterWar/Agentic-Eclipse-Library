import numpy as np, lib, esf, json, sys

FRAMES = [
    # (nom, exposicio)
    ("572A3009.CR3", "1/3200"), ("572A3012.CR3", "1/3200"), ("572A3015.CR3", "1/3200"),
    ("572A3018.CR3", "1/3200"), ("572A2962.CR3", "1/3200"), ("572A2965.CR3", "1/3200"),
    ("572A2997.CR3", "1/2000"), ("572A3003.CR3", "1/2000"), ("572A2985.CR3", "1/2000"),
    ("572A2991.CR3", "1/1000"), ("572A2973.CR3", "1/1000"),
    ("572A2998.CR3", "1/500"),  ("572A3004.CR3", "1/500"), ("572A2986.CR3", "1/500"),
    ("572A2992.CR3", "1/250"),  ("572A2974.CR3", "1/250"),
    ("572A2999.CR3", "1/125"),  ("572A3005.CR3", "1/125"), ("572A2987.CR3", "1/125"),
    ("572A2993.CR3", "1/60"),
    ("572A3000.CR3", "1/30"),   ("572A3006.CR3", "1/30"), ("572A2988.CR3", "1/30"),
]

NSEC = 240
rows = []
for name, ex in FRAMES:
    img = lib.load(name)
    geo = lib.solve_geometry(img)[:3]
    rec = dict(name=name, exp=ex, CY=geo[0], CX=geo[1], R=geo[2])
    _, _, out = esf.measure_frame('', keys=('R', 'G1', 'G2', 'B'), nsec=NSEC, img=img, geo=geo)
    for k in ('R', 'G1', 'G2', 'B'):
        rr = out[k]['rows']
        s = np.array([x['sigma'] for x in rr]); a = np.array([x['amp'] for x in rr])
        rm = np.array([x['rms'] for x in rr]); th = np.array([x['th'] for x in rr])
        r0 = np.array([x['r0'] for x in rr]); P = np.array([x['P'] for x in rr])
        snr = a/np.maximum(rm, 1e-6)
        g = (snr > 12) & (s > 0.2) & (s < 8)
        rec[k] = dict(n=int(g.sum()),
                      fwhm_px=float(2.3548*np.median(s[g])) if g.sum() > 5 else None,
                      p16=float(2.3548*np.percentile(s[g], 16)) if g.sum() > 5 else None,
                      p84=float(2.3548*np.percentile(s[g], 84)) if g.sum() > 5 else None,
                      pedestal_frac=float(np.median(P[g]/a[g])) if g.sum() > 5 else None)
        rec[k+'_th'] = th[g].tolist(); rec[k+'_s'] = s[g].tolist()
    rows.append(rec)
    print("%-14s %-7s  R %.2f\"  G1 %.2f\"  G2 %.2f\"  B %.2f\"   (n=%d)" % (
        name, ex,
        *[ (rec[k]['fwhm_px'] or np.nan)*lib.SCALE for k in ('R','G1','G2','B')],
        rec['G1']['n']), flush=True)

json.dump(rows, open("via_a.json", "w"))
