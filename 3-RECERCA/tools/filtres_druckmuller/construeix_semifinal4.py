"""FiltresSEMIFINAL4.psb = la FiltresSEMIFINAL3.psb TAL COM L'HA DEIXADA PERE (capes, màscares, opacitats,
visibilitats, ordre) + dues capes noves just damunt de la FLAT:
   HALO fora  (Linear Light, visible)  = 0,5 + Δ_fora/2   (halo_uniforme.py, R1 3,2 → R2 5,5 R☉)
   HALO suau  (Linear Light, oculta)   = 0,5 + Δ_suau/2   (R2 7 R☉)
amb la mateixa màscara que Pere va pintar a la FLAT (blanca menys la zona de les protuberàncies).
També escriu els TIF de les dues capes i la base plana (base + FLAT + HALO fora) per a PixInsight.
Imatge fusionada = composició de les capes visibles (Overlay/Linear Light com Photoshop).
"""
import os, sys, time, numpy as np, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression, ChannelID
from psb_utils import new_psb, add_pixel_layer, add_mask16, set_merged, finalize_lr16

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo')
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL3.psb')
OUT = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL4.psb')
TIFD = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10')
W, H = 7648, 5353
COMP = Compression.ZIP
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def overlay(b, s): return np.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))

psd3 = PSDImage.open(SRC)
icc = psd3.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd3)
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
        mm = m16[top - mt:top - mt + h, left - ml:left - ml + w].astype(np.float32) / 65535.0
        f = f * mm[..., None]
    comp[sl] = b + f * (bl - b)
    return comp

halo_mask = None
for i, l in enumerate(psd3):
    c = chans(l); rec = l._record
    rgb = np.stack([c[0], c[1], c[2]], -1)
    lyr = add_pixel_layer(psd, np.ascontiguousarray(rgb), l.name, top=rec.top, left=rec.left, blend=l.blend_mode,
                          opacity=l.opacity, visible=l.visible, compression=COMP)
    mask = c.get('mask')
    if mask is not None:
        add_mask16(lyr, mask[0], top=mask[1], left=mask[2])
    comp = blend_into(comp, rgb, mask, rec.top, rec.left, l.blend_mode, l.opacity, l.visible)
    log(f'capa {i} {l.name[:40]!r} vis={l.visible} op={l.opacity} {l.blend_mode.name}')
    if i == 1:
        halo_mask = mask[0].copy() if mask is not None else np.full((H, W), 65535, np.uint16)
        base_flat = comp.copy()
        # --- les dues capes del HALO, just damunt de la FLAT ---------------------------------
        for tag, vis, titol in (('fora', True, 'HALO fora · resta la component uniforme de la corona de 3,2 a 6 R☉ (envolupant p25 per anell) i corba sense terra (Linear Light; halo_uniforme.py 19-08)'),
                                ('suau', False, 'HALO suau · el mateix però de 3,2 a 7,5 R☉ (Linear Light, oculta; activa aquesta i desactiva «fora» si vols conservar una mica de resplendor)')):
            d = np.load(os.path.join(HO, f'uniform_delta_{tag}.npy'), mmap_mode='r')
            lay = np.empty((H, W, 3), np.uint16)
            for cc in range(3): lay[..., cc] = u16(0.5 + np.asarray(d[..., cc]) / 2.0)
            lyr2 = add_pixel_layer(psd, lay, titol, blend=BlendMode.LINEAR_LIGHT, opacity=255, visible=vis, compression=COMP)
            add_mask16(lyr2, halo_mask, top=0, left=0)
            tifffile.imwrite(os.path.join(TIFD, f'HALO_{tag}_LinearLight.tif'), lay, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                             description=f'HALO {tag}: Linear Light damunt de base+FLAT. halo_uniforme.py 2026-08-19', extratags=[(34675, 7, len(icc), icc, False)])
            comp = blend_into(comp, lay, (halo_mask, 0, 0), 0, 0, BlendMode.LINEAR_LIGHT, 255, vis)
            if vis:
                np.save(os.path.join(HO, 'base_flat_halo_fora.npy'), u16(comp))
                tifffile.imwrite(os.path.join(TIFD, 'Base_corregida_camp_i_halo.tif'), u16(comp), photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                                 description='Base + FLAT + HALO fora, plana (per a PixInsight). 2026-08-19', extratags=[(34675, 7, len(icc), icc, False)])
            log('capa HALO', tag)
            del lay, d

