import numpy as np, ptc, json, sys, time

V = '/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
PED = 512.0

PAIRS = [
    # (exp, fitxer A, fitxer B, dt_s)
    ('1/3200', '572A2936', '572A2937', 0.73),
    ('1/3200', '572A2938', '572A2939', 0.65),
    ('1/3200', '572A2944', '572A2945', 0.65),
    ('1/3200', '572A2950', '572A2951', 0.65),
    ('1/3200', '572A2958', '572A2959', 0.65),
    ('1/2000', '572A2997', '572A3003', 6.06),
    ('1/500',  '572A2998', '572A3004', 6.06),
    ('1/125',  '572A2999', '572A3005', 6.06),
    ('1/30',   '572A3000', '572A3006', 6.07),
    ('1/8',    '572A3001', '572A3007', 6.07),
    ('0.5',    '572A3002', '572A3008', 6.07),
    ('2',      '572A2979', '572A2980', 2.90),
    ('2',      '572A2980', '572A2981', 2.91),
    ('10.3',   '572A2982', '572A2983', 13.07),
    ('10.3',   '572A2983', '572A2984', 13.40),
    ('1/1000', '572A2973', '572A2991', 61.71),
    ('1/250',  '572A2974', '572A2992', 61.71),
    ('1/60',   '572A2975', '572A2993', 61.71),
    ('1/15',   '572A2976', '572A2994', 61.71),
    ('1/4',    '572A2977', '572A2995', 61.71),
    ('1',      '572A2978', '572A2996', 61.71),
    ('1/2000', '572A2967', '572A2985', 61.64),
    ('1/500',  '572A2968', '572A2986', 61.78),
    ('1/125',  '572A2969', '572A2987', 61.71),
    ('1/30',   '572A2970', '572A2988', 61.69),
    ('1/8',    '572A2971', '572A2989', 61.70),
    ('0.5',    '572A2972', '572A2990', 61.71),
]

chan = sys.argv[1] if len(sys.argv) > 1 else 'G1'
box = int(sys.argv[2]) if len(sys.argv) > 2 else 24
order = int(sys.argv[3]) if len(sys.argv) > 3 else 2

rows = []
for exp, fa, fb, dt in PAIRS:
    t = time.time()
    a = ptc.plane(V + fa + '.CR3', chan)
    b = ptc.plane(V + fb + '.CR3', chan)
    dy, dx, pk = ptc.est_shift(a, b)
    if dy or dx:
        b = np.roll(np.roll(b, dy, 0), dx, 1)
        m = 8 + max(abs(dy), abs(dx))
        a2, b2 = a[m:-m, m:-m], b[m:-m, m:-m]
    else:
        a2, b2 = a[8:-8, 8:-8], b[8:-8, 8:-8]
    S, Vr, n, gr = ptc.patch_stats(a2, b2, PED, box=box, order=order)
    for s, v, g in zip(S, Vr, gr):
        rows.append((exp, fa, fb, dt, float(s), float(v), float(g)))
    print(f'{exp:8s} {fa}-{fb} dt={dt:6.2f}s shift=({dy},{dx}) pegats={len(S):6d} '
          f'S=[{S.min():9.1f},{S.max():9.1f}] {time.time()-t:.1f}s', flush=True)

np.save(f'vixen_{chan}_{box}_{order}.npy', np.array([(r[4], r[5], r[6], r[3]) for r in rows]))
with open(f'vixen_{chan}_{box}_{order}_meta.json', 'w') as f:
    json.dump([[r[0], r[1], r[2], r[3]] for r in rows], f)
print('total pegats', len(rows))
