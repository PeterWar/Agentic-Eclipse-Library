"""FiltresSEMIFINAL3.psb (nit del 19-08-2026): la mateixa base que FiltresSEMIFINAL2.psb, les capes que
Pere hi tenia ACTIVES (Radials B, corona_detall_v2_40, CONTROL_NRGF_gris) amb les seves màscares, la capa
FLAT de correcció del camp (flat_camp.py) just damunt de la base, i tres prototips de filtre nous amb la seva
màscara (capes_semifinal3.py). RGB 16 bits, Display P3 (ICC de la SEMIFINAL2), PSB (Lr16).

Capes (de baix a dalt):
 0 Base (Normal 100 %)                                        = capa 0 de la SEMIFINAL2, byte a byte
 1 FLAT · correcció de camp (Linear Light 100 %, màscara blanca)
 2 Radials B · original de Pere (Overlay 100 %, OCULTA)      + la seva màscara
 3 Radials B · camp net (Overlay 100 %)                       + la seva màscara
 4 corona_detall_v2_40 · camp net (Overlay 58 %)             + la seva màscara
 5 CONTROL_NRGF_gris · camp net (Overlay 9 %)                + la seva màscara
 6-8 PROTOTIPS (Overlay 60 %, OCULTS): ESPENAK_multiescala, ACHF_lite_isotrop, ESPENAK_ampli + MASCARA_prototips
Imatge fusionada = composició de les capes visibles (calculada aquí, Overlay com Photoshop).
"""
import os, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, set_merged, finalize_lr16

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
C3 = os.path.join(SCR, 'capes3')
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL2.psb')
OUT = os.environ.get('FD3_PSB', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL3.psb'))
W, H = 7648, 5353
COMP = Compression.ZIP
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)

def carrega(nom):
    return np.load(os.path.join(SCR, nom), mmap_mode='r')

def overlay(b, s):
    return np.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))

psd2 = PSDImage.open(SRC)
icc = psd2.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd2)
log('document nou', W, H, 'ICC', len(icc))

# --- 0 base ---------------------------------------------------------------------------------
base = carrega('capa0_rgb16.npy')
add_pixel_layer(psd, np.ascontiguousarray(base), 'Base · Aplicant_Filtres.tif (fusionada; és el llenç E) · idèntica a la SEMIFINAL2',
                blend=BlendMode.NORMAL, compression=COMP)
log('capa 0 base')
comp = np.empty((H, W, 3), np.float32)
for c in range(3):
    comp[..., c] = np.asarray(base[..., c], np.float32) / 65535.0

# --- 1 FLAT ---------------------------------------------------------------------------------
flat = np.load(os.path.join(C3, 'FLAT_correccio_camp.npy'))
white = np.full((H, W), 65535, np.uint16)
lyr = add_pixel_layer(psd, flat, 'FLAT · correcció de camp (Linear Light; flat_camp.py 19-08; treu arcs, caixa, cantons, costura i gradient del cel)',
                      blend=BlendMode.LINEAR_LIGHT, compression=COMP)
add_mask16(lyr, white, top=0, left=0)
for c in range(3):
    comp[..., c] = np.clip(comp[..., c] + 2.0 * (flat[..., c].astype(np.float32) / 65535.0 - 0.5), 0, 1)
del flat
log('capa 1 FLAT')

# --- 2-3 Radials B --------------------------------------------------------------------------
rb0 = carrega('capa1_rgb16.npy'); m1 = np.ascontiguousarray(carrega('capa1_mask16.npy'))
lyr = add_pixel_layer(psd, np.ascontiguousarray(rb0), 'Radials B · original de Pere (Overlay al fitxer de Pere; signe normal) · E+(599,549)',
                      top=549, left=599, blend=BlendMode.OVERLAY, opacity=255, visible=False, compression=COMP)
