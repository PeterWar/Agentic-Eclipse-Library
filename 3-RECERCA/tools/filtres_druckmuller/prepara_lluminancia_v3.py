"""Prepara, AL LLENÇ DE PERE (7648×5353), la luminància lineal dels dos trens i la combinada — VERSIÓ v3 (19/20-08-2026).

Respecte de prepara_lluminancia.py (que queda com a referència): (a) apilat Sony v3 (FD_SONY_DIR=sony3: tots els
> 1/8 s, meitats A/B a part); (b) CORRECCIÓ DE LA VORA DEL VIXEN: el VSD90SS + R6 III cau ~0,3–0,6 % als últims
~200 px del seu marc (vinyeta/cobertura del drizzle) i la costura σ 200 px no ho pot seguir (A3 de la SF8): es
mesura el perfil del residu (L_s − L_v − corr) contra la distància a cada vora del marc Vixen i s'afegeix a L_v;
(c) el pes del Vixen s'esvaeix en 300 px (no 150) cap a la vora de la seva caixa. FD_VIXEN_EDGE_FIX=0 ho desactiva.


Entrades:
  - Vixen: Corona_HDR_Vixen/hdr_vixen_countss.npy (+ _var, _cobertura), 68 fotogrames, ADU/s.
  - Sony: l'apilat ≥ 1 s (apila_sony.py → sony_stack_ref_rgb.npy, _wt.npy) i el flat del 300 mm.
Sortides (a $FD_SCR, float32, tot al llenç):
  - lum_llenc.npz: L_v, sig_v, valid_v (Vixen); L_s, sig_s, valid_s (Sony aparellada a ADU/s Vixen);
    L_c, sig_c, valid_c (combinada per inversa de la variància); i la geometria (JSON a part).
Què fa i per què:
  1. Vixen → llenç per translació subpíxel (bilineal); validesa = caixa RETALL & finit.
  2. Sony → llenç per similitud (escala astromètrica, gir 33,088°) amb la TRANSLACIÓ REFINADA per
     correlació de fase de la corona (banda 6–40 px, anell 3,4–5,0 R☉) contra la Vixen; comprovació
     per sectors del residu de gir/escala.
  3. Aparellament fotomètric L_v ≈ a·L_s + pla, robust, a l'anell 3,4–5,2 R☉ (les dues fonts són
     lineals i calibrades; a és la raó de guanys × òptica; el pla absorbeix la diferència de cel).
  4. Soroll: Vixen del mapa de variància (×κ calibrat al cel); Sony empíric per anells del passa-alt
     fi (transferència del filtre calibrada amb soroll sintètic passat pel mateix warp) i escalat
     amb el pes acumulat.
  5. Combinació: pesos 1/σ² on les dues són vàlides (r > ~3,3 R☉); Vixen sola a dins.
"""
import os, sys, json, math, time
import numpy as np
import cv2
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu as C

t0 = time.time()
SCR = C.SCR
os.makedirs(SCR, exist_ok=True)
SONY_DIR = os.environ.get('FD_SONY_DIR', os.path.join(os.path.dirname(SCR), 'sony'))
H, W = C.H_LLENC, C.W_LLENC
SX, SY = C.SOL_LLENC
R = C.R_SOL_PX
r_ll, th_ll = C.malla_llenc()


def log(*a):
    print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)


# ------------------------------------------------------------------ 1. Vixen al llenç
hdr = np.load(os.path.join(C.HDR_DIR, 'hdr_vixen_countss.npy'), mmap_mode='r')
var = np.load(os.path.join(C.HDR_DIR, 'hdr_vixen_var.npy'), mmap_mode='r')
Rv, Gv = np.asarray(hdr[..., 0]), np.asarray(hdr[..., 1])
vR, vG = np.asarray(var[..., 0]), np.asarray(var[..., 1])
k = C.K_VERMELL
Lv_h = 0.5 * (Gv + k * Rv)
varv_h = 0.25 * (vG + k * k * vR)
r0, r1, c0, c1 = C.HDR_RETALL
caixa = np.zeros(Lv_h.shape, bool); caixa[r0:r1 + 1, c0:c1 + 1] = True
valid_h = caixa & np.isfinite(Lv_h) & np.isfinite(varv_h) & (varv_h > 0)
Lv_h = np.where(valid_h, Lv_h, 0.0).astype(np.float32)
varv_h = np.where(valid_h, varv_h, 0.0).astype(np.float32)
del Rv, Gv, vR, vG, hdr, var
dx, dy = C.HDR_A_LLENC
M = np.array([[1, 0, dx], [0, 1, dy]], np.float64)


