"""Apilat Sony v2 (19-08-2026, tarda): TOTS els fotogrames de dins la totalitat de més de 1/8 s inclòs
(1/8 ×3, 1/4 ×3, 1 s ×2, 2 s ×3, 8 s ×2 — 06988 i 06990 cauen pels salts de muntura), registrats a la reixa
de la DSC06993 i sumats en ADU/s amb pes = exposició. «Fins l'últim fotó» i sense el retall del 85 %:
la saturació es talla al nivell físic (SAT_V2, dilatada 3 px) en lloc de 15600/8 px.

Respecte d'apila_sony.py: (1) els fotogrames nous no tenen astrometria: es registren per correlació
creuada PLANA de la corona (banda 6–40 px del ln, anell 1,3–3,5 R☉, màscara suau) contra la 06993 ja
processada, després del warp A→C si són del grup A; (2) pes = exposició; (3) mateix anivellament del cel
(pla + σ 300 px) contra la 06993. Sortides a SONY2_OUT: sony_stack_v2_rgb.npy, sony_stack_v2_wt.npy,
registre_v2.json.
"""
import os, pickle, sys, json, time
import numpy as np, rawpy, cv2
from scipy import ndimage as ndi

WORK = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/sony')
DADES = os.path.expanduser('~/Desktop/Eclipse 2026/300mm A7RIIIA')
OUT = os.environ.get('SONY2_OUT', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sony2')
os.makedirs(OUT, exist_ok=True)
OFF = pickle.load(open(os.path.join(WORK, 'offsets6.pkl'), 'rb'))['off']
M = np.load(os.path.join(WORK, 'warpM.npy')); Tt = np.load(os.path.join(WORK, 'warpT.npy')); Cc = np.load(os.path.join(WORK, 'warpC.npy'))
Minv = np.linalg.inv(M)
SX_, SY_ = 3894.7, 2768.7; R_PX = 295.8
SAT_V2 = float(os.environ.get('SAT_V2', 16100)); DIL = 3
# (nom, exposició, grup) — l'ordre: la referència primer
FRAMES = [('DSC06993', 8., 'C'), ('DSC06991', 1., 'C'), ('DSC06996', 2., 'C'), ('DSC06999', 2., 'C'),
          ('DSC06992', 0.125, 'C'), ('DSC06994', 0.25, 'C'), ('DSC06997', 0.25, 'C'),
          ('DSC06984', 2., 'A'), ('DSC06985', 1., 'A'), ('DSC06987', 8., 'A'), ('DSC06982', 0.25, 'A'), ('DSC06986', 0.125, 'A'),
          ('DSC06989', 0.125, 'B')]
SIG = {0: 1.0, 1: 0.7, 2: 1.0}
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)

def masterdark(e):
    nom = {8.: '8', 2.: '2', 1.: '1', 0.25: '0.25', 0.125: '0.125'}[e]
    for d in (WORK, OUT):
        p = os.path.join(d, f'masterdark_{nom}s.npy')
        if os.path.exists(p): return np.load(p)
    raise SystemExit('falta masterdark ' + nom)

def normconv(a, m, sig):
    return ndi.gaussian_filter(a * m, sig, mode='constant'), ndi.gaussian_filter(m, sig, mode='constant')

def llegeix(n, e):
    with rawpy.imread(os.path.join(DADES, n + '.ARW')) as r:
        raw = r.raw_image_visible.astype(np.float32); col = r.raw_colors_visible.copy()
    res = raw - masterdark(e)
    sat = ndi.binary_dilation(raw >= SAT_V2, iterations=DIL)
    valid = ~sat
    valid[:40] = valid[-40:] = False; valid[:, :40] = valid[:, -40:] = False
    return res, col, valid, float(sat.mean())

def plans(res, col, valid, e):
    """tres plans (ADU/s) a resolució plena + pes, a la reixa nativa del fotograma."""
    I3 = []; W3 = []
    for c, pl in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        m = (valid & np.isin(col, pl)).astype(np.float32)
        num, den = normconv(np.where(m > 0, res, 0.0).astype(np.float32), m, SIG[c])
        I3.append((np.where(den > 0.08, num / np.maximum(den, 1e-6), 0.0) / e).astype(np.float32))
        W3.append((den > 0.08).astype(np.float32))
    return I3, W3

def transform(A_xy, b_xy, I, order=1):
    A_rc = np.array([[A_xy[1, 1], A_xy[1, 0]], [A_xy[0, 1], A_xy[0, 0]]]); b_rc = np.array([b_xy[1], b_xy[0]])
    return ndi.affine_transform(I, A_rc, offset=b_rc, order=order, mode='constant', cval=0.0)

