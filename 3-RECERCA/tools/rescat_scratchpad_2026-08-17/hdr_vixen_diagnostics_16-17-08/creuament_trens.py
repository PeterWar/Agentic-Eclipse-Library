"""Prova creuada: les línies radials hi són als DOS trens?

Si una estructura radial surt al mateix angle de posició CELESTE amb el Vixen
(VSD90SS, refractor de 90 mm) i amb la Sony (300 mm f/2,8, teleobjectiu), no pot
ser de cap de les dues òptiques: és el Sol. Si només surt en un, és
instrumental.
"""
import sys, os, math
import numpy as np
import rawpy
import cv2
from scipy.ndimage import uniform_filter, gaussian_filter1d

sys.path.insert(0, '/Users/USUARI/Downloads/Eclipse 2026/research/tools')
os.environ['SENSE_PRNU'] = '1'
import hdr_corona_vixen as M

SONY = os.path.expanduser('~/Desktop/Eclipse 2026/300mm')
# research/75 §5.1
ESC_SONY, PA_N_SONY, PA_E_SONY = 3.2020, 90.27, 358.64
R_SOL_SONY = 959.0 / ESC_SONY
R_LLUNA_SONY = 308.7


def vec(pa):
    a = math.radians(pa)
    return np.array([math.sin(a), -math.cos(a)])


def limb(g, cy, cx, rmig):
    for _ in range(3):
        pts = M.punts_limbe(g, cy, cx, rmig)
        if len(pts) < 60:
            return None
        cy, cx, _r, n, rms = M.ajusta_cercle(pts)
    return cy, cx, n, rms


def crestes(g, cy, cx, R, r0=1.12, r1=2.40, na=3600):
    H, W = g.shape
    y = (np.arange(H) - cy)[:, None]
    x = (np.arange(W) - cx)[None, :]
    r = np.hypot(x, y)
    ib = r.astype(np.int32)
    bo = np.isfinite(g)
    n = int(min(H, W) / 2)
    prof = np.full(n, np.nan)
    for k in range(n):
        m = bo & (ib == k)
        if m.sum() > 200:
            prof[k] = np.nanmean(g[m])
    ok = np.isfinite(prof)
    prof = np.interp(np.arange(n), np.arange(n)[ok], prof[ok])
    norm = np.where(bo, g / np.maximum(prof[np.clip(ib, 0, n - 1)], 1e-9), 1.0)
    NR = n
    pol = cv2.warpPolar(np.nan_to_num(norm, nan=1.0).astype(np.float32),
                        (NR, na), (cx, cy), float(NR),
                        cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR)
    rr = np.arange(NR) / NR * NR / R
    sel = (rr > r0) & (rr < r1)
    b = pol[:, sel].astype(np.float64)
    b = b - uniform_filter(b, (int(na / 300), 1))
    s = gaussian_filter1d(b.mean(1), na / 1800.0, mode='wrap')
    sd = 1.4826 * np.median(np.abs(s - np.median(s)))
    out = []
    for i in range(na):
        w = np.take(s, range(i - int(na / 240), i + int(na / 240) + 1), mode='wrap')
        if s[i] == w.max() and s[i] > 3.0 * sd:
            out.append(((360 - i / na * 360) % 360, s[i] / sd))
    return out


def a_pa_celeste(ang_imatge, pa_nord):
    """angle d'imatge (0°=+x, antihorari, y avall) → angle de posició celeste."""
    v = np.array([math.cos(math.radians(ang_imatge)),
                  -math.sin(math.radians(ang_imatge))])
    n = vec(pa_nord)
    e = np.array([-n[1], n[0]])          # est a 90° del nord, sentit del camp
    return math.degrees(math.atan2(float(v @ e), float(v @ n))) % 360


# ---------------------------------------------------------------- Vixen
fgv = {f.nom: f for f in M.llegeix_manifest()}
fv = fgv['572A2989.CR3']
mos, _ = M.calibra(fv)
gv = 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2])
gv = np.where((mos[0::2, 1::2] > M.SOSTRE) | (mos[1::2, 0::2] > M.SOSTRE), np.nan, gv)
cv_ = crestes(gv, fv.sol_y / 2, fv.sol_x / 2, M.R_SOL_PX / 2)
print('VIXEN 572A2989 (1/8 s) — crestes radials')
print('  %-12s %-8s %s' % ('angle imatge', 'força', 'PA celeste'))
vix = []
for a, f in sorted(cv_, key=lambda z: -z[1])[:12]:
    pa = a_pa_celeste(a, M.PA_NORD)
    vix.append((pa, f))
    print('  %10.2f°  %5.1fσ   %7.2f°' % (a, f, pa))

# ---------------------------------------------------------------- Sony
print('\nSONY DSC06986 (1/8 s) — crestes radials')
with rawpy.imread(f'{SONY}/DSC06986.ARW') as raw:
    cru = M.parell(raw.raw_image_visible).astype(np.float32) - 512.0
    pat = raw.raw_pattern.tolist()
print('  patró de Bayer de la Sony:', pat)
gs = 0.5 * (cru[0::2, 1::2] + cru[1::2, 0::2])
gs = np.where(gs > 0.85 * (16383 - 512), np.nan, gs)
H, W = gs.shape
res = limb(np.nan_to_num(gs, nan=0.0), H / 2, W / 2, R_LLUNA_SONY / 2)
if res is None:
    print('  ⛔ no s\'ha pogut ajustar el limbe')
    sys.exit(1)
cy, cx, nn, rms = res
print('  limbe: centre lunar (%.1f, %.1f) amb %d punts i rms %.2f px' % (2 * cx, 2 * cy, nn, 2 * rms))
cs = crestes(gs, cy, cx, R_SOL_SONY / 2)
print('  %-12s %-8s %s' % ('angle imatge', 'força', 'PA celeste'))
son = []
for a, f in sorted(cs, key=lambda z: -z[1])[:12]:
    pa = a_pa_celeste(a, PA_N_SONY)
    son.append((pa, f))
    print('  %10.2f°  %5.1fσ   %7.2f°' % (a, f, pa))

print('\nCOINCIDÈNCIES entre trens (PA celeste, tolerància 4°):')
cap = True
for pv, fv_ in vix:
    for ps, fs in son:
        d = abs(pv - ps)
        d = min(d, 360 - d)
        if d < 4:
            cap = False
            print('   Vixen %7.2f° (%.1fσ)  ↔  Sony %7.2f° (%.1fσ)   Δ=%.2f°' % (pv, fv_, ps, fs, d))
if cap:
    print('   CAP. Les crestes de cada tren cauen a angles diferents.')
