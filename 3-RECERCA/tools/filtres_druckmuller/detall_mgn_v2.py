"""`corona_vixen_detall` v2: la mateixa recepta que Pere troba útil (log de la corona al 72 % +
normalització gaussiana multiescala —MGN— al 28 %), refeta perquè no tingui els artefactes que
va marcar el 18-08 al vespre, i AL SEU LLENÇ (7648×5353), amb els dos trens de 3,3 R☉ enfora.

Què tenia la v1 (`hdr_corona_vixen.py vis`, 17-08) i d'on venien els artefactes:
  - `norm = net / perfil_azimutal(net)`: el perfil radial és exacte fins al cercle inscrit (5,2 R☉)
    i extrapolat més enllà → colze → l'MGN el pinta com un ANELL a 5,2 R☉ i un altre a ~7,6 R☉ (on
    s'acaba el sector mesurat). ⇒ v2: fons de Fourier m ≤ 4 per columna en log-polars (mai un
    perfil extrapolat), com el `detall_logpolar` viu.
  - `realca` a σ = 6…64 px d'imatge, dividint per la σ LOCAL sense pis: amplifica ×30 tot el que és
    més fi que 6 px —la reixa del drizzle, la PRNU residual, i els fils radials reals del limbe—
    fins al mateix contrast: la «pinta» radial i la trama fina. ⇒ v2: bandes en GRAUS (escalen amb
    el radi) que s'apaguen per sota de 4 px d'imatge (PSF 2,7 px, drizzle 2 px), pis de soroll a
    la normalització (σ_local² + n²), i porta de significació per banda.
  - els arcs residuals de les fronteres de saturació (≤ 0,24 %): el fons de Fourier per columna
    absorbeix tot el que és constant a l'anell; el que queda són trossos d'arc.
  - Lluna a 0,10 com abans; component d'anell del detall = 0.

Sortides (a FD_OUT): corona_detall_v2_{28,40}.png (8 bits) i .tif (16 bits gris), 7648×5353,
alineats amb `Aplicant_Filtres.tif`; i les prèvies.
"""
import os, sys, json, math, time
import numpy as np
import cv2
import tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu as C
from polar_utils import LogPolar, smooth01

t0 = time.time()
SCR = C.SCR
OUTDIR = os.environ.get('FD_OUT', os.path.join(SCR, 'capes'))
os.makedirs(OUTDIR, exist_ok=True)
H, W = C.H_LLENC, C.W_LLENC
SX, SY = C.SOL_LLENC
R_SOL = C.R_SOL_PX
NA = int(os.environ.get('NA_POLAR', '8192'))
NR = int(os.environ.get('NR_POLAR', '3072'))
VARIANT = os.environ.get('VARIANT', 'suau')     # suau | fort
K_MGN = {'suau': 0.5, 'fort': 0.7}[VARIANT]     # el k de l'arctan (0,5 = `realca` «suau»; 0,7 = MGN del paper)
MESCLES = [0.28, 0.40]          # 0,28 = la v1; 0,40 més detall
SIG_MIN_IMG_PX = 3.0            # per sota, la banda s'apaga (PSF 2,7 px FWHM, drizzle 2 px)
SUFIX = '' if VARIANT == 'suau' else '_FORT'


def log(*a):
    print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)


# ------------------------------------------------------------------ dades
z = np.load(os.path.join(SCR, 'lum_llenc.npz'))
L_v, sig_v, valid_v = z['L_v'], z['sig_v'], z['valid_v']
L_s, sig_s, valid_s = z['L_s'], z['sig_s'], z['valid_s']
L_c, sig_c, valid_c, frac_s = z['L_c'], z['sig_c'], z['valid_c'], z['frac_s']
del z
geo = json.load(open(os.path.join(SCR, 'lum_llenc_geometria.json')))
r_ll, th_ll = C.malla_llenc()
LLUNA = (4034.7, 2736.7)
r_lluna = np.hypot(np.arange(W)[None, :] - LLUNA[0], np.arange(H)[:, None] - LLUNA[1])
disc = r_lluna < 452.5 + 1.5
valid_c &= ~disc; valid_v &= ~disc
valid_s &= (r_ll > 3.3)
log('dades')

