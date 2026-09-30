import numpy as np, ptc2, json, sys, time, os

CFG = {
    'vixen': dict(dirn='/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/', ext='.CR3', ped=512.0,
                  pairs=[
                      ('1/3200', '572A2936', '572A2937', 0.73), ('1/3200', '572A2938', '572A2939', 0.65),
                      ('1/3200', '572A2940', '572A2941', 0.65), ('1/3200', '572A2944', '572A2945', 0.65),
                      ('1/3200', '572A2950', '572A2951', 0.65), ('1/3200', '572A2958', '572A2959', 0.65),
                      ('1/3200', '572A3020', '572A3021', 0.65), ('1/3200', '572A3030', '572A3031', 0.65),
                      ('1/2000', '572A2997', '572A3003', 6.06), ('1/500', '572A2998', '572A3004', 6.06),
                      ('1/125', '572A2999', '572A3005', 6.06), ('1/30', '572A3000', '572A3006', 6.07),
                      ('1/8', '572A3001', '572A3007', 6.07), ('0.5', '572A3002', '572A3008', 6.07),
                      ('2', '572A2979', '572A2980', 2.90), ('2', '572A2980', '572A2981', 2.91),
                      ('10.3', '572A2982', '572A2983', 13.07), ('10.3', '572A2983', '572A2984', 13.40),
                      ('1/1000', '572A2973', '572A2991', 61.71), ('1/250', '572A2974', '572A2992', 61.71),
                      ('1/60', '572A2975', '572A2993', 61.71), ('1/15', '572A2976', '572A2994', 61.71),
                      ('1/4', '572A2977', '572A2995', 61.71), ('1', '572A2978', '572A2996', 61.71),
                      ('1/320f', '572A3057', '572A3058', 29.85), ('1/320f', '572A3058', '572A3059', 29.85),
                  ]),
    'sony': dict(dirn='/Users/USUARI/Desktop/Eclipse 2026/300mm/', ext='.ARW', ped=512.0,
                 pairs=[
                     ('1/800', 'DSC06973', 'DSC06976', 3.0), ('1/800', 'DSC06976', 'DSC06979', 3.0),
                     ('1/6400', 'DSC06974', 'DSC06977', 3.0), ('1/6400', 'DSC06977', 'DSC06980', 3.0),
                     ('1/100', 'DSC06975', 'DSC06978', 3.0), ('1/100', 'DSC06978', 'DSC06981', 3.0),
                     ('1/800', 'DSC07000', 'DSC07003', 4.0), ('1/6400', 'DSC07001', 'DSC07004', 4.0),
                     ('1/100', 'DSC07002', 'DSC07005', 4.0),
                     ('1/4', 'DSC06994', 'DSC06997', 5.0), ('1/30', 'DSC06995', 'DSC06998', 5.5),
                     ('2', 'DSC06996', 'DSC06999', 5.5),
                     ('1/4', 'DSC06982', 'DSC06994', 64.0), ('1/30', 'DSC06983', 'DSC06995', 64.0),
                     ('2', 'DSC06984', 'DSC06996', 64.0),
                     ('1', 'DSC06985', 'DSC06988', 17.0), ('1', 'DSC06988', 'DSC06991', 17.0),
                     ('1/8', 'DSC06986', 'DSC06989', 17.0), ('1/8', 'DSC06989', 'DSC06992', 16.0),
                     ('8', 'DSC06987', 'DSC06993', 33.0),
                     ('1/1000', 'DSC06952', 'DSC06953', 2.0), ('1/1000', 'DSC06951', 'DSC06952', 2.0),
                     ('1/1000', 'DSC06955', 'DSC06956', 3.0), ('1/1000', 'DSC06939', 'DSC06940', 2.0),
                     ('1/1000', 'DSC06940', 'DSC06941', 2.0),
                     ('1/500', 'DSC07104', 'DSC07105', 30.0), ('1/500', 'DSC07108', 'DSC07109', 30.0),
                     ('1/400f', 'DSC07082', 'DSC07083', 29.0), ('1/400f', 'DSC07090', 'DSC07091', 30.0),
                 ]),
}

which = sys.argv[1]
chan = sys.argv[2] if len(sys.argv) > 2 else 'G1'
box = int(sys.argv[3]) if len(sys.argv) > 3 else 24
order = int(sys.argv[4]) if len(sys.argv) > 4 else 2
c = CFG[which]

rows = []
info = []
for exp, fa, fb, dt in c['pairs']:
    pa, pb = c['dirn'] + fa + c['ext'], c['dirn'] + fb + c['ext']
    if not (os.path.exists(pa) and os.path.exists(pb)):
        print('FALTA', fa, fb); continue
    t = time.time()
    a = ptc2.plane(pa, chan); b = ptc2.plane(pb, chan)
    sh, ctr = ptc2.measure_shift(a, b, c['ped'])
    dy, dx = int(round(sh[0])), int(round(sh[1]))
    if dy or dx:
        b = np.roll(np.roll(b, dy, 0), dx, 1)
    m = 8 + max(abs(dy), abs(dx))
    a2, b2 = a[m:-m, m:-m], b[m:-m, m:-m]
    S, V, Vm, St = ptc2.patch_table(a2, b2, c['ped'], box=box, order=order)
    k = len(rows)
    rows.append(np.stack([S, V, Vm, St, np.full(len(S), len(info), float)], 1))
    resid = np.hypot(sh[0] - dy, sh[1] - dx)
    info.append(dict(exp=exp, a=fa, b=fb, dt=dt, shift=sh, resid=resid, n=int(len(S))))
    print(f'{exp:8s} {fa}-{fb} dt={dt:6.1f} shift=({sh[0]:+6.2f},{sh[1]:+6.2f}) resid={resid:.2f} '
          f'pegats={len(S):6d} S=[{S.min():9.1f},{S.max():9.1f}] {time.time()-t:.1f}s', flush=True)

D = np.concatenate(rows)
np.save(f'{which}_{chan}_{box}_{order}.npy', D)
json.dump(info, open(f'{which}_{chan}_{box}_{order}.json', 'w'))
print('total', len(D))
