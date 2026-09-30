"""(1) Limbe lunar per capa (la Lluna es mou entre exposicions). (2) Diff de les màscares editades contra les lliurades.
(3) Perfils del compost del V4 editat amb i sense 04/03, i de les capes 04/03, per dissenyar les màscares noves."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta4 = json.load(open('v5in/meta.json')); meta3 = json.load(open('v3/meta.json'))
files3 = sorted(glob.glob('v3/*_rgb.npy')); files3 = [f for f in files3 if 'merged' not in f]
SUN = (4020.89, 2737.66); RS = 446.15    # geometria V4/V5 (18-08)
# correspondència capa V4-editat → npy de V3 i offset: doc (x,y) → npy[y+oy, x+ox]
# idx: (fitxer v3, ox, oy)   [npy indexat per contingut de capa V3 sencera]
MAP = {0: (0, -456, -462), 1: (0, -457, -463), 2: (1, 0, 0), 3: (2, 0, 0), 4: (3, -458, -464),
       5: (3, -458, -464), 6: (4, -458, -464), 7: (5, -458, -464), 8: (6, -458, -464), 9: (7, -458, -464), 10: (8, -458, -464), 11: (9, -458, -464)}
# (les 5..11 són retallades a (457,463): doc(x,y) → capa retallada (y-463, x-457) = npy_v3[y-463 + 1, x-457 + 1] per t0=464,l0=458 → oy=-462?? comprovem: contingut retallat = npy[464-t0v3 : ...]; per DNG t0v3=464 → files 0.. de la retallada = npy files 0.. → doc y=463 → fila 0 → npy fila 0 → oy = -463+ (464-464) = -463. Per npy indexat 0.. la retallada començava a npy[0] posada a doc 463 → npy[y-463]. Amb el marc [464..5104) de V3: la retallada = npy[464-t0v3=0 : 4640, 458-l0v3=0 : 6960]. OK: doc(x,y)→npy[y-463, x-457].)
for k in (5, 6, 7, 8, 9, 10, 11): MAP[k] = (MAP[k][0], -457, -463)
def limb_fit(j3, t_lab):
    a = np.load(files3[j3], mmap_mode='r'); l0, t0 = meta3['layers'][j3]['bbox'][:2]
    rr = np.arange(0.90, 1.10, 0.0005); th = np.deg2rad(np.arange(0, 360, 1.0))
    R, T = np.meshgrid(rr, th, indexing='ij')
    X = (SUN[0] + 1) + R * RS * np.cos(T); Y = (SUN[1] + 1) - R * RS * np.sin(T)   # coords doc V3
    G = ndi.map_coordinates(np.asarray(a[..., 1], np.float32) / 65535., [Y - t0, X - l0], order=1)
    Lg = np.log(np.maximum(G, 1e-4)); Gr = np.gradient(ndi.gaussian_filter1d(Lg, 4, axis=0), axis=0)
    j0, j1 = int((0.93 - 0.9) / 0.0005), int((1.06 - 0.9) / 0.0005)
    jm = j0 + np.argmax(Gr[j0:j1], axis=0); rl = rr[jm]
    x = (SUN[0] + 1) + rl * RS * np.cos(th); y = (SUN[1] + 1) - rl * RS * np.sin(th)
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]; b = x * x + y * y
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + cx * cx + cy * cy)
    res = np.hypot(x - cx, y - cy) - r; ok = np.abs(res) < 2.5 * res.std()
    A2 = A[ok]; b2 = b[ok]; cx, cy, c = np.linalg.lstsq(A2, b2, rcond=None)[0]; r = np.sqrt(c + cx * cx + cy * cy)
    print(f'limbe {t_lab:14s}: centre V5-doc ({cx-1:.1f}, {cy-1:.1f}) radi {r:.1f} px  (residu {res[ok].std():.1f})')
    return cx - 1, cy - 1, r
print('== limbe lunar per capa (cada exposició té la Lluna al seu lloc):')
limbs = {}
for j3, lab in ((0, '12 1/3200'), (1, 'C4 1/500'), (2, 'C5 1/125'), (3, '09 1/60'), (4, '08 1/30'), (5, '07 1/15'), (6, '06 1/8'), (7, '05 1/4'), (8, '04 1/2'), (9, '03 1s')):
    limbs[j3] = limb_fit(j3, lab)
json.dump({str(k): [float(v) for v in vv] for k, vv in limbs.items()}, open('v5in/limbs.json', 'w'))
# (2) diff de màscares editades vs lliurades (les lliurades: v5/masks/{i}_mask.npy, i=1..9 → capes 5..11 i 2,3? mapa: lliurada i=1→Capa4(idx2), 2→Capa5(idx3), 3→09(idx5), 4→08(idx6), 5→07(idx7), 6→06(idx8), 7→05(idx9), 8→04(idx10), 9→03(idx11))
print('\n== on ha actuat Pere (diff màscara editada − lliurada, valors 0..1):')
pair = {2: 1, 3: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9}
for idx4, i5 in pair.items():
    info = meta4['layers'][idx4]
    if info['mask'] is None: continue
    mb = info['mask']['bbox']
    ed = np.load(f'v5in/{idx4:02d}_mask.npy', mmap_mode='r')
    old = np.load(f'v5/masks/{i5:02d}_mask.npy', mmap_mode='r')
    # la lliurada és el marc (4640×6960) a (457,463); l'editada pot tenir un altre bbox
    if idx4 in (2, 3):
        # Capa 1/2: màscara al llenç sencer; la lliurada de Capa4/5 era al marc
        sub = np.asarray(ed[463:5103, 457:7417], np.float32) / 65535.
    else:
        y0, x0 = 463 - mb[1], 457 - mb[0]
        sub = np.asarray(ed[y0:y0 + 4640, x0:x0 + 6960], np.float32) / 65535.
    d = sub - np.asarray(old, np.float32) / 65535.
    n = (np.abs(d) > 0.02).sum()
    print(f'  capa {idx4:2d} ({info["name"][:20]:20s}): píxels canviats (>2 %): {n:8d}  ({n/d.size*100:.2f} %)  màx |Δ| {np.abs(d).max():.2f}  mitjana Δ {d.mean():+.4f}')
    if n: np.save(f'v5in/diff_{idx4:02d}.npy', d.astype(np.float32))
