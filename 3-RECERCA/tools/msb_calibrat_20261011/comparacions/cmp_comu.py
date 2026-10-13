"""cmp_comu · Mòdul comú de les comparacions del mapa MSB amb el K-Cor (pB) i el LASCO C2 (B total). Encàrrec «comparacions», 11-10-2026.

Importar-lo no escriu res ni llegeix cap fitxer gros.

Què hi ha:
  - rutes (ARREL = 4-Photoshop) i les dades externes (K-Cor L2 de l'11-10, LASCO C2 de l'01-10, taula del factor d'exposició);
  - els anells i les caselles d'1° (els de la c9 de l'01-10 i els nous del K-Cor);
  - percentils per grup (lexsort, sense bucles per casella) i la regressió robusta de la c9 (retall 3σ MAD, bootstrap per blocs de 10°);
  - el grau de polarització p(r) de la corona K (Thomson, van de Hulst 1950, enfosquiment lineal del limbe), tres models de densitat;
  - els dos models de corona F VERIFICATS a la font (van de Hulst 1950, eq. 7; Koutchmy & Lamy 1985, Fig. 3 digitalitzada);
  - els dos calibratges del C2 (SolarSoft c2_calfactor i Colaninno & Howard 2015, eq. 8).

⛔ Normes: res inventat. La franja del moviment lunar, el buit del limbe, el disc lunar, les protuberàncies i el fantasma de la Sony
no entren a cap comparació: una casella que en toqui un sol píxel queda fora sencera.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent                         # …/tools/msb_calibrat_20261011/comparacions
sys.path.insert(0, str(AQUI.parent))
import msb_comu as mc                                            # noqa: E402

ARREL = mc.ARREL                                                 # …/4-Photoshop
RES = mc.RES / 'comparacions'
COMPARTIR = mc.RES / 'per_compartir'
D11 = ARREL / '3-RECERCA/data/externes_20261011'
D01 = ARREL / '3-RECERCA/data/externes_20261001'
TOOLS01 = ARREL / '3-RECERCA/tools/comparacio_sdo_lasco_20261001'
RES01 = ARREL / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001'
PLE = mc.MAPA / 'ple'

KCOR_TOT = ['20260812_182846', '20260812_182902', '20260812_182917', '20260812_182932',
            '20260812_182947', '20260812_183002', '20260812_183017']          # els 7 fotogrames de 15 s dins de la totalitat
KCOR_CTRL = ['20260812_182831', '20260812_183033']                          # controls: acaba a C2 / comença després de C3
KCOR_AVG = ['20260812_182731', '20260812_182932']                           # mitjanes de 2 min (pb_avg)
GIF_C9 = '20260812_182932_kcor_l2_pb_avg_cropped.gif'                       # la GIF de la c9 (01-10)
C2_FITXERS = ['24038985.fts', '24038986.fts']                               # 18:24:31 i 18:36:15 (a cada costat de la totalitat)

ANELLS_KCOR = [(1.15, 1.25), (1.25, 1.40), (1.40, 1.70), (1.70, 2.00), (2.0, 2.5)]
ANELL_C9_FRANJA = (1.10, 1.15)                                              # anell K-Cor de la c9 que trepitja la franja (només es compta)
ANELLS_C2 = [(2.4, 2.6), (2.6, 2.9), (2.9, 3.3), (3.3, 3.8), (3.8, 4.5), (4.5, 5.5)]
PILAR = (288.0, 360.0)                                                      # pilar de l'ocultador del C2 (com la c9)
RADIS_FIG = np.round(np.geomspace(1.10, 6.0, 44), 4)                        # anells fins (±1,5 %) per a la figura
AMPLE_FIG = 0.015

# Bits que treuen una casella sencera si la toquen (predeclarat). SONY_DOMINATED i SKY_LIMITED NO: són dada.
TOCA = (mc.BITS['NO_DATA'] | mc.BITS['LIMB_GAP'] | mc.BITS['MOON_BAND'] | mc.BITS['PROMINENCE'] |
        mc.BITS['SONY_GHOST'] | mc.BITS['OUTSIDE_INSCRIBED'])


def sha256(ruta):
    return mc.sha256(ruta)


def rel(ruta):
    """Ruta relativa a 4-Photoshop/ (per als rebuts)."""
    p = Path(ruta).resolve()
    try:
        return str(p.relative_to(ARREL))
    except ValueError:
        return str(p)


# ------------------------------------------------------------------------------------------------ estadística
def percentils_grup(key, val, ngr, quant=(50,)):
    """Percentils per grup (key en [0, ngr)), ignorant NaN. Retorna (n, {q: valors}). (Com p3_perfils.medianes.)"""
    key = np.asarray(key); val = np.asarray(val, np.float64)
    m = (key >= 0) & (key < ngr) & np.isfinite(val)
    k = key[m].astype(np.int64); v = val[m]
    o = np.lexsort((v, k)); k = k[o]; v = v[o]
    n = np.bincount(k, minlength=ngr)[:ngr]
    ini = np.concatenate([[0], np.cumsum(n)[:-1]])
    res = {}
    for q in quant:
        out = np.full(ngr, np.nan)
        ok = n > 0
        pos = ini[ok] + (n[ok] - 1) * q / 100.0
        lo = np.floor(pos).astype(np.int64); hi = np.ceil(pos).astype(np.int64); fr = pos - lo
        out[ok] = v[lo] * (1 - fr) + v[hi] * fr
        res[q] = out
    return n, res


def clau_caselles(r, pa, anells, dpa=1.0):
    """Clau = anell·nb + casella d'angle (nb = 360/dpa); −1 fora de tots els anells."""
    nb = int(round(360 / dpa))
    key = np.full(np.shape(r), -1, np.int64)
    for i, (a, b) in enumerate(anells):
        m = (r >= a) & (r < b)
        key[m] = i * nb + (np.floor(pa[m] / dpa).astype(np.int64) % nb)
    return key, nb


