"""A1 (V34) · Pes i valor de CADA fotograma (G, R i B) al llenç final, a 1/4 de resolució, amb la finestra V34 i la linealitat Sony.

Reprodueix, fotograma a fotograma, el que `prepare_final_grid.py` suma: el
subpla G calibrat (per segon, balancejat), la finestra de pes LDIC `f2.finestra`
(x t_exp), la validesa del sensor i la màscara lunar del fotograma, remostrejats
amb el mateix registre (F1.3) a la graella final de la V29/V31. No aplica k ni
els offsets del c03: es guarden a part a la meta perquè la diagnosi els pugui
posar o treure.

Sortida (memmap, float32, (n_fotogrames, 1877, 2638)):
  cau/{tren}_w.npy   Σ pes dels dos subplans G (amb màscara lunar)
  cau/{tren}_v.npy   valor G calibrat del fotograma (mitjana ponderada dels dos G)
  cau/{tren}_meta.json
Només lectura sobre RAW, runs i rebuts. Cap PSB.
"""
from comu34 import *

def main():
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
    xc, yc = coarse_coords()
    XX, YY = np.meshgrid(xc, yc)
    qx = (inv[0, 0] * XX + inv[0, 1] * YY + inv[0, 2]).astype(np.float32)
    qy = (inv[1, 0] * XX + inv[1, 1] * YY + inv[1, 2]).astype(np.float32)
    offsets = load_offsets()
    for tag in ('sony', 'vixen'):
        path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
        pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']
        kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
        names = sorted(pos); groups = frame_groups(tag, names)
        Wm = np.lib.format.open_memmap(CAU34 / f'{tag}_w.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC))
        Vm = np.lib.format.open_memmap(CAU34 / f'{tag}_v.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC))
        RB = {c: (np.lib.format.open_memmap(CAU34 / f'{tag}_{c}_w.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC)), np.lib.format.open_memmap(CAU34 / f'{tag}_{c}_v.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC)), sub) for c, sub in (('R', 0), ('B', 2))}
        dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
        meta = []
        t0 = time.time()
        for j, n in enumerate(names):
            v = pos[n]
            rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32)
            ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
            lunar = f2.mascara_lluna(ctx, v, rx, ry)
            num = np.zeros((HC, WC), np.float32); den = np.zeros((HC, WC), np.float32)
            plans = ctx.plans(n, v['exp'])
            for i in (1, 3):                      # els dos subplans G
                pl, w = plans[i]; oy, ox = ctx.orig[i]
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                nn = cv2.remap(pl * w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                num += nn; den += dd
            Wm[j] = den
            Vm[j] = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan)
            for c, (Wc, Vc, sub) in RB.items():          # R i B en la mateixa passada (a1b de la V32)
                pl, w = plans[sub]; oy, ox = ctx.orig[sub]
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                nn = cv2.remap(pl * w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                Wc[j] = dd; Vc[j] = np.where(dd > 0, nn / np.maximum(dd, 1e-20), np.nan)
            g = groups[n]
            b = offsets['groups'][g]['offsets'].get(n, [0, 0, 0])
            meta.append({'i': j, 'name': n, 'group': g, 'exp': v['exp'], 't': v['t'],
                         'k': kq.get(n, 1.0), 'offset_G': float(b[1]), 'offset_RGB': b,
                         'sol_xy_sensor': [v['sol_x'], v['sol_y']], 'font_registre': v.get('font'),
                         'w_max': float(den.max()), 'coverage_cells': int((den > 0).sum())})
            log(f'{tag} {j+1}/{len(names)} {n} exp {v["exp"]} wmax {den.max():.3f} ({time.time()-t0:.0f}s)')
        Wm.flush(); Vm.flush()
        for Wc, Vc, _ in RB.values():
            Wc.flush(); Vc.flush()
        savejson(CAU34 / f'{tag}_meta.json', {'tren': tag, 'run': str(path), 'Q': Q, 'shape': [HC, WC],
                 'canal': 'G (subplans 1 i 3, mitjana ponderada pel pes)', 'pes': 'finestra V34 (sostre gradual 0,35→0,85 sat) x t_exp x validesa x màscara lunar; sense k', 'canvis_v34': REP_CANVIS,
                 'valor': 'comu.calibra_pla: per segon, balanç de dia; sense k ni offset c03', 'frames': meta,
                 'sensor_k_llenc': ctx.k, 'pa_north_deg': ctx.LL['pa_north_deg']})
        del Wm, Vm, ctx
    log('A1 fet')

if __name__ == '__main__':
    main()