# ------------------------------------------------------------------ 1. la part «log» (com la v1)
# cel: constant a r > 7,2 R☉ més un pla ajustat al residu (L − perfil) a r > 3,5, com etapa_vis
xs = (np.arange(W)[None, :] - SX) / R_SOL; ys = (np.arange(H)[:, None] - SY) / R_SOL
XX = np.broadcast_to(xs, (H, W)); YY = np.broadcast_to(ys, (H, W))
lluny = valid_c & (r_ll > 7.2)
cel_const = float(np.median(L_c[lluny])) if lluny.sum() > 1000 else float(np.median(L_c[valid_c & (r_ll > 6.0)]))
# perfil azimutal ràpid (mitjana per anell d'1 px) només per al pla del cel
ib = np.clip(r_ll * R_SOL, 0, 5000).astype(np.int32)
suma = np.bincount(ib[valid_c], weights=L_c[valid_c], minlength=5001)
cnt = np.bincount(ib[valid_c], minlength=5001)
perf = np.where(cnt > 50, suma / np.maximum(cnt, 1), np.nan)
idx = np.arange(5001); okp = np.isfinite(perf)
perf = np.interp(idx, idx[okp], perf[okp])
base_r = perf[ib]
fora = valid_c & (r_ll > 3.5) & (r_ll < 6.5)
A = np.c_[np.ones(fora.sum()), XX[fora], YY[fora]]
coef, *_ = np.linalg.lstsq(A, (L_c - base_r)[fora], rcond=None)
net = np.where(valid_c, L_c - cel_const - (coef[1] * XX + coef[2] * YY), 0.0).astype(np.float32)
lo = 1.5
hi = float(np.percentile(net[valid_c & (r_ll < 1.06)], 99.5))
gamma = np.clip((np.log10(np.maximum(net, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)), 0, 1) ** 0.9
gamma = np.where(valid_c, gamma, 0.0).astype(np.float32)
log(f'log: cel {cel_const:.1f} ADU/s, gradient ({coef[1]:+.1f},{coef[2]:+.1f}) per R☉, hi = {hi:.0f}')

# ------------------------------------------------------------------ 2. l'MGN en log-polars amb pis de soroll
LP = LogPolar(H, W, SX, SY, NA=NA, NR=NR)
rs_of = LP.r_of / R_SOL
log(f'log-polar {NA}×{NR}: radial {R_SOL*4/LP.K:.2f} px a 4 R☉, azimutal {2*math.pi*R_SOL*4/NA:.2f} px')

# soroll sintètic amb l'estadística de cada font (com filtre_corona_externa)
rng = np.random.default_rng(20260818)
zv = rng.standard_normal((H, W)).astype(np.float32)
zv = cv2.blur(zv, (2, 2), borderType=cv2.BORDER_REFLECT)
Msh = np.array([[1, 0, C.HDR_A_LLENC[0] % 1], [0, 1, C.HDR_A_LLENC[1] % 1]], np.float64)
zv = cv2.warpAffine(zv, Msh, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
zv /= float(zv[valid_v].std())
from scipy import ndimage as ndi
zs0 = rng.standard_normal((5320, 7968)).astype(np.float32)
S_, th_ = geo['sony_escala'], math.radians(geo['sony_gir_deg'])
CXs, CYs = geo['sony_sol_llenc']
c2, s2 = math.cos(th_), math.sin(th_)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
ux = (xx - CXs) / S_; uy = (yy - CYs) / S_
pxs = C.SONY_SOL_PLACA[0] + ux * c2 - uy * s2; pys = C.SONY_SOL_PLACA[1] + ux * s2 + uy * c2
zs = ndi.map_coordinates(zs0, [pys, pxs], order=1, mode='constant', cval=0.0).astype(np.float32)
del zs0, yy, xx, ux, uy, pxs, pys
zs /= float(zs[valid_s].std())
nc_img = np.where(valid_c, ((1 - frac_s) * sig_v * zv + frac_s * sig_s * zs) / np.maximum(L_c, 1.0), 0.0).astype(np.float32)
nv_img = np.where(valid_v, sig_v * zv / np.maximum(L_v, 1.0), 0.0).astype(np.float32)
del zv, zs

Rc, okc, mpc, _ = LP.residu_polar(L_c, valid_c)
Rv, okv, mpv, _ = LP.residu_polar(L_v, valid_v)
Nc = LP.cap_a_polar(nc_img) * okc
Nv = LP.cap_a_polar(nv_img) * okv
del nc_img, nv_img
log('residus polars')

# bandes en graus: a 2 R☉ (892 px) equivalen a 5,4 · 9,3 · 16 · 26 · 45 · 78 · 132 px, comparables als
# 6…64 px de la v1; al limbe són més fines (3–70 px), i a 4 R☉ més gruixudes (11–265 px)
BANDES_DEG = [0.22, 0.35, 0.60, 1.0, 1.7, 2.9, 5.0, 8.5, 14.0]
T_SIG = {'suau': [3.0, 2.2, 1.6, 1.4, 1.2, 1.1, 1.0, 1.0],
         'fort': [3.0, 1.5, 1.2, 1.1, 1.0, 1.0, 1.0, 1.0]}[VARIANT]
# el sistemàtic d'escala fina (reixa del drizzle, PRNU) s'aplica a totes les bandes al «suau» i només a
# la banda més fina al «fort» (deixa passar els fils reals del limbe, a canvi d'una mica de pinta)
F_SIST_TOTES = (VARIANT == 'suau')
# pes per banda dins la mitjana (els g_i de l'MGN, aquí per compensar la mitja potència que perden les
# fines respecte de la v1 en treure la pinta): FORT reforça 0,35–1,7°
G_J = {'suau': [1.0, 1.2, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0],
       'fort': [1.0, 1.7, 1.6, 1.3, 1.0, 1.0, 1.0, 1.0]}[VARIANT]
esc = [d * LP.px_deg for d in BANDES_DEG]
SONY_MIN_IMG_PX = 8.0
i4 = int(np.searchsorted(LP.r_of, 4.0 * R_SOL)); i1 = int(np.searchsorted(LP.r_of, 1.15 * R_SOL))
prev = {'v': LP.blur_n(Rv, okv, esc[0]), 'c': LP.blur_n(Rc, okc, esc[0])}
prevN = {'v': LP.blur_n(Nv, okv, esc[0]), 'c': LP.blur_n(Nc, okc, esc[0])}
det = np.zeros((NA, NR), np.float32)
nb = np.zeros((1, NR), np.float32)
print('   banda (°)    σimg 1,15/4 R☉    pes mitjà (v,c) 1,2–3 · 3,5–5 R☉')
for j, (d0, d1) in enumerate(zip(BANDES_DEG[:-1], BANDES_DEG[1:])):
    s1 = esc[j + 1]
    b = {}; n = {}; v = {}; w = {}
    for nom, Rx, okx, Nx, mp in (('v', Rv, okv, Nv, mpv), ('c', Rc, okc, Nc, mpc)):
        seg = LP.blur_n(Rx, okx, s1)
        b[nom] = prev[nom] - seg; prev[nom] = seg
        segN = LP.blur_n(Nx, okx, s1)
        bz = prevN[nom] - segN; prevN[nom] = segN
        k_r = np.sqrt(np.sum(bz.astype(np.float64) ** 2 * mp, axis=0) / np.maximum(mp.sum(axis=0), 1.0)).astype(np.float32)
        n[nom] = k_r[None, :]
        v[nom] = LP.blur_n(b[nom] * b[nom], okx, 2.0 * s1)      # potència LOCAL (MGN: σ_w local, finestra 2σ)
        w[nom] = np.clip(1.0 - (T_SIG[j] * n[nom]) ** 2 / np.maximum(v[nom], 1e-14), 0.0, 1.0).astype(np.float32)
    if j == 0:
        zc = (mpv > 0.5) & ((LP.r_of > 4.2 * R_SOL) & (LP.r_of < 5.2 * R_SOL))[None, :]
        rms_cel = float(np.sqrt(np.mean(b['v'][zc].astype(np.float64) ** 2)))
        F_SIST = max(1.0, rms_cel / max(float(np.median(np.broadcast_to(n['v'], b['v'].shape)[zc])), 1e-12))
        print(f'  sistemàtic d’escala fina (banda {d0}–{d1}° al cel de 4,2–5,2 R☉): ×{F_SIST:.2f} sobre el soroll')
    fs = F_SIST if (F_SIST_TOTES or j == 0) else 1.0
    for nom in ('v', 'c'):
        n[nom] = n[nom] * fs
        w[nom] = np.clip(1.0 - (T_SIG[j] * n[nom]) ** 2 / np.maximum(v[nom], 1e-14), 0.0, 1.0).astype(np.float32)
    sig_img = np.deg2rad(d0) * LP.r_of
    f_c = smooth01((sig_img - 5.0) / (SONY_MIN_IMG_PX - 5.0))[None, :]
    b_use = (1 - f_c) * b['v'] + f_c * b['c']
    w_use = (1 - f_c) * w['v'] + f_c * w['c']
    v_use = (1 - f_c) * v['v'] + f_c * v['c']
    n_use = (1 - f_c) * n['v'] + f_c * n['c']
    fina = smooth01((sig_img - 2.2) / 1.5)[None, :]      # 0 a 2,2 px (reixa del drizzle), 1 a 3,7 px (fils reals)
    # sostre en píxels d'imatge (com la v1, que treballava a 6–64 px): a 4 R☉ només fins a ~2–4°; sense
    # això les bandes de 3–8° igualades al camp llunyà (cel, PRNU) surten com a taques grosses
    fina = fina * (1.0 - smooth01((sig_img - 60.0) / 60.0))[None, :]
    # MGN amb pis: C = b / sqrt(σ_local² + n²); C' = arctan(k·C)
    Cj = b_use / np.sqrt(np.maximum(v_use + n_use ** 2, 1e-16))
    det += (G_J[j] * fina * w_use * np.arctan(K_MGN * Cj)).astype(np.float32)
    nb += fina
    def pw(nom, r0, r1):
        mp = {'v': mpv, 'c': mpc}[nom]
        zz = (mp > 0.5) & ((LP.r_of > r0 * R_SOL) & (LP.r_of < r1 * R_SOL))[None, :]
        return float(w[nom][zz].mean()) if zz.any() else np.nan
    print(f'  {d0:5.2f}–{d1:5.2f}   {sig_img[i1]:5.1f}/{sig_img[i4]:6.1f} px     {pw("v",1.2,3):.2f} {pw("c",1.2,3):.2f} · {pw("v",3.5,5):.2f} {pw("c",3.5,5):.2f}', flush=True)
det = det / np.maximum(nb, 1.0)                # mitjana de les bandes actives (MGN: 1/n Σ)
# (sense el factor 2/π: la v1 barrejava det·0,5 + 0,5 amb det ∈ (−π/2, π/2); mateixa amplitud aquí)
# component d'anell zero
mcol = (mpc > 0.5).astype(np.float32)
mitj = (det * mcol).sum(0) / np.maximum(mcol.sum(0), 1.0)
det = np.where(mcol > 0, det - mitj[None, :], det)
det_img = np.where(valid_c, LP.cap_a_imatge(det), 0.0).astype(np.float32)
# el detall només on hi ha la Vixen (la v1 tampoc en tenia més enllà), amb esvaïment de 250 px: fora de la
# seva caixa la combinada és Sony sola i la vora sortia com una ratlla en normalitzar
dvix = cv2.distanceTransform(valid_v.astype(np.uint8), cv2.DIST_L2, 5)
det_img *= smooth01(dvix / 250.0).astype(np.float32)
# i esvaïment radial de 4,8 a 6,0 R☉: més enllà el que s'iguala és cel i camp, i la vora de la caixa
# Vixen (a 5,0–5,1 R☉ a dalt i a baix) deixaria un rectangle
det_img *= (1.0 - smooth01((r_ll - 4.8) / 1.2)).astype(np.float32)
del prev, prevN, Rv, Rc, Nv, Nc
log(f'MGN v2: sd del detall a 1,2–3 R☉ {det_img[valid_c & (r_ll>1.2) & (r_ll<3)].std():.3f}, a 3,5–5 {det_img[valid_c & (r_ll>3.5) & (r_ll<5)].std():.3f}')

# ------------------------------------------------------------------ 3. mescla i sortides
def anell_test(D, nom):
    res = []
    for ra in np.arange(1.2, 6.0, 0.1):
        m = valid_c & (r_ll > ra) & (r_ll < ra + 0.1)
        if m.sum() > 2000:
            res.append(abs(float(D[m].mean())))
    print(f'   test d’anell {nom}: |mitjana per anell| màx {100*max(res):.3f} %')

anell_test(det_img, 'det')
disc_out = r_lluna < 452.5 + 1.5
for mescla in MESCLES:
    mix = np.clip((1 - mescla) * gamma + mescla * (0.5 + 0.5 * det_img), 0, 1)
    mix = cv2.GaussianBlur(mix, (0, 0), 0.9)          # l'antialiàsing de 0,9 px de la v1
    out = np.where(disc_out, 0.10, np.where(valid_c, mix, 0.0)).astype(np.float32)
    nom = f'corona_detall_v2_{int(mescla*100)}{SUFIX}'
    cv2.imwrite(os.path.join(OUTDIR, nom + '.png'), (out * 255 + 0.5).astype(np.uint8))
    tifffile.imwrite(os.path.join(OUTDIR, nom + '.tif'), (out * 65535 + 0.5).astype(np.uint16),
                     photometric='minisblack', compression='zlib', metadata=None, resolution=(300, 300),
                     description=f'corona_vixen_detall v2 (log {1-mescla:.2f} + MGN log-polar {mescla:.2f}); llenc 7648x5353, Sol ({SX:.2f},{SY:.2f}); dos trens')
    cv2.imwrite(os.path.join(OUTDIR, nom + '_x4.jpg'), (cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    log(f'→ {nom}.png / .tif')
# retalls de comprovació al voltant del disc (on Pere va marcar la pinta) i a 5,2 R☉ (on hi havia l'anell)
mix = np.clip(0.72 * gamma + 0.28 * (0.5 + 0.5 * det_img), 0, 1)
mix = np.where(disc_out, 0.10, mix)
cy, cx = int(SY), int(SX)
cv2.imwrite(os.path.join(OUTDIR, f'corona_detall_v2_28{SUFIX}_retall_disc.jpg'), (mix[cy - 600:cy + 600, cx - 600:cx + 600] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
r52 = int(5.2 * R_SOL)
cv2.imwrite(os.path.join(OUTDIR, f'corona_detall_v2_28{SUFIX}_retall_5R.jpg'), (mix[cy - 300:cy + 300, cx - r52 - 500:cx - r52 + 500] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
log('fet')
