"""A1b · El mateix que A1 per als subplans R i B (per a la cura per canal).

Sortida: cau/{tren}_R_w.npy, cau/{tren}_R_v.npy, cau/{tren}_B_w.npy, cau/{tren}_B_v.npy
(la G ja és a {tren}_w.npy / {tren}_v.npy). Només lectura sobre RAW i runs.
"""
from comu32 import *

def main():
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
    xc, yc = coarse_coords(); XX, YY = np.meshgrid(xc, yc)
    qx = (inv[0, 0] * XX + inv[0, 1] * YY + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * XX + inv[1, 1] * YY + inv[1, 2]).astype(np.float32)
    for tag in ('sony', 'vixen'):
        path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
        pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; names = sorted(pos)
        meta = json.loads((CAU32 / f'{tag}_meta.json').read_text())['frames']; assert [m['name'] for m in meta] == names
        outs = {}
        for c, sub in (('R', 0), ('B', 2)):
            outs[c] = (np.lib.format.open_memmap(CAU32 / f'{tag}_{c}_w.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC)),
                       np.lib.format.open_memmap(CAU32 / f'{tag}_{c}_v.npy', mode='w+', dtype=np.float32, shape=(len(names), HC, WC)), sub)
        dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k; t0 = time.time()
        for j, n in enumerate(names):
            v = pos[n]
            rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
            lunar = f2.mascara_lluna(ctx, v, rx, ry); plans = ctx.plans(n, v['exp'])
            for c, (Wm, Vm, sub) in outs.items():
                pl, w = plans[sub]; oy, ox = ctx.orig[sub]
                mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                nn = cv2.remap(pl * w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * lunar
                Wm[j] = dd; Vm[j] = np.where(dd > 0, nn / np.maximum(dd, 1e-20), np.nan)
            if j % 10 == 0 or j == len(names) - 1:
                log(f'{tag} R/B {j+1}/{len(names)} ({time.time()-t0:.0f}s)')
        for c, (Wm, Vm, sub) in outs.items():
            Wm.flush(); Vm.flush()
        del ctx
    log('A1b fet')

if __name__ == '__main__':
    main()
