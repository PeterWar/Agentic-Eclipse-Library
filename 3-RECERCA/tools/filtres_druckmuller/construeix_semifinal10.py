"""FiltresSEMIFINAL10.psb a partir de FiltresSEMIFINAL9.psb: revisió de les MÀSCARES de les capes exteriors (la feina de
CapesInteriorsV4 aplicada al projecte de filtres). Mateixes capes, mateixos píxels (tret del CONTROL_NRGF, vegeu sota),
mateixes opacitats i visibilitats; el que canvia són les màscares:
  - DETALL EXTERIOR v9: la màscara de la v8 i la v9 era TOTA ZERO (error d'unitats a filtres_profunds_v8/v9.py: rR ja és en
    R☉ i s'hi restava 3,3·R_SOL en píxels) → la capa no feia res a la SF8 ni a la SF9. Ara porta la màscara prevista:
    entrada radial 3,3→4,3 R☉ × validesa erosionada, sense sortida.
  - Radials B (les dues): la màscara de Pere era una màscara de lluminositat amb un disc negre fet de cercles superposats
    amb vores dures (gradient màxim 0,44) i estructura de streamers (68 % de la variància no radial) → màscara NOMÉS
    radial: la mitjana per anell de la de Pere (0 fins a 1,1 R☉ → 0,36 a 1,8), amb el tall interior centrat a la Lluna
    (r_ll < 470 px) on la capa té la resposta de vora del disc.
  - corona_detall_v2_40: la màscara era una còpia desenfocada de la capa (R² 0,87: la capa s'autoemmascarava i els
    streamers brillants rebien més filtre que les valls) → mitjana per anell; 0 a la transició del disc lunar de la capa
    (r_ll < 466 px, on passava de 0,1 a 0,69 i feia una vora fosca al limbe).
  - CONTROL_NRGF_gris: la màscara era la capa mateixa (R² 0,99, 99,5 % no radial; sectors) → constant 0,5; i la capa es
    recentra per anell A TOT ARREU (la v8 només ho feia fora d'1,15 R☉ i deixava un +1 % d'1,0 a 1,4 R☉).
  - CEL blau-gris V1/V2: màscara de lluminositat (retallava els streamers de 3,6 a 5,5 R☉: taques fosques) → només radial.
  - GUARDA DE LA PROTUBERÀNCIA: dins d'una el·lipse suau al voltant de la protuberància (centre 3578, 2653; 90×110 px,
    rampa 50 px) les capes de Pere conserven màscara i contingut EXACTES de la SF9 (les protuberàncies són sagrades).
  - ANELL recalculat. FLAT, HALO, v9 RADIALS/MGN/NRGF: màscares ja radials, no es toquen.
Sortides: el PSB, TIF de les màscares noves i del CONTROL_NRGF recentrat a Capes_SEMIFINAL3_a_10, semifinal10_merged.npy.
"""
import os, sys, time, json, numpy as np, cv2, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, set_merged, finalize_lr16
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo')
NOVES = os.environ.get('SF10_NOVES', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ff8e9b6e-06c6-4064-b43d-763e81ba1468/scratchpad/sf10/noves')
OUTD = os.environ.get('SF10_OUT', os.path.dirname(NOVES))
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL9.psb')
OUT = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL10.psb')
TIFD = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10')
W, H = 7648, 5353; COMP = Compression.ZIP
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def overlay(b, s): return np.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))
def smootherstep(t):
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)
psd9 = PSDImage.open(SRC); icc = psd9.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd9)
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
    json.dump(dict(r_c=r_c.tolist(), rho=rhos), open(os.path.join(OUTD, 'anell_rho_psb10.json'), 'w'))
    return anell, comp
def escriu_tif(nom, arr, desc):
    kw = dict(photometric='rgb') if arr.ndim == 3 else dict(photometric='minisblack')
    tifffile.imwrite(os.path.join(TIFD, nom + '.tif'), arr, compression='zlib', metadata=None, resolution=(300, 300), description=desc,
                     extratags=[(34675, 7, len(icc), icc, False)] if arr.ndim == 3 else None, **kw)
# màscares noves (u16 del llenç)
MK = {k: np.load(os.path.join(NOVES, f)) for k, f in dict(detall='mask_detall_sf10.npy', radialsB='mask_radialsB_sf10.npy', coronadetall='mask_coronadetall_sf10.npy',
                                                           controlnrgf='mask_controlnrgf_sf10.npy', cel='mask_cel_sf10.npy').items()}
for k, m in MK.items():
    assert m.shape == (H, W) and m.dtype == np.uint16, k
    escriu_tif('MASCARA_' + k + '_SF10', m, f'Mascara radial SF10 ({k}). Nomes depen de la distancia al Sol (i del tall interior centrat a la Lluna). 2026-08-20')
