"""Filtres «profunds» v8 per a FiltresSEMIFINAL8.psb (19/20-08-2026).

Pere, després de la SEMIFINAL7: CONTROL_NRGF, corona_detall_v2_40, NRGF/MGN profunds «plens d'artefactes a les
cantonades del camp», i el RADIALS profund amb una banda horitzontal a la vora superior de la caixa Vixen. Demana:
(1) reconstruir la corona amb TOTES les llargues (Sony > 1/8 s menys la 8 s moguda; Vixen llargues), (2) flat
perquè cap filtre no porti artefactes al límit del camp conjunt Canon+Sony, (3) reconstruir TOTS els filtres.

Què canvia respecte de filtres_profunds_v7.py:
  - Referència: lum_llenc v3 (apilat Sony v3 = tots els > 1/8 s, meitats A/B) + corr_lf (flat del 300 mm tornat
    a posar: L_d = L_c + corr_lf) [+ si FD_LONG ho diu, la Vixen «només llargues»].
  - SOROLL REAL I LOCAL a tot arreu: per banda, n²_s = var(b_A − b_B)·wA·wB/(wA+wB)² (meitats independents de la
    Sony, inclou els seus sistemàtics, val també fora de la caixa Vixen), n²_v sintètic del mapa de variància
    del Vixen × F_SIST, combinats amb els pesos reals f = frac_s; dins de la zona comuna, pis per columna
    var(b_v − b_s)/2. Cap extrapolació «last value».
  - CAP pes en forma de caixa ni taper a la costura (la continuïtat de baixa freqüència la dona corr_lf; es
    mesura i es registra el graó residual a cada vora de la caixa). Només taper de 150 px a les vores de dades
    (marc Sony, triangles, disc) i l'esvaïment radial per banda de la v7.
  - Les capes valen EXACTAMENT 0,5 fora de la validesa i als cantons: mitjana zero per anell dins del taper.
  - Es reconstrueixen TOTS els filtres: RADIALS, MGN, NRGF (v8), DETALL EXTERIOR (coherència, v8), i les dues capes
    «Radials B» de Pere amb el camp llunyà neutre (camp net v8). corona_detall_v2_40 i CONTROL_NRGF queden
    substituïts per MGN v8 i NRGF v8 (la part «imatge log» del v2_40 és una corba de to, no un filtre).
Sortides: FD3_SCR/v8/*.npy + TIF a FD3_OUT + QA.
"""
import os, sys, json, math, time
import numpy as np, cv2, tifffile
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import LogPolar, smooth01

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
ROOT = os.path.dirname(SCR)
TREB = os.environ.get('FD3_TREB', os.path.join(ROOT, 'treball3'))
LUM = os.path.join(TREB, 'lum_llenc.npz'); GEO = os.path.join(TREB, 'lum_llenc_geometria.json')
SONY3 = os.environ.get('FD3_SONY3', os.path.join(ROOT, 'sony3'))
FLAT = os.path.join(ROOT, 'sony', 'flat_a7r3a_rgb.npy')
OUT = os.environ.get('FD3_OUT', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10'))
V8 = os.path.join(SCR, 'v8'); os.makedirs(V8, exist_ok=True)
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
LLUNA = (4034.7, 2736.7)
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
A_RAD = float(os.environ.get('V8_A_RAD', 0.125)); A_MGN = float(os.environ.get('V8_A_MGN', 0.125)); A_NRGF = float(os.environ.get('V8_A_NRGF', 0.20)); A_DET = float(os.environ.get('V8_A_DET', 0.06))
R_MASK = (2.6, 3.6); R_MASK_FULL = (1.15, 1.35)
TAPER_PX = float(os.environ.get('V8_TAPER', 200.0))
ERODE_PX = int(os.environ.get('V8_ERODE', 70))     # A3: la dada Sony és fiable des de ~60 px del seu marc
SEAM_TAPER_PX = float(os.environ.get('V8_SEAM_TAPER', 0.0))      # 0 = cap taper a la costura de la caixa (decisió v8)
RAD_BANDES = [0.4, 2.0, 6.0, 18.0]; RAD_W = [1.0, 0.6, 0.25]; RAD_TSIG = [1.8, 1.3, 1.1]; RAD_FSIST = [3.0, 2.0, 1.6]; RAD_FSONY = [1.6, 1.25, 1.1]
MGN_BANDES = [0.5, 0.8, 1.3, 2.1, 3.4, 5.5, 9.0]; MGN_G = [1.0, 1.2, 1.3, 1.2, 0.6, 0.3]; MGN_TSIG = [2.2, 1.8, 1.5, 1.3, 1.15, 1.05]; MGN_FSIST = [3.0, 2.5, 2.0, 1.8, 1.6, 1.5]; MGN_FSONY = [1.6, 1.4, 1.3, 1.2, 1.1, 1.0]
DET_BANDES = [0.8, 1.3, 2.1, 3.4, 5.5, 9.0]; DET_TSIG = [1.5, 1.3, 1.15, 1.05, 1.0]; DET_G = [1.3, 1.2, 1.0, 0.6, 0.4]; DET_FSIST = [2.0, 1.8, 1.6, 1.5, 1.5]; DET_FSONY = [1.4, 1.3, 1.2, 1.1, 1.0]
DET_RIN = (2.8, 4.2); DET_ROUT = (6.0, 7.5)
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.1f} s]', *a, flush=True)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
def jpg(path, a01, q=88):
    a8 = np.clip(np.rint(np.asarray(a01) * 255), 0, 255).astype(np.uint8)
    if a8.ndim == 3: a8 = a8[..., ::-1]
    cv2.imwrite(path, a8, [cv2.IMWRITE_JPEG_QUALITY, q])