add_mask16(lyr, m1, top=0, left=0)
log('capa 2 Radials B original (oculta)')
rbn = np.load(os.path.join(C3, 'RadialsB_campnet.npy'))
lyr = add_pixel_layer(psd, rbn, 'Radials B · camp net (idèntic fins a 4,5 R☉; > 6 R☉ sense els desplaçaments suaus, LP 60 px) · E+(599,549)',
                      top=549, left=599, blend=BlendMode.OVERLAY, opacity=255, visible=True, compression=COMP)
add_mask16(lyr, m1, top=0, left=0)
sl = (slice(549, 549 + rbn.shape[0]), slice(599, 599 + rbn.shape[1]))
mm = m1[sl].astype(np.float32) / 65535.0
for c in range(3):
    b = comp[sl][..., c]; s = rbn[..., c].astype(np.float32) / 65535.0
    comp[sl][..., c] = b + mm * (overlay(b, s) - b)
del rbn, rb0, m1, mm
log('capa 3 Radials B camp net')

# --- 4 v2_40 --------------------------------------------------------------------------------
v2 = np.load(os.path.join(C3, 'corona_detall_v2_40_campnet.npy')); m3 = np.ascontiguousarray(carrega('capa3_mask16.npy'))
lyr = add_pixel_layer(psd, v2, 'corona_detall_v2_40 · camp net (idèntic fins a 5,5 R☉; més enllà = perfil azimutal)',
                      blend=BlendMode.OVERLAY, opacity=148, visible=True, compression=COMP)
add_mask16(lyr, m3, top=0, left=0)
mm = m3.astype(np.float32) / 65535.0 * (148 / 255.0)
for c in range(3):
    b = comp[..., c]; s = v2[..., c].astype(np.float32) / 65535.0
    comp[..., c] = b + mm * (overlay(b, s) - b)
del v2, m3, mm
log('capa 4 v2_40 camp net')

# --- 5 NRGF ---------------------------------------------------------------------------------
nr = np.load(os.path.join(C3, 'CONTROL_NRGF_campnet.npy')); m7 = np.ascontiguousarray(carrega('capa7_mask16.npy'))
lyr = add_pixel_layer(psd, nr, 'CONTROL_NRGF_gris · camp net (idèntic fins a 4,5 R☉; més enllà sense l\'estructura de gran escala)',
                      blend=BlendMode.OVERLAY, opacity=23, visible=True, compression=COMP)
add_mask16(lyr, m7, top=0, left=0)
mm = m7.astype(np.float32) / 65535.0 * (23 / 255.0)
for c in range(3):
    b = comp[..., c]; s = nr[..., c].astype(np.float32) / 65535.0
    comp[..., c] = b + mm * (overlay(b, s) - b)
del nr, m7, mm
log('capa 5 NRGF camp net')

# --- 6-8 prototips --------------------------------------------------------------------------
mp = np.load(os.path.join(C3, 'MASCARA_prototips.npy'))
for nom, titol in (('ESPENAK_multiescala', 'PROTOTIP · ESPENAK multiescala (unsharp radial Spin 2°+6°+18°, sobre la base corregida) · Overlay 60 %'),
                   ('ACHF_lite_isotrop', 'PROTOTIP · ACHF-lite isòtrop (unsharp gaussià σ 12+36 px; veu radials i tangencials) · Overlay 60 %'),
                   ('ESPENAK_ampli', 'PROTOTIP · ESPENAK ampli (unsharp polar 6° d\'arc × 30 px radials) · Overlay 60 %')):
    a = np.load(os.path.join(C3, nom + '.npy'))
    lyr = add_pixel_layer(psd, a, titol, blend=BlendMode.OVERLAY, opacity=153, visible=False, compression=COMP)
    add_mask16(lyr, mp, top=0, left=0)
    del a
    log('capa prototip', nom)

# --- tanca ----------------------------------------------------------------------------------
finalize_lr16(psd)
merged = np.clip(np.rint(comp * 65535.0), 0, 65535).astype(np.uint16)
np.save(os.path.join(SCR, 'semifinal3_merged.npy'), merged)
set_merged(psd, merged)
log('escrivint', OUT)
psd.save(OUT)
log('desat', os.path.getsize(OUT) / 1e9, 'GB')
