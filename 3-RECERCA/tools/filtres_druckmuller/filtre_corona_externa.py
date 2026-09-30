"""Filtres «Druckmüller» per a la corona EXTERNA (2–6 R☉), com a capes per al Photoshop de Pere.

Entrada: lum_llenc.npz de prepara_lluminancia.py (Vixen, Sony i combinada, al llenç 7648×5353).
Tot es fa en coordenades LOG-POLARS centrades al Sol (files = angle, columnes = ln r), on una
gaussiana de σ fix en polars és una gaussiana que ESCALA amb el radi (l'esperit del nucli en
(Δr, arc) de l'ACHF, tesi §5.2, però amb bandes en GRAUS: la corona té estructura angular).

Per a cada font f ∈ {Vixen, Sony, combinada}:
    x_f  = ln L_f (cel inclòs), omplert per dins del limbe (inpaint_radial)
    F    = fons de Fourier m ≤ 4 per columna (mitjana azimutal amb 4 harmònics: el terme a_0..a_4
           del FNRGF; exacte on l'anell és sencer, extrapolat en ρ més enllà)
    R_f  = (x_f − F)·màscara                        contrast azimutal en log
    b_j  = Gn(R, σ_j) − Gn(R, σ_{j+1})              bandes DoG isòtropes en la imatge (graus)
    n_j(ρ) = rms per columna de la MATEIXA banda sobre una realització de soroll amb l'estadística
           exacta de la font (drizzle 2×2 + shift bilineal la Vixen; warp bilineal ×1,49 la Sony;
           la combinació ponderada per a la combinada), dividida per L (soroll en ln)
    w_j  = max(0, 1 − n_j²/v_j)                     porta de Wiener, v_j potència local de la banda
    D_add   = Σ g_j(ρ)·w_j·b_j                       amplitud CONSERVADA (jerarquia real; PASSALT)
    D_white = Σ g_j·w_j·b_j / sqrt(v_j + n_j²)       blanquejat (FNRGF/WOW/MGN: contrast igualat a
                                                     tots els radis, amb pis de soroll = n_j)
    coherència c_j = <b_v·b_s>/sqrt(<b_v²><b_s²>) local  (r > 3,6 R☉): el test de dos trens del
           2006 fet pes; variant «COHERENT» = D·smoothstep(c)
Cada banda es pren de la combinada si la seva σ en píxels d'imatge és ≥ 8 px (per sota, la Sony
no hi aporta res: PSF 11″ = 5 px al llenç), i de la Vixen sola si és fina (fos entre 5 i 8 px).
Sortides (16 bits, llenç 7648×5353, gris 50 % + D/A com el PASSALT viu, Linear Light):
    DRUCK_EXTERIOR_ADD_{SUAU,MITJA,FORT}.tif, DRUCK_EXTERIOR_WHITE_{...}.tif, *_COHERENT.tif,
    DRUCK_TOTCAMP_ADD_MITJA.tif, DRUCK_TOTCAMP_WHITE_MITJA.tif, mapa de coherència, NRGF de control,
    composició de colors Vixen/Sony (QA 2006), test d'anell.
"""
import os, sys, json, math, time
import numpy as np
import cv2
import tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu as C

t0 = time.time()
SCR = C.SCR
OUTDIR = os.environ.get('FD_OUT', os.path.join(SCR, 'capes'))
os.makedirs(OUTDIR, exist_ok=True)
H, W = C.H_LLENC, C.W_LLENC
SX, SY = C.SOL_LLENC
R_SOL = C.R_SOL_PX
NA = int(os.environ.get('NA_POLAR', '8192'))
NR = int(os.environ.get('NR_POLAR', '3072'))
R_MIN = 400.0
A_T = 0.9            # topall/escala de la capa: capa = 0,5 + 0,5·D/A_T (com corona_vixen_PASSALT)
NOMES = os.environ.get('NOMES', '')   # per depurar: 'add', 'white'


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
# el disc lunar: no és vàlid (la Lluna no és corona). Radi lunar ~452,5 px al llenç, centre a
# (4034,7, 2736,7) (research/80 §13). Fem servir un radi generós de 470 px des del centre lunar.
LLUNA = (4034.7, 2736.7)
r_lluna = np.hypot(np.arange(W)[None, :] - LLUNA[0], np.arange(H)[:, None] - LLUNA[1])
disc = r_lluna < 470.0
valid_v &= ~disc; valid_c &= ~disc
valid_s &= (r_ll > 3.3)
log('dades carregades')

