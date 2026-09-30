"""Màscares 04/03 de V5, versió 2: el PERFIL de les màscares velles de Pere (el nivell que ell veia i aprovava),
arreglat: (a) res per sota d'1,15/1,25 R☉ (limbe, perles, protuberàncies fora d'abast), amb rampa llarga;
(b) monotòniques de 3 R☉ enfora (fora el forat-anell de la 04 i la caiguda de la 03); (c) gaussianes pertot."""
import numpy as np
from scipy import ndimage as ndi
SUN = (4020.89, 2737.66); RS = 446.15
FRAME = (457, 463, 7417, 5103)
E = np.load('v5in/perfils_mascares_editades.npz'); rr = E['rr']    # 0,95..11,0 cada 0,01
def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def neteja(p, r_on0, r_on1, r_flat, extend=None):
    p = p.copy()
    ok = np.isfinite(p); p[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), p[ok])
    j = np.searchsorted(rr, r_flat)
    p[j:] = extend if extend is not None else p[j]          # aplanat de r_flat enfora (fora el forat-anell)
    p = np.maximum.accumulate(np.minimum.accumulate(p[::-1])[::-1])  # monotònica no decreixent (des de dins)
    p = p * smoothstep(rr, r_on0, r_on1)                     # protecció del limbe/perles
    p = ndi.gaussian_filter1d(p, 0.04 / 0.01, mode='nearest')
    return np.clip(p, 0, 1)
p04 = neteja(E['p10'], 1.15, 1.45, 3.0)
p03 = neteja(E['p11'], 1.25, 1.60, 3.0)
print('perfil m04 nou:', {round(float(q),2): round(float(np.interp(q, rr, p04)), 3) for q in (1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 6.0, 9.0)})
print('perfil m03 nou:', {round(float(q),2): round(float(np.interp(q, rr, p03)), 3) for q in (1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 6.0, 9.0)})
yy, xx = np.mgrid[FRAME[1]:FRAME[3], FRAME[0]:FRAME[2]].astype(np.float32)
r = np.hypot(xx - SUN[0], yy - SUN[1]) / RS
del yy, xx
# m_nova = MÀXIM(vella de Pere, neta radial): la vella mana pertot on és més oberta (vel del limbe, protuberàncies,
# perles: es veuen EXACTAMENT igual) i la neta només actua on la vella queia (forat-anell de la 04 a 4–6 R☉,
# caiguda exterior de la 03). El màxim de dues màscares suaus no crea cap graó.
import json; meta = json.load(open('v5in/meta.json'))
for nm, p, idx in (('04', p04, 10), ('03', p03, 11)):
    m_net = np.interp(r, rr, p, left=0.0, right=float(p[-1])).astype(np.float32)
    m_net = ndi.gaussian_filter(m_net, 3.0)
    mb = meta['layers'][idx]['mask']['bbox']
    mv_full = np.load(f'v5in/{idx:02d}_mask.npy', mmap_mode='r')
    m_vella = np.asarray(mv_full[FRAME[1] - mb[1]:FRAME[3] - mb[1], FRAME[0] - mb[0]:FRAME[2] - mb[0]], np.float32) / 65535.
    assert m_vella.shape == m_net.shape
    m = np.maximum(m_vella, m_net)
    frac = float((m_net > m_vella + 0.02).mean())
    np.save(f'v5out/mask_{nm}.npy', np.clip(np.round(m * 65535), 0, 65535).astype(np.uint16))
    print(f'màscara {nm}: mitjana {float(m.mean()):.3f}; la neta mana al {frac*100:.1f} % dels píxels (la resta, la vella de Pere tal qual)')
np.savez('v5out/perfils_0403.npz', rr=rr, p04=p04, p03=p03)
