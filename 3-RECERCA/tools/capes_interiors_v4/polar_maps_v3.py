"""Mapes polars: màscares, pesos efectius, compost V3 (reproduït) i compost amb pesos només radials; i el quocient = estructura fabricada per les màscares."""
import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
d = np.load('v3/polar.npz'); meta = json.load(open('v3/meta.json'))
rr = d['rr']; th = d['th']; nL = len(meta['layers'])
L = [d[f'L{i}'] for i in range(nL)]               # (3, nr, nth)
M = [d[f'M{i}'] if f'M{i}' in d else np.ones_like(L[0][0]) for i in range(nL)]
vis = [meta['layers'][i]['visible'] for i in range(nL)]
def compose(masks):
    C = np.zeros_like(L[0])
    for i in range(nL):
        if not vis[i]: continue
        a = masks[i][None]
        C = C * (1 - a) + L[i] * a        # la base (capa 0) no té màscara → a=1: la substitueix
    return C
def eff_weights(masks):
    W = []
    rem = np.ones_like(L[0][0])
    for i in reversed(range(nL)):
        if not vis[i]:
            W.append(np.zeros_like(rem)); continue
        W.append(masks[i] * rem); rem = rem * (1 - masks[i])
    return W[::-1]
C3 = compose(M)
W3 = eff_weights(M)
Mbar = [np.repeat(np.nanmean(m, axis=1, keepdims=True), m.shape[1], axis=1) for m in M]
Cr = compose(Mbar)
lum = lambda C: 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
Q = lum(C3) / np.maximum(lum(Cr), 1e-4)
np.savez_compressed('v3/polar_compost.npz', C3=C3, Cr=Cr, Q=Q, W3=np.array(W3))
# estadística del quocient per radi
print('r     mitjana Q   desv Q (az)   p5    p95   | desv az del log-lum V3 i del radial (estructura total vs real)')
for r in [1.02, 1.05, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0, 2.3, 2.6, 3.0, 3.5]:
    j = int(round((r - 0.90) / 0.005)); q = Q[j]
    l3 = np.log(np.maximum(lum(C3)[j], 1e-4)); lr = np.log(np.maximum(lum(Cr)[j], 1e-4))
    print(f'{r:4.2f}  {q.mean():8.3f}  {q.std():8.3f}  {np.percentile(q,5):6.3f} {np.percentile(q,95):6.3f}   | {l3.std():.3f}  {lr.std():.3f}')
# imatges polars: files = r (de 0,9 a 4), columnes = θ
def to_img(a, lo=None, hi=None, gamma=1.0):
    a = np.asarray(a, np.float64)
    lo = np.nanpercentile(a, 0.5) if lo is None else lo; hi = np.nanpercentile(a, 99.5) if hi is None else hi
    x = np.clip((a - lo) / (hi - lo + 1e-12), 0, 1) ** gamma
    return (x * 255).astype(np.uint8)
rows = []
def strip(img, label):
    im = Image.fromarray(img).convert('RGB')
    from PIL import ImageDraw
    ImageDraw.Draw(im).text((4, 2), label, fill=(255, 255, 0))
    return im
# màscares
for i in range(nL):
    if f'M{i}' in d:
        rows.append(strip(to_img(M[i], 0, 1), f'màscara {meta["layers"][i]["name"][:22]}  (r 0,90→4,0 de dalt a baix, θ 0→360)'))
rows.append(strip(to_img(np.log(np.maximum(lum(C3), 1e-4))), 'log lum compost V3'))
rows.append(strip(to_img(np.log(np.maximum(lum(Cr), 1e-4))), 'log lum compost amb màscares radials (mitjana az.)'))
rows.append(strip(to_img(Q, 0.7, 1.3), 'quocient V3 / radial (0,7 → 1,3)'))
Wt = np.array(W3)
for i in range(nL):
    if vis[i] and Wt[i].max() > 0.01:
        rows.append(strip(to_img(Wt[i], 0, 1), f'pes efectiu {meta["layers"][i]["name"][:22]}'))
Wd = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows:
    Wd.paste(r, (0, y)); y += r.height
Wd.save('v3/polar_maps.png'); print(Wd.size)
