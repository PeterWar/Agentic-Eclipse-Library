"""Versions «v8» de les dues capes velles de Pere que encara eren al compost (SEMIFINAL7) i que A4 va trobar
responsables dels artefactes de les cantonades:
  corona_detall_v2_40 · camp net : el camp > 5,5–6,5 R☉ era el seu perfil azimutal (0,14–0,33, fosc) → Overlay
                                   enfosquia el camp −3,5 % on la màscara val 0,10 i 0 als triangles del marc Sony
                                   → triangles +3,3/+3,5 punts MÉS CLARS al compost. Ara: > 5,5→6,5 R☉ = 0,5 exacte.
  CONTROL_NRGF_gris · camp net   : offset global +0,11 (el neutre era 0,61) i cunya clara als triangles → ara es
                                   recentra, s' = 0,5 + (s − m0(r))·w(r), w = 1 fins a 4,5 R☉ → 0 a 6; i 0,5 exacte fora
                                   de la validesa (taper 60 px).
Sortides a FD3_SCR/v8: corona_detall_v2_40_campnet_v8.npy, CONTROL_NRGF_campnet_v8.npy + TIF a FD3_OUT.
"""
import os, sys, numpy as np, cv2, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import smooth01
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
ROOT = os.path.dirname(SCR); V8 = os.path.join(SCR, 'v8')
OUT = os.environ.get('FD3_OUT', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10'))
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32); rR = rr / R_SOL
z = np.load(os.path.join(ROOT, 'treball3', 'lum_llenc.npz')); vc = z['valid_c']
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))
vcE = cv2.erode(vc.astype(np.uint8), k, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
dist = cv2.distanceTransform(vcE.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
tap = smooth01(dist / 60.0).astype(np.float32)
# la validesa de lum_llenc no inclou el disc lunar: el taper NOMÉS actua al camp exterior (r > 3 R☉); el limbe i les
# protuberàncies queden exactament com eren
tap = (1.0 - (1.0 - tap) * smooth01((rR - 2.5) / 0.5)).astype(np.float32)
def perfil_m0(img, dr=4.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1).ravel()
    s_ = np.bincount(idx, weights=img.ravel().astype(np.float64), minlength=n); c = np.bincount(idx, minlength=n)
    p = np.where(c > 0, s_ / np.maximum(c, 1), np.nan); ok = np.isfinite(p); r_c = (np.arange(n) + 0.5) * dr
    return np.interp(rr, r_c[ok], p[ok]).astype(np.float32)
def escriu(nom, rgb, desc):
    np.save(os.path.join(V8, nom + '.npy'), rgb)
    tifffile.imwrite(os.path.join(OUT, nom + '.tif'), rgb, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                     description=desc, extratags=[(34675, 7, len(ICC), ICC, False)])
    print('→', nom)
# 1) corona_detall_v2_40 camp net → camp llunyà neutre
v2 = np.load(os.path.join(SCR, 'capes3', 'corona_detall_v2_40_campnet.npy'))
keep = ((1 - smooth01((rR - 5.5) / 1.0)) * tap).astype(np.float32)
out = np.empty_like(v2)
for c in range(3):
    a = v2[..., c].astype(np.float32) / 65535.0
    out[..., c] = u16(0.5 + (a - 0.5) * keep)
escriu('corona_detall_v2_40_campnet_v8', out, 'corona_detall_v2_40 camp net; > 5.5-6.5 R i fora de dades = 0.5 exacte (abans: perfil azimutal fosc -> triangles clars). 2026-08-19')
del v2, out
# 2) CONTROL_NRGF camp net → recentrat i neutre fora
nr = np.load(os.path.join(SCR, 'capes3', 'CONTROL_NRGF_campnet.npy'))
w = ((1 - smooth01((rR - 4.5) / 1.5)) * tap).astype(np.float32)
w_in = smooth01((rR - 1.15) / 0.25).astype(np.float32)      # dins d'1,15 R☉ (limbe, protuberàncies) la capa queda EXACTAMENT com era
out = np.empty_like(nr)
for c in range(3):
    a = nr[..., c].astype(np.float32) / 65535.0
    m0 = perfil_m0(a)
    nou = 0.5 + (a - m0) * w
    out[..., c] = u16(a + w_in * (nou - a))
    print('NRGF canal', c, 'm0 a 1.2/2/4/6 R:', [round(float(m0[int(SOL[1]), int(SOL[0] + R * R_SOL)]), 3) for R in (1.2, 2, 4, 6)])
escriu('CONTROL_NRGF_campnet_v8', out, 'CONTROL_NRGF_gris camp net, recentrat (0.5 + (s - m0)*w, w 1 fins a 4.5 R -> 0 a 6; dins d 1.15 R identic a l original) i 0.5 exacte fora de dades (abans: neutre 0.61, cunya als triangles). 2026-08-19')
print('fi')