def regressio(x, y, nboot=400, llavor=1):
    """La regressió de la c9 (01-10): y = f·x + s amb 4 iteracions de retall a 3σ (MAD); errors amb bootstrap per blocs de 10 caselles."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 12:
        return None
    xx_, yy_ = x[ok], y[ok]
    w = np.ones(ok.sum(), bool)
    for _ in range(4):
        f, s = np.polyfit(xx_[w], yy_[w], 1); res = yy_ - (f * xx_ + s); sd = 1.4826 * np.median(np.abs(res[w])); w = np.abs(res) < 3 * sd
    idx = np.nonzero(ok)[0]; blocs = idx // 10; ub = np.unique(blocs); rng = np.random.default_rng(llavor); fb = []
    pos = np.arange(ok.sum())
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([pos[blocs == b] for b in tria]); sel = sel[w[sel]]
        if len(sel) > 10:
            fb.append(np.polyfit(xx_[sel], yy_[sel], 1))
    fb = np.array(fb)
    rho = float(np.corrcoef(xx_[w], yy_[w])[0, 1])
    from scipy.stats import theilslopes
    ts = theilslopes(yy_, xx_)
    return dict(f=float(f), s=float(s), f_err=float(fb[:, 0].std()), s_err=float(fb[:, 1].std()), rho=rho, n=int(w.sum()), n_parells=int(ok.sum()),
                theil_sen=float(ts[0]), theil_sen_lo95=float(ts[2]), theil_sen_hi95=float(ts[3]))


def quocients(nostra, inst, nboot=400, llavor=2):
    """Sobre les caselles aparellades: quocient de medianes (com la c9) i mediana dels quocients per casella, amb bootstrap per blocs de 10°."""
    nostra = np.asarray(nostra, float); inst = np.asarray(inst, float)
    ok = np.isfinite(nostra) & np.isfinite(inst) & (inst > 0)
    if ok.sum() < 5:
        return dict(n=int(ok.sum()))
    qm = float(np.median(nostra[ok]) / np.median(inst[ok]))
    q = nostra[ok] / inst[ok]
    mq = float(np.median(q))
    idx = np.nonzero(ok)[0]; blocs = idx // 10; ub = np.unique(blocs); rng = np.random.default_rng(llavor)
    bq, bm = [], []
    pos = np.arange(ok.sum())
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([pos[blocs == b] for b in tria])
        bq.append(np.median(nostra[ok][sel]) / np.median(inst[ok][sel])); bm.append(np.median(q[sel]))
    return dict(n=int(ok.sum()), quocient_medianes=qm, quocient_medianes_err=float(np.std(bq)),
                mediana_quocients=mq, mediana_quocients_err=float(np.std(bm)),
                mediana_nostra=float(np.median(nostra[ok])), mediana_instrument=float(np.median(inst[ok])))


# ------------------------------------------------------------------------------------------------ polarització de la corona K
def _coef(r):
    """Coeficients A, B, C, D de van de Hulst (1950) per a un punt a distància r (R☉) del centre."""
    s = 1.0 / r; c = np.sqrt(np.clip(1 - s * s, 0, 1)); L = np.log((1 + s) / np.maximum(c, 1e-12))
    A = c * s * s
    B = -(1 / 8) * (1 - 3 * s * s - (c * c / s) * (1 + 3 * s * s) * L)
    C = 4 / 3 - c - c ** 3 / 3
    D = (1 / 8) * (5 + s * s - (c * c / s) * (5 - s * s) * L)
    return A, B, C, D


MODELS_DENSITAT = {   # densitats electròniques de manual (com la c9, c9_brillantor.py:178-180); la unitat no compta per a p
    'Baumbach-Allen': lambda r: 2.99 * r ** -16 + 1.55 * r ** -6 + 0.036 * r ** -1.5,
    'Saito (equator)': lambda r: 3.09 * r ** -16 + 1.58 * r ** -6 + 0.0251 * r ** -2.5,
    'streamer n~r^-4': lambda r: r ** -4.0,
}
U_ADOPTAT = 0.56   # enfosquiment lineal del limbe (com la c9); la sensibilitat a u es dona a part (no és un valor verificat per banda)


def integrals_k(rho, model, u=U_ADOPTAT):
    """(tB, pB) de la corona K, en unitats arbitràries proporcionals a la intensitat central del disc, a la distància aparent rho."""
    z = np.linspace(0, 20, 20001); r = np.sqrt(rho ** 2 + z ** 2); A, B, C, D = _coef(r); n = model(r)
    It = np.trapezoid(n * ((1 - u) * C + u * D), z)
    pB = np.trapezoid(n * (rho / r) ** 2 * ((1 - u) * A + u * B), z)
    return 2 * It - pB, pB


def polaritzacio(rho, model, u=U_ADOPTAT):
    tB, pB = integrals_k(rho, model, u)
    return pB / tB


_PCACHE = {}


def p_de_r(r, nom_model, u=U_ADOPTAT):
    """p(r) per interpolació en una graella de 1,04 a 3,2 R☉ (pas 0,005)."""
    k = (nom_model, u)
    if k not in _PCACHE:
        g = np.round(np.arange(1.04, 3.2001, 0.005), 4)
        _PCACHE[k] = (g, np.array([polaritzacio(x, MODELS_DENSITAT[nom_model], u) for x in g]))
    g, p = _PCACHE[k]
    return np.interp(r, g, p, left=np.nan, right=np.nan)


def transfer_banda_k(rho, model, u_nostra, u_kcor):
    """K(MSB) a la nostra banda / K(MSB) a la del K-Cor: tB(u)/(1 − u/3) (la MSB divideix per la brillantor MITJANA del disc)."""
    a = integrals_k(rho, model, u_nostra)[0] / (1 - u_nostra / 3)
    b = integrals_k(rho, model, u_kcor)[0] / (1 - u_kcor / 3)
    return a / b


# ------------------------------------------------------------------------------------------------ corona F (dos models verificats)
def f_vdh1950(r):
    """van de Hulst (1950), BAN 11, 135, eq. (7): F = 14,86 r^-7 + 4,99 r^-2,5, en unitats de 1e-8 × la brillantor MITJANA del disc
    (p. 136: «As a unit we take 10^-8 times the average surface brightness of the sun»). Simetria esfèrica (eqs. 8–9 fan servir la
    mateixa F als pols). Llegit a l'escaneig de l'ADS (1950BAN....11..135V, pp. 136 i 139)."""
    r = np.asarray(r, float)
    return (14.86 * r ** -7 + 4.99 * r ** -2.5) * 1e-8


_KL = None


def kl1985_coefs():
    global _KL
    if _KL is None:
        f = RES / 'models_f' / 'F_KL1985_digitalitzat.json'
        if not f.is_file():
            raise SystemExit('Falta comparacions/models_f/F_KL1985_digitalitzat.json: corre c0_models_f.py')
        _KL = json.load(open(f))
    return _KL


def f_kl1985(r, pa_deg=None):
    """Koutchmy & Lamy (1985), IAU Colloq. 85, Fig. 3 (model ASNS, 400–600 nm, log B en B/B☉ mitjà), digitalitzada (c0_models_f.py).
    Perfils equatorial i polar; entre tots dos, isofotes el·líptiques (com Lamy et al. 2020, §8.8): el punt (r, latitud φ) és a
    l'isofota de semieixos (r_eq, r_pol) amb F_eq(r_eq) = F_pol(r_pol) i (r cos φ / r_eq)² + (r sin φ / r_pol)² = 1.
    Latitud aproximada pel PA: φ = |PA mod 180 − 90| (eix de simetria = eix de rotació solar; aproximació declarada)."""
    k = kl1985_coefs()
    ce = np.array(k['coef_equ'])
    r = np.asarray(r, float)
    if pa_deg is None:
        return 10 ** np.polyval(ce, np.log10(r))
    pa = np.asarray(pa_deg, float) % 360
    lat = np.abs((pa % 180.0) - 90.0)                          # 0 a l'equador (PA 90, 270), 90° als pols (PA 0, 180)
    lr_g, lat_g, lF = _taula_kl()
    from scipy.interpolate import RegularGridInterpolator
    it = RegularGridInterpolator((lr_g, lat_g), lF, bounds_error=False, fill_value=np.nan)
    pts = np.c_[np.log10(r).ravel(), lat.ravel()]
    return (10 ** it(pts)).reshape(np.shape(r))


_KLT = None


def _taula_kl():
    """Taula log F(log r, latitud) de les isofotes el·líptiques (1,02–8 R☉, 0–90°)."""
    global _KLT
    if _KLT is None:
        k = kl1985_coefs()
        ce, cp = np.array(k['coef_equ']), np.array(k['coef_pol'])
        req = np.geomspace(0.9, 40.0, 4000)
        lFe = np.polyval(ce, np.log10(req))
        lrp = np.linspace(np.log10(0.8), np.log10(60.0), 6000); lFp = np.polyval(cp, lrp)
        o = np.argsort(lFp)
        rpol = 10 ** np.interp(lFe, lFp[o], lrp[o])             # r_pol(r_eq): mateixa F
        lr_g = np.linspace(np.log10(1.02), np.log10(8.0), 300); lat_g = np.linspace(0, 90, 91)
        out = np.full((lr_g.size, lat_g.size), np.nan)
        for i, lr in enumerate(lr_g):
            rr = 10 ** lr
            for j, la in enumerate(np.radians(lat_g)):
                x, z = rr * np.cos(la), rr * np.sin(la)
                g = (x / req) ** 2 + (z / rpol) ** 2 - 1.0
                jj = np.nonzero(np.diff(np.sign(g)))[0]
                if len(jj) == 0:
                    continue
                jj = jj[0]; t = g[jj] / (g[jj] - g[jj + 1]); re = req[jj] + t * (req[jj + 1] - req[jj])
                out[i, j] = np.polyval(ce, np.log10(re))
        _KLT = (lr_g, lat_g, out)
    return _KLT


MODELS_F = {'vdH1950': 'van de Hulst 1950, BAN 11, 135, eq. (7)',
            'KL1985': 'Koutchmy & Lamy 1985, IAU Colloq. 85 (ASSL 119), 63, Fig. 3 (digitised, elliptical isophotes)'}


# ------------------------------------------------------------------------------------------------ LASCO C2
def calfac_ssw(mjd):
    """SolarSoft c2_calfactor.pro (v1.9, 2007), Orange/Clear sense agrupar: (4,60403e-7·MJD + 0,0374116)·1e-10 B/B☉ per DN/s/px.
    És l'eq. (1) de Colaninno & Howard 2015 escrita com (4,60403e-5·MJD + 3,74116)·1e-12."""
    return (4.60403e-7 * mjd + 0.0374116) * 1e-10