# ------------------------------------------------------------------ log-polar (adaptat de hdr_corona_vixen.py)
r_max = math.hypot(max(SX, W - SX), max(SY, H - SY)) + 4.0
K = NR / math.log(r_max / R_MIN)
thp = (2 * math.pi * np.arange(NA, dtype=np.float64) / NA)[:, None]
r_of = R_MIN * np.exp(np.arange(NR, dtype=np.float64) / K)
map_x = (SX + r_of[None, :] * np.cos(thp)).astype(np.float32)
map_y = (SY + r_of[None, :] * np.sin(thp)).astype(np.float32)
yy = (np.arange(H, dtype=np.float32) - SY)[:, None]
xx = (np.arange(W, dtype=np.float32) - SX)[None, :]
rr = np.hypot(xx, yy)
tt = np.arctan2(yy, xx); tt = np.where(tt < 0, tt + 2 * math.pi, tt)
imap_x = (K * np.log(np.maximum(rr, R_MIN) / R_MIN)).astype(np.float32)
imap_y = (tt / (2 * math.pi) * NA).astype(np.float32)
del yy, xx, rr, tt
px_deg = NA / 360.0
iso = 2 * math.pi * K / NA          # σ_ρ = σ_θ·iso perquè el nucli sigui isòtrop en la imatge
rs_of = r_of / R_SOL
log(f'log-polar {NA}×{NR}: r {R_MIN:.0f}–{r_max:.0f} px, K = {K:.1f}; mostreig radial '
    f'{r_of[0]/K:.2f} px al limbe, {R_SOL*4/K:.2f} px a 4 R☉; azimutal {2*math.pi*R_SOL*4/NA:.2f} px a 4 R☉')


