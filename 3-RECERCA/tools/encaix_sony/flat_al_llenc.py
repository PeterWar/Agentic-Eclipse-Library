"""Porta el flat de l'A7RIIIA (reixa 5320×7968 de DSC06993) al domini estès del llenç amb la mateixa
similitud que l'apilat (similitud_sony_canvas.npy = [escala, θ°, tx, ty]; Sol de la placa a
(3894,7, 2768,7)), i comprova primer que la similitud reprodueix sony_stack_ext_rgb.npy a partir de
sony_stack_ref_rgb.npy. Sortida: flat_ext_rgb.npy (H×W×3 al domini estès), i l'apilat aplanat
sony_stack_ext_rgb_FLAT.npy (= sony_stack_ext_rgb / flat)."""
import os, numpy as np
from scipy import ndimage as ndi

SP = os.path.dirname(os.path.abspath(__file__))
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
SXs, SYs = 3894.7, 2768.7
sim = np.load(os.path.join(SP, 'similitud_sony_canvas.npy'))
S, th, tx, ty = float(sim[0]), np.radians(float(sim[1])), float(sim[2]), float(sim[3])
CX, CY = tx + Lm, ty + T
c, s = np.cos(th), np.sin(th)

def warp_to_ext(img, order=1, ds=1, cval=np.nan):
    yy, xx = np.mgrid[0:H:ds, 0:W:ds].astype(np.float64)
    ux = (xx - CX) / S; uy = (yy - CY) / S
    # p_canvas − c = S·(u_x cosθ + u_y sinθ, −u_x sinθ + u_y cosθ)  ⇒  inversa: p_sony − c_sony = (ux cosθ − uy sinθ, ux sinθ + uy cosθ)
    px = SXs + ux * c - uy * s; py = SYs + ux * s + uy * c
    return ndi.map_coordinates(img, [py, px], order=order, mode='constant', cval=cval)

ref = np.load(os.path.join(SP, 'sony_stack_ref_rgb.npy'), mmap_mode='r')
ext = np.load(os.path.join(SP, 'sony_stack_ext_rgb.npy'), mmap_mode='r')
# comprovació a 1/8 sobre el verd
ds = 8
Gt = warp_to_ext(np.nan_to_num(np.asarray(ref[..., 1])), ds=ds)
Ge = np.asarray(ext[::ds, ::ds, 1])
m = np.isfinite(Gt) & np.isfinite(Ge) & (Gt > 0)
print('comprovació de la similitud (verd, 1/8): corr %.5f, mediana |dif|/|val| %.5f, n=%d' % (
    np.corrcoef(Gt[m], Ge[m])[0, 1], np.median(np.abs(Gt[m] - Ge[m]) / np.maximum(np.abs(Ge[m]), 1e-3)), m.sum()))
# altres convencions per si de cas
def warp_alt(img, sgn, ds=8):
    yy, xx = np.mgrid[0:H:ds, 0:W:ds].astype(np.float64)
    ux = (xx - CX) / S; uy = (yy - CY) / S
    px = SXs + ux * c + sgn * uy * s; py = SYs - sgn * ux * s + uy * c
    return ndi.map_coordinates(img, [py, px], order=1, mode='constant', cval=np.nan)
for sgn in (+1, -1):
    Ga = warp_alt(np.nan_to_num(np.asarray(ref[..., 1])), sgn)
    ma = np.isfinite(Ga) & np.isfinite(Ge) & (Ga > 0)
    print(f'  convenció alternativa sgn={sgn:+d}: corr {np.corrcoef(Ga[ma], Ge[ma])[0, 1]:.5f}')

flat = np.load(os.path.join(SP, 'flat_a7r3a_rgb.npy'))
fext = np.empty((H, W, 3), np.float32)
for k in range(3):
    fext[..., k] = warp_to_ext(flat[..., k], order=1, cval=1.0)
fext = np.clip(np.nan_to_num(fext, nan=1.0), 0.2, 1.05)
np.save(os.path.join(SP, 'flat_ext_rgb.npy'), fext)
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
print('flat al llenç (verd): centre del Sol %.3f, cantons %.3f %.3f %.3f %.3f, costats dalt %.3f baix %.3f esq %.3f dreta %.3f' % (
    fext[int(CY), int(CX), 1], fext[sl][0, 0, 1], fext[sl][0, -1, 1], fext[sl][-1, 0, 1], fext[sl][-1, -1, 1],
    fext[sl][0, W0 // 2, 1], fext[sl][-1, W0 // 2, 1], fext[sl][H0 // 2, 0, 1], fext[sl][H0 // 2, -1, 1]))
out = np.asarray(ext) / fext
np.save(os.path.join(SP, 'sony_stack_ext_rgb_FLAT.npy'), out.astype(np.float32))
print('fet: sony_stack_ext_rgb_FLAT.npy')