def calfac_ch2015(mjd):
    """Colaninno & Howard 2015, Sol. Phys. 290, 997, eq. (8): PCF = (3,9 [±0,5]·1e-5·MJD + 5,2 [±0,3])·1e-12 MSB/(DN s^-1 px^-1).
    Llegida a la imatge de l'equació a PMC4479163 (200×19 px); comprovada: (i) el seu ajust ponderat de la Taula 2 dona
    3,927e-5 i 5,202; (ii) val 7,40e-12 el 2013 (Taula 2); (iii) 0,19 %/any (el text diu 0,20 ± 0,03 %/any).
    Al 2026 és una EXTRAPOLACIÓ de 13 anys de la recta 1996–2013."""
    return (3.9e-5 * mjd + 5.2) * 1e-12


def expfac(fitxer):
    """(factor, biaix) de la taula oficial c2_expfactor_260812.dat (format de read_exp_factor.pro)."""
    for lin in open(D11 / 'lasco_calib/c2_expfactor_260812.dat'):
        p = lin.split()
        if p and p[0] == fitxer:
            return float(p[1]), float(p[2])
    raise SystemExit(f'{fitxer} no és a c2_expfactor_260812.dat')


def carrega_c2(fitxer):
    """comu_comp.carrega_lasco (01-10: (DN − OFFSET)/EXPTIME, geometria de la capçalera amb sunpy) + factor d'exposició:
    B_DN/s = (DN − biaix)/(EXPTIME·expfac) (c2_calibrate.pro + get_exp_factor.pro), i vinyetatge c2vig_final.fts (0–100)."""
    sys.path.insert(0, str(TOOLS01))
    import comu_comp as cc
    from astropy.io import fits
    from astropy.time import Time
    d, g, hd = cc.carrega_lasco(fitxer)
    off = float(hd.get('offset', 0.0)); ex = float(hd['exptime'])
    fac, bias = expfac(fitxer)
    dn = d.astype(np.float64) * ex + off                         # torna als DN
    dns = (dn - bias) / (ex * fac)                               # DN/s amb el biaix i l'exposició corregits
    vig = np.clip(fits.open(D01 / 'lasco_calib/c2vig_final.fts')[0].data.astype(np.float64), 0, 100)
    mjd = Time(hd['date-obs'].replace('/', '-') + 'T' + hd['time-obs']).mjd
    info = dict(fitxer=fitxer, date_obs=hd['date-obs'], time_obs=hd['time-obs'], mjd=float(mjd), exptime=ex, offset_capcalera=off,
                expfac=fac, biaix_taula=bias, r1col=hd.get('r1col'), r1row=hd.get('r1row'), naxis1=hd.get('naxis1'), naxis2=hd.get('naxis2'),
                sumcol=hd.get('sumcol'), sumrow=hd.get('sumrow'), lebxsum=hd.get('lebxsum'), lebysum=hd.get('lebysum'),
                filtre=hd.get('filter'), polaritzador=hd.get('polar'), R_sol_px=float(g.R), centre=(float(g.cx), float(g.cy)),
                efecte_expfac_rel=float(np.nanmedian(((dn - bias) / (ex * fac)) / ((dn - off) / ex)) - 1))
    return dns * vig, g, info