def cap_al_llenc(a, interp=cv2.INTER_LINEAR):
    return cv2.warpAffine(np.ascontiguousarray(a, np.float32), M, (W, H), flags=interp,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


mv = cap_al_llenc(valid_h.astype(np.float32))
L_v = cap_al_llenc(Lv_h) / np.maximum(mv, 1e-6)
var_v = cap_al_llenc(varv_h) / np.maximum(mv, 1e-6)
valid_v = mv > 0.999
L_v = np.where(valid_v, L_v, 0.0).astype(np.float32)
var_v = np.where(valid_v, var_v, 0.0).astype(np.float32)
del Lv_h, varv_h, valid_h, mv
log('Vixen al llenç: vàlids', valid_v.mean().round(4), 'L mediana a 4 R☉',
    float(np.median(L_v[valid_v & (r_ll > 3.9) & (r_ll < 4.1)])))

# κ del drizzle: dispersió observada al cel contra la del mapa (com fa hdr_corona_vixen.vis)
cel_z = valid_v & (r_ll > 3.6) & (r_ll < 4.6)
hp = L_v - cv2.GaussianBlur(L_v, (0, 0), 2.0)
obs = float(np.std(hp[cel_z]))
# transferència del passa-alt σ=2 sobre soroll amb la correlació del drizzle (caixa 2×2)
rng = np.random.default_rng(20260818)
z = rng.standard_normal((2048, 2048)).astype(np.float32)
z = cv2.blur(z, (2, 2)); z /= z.std()
kt = float(np.std((z - cv2.GaussianBlur(z, (0, 0), 2.0))[16:-16, 16:-16]))
esp = float(np.median(np.sqrt(var_v[cel_z]))) * kt
kappa = obs / esp
sig_v = (np.sqrt(var_v) * kappa).astype(np.float32)
log(f'soroll Vixen: observat/esperat al cel = {kappa:.3f} (transferència hp {kt:.3f})')
del hp, var_v

# ------------------------------------------------------------------ 2. Sony al llenç
sony = np.load(os.path.join(SONY_DIR, 'sony_stack_ref_rgb.npy'), mmap_mode='r')
wt = np.load(os.path.join(SONY_DIR, 'sony_stack_ref_wt.npy'), mmap_mode='r')
flat = np.load(os.path.join(SONY_DIR, 'flat_a7r3a_rgb.npy'), mmap_mode='r')
Rs = np.asarray(sony[..., 0]) / np.asarray(flat[..., 0])
Gs = np.asarray(sony[..., 1]) / np.asarray(flat[..., 1])
Ws = np.minimum(np.asarray(wt[..., 0]), np.asarray(wt[..., 1]))
oks = np.isfinite(Rs) & np.isfinite(Gs) & (Ws > 0)
oks = ndi.binary_erosion(oks, iterations=3, border_value=0)
# k Sony: G/R a l'anell 3,5–4,5 R☉ de la seva pròpia geometria (escala 3,2020″/px → R☉ = 299,5 px)
Rsol_s = 959.0 / 3.2020
yy, xx = np.mgrid[0:Rs.shape[0], 0:Rs.shape[1]].astype(np.float32)
rs = np.hypot(xx - C.SONY_SOL_PLACA[0], yy - C.SONY_SOL_PLACA[1]) / Rsol_s
an = oks & (rs > 3.5) & (rs < 4.5)
ks = float(np.median(Gs[an]) / np.median(Rs[an]))
Ls_g = np.where(oks, 0.5 * (Gs + ks * Rs), 0.0).astype(np.float32)
Ws_g = np.where(oks, Ws, 0.0).astype(np.float32)
del Rs, Gs, Ws, yy, xx, rs, an, sony, wt, flat
log(f'Sony a la seva reixa: k = {ks:.3f}, vàlids {oks.mean():.3f}')

S = C.SONY_ESCALA
th = math.radians(C.SONY_GIR_DEG)
c_, s_ = math.cos(th), math.sin(th)
SXs, SYs = C.SONY_SOL_PLACA


def warp_sony(img, CX, CY, order=1, ds=1, cval=0.0):
    yy, xx = np.mgrid[0:H:ds, 0:W:ds].astype(np.float64)
    ux = (xx - CX) / S; uy = (yy - CY) / S
    px = SXs + ux * c_ - uy * s_; py = SYs + ux * s_ + uy * c_
    return ndi.map_coordinates(img, [py, px], order=order, mode='constant', cval=cval).astype(np.float32)


CX, CY = C.SONY_SOL_LLENC_INICIAL
S_cur, th_cur = S, C.SONY_GIR_DEG


def warp_sony2(img, CX, CY, S_, thdeg, order=1, cval=0.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    c2, s2 = math.cos(math.radians(thdeg)), math.sin(math.radians(thdeg))
    ux = (xx - CX) / S_; uy = (yy - CY) / S_
    px = SXs + ux * c2 - uy * s2; py = SYs + ux * s2 + uy * c2
    return ndi.map_coordinates(img, [py, px], order=order, mode='constant', cval=cval).astype(np.float32)


def bandpass_ln(Limg, valid, s0=8.0, s1=50.0):
    x = np.log(np.maximum(Limg, 1.0)) * valid
    m = valid.astype(np.float32)

    def gn(a, s):
        return cv2.GaussianBlur(a, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-3)
    return (gn(x, s0) - gn(x, s1)) * valid


def xcorr_shift(a, b, mask, maxlag=40):
    """Correlació creuada PLANA (sense blanquejar) amb màscara suau: corr(l) = Σ a(x+l) b(x).
    Retorna l = (ly, lx): el contingut de b és el de a desplaçat en −l (b(x) ≈ a(x+l)), i el
    coeficient de correlació al pic. La correlació de fase no serveix aquí: la màscara compartida
    hi posa un pic fals a l'origen."""
    a = a * mask; b = b * mask
    A = np.fft.rfft2(a); B = np.fft.rfft2(b)
    cc = np.fft.fftshift(np.fft.irfft2(A * np.conj(B), s=a.shape))
    cy, cx = np.array(cc.shape) // 2
    win = cc[cy - maxlag:cy + maxlag + 1, cx - maxlag:cx + maxlag + 1]
    iy, ix = np.unravel_index(np.argmax(win), win.shape)

    def par(f_1, f0, f1):
        d = f_1 - 2 * f0 + f1
        return 0.0 if d == 0 else 0.5 * (f_1 - f1) / d
    dy = par(win[iy - 1, ix], win[iy, ix], win[iy + 1, ix]) if 0 < iy < win.shape[0] - 1 else 0.0
    dx = par(win[iy, ix - 1], win[iy, ix], win[iy, ix + 1]) if 0 < ix < win.shape[1] - 1 else 0.0
    return iy - maxlag + dy, ix - maxlag + dx, float(win.max() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-30))


# comprovació del signe amb un desplaçament sintètic conegut
_t = rng.standard_normal((512, 512)).astype(np.float32); _t = cv2.GaussianBlur(_t, (0, 0), 6) - cv2.GaussianBlur(_t, (0, 0), 20)
_tb = ndi.shift(_t, (3.0, -5.0), order=1)   # el contingut de b és el de a mogut (+3, −5)
_m = np.ones_like(_t); _m[:40] = _m[-40:] = _m[:, :40] = _m[:, -40:] = 0
_ly, _lx, _ = xcorr_shift(_t, _tb, _m)
log(f'comprovació xcorr: contingut mogut (+3,−5) → l = ({_ly:+.2f},{_lx:+.2f}) (esperat (−3,+5))')

bv = bandpass_ln(L_v, valid_v)
sect = []
# ⛔ Problema d'obertura: a 3,4–5,2 R☉ l'estructura són raigs RADIALS; la correlació creuada d'un
# sector només fixa la component TANGENCIAL del desplaçament (al llarg del raig no es veu res). Per
# això: (1) la translació global surt de la correlació de tot l'anell (totes les direccions hi
# són); (2) per sectors només es fa servir la component tangencial, que és la que un gir residual
# faria constant al voltant del Sol; (3) l'escala no és observable així i es pren de les 7
# estrelles (research/80 §7): 1,48860 i 33,088°.
S_cur, th_cur = 1.48860, 33.088
for it in range(3):
    L_s = warp_sony2(Ls_g, CX, CY, S_cur, th_cur)
    ws_l = warp_sony2(Ws_g, CX, CY, S_cur, th_cur)
    valid_s = ws_l > 0.5
    bs = bandpass_ln(L_s, valid_s)
    an_all = valid_v & valid_s & (r_ll > 3.4) & (r_ll < 5.2)
    yi, xi = np.where(an_all)
    y0, y1, x0, x1 = max(yi.min() - 60, 0), min(yi.max() + 61, H), max(xi.min() - 60, 0), min(xi.max() + 61, W)
    mk = cv2.GaussianBlur(an_all[y0:y1, x0:x1].astype(np.float32), (0, 0), 25)
    ly, lx, cc = xcorr_shift(bv[y0:y1, x0:x1], bs[y0:y1, x0:x1], mk)
    dxg, dyg = -lx, -ly       # on cau la Sony respecte de la Vixen
    log(f'iter {it}: global (anell 3,4–5,2, banda 8–50 px): la Sony és a (dx,dy) = ({dxg:+.2f},{dyg:+.2f}) px, corr {cc:.3f}')
    sect = []; T = []; Ang = []; Wt = []
    for j in range(12):
        a0 = -math.pi + j * math.pi / 6; a1 = a0 + math.pi / 6
        ms = an_all & (th_ll >= a0) & (th_ll < a1)
        if ms.sum() < 20000:
            continue
        yi, xi = np.where(ms)
        yy0, yy1, xx0, xx1 = max(yi.min() - 60, 0), min(yi.max() + 61, H), max(xi.min() - 60, 0), min(xi.max() + 61, W)
        mks = cv2.GaussianBlur(ms[yy0:yy1, xx0:xx1].astype(np.float32), (0, 0), 25)
        ly2, lx2, cc2 = xcorr_shift(bv[yy0:yy1, xx0:xx1], bs[yy0:yy1, xx0:xx1], mks)
        ang = (a0 + a1) / 2
        d = np.array([-lx2, -ly2])
        tang = float(d @ np.array([-math.sin(ang), math.cos(ang)]))    # component tangencial (sentit de θ creixent)
        radi = float(d @ np.array([math.cos(ang), math.sin(ang)]))
        sect.append((j, math.degrees(ang), ly2, lx2, cc2))
        T.append(tang); Ang.append(ang); Wt.append(max(cc2, 0.05))
        log(f'   sector {math.degrees(ang):+7.1f}°: Sony a (dx,dy) = ({-lx2:+.2f},{-ly2:+.2f}); tangencial {tang:+.2f}, radial {radi:+.2f} px, corr {cc2:.2f}')
    T = np.array(T); Ang = np.array(Ang); Wt = np.sqrt(np.array(Wt))
    # tang ≈ g·r_mig + tx·(−sin) + ty·(cos): el gir (g) i la translació (només la seva empremta tangencial)
    rmig = 4.3 * R
    A = np.c_[np.full(len(T), rmig), -np.sin(Ang), np.cos(Ang)]
    sol, *_ = np.linalg.lstsq(A * Wt[:, None], T * Wt, rcond=None)
    g, txt, tyt = sol
    res = A @ sol - T
    log(f'   ajust tangencial per sectors: gir residual {math.degrees(g):+.4f}° ({g*rmig:+.2f} px a 4,3 R☉), '
        f'translació tangencial ({txt:+.2f},{tyt:+.2f}); rms residus {np.sqrt(np.mean(res**2)):.2f} px')
    # correcció: translació global de la correlació de tot l'anell; gir només si és significatiu (> 0,03° i rms baix)
    CX -= dxg; CY -= dyg
    if abs(math.degrees(g)) > 0.03 and np.sqrt(np.mean(res**2)) < 2.0:
        th_cur -= math.degrees(g)
    log(f'   → similitud Sony: escala {S_cur:.5f}, gir {th_cur:.4f}°, Sol Sony al llenç ({CX:.2f}, {CY:.2f}) [Vixen ({SX:.2f}, {SY:.2f})]')
    if abs(dxg) < 0.2 and abs(dyg) < 0.2:
        break

L_s = warp_sony2(Ls_g, CX, CY, S_cur, th_cur)
ws_l = warp_sony2(Ws_g, CX, CY, S_cur, th_cur)
valid_s = ws_l > 0.5


def warp_sony(img, CX_, CY_, order=1, ds=1, cval=0.0):
    return warp_sony2(img, CX_, CY_, S_cur, th_cur, order=order, cval=cval)


# ------------------------------------------------------------------ 3. aparellament fotomètric
an = valid_v & valid_s & (r_ll > 3.4) & (r_ll < 5.2)
sub = np.zeros_like(an); sub[::4, ::4] = True
m = an & sub
xs = (np.arange(W)[None, :] - SX) / R; ys = (np.arange(H)[:, None] - SY) / R
XX = np.broadcast_to(xs, (H, W)); YY = np.broadcast_to(ys, (H, W))
A = np.c_[L_s[m], np.ones(m.sum()), XX[m], YY[m]].astype(np.float64)
y = L_v[m].astype(np.float64)
keep = np.ones(len(y), bool)
for it in range(4):
    p, *_ = np.linalg.lstsq(A[keep], y[keep], rcond=None)
    res = y - A @ p
    sd = 1.4826 * np.median(np.abs(res[keep] - np.median(res[keep])))
    keep = np.abs(res) < 3 * sd
a_s, b0, b1, b2 = p
log(f'aparellament: L_v ≈ {a_s:.4f}·L_s + {b0:.1f} + {b1:.1f}·x + {b2:.1f}·y  (rms {sd:.1f} ADU/s, {keep.mean():.3f} conservats)')
L_s = np.where(valid_s, a_s * L_s + (b0 + b1 * XX + b2 * YY), 0.0).astype(np.float32)
# comprovació per anells
for ra, rb in ((3.4, 3.8), (3.8, 4.2), (4.2, 4.6), (4.6, 5.0), (5.0, 5.4), (5.4, 6.0), (6.0, 7.0)):
    mm = valid_v & valid_s & (r_ll > ra) & (r_ll < rb)
    if mm.sum() > 1000:
        log(f'   {ra}–{rb} R☉: mediana L_v {np.median(L_v[mm]):7.1f}  L_s {np.median(L_s[mm]):7.1f}  '
            f'raó {np.median(L_v[mm])/np.median(L_s[mm]):.4f}')

# ------------------------------------------------------------------ 4. soroll Sony
# transferència del passa-alt fi (σ 1,5) sobre soroll blanc passat pel MATEIX warp (bilineal + escala 1,49)
zs = rng.standard_normal(Ls_g.shape[:2] if Ls_g.ndim == 2 else Ls_g.shape).astype(np.float32)
zw = warp_sony(zs, CX, CY, ds=1)
hz = zw - cv2.GaussianBlur(zw, (0, 0), 1.5)
zone = valid_s & (r_ll > 4.5) & (r_ll < 7.5)
kt_s = float(np.std(hz[zone]))
del zs, zw, hz
hs = L_s - cv2.GaussianBlur(L_s, (0, 0), 1.5)
# rms per anell, robust (MAD), amb pes normalitzat a 24 s
wn = np.clip(ws_l / 24.0, 0.05, 1.0)
rb = np.arange(3.3, 9.6, 0.2)
sig_r = []
for ra, rb_ in zip(rb[:-1], rb[1:]):
    mm = valid_s & (r_ll > ra) & (r_ll < rb_) & (wn > 0.95)
    if mm.sum() < 5000:
        sig_r.append(np.nan); continue
    v = hs[mm]
    sig_r.append(1.4826 * float(np.median(np.abs(v - np.median(v)))) / kt_s)
sig_r = np.array(sig_r); rc = 0.5 * (rb[:-1] + rb[1:])
ok = np.isfinite(sig_r)
# model σ² = α + β·L (fotons + lectura), sobre la mediana de L per anell
Lr = np.array([np.median(L_s[valid_s & (r_ll > ra) & (r_ll < rb_)]) if np.isfinite(s) else np.nan
               for ra, rb_, s in zip(rb[:-1], rb[1:], sig_r)])
Aa = np.c_[np.ones(ok.sum()), Lr[ok]]
(alpha, beta), *_ = np.linalg.lstsq(Aa, sig_r[ok] ** 2, rcond=None)
alpha = max(alpha, 0.0); beta = max(beta, 0.0)
log(f'soroll Sony (per píxel, unitats Vixen, pes 24 s): σ² = {alpha:.1f} + {beta:.4f}·L ; ' +
    ' '.join(f'{rc_:.1f}:{s:.1f}' for rc_, s in zip(rc[ok][::3], sig_r[ok][::3])))
sig_s = np.where(valid_s, S_cur * np.sqrt((alpha + beta * np.maximum(L_s, 0)) / wn), 0.0).astype(np.float32)   # ×escala: σ per píxel Sony → per píxel del llenç (mateixa potència de soroll per àrea)
del hs
# la Vixen, mateixa mesura per comparar (r > 3,3)
hv = L_v - cv2.GaussianBlur(L_v, (0, 0), 1.5)
zv = rng.standard_normal((2048, 2048)).astype(np.float32); zv = cv2.blur(zv, (2, 2)); zv /= zv.std()
kt_v = float(np.std((zv - cv2.GaussianBlur(zv, (0, 0), 1.5))[16:-16, 16:-16]))
for ra, rb_ in ((3.4, 3.8), (4.2, 4.6), (5.0, 5.4), (6.0, 6.5)):
    mm = valid_v & valid_s & (r_ll > ra) & (r_ll < rb_)
    v = hv[mm]
    log(f'   σ per píxel a {ra}–{rb_} R☉: Vixen empíric {1.4826*np.median(np.abs(v-np.median(v)))/kt_v:.1f} '
        f'(mapa {np.median(sig_v[mm]):.1f})  Sony {np.median(sig_s[mm]):.1f}')
del hv, zv

# ------------------------------------------------------------------ 4 ter + 4 bis (v3): costura SENSE biaix de vora i vora del marc Vixen
# A3 (SF8): la diferència Sony−Vixen a baixa freqüència és un camp suau NO radial (poly4 R² 0,94); la convolució
# normalitzada σ 200 té biaix a la vora de la caixa (no segueix cap gradient als últims ~200 px) i deixava un sot
# de −0,1…−0,2 % a L_d a ~100 px dins de la caixa. Ara: corr = poly4 ajustat al nucli (dV > 200) + residu σ 200
# (calculat sense la franja dV < 150), i l'excés que queda a la vora (la caiguda del Vixen als últims ~200 px del
# seu marc: vinyeta/cobertura) es mesura per vora i s'afegeix a L_v.
EDGE_FIX = os.environ.get('FD_VIXEN_EDGE_FIX', '1') == '1'
edge_prof = {}
zona = valid_v & valid_s & (r_ll > 3.4)
ys_v, xs_v = np.where(valid_v); x0v, x1v, y0v, y1v = xs_v.min(), xs_v.max(), ys_v.min(), ys_v.max(); del ys_v, xs_v
Xg = np.arange(W, dtype=np.float32)[None, :] * np.ones((H, 1), np.float32); Yg = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
dists = np.stack([Xg - x0v, x1v - Xg, Yg - y0v, y1v - Yg], 0)      # esq, dreta, dalt, baix
quina = np.argmin(dists, axis=0); dV = np.min(dists, axis=0)
del dists
BS = 8; Hb, Wb = (H // BS) * BS, (W // BS) * BS
def blk(a): return a[:Hb, :Wb].reshape(Hb // BS, BS, Wb // BS, BS).mean(axis=(1, 3))
def lf_normalitzada(dif_, m_, sig=200.0):
    num = cv2.GaussianBlur(blk(dif_ * m_), (0, 0), sig / BS); den = cv2.GaussianBlur(blk(m_), (0, 0), sig / BS)
    cs = np.where(den > 0.03, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    idx_ = ndi.distance_transform_edt(np.isnan(cs), return_distances=False, return_indices=True)
    cs = cs[tuple(idx_)]
    return cv2.resize(cs, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
def poly4_fit(dif_, m_):
    sub = np.zeros_like(m_); sub[::6, ::6] = True
    sel = m_ & sub
    xn = (Xg[sel] - W / 2) / (W / 2); yn = (Yg[sel] - H / 2) / (H / 2); v = dif_[sel].astype(np.float64)
    cols = []
    for i in range(5):
        for j in range(5 - i):
            cols.append((xn ** i) * (yn ** j))
    A_ = np.stack(cols, 1).astype(np.float64)
    keep = np.ones(len(v), bool)
    for it in range(3):
        c_, *_ = np.linalg.lstsq(A_[keep], v[keep], rcond=None)
        r_ = v - A_ @ c_; sd_ = 1.4826 * np.median(np.abs(r_[keep] - np.median(r_[keep]))); keep = np.abs(r_) < 3 * sd_
    XN = (Xg - W / 2) / (W / 2); YN = (Yg - H / 2) / (H / 2)
    out = np.zeros((H, W), np.float32); k = 0
    for i in range(5):
        for j in range(5 - i):
            out += (c_[k] * (XN ** i) * (YN ** j)).astype(np.float32); k += 1
    return out, float(sd_)
dif = np.where(zona, L_s - L_v, 0.0).astype(np.float32)
P4, sd4 = poly4_fit(dif, zona & (dV > 200))
res = np.where(zona, dif - P4, 0.0).astype(np.float32)
corr_res = lf_normalitzada(res, (zona & (dV >= 150)).astype(np.float32))
corr_lf = (P4 + corr_res).astype(np.float32)
log(f'costura v3: poly4 rms residu {sd4:.2f} ADU/s; corr = poly4 + residu σ200 (sense la franja dV<150): mediana {np.median(corr_lf[zona]):+.2f}, rang {np.percentile(corr_lf[zona],1):+.1f}…{np.percentile(corr_lf[zona],99):+.1f}')
if EDGE_FIX:
    rho = np.where(zona, dif - corr_lf, 0.0).astype(np.float32)
    P = np.zeros((H, W), np.float32)
    DMAX = 500; bins = np.arange(0, DMAX + 5, 5)
    for e, nom_e in enumerate(('esq', 'dreta', 'dalt', 'baix')):
        sel = zona & (quina == e) & (dV < DMAX) & (r_ll > 3.6)
        if sel.sum() < 5000:
            continue
        d_ = dV[sel]; v_ = rho[sel]
        idx = np.minimum((d_ / 5).astype(np.int32), len(bins) - 2)
        prof = np.full(len(bins) - 1, np.nan, np.float32)
        for k in range(len(bins) - 1):
            mk = idx == k
            if mk.sum() >= 200: prof[k] = np.median(v_[mk])
        okp_ = np.isfinite(prof)
        if okp_.sum() < 10: continue
        prof = np.interp(np.arange(len(prof)), np.where(okp_)[0], prof[okp_]).astype(np.float32)
        prof = cv2.GaussianBlur(prof.reshape(1, -1), (0, 0), 3.0, borderType=cv2.BORDER_REPLICATE).ravel()
        dd = bins[:-1].astype(np.float64); sel_l = dd >= 300
        pl = np.polyfit(dd[sel_l], prof[sel_l].astype(np.float64), 1)
        prof = (prof - np.polyval(pl, dd)).astype(np.float32)
        ramp = np.clip((DMAX - 150 - bins[:-1]) / 200.0, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
        prof = prof * ramp
        edge_prof[nom_e] = dict(d=bins[:-1].tolist(), p=prof.tolist())
        zone_e = (quina == e) & (dV < DMAX) & valid_v
        P[zone_e] = np.interp(dV[zone_e], bins[:-1] + 2.5, prof)
        log(f'   vora Vixen {nom_e}: excés Sony−Vixen a 0–50 px {np.mean(prof[:10]):+.2f} ADU/s, a 100–150 {np.mean(prof[20:30]):+.2f}, a 200–250 {np.mean(prof[40:50]):+.2f} (→ s afegeix a L_v)')
    P = cv2.GaussianBlur(P, (0, 0), 12.0)
    L_v = np.where(valid_v, L_v + P, 0.0).astype(np.float32)
    # segona passada: el que quedi (la primera l'ha vist contra una corr ja sense biaix) i comprovació
    rho1 = np.where(zona, L_s - L_v - corr_lf, 0.0)
    for e, nom_e in enumerate(('esq', 'dreta', 'dalt', 'baix')):
        sel0 = zona & (quina == e) & (dV < 100) & (r_ll > 3.6); sel1 = zona & (quina == e) & (dV > 150) & (dV < 300) & (r_ll > 3.6)
        if sel0.any() and sel1.any():
            log(f'   vora {nom_e}: residu (Ls−Lv−corr) mediana abans {np.median(rho[sel0]):+.2f} → després {np.median(rho1[sel0]):+.2f} ADU/s (0–100 px); a 150–300 px {np.median(rho1[sel1]):+.2f}')
    del rho, rho1, P
# la Sony es porta a la baixa freqüència del Vixen (ara amb el Vixen corregit a la vora, i sense biaix de vora)
L_s = np.where(valid_s, L_s - corr_lf, 0.0).astype(np.float32)
log(f'costura: correcció de baixa freqüència de la Sony: mediana {np.median(corr_lf[zona]):+.2f}, rang {np.percentile(corr_lf[zona], 1):+.1f}…{np.percentile(corr_lf[zona], 99):+.1f} ADU/s')
for ra, rb_ in ((3.4, 3.8), (4.2, 4.6), (5.0, 5.4), (6.0, 7.0)):
    mm = valid_v & valid_s & (r_ll > ra) & (r_ll < rb_)
    log(f'   {ra}–{rb_} R☉ després: raó medianes L_v/L_s {np.median(L_v[mm])/np.median(L_s[mm]):.4f}; '
        f'sd (L_s−L_v) suavitzat 30 px: {float(np.std(cv2.GaussianBlur(np.where(mm, L_s-L_v, 0), (0,0), 30)[mm])):.2f} ADU/s')
del Xg, Yg, quina, dif, res, P4, corr_res

# ------------------------------------------------------------------ 5. combinació
wv = np.where(valid_v, 1.0 / np.maximum(sig_v, 1e-3) ** 2, 0.0)
ws = np.where(valid_s, 1.0 / np.maximum(sig_s, 1e-3) ** 2, 0.0)
# la Sony només compta on no està cremada: r > 3,3 R☉ amb rampa fins a 3,6 (research/80: cremada fins a 3,25 en R)
ramp = np.clip((r_ll - 3.3) / 0.3, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
ws = ws * ramp
# la Vixen s'esvaeix cap a la vora de la seva caixa (150 px) on hi ha Sony: la combinada canvia de
# caràcter (soroll, resolució) gradualment i no en un graó
dv = cv2.distanceTransform(valid_v.astype(np.uint8), cv2.DIST_L2, 5)
FV_PX = float(os.environ.get('FD_FV_PX', 400.0))
fv = np.clip(dv / FV_PX, 0, 1); fv = fv * fv * (3 - 2 * fv)
wv = np.where(valid_s & (ramp > 0.999), wv * fv, wv)
wt_ = wv + ws
valid_c = wt_ > 0
L_c = np.where(valid_c, (wv * L_v + ws * L_s) / np.maximum(wt_, 1e-12), 0.0).astype(np.float32)
sig_c = np.where(valid_c, 1.0 / np.sqrt(np.maximum(wt_, 1e-12)), 0.0).astype(np.float32)
frac_s = np.where(valid_c, ws / np.maximum(wt_, 1e-12), 0.0).astype(np.float32)
for ra, rb_ in ((3.4, 3.8), (4.2, 4.6), (5.0, 5.4), (6.0, 6.5), (7.0, 8.0)):
    mm = valid_c & (r_ll > ra) & (r_ll < rb_)
    log(f'   pes de la Sony a {ra}–{rb_} R☉: {np.median(frac_s[mm]):.2f}   σ_c/σ_v {np.median(sig_c[mm]/np.maximum(sig_v[mm],1e-3)):.2f}')

np.savez(os.path.join(SCR, 'lum_llenc.npz'), L_v=L_v, sig_v=sig_v, valid_v=valid_v,
         L_s=L_s, sig_s=sig_s, valid_s=valid_s, L_c=L_c, sig_c=sig_c, valid_c=valid_c, frac_s=frac_s, corr_lf=corr_lf)
json.dump(dict(sol_llenc=[SX, SY], sony_sol_llenc=[CX, CY], sony_escala=S_cur, sony_gir_deg=th_cur, sony_escala_astrometria=S,
               k_vermell_vixen=k, k_vermell_sony=ks, aparellament=dict(a=a_s, b0=b0, b1=b1, b2=b2, rms=sd),
               kappa_vixen=kappa, soroll_sony=dict(alpha=alpha, beta=beta), vixen_edge_fix=edge_prof, fv_px=FV_PX,
               sectors=[(int(j), float(ang), float(ly), float(lx), float(cc)) for j, ang, ly, lx, cc in sect]),
          open(os.path.join(SCR, 'lum_llenc_geometria.json'), 'w'), indent=1)
log('desat lum_llenc.npz')

# vista ràpida
def vista(nom, a, val):
    x = np.log10(np.maximum(a, 1.0)); x = np.where(val, x, np.nan)
    lo, hi = np.nanpercentile(x, [0.5, 99.8])
    v = np.clip((x - lo) / (hi - lo), 0, 1); v = np.nan_to_num(v)
    v = cv2.resize(v, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(SCR, f'vista_{nom}.jpg'), (v * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 85])
vista('L_v', L_v, valid_v); vista('L_s', L_s, valid_s); vista('L_c', L_c, valid_c)
log('fet')