def ab_for(grup, dx, dy):
    if grup == 'A':
        A_xy = Minv; b_xy = -Minv @ (Cc + Tt) + Cc + np.array([dx, dy])
    else:
        A_xy = np.eye(2); b_xy = np.array([dx, dy])
    return A_xy, b_xy

def bandpass_ln(I, ok, s0=6.0, s1=40.0):
    x = np.log(np.maximum(I, 1.0)) * ok; m = ok.astype(np.float32)
    def gn(a, s): return cv2.GaussianBlur(a, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-3)
    return ((gn(x, s0) - gn(x, s1)) * ok).astype(np.float32)

def xcorr_shift(a, b, mask, maxlag):
    a = a * mask; b = b * mask
    A = np.fft.rfft2(a); B = np.fft.rfft2(b)
    cc = np.fft.fftshift(np.fft.irfft2(A * np.conj(B), s=a.shape))
    cy, cx = np.array(cc.shape) // 2
    win = cc[cy - maxlag:cy + maxlag + 1, cx - maxlag:cx + maxlag + 1]
    iy, ix = np.unravel_index(np.argmax(win), win.shape)
    def par(f_1, f0, f1):
        d = f_1 - 2 * f0 + f1
        return 0.0 if d >= 0 else 0.5 * (f_1 - f1) / d
    dy = iy - maxlag + (par(win[iy - 1, ix], win[iy, ix], win[iy + 1, ix]) if 0 < iy < win.shape[0] - 1 else 0)
    dx = ix - maxlag + (par(win[iy, ix - 1], win[iy, ix], win[iy, ix + 1]) if 0 < ix < win.shape[1] - 1 else 0)
    pic = win[iy, ix] / np.sqrt((a * a).sum() * (b * b).sum() + 1e-12)
    return dy, dx, float(pic)

