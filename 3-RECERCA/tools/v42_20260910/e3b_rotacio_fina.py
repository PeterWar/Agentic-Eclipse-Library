"""E3b · rotació de les capes 06–12 de Pere respecte de la base V42 amb pas azimutal fi (0,05°) i interpolació parabòlica del pic, més un control:
la base contra ella mateixa girada +0,30° (rotació coneguda) per veure què retorna el mètode. E3 anava a 0,25° de pas (1440 mostres) i les sis capes donaven +0,25°."""
import json, numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter, rotate
from psd_tools import PSDImage
from comu42 import *
import e3_alineament_capes as E
F42 = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V42.psb')
def polar(img, cx, cy, r0, r1, nr=48, nth=7200):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.linspace(r0, r1, nr); R, T = np.meshgrid(rs, th, indexing='ij'); v = map_coordinates(img, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest'); return v - gaussian_filter(v, (0, 40), mode='wrap')
def rot_az(pa, pb):
    nth = pa.shape[1]; A = pa - pa.mean(axis=1, keepdims=True); B_ = pb - pb.mean(axis=1, keepdims=True); cc = np.fft.ifft(np.fft.fft(A, axis=1) * np.conj(np.fft.fft(B_, axis=1)), axis=1).real.sum(axis=0); cc /= (np.linalg.norm(A) * np.linalg.norm(B_) + 1e-12)
    k = int(np.argmax(cc)); y0, y1, y2 = cc[k - 1], cc[k], cc[(k + 1) % nth]; d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0; kk = k + d
    if kk > nth / 2: kk -= nth
    return float(kk * 360.0 / nth), float(y1)
s = PSDImage.open(F42); n = {l.name: l for l in s}
base = n['00 Base corba (total) · V42']; lb = np.log(np.maximum(E.C.channel(base, 1).astype(np.float32) / 65535, 1e-4)); pb = polar(lb, CX, CY, 1.1 * RS, 1.5 * RS); rep = {}
# control: la base girada +0,30° al voltant del Sol
rb = rotate(lb, 0.30, reshape=False, order=1, mode='nearest')   # gira al voltant del centre de la imatge; corregim el centre traslladant abans/després
H_, W_ = lb.shape; from scipy.ndimage import shift as ndshift
def gira_sol(img, ang):
    c = np.array([H_ / 2 - 0.5, W_ / 2 - 0.5]); d = np.array([CY, CX]) - c; a = np.deg2rad(ang); Rm = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    t = d - Rm @ d; return ndshift(rotate(img, -ang, reshape=False, order=1, mode='nearest'), t, order=1, mode='nearest')   # signe: escollit perquè la prova ho digui
for ang in (0.30, -0.30):
    g = gira_sol(lb, ang); a_, v_ = rot_az(polar(g, CX, CY, 1.1 * RS, 1.5 * RS), pb); rep[f'control_base_girada_{ang:+.2f}'] = {'rotacio_mesurada_deg': a_, 'pic': v_}; print(f'control: base girada {ang:+.2f}° → mesurat {a_:+.3f}° (pic {v_:.3f})')
for nom in ['11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    l = n[nom]; g = np.zeros((H, W), np.float32); x0, y0, x1, y1 = l.bbox; ch = E.C.channel(l, 1).astype(np.float32) / 65535; g[y0:y1, x0:x1] = ch; lg = np.log(np.maximum(g, 1e-4))
    al = E.C.channel(l, -1); m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = (ch > 0) if al is None else (al > 0)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - CX, yy - CY); sel = m & (r > 1.1 * RS) & (r < 1.5 * RS); frac = float(sel.mean() / ((r > 1.1 * RS) & (r < 1.5 * RS)).mean())
    a_, v_ = rot_az(polar(lg, CX, CY, 1.1 * RS, 1.5 * RS), pb); rep[nom] = {'rotacio_deg': a_, 'pic': v_, 'fraccio_anell_amb_dada': frac}; print(f'{nom}: rotació {a_:+.3f}° (pic {v_:.3f}; anell cobert {100*frac:.0f} %)')
(REB42 / 'E3b_rotacio_fina.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E3b fet')
