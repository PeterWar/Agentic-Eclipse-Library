"""Sanitat: base Aplicant_Filtres + filtres SF10 (ANELL original inclòs) → ha de coincidir amb el benchmark."""
import os, json, numpy as np, tifffile
D = os.path.dirname(os.path.abspath(__file__)); SF = os.path.join(D, 'sf10')
W, H = 7648, 5353
meta_sf = {m['i']: m for m in json.load(open(os.path.join(SF, 'meta.json')))}
def canvas_rgb(i, m):
    rgb = np.load(os.path.join(SF, f'f{i:02d}_rgb.npy')).astype(np.float32)/65535.0
    s = np.zeros((H, W, 3), np.float32)
    l, t2 = m['left'], m['top']
    hh = min(m['bottom'],H)-max(0,t2); ww = min(m['right'],W)-max(0,l)
    s[max(0,t2):max(0,t2)+hh, max(0,l):max(0,l)+ww] = rgb[max(0,-t2):max(0,-t2)+hh, max(0,-l):max(0,-l)+ww]
    cov = np.zeros((H, W), np.float32); cov[max(0,t2):max(0,t2)+hh, max(0,l):max(0,l)+ww] = 1.0
    return s, cov
def canvas_mask(i, m):
    mk = m.get('mask')
    if mk is None: return np.ones((H, W), np.float32)
    mask = np.load(os.path.join(SF, f'f{i:02d}_mask.npy')).astype(np.float32)/65535.0
    mfull = np.full((H, W), mk['bg']/255.0, np.float32)
    ml, mt2 = mk['left'], mk['top']
    mhh = min(mk['bottom'],H)-max(0,mt2); mww = min(mk['right'],W)-max(0,ml)
    mfull[max(0,mt2):max(0,mt2)+mhh, max(0,ml):max(0,ml)+mww] = mask[max(0,-mt2):max(0,-mt2)+mhh, max(0,-ml):max(0,-ml)+mww]
    return mfull
def blend(comp, s, a, mode):
    if 'LINEAR_LIGHT' in mode: out = np.clip(comp + 2.0*s - 1.0, 0.0, 1.0)
    elif 'OVERLAY' in mode: out = np.where(comp <= 0.5, 2.0*comp*s, 1.0-2.0*(1.0-comp)*(1.0-s))
    else: out = s
    return comp*(1.0-a[...,None]) + out*a[...,None]
comp = tifffile.imread(os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Base/Aplicant_Filtres.tif')).astype(np.float32)/65535.0
for i in [1,2,5,6,7,8,9,10,11,12,13,15]:   # tots els visibles de SF10, ANELL original inclòs
    m = meta_sf[i]
    s, cov = canvas_rgb(i, m)
    comp = blend(comp, s, canvas_mask(i, m)*(m['opacity']/255.0)*cov, m['blend'])
    print('filtre', i, 'aplicat', flush=True)
bm = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif')).astype(np.float32)/65535.0
d = np.abs(comp - bm)*65535.0
print('dif amb benchmark: mediana', float(np.median(d)), 'p99', float(np.percentile(d, 99)), 'p99,99', float(np.percentile(d, 99.99)), 'màx', float(d.max()))
