"""msb_comu_v2 · Mòdul comú de la VERSIÓ 2 del mapa MSB (12-10-2026). No toca res de la v1: importa msb_comu (geometria,
zones, color, massa d'aire, cau) i hi afegeix el que canvia després de les dues verificacions (rev10, calcul.json: v1 i v2).

Què canvia respecte de la v1 (cada punt surt d'un «must_fix»):
  - REFERÈNCIA DE L'EXTINCIÓ: E = 10^(0,4·k·(X − X_ZP)) amb X_ZP = 6,0241 (la massa d'aire del Sol a la qual es va avaluar el
    punt zero, zp2.json), no X☉ a DATE-OBS (6,053). El punt zero dona el flux del Sol vist a través de X_ZP; cada píxel s'ha de
    portar a aquesta mateixa massa d'aire. La v1 feia servir 6,053: el mapa quedava un 1,1 % baix (10^(0,4·0,40·0,029) = 1,011).
    X a cada píxel continua essent la de DATE-OBS (meitat de la totalitat): la incertesa de l'època efectiva és el terme de deriva.
  - CEL: els models es llegeixen de v2/mapa/cel/CEL_v2.json (w1_cel_v2.py): a, b_old (el de la v1), b_new (pla a r ≥ 8 R☉),
    joint (cel + C(r)·10^(−0,4k(X−X_ZP))) i c (contaminat de corona: només registre).
  - INCERTESA DEL PUNT ZERO ASIMÈTRICA: bootstrap de fac_G (SENSIBILITAT_ZP.json, 2.000 mostres) 68 %: 2,308–2,754e-11 =
    −16,7 % / −0,6 % de l'adoptat (mediana −5,9 %). Costat de dalt: la σ de la covariància del wls (2,0 %), perquè el bootstrap
    no hi deixa marge. La TRIA DEL TERME DE COLOR (±9,4 %: 10^(0,4·0,653·c) − 1, c = 0,1488) va com a terme a part.
  - BIAIX DEL CEL (un sol sentit): la corona K+F que hi ha als píxels on s'estima el cel. Model: van de Hulst 1950, BAN 11, 135,
    eq. (5) K_max + eq. (7) F (escaneig de l'ADS llegit; unitats 1e-8 de la brillantor MITJANA del disc), passat pel MATEIX
    estimador del cel. El mapa queda massa baix en aquesta quantitat. No es corregeix (és un model): es declara i va al pressupost.

⛔ Normes: res inventat (NaN on no hi ha dada); la franja lunar i el buit del limbe no entren a cap ajust ni comparació.
Importar-lo no escriu res ni llegeix cap fitxer gros."""
import json
import math
from pathlib import Path

import numpy as np

import msb_comu as mc

V2 = mc.RES / 'v2'
MAPA2 = V2 / 'mapa'
CELDIR = MAPA2 / 'cel'
H, W = mc.H, mc.W

# ------------------------------------------------------------------------------------------------ extinció
K_EXT = mc.K_EXT                      # 0,40 (predeclarat a la v1; no canvia)
K_BANDA = mc.K_BANDA                  # (0,35; 0,72): capa sistemàtica
K_DIPOL = (0.0, 0.40, 0.57, 0.72)     # valors de k per a la prova del dipol amb el C2 (encàrrec v2)
X_REF = mc.ZP_X_SOL                   # 6,0241: referència de E (massa d'aire del Sol al punt zero)


def factor_extincio(X, k=K_EXT):
    """E = 10^(0,4·k·(X − X_ZP)). S'aplica DESPRÉS de restar el cel (el cel és llum atmosfèrica)."""
    return 10.0 ** (0.4 * k * (np.asarray(X, np.float64) - X_REF))


# ------------------------------------------------------------------------------------------------ punt zero
_SENS = mc.RES / 'zp_canal/SENSIBILITAT_ZP.json'
_ZPC = mc.RES / 'zp_canal/ZP_CANAL.json'
FAC_G = mc.FAC_G
C_G = 0.14879704521968498             # terme de color del verd (ZP_CANAL.json canals/G/c = zp2.json)


def punt_zero():
    """Percentils del bootstrap de fac_G i σ del wls, llegits dels JSON de zp_canal (post hoc, 11-10)."""
    s = json.load(open(_SENS))['r6']['bootstrap_conjunt']['fac_G']
    z = json.load(open(_ZPC))['canals']['G']
    out = dict(adoptat=FAC_G, p2_5=s['p2_5'], p16=s['p16'], p50=s['p50'], p84=s['p84'], p97_5=s['p97_5'], n=s['n'],
               sigma_wls_rel=z['sigma_fac_rel'], fac_sense_terme_color=z['model_sense_color']['fac'], c=z['c'])
    out['rel'] = {k: out[k] / FAC_G - 1 for k in ('p2_5', 'p16', 'p50', 'p84', 'p97_5')}
    out['rel_lo'] = -out['rel']['p16']                                   # 0,167
    out['rel_hi'] = max(out['rel']['p84'], out['sigma_wls_rel'])          # el bootstrap no dona marge cap amunt: σ del wls
    out['terme_color_rel'] = 10 ** (0.4 * 0.653 * out['c']) - 1          # 0,094
    out['sense_terme_color_rel'] = out['fac_sense_terme_color'] / FAC_G - 1
    return out


