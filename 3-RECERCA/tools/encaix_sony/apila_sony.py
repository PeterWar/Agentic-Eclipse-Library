"""Apilat lineal (ADU/s) dels 7 fotogrames Sony ≥ 1 s de dins la totalitat, registrats a les
estrelles amb els offsets i la similitud A→C de la cadena d'astrometria (research/tools/astrometria/sony),
en la reixa del fotograma de referència DSC06993 (5320×7968, raw_image_visible).

Per fotograma: raw − masterdark, saturació emmascarada (≥ 15600, dilatada 8 px), cada pla de Bayer
reconstruït a resolució plena per convolució normalitzada (σ 0,7 px el verd, 1,0 px R i B), /exposició,
desplaçament (−dy, −dx) i, al grup A (abans del salt), la similitud A→C (rotació 0,138°). Pes = exposició.
Sortida: sony_stack_ref_rgb.npy (ADU/s, float32), sony_stack_ref_wt.npy (pes acumulat per canal).
"""
import os, pickle, sys
import numpy as np
import rawpy
from scipy import ndimage as ndi

WORK = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/sony')
DADES = os.path.expanduser('~/Desktop/Eclipse 2026/300mm A7RIIIA')
OFF = pickle.load(open(os.path.join(WORK, 'offsets6.pkl'), 'rb'))['off']
M = np.load(os.path.join(WORK, 'warpM.npy')); Tt = np.load(os.path.join(WORK, 'warpT.npy')); Cc = np.load(os.path.join(WORK, 'warpC.npy'))
EXP = {'DSC06993': 8., 'DSC06984': 2., 'DSC06985': 1., 'DSC06987': 8., 'DSC06991': 1., 'DSC06996': 2., 'DSC06999': 2.}
SX_, SY_ = 3894.7, 2768.7
REF_LVL = None
GRUP = {'DSC06984': 'A', 'DSC06985': 'A', 'DSC06987': 'A', 'DSC06991': 'C', 'DSC06993': 'C', 'DSC06996': 'C', 'DSC06999': 'C'}
SAT = 15600
SIG = {0: 1.0, 1: 0.7, 2: 1.0}
Minv = np.linalg.inv(M)

def normconv(a, m, sig):
    num = ndi.gaussian_filter(a * m, sig, mode='constant')
    den = ndi.gaussian_filter(m, sig, mode='constant')
    return num, den