H = W = None; ACC = WT = None; REF = [None] * 3; REFW = [None] * 3
REFLUM = None; REFOK = None; XX_ = YY_ = RR_ = None
registre = {}
for n, e, g in FRAMES:
    res, col, valid, fsat = llegeix(n, e)
    if H is None:
        H, W = res.shape
        ACC = np.zeros((H, W, 3), np.float32); WT = np.zeros((H, W, 3), np.float32)
        YY_, XX_ = np.mgrid[0:H, 0:W].astype(np.float32)
        RR_ = (np.hypot(XX_ - SX_, YY_ - SY_) / R_PX).astype(np.float32)
    I3, W3 = plans(res, col, valid, e)
    del res
    # ---- offset: conegut (offsets6) o per correlació de la corona
    if n in OFF:
        dx, dy = OFF[n]; font = 'astrometria'
    else:
        # inicial: mitjana del grup (A o C); grup B: cerca gran a escala 1/8
        if g == 'A': dx, dy = np.mean([OFF[k] for k in ('DSC06984', 'DSC06985', 'DSC06987')], axis=0)
        elif g == 'C': dx, dy = np.mean([OFF[k] for k in ('DSC06991', 'DSC06993', 'DSC06996', 'DSC06999')], axis=0)
        else: dx, dy = OFF['DSC06988']   # grup B: 06988 hi era (−6, 693); afinarem amb cerca ampla
        lum = (0.5 * I3[1] + 0.25 * (I3[0] + I3[2])).astype(np.float32); okl = (W3[1] > 0.5)
        for passada, (f, lag) in enumerate(((8, 120), (1, 30))):
            A_xy, b_xy = ab_for(g, dx, dy)
            Lw = transform(A_xy, b_xy, lum); Ow = transform(A_xy, b_xy, okl.astype(np.float32)) > 0.97
            ok2 = Ow & REFOK & (RR_ > 1.25) & (RR_ < 3.6)
            if f > 1:
                def red(a): return cv2.resize(a, (W // f, H // f), interpolation=cv2.INTER_AREA)
                a_ = bandpass_ln(red(Lw), red(ok2.astype(np.float32)) > 0.99, 6.0 / f * 2, 40.0 / f * 2)
                b_ = bandpass_ln(red(REFLUM), red(ok2.astype(np.float32)) > 0.99, 6.0 / f * 2, 40.0 / f * 2)
                mk = cv2.GaussianBlur(red(ok2.astype(np.float32)), (0, 0), 4)
            else:
                a_ = bandpass_ln(Lw, ok2); b_ = bandpass_ln(REFLUM, ok2)
                mk = cv2.GaussianBlur(ok2.astype(np.float32), (0, 0), 25)
            ddy, ddx, pic = xcorr_shift(a_, b_, mk, lag)
            # b ≈ a desplaçada −l: la imatge Lw cal moure-la (−ddy,−ddx) → x_in = x_out + (dx − ddx)... signe: comprovat amb comu de prepara
            dx = dx + ddx * f; dy = dy + ddy * f
            log(f'   {n} registre passada {passada} (×{f}): corr pic {pic:.3f}, ajust ({ddx*f:+.2f}, {ddy*f:+.2f}) → offset ({dx:.2f}, {dy:.2f})')
        # comprovació per sectors (rotació?)
        A_xy, b_xy = ab_for(g, dx, dy)
        Lw = transform(A_xy, b_xy, lum); Ow = transform(A_xy, b_xy, okl.astype(np.float32)) > 0.97
        th_ = np.arctan2(YY_ - SY_, XX_ - SX_); secs = []
        for k in range(4):
            a0 = -np.pi + k * np.pi / 2
            ok2 = Ow & REFOK & (RR_ > 1.25) & (RR_ < 3.6) & (th_ >= a0) & (th_ < a0 + np.pi / 2)
            a_ = bandpass_ln(Lw, ok2); b_ = bandpass_ln(REFLUM, ok2); mk = cv2.GaussianBlur(ok2.astype(np.float32), (0, 0), 25)
            ddy, ddx, pic = xcorr_shift(a_, b_, mk, 20)
            secs.append((round(ddx, 2), round(ddy, 2), round(pic, 3)))
        log(f'   {n} per quadrants (dx, dy, pic): {secs}')
        font = 'corona'
        registre[n] = dict(dx=float(dx), dy=float(dy), grup=g, font=font, quadrants=secs)
        del lum, Lw, Ow
    A_xy, b_xy = ab_for(g, dx, dy)
    for c in range(3):
        Iw = transform(A_xy, b_xy, I3[c]); Ww = transform(A_xy, b_xy, W3[c])
        Ww = np.where(Ww > 0.97, 1.0, 0.0).astype(np.float32)
        if n == 'DSC06993':
            REF[c] = Iw.copy(); REFW[c] = Ww > 0
            if c == 1:
                REFLUM = None
        else:
            # anivellament del cel: pla robust + residu suavitzat σ 300 px sobre r > 3,5 R☉ (com apila_sony.py)
            m_ = ((Ww > 0) & REFW[c] & (RR_ > 3.5)).astype(np.float32)
            dif = Iw - REF[c]
            sub = (m_ > 0)[::6, ::6]
            dv = dif[::6, ::6][sub].astype(np.float64); xs_ = XX_[::6, ::6][sub].astype(np.float64); ys_ = YY_[::6, ::6][sub].astype(np.float64)
            A_ = np.c_[np.ones_like(dv), xs_ / 1000.0, ys_ / 1000.0]; keep = np.ones(len(dv), bool)
            for it in range(3):
                p, *_ = np.linalg.lstsq(A_[keep], dv[keep], rcond=None)
                res_ = dv - A_ @ p; sd = 1.4826 * np.median(np.abs(res_[keep] - np.median(res_[keep])))
                keep = np.abs(res_) < 3 * sd
            pla = (p[0] + p[1] * XX_ / 1000.0 + p[2] * YY_ / 1000.0).astype(np.float32)
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
                log(f'   {n} anivellament G: mediana {np.median(cm):+.1f} ADU/s, rang {cm.min():+.1f}…{cm.max():+.1f}')
        ACC[..., c] += Iw * Ww * e; WT[..., c] += Ww * e
    if n == 'DSC06993':
        REFLUM = (0.5 * REF[1] + 0.25 * (REF[0] + REF[2])).astype(np.float32); REFOK = REFW[1]
    log(f'{n} {e} s grup {g} offset ({dx:.2f}, {dy:.2f}) saturat {fsat:.4f}')
    del I3, W3

out = np.where(WT > 0, ACC / np.maximum(WT, 1e-9), np.nan).astype(np.float32)
np.save(os.path.join(OUT, 'sony_stack_v2_rgb.npy'), out); np.save(os.path.join(OUT, 'sony_stack_v2_wt.npy'), WT)
json.dump(dict(frames=[(n, e, g) for n, e, g in FRAMES], registre=registre, SAT_V2=SAT_V2, pes='exposicio'), open(os.path.join(OUT, 'registre_v2.json'), 'w'), indent=1)
log('fet: forma', out.shape, 'pes màxim (s)', float(WT.max()), 'fracció sense dada (verd)', float(np.isnan(out[..., 1]).mean()))
