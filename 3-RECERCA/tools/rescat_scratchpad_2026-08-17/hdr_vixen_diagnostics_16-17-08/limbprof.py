import numpy as np, json
from scipy.ndimage import map_coordinates
sk = np.load('sketch_q4.npy'); fo = np.load('foto.npy')
g = json.load(open('geom.json'))
def perfil(img, cx, cy, r0, r1, dr=1.0, n_az=720):
    th = np.linspace(0, 2*np.pi, n_az, endpoint=False)
    rr = np.arange(r0, r1, dr)
    xx = cx + rr[None,:]*np.cos(th)[:,None]; yy = cy + rr[None,:]*np.sin(th)[:,None]
    out = []
    for c in range(3):
        p = map_coordinates(img[...,c], [yy, xx], order=1, mode='nearest')
        out.append(np.median(p, axis=0))
    return rr, np.array(out)
s = g['sketch_q4']; f = g['foto']
rr, p = perfil(sk, s['cx'], s['cy'], 200, 340, 2.0)
print('SKETCH q4 (r, R,G,B mediana azimutal)')
for r_, v in zip(rr, p.T): print(f'{r_:6.0f} {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}')
rr, p = perfil(fo, f['cx'], f['cy'], 380, 520, 3.0)
print('FOTO (r, R,G,B)')
for r_, v in zip(rr, p.T): print(f'{r_:6.0f} {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}')