# Termes multiplicatius simètrics que no canvien (msb_comu.SIS_REL sense el punt zero, que ara va a part)
SIS_REL_SIM = {
    'transparency_drift_in_totality': 0.04,   # f2.py: caiguda del 8 % → ±4 %. Massa d'aire sola de C2 a C3 (k 0,40): −6,8 %
    'colour_inversion_and_chain': 0.025,
    'flat_field': 0.016,
    'linearity': 0.0013,
}


def rel_lo_hi_constants():
    """Termes relatius constants (sense extinció ni cel): (lo, hi) en quadratura, i el detall."""
    z = punt_zero()
    lo = [z['rel_lo'], z['terme_color_rel']] + list(SIS_REL_SIM.values())
    hi = [z['rel_hi'], z['terme_color_rel']] + list(SIS_REL_SIM.values())
    return math.sqrt(sum(x * x for x in lo)), math.sqrt(sum(x * x for x in hi)), z


# ------------------------------------------------------------------------------------------------ corona K i F (models)
def k_max_vdh(r):
    """van de Hulst 1950, eq. (5): K_max = 355,6 r^-17 + 177,8 r^-7 + 0,708 r^-2,5 (×1e-8 B☉ mitjà), equador, màxim solar."""
    r = np.asarray(r, np.float64)
    return (355.6 * r ** -17 + 177.8 * r ** -7 + 0.708 * r ** -2.5) * 1e-8


def k_min_vdh(r):
    """van de Hulst 1950, eq. (6): K_min = 200,0 r^-17 + 100,0 r^-7 + 0,398 r^-2,5 (×1e-8), equador, mínim solar."""
    r = np.asarray(r, np.float64)
    return (200.0 * r ** -17 + 100.0 * r ** -7 + 0.398 * r ** -2.5) * 1e-8


def f_vdh(r):
    """van de Hulst 1950, eq. (7): F = 14,86 r^-7 + 4,99 r^-2,5 (×1e-8 B☉ mitjà), simetria esfèrica."""
    r = np.asarray(r, np.float64)
    return (14.86 * r ** -7 + 4.99 * r ** -2.5) * 1e-8


# ------------------------------------------------------------------------------------------------ cel
def coef_cel_v2():
    f = CELDIR / 'CEL_v2.json'
    if not f.is_file():
        raise SystemExit('Falta v2/mapa/cel/CEL_v2.json: corre w1_cel_v2.py')
    return json.load(open(f))


def uv(x, y):
    return ((np.asarray(x, np.float64) - mc.SOL_XY[0]) / mc.RSOL_PX, (np.asarray(y, np.float64) - mc.SOL_XY[1]) / mc.RSOL_PX)


def cel_model_v2(x, y, nom, cel):
    """Cel en ADU/s de G_cam per a qualsevol model de CEL_v2.json (pla: c0, gu, gv; c: 6 coeficients)."""
    u, v = uv(x, y)
    m = cel['models'][nom]
    if 'coef' in m:
        q = m['coef']
        return q[0] + q[1] * u + q[2] * v + q[3] * u * u + q[4] * u * v + q[5] * v * v
    return m['c0'] + m.get('gu', 0.0) * u + m.get('gv', 0.0) * v


def biaix_cel_g(x, y, nom, cel, variant='central'):
    """Biaix del cel (ADU/s de G_cam, ≥ 0 si el cel porta corona): la resposta de l'estimador del cel al model K+F."""
    u, v = uv(x, y)
    b = cel['biaix_KF'][nom][variant]
    return b['dc0'] + b.get('dgu', 0.0) * u + b.get('dgv', 0.0) * v


SIGMA_SKY_FLOOR_BSOL = mc.SIGMA_SKY_FLOOR_BSOL   # 1e-9 B☉ (predeclarat a la v1; es manté)

# ------------------------------------------------------------------------------------------------ marques
BITS = mc.BITS
EXCLOU_PERFILS = mc.EXCLOU_PERFILS


