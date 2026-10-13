"""w3 · El mapa MSB v2 a resolució plena i el FITS 2×2 amb WCS helioprojectiu (12-10-2026). No toca res de la v1.

Per blocs de 512 files, amb mmap (la cau és NOMÉS LECTURA), amb msb_comu_v2.calcul_bloc_v2:
  MSB = FAC_G · (G_cam − S) · 10^(0,4·k·(X − X_ZP)),   S = cel adoptat a CEL_v2.json (b_new: constant + pla a r ≥ 8 R☉)
Plens (v2/mapa/ple/): msb_ple_v2.npy, msb_noext_ple_v2.npy (float32), flags_ple_v2.npy (uint8).
FITS (v2/mapa/msb_mapa_2x2_v2.fits), mateixa regla d'agrupació que la v1: un píxel agrupat val la mitjana dels 4 si els 4 tenen
dada (ni NO_DATA ni LIMB_GAP); si no, NaN. σ_stat agrupada = √(Σσ²)/4 (PROPAGADA com si els píxels fossin independents: no ho són,
vegeu w3a); σ_sys_lo/hi, σ_sky i el biaix del cel agrupats = mitjana. Columna 10551 afegida com a NO_DATA (amplada senar).
Els COMMENT es tallen per paraules a 72 caràcters (textwrap) perquè el FITS no els parteixi a mig mot.
Ús: executa.sh w3_mapa_v2.py               → plens + FITS nou (s'atura si el FITS ja existeix: una versió nova porta un nom nou)
    executa.sh w3_mapa_v2.py --capcalera   → NOMÉS reescriu les capçaleres (COMMENT) del FITS v2 ja fet per aquest guió
                                             (comprova MAPVERS = 2 i SRCSHA); les dades no es toquen."""
import json
import math
import sys
import textwrap
import time
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

warnings.filterwarnings('ignore', category=RuntimeWarning)
T0 = time.time()
cau = mc.obre_cau()
MA = mc.MassaAire()
CEL = m2.coef_cel_v2()
Z = mc.zones()
SOR = json.load(open(m2.MAPA2 / 'soroll' / 'SOROLL_BLOCS.json'))
ZP = m2.punt_zero()
RLO, RHI, _ = m2.rel_lo_hi_constants()
NOMES_CAP = '--capcalera' in sys.argv
PLE = m2.MAPA2 / 'ple'; PLE.mkdir(parents=True, exist_ok=True)
H, W = mc.H, mc.W
Hb, Wb = H // 2, (W + 1) // 2
if not NOMES_CAP:
  o_msb = np.lib.format.open_memmap(PLE / 'msb_ple_v2.npy', mode='w+', dtype=np.float32, shape=(H, W))
  o_noe = np.lib.format.open_memmap(PLE / 'msb_noext_ple_v2.npy', mode='w+', dtype=np.float32, shape=(H, W))
  o_flg = np.lib.format.open_memmap(PLE / 'flags_ple_v2.npy', mode='w+', dtype=np.uint8, shape=(H, W))
plans_f = ['MSB', 'MSB_NOEXT', 'SIGMA_STAT', 'SIGMA_SYS_LO', 'SIGMA_SYS_HI', 'SIGMA_SKY', 'SKY_BIAS', 'SKY', 'AIRMASS', 'WVIXEN']
B = {p: np.full((Hb, Wb), np.nan, np.float32) for p in plans_f}
B['FLAGS'] = np.zeros((Hb, Wb), np.uint8)
recompte = {k: 0 for k in mc.BITS}
BL = 512


def pad(a, val):
    out = np.full((a.shape[0], W + 1), val, dtype=a.dtype)
    out[:, :W] = a
    return out


