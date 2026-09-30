"""Verifica CapesTotalsV1.psb: estructura, i recomposició de finestres contra la fusionada desada."""
import os, numpy as np
from psd_tools import PSDImage
PSB = os.path.expanduser(os.environ.get('CT1_OUT', '~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV1.psb'))
psd = PSDImage.open(PSB)
print('llenç', psd.width, 'x', psd.height, '| bits', psd.depth, '| capes', len(list(psd)))
for i, l in enumerate(psd):
    m = l.mask
    print(f"[{i:2d}] {'VIS' if l.visible else 'OFF'} {str(l.blend_mode).split('.')[-1]:13s} op={l.opacity:3d} '{l.name[:80]}' {'m16' if m is not None else '—'}")
merged = psd.numpy()[..., :3]
W, H = psd.width, psd.height
FINS = {'limbe': (2400, 3300, 512), 'traspas': (2100, 4900, 512), 'exterior': (700, 6300, 512), 'canto BR': (4800, 7100, 500)}
def blend(comp, s, a, mode):
    if 'linear_light' in mode: out = np.clip(comp + 2.0*s - 1.0, 0, 1)
    elif 'overlay' in mode: out = np.where(comp <= 0.5, 2*comp*s, 1 - 2*(1-comp)*(1-s))
    else: out = s
    return comp*(1 - a[..., None]) + out*a[..., None]
for nom, (y0, x0, s) in FINS.items():
    comp = np.zeros((s, s, 3), np.float32)
    for l in psd:
        if not l.visible: continue
        sl = np.zeros((s, s, 3), np.float32); cov = np.zeros((s, s), np.float32)
        iy0, ix0 = max(l.top, y0), max(l.left, x0)
        iy1, ix1 = min(l.bottom, y0+s), min(l.right, x0+s)
        if iy1 <= iy0 or ix1 <= ix0:
            pass
        else:
            arr = l.numpy('color')
            sl[iy0-y0:iy1-y0, ix0-x0:ix1-x0] = arr[iy0-l.top:iy1-l.top, ix0-l.left:ix1-l.left]
            cov[iy0-y0:iy1-y0, ix0-x0:ix1-x0] = 1.0
            del arr
        a = cov
        m = l.mask
        if m is not None:
            mk = np.full((s, s), m.background_color/255.0, np.float32)
            my0, mx0 = max(m.top, y0), max(m.left, x0)
            my1, mx1 = min(m.bottom, y0+s), min(m.right, x0+s)
            if my1 > my0 and mx1 > mx0:
                marr = l.numpy('mask')[..., 0]
                mk[my0-y0:my1-y0, mx0-x0:mx1-x0] = marr[my0-m.top:my1-m.top, mx0-m.left:mx1-m.left]
                del marr
            a = a * mk
        a = a * (l.opacity/255.0)
        comp = blend(comp, sl, a, str(l.blend_mode).lower())
    d = np.abs(comp - merged[y0:y0+s, x0:x0+s]) * 65535
    print(f'finestra {nom:9s}: |dif| mediana {np.median(d):6.2f}  p99 {np.percentile(d,99):8.2f}  màx {d.max():8.1f} (u16)')
