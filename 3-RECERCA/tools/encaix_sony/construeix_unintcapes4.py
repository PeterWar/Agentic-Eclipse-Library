"""UnintCapes4.psb: el projecte de Pere (UnintCapes3.psb: 1 s + 2 s + 10,3 s de l'HDR4 amb màscares)
més els retocs de la sessió del 18-08, tot com a capes imatge + màscara, al llenç estès de 7648×5353
(el de l'ESTESA_EXTENSIO_TANGENCIAL_MITJA que Pere ha triat). RGB 16 bits, Display P3, PSB (Lr16).

Capes (de baix a dalt):
 1. 03_1s (rasteritzada des de l'objecte intel·ligent de Pere), 2. 02_2s + màscara, 3. 01_10,3s + màscara (68 %)
    — les tres de Pere, desplaçades (+457, +463) perquè la reixa 6960×4640 caigui al seu lloc dins l'estès;
 4. Vixen — la capa Vixen processada de Pere (NoEncaixa) i, a les bandes de dalt/dreta, LUT(Vixen lineal);
 5. Sony 300 mm apilat ≥1 s aplanat i encaixat (LUT + residu) + MÀSCARA = pes de barreja w (corredor del raig inclòs);
 6. Correcció del graó HDR del 10,3 s (Linear Light) + màscara del sector;
 7. Detall tangencial MITJA (Linear Light, gris 50 % + D/2) + màscara blanca;
 8. Extensió radial k 1→1,4 (Linear Light) + màscara blanca;
 9. Cel pla (cosmètic, Linear Light), OCULTA, + màscara blanca.
Imatge fusionada = APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif (v4b).
"""
import os, sys, time, numpy as np, tifffile
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16

SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser('~/Downloads/UnintCapes4.psb')
SRC3 = os.path.expanduser('~/Downloads/UnintCapes3.psb')
TIF = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif')
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm          # 5353 × 7648
DY3, DX3 = T - 87, Lm - 143               # la reixa 6960×4640 de Pere dins l'estès: (463, 457)
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
COMP = Compression.ZIP_WITH_PREDICTION
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(a * 65535.0), 0, 65535).astype(np.uint16)
def u8(a): return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)

psd3 = PSDImage.open(SRC3)
icc = open(os.path.join(SP, 'perfil.icc'), 'rb').read()
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd3)
log('document nou', W, H)

# --- 1–3: les capes de Pere -------------------------------------------------------------------
l03, l02, l01 = psd3[0], psd3[1], psd3[2]
assert l03.name.startswith('03_') and l02.name.startswith('02_') and l01.name.startswith('01_')
a = l03.numpy()                       # float32 (h, w, 4) 0–1
log('03 rasteritzada', a.shape, a.dtype, float(a[..., :3].max()))
add_pixel_layer(psd, u16(a[..., :3]), l03.name + ' (rasteritzada des de l\'objecte intel·ligent d\'UnintCapes3)',
                top=l03.top + DY3, left=l03.left + DX3, compression=COMP)
del a
for lyr in (l02, l01):
    rec, chans = lyr._record, lyr._channels
    rec.top += DY3; rec.bottom += DY3; rec.left += DX3; rec.right += DX3
    if rec.mask_data is not None:
        rec.mask_data.top += DY3; rec.mask_data.bottom += DY3; rec.mask_data.left += DX3; rec.mask_data.right += DX3
    new = PixelLayer(psd, rec, chans)
    psd.append(new)
    log('reutilitzada', lyr.name, 'bbox', new.bbox, 'màscara', new.mask.bbox if new.mask is not None else None, 'opacitat', new.opacity)

# --- 4: Vixen (referència: capa de Pere / vix_ref) --------------------------------------------
fbk_in = np.load(os.path.join(SP, 'v4_fbk_in.npy'), mmap_mode='r')
L4 = np.array(fbk_in[sl])            # (H0, W0, 3) 0–1
add_pixel_layer(psd, u16(L4), 'Vixen · capa de Pere (NoEncaixa); a dalt i a la dreta LUT(Vixen lineal), sense l\'enfosquiment',
                top=T, left=Lm, compression=COMP)
log('capa 4 Vixen')

