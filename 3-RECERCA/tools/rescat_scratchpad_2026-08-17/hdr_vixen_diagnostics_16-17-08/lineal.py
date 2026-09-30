import numpy as np, json, math
OUT='/Users/USUARI/Desktop/Eclipse 2026/Corona_HDR_Vixen/'
hdr = np.load(OUT+'hdr_vixen_countss.npy', mmap_mode='r')
H, W, _ = hdr.shape; cy, cx = H/2.0, W/2.0
R_SOL = 446.15
RETALL = (85, 4595, 40, 6830)
G = np.array(hdr[...,1]); R = np.array(hdr[...,0])
valid = np.isfinite(G) & np.isfinite(R)
caixa = np.zeros_like(valid); caixa[RETALL[0]:RETALL[1]+1, RETALL[2]:RETALL[3]+1] = True
valid &= caixa
r = np.hypot((np.arange(W)-cx)[None,:], (np.arange(H)-cy)[:,None]) / R_SOL
ref = valid & (r > 1.3) & (r < 1.5)
kr = float(np.median(G[ref]) / np.median(R[ref]))
L = 0.5*(np.nan_to_num(G) + kr*np.nan_to_num(R))
print('kr', kr)
vores = np.round(np.arange(1.0, 8.6, 0.1), 2)
rows = []
for a, b in zip(vores[:-1], vores[1:]):
    m = valid & (r >= a) & (r < b)
    if m.sum() < 50: continue
    q = np.percentile(L[m], [16, 50, 84]); qg = np.percentile(G[m], [16,50,84])
    rows.append(dict(r0=float(a), r1=float(b), n=int(m.sum()), L=float(q[1]), L16=float(q[0]), L84=float(q[2]), G=float(qg[1])))
zs = valid & (r > 6.2) & (r < 7.0)
L_cel = float(np.median(L[zs]))
zc = valid & (r > 1.5) & (r < 2.2)
L_cor = float(np.median(L[zc]))
print('L cel 6.2-7.0', L_cel, ' L corona 1.5-2.2', L_cor)
for d in rows:
    d['L_sobre_cel'] = d['L']/L_cel
json.dump(dict(kr=kr, L_cel=L_cel, L_cor=L_cor, files=rows), open('lineal.json','w'), indent=1)
for d in rows:
    if abs((d['r0']*10) % 5) < 1e-6 or d['r0'] < 2.0:
        print(f"{d['r0']:.1f}-{d['r1']:.1f}  L={d['L']:10.1f}  L/L_cel={d['L_sobre_cel']:7.3f}  (16-84: {d['L16']/L_cel:.3f}-{d['L84']/L_cel:.3f})")
# lo/hi com el tool
dins = valid & (r > 1.03) & (r < 6.0)
lo = float(np.percentile(L[dins], 0.02))*0.85
hi = float(np.percentile(L[valid & (r < 1.06)], 99.6))
print('lo', lo, 'hi', hi, '(foto_params: 275.8, 1200409)')