def escriu_tif(nom, arr16, desc):
    tifffile.imwrite(os.path.join(OUT, nom + '.tif'), arr16, photometric='rgb' if arr16.ndim == 3 else 'minisblack',
                     compression='zlib', metadata=None, resolution=(300, 300), description=desc.encode('ascii', 'replace').decode(),
                     extratags=[(34675, 7, len(ICC), ICC, False)])
    log('→', nom + '.tif')

yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32); rR = rr / R_SOL
r_ll = np.hypot(np.arange(W, dtype=np.float32)[None, :] - LLUNA[0], np.arange(H, dtype=np.float32)[:, None] - LLUNA[1]).astype(np.float32)
disc = r_ll < 470.0

# ================================================================== 1. dades
z = np.load(LUM)
Lc, sc, vc = z['L_c'], z['sig_c'], z['valid_c']
Lv, sv, vv = z['L_v'], z['sig_v'], z['valid_v']; Ls_saved, vs = z['L_s'], z['valid_s']; frac_s = z['frac_s']
geo = json.load(open(GEO))
log('lum_llenc carregat de', TREB)

CX, CY = geo['sony_sol_llenc']; S_ = geo['sony_escala']; thdeg = geo['sony_gir_deg']
SXs, SYs = 3894.7, 2768.7
c2, s2 = math.cos(math.radians(thdeg)), math.sin(math.radians(thdeg))
def warp(img):
    out = np.empty((H, W), np.float32)
    for y0 in range(0, H, 512):
        y1 = min(H, y0 + 512)
        yyg, xxg = np.mgrid[y0:y1, 0:W].astype(np.float64)
        ux = (xxg - CX) / S_; uy = (yyg - CY) / S_
        px = SXs + ux * c2 - uy * s2; py = SYs + ux * s2 + uy * c2
        out[y0:y1] = ndi.map_coordinates(img, [py, px], order=1, mode='constant', cval=0.0).astype(np.float32)
    return out
ap = geo['aparellament']; ks = geo['k_vermell_sony']
XXr = (np.arange(W, dtype=np.float32)[None, :] - SOL[0]) / R_SOL; YYr = (np.arange(H, dtype=np.float32)[:, None] - SOL[1]) / R_SOL
PLA = (ap['b0'] + ap['b1'] * XXr + ap['b2'] * YYr).astype(np.float32)

def lum_sony_placa(rgb_path, wt_path):
    sony = np.load(rgb_path, mmap_mode='r'); wt = np.load(wt_path, mmap_mode='r'); flat = np.load(FLAT, mmap_mode='r')
    Rs = np.asarray(sony[..., 0]) / np.asarray(flat[..., 0]); Gs = np.asarray(sony[..., 1]) / np.asarray(flat[..., 1])
    Ws = np.minimum(np.asarray(wt[..., 0]), np.asarray(wt[..., 1]))
    oks = np.isfinite(Rs) & np.isfinite(Gs) & (Ws > 0)
    oks = ndi.binary_erosion(oks, iterations=3, border_value=0)
    return np.where(oks, 0.5 * (Gs + ks * Rs), 0.0).astype(np.float32), np.where(oks, Ws, 0.0).astype(np.float32)

def sony_al_llenc(rgb_path, wt_path):
    Lg, Wg = lum_sony_placa(rgb_path, wt_path)
    L = warp(Lg); Wl = warp(Wg); ok = Wl > 0.5
    L = np.where(ok, ap['a'] * L + PLA, 0.0).astype(np.float32)
    return L, np.where(ok, Wl, 0.0).astype(np.float32), ok

# --- corr_lf (idèntic a v7 però amb l'apilat v3) ---
p_corr = os.path.join(V8, 'corr_lf.npy')
if 'corr_lf' in z.files:
    corr_lf = z['corr_lf'].astype(np.float32); np.save(p_corr, corr_lf)
    log('corr_lf llegida del npz (prepara_lluminancia_v3: poly4 + residu σ200 sense biaix de vora)')
elif os.path.exists(p_corr):
    corr_lf = np.load(p_corr)
