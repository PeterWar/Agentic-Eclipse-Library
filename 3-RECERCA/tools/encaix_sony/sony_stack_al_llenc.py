"""Posa l'apilat Sony (reixa DSC06993) al domini estès del llenç de Pere.
Mapa: p_sony = c_sony + R(−θ)·(p_canvas − c_canvas)/S ; S = 3,2020/2,1495, θ ≈ 33,1° (signe i valor
afinats per correlació de la corona 1,8–3,4 R☉ amb la Vixen, a 1/4 de resolució), c_sony = centre del Sol
de la placa (3894,7, 2768,7), c_canvas = (3420,89+600, 2187,66+550).
Sortida: sony_stack_ext_rgb.npy (ADU/s, NaN on no hi ha dada), sony_stack_ext_cov.npy.
"""
import numpy as np
from scipy import ndimage as ndi

T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
CX, CY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
SX, SY = 3894.7, 2768.7
S0 = 3.2020 / 2.1495
S = np.load('sony_stack_ref_rgb.npy'); WT = np.load('sony_stack_ref_wt.npy')
Sf = np.nan_to_num(S, nan=0.0)
cov = (WT > 0).all(-1).astype(np.float32)
vix = np.load('vixen_canvas_rgb.npy')

def warp(img, theta_deg, scale, dxy=(0, 0), ds=4, order=1):
    """Retorna img (reixa Sony) mostrejada sobre el domini estès a 1/ds."""
    th = np.radians(theta_deg)
    # R_ccw(θ) sobre (x,y) amb y cap avall: (x cosθ + y sinθ, −x sinθ + y cosθ); la inversa és R(−θ)
    c, s = np.cos(th), np.sin(th)
    yy, xx = np.mgrid[0:H:ds, 0:W:ds].astype(np.float64)
    ux = (xx - CX - dxy[0]) / scale; uy = (yy - CY - dxy[1]) / scale
    # inversa: p_sony − c_sony = R(−θ)(u) = (ux cosθ − uy sinθ, ux sinθ + uy cosθ)
    px = SX + ux * c - uy * s; py = SY + ux * s + uy * c
    return ndi.map_coordinates(img, [py, px], order=order, mode='constant', cval=np.nan)

# --- 1. signe i valor del gir, per correlació de la corona a 1/4 -----------------------------
ds = 4
G = Sf[..., 1]
vixL = vix.mean(-1)
vix_ext = np.full((H, W), np.nan, np.float32); vix_ext[T:T + H0, Lm:Lm + W0] = vixL
V4 = vix_ext[::ds, ::ds]
yy, xx = np.mgrid[0:H:ds, 0:W:ds]
r4 = np.hypot(xx - CX, yy - CY) / 446.15
ann = (r4 > 1.8) & (r4 < 3.4) & np.isfinite(V4)
def hp(a, s=6):
    a = np.nan_to_num(a); return a - ndi.gaussian_filter(a, s)
Vh = hp(np.log(np.clip(V4, 1e-3, None)))
best = None
for theta in (33.1, -33.1):
    Sw = warp(G, theta, S0, ds=ds)
    Sh = hp(np.log(np.clip(Sw, 1.0, None)))
    m = ann & np.isfinite(Sw) & (Sw > 0)
    cc = np.corrcoef(Vh[m], Sh[m])[0, 1]
    print(f'θ = {theta:+.1f}°: correlació corona (log, passa alt) = {cc:.3f}')
    if best is None or cc > best[0]: best = (cc, theta)
theta0 = best[1]
# afinament: graella θ ± 0,4°, escala ± 0,6 %, i desplaçament ± 12 px (a 1/4: ±3)
res = []
for th in theta0 + np.arange(-0.4, 0.41, 0.1):
    for sc in S0 * (1 + np.arange(-0.006, 0.0061, 0.002)):
        Sw = warp(G, th, sc, ds=ds)
        Sh = hp(np.log(np.clip(Sw, 1.0, None)))
        m = ann & np.isfinite(Sw) & (Sw > 0)
        cc = np.corrcoef(Vh[m], Sh[m])[0, 1]
        res.append((cc, th, sc))
res.sort(reverse=True)
print('millors (cc, θ, escala):', [(round(a, 4), round(b, 2), round(c, 5)) for a, b, c in res[:5]])
cc0, th_b, sc_b = res[0]
# desplaçament fi per correlació creuada (a 1/2 de resolució)
ds2 = 2
Sw = warp(G, th_b, sc_b, ds=ds2)
V2 = vix_ext[::ds2, ::ds2]; yy2, xx2 = np.mgrid[0:H:ds2, 0:W:ds2]; r2 = np.hypot(xx2 - CX, yy2 - CY) / 446.15
m2 = (r2 > 1.8) & (r2 < 3.4) & np.isfinite(V2) & np.isfinite(Sw) & (Sw > 0)
A = np.where(m2, hp(np.log(np.clip(V2, 1e-3, None)), 12), 0); Bm = np.where(m2, hp(np.log(np.clip(Sw, 1.0, None)), 12), 0)
F = np.fft.rfft2(A) * np.conj(np.fft.rfft2(Bm)); F /= np.abs(F) + 1e-9
pc = np.fft.irfft2(F, s=A.shape); iy, ix = np.unravel_index(np.argmax(pc), pc.shape)
if iy > A.shape[0] // 2: iy -= A.shape[0]
if ix > A.shape[1] // 2: ix -= A.shape[1]
print(f'desplaçament residual (canvas − sony) a 1/2: dy={iy} dx={ix} → {ds2*iy}, {ds2*ix} px')
dxy = (ds2 * ix, ds2 * iy)
Sw = warp(G, th_b, sc_b, dxy=dxy, ds=ds2)
m2 = (r2 > 1.8) & (r2 < 3.4) & np.isfinite(V2) & np.isfinite(Sw) & (Sw > 0)
cc1 = np.corrcoef(hp(np.log(np.clip(V2, 1e-3, None)), 12)[m2], hp(np.log(np.clip(Sw, 1.0, None)), 12)[m2])[0, 1]
print(f'correlació final a 1/2 amb dxy={dxy}: {cc1:.3f}   (θ={th_b:.2f}°, escala={sc_b:.5f}, S0={S0:.5f})')
np.save('sony_stack_transform.npy', np.array([th_b, sc_b, dxy[0], dxy[1]]))

# --- 2. remostreig complet -----------------------------------------------------------------
out = np.empty((H, W, 3), np.float32)
for c in range(3):
    out[..., c] = warp(Sf[..., c], th_b, sc_b, dxy=dxy, ds=1)
covw = warp(cov, th_b, sc_b, dxy=dxy, ds=1)
covw = np.nan_to_num(covw) > 0.999
out[~covw] = np.nan
np.save('sony_stack_ext_rgb.npy', out); np.save('sony_stack_ext_cov.npy', covw)
print('fet: cobertura al domini estès', covw.mean(), ' dins el llenç', covw[T:T + H0, Lm:Lm + W0].mean())