# --- 5: Sony aplanada i encaixada + màscara w --------------------------------------------------
gD = np.load(os.path.join(SP, 'v4_sony_gD.npy'), mmap_mode='r')
w = np.load(os.path.join(SP, 'v4_w.npy'))
fbk = np.load(os.path.join(SP, 'v4_fbk.npy'), mmap_mode='r')
valid = np.load(os.path.join(SP, 'v4_valid_px.npy'))
inside = np.zeros((H, W), bool); inside[sl] = True
img5 = np.where(valid[..., None], gD, fbk).astype(np.float32)
# fora del llenç no hi ha res a sota: la barreja s'hi cou dins la imatge i la màscara hi és blanca
outside = ~inside
img5[outside] = (np.asarray(gD)[outside] * w[outside, None] + np.asarray(fbk)[outside] * (1 - w[outside, None]))
mask5 = w.copy(); mask5[outside] = 1.0
add_pixel_layer(psd, u16(np.clip(img5, 0, 1)), 'Sony 300 mm · apilat ≥1 s (7 fotogrames, 24 s), aplanat amb el flat, encaixat a la Vixen (LUT + residu σ80)',
                top=0, left=0, mask8=u8(mask5), compression=COMP)
del img5, mask5, gD, fbk
log('capa 5 Sony + màscara w')

# --- 6: correcció del graó HDR (Linear Light) --------------------------------------------------
K = np.load(os.path.join(SP, 'K_grao_total.npy'))            # (H0, W0, 3)
d6 = 0.5 + (K - 1.0) * L4 / 2.0
zone = np.any(np.abs(K - 1.0) > 1e-4, axis=-1)
from scipy import ndimage as ndi
mask6 = ndi.binary_dilation(zone, iterations=8).astype(np.float32)
mask6 = ndi.gaussian_filter(mask6, 3)
add_pixel_layer(psd, u16(d6), 'Correcció del graó HDR al contorn del 10,3 s (sector) · LINEAR LIGHT',
                top=T, left=Lm, mask8=u8(mask6), blend=BlendMode.LINEAR_LIGHT, compression=COMP)
del d6, K, mask6, L4
log('capa 6 graó HDR')

# --- 7: detall tangencial MITJA (Linear Light) -------------------------------------------------
D = np.load(os.path.join(SP, 'D_tang_MITJA.npy'))             # (H, W) luminància, ja amb rampa i estrelles fora
fit = np.load(os.path.join(SP, 'fit_ext_VORESNETES_APILAT.npy'), mmap_mode='r')
enh = np.load(os.path.join(SP, 'enh_tang_MITJA.npy'), mmap_mode='r')
chk = float(np.abs((np.asarray(enh[2000:2100, 3000:3100]) - np.asarray(fit[2000:2100, 3000:3100])) - D[2000:2100, 3000:3100, None]).max())
log('comprovació enh = fit + D:', chk)
d7 = np.repeat((0.5 + D / 2.0)[..., None], 3, -1)
add_pixel_layer(psd, u16(d7), 'Detall tangencial MITJA (només azimutal, 0,6–16°, rampa 3,2→4,4 R☉) · LINEAR LIGHT',
                top=0, left=0, mask8=np.full((H, W), 255, np.uint8), blend=BlendMode.LINEAR_LIGHT, compression=COMP)
del d7, D
log('capa 7 detall')

# --- 8: extensió radial (Linear Light) --------------------------------------------------------
ext = np.load(os.path.join(SP, 'ext_tang_rgb.npy'), mmap_mode='r')
d8 = 0.5 + (np.asarray(ext) - np.asarray(enh)) / 2.0
add_pixel_layer(psd, u16(d8), 'Extensió radial k 1→1,4 (3,4→6 R☉) sobre base − cel · LINEAR LIGHT',
                top=0, left=0, mask8=np.full((H, W), 255, np.uint8), blend=BlendMode.LINEAR_LIGHT, compression=COMP)
del d8, enh, fit
log('capa 8 extensió')

# --- 9: cel pla (cosmètic, oculta) ------------------------------------------------------------
F1 = np.load(os.path.join(SP, 'celpla_factor.npy'))          # (H, W)
d9 = 0.5 + (F1[..., None] - 1.0) * np.asarray(ext) / 2.0
add_pixel_layer(psd, u16(d9), 'Cel pla (cosmètic: luminància del camp llunyà al nivell de 6 R☉, rampa 4,8→6,2) · LINEAR LIGHT · OCULTA',
                top=0, left=0, mask8=np.full((H, W), 255, np.uint8), blend=BlendMode.LINEAR_LIGHT, visible=False, compression=COMP)
del d9, F1, ext
log('capa 9 cel pla (oculta)')

# --- fusionada i desat -------------------------------------------------------------------------
blk = finalize_lr16(psd)
log('Lr16 amb', blk.layer_count, 'capes')
merged = tifffile.imread(TIF)
assert merged.shape == (H, W, 3) and merged.dtype == np.uint16
set_merged(psd, merged)
del merged
psd.save(OUT)
log('desat', OUT, os.path.getsize(OUT) / 1e9, 'GB')
