"""Compon la cadena de CapesExteriors (en espai codificat, com Photoshop) i compara amb Aplicant_Filtres.tif."""
import os, json, time, numpy as np, tifffile
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
D = os.path.dirname(os.path.abspath(__file__)); EXT = os.path.join(D, 'ext')
W, H = 7648, 5353
SOL = (4021.35, 2737.90); R_SOL = 446.15
meta = json.load(open(os.path.join(EXT, 'meta.json')))

def canvas_layer(i, m):
    rgb = np.load(os.path.join(EXT, f'capa{i:02d}_rgb.npy')).astype(np.float32) / 65535.0
    l, t, r, b = m['left'], m['top'], m['right'], m['bottom']
    s = np.zeros((H, W, 3), np.float32); cov = np.zeros((H, W), np.float32)
    # retalla el bbox al llenç
    sy0, sx0 = max(0, -t), max(0, -l)
    dy0, dx0 = max(0, t), max(0, l)
    hh = min(b, H) - dy0; ww = min(r, W) - dx0
    s[dy0:dy0+hh, dx0:dx0+ww] = rgb[sy0:sy0+hh, sx0:sx0+ww]
    cov[dy0:dy0+hh, dx0:dx0+ww] = 1.0
    a = cov.copy()
    mk = m.get('mask')
    if mk is not None:
        mask = np.load(os.path.join(EXT, f'capa{i:02d}_mask.npy')).astype(np.float32) / 65535.0
        mfull = np.full((H, W), mk['bg']/255.0, np.float32)
        ml, mt2, mr, mb = mk['left'], mk['top'], mk['right'], mk['bottom']
        msy0, msx0 = max(0, -mt2), max(0, -ml)
        mdy0, mdx0 = max(0, mt2), max(0, ml)
        mhh = min(mb, H) - mdy0; mww = min(mr, W) - mdx0
        mfull[mdy0:mdy0+mhh, mdx0:mdx0+mww] = mask[msy0:msy0+mhh, msx0:msx0+mww]
        a = a * mfull
    a = a * (m['opacity'] / 255.0)
    return s, a, cov

comp = np.zeros((H, W, 3), np.float32); covtot = np.zeros((H, W), np.float32)
for m in meta:
    if not m['visible']:
        log(f"capa {m['i']} OCULTA, saltada:", m['nom'][:50]); continue
    s, a, cov = canvas_layer(m['i'], m)
    if 'LINEAR_LIGHT' in m['blend']:
        ll = np.clip(comp + 2.0*s - 1.0, 0.0, 1.0)
        comp = comp*(1.0 - a[...,None]) + ll*a[...,None]
    else:
        comp = comp*(1.0 - a[...,None]) + s*a[...,None]
        covtot = np.maximum(covtot, a)
    log(f"capa {m['i']} composta ({m['blend']}, op={m['opacity']}):", m['nom'][:50])
np.save(os.path.join(D, 'compost_exteriors.npy'), np.clip(np.rint(comp*65535),0,65535).astype(np.uint16))
log('compost desat')
base = tifffile.imread(os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Base/Aplicant_Filtres.tif')).astype(np.float32)/65535.0
log('base llegida', base.shape)
dif = comp - base
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / R_SOL
print('\n== |dif| per anell (mediana, p99) — tot el llenç ==')
for r0 in [0.0,0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0,6.0,7.0,8.0,9.0,10.0]:
    sel = (r >= r0) & (r < r0+0.5)
    if sel.sum() == 0: continue
    d = np.abs(dif[sel]).ravel()
    print(f'r {r0:4.1f}–{r0+0.5:4.1f} R☉: mediana {np.median(d)*65535:7.1f}  p99 {np.percentile(d,99)*65535:8.1f}  (u16)')
print('\n== cantonades (300x300) ==')
for nom,(y0,x0) in {'TL':(0,0),'TR':(0,W-300),'BL':(H-300,0),'BR':(H-300,W-300)}.items():
    d = np.abs(dif[y0:y0+300, x0:x0+300])
    print(f'{nom}: mediana {np.median(d)*65535:7.1f}  p99 {np.percentile(d,99)*65535:8.1f}')
print('\n== cobertura Normal < 0,999 ==', int((covtot < 0.999).sum()), 'px')
