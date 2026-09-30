"""FiltresSEMIFINAL7.psb = FiltresSEMIFINAL6.psb + els tres filtres PROFUNDS (filtres_profunds_v7.py) just damunt del
DETALL EXTERIOR, cadascun amb la MASCARA_profund (0 dins de 2,6 R☉ → 1 a 3,6), Overlay:
   RADIALS profund  40 %   MGN profund  30 %   NRGF profund  8 %
i l'ANELL recalculat per al conjunt de capes visibles (mateixa lògica que construeix_semifinal4.py). Les capes de Pere
no es toquen (ni màscares, ni opacitats, ni visibilitats). La imatge fusionada es recalcula amb les capes visibles.
"""
import os, sys, time, json, numpy as np, cv2, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, set_merged, finalize_lr16
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo'); V7 = os.path.join(SCR, 'v7')
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL6.psb')
OUT = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL7.psb')
TIFD = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10')
OPS = dict(RADIALS_profund=int(os.environ.get('S7_OP_RAD', 102)), MGN_profund=int(os.environ.get('S7_OP_MGN', 77)), NRGF_profund=int(os.environ.get('S7_OP_NRGF', 20)))
TITOLS = dict(RADIALS_profund='RADIALS profund · Espenak multiescala (bandes angulars 0,4–2 / 2–6 / 6–18°) sobre la referència profunda (Vixen HDR + Sony v2, flat 300 mm, fons de Fourier), porta de soroll entre trens, mitjana zero per anell (Overlay 40 %; v7 19-08)',
              MGN_profund='MGN profund · bandes isòtropes 0,5–9° sobre la referència profunda, porta de soroll, normalització local amb pis d\'anell, mitjana zero per anell; les amples s\'apaguen de 4,5 a 7,5 R☉ (Overlay 30 %; v7 19-08)',
              NRGF_profund='NRGF profund · (ln L − fons m≤2) / σ de l\'anell amb pis de soroll, mitjana zero per anell, 4,5→7 R☉ (Overlay 8 %; v7 19-08)')
for _k, _v in TITOLS.items(): assert len(_v) <= 255, (_k, len(_v))
W, H = 7648, 5353; COMP = Compression.ZIP
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def overlay(b, s): return np.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))
def smootherstep(t):
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)
psd6 = PSDImage.open(SRC); icc = psd6.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd6)
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

# ANELL (mateixa lògica que construeix_semifinal4.py)
SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
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
def anell_recalcula(comp):
    bfh = np.load(os.path.join(HO, 'base_flat_halo_fora.npy'), mmap_mode='r')
    anell = np.empty((H, W, 3), np.uint16); rhos = []
    for cc in range(3):
        r_c, mb = mediana_anells(np.asarray(bfh[..., cc], np.float32) / 65535.0, rr, 4.0, r_min=1.2 * R_SOL)
        r_c, mc = mediana_anells(comp[..., cc], rr, 4.0, r_min=1.2 * R_SOL)
        ok = np.isfinite(mb) & np.isfinite(mc)
        rho = np.interp(r_c, r_c[ok], (mb - mc)[ok]).astype(np.float32)
        rho *= smootherstep((r_c - 3.0 * R_SOL) / (0.8 * R_SOL))
        rho = cv2.GaussianBlur(rho.reshape(1, -1), (0, 0), 4.0, borderType=cv2.BORDER_REPLICATE).ravel()
        rho[r_c > 11.5 * R_SOL] = 0
        rhos.append(rho.tolist())
        d = np.interp(rr, r_c, rho).astype(np.float32)
        anell[..., cc] = u16(0.5 + d / 2.0)
        comp[..., cc] = np.clip(comp[..., cc] + d, 0, 1)
        log(f'ANELL canal {cc}: ρ a 3.5/4/5/6/7/8/9 R☉:', [round(float(np.interp(R * R_SOL, r_c, rho)), 4) for R in (3.5, 4, 5, 6, 7, 8, 9)])
    json.dump(dict(r_c=r_c.tolist(), rho=rhos), open(os.path.join(HO, 'anell_rho_psb7.json'), 'w'))
    return anell, comp

mk7 = np.load(os.path.join(V7, 'mascara_profund.npy'))
for i, l in enumerate(psd6):
    c = chans(l); rec = l._record
    rgb = np.stack([c[0], c[1], c[2]], -1)
    mask = c.get('mask')
    if l.name.startswith('ANELL'):
        anell, comp = anell_recalcula(comp)
        lyr = add_pixel_layer(psd, anell, 'ANELL · compensa la mitjana radial dels filtres Overlay al camp exterior (Linear Light; radial i llisa; RECALCULAT per a la SEMIFINAL7; recalcular si canvies opacitats o màscares)',
                              blend=BlendMode.LINEAR_LIGHT, opacity=255, visible=True, compression=COMP)
        add_mask16(lyr, np.full((H, W), 65535, np.uint16), top=0, left=0)
        tifffile.imwrite(os.path.join(TIFD, 'ANELL_compensa_filtres_LinearLight_SF7.tif'), anell, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                         description='ANELL recalculat per a la SEMIFINAL7. 2026-08-19', extratags=[(34675, 7, len(icc), icc, False)])
        del anell
        log('capa ANELL recalculada')
        continue
    lyr = add_pixel_layer(psd, np.ascontiguousarray(rgb), l.name, top=rec.top, left=rec.left, blend=l.blend_mode, opacity=l.opacity, visible=l.visible, compression=COMP)
    if mask is not None: add_mask16(lyr, mask[0], top=mask[1], left=mask[2])
    comp = blend_into(comp, rgb, mask, rec.top, rec.left, l.blend_mode, l.opacity, l.visible)
    log(f'capa {i} {l.name[:40]!r}')
    if l.name.startswith('DETALL EXTERIOR'):
        for nom in ('RADIALS_profund', 'MGN_profund', 'NRGF_profund'):
            lay = np.load(os.path.join(V7, nom + '.npy'))
            lyr2 = add_pixel_layer(psd, lay, TITOLS[nom], blend=BlendMode.OVERLAY, opacity=OPS[nom], visible=True, compression=COMP)
            add_mask16(lyr2, mk7, top=0, left=0)
            comp = blend_into(comp, lay, (mk7, 0, 0), 0, 0, BlendMode.OVERLAY, OPS[nom], True)
            log('capa', nom, 'inserida, opacitat', OPS[nom])
            del lay
finalize_lr16(psd)
merged = u16(comp); np.save(os.path.join(HO, 'semifinal7_merged.npy'), merged); set_merged(psd, merged)
log('escrivint', OUT); psd.save(OUT); log('desat', os.path.getsize(OUT) / 1e9, 'GB')
