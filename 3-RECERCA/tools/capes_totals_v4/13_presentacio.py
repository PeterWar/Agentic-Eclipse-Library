"""13 — Render de presentació de la V4 (DERIVAT; no toca la cadena ni el PSB).

Objectiu de to: `~/Downloads/Maqueta de resultat esperat.tif` (estirada a ull per Pere;
els seus artefactes de vora NO es repliquen). Mètode v2 — to i color separats, tot en lineal:

1. To: guany radial g_t(r) = lluminància_maqueta(r) / lluminància_V4(r) per anell solar
   (mediana, suavitzat, limitat). Reprodueix la caiguda de to de la maqueta directament.
2. Color: crominància per anell g_c(r) = (mq_c/mq_L)/(v4_c/v4_L), normalitzada (no toca el
   nivell), suavitzada, limitada — daurat K i cel blau sense destruir el color local real.
3. Cel: cap a 5–7 R☉ es barreja suaument al color de cel de la maqueta; els marges fora del
   frame s'hi omplen directament. Disc lunar: color de disc de la maqueta.
4. Detall suau: passa-alt en espai log (σ 6 px, k 0,5), fora del disc.
5. TIFF 16 bits Display P3 + PNG de revisió a QA/presentacio/.
"""
import os, sys, json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
import tifffile
from v4_lib import *

MAQUETA = Path.home() / 'Downloads/Maqueta de resultat esperat.tif'
OUT = V4W / 'QA/presentacio'
DETALL_K, DETALL_SIGMA = 0.5, 6.0

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def srgb_trc(lin):
    lin = np.clip(lin, 0, None)
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.power(lin, 1 / 2.4) - 0.055)