# ------------------------------------------------------------------------------------------------ K-Cor
def geo_kcor(hd):
    """Geometria solar del K-Cor L2 des de la capçalera: centre = CRPIX − 1 (0-based), nord solar +fila, oest +x (INST_ROT = 0;
    «image has N up»), R☉ = RSUN_OBS/CDELT. Es comprova amb el WCS d'astropy."""
    from astropy.wcs import WCS
    w = WCS(hd)
    cx, cy = w.world_to_pixel_values(0.0, 0.0)
    nx, ny = w.world_to_pixel_values(0.0, 1000.0 / 3600.0) if w.wcs.cunit[0] == 'deg' else w.world_to_pixel_values(0.0, 1000.0)
    wx, wy = w.world_to_pixel_values(1000.0 / 3600.0, 0.0) if w.wcs.cunit[0] == 'deg' else w.world_to_pixel_values(1000.0, 0.0)
    nord = (float(nx - cx), float(ny - cy)); oest = (float(wx - cx), float(wy - cy))
    R = float(hd['RSUN_OBS']) / float(hd['CDELT1'])
    return mc.Geo(float(cx), float(cy), R, nord, (-oest[0], -oest[1]))


def carrega_kcor(stem, avg=False):
    from astropy.io import fits
    f = D11 / 'kcor' / f"{stem}_kcor_l2_pb{'_avg' if avg else ''}.fts.gz"
    h = fits.open(f)[0]
    return h.data.astype(np.float64), geo_kcor(h.header), h.header, f


