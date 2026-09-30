"""CapesInteriors.psb (6961×4641) → llenç 7648×5353 amb totes les capes desplaçades (+456, +462), de manera
que coincideixi píxel a píxel amb CapesExteriors.psb (mesurat: la capa 03_1s d'Interiors i la d'Exteriors
tenen el mateix contingut a I+(456,462) = E, pic 0,96; i Capa 1 = TIFF a I(−457,−463) ↔ EDITAT PERE =
TIFF a E(−1,−1)). Es conserva tot (capes, màscares, opacitats, blocs de Photoshop); es treu el bloc
Mt16 (transparència fusionada de la mida antiga) i el recurs de talls (SLICES) de la mida antiga.
La imatge fusionada nova = el TIFF ESTESA a (−1,−1) i, a sobre, la fusionada antiga a (456,462).
També: CapesExteriors.psb → la capa 01_10.3s es mou (+2, −1) (mesurat contra EDITAT/03: era a (−2,+1)).
Els originals es guarden com a *_abans_redimensionar.psb."""
import os, shutil, numpy as np, tifffile
from psd_tools import PSDImage
from psd_tools.constants import Tag, Resource, Compression
from psb_utils import set_merged

DI = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
DE = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/')
TIF = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif')
DX, DY = 456, 462
W, H = 7648, 5353

def shift_layer(l, dx, dy):
    rec = l._record
    rec.left += dx; rec.right += dx; rec.top += dy; rec.bottom += dy
    if rec.mask_data is not None:
        md = rec.mask_data
        md.left += dx; md.right += dx; md.top += dy; md.bottom += dy
        if getattr(md, 'real_left', None) is not None and md.real_flags is not None:
            md.real_left += dx; md.real_right += dx; md.real_top += dy; md.real_bottom += dy
    # punt de referència (fxrp), si hi és
    tb = rec.tagged_blocks
    if tb is not None and Tag.REFERENCE_POINT in tb:
        rp = tb.get_data(Tag.REFERENCE_POINT)
        try:
            rp[0] += dx; rp[1] += dy
        except Exception:
            pass

# ---------------- CapesInteriors ----------------
src = DI + 'CapesInteriors.psb'
bak = DI + 'CapesInteriors_abans_redimensionar.psb'
if not os.path.exists(bak):
    shutil.copy2(src, bak); print('còpia de seguretat:', bak)
psd = PSDImage.open(src)
hdr = psd._record.header
print('Interiors abans:', hdr.width, hdr.height, len(list(psd)), 'capes')
# fusionada antiga (16 bits) → la nova
old = psd._record.image_data.get_data(hdr)          # llista de bytes per canal
oldW, oldH = hdr.width, hdr.height
oldm = np.stack([np.frombuffer(c, dtype='>u2').reshape(oldH, oldW) for c in old[:3]], -1).astype(np.uint16)
tif = tifffile.imread(TIF)
assert tif.shape == (H, W, 3)
merged = np.zeros((H, W, 3), np.uint16)
merged[:H - 1, :W - 1] = tif[1:, 1:]                 # el TIFF a (−1,−1)
merged[DY:DY + oldH, DX:DX + oldW] = oldm            # la fusionada antiga a (+456,+462)
for l in psd.descendants():
    shift_layer(l, DX, DY)
hdr.width, hdr.height = W, H
lm = psd._record.layer_and_mask_information
if lm.tagged_blocks is not None and Tag.SAVING_MERGED_TRANSPARENCY16 in lm.tagged_blocks:
    del lm.tagged_blocks[Tag.SAVING_MERGED_TRANSPARENCY16]; print('tret el bloc Mt16')
res = psd._record.image_resources
for k in (Resource.SLICES, Resource.THUMBNAIL_RESOURCE):
    if k in res:
        del res[k]; print('tret el recurs', k.name)
set_merged(psd, merged)
psd._updated = False
out = DI + 'CapesInteriors.psb'
psd.save(out)
print('desat', out, os.path.getsize(out) / 1e9, 'GB')

# ---------------- CapesExteriors: 01_10.3s (+2, −1) ----------------
srcE = DE + 'CapesExteriors.psb'
bakE = DE + 'CapesExteriors_abans_alinear01.psb'
if not os.path.exists(bakE):
    shutil.copy2(srcE, bakE); print('còpia de seguretat:', bakE)
E = PSDImage.open(srcE)
for l in E:
    if l.name.startswith('01_10.3s'):
        print('01 abans:', l.bbox, 'màscara', l.mask.bbox if l.mask else None)
        shift_layer(l, +2, -1)
        print('01 després:', l.bbox, 'màscara', l.mask.bbox if l.mask else None)
E._updated = False
E.save(srcE)
print('desat', srcE, os.path.getsize(srcE) / 1e9, 'GB')