def cap_a_polar(a):
    return cv2.remap(np.ascontiguousarray(a, np.float32), map_x, map_y, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def cap_a_imatge(Dp):
    Dp2 = np.concatenate([Dp[-2:], Dp, Dp[:2]], axis=0)
    return cv2.remap(np.ascontiguousarray(Dp2, np.float32), imap_x, imap_y + 2.0, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def desenfoca_polar(x, s_rho, s_ang):
    a = np.ascontiguousarray(x, np.float32)
    pad = int(math.ceil(3 * s_ang)) + 1
    ap = np.concatenate([a[-pad:], a, a[:pad]], axis=0)
    s_min = min(s_rho, s_ang)

    def k(s):
        return int(2 * math.ceil(3 * max(s, 0.5)) + 1)
    if s_min <= 6.0:
        out = cv2.GaussianBlur(ap, (k(s_rho), k(s_ang)), sigmaX=s_rho, sigmaY=s_ang, borderType=cv2.BORDER_REPLICATE)
    else:
        f = max(1, int(s_min / 4.0))
        h, w = ap.shape
        pt = cv2.resize(ap, (max(8, w // f), max(8, h // f)), interpolation=cv2.INTER_AREA)
        sr, sa = s_rho / f, s_ang / f
        pt = cv2.GaussianBlur(pt, (k(sr), k(sa)), sigmaX=sr, sigmaY=sa, borderType=cv2.BORDER_REPLICATE)
        out = cv2.resize(pt, (w, h), interpolation=cv2.INTER_LINEAR)
    return out[pad:pad + a.shape[0]]


def inpaint_radial(xp, mp, n_pend=30):
    na, nr = xp.shape
    ok = mp > 0.5
    te = ok.any(axis=1)
    c0 = np.where(te, np.argmax(ok, axis=1), 0)
    c1 = np.where(te, nr - 1 - np.argmax(ok[:, ::-1], axis=1), nr - 1)
    fila = np.arange(na)
    col = np.arange(nr)[None, :]
    a = xp[fila, c0]
    b = xp[fila, np.minimum(c0 + n_pend, c1)]
    pend_in = np.where(c1 - c0 > n_pend, (b - a) / n_pend, 0.0)
    dins = col < c0[:, None]
    return np.where(dins, a[:, None] + pend_in[:, None] * (col - c0[:, None]), xp).astype(np.float32)


def fons_fourier(xp, mp, m_max=4, ridge=5.0):
    """Fons per columna: 1, cos kθ, sin kθ (k ≤ m_max), robust; exacte mentre l'anell és sencer i
    extrapolat en ρ més enllà (còpia de hdr_corona_vixen.fons_fourier)."""
    from scipy.ndimage import gaussian_filter1d
    na, nr = xp.shape
    th = 2 * math.pi * np.arange(na) / na
    cols = [np.ones(na)]
    for k_ in range(1, m_max + 1):
        cols += [np.cos(k_ * th), np.sin(k_ * th)]
    A = np.stack(cols, axis=1).astype(np.float32)
    p_ = A.shape[1]
    M = mp.astype(np.float32)
    coef = None
    for passada in range(2):
        S = np.einsum('ia,ib,ic->cab', A, A, M, optimize=True).astype(np.float64)
        T = np.einsum('ia,ic->ca', A, (M * xp).astype(np.float32), optimize=True).astype(np.float64)
        S[:, np.arange(1, p_), np.arange(1, p_)] += ridge
        S[:, 0, 0] += 1e-6
        coef = np.linalg.solve(S, T[..., None])[..., 0]
        if passada == 0:
            F0 = (A @ coef.T.astype(np.float32))
            res = np.where(mp > 0.5, xp - F0, np.nan)
            med = np.nanmedian(res, axis=0)
            mad = 1.4826 * np.nanmedian(np.abs(res - med[None, :]), axis=0) + 1e-6
            M = M * (np.abs(np.nan_to_num(res)) < 4.0 * mad[None, :])
            del F0, res
    frac = mp.mean(axis=0)
    plenes = np.where(frac >= 0.999)[0]
    c_ple = int(plenes.max()) if plenes.size else nr - 1
    coef = gaussian_filter1d(coef, 3.0, axis=0, mode='nearest')
    xt = np.arange(nr, dtype=np.float64)
    x_out = xt - c_ple
    ext = coef.copy()
    amb = np.where(frac > 0.05)[0]
    c_fi = int(amb.max()) if amb.size else nr - 1
    n_p = 20
    for j in range(p_):
        v0 = float(coef[c_ple, j])
        s0 = float(coef[c_ple, j] - coef[max(c_ple - n_p, 0), j]) / n_p
        if j <= 4 and c_fi > c_ple + 60:
            xo = np.arange(c_ple + 1, c_fi + 1, dtype=np.float64) - c_ple
            wo = np.sqrt(np.clip(frac[c_ple + 1:c_fi + 1], 0, 1))
            res = coef[c_ple + 1:c_fi + 1, j] - (v0 + s0 * xo)
            A2 = np.stack([xo ** 2, xo ** 3], axis=1) * wo[:, None]
            ab, *_ = np.linalg.lstsq(A2, res * wo, rcond=None)
            fora = v0 + s0 * x_out + ab[0] * x_out ** 2 + ab[1] * x_out ** 3
        else:
            fora = v0 + s0 * 150.0 * (1.0 - np.exp(-np.clip(x_out, 0, None) / 150.0))
        ext[:, j] = np.where(x_out > 0, fora, coef[:, j])
    coef = ext
    return (A @ coef.T.astype(np.float32)).astype(np.float32), c_ple


def residu_polar(L, valid):
    """ln L en polars, omplert per dins, menys el fons de Fourier. Retorna R, ok (màscara per al
    fons i les gaussianes: l'ompliment interior compta), mp0 (vàlids reals)."""
    mp0 = cap_a_polar(valid.astype(np.float32))
    xp = cap_a_polar(np.where(valid, np.log(np.maximum(L, 1.0)), 0.0)) / np.maximum(mp0, 1e-3)
    mp0 = (mp0 > 0.5).astype(np.float32)
    xp = inpaint_radial(xp, mp0)
    ok = mp0.copy()
    c0 = np.argmax(mp0 > 0.5, axis=1)
    ok[np.arange(NR)[None, :] < c0[:, None]] = 1.0
    F, c_ple = fons_fourier(xp, ok)
    R = ((xp - F) * ok).astype(np.float32)
    return R, ok, mp0, c_ple


# ------------------------------------------------------------------ soroll sintètic amb l'estadística de cada font
rng = np.random.default_rng(20260818)
# Vixen: blanc → caixa 2×2 (drizzle) → shift bilineal (0,35, 0,90) ; unitat = σ_v per píxel abans de la caixa
zv = rng.standard_normal((H, W)).astype(np.float32)
zv = cv2.blur(zv, (2, 2), borderType=cv2.BORDER_REFLECT)
Msh = np.array([[1, 0, C.HDR_A_LLENC[0] % 1], [0, 1, C.HDR_A_LLENC[1] % 1]], np.float64)
zv = cv2.warpAffine(zv, Msh, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
zv = zv / float(zv[valid_v].std())   # ⚠️ normalitzat a dispersió 1 per píxel DESPRÉS de la cadena: sig_v ja és empíric per píxel
# Sony: blanc a la reixa Sony (5320×7968) → warp similitud (bilineal, ×1,4886)
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
zs = zs / float(zs[valid_s].std())   # ídem: sig_s és empíric per píxel del llenç (ja ×escala)
# soroll en unitats de ln L per a cada font
wv = np.where(valid_v, 1.0 / np.maximum(sig_v, 1e-3) ** 2, 0.0)
ws = np.where(valid_s, 1.0 / np.maximum(sig_s, 1e-3) ** 2, 0.0) * np.where(valid_c, frac_s > 0, 0)
nv_img = np.where(valid_v, sig_v * zv / np.maximum(L_v, 1.0), 0.0).astype(np.float32)
ns_img = np.where(valid_s, sig_s * zs / np.maximum(L_s, 1.0), 0.0).astype(np.float32)
# combinada: mateixos pesos que prepara_lluminancia (frac_s = ws/(wv+ws))
nc_img = np.where(valid_c, ((1 - frac_s) * sig_v * zv + frac_s * sig_s * zs) / np.maximum(L_c, 1.0), 0.0).astype(np.float32)
del zv, zs, wv, ws
log('soroll sintètic preparat')

# ------------------------------------------------------------------ residus en polars
Rv, okv, mpv, c_ple_v = residu_polar(L_v, valid_v)
Rs, oks, mps, c_ple_s = residu_polar(L_s, valid_s)
Rc, okc, mpc, c_ple_c = residu_polar(L_c, valid_c)
Nv = cap_a_polar(nv_img) * okv; Ns = cap_a_polar(ns_img) * oks; Nc = cap_a_polar(nc_img) * okc
del nv_img, ns_img, nc_img
log(f'residus polars fets; anell sencer fins a {rs_of[c_ple_v]:.2f} R☉ (Vixen), {rs_of[c_ple_c]:.2f} (comb.)')

# ------------------------------------------------------------------ bandes
BANDES_DEG = [0.10, 0.17, 0.27, 0.44, 0.71, 1.16, 1.86, 3.0, 4.9, 7.9, 12.8, 20.8, 34.0]
esc = [d * px_deg for d in BANDES_DEG]
SIG_MIN_IMG_PX = 1.6
SONY_MIN_IMG_PX = 8.0     # per sota d'això, banda només Vixen (PSF Sony 11″ = 5 px)


def blur(a, s_ang):
    return desenfoca_polar(a, s_ang * iso, s_ang)


# llindar de significació (múltiple del soroll de la banda) per obrir la porta, per banda:
#          0,10 0,17 0,27 0,44 0,71 1,16 1,86 3,0  4,9  7,9  12,8 20,8
T_SIG = [3.0, 2.5, 2.2, 1.9, 1.6, 1.4, 1.25, 1.15, 1.1, 1.05, 1.0, 1.0]


def blur_n(a, ok, s_ang):
    return blur(a, s_ang) / np.maximum(blur(ok, s_ang), 1e-3)


# guanys per banda: tres jocs. Índex j = banda entre BANDES_DEG[j] i [j+1].
#            0,10 0,17 0,27 0,44 0,71 1,16 1,86 3,0  4,9  7,9  12,8 20,8  (° inici)
G_EXT = {   # capa EXTERIOR: el que hi ha a 2–6 R☉ són raigs de 0,5–2° i serpentines de 3–20°
    'SUAU':  [0.0, 0.0, 0.8, 1.6, 2.4, 3.0, 3.0, 2.8, 2.4, 1.8, 1.0, 0.5],
    'MITJA': [0.0, 0.5, 1.5, 3.0, 4.5, 5.0, 5.0, 4.5, 3.8, 2.8, 1.6, 0.8],
    'FORT':  [0.0, 1.0, 3.0, 5.0, 7.0, 8.0, 8.0, 7.0, 5.5, 4.0, 2.4, 1.2],
}
G_TOT = {   # tot el camp: el joc viu de la FOTO (research/76), amb un pèl més a les bandes amples
    'MITJA': [0.0, 2.0, 4.0, 6.0, 6.0, 5.5, 4.5, 3.5, 2.5, 1.6, 0.6, 0.0],
}
G_WHITE = {  # blanquejat (FNRGF: normalització per ANELL, no local): els raigs de 0,5–5° manen; les
    # bandes de > 8° són taques de cel/camp i, igualades, embruten: se'ls treu pes
    'SUAU':  [0.0, 0.0, 0.3, 0.6, 0.8, 1.0, 1.0, 1.0, 0.7, 0.4, 0.15, 0.0],
    'MITJA': [0.0, 0.2, 0.5, 0.8, 1.0, 1.0, 1.0, 1.0, 0.7, 0.4, 0.15, 0.0],
    'FORT':  [0.0, 0.4, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0, 0.8, 0.5, 0.2, 0.0],
}


TH_POLAR = (2 * math.pi * np.arange(NA) / NA).astype(np.float32)
COS1, SIN1, COS2, SIN2 = np.cos(TH_POLAR)[:, None], np.sin(TH_POLAR)[:, None], np.cos(2 * TH_POLAR)[:, None], np.sin(2 * TH_POLAR)[:, None]


def variancia_anell(b, mp, att=(0.7, 0.4)):
    """Potència de la banda per ANELL (columna de log-radi), amb dos harmònics azimutals atenuats
    (com els C_k del FNRGF): mitjana NO robusta de b² sobre les files vàlides (els raigs són el senyal,
    no atípics), suavitzada 5 columnes en ρ; pis a 0,3× la mitjana de l'anell."""
    from scipy.ndimage import gaussian_filter1d
    okb = (mp > 0.5).astype(np.float32)
    b2 = np.where(okb > 0, b * b, 0.0).astype(np.float32)
    nrow = np.maximum(okb.sum(0), 1.0)
    c0 = b2.sum(0) / nrow
    a1 = 2 * (b2 * COS1).sum(0) / nrow; b1 = 2 * (b2 * SIN1).sum(0) / nrow
    a2 = 2 * (b2 * COS2).sum(0) / nrow; b2_ = 2 * (b2 * SIN2).sum(0) / nrow
    for arr in (c0, a1, b1, a2, b2_):
        arr[:] = gaussian_filter1d(arr, 5.0, mode='nearest')
    vr = (c0[None, :] + att[0] * (a1[None, :] * COS1 + b1[None, :] * SIN1)
          + att[1] * (a2[None, :] * COS2 + b2_[None, :] * SIN2))
    return np.maximum(vr, 0.3 * c0[None, :]).astype(np.float32)


def smooth01(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


# rampa radial de la capa exterior: 0 fins a 1,8 R☉, 1 a partir de 2,8; i sense res més enllà de 6,5
ramp_ext = smooth01((rs_of - 1.8) / 1.0) * (1 - smooth01((rs_of - 6.5) / 1.0))
# el blanquejat iguala el contrast per anell: més enllà de ~5 R☉ el que hi ha és cel i camp (no
# corona) i igualar-ho l'ompliria de taques; s'esvaeix de 5,0 a 6,0 R☉
ramp_white = smooth01((rs_of - 1.8) / 1.0) * (1 - smooth01((rs_of - 4.6) / 1.4))
ramp_tot = np.ones_like(rs_of) * (1 - smooth01((rs_of - 6.5) / 1.0))
# γ < 1 de Corona (2006): «outer corona in higher contrast — usual». Multiplicador de guany creixent
# amb r a la capa exterior: ×1 a 2 R☉ → ×2 a 4 R☉ → ×2,5 a 5,5 (i la porta de soroll decideix on cal)
gamma_r = np.clip(1.0 + 0.5 * (rs_of - 2.0), 1.0, 2.5)

dist_vora = {}
for nom, ok in (('v', okv), ('s', oks), ('c', okc)):
    dist_vora[nom] = cv2.distanceTransform((ok > 0.5).astype(np.uint8), cv2.DIST_L2, 5)

i_ref = int(np.searchsorted(r_of, 4.0 * R_SOL))
i2 = int(np.searchsorted(r_of, 2.0 * R_SOL))
i5 = int(np.searchsorted(r_of, 5.0 * R_SOL))
zona_cel = (mpc > 0.5) & ((r_of > 6.2 * R_SOL) & (r_of < 7.5 * R_SOL))[None, :]

# acumuladors
acc = {}
for nom in ('EXT_ADD_SUAU', 'EXT_ADD_MITJA', 'EXT_ADD_FORT', 'EXT_WHITE_SUAU', 'EXT_WHITE_MITJA', 'EXT_WHITE_FORT',
            'TOT_ADD_MITJA', 'TOT_WHITE_MITJA', 'EXT_ADD_MITJA_COH', 'EXT_WHITE_MITJA_COH',
            'V_ADD_MITJA', 'S_ADD_MITJA'):
    acc[nom] = np.zeros((NA, NR), np.float32)
coh_acc = np.zeros((NA, NR), np.float32); coh_n = np.zeros((NA, NR), np.float32)

prev = {'v': blur_n(Rv, okv, esc[0]), 's': blur_n(Rs, oks, esc[0]), 'c': blur_n(Rc, okc, esc[0])}
prevN = {'v': blur_n(Nv, okv, esc[0]), 's': blur_n(Ns, oks, esc[0]), 'c': blur_n(Nc, okc, esc[0])}
taula = []
print('   banda (°)     σimg@2/4 R☉  |  S/N cel(v,s,c)  pes mitjà 3.5-5R☉ (v,s,c)  coh mediana 3.6-5')
for j, (d0, d1) in enumerate(zip(BANDES_DEG[:-1], BANDES_DEG[1:])):
    s1 = esc[j + 1]
    b = {}; n = {}; v = {}; w = {}
    for nom, Rx, okx, Nx in (('v', Rv, okv, Nv), ('s', Rs, oks, Ns), ('c', Rc, okc, Nc)):
        seg = blur_n(Rx, okx, s1)
        b[nom] = prev[nom] - seg
        prev[nom] = seg
        segN = blur_n(Nx, okx, s1)
        bz = prevN[nom] - segN
        prevN[nom] = segN
        mp = {'v': mpv, 's': mps, 'c': mpc}[nom]
        k_r = np.sqrt(np.sum(bz.astype(np.float64) ** 2 * mp, axis=0) / np.maximum(mp.sum(axis=0), 1.0)).astype(np.float32)
        n[nom] = k_r[None, :] * np.ones((NA, 1), np.float32)     # soroll de la banda per columna
        v[nom] = blur_n(b[nom] * b[nom], okx, 4.0 * s1)
        # porta de Wiener amb llindar de significació per banda (a l'estil dels n_s = {5,3,1,…} del
        # WOW): les bandes fines han de superar el soroll amb més marge, perquè amb w = 1 − n²/v
        # a S/N ~ 1 la porta queda mig oberta i el soroll surt en grumolls
        w[nom] = np.clip(1.0 - (T_SIG[j] * n[nom]) ** 2 / np.maximum(v[nom], 1e-14), 0.0, 1.0).astype(np.float32)
        # finestra a la vora de la màscara (2,5 σ), com a la FOTO viva
        wv_ = np.clip(dist_vora[nom] / (2.5 * s1), 0.0, 1.0)
        w[nom] *= (wv_ * wv_ * (3.0 - 2.0 * wv_)).astype(np.float32)
    sig_img = np.deg2rad(d0) * r_of                     # σ interior de la banda en px d'imatge, per columna
    # fos Vixen-sola / combinada segons la σ d'imatge (la Sony no aporta res per sota de ~5–8 px)
    f_c = smooth01((sig_img - 5.0) / (SONY_MIN_IMG_PX - 5.0))[None, :]
    # per a la banda: b_use = fos, w_use = fos, n_use = fos
    b_use = (1 - f_c) * b['v'] + f_c * b['c']
    w_use = (1 - f_c) * w['v'] + f_c * w['c']
    v_use = (1 - f_c) * v['v'] + f_c * v['c']
    n_use = (1 - f_c) * n['v'] + f_c * n['c']
    fina = np.clip(sig_img / SIG_MIN_IMG_PX - 1.0, 0.0, 1.0)[None, :]      # apaga per sota del límit òptic
    # blanquejat a l'estil FNRGF: la σ de normalització és la de l'ANELL (potència de la banda per
    # columna, amb dos harmònics azimutals com els C_k del FNRGF), no la local: dins d'un mateix
    # radi la jerarquia entre un raig fort i una taca feble es conserva; entre radis s'iguala
    vr = variancia_anell(b_use, mpc)
    den_w = np.sqrt(np.maximum(vr + n_use ** 2, 1e-16)).astype(np.float32)
    # coherència Vixen–Sony (només on hi ha les dues i la banda no és massa fina per a la Sony)
    both = ((mpv > 0.5) & (mps > 0.5)).astype(np.float32)
    cv_ = blur(b['v'] * b['s'] * both, 4.0 * s1)
    cvv = blur(b['v'] * b['v'] * both, 4.0 * s1); css = blur(b['s'] * b['s'] * both, 4.0 * s1)
    coh = np.where(both > 0, cv_ / np.sqrt(np.maximum(cvv * css, 1e-20)), 0.0).astype(np.float32)
    coh_w = smooth01((coh - 0.05) / 0.5)          # 0 a c ≤ 0,05 → 1 a c ≥ 0,55
    zona_coh = ((mpv > 0.5) & (mps > 0.5) & (r_of > 3.6 * R_SOL)[None, :] & (r_of < 6.5 * R_SOL)[None, :])
    if sig_img[i_ref] >= 5.0:
        coh_acc += coh * zona_coh; coh_n += zona_coh
    # acumula
    for nivell in ('SUAU', 'MITJA', 'FORT'):
        gA = (G_EXT[nivell][j] * fina * ramp_ext[None, :] * gamma_r[None, :]).astype(np.float32)
        acc[f'EXT_ADD_{nivell}'] += gA * w_use * b_use
        gW = (G_WHITE[nivell][j] * fina * ramp_white[None, :]).astype(np.float32)
        acc[f'EXT_WHITE_{nivell}'] += gW * w_use * b_use / den_w
    acc['TOT_ADD_MITJA'] += (G_TOT['MITJA'][j] * fina * ramp_tot[None, :]).astype(np.float32) * w_use * b_use
    acc['TOT_WHITE_MITJA'] += (G_WHITE['MITJA'][j] * fina * (1 - smooth01((rs_of - 4.6) / 1.4))[None, :]).astype(np.float32) * w_use * b_use / den_w
    # coherent: la mateixa MITJA però multiplicada per la porta de coherència on hi ha les dues fonts
    # la porta de coherència s'aplica amb la màscara «hi ha les dues fonts» SUAVITZADA (3σ): la vora
    # de saturació de la Sony és irregular i la caixa Vixen és recta, i un graó de porta es veuria
    bothS = blur(both, 3.0 * s1) * smooth01((rs_of - 3.6) / 0.5)[None, :]     # i no abans de 3,6–4,1 R☉ (vora de saturació Sony)
    gate = (1.0 - bothS * (1.0 - coh_w)).astype(np.float32) if sig_img[i_ref] >= 5.0 else np.ones_like(coh_w)
    gA = (G_EXT['MITJA'][j] * fina * ramp_ext[None, :] * gamma_r[None, :]).astype(np.float32)
    acc['EXT_ADD_MITJA_COH'] += gA * w_use * b_use * gate
    gW = (G_WHITE['MITJA'][j] * fina * ramp_white[None, :]).astype(np.float32)
    acc['EXT_WHITE_MITJA_COH'] += gW * w_use * b_use / den_w * gate
    # per al test de colors: Vixen sola i Sony sola (ADD MITJA, sense fos)
    acc['V_ADD_MITJA'] += gA * w['v'] * b['v']
    acc['S_ADD_MITJA'] += gA * w['s'] * b['s']
    # informe
    z35 = ((r_of > 3.5 * R_SOL) & (r_of < 5.0 * R_SOL))[None, :]
    def sn(nom):
        mp = {'v': mpv, 's': mps, 'c': mpc}[nom]
        zz = (mp > 0.5) & zona_cel
        rms = float(np.sqrt(np.mean(b[nom][zz].astype(np.float64) ** 2))) if zz.any() else np.nan
        return rms / max(float(np.median(n[nom][zz])) if zz.any() else 1e-9, 1e-12)
    def pw(nom):
        mp = {'v': mpv, 's': mps, 'c': mpc}[nom]
        zz = (mp > 0.5) & z35
        return float(w[nom][zz].mean()) if zz.any() else np.nan
    cohm = float(np.median(coh[zona_coh])) if zona_coh.any() else np.nan
    fila = (d0, d1, sig_img[i2], sig_img[i_ref], sn('v'), sn('s'), sn('c'), pw('v'), pw('s'), pw('c'), cohm)
    taula.append(fila)
    print(f'  {d0:5.2f}–{d1:5.2f}   {sig_img[i2]:5.1f}/{sig_img[i_ref]:5.1f} px  |  {sn("v"):5.1f} {sn("s"):5.1f} {sn("c"):5.1f}'
          f'   {pw("v"):5.2f} {pw("s"):5.2f} {pw("c"):5.2f}      {cohm:5.2f}', flush=True)
del prev, prevN, Rv, Rs, Rc, Nv, Ns, Nc
coh_map = np.where(coh_n > 0, coh_acc / np.maximum(coh_n, 1), 0.0)
log('bandes acumulades')

# ------------------------------------------------------------------ sortides
ICC = None
try:
    with tifffile.TiffFile(os.path.join(C.HDR_DIR, 'corona_vixen_PASSALT_FORT_llencPere.tif')) as t:
        ICC = t.pages[0].tags[34675].value
except Exception as e:
    print('sense ICC:', e)


def escriu_capa(nom, D_img, A=A_T, descripcio='', amplia=3.0):
    capa = np.clip(0.5 + 0.5 * D_img / A, 0, 1)
    rgb = np.repeat((capa * 65535 + 0.5).astype(np.uint16)[..., None], 3, axis=2)
    extra = [(34675, 7, len(ICC), ICC, False)] if ICC else []
    tifffile.imwrite(os.path.join(OUTDIR, nom + '.tif'), rgb, photometric='rgb', compression='zlib',
                     metadata=None, resolution=(300, 300), description=descripcio, extratags=extra)
    prev = cv2.resize(np.clip((capa - 0.5) * amplia + 0.5, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUTDIR, nom + f'_previa_x{amplia:.0f}.jpg'), (prev * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    log(f'→ {nom}.tif   (rang D {float(D_img.min()):+.3f}…{float(D_img.max()):+.3f}, sd {float(D_img[valid_c].std()):.4f})')


def anell_test(D_img, valid, nom):
    """Mitjana de D per anell (0,1 R☉) i sector (12): la mitjana per anell ha de ser ~0 (≤ 0,15 %)."""
    res = []
    for ra in np.arange(1.2, 6.0, 0.1):
        m = valid & (r_ll > ra) & (r_ll < ra + 0.1)
        if m.sum() > 2000:
            res.append((ra, float(D_img[m].mean()), float(np.abs([D_img[m & (th_ll >= a0) & (th_ll < a0 + math.pi/6)].mean()
                        for a0 in np.arange(-math.pi, math.pi, math.pi/6) if (m & (th_ll >= a0) & (th_ll < a0 + math.pi/6)).sum() > 500]).max())))
    res = np.array(res)
    print(f'   test d’anell {nom}: |mitjana per anell| màx {100*np.abs(res[:,1]).max():.3f} %, per sector màx {100*res[:,2].max():.3f} % '
          f'(anells {res[0,0]:.1f}–{res[-1,0]:.1f} R☉)')
    return res


resum = {}
# normalització del blanquejat: D_white és una suma de bandes en unitats de σ local; es divideix per
# sqrt(Σ g_j²) (soroll unitari a l'estructura de totes les escales) i s'escala a 0,35 per σ
def norm_white(nivell, joc):
    g = np.array(joc[nivell], np.float64)
    return 0.18 / math.sqrt(float((g ** 2).sum()))
NW = {'EXT_WHITE_SUAU': norm_white('SUAU', G_WHITE), 'EXT_WHITE_MITJA': norm_white('MITJA', G_WHITE),
      'EXT_WHITE_FORT': norm_white('FORT', G_WHITE), 'TOT_WHITE_MITJA': norm_white('MITJA', G_WHITE),
      'EXT_WHITE_MITJA_COH': norm_white('MITJA', G_WHITE)}
for nom, Dp in acc.items():
    if NOMES and NOMES.upper() not in nom:
        continue
    if nom.startswith(('V_', 'S_')):
        continue
    if 'WHITE' in nom:
        Dp = Dp * NW[nom]
    # component d'anell = 0: es resta la mitjana per columna (radi) sobre les files vàlides
    mcol = ((Dp != 0) & (mpc > 0.5)).astype(np.float32)
    mitj = (Dp * mcol).sum(0) / np.maximum(mcol.sum(0), 1.0)
    Dp = np.where(mcol > 0, Dp - mitj[None, :], Dp)
    Dp2 = (A_T * np.tanh(Dp / A_T)).astype(np.float32)
    D_img = np.where(valid_c, cap_a_imatge(Dp2), 0.0).astype(np.float32)
    escriu_capa('DRUCK_' + nom.replace('EXT_', 'EXTERIOR_').replace('TOT_', 'TOTCAMP_'), D_img,
                descripcio=f'Filtre Druckmuller log-polar {nom}; llenc 7648x5353, Sol ({SX:.2f},{SY:.2f}); gris 50% + D/{A_T}; Linear Light',
                amplia=1.0 if 'WHITE' in nom else 3.0)
    resum[nom] = anell_test(D_img, valid_c & (r_ll > 1.2), nom)
    np.save(os.path.join(OUTDIR, f'D_{nom}.npy'), D_img)

# mapa de coherència Vixen–Sony (diagnòstic i màscara possible)
coh_img = np.where(valid_c, cap_a_imatge(coh_map.astype(np.float32)), 0.0)
cv2.imwrite(os.path.join(OUTDIR, 'coherencia_vixen_sony_x4.png'),
            (np.clip(cv2.resize(coh_img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8))
tifffile.imwrite(os.path.join(OUTDIR, 'MASCARA_coherencia_vixen_sony.tif'), (np.clip(coh_img, 0, 1) * 65535 + 0.5).astype(np.uint16),
                 photometric='minisblack', compression='zlib', metadata=None, resolution=(300, 300))
log('→ MASCARA_coherencia_vixen_sony.tif')

# composició de colors Vixen (taronja) / Sony (blau): gris = coincideixen (Druckmüller 2006, fig. 5)
Dv = np.where(valid_c, cap_a_imatge((A_T * np.tanh(acc['V_ADD_MITJA'] / A_T)).astype(np.float32)), 0.0)
Ds = np.where(valid_c, cap_a_imatge((A_T * np.tanh(acc['S_ADD_MITJA'] / A_T)).astype(np.float32)), 0.0)
sel = valid_v & valid_s & (r_ll > 3.4)
esc_c = 3.0 * float(np.std(Dv[sel])) if sel.any() else 0.1
rgb = np.zeros((H, W, 3), np.float32)
rgb[..., 0] = 0.5 + 0.5 * Dv / esc_c        # vermell/taronja: Vixen
rgb[..., 1] = 0.5 + 0.5 * (0.5 * Dv + 0.5 * Ds) / esc_c
rgb[..., 2] = 0.5 + 0.5 * Ds / esc_c        # blau: Sony
rgb = np.where(sel[..., None], rgb, 0.5)
cv2.imwrite(os.path.join(OUTDIR, 'QA_colors_vixen_taronja_sony_blau_x3.jpg'),
            (np.clip(cv2.resize(rgb, (W // 3, H // 3), interpolation=cv2.INTER_AREA)[..., ::-1], 0, 1) * 255).astype(np.uint8),
            [cv2.IMWRITE_JPEG_QUALITY, 90])
corr_ext = float(np.corrcoef(Dv[sel], Ds[sel])[0, 1]) if sel.any() else np.nan
log(f'→ QA colors; correlació D_vixen vs D_sony a r > 3,4: {corr_ext:.3f}')

# NRGF clàssic de control sobre L_c (anells de 2 px, mitjana i σ azimutals) — imatge gris
Lp = cap_a_polar(np.where(valid_c, L_c, 0.0)); Mp = cap_a_polar(valid_c.astype(np.float32)) > 0.5
mu = np.where(Mp.sum(0) > 0, (Lp * Mp).sum(0) / np.maximum(Mp.sum(0), 1), 0.0)
sd = np.sqrt(np.where(Mp.sum(0) > 1, ((Lp - mu[None, :]) ** 2 * Mp).sum(0) / np.maximum(Mp.sum(0) - 1, 1), 1.0))
from scipy.ndimage import gaussian_filter1d
mu = gaussian_filter1d(mu, 3.0); sd = gaussian_filter1d(sd, 3.0)
nrgf = np.where(Mp, (Lp - mu[None, :]) / np.maximum(sd[None, :], 1e-6), 0.0).astype(np.float32)
nrgf_img = np.where(valid_c, cap_a_imatge(nrgf), 0.0)
g = np.clip(0.5 + 0.5 * nrgf_img / 2.5, 0, 1)
tifffile.imwrite(os.path.join(OUTDIR, 'CONTROL_NRGF_gris.tif'), (g * 65535 + 0.5).astype(np.uint16),
                 photometric='minisblack', compression='zlib', metadata=None, resolution=(300, 300))
cv2.imwrite(os.path.join(OUTDIR, 'CONTROL_NRGF_gris_x4.jpg'), (cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
log('→ CONTROL_NRGF_gris.tif')

json.dump(dict(bandes_deg=BANDES_DEG, G_EXT=G_EXT, G_TOT=G_TOT, G_WHITE=G_WHITE, A_T=A_T, NA=NA, NR=NR,
               sol_llenc=[SX, SY], lluna_llenc=list(LLUNA), taula=[list(map(float, f)) for f in taula],
               corr_vixen_sony_D=corr_ext,
               anells={k: {'max_anell_pct': float(100 * np.abs(v[:, 1]).max()), 'max_sector_pct': float(100 * v[:, 2].max())} for k, v in resum.items()}),
          open(os.path.join(OUTDIR, 'parametres.json'), 'w'), indent=1)
log('fet')
