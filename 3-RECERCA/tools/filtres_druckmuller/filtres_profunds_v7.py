"""Filtres «profunds» per a FiltresSEMIFINAL7.psb (19-08-2026, nit).

Pere (19-08, vespre): «els filtres que afecten la corona externa han de fer-se pensant en l'stack de les
exposicions de la Sony de llarga durada i les de Vixen de llarga durada», i «ja amb les correccions de
gradient/vinyetatge de les lents a la part exterior», sense carregar-se el gradient suau que ja tenim.

Referència profunda L_d (al llenç 7648×5353, ADU/s del Vixen):
  L_c v2 (treball2/lum_llenc.npz: Vixen HDR dins, Vixen+Sony v2 de 13 fotogrames ≥ 1/8 s de 3,3 R☉ enfora,
  pesos 1/σ²) + corr_lf, la correcció de baixa freqüència (σ 200 px) que prepara_lluminancia.py havia RESTAT a
  la Sony perquè coincidís amb el Vixen a la costura. Afegir-la torna a posar el camp llunyà amb el flat MESURAT
  del 300 mm (research/80 §9: bo a 0,993–1,006 de 4 a 8,8 R☉) en lloc de la vinyeta sense flat del VSD90SS
  (≤ 3 % als cantons). Es recupera exactament repetint el warp i l'aparellament de la Sony amb la geometria
  desada, i es comprova contra la L_s desada (error < 0,01 ADU/s). El pla del cel i el que quedi de vinyeta
  (m = 0, 1, 2 en azimut) se'ls menja el fons de Fourier per anell abans de filtrar: cap filtre no els veu.

Tres filtres, en log-polars (files = angle, columnes = ln r), sobre R = ln L_d − fons de Fourier:
  RADIALS profund  bandes NOMÉS angulars 0,4–2°, 2–6°, 6–18° (l'Espenak multiescala = el relleu del Radials B
                   de Pere), σ radial 2 columnes (~0,16 % de r), porta de Wiener per banda amb el soroll REAL
                   (var(b_v − b_s)/2 entre trens, per columna) i blanquejat per anell → tanh.
  MGN profund      bandes isòtropes 0,5…9° (DoG en graus), porta de Wiener, normalització local amb pis de
                   soroll I pis d'anell (on l'estructura és feble mana la normalització per anell: conserva la
                   jerarquia i no pinta el camp feble) → tanh. És la part de detall del corona_detall_v2 sense la log.
  NRGF profund     R₂ (fons m ≤ 2: només pla/vinyeta) suavitzat 0,25°, dividit per la σ robusta de l'anell
                   amb pis de soroll → tanh(·/2,5).
Tots: mitjana zero per anell (no toquen el perfil radial), porta de soroll (neutres on no hi ha estructura),
esvaïts a 150 px de qualsevol vora de dades i de la costura de la caixa Vixen; les bandes FINES (≤ 2°) arriben
fins a 7,5→9 R☉ i les AMPLES s'apaguen abans i molt gradualment (3,4°: 6→8,5; 5,5°: 5→7,5; 9°: 4,5→7; 18°: 4→6,5;
el NRGF 4,5→7),
perquè a 7 R☉ una banda de 9° són 500 px, l'escala on viuen les incerteses de flat i cel entre trens. Fora de
la caixa Vixen (un sol tren) només passen les bandes fines, a la meitat (el NRGF a la meitat). Capa grisa
0,5 + A·D (Overlay), 16 bits, + MASCARA_profund (0 dins de 2,6 R☉ → 1 a 3,6; pinta-la si vols).

Sortides: FD3_SCR/v7/*.npy, TIF a FD3_OUT, QA jpg/json.
"""
import os, sys, json, math, time
import numpy as np, cv2, tifffile
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polar_utils import LogPolar, smooth01

SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
ROOT = os.path.dirname(SCR)
LUM = os.environ.get('FD3_LUM2', os.path.join(ROOT, 'treball2', 'lum_llenc.npz'))
GEO = os.path.join(ROOT, 'treball2', 'lum_llenc_geometria.json')
SONY2 = os.path.join(ROOT, 'sony2')
OUT = os.environ.get('FD3_OUT', os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10'))
V7 = os.path.join(SCR, 'v7'); os.makedirs(V7, exist_ok=True)
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
LLUNA = (4034.7, 2736.7)
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
# paràmetres
A_RAD = float(os.environ.get('V7_A_RAD', 0.125)); A_MGN = float(os.environ.get('V7_A_MGN', 0.125)); A_NRGF = float(os.environ.get('V7_A_NRGF', 0.20))
R_FAR = (7.5, 9.0)                     # esvaïment exterior (R☉)
R_MASK = (2.6, 3.6)                    # màscara: entrada (R☉)
TAPER_PX = 150.0                       # esvaïment a les vores de dades i a la costura de la caixa Vixen
RAD_BANDES = [0.4, 2.0, 6.0, 18.0]; RAD_W = [1.0, 0.6, 0.25]; RAD_TSIG = [1.8, 1.3, 1.1]; RAD_FSIST = [3.0, 2.0, 1.6]
MGN_BANDES = [0.5, 0.8, 1.3, 2.1, 3.4, 5.5, 9.0]; MGN_G = [1.0, 1.2, 1.3, 1.2, 0.6, 0.3]; MGN_TSIG = [2.2, 1.8, 1.5, 1.3, 1.15, 1.05]; MGN_FSIST = [3.0, 2.5, 2.0, 1.8, 1.6, 1.5]
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

# ================================================================== 1. dades i referència profunda
z = np.load(LUM)
Lc, sc, vc = z['L_c'], z['sig_c'], z['valid_c']
Lv, vv = z['L_v'], z['valid_v']; Ls_saved, vs = z['L_s'], z['valid_s']
geo = json.load(open(GEO))
log('lum_llenc v2 carregat')

# --- 1a. recuperar corr_lf: warp de la Sony v2 aplanada amb la geometria desada + aparellament ----------
def corr_lf_recupera():
    p = os.path.join(V7, 'corr_lf.npy')
    if os.path.exists(p):
        return np.load(p)
    sony = np.load(os.path.join(SONY2, 'sony_stack_v2_rgb.npy'), mmap_mode='r')
    wt = np.load(os.path.join(SONY2, 'sony_stack_v2_wt.npy'), mmap_mode='r')
    flat = np.load(os.path.join(ROOT, 'sony', 'flat_a7r3a_rgb.npy'), mmap_mode='r')
    Rs = np.asarray(sony[..., 0]) / np.asarray(flat[..., 0]); Gs = np.asarray(sony[..., 1]) / np.asarray(flat[..., 1])
    Ws = np.minimum(np.asarray(wt[..., 0]), np.asarray(wt[..., 1]))
    oks = np.isfinite(Rs) & np.isfinite(Gs) & (Ws > 0)
    oks = ndi.binary_erosion(oks, iterations=3, border_value=0)
    ks = geo['k_vermell_sony']
    Ls_g = np.where(oks, 0.5 * (Gs + ks * Rs), 0.0).astype(np.float32); Ws_g = np.where(oks, Ws, 0.0).astype(np.float32)
    del Rs, Gs, Ws, oks, sony, wt, flat
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
    L_s = warp(Ls_g); ws_l = warp(Ws_g); valid_s = ws_l > 0.5
    del Ls_g, Ws_g
    ap = geo['aparellament']
    XX = (np.arange(W, dtype=np.float32)[None, :] - SOL[0]) / R_SOL; YY = (np.arange(H, dtype=np.float32)[:, None] - SOL[1]) / R_SOL
    L_s = np.where(valid_s, ap['a'] * L_s + (ap['b0'] + ap['b1'] * XX + ap['b2'] * YY), 0.0).astype(np.float32)
    # la costura, idèntica a prepara_lluminancia.py §4 bis
    zona = vv & valid_s & (rR > 3.4)
    dif = np.where(zona, L_s - Lv, 0.0).astype(np.float32); mz = zona.astype(np.float32)
    BS = 8; Hb, Wb = (H // BS) * BS, (W // BS) * BS
    def blk(a): return a[:Hb, :Wb].reshape(Hb // BS, BS, Wb // BS, BS).mean(axis=(1, 3))
    num = cv2.GaussianBlur(blk(dif), (0, 0), 200.0 / BS); den = cv2.GaussianBlur(blk(mz), (0, 0), 200.0 / BS)
    cs = np.where(den > 0.03, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    idx_ = ndi.distance_transform_edt(np.isnan(cs), return_distances=False, return_indices=True)
    cs = cs[tuple(idx_)]
    corr = cv2.resize(cs, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    # comprovació: L_s − corr ha de ser la L_s desada
    d = np.abs((L_s - corr) - Ls_saved)[valid_s & vs]
    log(f'corr_lf recuperada: mediana {np.median(corr[zona]):+.2f}, p1/p99 {np.percentile(corr[zona],1):+.1f}/{np.percentile(corr[zona],99):+.1f} ADU/s; '
        f'comprovació contra L_s desada: error mitjà {d.mean():.4f}, màxim {d.max():.3f} ADU/s; valid_s coincideix {float((valid_s==vs).mean()):.5f}')
    np.save(p, corr)
    # vista
    v = np.clip((corr + 6) / 16, 0, 1); jpg(os.path.join(V7, 'corr_lf_x8.jpg'), cv2.resize(v, (W // 8, H // 8), interpolation=cv2.INTER_AREA))
    return corr

corr_lf = corr_lf_recupera()
Ld = np.where(vc, Lc + corr_lf, 0.0).astype(np.float32)
Lv2 = np.where(vv, Lv + corr_lf, 0.0).astype(np.float32)    # Vixen amb el mateix camp de baixa freqüència (per al soroll entre trens)
for ra, rb in ((3.5, 4.0), (5.0, 5.5), (7.0, 7.5), (8.5, 9.0)):
    m = vc & (rR > ra) & (rR < rb)
    log(f'   {ra}–{rb} R☉: L_c {np.median(Lc[m]):.1f} → L_d {np.median(Ld[m]):.1f} (corr mediana {np.median(corr_lf[m]):+.2f}, p5/p95 {np.percentile(corr_lf[m],5):+.1f}/{np.percentile(corr_lf[m],95):+.1f})')
del Lc

# validesa erosionada (tira brillant del marc Sony, vores) i sense el disc lunar
k30 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))
vcE = cv2.erode(vc.astype(np.uint8), k30, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool) & ~disc
kv = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
vvE = cv2.erode(vv.astype(np.uint8), kv).astype(bool) & ~disc
vsE = cv2.erode(vs.astype(np.uint8), kv, borderType=cv2.BORDER_CONSTANT, borderValue=1).astype(bool) & (rR > 3.3)
dist_valid = cv2.distanceTransform(vcE.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
taper = smooth01(dist_valid / TAPER_PX).astype(np.float32)
# costura de la caixa Vixen (la composició canvia de caràcter): ±TAPER_PX al voltant del rectangle
X1 = np.arange(W, dtype=np.float32)[None, :]; Y1 = np.arange(H, dtype=np.float32)[:, None]
dbox = np.minimum(np.minimum(np.abs(X1 - 600), np.abs(X1 - 7348)) * np.ones((H, 1), np.float32), np.minimum(np.abs(Y1 - 550), np.abs(Y1 - 5103)) * np.ones((1, W), np.float32))
taper *= smooth01((dbox - TAPER_PX * 0.4) / TAPER_PX)
taper *= (1 - smooth01((rR - R_FAR[0]) / (R_FAR[1] - R_FAR[0])))
taper = taper.astype(np.float32)
del dbox, dist_valid
log('referència profunda i tapers fets; vàlid erosionat', float(vcE.mean()))

# ================================================================== 2. log-polar
lp = LogPolar(H, W, SOL[0], SOL[1], NA=8192, NR=3072, r_min=400.0)
NA, NR = lp.NA, lp.NR
R, okp, mp0, c_ple = lp.residu_polar(Ld, vcE)           # fons m ≤ 4
Rv, okv, mpv_, _ = lp.residu_polar(np.where(vvE, Lv2, 0), vvE)
Rs, oks, mps_, _ = lp.residu_polar(np.where(vsE, Ls_saved, 0), vsE)
mpv = mpv_ > 0.5; mps = mps_ > 0.5; both = mpv & mps
# R₂: fons m ≤ 2 (per al NRGF)
xp = lp.cap_a_polar(np.where(vcE, np.log(np.maximum(Ld, 1.0)), 0.0)) / np.maximum(lp.cap_a_polar(vcE.astype(np.float32)), 1e-3)
xp = lp.inpaint_radial(xp, mp0)
F2, _ = lp.fons_fourier(xp, okp, m_max=2)
R2 = ((xp - F2) * okp).astype(np.float32)
del xp, F2
# soroll sintètic en ln (σ_c / L_d)
rng = np.random.default_rng(7)
nimg = (rng.standard_normal((H, W)).astype(np.float32) * np.where(vcE, sc / np.maximum(Ld, 1.0), 0.0)).astype(np.float32)
Np = lp.cap_a_polar(nimg) / np.maximum(lp.cap_a_polar(vcE.astype(np.float32)), 1e-3)
del nimg
rcol = lp.r_of / R_SOL
log('residus polars; c_ple', c_ple, f'({rcol[c_ple]:.2f} R☉); zona comuna {float(both.mean()):.3f}')
# dins de la caixa Vixen (els dos trens) = 1; fora (només Sony) = 0, transició 150 px
dist_in = lp.cap_a_polar(cv2.distanceTransform(vvE.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32))
fb = smooth01(dist_in / 150.0).astype(np.float32)
del dist_in
def pes_banda(s1_deg):
    """Pes radial i pes fora de la caixa per a una banda d'amplada s1 (graus): les bandes amples s'apaguen abans
    (a 7 R☉ una banda de 9° són 500 px: l'escala on viuen les incerteses de flat/cel entre trens, research/80 §9),
    i fora de la caixa (un sol tren) només passen les fines, atenuades."""
    if s1_deg <= 2.15: ra, rb, wo = 7.5, 9.0, 0.5
    elif s1_deg <= 3.5: ra, rb, wo = 6.0, 8.5, 0.25
    elif s1_deg <= 6.0: ra, rb, wo = 5.0, 7.5, 0.0
    elif s1_deg <= 9.5: ra, rb, wo = 4.5, 7.0, 0.0
    else: ra, rb, wo = 4.0, 6.5, 0.0
    g = (1 - smooth01((rcol - ra) / (rb - ra))).astype(np.float32)
    return g[None, :] * (wo + (1 - wo) * fb)

# --- desenfoc només angular per FFT (periòdic en angle, exacte) + σ radial petita ----------------------
_kθ = np.fft.rfftfreq(NA) * 2 * math.pi         # rad/fila
def blur_ang(a, s_ang, s_rho=2.0):
    """gaussiana σ=s_ang files al llarg de l'angle (FFT, periòdica) i σ=s_rho columnes radials."""
    a = np.ascontiguousarray(a, np.float32)
    if s_rho > 0:
        a = cv2.GaussianBlur(a, (int(2 * math.ceil(3 * s_rho) + 1), 1), sigmaX=s_rho, sigmaY=0, borderType=cv2.BORDER_REPLICATE)
    A = np.fft.rfft(a, axis=0)
    A *= np.exp(-0.5 * (_kθ * s_ang) ** 2)[:, None].astype(np.float32)
    return np.fft.irfft(A, n=NA, axis=0).astype(np.float32)
def blur_ang_n(a, ok, s_ang, s_rho=2.0):
    return blur_ang(a * ok, s_ang, s_rho) / np.maximum(blur_ang(ok, s_ang, s_rho), 1e-3)

def soroll_real_col(bv, bs):
    """var(b_v − b_s)/2 per columna a la zona comuna (inclou sistemàtics de cada tren), mediana robusta; interpolat."""
    d2 = np.where(both, (bv - bs) ** 2, np.nan)
    nv_col = np.nanmedian(d2, axis=0) / 2.0
    okc = np.isfinite(nv_col) & (np.sum(both, axis=0) > 200)
    if okc.any():
        last = np.where(okc)[0].max()
        nv_col = np.interp(np.arange(len(nv_col)), np.where(okc)[0], nv_col[okc]); nv_col[last + 1:] = nv_col[last]
        nv_col = cv2.GaussianBlur(nv_col.reshape(1, -1).astype(np.float32), (0, 0), 15.0, borderType=cv2.BORDER_REPLICATE).ravel()
    else:
        nv_col = np.zeros(NR, np.float32)
    return nv_col.astype(np.float32)

def mitjana_anell_zero(D, ok):
    m = (D * ok).sum(0) / np.maximum(ok.sum(0), 1)
    return ((D - m[None, :]) * ok).astype(np.float32)

def rms_col_robust(bg, ok, vn_col, s_smooth=20.0):
    v = np.where(ok > 0.5, bg * bg, np.nan)
    rms = np.sqrt(np.maximum(np.nanmedian(v, axis=0), 1e-12)) * 1.2
    rms = np.nan_to_num(rms, nan=1e-3)
    rms = cv2.GaussianBlur(rms.reshape(1, -1).astype(np.float32), (0, 0), s_smooth, borderType=cv2.BORDER_REPLICATE).ravel()
    return np.maximum(rms, np.sqrt(np.maximum(vn_col, 1e-12)) * 0.5).astype(np.float32)

qa = {}
# ================================================================== 3. RADIALS profund (bandes angulars)
D_rad = np.zeros_like(R); nb = 0
for j in range(len(RAD_BANDES) - 1):
    s0, s1 = RAD_BANDES[j] * lp.px_deg, RAD_BANDES[j + 1] * lp.px_deg
    b = blur_ang_n(R, okp, s0) - blur_ang_n(R, okp, s1)
    n = blur_ang(Np, s0) - blur_ang(Np, s1)
    bv = blur_ang_n(Rv, okv, s0) - blur_ang_n(Rv, okv, s1); bs = blur_ang_n(Rs, oks, s0) - blur_ang_n(Rs, oks, s1)
    nv_col = soroll_real_col(bv, bs)
    del bv, bs
    v = lp.blur_n(b * b, okp, 2 * s1); vn = lp.blur_n(n * n, okp, 2 * s1)
    vn = np.maximum(vn * RAD_FSIST[j] ** 2, nv_col[None, :])
    w = np.clip(1.0 - (RAD_TSIG[j] ** 2) * vn / np.maximum(v, 1e-12), 0, 1)
    bg = b * w
    rms = rms_col_robust(bg, okp, nv_col)
    D_rad += RAD_W[j] * pes_banda(RAD_BANDES[j + 1]) * bg / rms[None, :]; nb += RAD_W[j]
    frac = float((w[:, (rcol > 3.5) & (rcol < 8)] > 0.5).mean())
    qa[f'rad_{RAD_BANDES[j]}-{RAD_BANDES[j+1]}'] = dict(frac_sig_3p5_8=round(frac, 3), rms_col_4R=float(rms[np.argmin(np.abs(rcol - 4))]), rms_col_7R=float(rms[np.argmin(np.abs(rcol - 7))]))
    log(f'RADIALS banda {RAD_BANDES[j]}–{RAD_BANDES[j+1]}°: fracció significativa 3,5–8 R☉ {frac:.2f}')
    del b, n, v, vn, w, bg
D_rad = mitjana_anell_zero(D_rad / nb, okp)
zona = (rcol > 3.5) & (rcol < 5.5)
esc = float(np.percentile(np.abs(D_rad[:, zona][okp[:, zona] > 0.5]), 99))
D_rad = np.tanh(D_rad / (2.5 * esc)).astype(np.float32)      # règim quasi lineal: p99 a 3,5–5,5 → ±0,38
qa['rad_esc_p99'] = esc
log(f'RADIALS: escala p99 {esc:.4f}')

# ================================================================== 4. MGN profund (bandes isòtropes, normalització local)
D_mgn = np.zeros_like(R); nb = 0
for j in range(len(MGN_BANDES) - 1):
    s0, s1 = MGN_BANDES[j] * lp.px_deg, MGN_BANDES[j + 1] * lp.px_deg
    b = lp.blur_n(R, okp, s0) - lp.blur_n(R, okp, s1)
    n = lp.blur(Np, s0) - lp.blur(Np, s1)
    bv = lp.blur_n(Rv, okv, s0) - lp.blur_n(Rv, okv, s1); bs = lp.blur_n(Rs, oks, s0) - lp.blur_n(Rs, oks, s1)
    nv_col = soroll_real_col(bv, bs)
    del bv, bs
    v = lp.blur_n(b * b, okp, 2 * s1); vn = lp.blur_n(n * n, okp, 2 * s1)
    vn = np.maximum(vn * MGN_FSIST[j] ** 2, nv_col[None, :])
    w = np.clip(1.0 - (MGN_TSIG[j] ** 2) * vn / np.maximum(v, 1e-12), 0, 1)
    # MGN: normalització LOCAL amb pis de soroll (σ_local² + n²) I pis d'anell (rms típic de la banda a l'anell):
    # on l'estructura és forta mana la local (±1, com l'MGN); on és feble, la de l'anell (conserva la jerarquia i
    # no «pinta» el camp feble amb el mateix contrast que el fort)
    rms_an = rms_col_robust(b * w, okp, nv_col)
    D_mgn += MGN_G[j] * pes_banda(MGN_BANDES[j + 1]) * (b * w) / np.sqrt(np.maximum(v + vn + rms_an[None, :] ** 2, 1e-12)); nb += MGN_G[j]
    frac = float((w[:, (rcol > 3.5) & (rcol < 8)] > 0.5).mean())
    qa[f'mgn_{MGN_BANDES[j]}-{MGN_BANDES[j+1]}'] = dict(frac_sig_3p5_8=round(frac, 3))
    log(f'MGN banda {MGN_BANDES[j]}–{MGN_BANDES[j+1]}°: fracció significativa 3,5–8 R☉ {frac:.2f}')
    del b, n, v, vn, w
D_mgn = mitjana_anell_zero(D_mgn / nb, okp)
D_mgn = np.tanh(D_mgn / 1.5).astype(np.float32)

# ================================================================== 5. NRGF profund
s_n = 0.25 * lp.px_deg
Rn = lp.blur_n(R2, okp, s_n)
nn = lp.blur(Np, s_n)
vn_col = np.nanmedian(np.where(okp > 0.5, nn * nn, np.nan), axis=0); vn_col = np.nan_to_num(vn_col, nan=1e-6).astype(np.float32)
sd = rms_col_robust(Rn, okp, vn_col * 4.0)     # σ robusta de l'anell amb pis de soroll (×2 en σ)
g_n = (1 - smooth01((rcol - 4.5) / 2.5)).astype(np.float32)[None, :] * (0.5 + 0.5 * fb)
D_nrgf = mitjana_anell_zero(g_n * Rn / sd[None, :], okp)
D_nrgf = np.tanh(D_nrgf / 2.5).astype(np.float32)
del Rn, nn, R2
log('NRGF fet')

# ================================================================== 6. a la imatge, tapers, mitjana zero per anell, capes
def perfil_anell(a, w, dr=4.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1).ravel()
    sw = np.bincount(idx, weights=(a * w).ravel().astype(np.float64), minlength=n)
    ww = np.bincount(idx, weights=w.ravel().astype(np.float64), minlength=n)
    cnt = np.bincount(idx, minlength=n)
    c = np.where(ww > 0.05 * np.maximum(cnt, 1), sw / np.maximum(ww, 1e-9), 0.0)
    r_c = (np.arange(n) + 0.5) * dr
    return np.interp(rr, r_c, c).astype(np.float32)

mask = (smooth01((rR - R_MASK[0]) / (R_MASK[1] - R_MASK[0])) * (r_ll > 470.0)).astype(np.float32)
mask = cv2.GaussianBlur(mask, (0, 0), 3)
np.save(os.path.join(V7, 'mascara_profund.npy'), u16(mask))
escriu_tif('MASCARA_profund', u16(mask), 'Mascara radial per als filtres profunds: 0 dins de 2.6 R, 1 a partir de 3.6 R. Pinta-la si vols. 2026-08-19')

res = {}
for nom, Dp, A, desc in (('RADIALS_profund', D_rad, A_RAD, 'RADIALS profund: Espenak multiescala (bandes angulars 0.4-2, 2-6, 6-18 graus) sobre L_d (Vixen HDR + Sony v2, flat mesurat, fons de Fourier), porta de soroll entre trens, mitjana zero per anell. Overlay ~50 %. 2026-08-19'),
                         ('MGN_profund', D_mgn, A_MGN, 'MGN profund: bandes isotropes 0.5-9 graus sobre L_d, porta de soroll, normalitzacio local amb pis, mitjana zero per anell. Overlay ~45 %. 2026-08-19'),
                         ('NRGF_profund', D_nrgf, A_NRGF, 'NRGF profund: (ln L_d - fons m<=2)/sigma anell, pis de soroll, mitjana zero per anell. Overlay ~12 %. 2026-08-19')):
    Dimg = lp.cap_a_imatge(Dp) * taper
    c_r = perfil_anell(Dimg, taper)
    Dimg = ((Dimg - c_r) * taper).astype(np.float32)         # mitjana zero per anell DINS del taper
    Dimg[disc] = 0.0
    capa = np.clip(0.5 + A * Dimg, 0, 1).astype(np.float32)
    rgb = np.repeat(u16(capa)[..., None], 3, axis=2)
    np.save(os.path.join(V7, nom + '.npy'), rgb)
    escriu_tif(nom, rgb, desc)
    jpg(os.path.join(V7, nom + '_x4.jpg'), cv2.resize(np.clip((capa - 0.5) * 6 + 0.5, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA))
    st = {}
    for ra, rb in ((2.0, 2.6), (3.0, 3.5), (3.5, 4.5), (4.5, 5.5), (5.5, 6.5), (6.5, 7.5), (7.5, 8.5), (8.5, 9.5)):
        m = (rR > ra) & (rR < rb) & vcE
        d = Dimg[m] * A
        st[f'{ra}-{rb}'] = dict(rms=float(np.sqrt(np.mean(d * d))), p99=float(np.percentile(np.abs(d), 99)), mitjana=float(np.mean(d)))
    res[nom] = st
    log(nom, ' '.join(f"{k}: rms {v['rms']:.4f} p99 {v['p99']:.4f} mitj {v['mitjana']:+.5f}" for k, v in st.items()))
    del Dimg, capa, rgb

# correlació entre els tres i amb el DETALL EXTERIOR v3 (sanitat: estructura real compartida)
try:
    det = np.load(os.path.join(SCR, 'halo', 'detall_exterior_COH_v3.npy'), mmap_mode='r')
    dv3 = np.asarray(det[::4, ::4, 0], np.float32) / 65535 - 0.5
    z4 = ((rR[::4, ::4] > 3.8) & (rR[::4, ::4] < 6.0) & vcE[::4, ::4])
    for nom in ('RADIALS_profund', 'MGN_profund', 'NRGF_profund'):
        a = np.load(os.path.join(V7, nom + '.npy'), mmap_mode='r')
        av = np.asarray(a[::4, ::4, 0], np.float32) / 65535 - 0.5
        res[nom]['corr_amb_DETALL_v3_3p8_6R'] = float(np.corrcoef(av[z4], dv3[z4])[0, 1])
        log(nom, 'correlació amb DETALL EXTERIOR v3 a 3,8–6 R☉:', round(res[nom]['corr_amb_DETALL_v3_3p8_6R'], 3))
except Exception as e:
    log('sense correlació amb v3:', e)
json.dump(dict(qa=qa, capes=res, A=dict(rad=A_RAD, mgn=A_MGN, nrgf=A_NRGF), R_FAR=R_FAR, R_MASK=R_MASK, TAPER_PX=TAPER_PX,
               RAD=dict(bandes=RAD_BANDES, w=RAD_W, tsig=RAD_TSIG, fsist=RAD_FSIST), MGN=dict(bandes=MGN_BANDES, g=MGN_G, tsig=MGN_TSIG, fsist=MGN_FSIST)),
          open(os.path.join(V7, 'filtres_profunds_v7.json'), 'w'), indent=1)
log('fi')
