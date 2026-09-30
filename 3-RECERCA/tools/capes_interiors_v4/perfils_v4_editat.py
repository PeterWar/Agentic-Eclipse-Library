"""Perfils radials (per anell solar) de les màscares editades de 04/03 i dels compostos del V4 editat (amb i sense 04/03),
i gradient radial de les màscares per localitzar els graons sense difuminar."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta4 = json.load(open('v5in/meta.json')); meta3 = json.load(open('v3/meta.json'))
files3 = sorted(glob.glob('v3/*_rgb.npy')); files3 = [f for f in files3 if 'merged' not in f]
SUN = (4020.89, 2737.66); RS = 446.15
rr = np.arange(0.95, 11.0, 0.01); th = np.deg2rad(np.arange(0, 360, 0.5))
R, T = np.meshgrid(rr, th, indexing='ij'); X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
inside = (X >= 458) & (X < 7416) & (Y >= 464) & (Y < 5102)
def samp(arr, ox, oy, fill=np.nan):
    v = ndi.map_coordinates(np.asarray(arr, np.float32), [Y + oy, X + ox], order=1, mode='constant', cval=fill)
    v[~inside] = np.nan; return v
# màscares editades de les capes (bbox (457,463) → doc(x,y) → m[y-463, x-457])
def mpol(idx):
    mb = meta4['layers'][idx]['mask']['bbox']
    m = np.load(f'v5in/{idx:02d}_mask.npy', mmap_mode='r')
    return samp(np.asarray(m, np.float32) / 65535., -mb[0], -mb[1])
def lpol(j3, dx=0):
    a = np.load(files3[j3], mmap_mode='r'); l0, t0 = meta3['layers'][j3]['bbox'][:2]
    # capes retallades a (457,463): doc → npy[y-463, x-457]; les de geometria vella (+1): doc → npy[y-t0+1, x-l0+1]
    return np.stack([samp(np.asarray(a[..., c], np.float32) / 65535., -(457 + dx), -(463 + dx)) for c in range(3)])
lum = lambda C: 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
M = {idx: mpol(idx) for idx in (2, 3, 5, 6, 7, 8, 9, 10, 11)}
print('perfil (mitjana az.) de les màscares editades:')
rsel = [1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 3.0, 4.0, 6.0, 9.0]
print('capa'.ljust(8) + ''.join(f'{r:>6.1f}' for r in rsel))
prof = {}
for idx in M:
    p = np.nanmean(M[idx], axis=1); prof[idx] = p
    nm = meta4['layers'][idx]['name'][:6]
    print(nm.ljust(8) + ''.join(f'{p[int(round((r-0.95)/0.01))]:6.2f}' for r in rsel))
np.savez('v5in/perfils_mascares_editades.npz', rr=rr, **{f'p{idx}': prof[idx] for idx in prof})
# graons: màxim del |gradient radial| del PERFIL (per 100 px) i del mapa
print('\ngraons del perfil (|dp/dr| màxim en finestres de 0,05 R☉), r 1,5–9:')
for idx in (9, 10, 11):
    p = prof[idx]; g = np.abs(np.gradient(p, rr))
    sel = (rr > 1.5) & (rr < 9)
    jm = np.argmax(g * sel)
    print(f'  {meta4["layers"][idx]["name"][:6]}: màx |dp/dr| = {g[jm]:.2f} per R☉ a r={rr[jm]:.2f} (canvi de {g[jm]*0.05:.3f} per 0,05 R☉)')
# compost del V4 editat: totes les capes vs sense 04/03 (ordre 0..11)
L = {0: lpol(0, dx=-1), 1: lpol(0), 2: lpol(1), 3: lpol(2), 4: lpol(3, dx=1), 5: lpol(3), 6: lpol(4), 7: lpol(5), 8: lpol(6), 9: lpol(7), 10: lpol(8), 11: lpol(9)}
def compose(idxs):
    C = np.zeros_like(L[0])
    for i in idxs:
        a = M[i][None] if i in M else np.ones_like(L[0][:1])
        Li = np.where(np.isfinite(L[i]), L[i], 0)
        C = C * (1 - a) + Li * a
    return C
C_tot = compose(range(12)); C_s43 = compose(range(10))
m_tot = np.nanmedian(np.where(inside[None].repeat(3,0)[:1][0], lum(C_tot), np.nan), axis=1)
m_s43 = np.nanmedian(lum(C_s43), axis=1)
p03 = {j: np.nanmedian(lum(L[j]), axis=1) for j in (9, 10, 11)}
print('\nperfil del compost (mediana az.): amb tot | sense 04/03 | capes 05, 04, 03 soles')
for r in (1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0, 5.0, 7.0, 9.0):
    j = int(round((r - 0.95) / 0.01))
    print(f'  {r:4.1f}  {m_tot[j]:.3f} | {m_s43[j]:.3f} | {p03[9][j]:.3f} {p03[10][j]:.3f} {p03[11][j]:.3f}')
np.savez('v5in/perfils_compost.npz', rr=rr, m_tot=m_tot, m_s43=m_s43, p05=p03[9], p04=p03[10], p03=p03[11])