else:
    L_s_raw, ws_l, valid_s = sony_al_llenc(os.path.join(SONY3, 'sony_stack_ref_rgb.npy'), os.path.join(SONY3, 'sony_stack_ref_wt.npy'))
    zona = vv & valid_s & (rR > 3.4)
    dif = np.where(zona, L_s_raw - Lv, 0.0).astype(np.float32); mz = zona.astype(np.float32)
    BS = 8; Hb, Wb = (H // BS) * BS, (W // BS) * BS
    def blk(a): return a[:Hb, :Wb].reshape(Hb // BS, BS, Wb // BS, BS).mean(axis=(1, 3))
    num = cv2.GaussianBlur(blk(dif), (0, 0), 200.0 / BS); den = cv2.GaussianBlur(blk(mz), (0, 0), 200.0 / BS)
    cs = np.where(den > 0.03, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    idx_ = ndi.distance_transform_edt(np.isnan(cs), return_distances=False, return_indices=True)
    cs = cs[tuple(idx_)]
    corr_lf = cv2.resize(cs, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    d = np.abs((L_s_raw - corr_lf) - Ls_saved)[valid_s & vs]
    log(f'corr_lf: mediana {np.median(corr_lf[zona]):+.2f}, p1/p99 {np.percentile(corr_lf[zona],1):+.1f}/{np.percentile(corr_lf[zona],99):+.1f}; comprovació vs L_s desada: mitjà {d.mean():.4f} màx {d.max():.3f}')
    np.save(p_corr, corr_lf); del L_s_raw, ws_l, dif, mz
Ld = np.where(vc, Lc + corr_lf, 0.0).astype(np.float32)
Lv2 = np.where(vv, Lv + corr_lf, 0.0).astype(np.float32)
Ls2 = np.where(vs, Ls_saved + corr_lf, 0.0).astype(np.float32)
# meitats de la Sony al llenç (mateixa geometria i aparellament; +0 perquè la costura no hi entra: les bandes no la veuen)
L_A, W_A, ok_A = sony_al_llenc(os.path.join(SONY3, 'sony_half_A_rgb.npy'), os.path.join(SONY3, 'sony_half_A_wt.npy'))
L_B, W_B, ok_B = sony_al_llenc(os.path.join(SONY3, 'sony_half_B_rgb.npy'), os.path.join(SONY3, 'sony_half_B_wt.npy'))
log('meitats Sony al llenç: pesos màx', float(W_A.max()), float(W_B.max()), 'vàlids', float(ok_A.mean()), float(ok_B.mean()))
del Lc

# --- estrelles: punts > 6 σ del passa-alt fi (σ 2,5 px) a r > 1,3 R☉, dilatats 8 px i omplerts amb l'entorn (σ 10):
#     un passa-alt al voltant d'una estrella fa un anell fosc i una taca «significativa» (les dues meitats la veuen)
def emmascara_estrelles(L, ok):
    """Estrelles: pics COMPACTES del DoG (σ 1,5 − σ 4) a r > 2,4 R☉, per damunt de 7 σ de l'anell (MAD per anells de
    0,25 R☉), màxim local 7×7 i contrast central (pic > 2× el valor a 6 px): les estructures coronals (allargades, de
    baix contrast) no hi entren. Dilatació 6 px i ompliment amb l'entorn (σ 8)."""
    g1 = cv2.GaussianBlur(L, (0, 0), 1.5); g4 = cv2.GaussianBlur(L, (0, 0), 4.0)
    dog = g1 - g4
    z = ok & (rR > 2.4)
    # σ per anell (robusta)
    nb = int(rR.max() / 0.25) + 1
    idx = np.minimum((rR / 0.25).astype(np.int32), nb - 1)
    sig = np.full(nb, np.nan, np.float32)
    sub = z[::3, ::3]; d_sub = dog[::3, ::3][sub]; i_sub = idx[::3, ::3][sub]
    for k in np.unique(i_sub):
        v = d_sub[i_sub == k]
        if v.size > 500: sig[k] = 1.4826 * np.median(np.abs(v - np.median(v)))
    okk = np.isfinite(sig); sig = np.interp(np.arange(nb), np.where(okk)[0], sig[okk]).astype(np.float32)
    thr = 7.0 * sig[idx]
    mx = cv2.dilate(dog, np.ones((7, 7), np.uint8))
    pics = z & (dog > thr) & (dog >= mx - 1e-6)
    # contrast central: el pic ha de valdre > 2× el màxim a 6 px (anell 5–7 px)
    k6 = np.zeros((13, 13), np.uint8); cv2.circle(k6, (6, 6), 6, 1, 1)
    ring_max = cv2.dilate(dog, k6)
    pics &= dog > 2.0 * np.maximum(ring_max, 0)
    n = int(pics.sum())
    kd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    m = cv2.dilate(pics.astype(np.uint8), kd).astype(bool)
    mm = (~m & ok).astype(np.float32)
    fill = cv2.GaussianBlur(L * mm, (0, 0), 8.0) / np.maximum(cv2.GaussianBlur(mm, (0, 0), 8.0), 1e-3)
    return np.where(m, fill, L).astype(np.float32), n, m
Ld, n_est, mask_est = emmascara_estrelles(Ld, vc)
log(f'estrelles emmascarades a L_d: {n_est} pics, {float(mask_est.mean())*100:.3f} % del llenç')
np.save(os.path.join(V8, 'mascara_estrelles.npy'), mask_est)
del mask_est

# validesa erosionada i tapers
k30 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ERODE_PX + 1, 2 * ERODE_PX + 1))
vcE = cv2.erode(vc.astype(np.uint8), k30, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool) & ~disc
kv = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
vvE = cv2.erode(vv.astype(np.uint8), kv).astype(bool) & ~disc
vsE = cv2.erode(vs.astype(np.uint8), kv, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool) & (rR > 3.3)
vAB = cv2.erode((ok_A & ok_B).astype(np.uint8), kv, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool) & (rR > 3.3)
dist_valid = cv2.distanceTransform(vcE.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
taper = smooth01(dist_valid / TAPER_PX).astype(np.float32)
if SEAM_TAPER_PX > 0:
    X1 = np.arange(W, dtype=np.float32)[None, :]; Y1 = np.arange(H, dtype=np.float32)[:, None]
    dbox = np.minimum(np.minimum(np.abs(X1 - 600), np.abs(X1 - 7348)) * np.ones((H, 1), np.float32), np.minimum(np.abs(Y1 - 550), np.abs(Y1 - 5103)) * np.ones((1, W), np.float32))
    taper *= smooth01((dbox - SEAM_TAPER_PX * 0.4) / SEAM_TAPER_PX); del dbox
del dist_valid
# graó residual a les vores de la caixa en L_d (registre)
def grao(L, ok, eix, pos, lo, hi):
    if eix == 'x':
        a = L[:, pos - hi:pos - lo]; b = L[:, pos + lo:pos + hi]; ma = ok[:, pos - hi:pos - lo]; mb = ok[:, pos + lo:pos + hi]
    else:
        a = L[pos - hi:pos - lo]; b = L[pos + lo:pos + hi]; ma = ok[pos - hi:pos - lo]; mb = ok[pos + lo:pos + hi]
    return float(np.median(b[mb]) - np.median(a[ma])) if ma.any() and mb.any() else float('nan')
okg = vcE & (rR > 3.6)
_ys, _xs = np.where(vv); CAIXA = dict(x0=int(_xs.min()), x1=int(_xs.max()), y0=int(_ys.min()), y1=int(_ys.max())); del _ys, _xs
graons = {f'{eix}={pos}': grao(Ld, okg, eix, pos, 100, 300) for eix, pos in (('x', CAIXA['x0']), ('x', CAIXA['x1']), ('y', CAIXA['y0']), ('y', CAIXA['y1']))}
log('caixa Vixen real (valid_v):', CAIXA)
log('graó de L_d a les vores de la caixa (mediana fora − dins, ±100..300 px, ADU/s):', {k: round(v, 2) for k, v in graons.items()})
log('referència profunda i tapers fets; vàlid erosionat', float(vcE.mean()))

# ================================================================== 2. log-polar i soroll
lp = LogPolar(H, W, SOL[0], SOL[1], NA=8192, NR=3072, r_min=400.0)
NA, NR = lp.NA, lp.NR
R, okp, mp0, c_ple = lp.residu_polar(Ld, vcE)
Rv, okv, mpv_, _ = lp.residu_polar(np.where(vvE, Lv2, 0), vvE)
Rs, oks, mps_, _ = lp.residu_polar(np.where(vsE, Ls2, 0), vsE)
RA, okA, mpA_, _ = lp.residu_polar(np.where(vAB, L_A + corr_lf, 0), vAB)
RB, okB, mpB_, _ = lp.residu_polar(np.where(vAB, L_B + corr_lf, 0), vAB)
mpv = mpv_ > 0.5; mps = mps_ > 0.5; both = mpv & mps; mpAB = (mpA_ > 0.5) & (mpB_ > 0.5)
fAB = mpAB.astype(np.float32)
wA_p = lp.cap_a_polar(W_A); wB_p = lp.cap_a_polar(W_B)
kAB = np.where(mpAB, wA_p * wB_p / np.maximum(wA_p + wB_p, 1e-6) ** 2, 0.0).astype(np.float32)   # var_total = var(A−B)·kAB
f_p = np.clip(lp.cap_a_polar(np.where(vcE, frac_s, 0.0)) / np.maximum(lp.cap_a_polar(vcE.astype(np.float32)), 1e-3), 0, 1)
# R₂ (m ≤ 2) per al NRGF
xp = lp.cap_a_polar(np.where(vcE, np.log(np.maximum(Ld, 1.0)), 0.0)) / np.maximum(lp.cap_a_polar(vcE.astype(np.float32)), 1e-3)
xp = lp.inpaint_radial(xp, mp0)
F2, _ = lp.fons_fourier(xp, okp, m_max=2)
R2 = ((xp - F2) * okp).astype(np.float32)
del xp, F2
rng = np.random.default_rng(7)
nimg = (rng.standard_normal((H, W)).astype(np.float32) * np.where(vvE, sv / np.maximum(Lv2, 1.0), 0.0)).astype(np.float32)
Npv = lp.cap_a_polar(nimg) / np.maximum(lp.cap_a_polar(vvE.astype(np.float32)), 1e-3)
del nimg, L_A, L_B
rcol = lp.r_of / R_SOL
log('residus polars; c_ple', c_ple, f'({rcol[c_ple]:.2f} R☉); zona comuna {float(both.mean()):.3f}; meitats {float(mpAB.mean()):.3f}')
jq = {}
for nom_, bmap in (('f_sony', f_p),):
    jq[nom_] = {f'{r}R': float(np.median(bmap[:, np.argmin(np.abs(rcol - r))][okp[:, np.argmin(np.abs(rcol - r))] > 0.5])) for r in (3.5, 4.5, 6, 7.5)}
log('pes de la Sony per radi:', jq)

_kθ = np.fft.rfftfreq(NA) * 2 * math.pi
def blur_ang(a, s_ang, s_rho=2.0):
    a = np.ascontiguousarray(a, np.float32)
    if s_rho > 0:
        a = cv2.GaussianBlur(a, (int(2 * math.ceil(3 * s_rho) + 1), 1), sigmaX=s_rho, sigmaY=0, borderType=cv2.BORDER_REPLICATE)
    A = np.fft.rfft(a, axis=0)
    A *= np.exp(-0.5 * (_kθ * s_ang) ** 2)[:, None].astype(np.float32)
    return np.fft.irfft(A, n=NA, axis=0).astype(np.float32)
def blur_ang_n(a, ok, s_ang, s_rho=2.0):
    return blur_ang(a * ok, s_ang, s_rho) / np.maximum(blur_ang(ok, s_ang, s_rho), 1e-3)

def soroll_col_comu(bv, bs):
    d2 = np.where(both, (bv - bs) ** 2, np.nan)
    nv_col = np.nanmedian(d2, axis=0) / 2.0
    okc = np.isfinite(nv_col) & (np.sum(both, axis=0) > 200)
    out = np.zeros(NR, np.float32)
    if okc.any():
        v = np.interp(np.arange(NR), np.where(okc)[0], nv_col[okc]).astype(np.float32)
        v = cv2.GaussianBlur(v.reshape(1, -1), (0, 0), 15.0, borderType=cv2.BORDER_REPLICATE).ravel()
        out = np.where(okc, v, 0.0).astype(np.float32)         # només on hi ha zona comuna; fora, 0 (mana el local)
        # suavitza la vora del domini: cap graó en el pis
        last = np.where(okc)[0].max(); first = np.where(okc)[0].min()
        out[last + 1:] = 0.0; out[:first] = 0.0
    return out

def soroll_banda(band_fn, s0, s1):
    """n² per píxel polar de la banda de L_d: (1−f)²·n_v²·F² + f²·n_s,local² amb pis per columna a la zona comuna."""
    n_v = band_fn(Npv, okv, s0, s1)
    bA = band_fn(RA, okA, s0, s1); bB = band_fn(RB, okB, s0, s1)
    d2 = ((bA - bB) ** 2) * fAB
    n2_s = lp.blur_n(d2, fAB, 2 * s1) * kAB                      # local, real, inclou sistemàtics de la Sony
    n2_s = np.where(mpAB, n2_s, 0.0)
    # fora de la zona de meitats (no hauria de passar gaire) i dins del radi de cremat: pren el màxim d'una mitjana per columna
    col = np.nanmedian(np.where(mpAB, n2_s, np.nan), axis=0); col = np.nan_to_num(col, nan=0.0)
    n2_s = np.where(mpAB, n2_s, col[None, :])
    n2_v = lp.blur_n(n_v * n_v, okv, 2 * s1)
    bv = band_fn(Rv, okv, s0, s1); bs = band_fn(Rs, oks, s0, s1)
    pis = soroll_col_comu(bv, bs)
    return n2_v, n2_s, pis[None, :], bv, bs

def band_iso(a, ok, s0, s1): return lp.blur_n(a, ok, s0) - lp.blur_n(a, ok, s1)
def band_ang(a, ok, s0, s1): return blur_ang_n(a, ok, s0) - blur_ang_n(a, ok, s1)
def mitjana_anell_zero(D, ok):
    m = (D * ok).sum(0) / np.maximum(ok.sum(0), 1)
    return ((D - m[None, :]) * ok).astype(np.float32)
def rms_col_robust(bg, ok, pis_col, s_smooth=20.0):
    v = np.where(ok > 0.5, bg * bg, np.nan)
    rms = np.sqrt(np.maximum(np.nanmedian(v, axis=0), 1e-12)) * 1.2
    rms = np.nan_to_num(rms, nan=1e-3)
    rms = cv2.GaussianBlur(rms.reshape(1, -1).astype(np.float32), (0, 0), s_smooth, borderType=cv2.BORDER_REPLICATE).ravel()
    return np.maximum(rms, np.sqrt(np.maximum(pis_col, 1e-12)) * 0.5).astype(np.float32)
def pes_banda(s1_deg, dr=0.0):
    # esvaïments radials per banda. Les fines acaben a 8 R☉: més enllà la corona (K+F ≈ 3 % del cel) no té estructura
    # detectable en aquestes bandes, i el que passa la porta a les zones només-Sony (7–9 R☉, cantons) té l'escala dels
    # residus del flat (pols: 100–200 px), comuns a les dues meitats. Les amples s'apaguen abans (incerteses de flat/cel).
    if s1_deg <= 2.15: ra, rb = 6.5, 8.0
    elif s1_deg <= 3.5: ra, rb = 6.0, 7.5
    elif s1_deg <= 6.0: ra, rb = 5.0, 7.0
    elif s1_deg <= 9.5: ra, rb = 4.5, 6.5
    else: ra, rb = 4.0, 6.0
    ra += dr; rb += dr
    return (1 - smooth01((rcol - ra) / (rb - ra))).astype(np.float32)[None, :]

qa = {'graons_Ld': graons, 'caixa_vixen': CAIXA, 'estrelles_emmascarades': n_est, 'c_ple_R': float(rcol[c_ple]), 'f_sony': jq}

KAP_MGN = (1.0 + smooth01((rcol - 5.0) / 2.0)).astype(np.float32)[None, :]   # pis d'anell de l'MGN ×2 a 7 R☉: el camp feble no s'iguala al fort
def filtre_bandes(nom, bandes, pesos, tsig, fsist, band_fn, mode, dr_fade=0.0, fsony=None):
    D = np.zeros_like(R); nb = 0
    for j in range(len(bandes) - 1):
        s0, s1 = bandes[j] * lp.px_deg, bandes[j + 1] * lp.px_deg
        b = band_fn(R, okp, s0, s1)
        n2_v, n2_s, pis, bv, bs = soroll_banda(band_fn, s0, s1)
        f2 = f_p
        fs_ = (fsony[j] if fsony else 1.0)
        vn = (1 - f2) ** 2 * n2_v * fsist[j] ** 2 + f2 ** 2 * n2_s * fs_ ** 2
        vn = np.maximum(vn, pis)
        v = lp.blur_n(b * b, okp, 2 * s1)
        w = np.clip(1.0 - (tsig[j] ** 2) * vn / np.maximum(v, 1e-12), 0, 1)
        bg = b * w
        pis_col = np.nanmedian(np.where(okp > 0.5, vn, np.nan), axis=0); pis_col = np.nan_to_num(pis_col, nan=1e-6)
        rms = rms_col_robust(bg, okp, pis_col)
        if mode == 'WHITE':
            Dj = bg / rms[None, :]
        elif mode == 'MGN':
            Dj = bg / np.sqrt(np.maximum(v + vn + (rms[None, :] * KAP_MGN) ** 2, 1e-12))
        D += pesos[j] * pes_banda(bandes[j + 1], dr_fade) * Dj; nb += pesos[j]
        zz = (rcol > 3.5) & (rcol < 8)
        frac = float((w[:, zz] > 0.5)[okp[:, zz] > 0.5].mean())
        fr_out = float((w[:, zz] > 0.5)[(okp[:, zz] > 0.5) & ~both[:, zz]].mean()) if (~both[:, zz] & (okp[:, zz] > 0.5)).any() else float('nan')
        qa[f'{nom}_{bandes[j]}-{bandes[j+1]}'] = dict(frac_sig_3p5_8=round(frac, 3), frac_sig_fora_caixa=round(fr_out, 3))
        log(f'{nom} banda {bandes[j]}–{bandes[j+1]}°: significatiu 3,5–8 R☉ {frac:.2f} (fora de la caixa {fr_out:.2f})')
        del b, n2_v, n2_s, bv, bs, vn, v, w, bg
    return mitjana_anell_zero(D / nb, okp)

# ================================================================== 3. filtres
D_rad = filtre_bandes('RADIALS', RAD_BANDES, RAD_W, RAD_TSIG, RAD_FSIST, band_ang, 'WHITE', fsony=RAD_FSONY)
zona = (rcol > 3.5) & (rcol < 5.5)
esc = float(np.percentile(np.abs(D_rad[:, zona][okp[:, zona] > 0.5]), 99))
D_rad = np.tanh(D_rad / (2.5 * esc)).astype(np.float32); qa['rad_esc'] = esc
D_mgn = filtre_bandes('MGN', MGN_BANDES, MGN_G, MGN_TSIG, MGN_FSIST, band_iso, 'MGN', dr_fade=-0.5, fsony=MGN_FSONY)
D_mgn = np.tanh(D_mgn / 1.5).astype(np.float32)
# NRGF
s_n = 0.25 * lp.px_deg
Rn = lp.blur_n(R2, okp, s_n)
n2_v, n2_s, pis, _, _ = soroll_banda(lambda a, ok, s0, s1: lp.blur_n(a, ok, s0), s_n, s_n)   # «banda» = suavitzat 0,25°
vn = np.maximum((1 - f_p) ** 2 * n2_v * 4.0 + f_p ** 2 * n2_s, pis)
pis_col = np.nan_to_num(np.nanmedian(np.where(okp > 0.5, vn, np.nan), axis=0), nan=1e-6)
sd = rms_col_robust(Rn, okp, pis_col * 4.0)
g_n = (1 - smooth01((rcol - 4.5) / 2.0)).astype(np.float32)[None, :]
D_nrgf = np.tanh(mitjana_anell_zero(g_n * Rn / sd[None, :], okp) / 2.5).astype(np.float32)
del Rn, n2_v, n2_s, vn
log('RADIALS, MGN, NRGF fets')

# DETALL EXTERIOR v8 (coherència Vixen–Sony; fora de la caixa, Sony sola amb porta local)
D_det = np.zeros_like(R); nb = 0; NUL = []
bm = both.astype(np.float32)
dist_in = lp.cap_a_polar(cv2.distanceTransform(vvE.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32))
fb = smooth01(dist_in / 120.0).astype(np.float32); del dist_in
for j in range(len(DET_BANDES) - 1):
    s0, s1 = DET_BANDES[j] * lp.px_deg, DET_BANDES[j + 1] * lp.px_deg
    b = band_iso(R, okp, s0, s1)
    n2_v, n2_s, pis, bv, bs = soroll_banda(band_iso, s0, s1)
    vn = np.maximum((1 - f_p) ** 2 * n2_v * DET_FSIST[j] ** 2 + f_p ** 2 * n2_s * DET_FSONY[j] ** 2, pis)
    v = lp.blur_n(b * b, okp, 2 * s1)
    w = np.clip(1.0 - (DET_TSIG[j] ** 2) * vn / np.maximum(v, 1e-12), 0, 1)
    num = lp.blur_n(bv * bs * bm, bm, 2 * s1)
    den = np.sqrt(np.maximum(lp.blur_n(bv * bv * bm, bm, 2 * s1) * lp.blur_n(bs * bs * bm, bm, 2 * s1), 1e-20))
    cc_ = np.clip(num / den, 0.0, 1.0) ** 1.5
    coh = (cc_ * 0.5 * (bv + bs) * bm).astype(np.float32)
    bs_n = np.roll(bs, NA // 2, axis=0)
    num_n = lp.blur_n(bv * bs_n * bm, bm, 2 * s1); den_n = np.sqrt(np.maximum(lp.blur_n(bv * bv * bm, bm, 2 * s1) * lp.blur_n(bs_n * bs_n * bm, bm, 2 * s1), 1e-20))
    coh_n = (np.clip(num_n / den_n, 0, 1) ** 1.5 * 0.5 * (bv + bs_n) * bm).astype(np.float32)
    z35 = (rcol > 3.5) & (rcol < 5.5)
    NUL.append((DET_BANDES[j], float(np.std(coh[:, z35][bm[:, z35] > 0.5])), float(np.std(coh_n[:, z35][bm[:, z35] > 0.5]))))
    # fora de la caixa: la Sony sola amb la porta de soroll LOCAL (real, de les meitats), a la meitat
    vs_s = lp.blur_n(bs * bs, oks, 2 * s1)
    w_s = np.clip(1.0 - (DET_TSIG[j] ** 2) * np.maximum(n2_s, 1e-12) * DET_FSONY[j] ** 2 * 1.5 / np.maximum(vs_s, 1e-12), 0, 1)
    sony = bs * w_s * 0.5
    Dj = fb * coh + (1 - fb) * sony
    D_det += DET_G[j] * pes_banda(DET_BANDES[j + 1]) * Dj; nb += DET_G[j]
    log(f'DETALL banda {DET_BANDES[j]}–{DET_BANDES[j+1]}°: control nul σ real {NUL[-1][1]:.5f} vs 180° {NUL[-1][2]:.5f} (raó {NUL[-1][1]/max(NUL[-1][2],1e-12):.1f})')
    del b, n2_v, n2_s, bv, bs, vn, v, w, num, den, cc_, coh, bs_n, num_n, den_n, coh_n, vs_s, w_s, sony, Dj
D_det = mitjana_anell_zero(D_det / nb, okp)
zona = (rcol > 3.5) & (rcol < 5.5)
esc_d = float(np.percentile(np.abs(D_det[:, zona][okp[:, zona] > 0.5]), 99))
D_det = np.tanh(D_det / (2.5 * esc_d)).astype(np.float32); qa['det_esc'] = esc_d; qa['det_nul'] = NUL
log('DETALL fet')

# ================================================================== 4. a la imatge
def perfil_anell(a, w, dr=4.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1).ravel()
    sw = np.bincount(idx, weights=(a * w).ravel().astype(np.float64), minlength=n)
    ww = np.bincount(idx, weights=w.ravel().astype(np.float64), minlength=n)
    cnt = np.bincount(idx, minlength=n)
    c = np.where(ww > 0.05 * np.maximum(cnt, 1), sw / np.maximum(ww, 1e-9), 0.0)
    return np.interp(rr, (np.arange(n) + 0.5) * dr, c).astype(np.float32)

mask_p = cv2.GaussianBlur((smooth01((rR - R_MASK[0]) / (R_MASK[1] - R_MASK[0])) * (r_ll > 470.0)).astype(np.float32), (0, 0), 3)
mask_f = cv2.GaussianBlur((smooth01((rR - R_MASK_FULL[0]) / (R_MASK_FULL[1] - R_MASK_FULL[0])) * (r_ll > 455.0)).astype(np.float32), (0, 0), 3)
np.save(os.path.join(V8, 'mascara_profund.npy'), u16(mask_p)); np.save(os.path.join(V8, 'mascara_campcomplet.npy'), u16(mask_f))
escriu_tif('MASCARA_profund_v8', u16(mask_p), 'Mascara radial: 0 dins de 2.6 R, 1 a partir de 3.6 R. 2026-08-19')
escriu_tif('MASCARA_campcomplet_v8', u16(mask_f), 'Mascara radial: 0 al disc i fins a 1.15 R, 1 a partir de 1.35 R. 2026-08-19')
win_det = (smooth01((rR - DET_RIN[0] * R_SOL) / ((DET_RIN[1] - DET_RIN[0]) * R_SOL)) * (1 - smooth01((rR - DET_ROUT[0] * R_SOL) / ((DET_ROUT[1] - DET_ROUT[0]) * R_SOL)))).astype(np.float32)
mask_det = cv2.GaussianBlur((win_det * vcE.astype(np.float32)), (0, 0), 3)
np.save(os.path.join(V8, 'mascara_detall.npy'), u16(mask_det))
escriu_tif('MASCARA_detall_v8', u16(mask_det), 'Mascara radial del DETALL EXTERIOR: 2.8-4.2 -> 6-7.5 R. 2026-08-19')

res = {}
for nom, Dp, A, desc in (('RADIALS_v8', D_rad, A_RAD, 'RADIALS v8: Espenak multiescala (bandes angulars 0.4-2, 2-6, 6-18 graus) sobre L_d v3 (Vixen HDR + Sony v3 tots >1/8 s, flat 300 mm), soroll real local (meitats Sony), mitjana zero per anell, 0.5 exacte fora de dades. Overlay ~40 %. 2026-08-19'),
                         ('MGN_v8', D_mgn, A_MGN, 'MGN v8: bandes isotropes 0.5-9 graus sobre L_d v3, soroll real local, normalitzacio local amb pis d anell, mitjana zero per anell, 0.5 exacte fora de dades. Overlay ~30 %. 2026-08-19'),
                         ('NRGF_v8', D_nrgf, A_NRGF, 'NRGF v8: (ln L_d - fons m<=2)/sigma anell amb pis de soroll, 4.5->7 R, mitjana zero per anell. Overlay ~8 %. 2026-08-19'),
                         ('DETALL_EXTERIOR_v8', D_det, A_DET, 'DETALL EXTERIOR v8: coherencia Vixen-Sony per banda (0.8-9 graus), fora de la caixa Sony sola amb porta local, control nul 180. Linear Light ~25 %, mascara 2.8-4.2 -> 6-7.5 R. 2026-08-19')):
    Dimg = lp.cap_a_imatge(Dp) * taper
    c_r = perfil_anell(Dimg, taper)
    Dimg = ((Dimg - c_r) * taper).astype(np.float32)
    Dimg[disc] = 0.0; Dimg[~vc] = 0.0
    capa = np.clip(0.5 + A * Dimg, 0, 1).astype(np.float32)
    rgb = np.repeat(u16(capa)[..., None], 3, axis=2)
    np.save(os.path.join(V8, nom + '.npy'), rgb)
    escriu_tif(nom, rgb, desc)
    jpg(os.path.join(V8, nom + '_x4.jpg'), cv2.resize(np.clip((capa - 0.5) * 6 + 0.5, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA))
    st = {}
    for ra, rb in ((2.0, 2.6), (3.0, 3.5), (3.5, 4.5), (4.5, 5.5), (5.5, 6.5), (6.5, 7.5), (7.5, 8.5), (8.5, 9.5)):
        m = (rR > ra) & (rR < rb) & vcE
        d = Dimg[m] * A
        st[f'{ra}-{rb}'] = dict(rms=float(np.sqrt(np.mean(d * d))), p99=float(np.percentile(np.abs(d), 99)), mitjana=float(np.mean(d)))
    res[nom] = st
    log(nom, ' '.join(f"{k}: rms {v['rms']:.4f} p99 {v['p99']:.4f}" for k, v in st.items()))
    del Dimg, capa, rgb

# ================================================================== 5. Radials B de Pere amb el camp llunyà neutre (camp net v8)
for src, nom in (('capa1_rgb16.npy', 'RadialsB_original_campnet_v8'), (os.path.join('capes3', 'RadialsB_campnet.npy'), 'RadialsB_campnet_v8')):
    rb = np.load(os.path.join(SCR, src))
    h1, w1 = rb.shape[:2]; top1, left1 = 549, 599
    rr1 = rR[top1:top1 + h1, left1:left1 + w1]
    keep = (1 - smooth01((rr1 - 4.5) / 1.0)).astype(np.float32)
    out = np.empty_like(rb)
    for c in range(3):
        a = rb[..., c].astype(np.float32) / 65535.0
        out[..., c] = u16(0.5 + (a - 0.5) * keep)
    np.save(os.path.join(V8, nom + '.npy'), out)
    escriu_tif(nom, out, 'Radials B de Pere; camp > 4.5-5.5 R exactament neutre (0.5). Posar a E+(599,549). 2026-08-19')
    del rb, out
json.dump(dict(qa=qa, capes=res, A=dict(rad=A_RAD, mgn=A_MGN, nrgf=A_NRGF, det=A_DET), TAPER_PX=TAPER_PX, SEAM_TAPER_PX=SEAM_TAPER_PX,
               RAD=dict(bandes=RAD_BANDES, w=RAD_W, tsig=RAD_TSIG, fsist=RAD_FSIST, fsony=RAD_FSONY), MGN=dict(bandes=MGN_BANDES, g=MGN_G, tsig=MGN_TSIG, fsist=MGN_FSIST, fsony=MGN_FSONY),
               DET=dict(bandes=DET_BANDES, g=DET_G, tsig=DET_TSIG, fsist=DET_FSIST, rin=DET_RIN, rout=DET_ROUT)),
          open(os.path.join(V8, 'filtres_profunds_v8.json'), 'w'), indent=1)
log('fi')
