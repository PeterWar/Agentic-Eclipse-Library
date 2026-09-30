"""QA d'una variant del prototip CapesTotals contra el benchmark (SF10) i contra V5 pura.
Ús: qa_ct1.py compost_<variant>.npy"""
import os, sys, numpy as np, tifffile
from scipy.ndimage import gaussian_filter1d
D = os.path.dirname(os.path.abspath(__file__))
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 446.15; LLUNA = (4034.7, 2736.7)
PROT = (3578, 2653)  # el·lipse guarda protuberància (90x110, rampa 50)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx-SOL[0], yy-SOL[1])/R_SOL
r_ll = np.hypot(xx-LLUNA[0], yy-LLUNA[1])
cand = np.load(os.path.join(D, sys.argv[1]), mmap_mode='r')
bm = tifffile.imread(os.path.expanduser('~/Downloads/Benchmark20Agost.tif'))
import os as _os
v5 = np.load(_os.environ.get('CT1_V5REF', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/47c293ed-2e8a-4c78-a543-00c84f771077/scratchpad/v5out/compost_rgb16.npy'), mmap_mode='r')
nom = sys.argv[1]
print('=====', nom, '=====')
lum = lambda a: (np.asarray(a[...,0],np.float32)+np.asarray(a[...,1],np.float32)+np.asarray(a[...,2],np.float32))/(3*65535.0)

# 1. test d'anells: residu rms de la mediana azimutal contra el seu suavitzat (per trams)
def test_anells(img, r0=1.09, r1=8.5):
    rb = np.arange(r0, r1, 0.01); rcx = 0.5*(rb[:-1]+rb[1:])
    L = lum(img)
    idx = np.digitize(r.ravel(), rb)-1
    Lf = L.ravel()
    med = np.full(len(rb)-1, np.nan, np.float32)
    for k in range(len(rb)-1):
        s = idx == k
        if s.sum() > 200: med[k] = np.median(Lf[s])
    ok = ~np.isnan(med)
    sm = gaussian_filter1d(med[ok], 8.0, mode='nearest')
    resid = (med[ok]-sm)/np.maximum(sm, 1e-4)
    return float(np.sqrt(np.mean(resid**2))), rcx[ok], med[ok], sm

ta_c, rcx, med_c, sm_c = test_anells(cand)
ta_b, _, med_b, sm_b = test_anells(bm)
print(f'test anells 1,09-8,5 R☉ (rms residu): candidat {ta_c*100:.3f} %  | benchmark {ta_b*100:.3f} %')

# 2. guardes: diferència amb V5 pura
def zona(nomz, sel):
    dc = np.abs(np.asarray(cand[sel], np.int32) - np.asarray(v5[sel], np.int32)).max(axis=-1)
    db = np.abs(np.asarray(bm[sel], np.int32) - np.asarray(v5[sel], np.int32)).max(axis=-1)
    print(f'  {nomz:34s} n={sel.sum():7d}  cand-V5: med {np.median(dc):6.0f} p99 {np.percentile(dc,99):7.0f} | bench-V5: med {np.median(db):6.0f}')
print('guardes (unitats u16; el candidat hauria de ser MOLT més a prop de V5 que el benchmark):')
ell = (((xx-PROT[0])/140.0)**2 + ((yy-PROT[1])/160.0)**2) < 1.0
zona('protuberància (el·lipse ampla)', ell)
zona('limbe lunar (r_ll 440-485)', (r_ll>=440)&(r_ll<485))
zona('perles/creixent (r 0,95-1,08)', (r>=0.95)&(r<1.08))
zona('dins la Lluna (r_ll<420)', r_ll<420)

# 3. diferència amb el benchmark per anells
print('diferència candidat-benchmark per anells (mediana |dif| u16 / lum mediana):')
for r0 in [1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0,6.0,8.0,10.0]:
    sel = (r>=r0)&(r<r0+0.5)
    d = np.abs(np.asarray(cand[sel],np.int32)-np.asarray(bm[sel],np.int32)).max(axis=-1)
    print(f'  r {r0:4.1f}: med {np.median(d):6.0f}  p99 {np.percentile(d,99):7.0f}')

# 4. estructura azimutal per anell (rms del residu de lum vs mediana de l'anell): més = més estructura
print('estructura azimutal (rms residu lum per anell, x1000): cand | bench')
Lc = lum(cand); Lb = lum(bm)
for r0 in [1.1,1.3,1.6,2.0,2.5,3.0,4.0,5.0]:
    sel = (r>=r0-0.05)&(r<r0+0.05)
    sc = np.std(Lc[sel]); sb = np.std(Lb[sel])
    print(f'  r {r0:3.1f}: {sc*1000:6.1f} | {sb*1000:6.1f}')