def agrupa_mitjana(a):
    a = pad(a.astype(np.float64), np.nan)
    return a.reshape(a.shape[0] // 2, 2, Wb, 2).mean(axis=(1, 3))


def agrupa_mitjana_disponible(a):
    a = pad(a.astype(np.float64), np.nan)
    return np.nanmean(a.reshape(a.shape[0] // 2, 2, Wb, 2), axis=(1, 3))


def agrupa_quad(a):
    a = pad(a.astype(np.float64), np.nan)
    return np.sqrt((a * a).reshape(a.shape[0] // 2, 2, Wb, 2).sum(axis=(1, 3))) / 4.0


def agrupa_or(f):
    f = pad(f, np.uint8(mc.BITS['NO_DATA']))
    f = f.reshape(f.shape[0] // 2, 2, Wb, 2)
    return f[:, 0, :, 0] | f[:, 0, :, 1] | f[:, 1, :, 0] | f[:, 1, :, 1]


if not NOMES_CAP:
    for y0 in range(0, H, BL):
        y1 = min(y0 + BL, H)
        o = m2.calcul_bloc_v2(y0, y1, cau, MA, CEL, Z)
        o_msb[y0:y1] = o['msb']; o_noe[y0:y1] = o['msb_noext']; o_flg[y0:y1] = o['flags']
        for k, b in mc.BITS.items():
            recompte[k] += int(((o['flags'] & b) > 0).sum())
        b0, b1 = y0 // 2, y1 // 2
        B['MSB'][b0:b1] = agrupa_mitjana(o['msb'])
        B['MSB_NOEXT'][b0:b1] = agrupa_mitjana(o['msb_noext'])
        B['SIGMA_STAT'][b0:b1] = agrupa_quad(o['sigma_stat'])
        B['SIGMA_SYS_LO'][b0:b1] = agrupa_mitjana(o['sigma_sys_lo'])
        B['SIGMA_SYS_HI'][b0:b1] = agrupa_mitjana(o['sigma_sys_hi'])
        B['SIGMA_SKY'][b0:b1] = agrupa_mitjana(o['sigma_sky_msb'])
        B['SKY_BIAS'][b0:b1] = agrupa_mitjana(o['sky_bias_msb'])
        B['SKY'][b0:b1] = agrupa_mitjana_disponible(m2.FAC_G * o['sky'].astype(np.float64))
        B['AIRMASS'][b0:b1] = agrupa_mitjana_disponible(o['X'])
        B['WVIXEN'][b0:b1] = agrupa_mitjana_disponible(o['wv'])
        B['FLAGS'][b0:b1] = agrupa_or(o['flags'])
        print(f'files {y0}-{y1} ({time.time() - T0:.0f} s)', flush=True)
    o_msb.flush(); o_noe.flush(); o_flg.flush()
    for p in ('SIGMA_STAT', 'SIGMA_SYS_LO', 'SIGMA_SYS_HI', 'SIGMA_SKY', 'SKY_BIAS', 'MSB_NOEXT'):
        B[p][~np.isfinite(B['MSB'])] = np.nan

# ---------------------------------------------------------------- WCS (la mateixa construcció que p2_mapa.py)
import astropy.units as u                                             # noqa: E402
from astropy.coordinates import EarthLocation, SkyCoord               # noqa: E402
from astropy.io import fits                                           # noqa: E402
from astropy.time import Time                                         # noqa: E402
from sunpy.coordinates import HeliographicStonyhurst                  # noqa: E402
import sunpy.map                                                      # noqa: E402

g = mc.geo_llenc()
kk_ = mc.RSOL_ARCSEC / (mc.RSOL_PX * g.det)
n, e = g.n, g.e
CD = np.array([[2 * kk_ * n[1], -2 * kk_ * n[0]], [2 * kk_ * e[1], -2 * kk_ * e[0]]])
CRPIX = ((mc.SOL_XY[0] - 0.5) / 2 + 1, (mc.SOL_XY[1] - 0.5) / 2 + 1)
tobs = Time(mc.DATE_OBS, scale='utc')
loc = EarthLocation(lat=mc.LLOC['lat'] * u.deg, lon=mc.LLOC['lon'] * u.deg, height=mc.LLOC['alt_m'] * u.m)
obs = loc.get_itrs(obstime=tobs).transform_to(HeliographicStonyhurst(obstime=tobs))
itrs = loc.get_itrs()
hdr = fits.Header()
hdr['WCSAXES'] = 2
hdr['CTYPE1'] = ('HPLN-TAN', 'helioprojective longitude (solar west +)')
hdr['CTYPE2'] = ('HPLT-TAN', 'helioprojective latitude (solar north +)')
hdr['CUNIT1'] = 'arcsec'; hdr['CUNIT2'] = 'arcsec'
hdr['CRPIX1'] = (CRPIX[0], 'Sun centre (ephemeris via Moon), binned')
hdr['CRPIX2'] = CRPIX[1]
hdr['CRVAL1'] = 0.0; hdr['CRVAL2'] = 0.0
hdr['CD1_1'] = CD[0, 0]; hdr['CD1_2'] = CD[0, 1]; hdr['CD2_1'] = CD[1, 0]; hdr['CD2_2'] = CD[1, 1]
hdr['DATE-OBS'] = (mc.DATE_OBS, 'mid-totality (UTC)')
hdr['DATE-BEG'] = (mc.DATE_BEG, 'C2, second contact (UTC)')
hdr['DATE-END'] = (mc.DATE_END, 'C3, third contact (UTC)')
hdr['TIMESYS'] = 'UTC'
hdr['HGLN_OBS'] = (float(obs.lon.deg), '[deg] observer Stonyhurst longitude')
hdr['HGLT_OBS'] = (float(obs.lat.deg), '[deg] observer Stonyhurst latitude')
hdr['DSUN_OBS'] = (float(obs.radius.to(u.m).value), '[m] observer-Sun distance')
hdr['OBSGEO-X'] = float(itrs.x.to(u.m).value); hdr['OBSGEO-Y'] = float(itrs.y.to(u.m).value); hdr['OBSGEO-Z'] = float(itrs.z.to(u.m).value)
hdr['RSUN_OBS'] = (mc.RSOL_ARCSEC, '[arcsec] apparent radius (DE421, site)')
hdr['RSUN_REF'] = (695700000.0, '[m]')
hdr['OBSRVTRY'] = ('Mirador Final 2', '42.299407 N, -5.02503 E, 798 m (Leon, Spain)')
hdr['SITELAT'] = mc.LLOC['lat']; hdr['SITELONG'] = mc.LLOC['lon']; hdr['SITEELEV'] = mc.LLOC['alt_m']
hdr['TELESCOP'] = ('Vixen VSD90SS + Sony 300mm GM', 'two trains; Vixen only < 1.9 Rsun')
hdr['INSTRUME'] = ('Canon EOS R6 Mark III', 'camera of the zero point (green)')
hdr['WAVELNTH'] = (530, 'APPROX., UNVERIFIED (camera green)')
hdr['WAVEUNIT'] = 'nm'

rr = np.array([1.0, 1.15, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]); pp = np.arange(0.0, 360.0, 22.5)
R_, P_ = np.meshgrid(rr, pp, indexing='ij'); R_ = R_.ravel(); P_ = P_.ravel()
x, y = g.px(R_, P_)
p1 = (x - 0.5) / 2 + 1; p2 = (y - 0.5) / 2 + 1

# ---------------------------------------------------------------- capçalera primària
bm = CEL['models'][CEL['adoptat']]
bias = CEL['biaix_KF'][CEL['adoptat']]['central']
sor = SOR['zones']['r_ge_8']
rho16 = max(sor['16']['rho_files'], sor['16']['rho_columnes']); rho32 = max(sor['32']['rho_files'], sor['32']['rho_columnes'])
rho1 = max(sor['1']['rho_files'], sor['1']['rho_columnes'])
com_primari = [
    'Calibrated map of the 2026-08-12 total-eclipse corona in mean solar brightness.',
    'VERSION 2 (2026-10-12). BUNIT MSB = B/Bsun, Bsun = mean brightness of the disc.',
    'TOTAL brightness (K + F corona), UNPOLARIZED, camera GREEN channel (native).',
    'Sky subtracted: constant + plane fitted directly at r >= 8 Rsun (SKYMODEL),',
    'where the coronal extinction dipole is small; then EXTINCTION-CORRECTED to the',
    'airmass of the Sun at the zero-point epoch (ZPXSUN), X per pixel at DATE-OBS:',
    'MSB = FACG * (G_cam - SKY) * 10**(0.4*KEXT*(X - ZPXSUN)).',
    'XSUN (Sun at DATE-OBS) is information only. Version 1 used XSUN as reference,',
    'which made it 1.1 % lower at KEXT = 0.40 (10**(0.4*0.40*(XSUN-ZPXSUN))).',
    'Airmass of the Sun from C2 to C3: 5.958 to 6.149, i.e. -6.8 % at KEXT = 0.40.',
    'Zero point from field stars (green; 14 stars; colour term at solar B-V): FACG.',
    'Bootstrap of FACG is asymmetric (FACGP16, FACGP50, FACGP84): the map may be too',
    'HIGH by up to 17 % (68 %); the colour-term choice (FACGCOL, +/-9.4 %) is apart.',
    'Input: linear composite fusion_total_v42 (Vixen R6 III + Sony A7R IIIA, Vixen units).',
    'Beyond ~1.9 Rsun the data are Sony scaled by rho (WVIXEN < 0.99); the Sony own',
    'zero point would give about +20 % (unresolved; NOT in SIGMA_SYS_LO/HI).',
    'NaN = no data: Moon disc, the 1-2 px gap at the limb, outside the sensors.',
    'Nothing is filled, extrapolated or modelled in place of data.',
    'Lunar-motion band = FLAGS value 4 (bit 2): within 496 px (canvas) of the lunar',
    'centre; frames of different instants are mixed there; exclude it from any fit.',
    'Binning 2x2: mean of the 4 canvas pixels if all 4 have data, else NaN.',
    'SIGMA_SYS_LO / SIGMA_SYS_HI: 1-sigma systematic downwards / upwards: zero point,',
    'colour term, drift, colour inversion and chain, flat, linearity, extinction',
    'k 0.35-0.72, sky model (with floor). NOT included: stray light / halo of our',
    'optics (no model), the Sony-rho transfer, and the one-sided SKY_BIAS.',
    'SKY_BIAS: model K+F corona (van de Hulst 1950 Kmax + F) that the sky estimate',
    'absorbs; the map is too LOW by about this amount. One-sided, model-based, NOT',
    'applied to MSB.',
    'SIGMA_STAT: a propagated estimate, NOT an upper bound. Neighbouring pixels are',
    f'correlated: the pixel-to-pixel scatter is {rho1:.2f} of it, but means of 16 and 32 px',
    f'blocks scatter {rho16:.2f} and {rho32:.2f} times the independent-pixel prediction',
    '(sky zone r >= 8 Rsun). Do not average it as sqrt(N).',
    'Our map exceeds LASCO-C2 at 2.4-5.5 Rsun; the size of the excess depends on the',
    'C2 calibration and on the sky level; cause unresolved (stray light, sky, C2).',
    "PRELIMINARY: not for publication without the author's consent.",
]


def cap_comu(h, extname, bunit, desc):
    h = h.copy()
    h['EXTNAME'] = extname
    h['BUNIT'] = (bunit, desc[:47])
    return h


h0 = hdr.copy()
h0['BUNIT'] = ('MSB', 'B/Bsun (mean solar brightness)')
h0['BTYPE'] = 'total brightness K+F unpolarized camera green'
h0['MAPVERS'] = (2, 'version of the map (1 = 2026-10-11)')
h0['FACG'] = (m2.FAC_G, 'MSB per ADU/s per native green pixel (stars)')
h0['FACGP16'] = (ZP['p16'], 'bootstrap 16th percentile of FACG')
h0['FACGP50'] = (ZP['p50'], 'bootstrap median of FACG')
h0['FACGP84'] = (ZP['p84'], 'bootstrap 84th percentile of FACG')
h0['FACGELO'] = (ZP['rel_lo'], 'relative 1-sigma of FACG downwards (bootstrap)')
h0['FACGEHI'] = (ZP['rel_hi'], 'relative 1-sigma of FACG upwards (wls cov.)')
h0['FACGCOL'] = (ZP['terme_color_rel'], 'colour-term choice, relative, separate term')
h0['KEXT'] = (m2.K_EXT, '[mag/airmass] adopted extinction (model)')
h0['KEXTLO'] = (m2.K_BANDA[0], 'k band low (systematic layer)')
h0['KEXTHI'] = (m2.K_BANDA[1], 'k band high (stars, vignetting-contaminated)')
h0['ZPXSUN'] = (m2.X_REF, 'REFERENCE of E: Sun airmass at the ZP epoch')
h0['ZPEPOCH'] = (mc.ZP_EPOCA_UTC, 'epoch of the star zero point (UTC)')
h0['XSUN'] = (MA.X_sol, 'Sun airmass at DATE-OBS (info; not reference)')
h0['HSUN'] = (MA.h_sol, '[deg] apparent altitude of the Sun at DATE-OBS')
h0['AIRMMOD'] = ('Kasten-Young 1989', 'apparent altitude, T 20 C, P 930 hPa, 550 nm')
h0['DRIFTC23'] = (-0.068, 'airmass-only change C2->C3 at KEXT (fraction)')
h0['PAZENITH'] = (33.21, '[deg] solar PA of the zenith at DATE-OBS')
h0['SKYMODEL'] = ('b_new: constant + plane at r>=8 Rsun', 'fitted directly to G_cam')
h0['SKYC0'] = (bm['c0'], '[ADU/s G_cam] sky at the Sun centre')
h0['SKYGU'] = (bm['gu'], '[ADU/s per Rsun] gradient along +x')
h0['SKYGV'] = (bm['gv'], '[ADU/s per Rsun] gradient along +row')
h0['SKYALT'] = (','.join(CEL['alternatives_sigma']), 'sky alternatives in SIGMA_SKY (a = constant)')
h0['SKYFLOOR'] = (m2.SIGMA_SKY_FLOOR_BSOL, '[Bsun] floor of the sky uncertainty')
h0['SKYBIAS0'] = (bias['dc0'], '[ADU/s] K+F model in the sky at the Sun centre')
h0['SKYBIAGV'] = (bias['dgv'], '[ADU/s per Rsun] K+F model gradient along +row')
h0['SYSRELLO'] = (RLO, 'constant relative systematic down (quadrature)')
h0['SYSRELHI'] = (RHI, 'constant relative systematic up (quadrature)')
for i, (kk, vv) in enumerate(m2.SIS_REL_SIM.items()):
    h0[f'SYSREL{i}'] = (vv, kk[:46])
h0['KAPPADOG'] = (mc.KAPPA_DOG, 'per-pixel sigma / sqrt(DoG variance), white')
h0['BINNING'] = (2, 'canvas pixels per side')
h0['CANVSCL'] = (mc.SC, '[arcsec] canvas pixel scale (unbinned)')
h0['CANVSUNX'] = (mc.SOL_XY[0], 'Sun centre on the full canvas, x (0-based)')
h0['CANVSUNY'] = (mc.SOL_XY[1], 'Sun centre on the full canvas, row (0-based)')
h0['RSUNPIX'] = (mc.RSOL_PX, 'Rsun in canvas px (unbinned)')
h0['MOONX'] = (mc.LLUNA_XY[0], 'Moon centre 18:28:49, canvas x (0-based)')
h0['MOONY'] = (mc.LLUNA_XY[1], 'Moon centre 18:28:49, canvas row (0-based)')
h0['MOONRPX'] = (mc.R_LLUNA_PX, 'Moon radius, canvas px')
h0['SRCSHA'] = (mc.SHA_CAU['fusion_total_v42.npy'][:16], 'sha256 (first 16) of fusion_total_v42.npy')
for kk, vv in mc.BITS.items():
    h0[f'FLAGB{int(math.log2(vv))}'] = (kk, f'bit {int(math.log2(vv))}, value {vv}')
def paragrafs(text_list):
    """Uneix les línies en paràgrafs (una línia que acaba en punt tanca el paràgraf) i les talla per paraules a 72."""
    out, cur = [], []
    for t in text_list:
        cur.append(t)
        if t.rstrip().endswith(('.', ':')) and not t.rstrip().endswith(('e.g.', 'i.e.')):
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    linies = []
    for p_ in out:
        linies += textwrap.wrap(p_, 72)
    return linies


COM0 = paragrafs(com_primari + ['Extensions: MSB_NOEXT, SIGMA_STAT, SIGMA_SYS_LO, SIGMA_SYS_HI, SIGMA_SKY, SKY_BIAS, SKY, AIRMASS, WVIXEN, FLAGS.',
                                'Code: 4-Photoshop/3-RECERCA/tools/msb_calibrat_20261011 (msb_comu_v2.py, w3_mapa_v2.py).'])
for c in COM0:
    h0['COMMENT'] = c
hdus = [fits.PrimaryHDU(None if NOMES_CAP else B['MSB'], header=h0)]
COMEXT = {}
desc = {
    'MSB_NOEXT': ('MSB', 'same map WITHOUT the extinction correction (E = 1)'),
    'SIGMA_STAT': ('MSB', 'statistical 1-sigma, PROPAGATED (not an upper bound): kappa*sqrt(wv^2 vV + ws^2 vS)*G_cam*FACG*E, '
                   'binned sqrt(sum s^2)/4 as if independent'),
    'SIGMA_SYS_LO': ('MSB', 'systematic 1-sigma DOWNWARDS (true value lower): ZP bootstrap 16.7 %, colour term 9.4 %, drift, '
                     'chain, flat, linearity, extinction band, sky'),
    'SIGMA_SYS_HI': ('MSB', 'systematic 1-sigma UPWARDS (true value higher): ZP 2.0 % (wls), colour term 9.4 %, drift, chain, '
                     'flat, linearity, extinction band, sky. SKY_BIAS, halo and Sony-rho NOT included'),
    'SIGMA_SKY': ('MSB', 'sky-model part of SIGMA_SYS_*: max(|sky a - adopted|, floor 1e-9 Bsun) * FACG * E'),
    'SKY_BIAS': ('MSB', 'ONE-SIDED, model-based: K+F (van de Hulst 1950 Kmax+F) absorbed by the sky estimate, * E; '
                 'the map is too low by about this amount; NOT applied'),
    'SKY': ('Bsun', 'adopted sky model (b_new) in Bsun, NOT extinction corrected (atmospheric light)'),
    'AIRMASS': ('', 'Kasten-Young airmass per pixel (refracted altitude) at DATE-OBS'),
    'WVIXEN': ('', 'Vixen weight of the fusion (1 = Vixen only; < 0.99 Sony scaled by rho)'),
    'FLAGS': ('', 'uint8 bit field, see FLAGB* keywords in the primary header'),
}
for nom, (bu, dd) in desc.items():
    h = cap_comu(hdr, nom, bu, dd)
    cl = textwrap.wrap(dd, 72)
    if nom == 'FLAGS':
        for kk, vv in mc.BITS.items():
            cl += textwrap.wrap(f'bit {int(math.log2(vv))} (value {vv}) {kk}: {mc.DESC_BITS[kk]}', 72)
    for c in cl:
        h['COMMENT'] = c
    COMEXT[nom] = cl
    hdus.append(fits.ImageHDU(None if NOMES_CAP else B[nom], header=h))
FITS = m2.MAPA2 / 'msb_mapa_2x2_v2.fits'
if NOMES_CAP:
    with fits.open(FITS, mode='update') as hl:
        if hl[0].header.get('MAPVERS') != 2 or hl[0].header.get('SRCSHA') != h0['SRCSHA']:
            raise SystemExit('el FITS no és la v2 d\'aquest guió: no es toca')
        for hh, cl in [(hl[0], COM0)] + [(hl[n_], COMEXT[n_]) for n_ in COMEXT]:
            while 'COMMENT' in hh.header:
                del hh.header['COMMENT']
            for c in cl:
                hh.header['COMMENT'] = c
        for kk in ('FLAGB0', 'FLAGB1', 'FLAGB2', 'FLAGB3', 'FLAGB4', 'FLAGB5', 'FLAGB6', 'FLAGB7'):
            hl[0].header[kk] = (h0[kk], h0.comments[kk])
        hl.flush()
    print('capçaleres reescrites (dades intactes)')
    sys.exit(0)
if FITS.exists():
    raise SystemExit(f'{FITS} ja existeix: una versió nova porta un nom nou (no se sobreescriu)')
fits.HDUList(hdus).writeto(FITS, overwrite=False, output_verify='exception')
print(f'FITS escrit ({time.time() - T0:.0f} s)', flush=True)
with fits.open(FITS) as hl:
    m2_ = sunpy.map.Map(np.asarray(hl[0].data), hl[0].header)
    noms_ext = [hh.name for hh in hl]
c2 = m2_.pixel_to_world((p1 - 1) * u.pix, (p2 - 1) * u.pix)
sep2 = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=c2.frame).separation(c2).to(u.rad).value
pa_ast = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=c2.frame).position_angle(c2).to(u.deg).value
dpa = ((-pa_ast) % 360 - P_ + 180) % 360 - 180
prova_wcs = dict(n=int(R_.size), max_err_r=float(np.max(np.abs(np.tan(sep2) * 206264.80624709636 / mc.RSOL_ARCSEC - R_))),
                 max_err_pa_deg=float(np.max(np.abs(dpa))), extensions=noms_ext, unitat_sunpy=str(m2_.unit),
                 nota='prova d\'AUTOCONSISTÈNCIA (anada i tornada amb sunpy): no valida el centre absolut, que té ±4,5 px')
v1c = json.load(open(mc.MAPA / 'PROVES_P2.json'))['recompte_flags_ple']
rep = dict(guio='w3_mapa_v2.py', data_execucio=time.strftime('%Y-%m-%dT%H:%M:%S'), temps_s=time.time() - T0,
           forma_ple=[H, W], forma_agrupat=[Hb, Wb], recompte_flags_ple=recompte, recompte_flags_v1=v1c,
           canvi_recompte={k: recompte[k] - v1c[k] for k in recompte}, prova_wcs=prova_wcs,
           cel_adoptat=CEL['adoptat'], X_ref=m2.X_REF, X_sol_date_obs=MA.X_sol, rel_lo=RLO, rel_hi=RHI, punt_zero=ZP)
json.dump(rep, open(m2.MAPA2 / 'PROVES_W3.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('fet', json.dumps({k: rep[k] for k in ('canvi_recompte', 'prova_wcs', 'rel_lo', 'rel_hi')}, ensure_ascii=False, default=float))