def carrega_gif_c9():
    """La GIF de la c9 amb la inversió i les màscares de la c9 (c9_brillantor.py:109-113)."""
    from PIL import Image
    a = np.asarray(Image.open(D01 / 'kcor' / GIF_C9).convert('L')).astype(np.float64)
    g = mc.Geo(255.5, 255.5, 170.394, (0, -1), (-1, 0))
    pb = 9e-7 * (a / 255.0) ** 1.25
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r, _ = g.polar(xx, yy)
    pb[(r < 1.075) | (a >= 254)] = np.nan
    for (x0, x1, y0, y1) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]:
        pb[y0:y1, x0:x1] = np.nan
    return pb, g


def caselles_imatge(img, g, anells, dpa=1.0, quant=(50,), extra=None):
    """Percentils per (anell, casella d'1°) dels píxels d'una imatge 2D (centre del píxel). extra: màscara booleana addicional de vàlids."""
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float64)
    r, pa = g.polar(xx, yy)
    key, nb = clau_caselles(r, pa, anells, dpa)
    v = np.where(np.isfinite(img), img, np.nan)
    if extra is not None:
        v = np.where(extra, v, np.nan)
    n, q = percentils_grup(key.ravel(), v.ravel(), len(anells) * nb, quant)
    return n.reshape(len(anells), nb), {k: x.reshape(len(anells), nb) for k, x in q.items()}, (r, pa)
