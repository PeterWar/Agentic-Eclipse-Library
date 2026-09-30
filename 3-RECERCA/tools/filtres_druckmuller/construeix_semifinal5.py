"""FiltresSEMIFINAL5.psb = FiltresSEMIFINAL4.psb + la capa «DETALL EXTERIOR (coherència dels dos trens, apilat
Sony v2)» (Linear Light 40 %, visible) amb la seva màscara radial, just damunt de les dues HALO.
La imatge fusionada es recalcula amb les capes visibles."""
import os, sys, time, numpy as np, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, set_merged, finalize_lr16
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo')
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL4.psb')
OUT = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL5.psb')
DET = os.environ.get('S5_DET', os.path.join(HO, 'detall_exterior_COH_v2.npy')); DMK = os.environ.get('S5_MK', os.path.join(HO, 'mascara_exterior_v2.npy'))
OPAC = int(os.environ.get('S5_OP', 102))
W, H = 7648, 5353; COMP = Compression.ZIP
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def overlay(b, s): return np.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))
psd4 = PSDImage.open(SRC); icc = psd4.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd4)
def chans(l):
    rec = l._record; out = {}
    Hh = rec.bottom - rec.top; Ww = rec.right - rec.left
    for info, cd in zip(rec.channel_info, l._channels):
        cid = int(info.id)
        if cid == -2:
            md = rec.mask_data; h = md.bottom - md.top; w = md.right - md.left
            out['mask'] = (np.frombuffer(cd.get_data(w, h, 16, 2), '>u2').reshape(h, w).copy(), md.top, md.left)
        elif cid in (0, 1, 2):
            out[cid] = np.frombuffer(cd.get_data(Ww, Hh, 16, 2), '>u2').reshape(Hh, Ww)
    return out
comp = None
def blend_into(comp, rgb16, mask, top, left, blend, op, visible):
    if not visible: return comp
    h, w = rgb16.shape[:2]; sl = (slice(top, top + h), slice(left, left + w))
    s = rgb16.astype(np.float32) / 65535.0
    if comp is None:
        comp = np.zeros((H, W, 3), np.float32); comp[sl] = s; return comp
    b = comp[sl]
    if blend == BlendMode.OVERLAY: bl = overlay(b, s)
    elif blend == BlendMode.LINEAR_LIGHT: bl = np.clip(b + 2 * s - 1, 0, 1)
    elif blend == BlendMode.NORMAL: bl = s
    else: raise ValueError(blend)
    f = op / 255.0
    if mask is not None:
        m16, mt, ml = mask
        f = f * (m16[top - mt:top - mt + h, left - ml:left - ml + w].astype(np.float32) / 65535.0)[..., None]
    comp[sl] = b + f * (bl - b); return comp
for i, l in enumerate(psd4):
    c = chans(l); rec = l._record
    rgb = np.stack([c[0], c[1], c[2]], -1)
    lyr = add_pixel_layer(psd, np.ascontiguousarray(rgb), l.name, top=rec.top, left=rec.left, blend=l.blend_mode, opacity=l.opacity, visible=l.visible, compression=COMP)
    mask = c.get('mask')
    if mask is not None: add_mask16(lyr, mask[0], top=mask[1], left=mask[2])
    comp = blend_into(comp, rgb, mask, rec.top, rec.left, l.blend_mode, l.opacity, l.visible)
    log(f'capa {i} {l.name[:40]!r}')
    if l.name.startswith('HALO suau'):
        det = np.load(DET); mk = np.load(DMK)
        lyr2 = add_pixel_layer(psd, det, 'DETALL EXTERIOR · coherència Vixen–Sony (apilat v2 de 13 fotogrames; correlació local per banda, control nul 8–26×), 2,8–7,5 R☉, bandes 0,8–9° (Linear Light 25 %; detall_exterior_v2.py 19-08)',
                               blend=BlendMode.LINEAR_LIGHT, opacity=OPAC, visible=True, compression=COMP)
        add_mask16(lyr2, mk, top=0, left=0)
        comp = blend_into(comp, det, (mk, 0, 0), 0, 0, BlendMode.LINEAR_LIGHT, OPAC, True)
        log('capa DETALL EXTERIOR inserida')
        del det
finalize_lr16(psd)
merged = u16(comp); np.save(os.path.join(HO, 'semifinal5_merged.npy'), merged); set_merged(psd, merged)
log('escrivint', OUT); psd.save(OUT); log('desat', os.path.getsize(OUT) / 1e9, 'GB')
