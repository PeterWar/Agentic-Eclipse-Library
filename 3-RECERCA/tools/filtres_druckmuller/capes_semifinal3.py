"""Capes per a FiltresSEMIFINAL3.psb (nit del 19-08-2026). Llegeix del scratchpad sf3:
  capa0_rgb16.npy (base), capa1/3/7 (Radials B, corona_detall_v2_40, CONTROL_NRGF_gris) + màscares,
  flat_corr.npy (correcció del camp, de flat_camp.py)
i escriu a FD3_SCR/capes3/*.npy (uint16) + TIF 16 bits a FD3_OUT:

  FLAT_correccio_camp          Linear Light: 0,5 − Corr/2 (restar la correcció a la base)
  RadialsB_campnet             el radial B de Pere amb el camp llunyà (> 4,5 R☉) sense els desplaçaments
                               suaus (passabaix σ 60 px) que hi deixaven un pedaç i cantons foscos
  corona_detall_v2_40_campnet  el v2_40 amb el camp > 5,5–6,5 R☉ substituït pel seu perfil azimutal
  CONTROL_NRGF_campnet         el NRGF amb l'estructura no radial de gran escala (σ 120 px) treta
                               a partir de 4,5–6 R☉ (era ±0,5 i deixava un gradient de 2 nivells al 9 %)
  ESPENAK_multiescala          unsharp radial (Spin) a 2°, 6° i 18°, sumat: el «relleu» de Pere a tres escales
  ACHF_lite_isotrop            unsharp gaussià isòtrop σ 12 i 36 px (Druckmüller tesi §5.2, nucli isòtrop):
                               veu també les tangencials, sense fase direccional
  ESPENAK_ampli                unsharp anisòtrop en polars: σ_θ 6° i σ_r 30 px (l'Espenak que no és cec)
  + màscares radials per als tres prototips (0 al disc, 1 d'1,1 a 5,5 R☉, 0 a 7 R☉).
Tots els prototips es calculen sobre la LUMINÀNCIA de la base JA CORREGIDA de camp, capa grisa 50 % + k·HP.
"""
import os, sys, math, time, json
import numpy as np, cv2, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import LogPolar, smooth01

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
OUT = os.environ.get('FD3_OUT', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10'))
C3 = os.path.join(SCR, 'capes3'); os.makedirs(C3, exist_ok=True); os.makedirs(OUT, exist_ok=True)
W, H = 7648, 5353
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495; R_LLUNA = 452.5; LLUNA = (4034.7, 2736.7)
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def gauss(a, s): return cv2.GaussianBlur(np.ascontiguousarray(a, np.float32), (0, 0), s, borderType=cv2.BORDER_REFLECT)

def escriu_tif(nom, rgb16, desc=''):
    tifffile.imwrite(os.path.join(OUT, nom + '.tif'), rgb16, photometric='rgb' if rgb16.ndim == 3 else 'minisblack',
                     compression='zlib', metadata=None, resolution=(300, 300), description=desc.encode('ascii', 'replace').decode(),
                     extratags=[(34675, 7, len(ICC), ICC, False)])
    log('→', nom + '.tif', rgb16.shape)

def previa(nom, a01, amplia=1.0, centre=None):
    a = np.asarray(a01, np.float32)
    if centre is not None: a = (a - centre) * amplia + centre
    p = cv2.resize(np.clip(a, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    if p.ndim == 3: p = p[..., ::-1]
    cv2.imwrite(os.path.join(C3, nom + '_x4.jpg'), (p * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])

yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
r_ll = np.hypot(np.arange(W, dtype=np.float32)[None, :] - LLUNA[0], np.arange(H, dtype=np.float32)[:, None] - LLUNA[1]).astype(np.float32)

def perfil_m0(img, dr=4.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1).ravel()
    s = np.bincount(idx, weights=img.ravel().astype(np.float64), minlength=n); c = np.bincount(idx, minlength=n)
    p = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    ok = np.isfinite(p); r_c = (np.arange(n) + 0.5) * dr
    return np.interp(rr, r_c[ok], p[ok]).astype(np.float32)

# ------------------------------------------------------------------ base, correcció, base corregida
base = np.load(os.path.join(SCR, 'capa0_rgb16.npy'), mmap_mode='r')
Corr = np.load(os.path.join(SCR, 'flat_corr.npy'), mmap_mode='r')
flat = np.empty((H, W, 3), np.uint16)
bcor = np.empty((H, W, 3), np.float32)
for c in range(3):
    flat[..., c] = u16(0.5 - np.asarray(Corr[..., c]) / 2.0)
    bcor[..., c] = np.clip(np.asarray(base[..., c], np.float32) / 65535.0 - np.asarray(Corr[..., c]), 0, 1)
np.save(os.path.join(C3, 'FLAT_correccio_camp.npy'), flat)
escriu_tif('FLAT_correccio_camp', flat, 'Linear Light sobre la base: 0.5 - Corr/2. flat_camp.py 2026-08-19')
np.save(os.path.join(C3, 'Base_corregida_camp.npy'), u16(bcor))
escriu_tif('Base_corregida_camp', u16(bcor), 'Base (Aplicant_Filtres) menys la correccio de camp. flat_camp.py 2026-08-19')
previa('FLAT_correccio_camp', flat / 65535.0, amplia=8.0, centre=0.5)
del flat
lum = bcor.mean(-1).astype(np.float32)
del bcor
log('base corregida i FLAT fets')

# ------------------------------------------------------------------ Radials B camp net
rb = np.load(os.path.join(SCR, 'capa1_rgb16.npy'))            # (4553, 6748, 3) a E+(599,549)
h1, w1 = rb.shape[:2]; top1, left1 = 549, 599
rr1 = rr[top1:top1 + h1, left1:left1 + w1]
w_far = smooth01((rr1 - 4.5 * R_SOL) / (1.5 * R_SOL)).astype(np.float32)
rbn = np.empty_like(rb)
for c in range(3):
    a = rb[..., c].astype(np.float32) / 65535.0
    lp = gauss(a - 0.5, 60.0)
    rbn[..., c] = u16(a - w_far * lp)
np.save(os.path.join(C3, 'RadialsB_campnet.npy'), rbn)
escriu_tif('RadialsB_campnet', rbn, 'Radial B de Pere; camp > 4.5-6 R sense desplacaments suaus (LP 60 px). Posar a E+(599,549).')
previa('RadialsB_campnet', np.pad(rbn, ((top1, H - top1 - h1), (left1, W - left1 - w1), (0, 0)), constant_values=32768) / 65535.0, amplia=5.0, centre=0.5)
del rb, rbn, lp, a
log('Radials B net')

# ------------------------------------------------------------------ v2_40 camp net
v2 = np.load(os.path.join(SCR, 'capa3_rgb16.npy'))
w_v2 = smooth01((rr - 5.5 * R_SOL) / (1.0 * R_SOL)).astype(np.float32)
v2n = np.empty_like(v2)
for c in range(3):
    a = v2[..., c].astype(np.float32) / 65535.0
    m0 = perfil_m0(a)
    v2n[..., c] = u16(a + w_v2 * (m0 - a))
np.save(os.path.join(C3, 'corona_detall_v2_40_campnet.npy'), v2n)
escriu_tif('corona_detall_v2_40_campnet', v2n, 'corona_detall_v2_40; camp > 5.5-6.5 R = perfil azimutal (no hi ha detall alla).')
previa('corona_detall_v2_40_campnet', v2n / 65535.0)
del v2, v2n, m0, a
log('v2_40 net')

# ------------------------------------------------------------------ NRGF camp net
nr = np.load(os.path.join(SCR, 'capa7_rgb16.npy'))
w_nr = smooth01((rr - 4.5 * R_SOL) / (1.5 * R_SOL)).astype(np.float32)
nrn = np.empty_like(nr)
for c in range(3):
    a = nr[..., c].astype(np.float32) / 65535.0
    m0 = perfil_m0(a)
    lp = gauss(a - m0, 120.0)
    nrn[..., c] = u16(a - w_nr * lp)
np.save(os.path.join(C3, 'CONTROL_NRGF_campnet.npy'), nrn)
escriu_tif('CONTROL_NRGF_campnet', nrn, 'CONTROL_NRGF_gris; estructura no radial de gran escala (LP 120 px) treta a partir de 4.5-6 R.')
previa('CONTROL_NRGF_campnet', nrn / 65535.0)
del nr, nrn, m0, lp, a
log('NRGF net')

# ------------------------------------------------------------------ prototips sobre la luminància corregida
lp_ = LogPolar(H, W, SOL[0], SOL[1], NA=8192, NR=3072, r_min=400.0)
disc = (r_ll < R_LLUNA + 2).astype(np.float32)
# dins del disc: omplim amb el valor del limbe per no arrossegar el negre als filtres
lum_f = lum.copy()
ring = (r_ll >= R_LLUNA + 2) & (r_ll < R_LLUNA + 12)
lum_f[disc > 0] = float(np.median(lum[ring]))
P = lp_.cap_a_polar(lum_f)                    # (NA, NR)
okp = lp_.cap_a_polar(np.ones((H, W), np.float32))
mask_proto = smooth01((r_ll - (R_LLUNA + 4)) / 60.0) * (1 - smooth01((rr - 5.5 * R_SOL) / (1.5 * R_SOL)))
mask_proto = mask_proto.astype(np.float32)
np.save(os.path.join(C3, 'MASCARA_prototips.npy'), u16(mask_proto))
escriu_tif('MASCARA_prototips', u16(mask_proto), 'Mascara radial per als prototips: 0 al disc, 1 d 1.1 a 5.5 R, 0 a 7 R.')

def blur_norm(P, s_rho, s_ang):
    """desenfoc polar normalitzat per la cobertura del marc (fora del llenç no hi ha dades)."""
    return lp_.desenfoca_polar(P * okp, s_rho, s_ang) / np.maximum(lp_.desenfoca_polar(okp, s_rho, s_ang), 1e-3)

def spin_unsharp(P, sig_deg):
    """Espenak: desenfoc només al llarg de l'arc (σ en graus), diferència."""
    s_ang = sig_deg * lp_.px_deg
    return (P - blur_norm(P, 0.3, s_ang)) * okp

def capa_grisa(nom, HP, k, desc):
    capa = np.clip(0.5 + k * HP, 0, 1)
    capa = capa * (1 - disc) + 0.5 * disc
    rgb = np.repeat(u16(capa)[..., None], 3, axis=2)
    np.save(os.path.join(C3, nom + '.npy'), rgb)
    escriu_tif(nom, rgb, desc)
    previa(nom, capa, amplia=4.0, centre=0.5)
    print(f'   {nom}: HP p1/p99 (1.1-3 R) {np.percentile(HP[(rr>1.1*R_SOL)&(rr<3*R_SOL)],[1,99])}, (3-6 R) {np.percentile(HP[(rr>3*R_SOL)&(rr<6*R_SOL)],[1,99])}')
    return rgb

# P1 Espenak multiescala
HP = np.zeros((H, W), np.float32)
for sd, wgt in ((2.0, 0.4), (6.0, 0.35), (18.0, 0.25)):
    HP += wgt * lp_.cap_a_imatge(spin_unsharp(P, sd))
capa_grisa('ESPENAK_multiescala', HP, 2.0, 'Unsharp radial (Spin) a 2, 6 i 18 graus (0.4/0.35/0.25) sobre la luminancia de la base corregida. Overlay 50-70 %.')
del HP
# P2 ACHF-lite isòtrop
HP = 0.5 * (lum_f - gauss(lum_f, 12.0)) + 0.5 * (lum_f - gauss(lum_f, 36.0))
capa_grisa('ACHF_lite_isotrop', HP, 2.0, 'Unsharp gaussia isotrop sigma 12 i 36 px (Druckmuller tesi 5.2, nucli isotrop). Overlay 50-70 %.')
del HP
# P3 Espenak ampli (anisòtrop polar: 6° en arc, 30 px radials)
s_ang = 6.0 * lp_.px_deg
# σ radial en px de la imatge → en columnes log-polars depèn del radi; aproximem amb la σ a 2,5 R☉
s_rho = 30.0 / (2.5 * R_SOL) * lp_.K
Pb = blur_norm(P, s_rho, s_ang)
HP = lp_.cap_a_imatge((P - Pb) * okp)
capa_grisa('ESPENAK_ampli', HP, 2.0, 'Unsharp anisotrop en polars: 6 graus d arc i ~30 px radials (a 2.5 R). Overlay 50-70 %.')
del HP, Pb
log('prototips fets')
json.dump(dict(SOL=SOL, R_SOL=R_SOL, capes=['FLAT_correccio_camp', 'Base_corregida_camp', 'RadialsB_campnet', 'corona_detall_v2_40_campnet',
               'CONTROL_NRGF_campnet', 'MASCARA_prototips', 'ESPENAK_multiescala', 'ACHF_lite_isotrop', 'ESPENAK_ampli']),
          open(os.path.join(C3, 'capes3.json'), 'w'), indent=1)
log('fi')
