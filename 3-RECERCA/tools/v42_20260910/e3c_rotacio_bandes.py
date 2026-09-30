"""E3c · la rotació de les capes de Pere respecte de la cadena és estable amb el radi? Mateix mètode que E3b (correlació azimutal de perfils polars, pas 0,05°, pic parabòlic)
en dues bandes (1,05–1,25 i 1,3–1,6 R☉), amb la base V42 llegida del .npy (idèntica a la capa del PSB) i les capes de Pere de la V39 (byte a byte a la V42);
control: la base contra ella mateixa DESPLAÇADA 3 px (una translació no ha de sortir com a rotació)."""
import json, numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter, shift as ndshift
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C
def polar(img, cx, cy, r0, r1, nr=48, nth=7200):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.linspace(r0, r1, nr); R, T = np.meshgrid(rs, th, indexing='ij'); v = map_coordinates(img, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest'); return v - gaussian_filter(v, (0, 40), mode='wrap')
def rot_az(pa, pb):
    nth = pa.shape[1]; A = pa - pa.mean(axis=1, keepdims=True); B_ = pb - pb.mean(axis=1, keepdims=True); cc = np.fft.ifft(np.fft.fft(A, axis=1) * np.conj(np.fft.fft(B_, axis=1)), axis=1).real.sum(axis=0); cc /= (np.linalg.norm(A) * np.linalg.norm(B_) + 1e-12)
    k = int(np.argmax(cc)); y0, y1, y2 = cc[k - 1], cc[k], cc[(k + 1) % nth]; den = (y0 - 2 * y1 + y2); d = 0.5 * (y0 - y2) / den if den != 0 else 0.0; kk = k + d
    if kk > nth / 2: kk -= nth
    return float(kk * 360.0 / nth), float(y1)
lb = np.log(np.maximum(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1].astype(np.float32) / 65535, 1e-4))
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}; rep = {}
caps = {}
for nom in ['11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    l = n[nom]; g = np.zeros((H, W), np.float32); x0, y0, x1, y1 = l.bbox; g[y0:y1, x0:x1] = C.channel(l, 1).astype(np.float32) / 65535; caps[nom] = np.log(np.maximum(g, 1e-4))
for (r0, r1) in ((1.05, 1.25), (1.1, 1.5), (1.3, 1.6)):
    pb = polar(lb, CX, CY, r0 * RS, r1 * RS); out = {}
    for nom, lg in caps.items(): a_, v_ = rot_az(polar(lg, CX, CY, r0 * RS, r1 * RS), pb); out[nom] = {'rotacio_deg': a_, 'pic': v_}
    rep[f'banda_{r0}_{r1}'] = out; print(f'banda {r0}–{r1} R☉: ' + ' · '.join(f"{k.split()[0]} {v['rotacio_deg']:+.3f}° ({v['pic']:.2f})" for k, v in out.items()))
pb = polar(lb, CX, CY, 1.1 * RS, 1.5 * RS)
for d in ((3, 0), (0, 3), (-3, 0)):
    a_, v_ = rot_az(polar(ndshift(lb, d, order=1, mode='nearest'), CX, CY, 1.1 * RS, 1.5 * RS), pb); rep[f'control_translacio_{d}'] = {'rotacio_deg': a_, 'pic': v_}; print(f'control: base desplaçada {d} px → rotació {a_:+.3f}° (pic {v_:.3f})')
(REB42 / 'E3c_rotacio_bandes.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E3c fet')
