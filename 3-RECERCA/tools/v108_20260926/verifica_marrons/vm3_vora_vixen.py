"""vm3 (verificador) · Textura fina a banda i banda de la VORA DEL CAMP DE LA VIXEN (suport = vixen_den > 0 del control), abans/després,
a la base_G i al compost amb les màscares de la V107. Textura = MAD del DoG σ2–σ16 del ln per calaixos de distància signada a la vora
(positiu = dins de la Vixen), només r > 3 R☉ i a > 200 px de la vora del llenç. Pas 2 per a la distància. Sortida: VM3_VORA_VIXEN.json."""
import json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/verifica_marrons'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
PI = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'; E = ARREL / '4-RESULTATS/v103_banda_20260926/E'
den = np.asarray(np.load(PI / 'control/vixen_den.npy', mmap_mode='r')[::2, ::2], np.float32) > 0
den = cv2.morphologyEx(den.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
ds = (edt(den) - edt(~den)) * 2; ds = cv2.resize(ds.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
yy, xx = np.mgrid[0:H, 0:W]; rs = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; lliure = (xx > 200) & (yy > 200) & (xx < W - 200) & (yy < H - 200); del yy, xx
def det(X):
    m = (np.isfinite(X) & (X > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(X, 1e-12)), 0).astype(np.float32)
    ng = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    return np.where(cv2.erode(m, np.ones((41, 41), np.uint8)) > 0, ng(2) - ng(16), np.nan)
res = {}
for nom, fa, fb in (('base_G', E / 'lineal_v103/base_G.npy', PI / 'lineal_v108/base_G.npy'), ('compost', PI / 'compost_v107mascares_abans.npy', PI / 'compost_v107mascares_despres.npy')):
    A = det(np.asarray(np.load(fa, mmap_mode='r'), np.float32)); B = det(np.asarray(np.load(fb, mmap_mode='r'), np.float32)); r = {}
    for a_, b_ in ((-900, -600), (-600, -300), (-300, -100), (-100, 0), (0, 100), (100, 300), (300, 600), (600, 900), (900, 1500)):
        k = (ds >= a_) & (ds < b_) & (rs > 3) & lliure & np.isfinite(A) & np.isfinite(B)
        if k.sum() < 2e4: continue
        ma = float(1.4826 * np.median(np.abs(A[k] - np.median(A[k])))); mb = float(1.4826 * np.median(np.abs(B[k] - np.median(B[k]))))
        r[f'{a_}..{b_}'] = dict(n=int(k.sum()), abans=ma, despres=mb)
    fora = [v for k_, v in r.items() if k_.startswith('-9') or k_.startswith('-6')]; dins = [v for k_, v in r.items() if k_.startswith('600') or k_.startswith('900')]
    fa_ = np.mean([v['abans'] for v in fora]); fb_ = np.mean([v['despres'] for v in fora]); da_ = np.mean([v['abans'] for v in dins]); db_ = np.mean([v['despres'] for v in dins])
    r['dins_sobre_fora'] = dict(abans=float(da_ / fa_ - 1), despres=float(db_ / fb_ - 1)); res[nom] = r
    print(nom, json.dumps(r, ensure_ascii=False), flush=True)
(OUT / 'VM3_VORA_VIXEN.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
