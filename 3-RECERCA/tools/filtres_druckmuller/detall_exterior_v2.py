"""Capa de detall de la corona EXTERIOR (3–8 R☉) amb l'apilat Sony v2 (19-08-2026, tarda).

L'objectiu és trencar el «halo»: allà on la corona es veu com un resplendor llis, ensenyar l'estructura
real (raigs, vores de streamers) a les escales on els dos trens coincideixen (≥ 0,5° a 4 R☉, research/82).
Mètode (Druckmüller/Brno, com filtre_corona_externa.py però centrat al camp exterior):
  ln L_c − fons de Fourier (m ≤ 4) en log-polars → bandes DoG en graus → porta de Wiener amb soroll
  sintètic per banda (σ de L_c) → blanquejat per ANELL (FNRGF-like) → suma amb guanys → tanh.
Finestra radial: 2,8→3,6 R☉ d'entrada, 8→9,5 de sortida. Capa grisa 0,5 + 0,5·D/A (Linear Light) + màscara.
Sortides a FD3_OUT: DETALL_EXTERIOR_v2.tif, MASCARA_exterior_v2.tif; QA a FD3_SCR/halo/.
"""
import os, sys, json, math, time
import numpy as np, cv2, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import LogPolar, smooth01
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
LUM = os.environ.get('FD3_LUM2', os.path.join(SCR, '..', 'treball2', 'lum_llenc.npz'))
OUT = os.environ.get('FD3_OUT', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10'))
HO = os.path.join(SCR, 'halo')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
TAG = os.environ.get('DE_TAG', 'v2')
MODE = os.environ.get('DE_MODE', 'WHITE')   # WHITE (blanquejat per anell) o ADD (amplitud real, guany global)
BANDES_DEG = [float(x) for x in os.environ.get('DE_BANDES', '0.5,0.8,1.3,2.1,3.4,5.5,9.0,14.0').split(',')]
T_SIG = [float(x) for x in os.environ.get('DE_TSIG', '2.2,1.8,1.5,1.3,1.15,1.05,1.0').split(',')]
G_J = [float(x) for x in os.environ.get('DE_GJ', '1.0,1.2,1.3,1.2,1.0,0.6,0.4').split(',')]
F_SIST = [float(x) for x in os.environ.get('DE_FSIST', '3.0,2.5,2.0,1.8,1.6,1.5,1.5').split(',')]
R_IN = tuple(float(x) for x in os.environ.get('DE_RIN', '2.8,4.2').split(',')); R_OUT = tuple(float(x) for x in os.environ.get('DE_ROUT', '6.0,7.5').split(',')); A_T = float(os.environ.get('DE_A', 0.06)); K_WHITE = float(os.environ.get('DE_K', 0.22))
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def jpg(path, a01, q=88):
    a8 = np.clip(np.rint(np.asarray(a01) * 255), 0, 255).astype(np.uint8)
    if a8.ndim == 3: a8 = a8[..., ::-1]
    cv2.imwrite(path, a8, [cv2.IMWRITE_JPEG_QUALITY, q])

z = np.load(LUM); Lc = z['L_c']; sc = z['sig_c']; vc = z['valid_c']
Lv = z['L_v']; vv = z['valid_v']; Ls = z['L_s']; vs = z['valid_s']
k_ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))
vc = cv2.erode(vc.astype(np.uint8), k_, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
lp = LogPolar(H, W, SOL[0], SOL[1], NA=8192, NR=3072, r_min=400.0)
log('carregat')
R, okp, mp0, c_ple = lp.residu_polar(Lc, vc)
# residus per tren, per mesurar el soroll REAL (amb sistemàtics) per banda a la zona comuna: var(b_v − b_s)
kv = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
vv2 = cv2.erode(vv.astype(np.uint8), kv).astype(bool); vs2 = cv2.erode(vs.astype(np.uint8), kv, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
Rv, okv, _, _ = lp.residu_polar(np.where(vv2, Lv, 0), vv2)
Rs, oks, _, _ = lp.residu_polar(np.where(vs2, Ls, 0), vs2)
mpv = lp.cap_a_polar(vv2.astype(np.float32)) > 0.5; mps = lp.cap_a_polar(vs2.astype(np.float32)) > 0.5
both = mpv & mps
log('residus polars fets; c_ple', c_ple, 'fracció comuna', float(both.mean()))
# soroll sintètic en ln: n = N(0,1)·sig/L
rng = np.random.default_rng(7)
nimg = (rng.standard_normal((H, W)).astype(np.float32) * np.where(vc, sc / np.maximum(Lc, 1.0), 0.0)).astype(np.float32)
Np = lp.cap_a_polar(nimg) / np.maximum(lp.cap_a_polar(vc.astype(np.float32)), 1e-3)
del nimg
# radi per columna (px de la imatge) → per convertir graus a σ angular en files: px_deg = NA/360
r_col = lp.r_of
rR = r_col / R_SOL
D = np.zeros_like(R); nb = 0
qa = []
RNG_NUL = True if os.environ.get('DE_NUL', '1') == '1' else None
NUL = []
for j in range(len(BANDES_DEG) - 1):
    s0, s1 = BANDES_DEG[j] * lp.px_deg, BANDES_DEG[j + 1] * lp.px_deg
    b = lp.blur(R, s0) - lp.blur(R, s1)
    n = lp.blur(Np, s0) - lp.blur(Np, s1)
    # potència local (σ 2× la banda gran) de senyal i soroll
    v = lp.blur_n(b * b, okp, 2 * s1); vn = lp.blur_n(n * n, okp, 2 * s1)
    # terra empíric de la banda al camp llunyà (r > 8,5 R☉: cel sense corona): inclou sistemàtics (flat, costures),
    # que el soroll sintètic no veu; la porta usa el màxim dels dos
    # el soroll sintètic no veu els sistemàtics (reixa, flat, costures): factor F_SIST per banda (research/82: ×4,5 a la
    # banda fina al cel; aquí més suau perquè les bandes són més amples)
    # soroll real per banda i radi: var(b_v − b_s)/2 a la zona comuna (inclou sistemàtics de cada tren), mediana per
    # columna; on només hi ha Sony (columnes sense zona comuna) es manté l'últim valor; mínim: el sintètic ×F
    bv = lp.blur(Rv, s0) - lp.blur(Rv, s1); bs = lp.blur(Rs, s0) - lp.blur(Rs, s1)
    d2 = np.where(both, (bv - bs) ** 2, np.nan)
    nv_col = np.nanmedian(d2, axis=0) / 2.0
    okc = np.isfinite(nv_col) & (np.sum(both, axis=0) > 200)
    if okc.any():
        last = np.where(okc)[0].max()
        nv_col = np.interp(np.arange(len(nv_col)), np.where(okc)[0], nv_col[okc])
        nv_col[last + 1:] = nv_col[last]
        nv_col = cv2.GaussianBlur(nv_col.reshape(1, -1).astype(np.float32), (0, 0), 15.0, borderType=cv2.BORDER_REPLICATE).ravel()
    else:
        nv_col = np.zeros(R.shape[1], np.float32)
    vn = np.maximum(vn * (F_SIST[j] ** 2), nv_col[None, :])
    w = np.clip(1.0 - (T_SIG[j] ** 2) * vn / np.maximum(v, 1e-12), 0, 1)
    del d2
    # blanquejat per anell: rms per columna (robust) de la banda gated
    bg = b * w
    rms_col = np.sqrt(np.maximum(np.median((bg * bg)[:, :], axis=0), 1e-12)) * 1.2
    rms_col = cv2.GaussianBlur(rms_col.reshape(1, -1).astype(np.float32), (0, 0), 20.0, borderType=cv2.BORDER_REPLICATE).ravel()
    rms_col = np.maximum(rms_col, np.sqrt(np.maximum(np.median(vn, axis=0), 1e-12)) * 0.5)
    if MODE == 'COH':
        # coherència entre trens: correlació creuada normalitzada LOCAL (finestra 2·s1) entre la banda Vixen i la
        # banda Sony; pes = clip(c,0,1)^1.5 sobre la mitjana de les dues bandes (el soroll, c≈0, cau; l'estructura
        # comuna, c→1, queda); on només hi ha Sony, la banda Sony amb la porta de Wiener, atenuada
        bm = both.astype(np.float32)
        num = lp.blur_n(bv * bs * bm, bm, 2 * s1)
        den = np.sqrt(np.maximum(lp.blur_n(bv * bv * bm, bm, 2 * s1) * lp.blur_n(bs * bs * bm, bm, 2 * s1), 1e-20))
        cc_ = np.clip(num / den, 0.0, 1.0) ** 1.5
        coh = (cc_ * 0.5 * (bv + bs) * bm).astype(np.float32)
        if RNG_NUL is not None:
            # control nul: la mateixa coherència amb la Sony girada 180° en angle (desalineada) → ha de caure
            bs_n = np.roll(bs, int(R.shape[0] * float(os.environ.get('DE_NUL_DEG', '180')) / 360.0), axis=0)
            num_n = lp.blur_n(bv * bs_n * bm, bm, 2 * s1); den_n = np.sqrt(np.maximum(lp.blur_n(bv * bv * bm, bm, 2 * s1) * lp.blur_n(bs_n * bs_n * bm, bm, 2 * s1), 1e-20))
            cc_n = np.clip(num_n / den_n, 0.0, 1.0) ** 1.5
            coh_n = (cc_n * 0.5 * (bv + bs_n) * bm).astype(np.float32)
            z35 = (rR > 3.5) & (rR < 5.5)
            NUL.append((BANDES_DEG[j], float(np.std(coh[:, z35][bm[:, z35] > 0.5])), float(np.std(coh_n[:, z35][bm[:, z35] > 0.5])), float(np.mean(cc_[:, z35][bm[:, z35] > 0.5])), float(np.mean(cc_n[:, z35][bm[:, z35] > 0.5]))))
            del bs_n, num_n, den_n, cc_n, coh_n
        sony = bs * w * 0.5
        dist_in = lp.cap_a_polar(cv2.distanceTransform(vv2.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32))
        fb = smooth01(dist_in / 120.0)          # 1 ben dins de la caixa Vixen, 0 fora (transició 120 px)
        Dj = fb * coh + (1 - fb) * sony
    else:
        Dj = bg / rms_col[None, :] if MODE == 'WHITE' else bg
    D += G_J[j] * Dj; nb += G_J[j]
    del bv, bs
    frac = float((w[:, (rR > 3.5) & (rR < 8)] > 0.5).mean())
    qa.append(dict(banda=(BANDES_DEG[j], BANDES_DEG[j + 1]), frac_significatiu_3p5_8=round(frac, 3)))
    log(f'banda {BANDES_DEG[j]}–{BANDES_DEG[j+1]}°: fracció significativa a 3,5–8 R☉ {frac:.2f}')
D /= nb
D -= np.mean(D, axis=0, keepdims=True)                       # component d'anell zero: no canvia el perfil radial
if MODE == 'WHITE':
    D = np.tanh(D / 1.5)                                     # ±1, compressió suau
else:
    zona = (rR > 3.5) & (rR < 5.5)
    esc = float(np.percentile(np.abs(D[:, zona][okp[:, zona] > 0.5]), 99))
    D = np.tanh(D / (2.5 * esc))                             # règim quasi lineal: p99 de 3,5–5,5 R☉ → ±0,38; l'amplitud segueix el contrast real
    log(f'ADD/COH: escala p99 a 3,5–5,5 R☉ = {esc:.4f}')
    if NUL:
        for bd, sr, sn, cr, cn in NUL:
            log(f'   control nul banda {bd}°: σ coherent real {sr:.5f} vs desalineat {sn:.5f} (raó {sr/max(sn,1e-12):.1f}); ⟨c⟩ real {cr:.3f} vs nul {cn:.3f}')
Dimg = lp.cap_a_imatge(D.astype(np.float32))
win = (smooth01((rr - R_IN[0] * R_SOL) / ((R_IN[1] - R_IN[0]) * R_SOL)) * (1 - smooth01((rr - R_OUT[0] * R_SOL) / ((R_OUT[1] - R_OUT[0]) * R_SOL)))).astype(np.float32)
# la costura de la caixa Vixen (combinació Vixen/Sony) surt a L_c i no a cap tren sol: s'apaga ±COST px al voltant del rectangle
COST = 150.0
X1 = np.arange(W, dtype=np.float32)[None, :]; Y1 = np.arange(H, dtype=np.float32)[:, None]
dbox = np.minimum(np.minimum(np.abs(X1 - 600), np.abs(X1 - 7348)) * np.ones((H, 1), np.float32), np.minimum(np.abs(Y1 - 550), np.abs(Y1 - 5103)) * np.ones((1, W), np.float32))
win = win * smooth01((dbox - COST * 0.4) / COST)
Dimg = Dimg * win
capa = np.clip(0.5 + A_T * Dimg, 0, 1)                        # Linear Light: ±2·A_T de desplaçament a opacitat 100 %
rgb = np.repeat(u16(capa)[..., None], 3, axis=2)
tifffile.imwrite(os.path.join(OUT, f'DETALL_EXTERIOR_{MODE}_{TAG}.tif'), rgb, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                 description=f'Detall corona exterior {TAG} (apilat Sony v2 + Vixen): Linear Light 40-70 %. 2026-08-19', extratags=[(34675, 7, len(ICC), ICC, False)])
np.save(os.path.join(HO, f'detall_exterior_{MODE}_{TAG}.npy'), rgb)
mask = u16(win * (vc.astype(np.float32)))
mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 3).astype(np.uint16)
tifffile.imwrite(os.path.join(OUT, f'MASCARA_exterior_{TAG}.tif'), mask, photometric='minisblack', compression='zlib', metadata=None, resolution=(300, 300),
                 description='Mascara radial 2.8-3.6 -> 8-9.5 R', extratags=[(34675, 7, len(ICC), ICC, False)])
np.save(os.path.join(HO, f'mascara_exterior_{TAG}.npy'), mask)
log('capa escrita; D p1/p99 a 3.5–8 R:', np.percentile(Dimg[(rr > 3.5 * R_SOL) & (rr < 8 * R_SOL)], [1, 50, 99]).round(4).tolist())
jpg(os.path.join(HO, f'detall_exterior_{MODE}_{TAG}_x4.jpg'), cv2.resize(np.clip((capa - 0.5) * 8 + 0.5, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA))
json.dump(dict(mode=MODE, nul=NUL, bandes=BANDES_DEG, T_SIG=T_SIG, G_J=G_J, R_IN=R_IN, R_OUT=R_OUT, A_T=A_T, K_WHITE=K_WHITE, qa=qa), open(os.path.join(HO, f'detall_exterior_{MODE}_{TAG}.json'), 'w'), indent=1)
log('fi')