# --- capa ANELL a dalt de tot: compensa la mitjana radial dels filtres Overlay (anell_compensa_filtres.py) ------------
def smootherstep(t):
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)
def mediana_anells(img, rr, dr, r_min=0.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1)
    sel = rr >= r_min; v = img[sel]; ii = idx[sel]
    order = np.argsort(ii, kind='stable'); v = v[order]; ii = ii[order]
    b = np.searchsorted(ii, np.arange(n + 1))
    med = np.full(n, np.nan, np.float32)
    for k in range(n):
        if b[k + 1] - b[k] >= 30: med[k] = np.median(v[b[k]:b[k + 1]])
    return (np.arange(n) + 0.5) * dr, med
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
bfh = np.load(os.path.join(HO, 'base_flat_halo_fora.npy'), mmap_mode='r')
anell = np.empty((H, W, 3), np.uint16); rhos = []
for cc in range(3):
    r_c, mb = mediana_anells(np.asarray(bfh[..., cc], np.float32) / 65535.0, rr, 4.0, r_min=1.2 * R_SOL)
    r_c, mc = mediana_anells(comp[..., cc], rr, 4.0, r_min=1.2 * R_SOL)
    ok = np.isfinite(mb) & np.isfinite(mc)
    rho = np.interp(r_c, r_c[ok], (mb - mc)[ok]).astype(np.float32)
    rho *= smootherstep((r_c - 3.0 * R_SOL) / (0.8 * R_SOL))
    import cv2
    rho = cv2.GaussianBlur(rho.reshape(1, -1), (0, 0), 4.0, borderType=cv2.BORDER_REPLICATE).ravel()
    rho[r_c > 11.5 * R_SOL] = 0
    rhos.append(rho.tolist())
    d = np.interp(rr, r_c, rho).astype(np.float32)
    anell[..., cc] = u16(0.5 + d / 2.0)
    comp[..., cc] = np.clip(comp[..., cc] + d, 0, 1)
    log(f'ANELL canal {cc}: ρ a 3.5/4/5/6/7/8/9 R☉:', [round(float(np.interp(R * R_SOL, r_c, rho)), 4) for R in (3.5, 4, 5, 6, 7, 8, 9)])
import json; json.dump(dict(r_c=r_c.tolist(), rho=rhos), open(os.path.join(HO, 'anell_rho_psb4.json'), 'w'))
lyrA = add_pixel_layer(psd, anell, 'ANELL · compensa la mitjana radial dels filtres Overlay al camp exterior (Linear Light; radial i llisa; recalcular si canvies opacitats o màscares)',
                       blend=BlendMode.LINEAR_LIGHT, opacity=255, visible=True, compression=COMP)
add_mask16(lyrA, np.full((H, W), 65535, np.uint16), top=0, left=0)
tifffile.imwrite(os.path.join(TIFD, 'ANELL_compensa_filtres_LinearLight.tif'), anell, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                 description='ANELL: compensacio radial de la mitjana dels filtres Overlay. 2026-08-19', extratags=[(34675, 7, len(icc), icc, False)])
del anell
log('capa ANELL')
finalize_lr16(psd)
merged = u16(comp)
np.save(os.path.join(HO, 'semifinal4_merged.npy'), merged)
set_merged(psd, merged)
log('escrivint', OUT)
psd.save(OUT)
log('desat', os.path.getsize(OUT) / 1e9, 'GB')