ACC = None
for n, e in EXP.items():
    with rawpy.imread(os.path.join(DADES, n + '.ARW')) as r:
        raw = r.raw_image_visible.astype(np.float32); col = r.raw_colors_visible.copy()
    md = np.load(os.path.join(WORK, f'masterdark_{int(e)}s.npy'))
    res = raw - md
    sat = ndi.binary_dilation(raw >= SAT, iterations=8)
    valid = ~sat
    valid[:40] = valid[-40:] = False; valid[:, :40] = valid[:, -40:] = False
    H, W = raw.shape
    # anivellament del cel per fotograma (el cel de la totalitat fa una V del ±20 %): nivell per canal a
    # l'anell 4,5–6 R☉ al voltant del Sol d'aquest fotograma (dins de tots els fotogrames), referència DSC06993
    dx0, dy0 = OFF[n]
    yy_, xx_ = np.mgrid[0:H, 0:W]
    rr_ = np.hypot(xx_ - (SX_ + dx0), yy_ - (SY_ + dy0)) / 295.8
    ring = (rr_ > 4.5) & (rr_ < 6.0) & valid
    lvl = {}
    for c, planes in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        pm = np.isin(col, planes) & ring
        lvl[c] = float(np.median(res[pm])) / e
    if n == 'DSC06993':
        REF_LVL = lvl
    if REF_LVL is None:
        raise SystemExit('DSC06993 ha de ser el primer per fixar la referència')
    print('   nivell 4,5–6 R☉ (ADU/s) R,G,B:', [round(lvl[c], 1) for c in range(3)], ' → desplaçament', [round(REF_LVL[c] - lvl[c], 1) for c in range(3)])
    del yy_, xx_, rr_, ring
    if ACC is None:
        ACC = np.zeros((H, W, 3), np.float32); WT = np.zeros((H, W, 3), np.float32)
        REF = [None, None, None]; REFW = [None, None, None]
        YY_, XX_ = np.mgrid[0:H, 0:W].astype(np.float32)
        RR_ = (np.hypot(XX_ - SX_, YY_ - SY_) / 295.8).astype(np.float32)
    dx, dy = OFF[n]
    # transformació sortida→entrada: x_in = U + (dx,dy), U = Minv (V − c − t) + c (grup A) o U = V (grup C)
    if GRUP[n] == 'A':
        A_xy = Minv; b_xy = -Minv @ (Cc + Tt) + Cc + np.array([dx, dy])
    else:
        A_xy = np.eye(2); b_xy = np.array([dx, dy])
    # a (fila, col): in_rc = P A P out_rc + P b, amb P = intercanvi d'eixos
    A_rc = np.array([[A_xy[1, 1], A_xy[1, 0]], [A_xy[0, 1], A_xy[0, 0]]]); b_rc = np.array([b_xy[1], b_xy[0]])
    for c, planes in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        pm = np.isin(col, planes)
        m = (valid & pm).astype(np.float32)
        num, den = normconv(np.where(m > 0, res, 0.0).astype(np.float32), m, SIG[c])
        I = np.where(den > 0.08, num / np.maximum(den, 1e-6), 0.0).astype(np.float32) / e
        Wc = (den > 0.08).astype(np.float32) * e
        Iw = ndi.affine_transform(I, A_rc, offset=b_rc, order=1, mode='constant', cval=0.0)
        Ww = ndi.affine_transform(Wc, A_rc, offset=b_rc, order=1, mode='constant', cval=0.0)
        Ww = np.where(Ww > 0.97 * e, e, 0.0).astype(np.float32)   # només píxels del tot dins del vàlid: la interpolació bilineal barreja zeros a les vores
        # anivellament contra la referència (DSC06993, ja alineada): Iw ≈ a·REF + b + cx·x + cy·y sobre la zona
        # comuna a r > 3,5 R☉ (extinció/exposició en a; el cel, que fa una V del ±20 % i té gradient, en el pla)
        if n == 'DSC06993':
            REF[c] = Iw.copy(); REFW[c] = Ww > 0
        else:
            m_ = (Ww > 0) & REFW[c] & (RR_ > 3.5)
            sub = m_[::6, ::6]
            yv = Iw[::6, ::6][sub].astype(np.float64); xr = REF[c][::6, ::6][sub].astype(np.float64)
            xs_ = XX_[::6, ::6][sub].astype(np.float64); ys_ = YY_[::6, ::6][sub].astype(np.float64)
            # el cel de cada fotograma és una superfície llisa diferent (l'ombra es mou: la V del ±20 % i el
            # gradient canvien): la diferència frame − ref es suavitza (σ 300 px, convolució normalitzada sobre
            # la zona comuna a r > 3,5 R☉) i es resta. Escales < ~700 px (la corona) no es toquen; a = 1.
            m_ = ((Ww > 0) & REFW[c] & (RR_ > 3.5)).astype(np.float32)
            dif = Iw - REF[c]
            # 1) pla robust de la diferència (treu el gradient perquè el suavitzat no es desviï a les vores)
            sub = (m_ > 0)[::6, ::6]
            dv = dif[::6, ::6][sub].astype(np.float64); xs_ = XX_[::6, ::6][sub].astype(np.float64); ys_ = YY_[::6, ::6][sub].astype(np.float64)
            A_ = np.c_[np.ones_like(dv), xs_ / 1000.0, ys_ / 1000.0]
            keep = np.ones(len(dv), bool)
            for it in range(3):
                p, *_ = np.linalg.lstsq(A_[keep], dv[keep], rcond=None)
                res_ = dv - A_ @ p; sd = 1.4826 * np.median(np.abs(res_[keep] - np.median(res_[keep])))
                keep = np.abs(res_) < 3 * sd
            pla = (p[0] + p[1] * XX_ / 1000.0 + p[2] * YY_ / 1000.0).astype(np.float32)
            # 2) residu suavitzat (σ 300 px, a 1/8 per blocs, convolució normalitzada) → superfície llisa
            BS = 8; Hb, Wb = (H // BS) * BS, (W // BS) * BS
            def blk(a): return a[:Hb, :Wb].reshape(Hb // BS, BS, Wb // BS, BS).mean(axis=(1, 3))
            dnum = ndi.gaussian_filter(blk((dif - pla) * m_), 300.0 / BS, mode='constant'); dden = ndi.gaussian_filter(blk(m_), 300.0 / BS, mode='constant')
            cs = np.where(dden > 0.02, dnum / np.maximum(dden, 1e-6), np.nan)
            idx_ = ndi.distance_transform_edt(np.isnan(cs), return_distances=False, return_indices=True)
            cs = cs[tuple(idx_)].astype(np.float32)
            corr_ = pla + ndi.zoom(cs, (H / cs.shape[0], W / cs.shape[1]), order=1)[:H, :W]
            Iw = np.where(Ww > 0, Iw - corr_, 0.0).astype(np.float32)
            if c == 1:
                cm = corr_[m_ > 0]
                print(f'   anivellament G contra 06993 (σ 300 px): correcció mediana {np.median(cm):+.1f} ADU/s, rang {cm.min():+.1f}…{cm.max():+.1f}')
        ACC[..., c] += Iw * Ww; WT[..., c] += Ww
    print(n, e, 's  grup', GRUP[n], ' offset', np.round(OFF[n], 2), ' saturat', round(float(sat.mean()), 4), flush=True)
    del raw, res, sat, valid, num, den, I, Wc, Iw, Ww

out = np.where(WT > 0, ACC / np.maximum(WT, 1e-9), np.nan).astype(np.float32)
np.save('sony_stack_ref_rgb.npy', out); np.save('sony_stack_ref_wt.npy', WT)
print('fet: forma', out.shape, ' pes màxim', WT.max(), ' fracció sense dada (verd)', np.isnan(out[..., 1]).mean())