def registra_maqueta(mq_lum, comp_lum, SC=4):
    """Desplaçament (dx, dy) maqueta→llenç per correlació de fase sobre log-luminància
    reescalada 1/4. La geometria lunar del compost és coneguda al subpíxel; la del disc de
    la maqueta s'hi transfereix (mateixa escala: R mesurat 446 ≈ 452 del compost)."""
    a = comp_lum[::SC, ::SC]
    b = mq_lum[::SC, ::SC]
    H = min(a.shape[0], b.shape[0])
    W = min(a.shape[1], b.shape[1])
    a = np.log1p(np.clip(a[:H, :W], 0, None))
    b = np.log1p(np.clip(b[:H, :W], 0, None))
    a = (a - a.mean()) / a.std()
    b = (b - b.mean()) / b.std()
    corr = np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=(H, W))
    py, px = np.unravel_index(np.argmax(corr), corr.shape)
    dy = (py if py < H // 2 else py - H) * SC
    dx = (px if px < W // 2 else px - W) * SC
    return int(dx), int(dy), float(corr.max())

def anells(img_lin, rr, sel, bins):
    """Mediana per anell i canal. Retorna (nr, 3) float64."""
    out = np.full((len(bins) - 1, 3), np.nan)
    for k in range(len(bins) - 1):
        s = (rr >= bins[k]) & (rr < bins[k + 1]) & sel
        if s.sum() < 2000:
            continue
        for c in range(3):
            out[k, c] = np.median(img_lin[..., c][s])
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    from v4_tests import lunar_coords
    comp = np.asarray(np.load(V4W / 'states/S17.npy', mmap_mode='r'), np.float32) / 65535.0
    xx, yy = canvas_grid()
    rs = r_sun(xx, yy)
    sel = frame_sel(7)
    d7, _, R7 = lunar_coords(7)
    _e7 = ell_all()['7']
    ell7_cx, ell7_cy = _e7['cx'], _e7['cy']
    vlin = srgb_to_linear(np.clip(comp, 0, 1))              # compost V4 en lineal
    # ---- maqueta: registrada contra el compost (la geometria lunar del compost és coneguda)
    mq = tifffile.imread(str(MAQUETA)).astype(np.float32) / 65535.0
    mlin = srgb_to_linear(mq)
    mh, mw = mlin.shape[:2]
    dx, dy, pic = registra_maqueta(lum(mq), lum(np.clip(comp, 0, 1)))
    print(f'registre maqueta: dx={dx} dy={dy} (pic {pic:.1f})')
    # centre lunar de la maqueta = centre lunar del compost − desplaçament; R mateixa escala (~1:1)
    mcx, mcy, mR = (ell7_cx - dx), (ell7_cy - dy), R7
    myy, mxx = np.mgrid[0:mh, 0:mw].astype(np.float32)
    mrs = np.hypot(mxx - mcx, myy - mcy) / mR
    msel = mrs < 9.0
    bins = np.arange(1.02, 8.0, 0.06)
    A_m = anells(mlin, mrs, msel, bins)
    A_v = anells(vlin, rs, sel, bins)
    Lm = A_m @ np.array([1 / 3, 1 / 3, 1 / 3])
    Lv = A_v @ np.array([1 / 3, 1 / 3, 1 / 3])
    ok = np.isfinite(Lm) & np.isfinite(Lv) & (Lm > 0) & (Lv > 0)
    # to: guany radial de lluminància
    gt = np.ones(len(bins) - 1)
    gt[ok] = Lm[ok] / Lv[ok]
    gt = ndi.gaussian_filter1d(np.interp(np.arange(len(gt)), np.nonzero(ok)[0], gt[ok]), 4)
    gt = np.clip(gt, 0.25, 120.0)
    # color: crominància relativa (sense nivell)
    gc = np.ones((len(bins) - 1, 3))
    with np.errstate(invalid='ignore', divide='ignore'):
        gc[ok] = (A_m[ok] / Lm[ok, None]) / (A_v[ok] / Lv[ok, None])
    for c in range(3):
        gc[:, c] = ndi.gaussian_filter1d(np.interp(np.arange(len(gc)), np.nonzero(ok)[0], gc[ok, c]), 4)
    gc = np.clip(gc, 0.45, 2.4)
    # APLICACIÓ CONTÍNUA píxel a píxel (interpolada): mai per bins discrets — els esglaons
    # de la taula sortien com a cercles concèntrics (artefacte v1/v2)
    centres = 0.5 * (bins[:-1] + bins[1:])
    gt_img = np.interp(rs, centres, gt).astype(np.float32)
    gc_img = np.stack([np.interp(rs, centres, gc[:, c]) for c in range(3)], axis=-1).astype(np.float32)
    # la zona interna (<1,25 R☉) NO s'acobla a la maqueta: la mediana d'anell allà barreja
    # l'anell brillant amb els forats foscs i en rentava el contrast (v3). Guany 1 a 1,25 R☉,
    # fusió suaument cap a l'acoblament entre 1,25 i 1,9 R☉.
    w_inner = smootherstep((rs - 1.25) / 0.65).astype(np.float32)
    gt_img = 1.0 + (gt_img - 1.0) * w_inner
    gc_img = 1.0 + (gc_img - 1.0) * w_inner[..., None]
    graded = vlin * gt_img[..., None] * gc_img
    rows = [dict(r=round(float(bins[k] + 0.03), 2), Lm=round(float(Lm[k]), 6), Lv=round(float(Lv[k]), 6),
                 gt=round(float(gt[k]), 3), gc=[round(float(x), 3) for x in gc[k]]) for k in np.nonzero(ok)[0]]
    # ---- cel i marges
    corners = np.concatenate([mlin[:300, :300].reshape(-1, 3), mlin[:300, -300:].reshape(-1, 3),
                              mlin[-300:, :300].reshape(-1, 3), mlin[-300:, -300:].reshape(-1, 3)])
    sky_target = np.median(corners, axis=0)
    wsky = smootherstep((rs - 5.5) / 2.0)[..., None]
    graded = graded * (1 - wsky) + sky_target[None, None, :] * wsky
    graded[~sel] = sky_target[None, None, :]
    # ---- disc: color de disc de la maqueta
    disc_target = np.median(mlin[mrs < 0.97], axis=0)
    graded[d7 <= R7 + 1] = disc_target[None, None, :]
    # ---- color Hα als nuclis cremats (P3/P4): el clip és del revelat amplificat, no del sensor;
    # el color del fenomen sobreviu a la vora no cremada. S'hi injecta la croma veïna, conservant
    # la lluminància del píxel. Cosmètica de presentació declarada; la cadena no es toca.
    core34 = (np.asarray(np.load(V4W / 'masks/core3.npy')) | np.asarray(np.load(V4W / 'masks/core4.npy')))
    clip = core34 & (graded.min(axis=2) >= 0.95)   # blanc cremat (lineal)
    # vora no cremada del fenomen (dins la ploma de protecció, fora del nucli, no cremada)
    dist_c = ndi.distance_transform_edt(~core34)
    franja = (dist_c > 0) & (dist_c <= 8) & (graded.min(axis=2) < 0.90) & (lum(graded) > np.median(lum(graded)))
    if clip.any() and franja.any():
        vf = graded[franja]
        Lf = vf.sum(axis=1)
        hue = np.median(vf / Lf[:, None], axis=0)          # croma mediana de la vora (Hα)
        hue = hue / hue.max()
        Lc = graded[clip].sum(axis=1, keepdims=True)
        graded[clip] = (Lc * hue[None, :]).astype(np.float32)
        print(f'Hα injectat a {clip.sum()} px cremats; to de la vora R:G:B = {np.round(hue, 3)}', flush=True)
    # ---- detall suau en log (fora del disc)
    Lg = lum(graded)
    logL = np.log(np.maximum(Lg, 1e-6))
    detail = logL - ndi.gaussian_filter(logL, DETALL_SIGMA)
    boost = np.exp(DETALL_K * detail).astype(np.float32)
    boost[d7 <= R7 + 2] = 1.0
    boost[~sel] = 1.0
    graded = graded * boost[..., None]
    # ---- sortida
    final = np.clip(srgb_trc(graded), 0, 1)
    tifffile.imwrite(str(OUT / 'V4_presentacio_v4.tif'), (final * 65535).astype(np.uint16), photometric='rgb')
    Image.fromarray((np.clip(final[::2, ::2], 0, 1) * 255).astype(np.uint8)).save(OUT / 'V4_presentacio_v4_1de2.png')
    # retalls 1:1 de verificació: protuberància i perles
    for nom, (cx, cy) in {'protuberancia': (3578, 2653), 'perles': (3607, 2585)}.items():
        S = 500
        crop = final[cy - S:cy + S, cx - S:cx + S]
        Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).save(OUT / f'V4_presentacio_v4_1a1_{nom}.png')
    jdump(dict(maqueta=str(MAQUETA), centre_maqueta=[mcx, mcy], R_disc_maqueta_px=mR,
               cel_objectiu_lin=sky_target.tolist(), disc_objectiu_lin=disc_target.tolist(),
               detall=dict(k=DETALL_K, sigma=DETALL_SIGMA),
               zona_interna='guany ancorat a 1,0 fins 1,25 R☉, fusió fins 1,9 R☉',
               Hα='croma de la vora injectada als nuclis cremats de P3/P4 (lluminància conservada)',
               anells=rows), OUT / 'presentacio_v4.json')
    print('cel objectiu:', np.round(sky_target, 5), '| disc:', np.round(disc_target, 5))
    print('->', OUT / 'V4_presentacio_v4_1de2.png')

if __name__ == '__main__':
    main()
