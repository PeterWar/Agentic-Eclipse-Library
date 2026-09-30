"""Perfils radials i estructura azimutal de les màscares de CapesExteriors; contingut d'EDITAT PERE al disc lunar; mapa de la dif interior."""
import os, json, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); EXT = os.path.join(D, 'ext')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 446.15
LLUNA = (4034.7, 2736.7); R_LL = 452.5
meta = json.load(open(os.path.join(EXT, 'meta.json')))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / R_SOL
r_ll = np.hypot(xx - LLUNA[0], yy - LLUNA[1])
th = np.degrees(np.arctan2(yy - SOL[1], xx - SOL[0]))

def mask_canvas(i, m):
    mk = m.get('mask')
    if mk is None: return None
    mask = np.load(os.path.join(EXT, f'capa{i:02d}_mask.npy')).astype(np.float32)/65535.0
    mfull = np.full((H, W), mk['bg']/255.0, np.float32)
    ml, mt2 = mk['left'], mk['top']
    msy0, msx0 = max(0,-mt2), max(0,-ml)
    mdy0, mdx0 = max(0,mt2), max(0,ml)
    mhh = min(mk['bottom'],H)-mdy0; mww = min(mk['right'],W)-mdx0
    mfull[mdy0:mdy0+mhh, mdx0:mdx0+mww] = mask[msy0:msy0+mhh, msx0:msx0+mww]
    return mfull

RS = [0.98, 1.05, 1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0]
for m in meta:
    mf = mask_canvas(m['i'], m)
    if mf is None:
        print(f"capa {m['i']} '{m['nom'][:45]}': SENSE màscara"); continue
    prof = []; azim = []
    for r0 in RS:
        sel = (r >= r0-0.04) & (r < r0+0.04)
        v = mf[sel]
        prof.append(f"{np.mean(v):.2f}")
        # desviació azimutal: std de les mitjanes per sectors de 15°
        tt = th[sel]; mm = []
        for a0 in range(-180, 180, 15):
            s2 = (tt >= a0) & (tt < a0+15)
            if s2.sum() > 50: mm.append(np.mean(v[s2]))
        azim.append(f"{np.std(mm):.2f}" if len(mm)>3 else "--")
    dins_lluna = mf[r_ll < 380].mean()
    vora_lluna = mf[(r_ll >= 440) & (r_ll < 480)].mean()
    print(f"capa {m['i']} '{m['nom'][:45]}' op={m['opacity']} vis={m['visible']}")
    print(f"   perfil (r={RS}): {prof}")
    print(f"   azim std 15°:    {azim}")
    print(f"   dins Lluna (r_ll<380): {dins_lluna:.3f} | anell limbe 440-480: {vora_lluna:.3f}")

# On és la diferència interior compost-base?
import tifffile
comp = np.load(os.path.join(D, 'compost_exteriors.npy'), mmap_mode='r')
base = tifffile.imread(os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Base/Aplicant_Filtres.tif'))
y0,y1,x0,x1 = 2000,3500,3300,4800  # regió del Sol
d = np.abs(comp[y0:y1,x0:x1].astype(np.int32) - base[y0:y1,x0:x1].astype(np.int32)).max(axis=2)
big = d > 300
print('\npíxels amb dif>300 u16 a la regió solar:', int(big.sum()))
if big.sum():
    ys, xs2 = np.nonzero(big)
    print('  bbox:', ys.min()+y0, ys.max()+y0, xs2.min()+x0, xs2.max()+x0)
    rr = r[y0:y1,x0:x1][big]; print('  radis solars: min', round(float(rr.min()),2), 'max', round(float(rr.max()),2), 'mediana', round(float(np.median(rr)),2))
    rl = r_ll[y0:y1,x0:x1][big]; print('  radis lunars px: min', int(rl.min()), 'max', int(rl.max()), 'mediana', int(np.median(rl)))
# contingut d'EDITAT PERE dins la Lluna vs 03_1s
c3 = np.load(os.path.join(EXT, 'capa03_rgb.npy'), mmap_mode='r')
c0 = np.load(os.path.join(EXT, 'capa00_rgb.npy'), mmap_mode='r')
selL = r_ll < 380
med3 = np.median(np.asarray(c3[2350:3150, 3600:4500]).reshape(-1,3)[selL[2350:3150,3600:4500].ravel()], axis=0)
print('\nEDITAT PERE dins la Lluna (mediana RGB u16):', med3.astype(int))
