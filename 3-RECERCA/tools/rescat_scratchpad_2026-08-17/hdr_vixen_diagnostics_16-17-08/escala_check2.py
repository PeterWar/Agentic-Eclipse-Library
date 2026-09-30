import numpy as np, cv2, json
from scipy.ndimage import gaussian_filter, map_coordinates
sk = np.load('sketch_q4.npy')[...,1]; fo = np.load('foto.npy')[...,1]
g = json.load(open('geom.json')); s = g['sketch_q4']
def hp(a, s1=2.0, s2=8.0): return gaussian_filter(a, s1) - gaussian_filter(a, s2)
skh = hp(sk); cxs, cys = s['cx'], s['cy']
Rc = 700
yy, xx = np.mgrid[-Rc:Rc, -Rc:Rc]; rr = np.hypot(xx, yy)
mask = (rr > 1.2*252) & (rr < 3.2*252)
ys, xs = np.mgrid[-Rc:Rc, -Rc:Rc].astype(np.float64)
cache = {}
def fwin(fac):
    if fac not in cache:
        f2 = cv2.resize(fo, None, fx=fac, fy=fac, interpolation=cv2.INTER_AREA)
        fh = hp(f2); cxf, cyf = 3439*fac, 2234*fac
        b = map_coordinates(fh, [ys+cyf, xs+cxf], order=1)
        b = (b - b[mask].mean())*mask; cache[fac] = b/np.sqrt((b**2).sum())
    return cache[fac]
def corr_at(fac, dx, dy):
    b = fwin(fac)
    a = map_coordinates(skh, [ys+cys+dy, xs+cxs+dx], order=1)
    a = (a - a[mask].mean())*mask
    return float((a*b).sum()/np.sqrt((a**2).sum()))
best=None
for fac in [0.5625, 0.565, 0.5675, 0.570, 0.5725]:
    for dy in range(-6, 7, 3):
        for dx in range(-6, 7, 3):
            c = corr_at(fac, dx, dy)
            if best is None or c > best[0]: best = (c, fac, dx, dy)
print('gruixut', best, flush=True)
c0, fac0, dx0, dy0 = best
for step in (1.0, 0.5):
    for fac in np.arange(fac0-0.0025, fac0+0.0026, 0.00125 if step==1.0 else 0.000625):
        fac = round(float(fac), 6)
        for dy in np.arange(dy0-step*2, dy0+step*2.1, step):
            for dx in np.arange(dx0-step*2, dx0+step*2.1, step):
                c = corr_at(fac, dx, dy)
                if c > best[0]: best = (c, fac, float(dx), float(dy))
    c0, fac0, dx0, dy0 = best
    print('pas', step, best, flush=True)
json.dump(dict(corr=best[0], fac_q4=best[1], sol_cx_q4=cxs+best[2], sol_cy_q4=cys+best[3],
               R_sol_q4=446.15*best[1], R_lluna_esperat_q4=460*best[1]), open('escala_sketch.json','w'), indent=1)
print(open('escala_sketch.json').read())