def calcul_bloc_v2(y0, y1, cau, ma, cel, zones_d, k=K_EXT, centre=None):
    """Tots els plans de la v2 per a un bloc de files [y0, y1) a resolució plena (float32/uint8)."""
    F = np.asarray(cau['fusion_total_v42'][y0:y1], np.float32)
    sup = np.asarray(cau['support_v42'][y0:y1])
    wv = np.asarray(cau['weight_vixen_v42'][y0:y1], np.float64)
    vV = np.asarray(cau['var_vixen_v42'][y0:y1], np.float64)
    vS = np.asarray(cau['var_sony_v42'][y0:y1], np.float64)
    hh = y1 - y0
    yy = np.arange(y0, y1, dtype=np.float64)[:, None] * np.ones((1, W))
    xx = np.ones((hh, 1)) * np.arange(W, dtype=np.float64)[None, :]
    g = mc.geo_llenc(centre)
    r, pa = g.polar(xx, yy)
    dada = sup & np.all(np.isfinite(F), axis=2) & np.all(F > 0, axis=2)
    G = mc.verd_camera(F)
    A_ = mc.matriu_inversa()
    Rc = A_[0, 0] * F[..., 0].astype(np.float64) + A_[0, 1] * F[..., 1] + A_[0, 2] * F[..., 2]
    ad = cel['adoptat']
    S = cel_model_v2(xx, yy, ad, cel)
    alt = [cel_model_v2(xx, yy, m, cel) for m in cel['alternatives_sigma']]
    sig_sky = np.full(S.shape, SIGMA_SKY_FLOOR_BSOL / FAC_G)
    for Sx in alt:
        sig_sky = np.maximum(sig_sky, np.abs(Sx - S))
    bias = biaix_cel_g(xx, yy, ad, cel)
    h = ma.altura_bloc(y0, y1)
    X = mc.kasten_young(h)
    E = factor_extincio(X, k)
    net = G - S
    msb_noext = FAC_G * net
    msb = msb_noext * E
    # σ estadística propagada (la mateixa recepta que la v1; és una ESTIMACIÓ PROPAGADA, vegeu w4)
    ws = np.where(np.isfinite(vS), 1.0 - wv, 0.0)
    tv = np.where(wv > 0, wv * wv * vV, 0.0)
    ts = np.where(ws > 0, ws * ws * vS, 0.0)
    vf = tv + ts
    vf = np.where(((wv > 0) & ~np.isfinite(vV)) | ((ws > 0) & ~np.isfinite(vS)), np.nan, vf)
    sig_stat = FAC_G * E * mc.KAPPA_DOG * np.sqrt(vf) * G
    # sistemàtica asimètrica
    rlo, rhi, _ = rel_lo_hi_constants()
    e_lo_k = factor_extincio(X, K_BANDA[0]) / E - 1.0           # canvi relatiu amb k = 0,35
    e_hi_k = factor_extincio(X, K_BANDA[1]) / E - 1.0           # amb k = 0,72
    up = np.maximum(np.maximum(e_lo_k, e_hi_k), 0.0)
    dn = np.maximum(np.maximum(-e_lo_k, -e_hi_k), 0.0)
    sig_sky_msb = FAC_G * E * sig_sky
    am = np.abs(msb)
    sig_lo = np.sqrt((rlo * am) ** 2 + (dn * am) ** 2 + sig_sky_msb ** 2)
    sig_hi = np.sqrt((rhi * am) ** 2 + (up * am) ** 2 + sig_sky_msb ** 2)
    sky_bias_msb = FAC_G * E * bias
    # marques (les mateixes regles que la v1)
    fl = np.zeros((hh, W), np.uint8)
    fl[~dada] |= BITS['NO_DATA']
    rm = np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1])
    if 'gap' in zones_d:
        gx0, gy0, gap = zones_d['gap']['x0'], zones_d['gap']['y0'], zones_d['gap']['mask']
        a0, a1 = max(y0, gy0), min(y1, gy0 + gap.shape[0])
        if a1 > a0:
            sub = np.zeros((hh, W), bool)
            sub[a0 - y0:a1 - y0, gx0:gx0 + gap.shape[1]] = gap[a0 - gy0:a1 - gy0]
            fl[sub & dada] |= BITS['LIMB_GAP']
    fl[dada & (rm < mc.R_BANDA_PX)] |= BITS['MOON_BAND']
    for p0, dpa in mc.PROM_SECTORS:
        dp = np.abs((pa - p0 + 180) % 360 - 180)
        fl[dada & (dp <= dpa) & (r < mc.PROM_RMAX)] |= BITS['PROMINENCE']
    fl[dada & (np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX)] |= BITS['SONY_GHOST']
    fl[dada & (wv < mc.WV_SONY)] |= BITS['SONY_DOMINATED']
    rins = zones_d.get('R_inscrit_Rsol')
    if rins is not None:
        fl[r > rins] |= BITS['OUTSIDE_INSCRIBED']
    nul = (fl & (BITS['NO_DATA'] | BITS['LIMB_GAP'])) > 0
    fl[~nul & (msb < sig_sky_msb)] |= BITS['SKY_LIMITED']
    out = dict(G_cam=G, R_cam=Rc, sky=S, sigma_sky_adu=sig_sky, sky_bias_adu=bias, X=X, h=h, E=E, msb=msb, msb_noext=msb_noext,
               sigma_stat=sig_stat, sigma_sys_lo=sig_lo, sigma_sys_hi=sig_hi, sigma_sky_msb=sig_sky_msb, sky_bias_msb=sky_bias_msb,
               wv=wv, r=r, pa=pa)
    for kk in ('G_cam', 'R_cam', 'msb', 'msb_noext', 'sigma_stat', 'sigma_sys_lo', 'sigma_sys_hi', 'sigma_sky_msb', 'sky_bias_msb'):
        out[kk] = np.where(nul, np.nan, out[kk])
    out = {kk: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for kk, v in out.items()}
    out['flags'] = fl
    out['dada'] = dada
    return out