NRGF10 = np.load(os.path.join(NOVES, 'CONTROL_NRGF_campnet_sf10.npy'))
escriu_tif('CONTROL_NRGF_campnet_SF10', NRGF10, 'CONTROL_NRGF_gris camp net, recentrat per anell a tot arreu (tambe dins d 1,15 R i dins la Lluna); fora d 1,4 R identic a la v8. 2026-08-20')
SUF = {
    'DETALL EXTERIOR v9': (' · MÀSCARA SF10 (la de la v9 era tota 0 per un error d\'unitats: la capa no feia res a la SF8/SF9; ara entrada radial 3,3→4,3 R☉ × validesa)', 'detall', None),
    'Radials B · original': (' · MÀSCARA RADIAL SF10 (mitjana per anell de la de Pere; 0 fins a 1,1 R☉; la de Pere tenia discos amb vores dures i estructura de streamers)', 'radialsB', None),
    'Radials B · camp net': (' · MÀSCARA RADIAL SF10 (mitjana per anell de la de Pere; 0 fins a 1,1 R☉)', 'radialsB', None),
    'corona_detall_v2_40': (' · MÀSCARA RADIAL SF10 (mitjana per anell de la de Pere, que era una còpia de la capa; 0 a la transició del disc)', 'coronadetall', None),
    'CONTROL_NRGF_gris': (' · SF10: recentrat per anell a TOT arreu + màscara constant 0,5 (la de Pere era la capa mateixa: sectors)', 'controlnrgf', NRGF10),
    'CEL blau-gris V1': (' · MÀSCARA RADIAL SF10 (abans per lluminositat: retallava els streamers de 3,6 a 5,5 R☉)', 'cel', None),
    'CEL blau-gris V2': (' · MÀSCARA RADIAL SF10 (abans per lluminositat: retallava els streamers de 3,6 a 5,5 R☉)', 'cel', None),
}
comp_ref = [None]; canvis = []
for i, l in enumerate(psd9):
    nom = l.name; c = chans(l); rec = l._record
    rgb = np.stack([c[0], c[1], c[2]], -1); mask = c.get('mask'); vis = l.visible; titol = nom
    if nom.startswith('ANELL'):
        anell, comp_ref[0] = anell_recalcula(comp_ref[0])
        lyr = add_pixel_layer(psd, anell, 'ANELL · compensa la mitjana radial dels filtres Overlay al camp exterior (Linear Light; radial i llisa; RECALCULAT per a la SEMIFINAL10; recalcular si canvies opacitats o màscares)',
                              blend=BlendMode.LINEAR_LIGHT, opacity=255, visible=True, compression=COMP)
        add_mask16(lyr, np.full((H, W), 65535, np.uint16), top=0, left=0)
        escriu_tif('ANELL_compensa_filtres_LinearLight_SF10', anell, 'ANELL recalculat per a la SEMIFINAL10. 2026-08-20')
        del anell; log('capa ANELL recalculada'); continue
    for pref, (suf, mk, px) in SUF.items():
        if nom.startswith(pref):
            base_t = nom.split(' (')[0] if len(nom) + len(suf) > 255 else nom
            titol = (base_t + suf)[:255]
            if px is not None:
                assert px.shape == rgb.shape, (px.shape, rgb.shape); rgb = px
            # la màscara nova cobreix tot el llenç
            mask = (MK[mk], 0, 0); canvis.append((i, nom[:40], mk, px is not None)); break
    assert len(titol) <= 255
    lyr = add_pixel_layer(psd, np.ascontiguousarray(rgb), titol, top=rec.top, left=rec.left, blend=l.blend_mode, opacity=l.opacity, visible=vis, compression=COMP)
    if mask is not None: add_mask16(lyr, mask[0], top=mask[1], left=mask[2])
    comp_ref[0] = blend_into(comp_ref[0], rgb, mask, rec.top, rec.left, l.blend_mode, l.opacity, vis)
    log(f'capa {i} {titol[:60]!r} vis={vis}' + (' · MÀSCARA NOVA' if any(cv[0] == i for cv in canvis) else ''))
finalize_lr16(psd)
merged = u16(comp_ref[0]); np.save(os.path.join(OUTD, 'semifinal10_merged.npy'), merged); set_merged(psd, merged)
json.dump(canvis, open(os.path.join(OUTD, 'canvis_sf10.json'), 'w'), ensure_ascii=False, indent=1)
log('escrivint', OUT); psd.save(OUT); log('desat', os.path.getsize(OUT) / 1e9, 'GB')
