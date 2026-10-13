"""p2 · El mapa MSB (B/B☉) a resolució plena i el FITS 2×2 amb WCS helioprojectiu (11-10-2026).

Per blocs de 512 files, amb mmap (la cau és NOMÉS LECTURA):
  G_cam = verd natiu (inversió exacta del color) · S = cel (model b) · X = massa d'aire per píxel · E = 10^(0,4·k·(X − X☉))
  MSB = 2,7714e-11 · (G_cam − S) · E      MSB_NOEXT = 2,7714e-11 · (G_cam − S)
Plens (mapa/ple/): msb_ple.npy, msb_noext_ple.npy (float32) i flags_ple.npy (uint8). Qualsevol altre pla es pot refer amb
msb_comu.calcul_bloc().
FITS (mapa/msb_mapa_2x2.fits): 2×2. REGLA DE L'AGRUPACIÓ: un píxel agrupat val la mitjana dels 4 si els 4 tenen dada
(ni NO_DATA ni LIMB_GAP); si no, NaN. σ_stat agrupada = √(Σσ²)/4 (píxels independents); σ_sys i σ_sky agrupades = mitjana
(sistemàtiques, correlacionades). Cel, massa d'aire i pes Vixen: mitjana dels píxels del llenç. FLAGS: OR dels 4.
L'amplada del llenç (10551) és senar: s'afegeix una columna sense dada (NO_DATA) i el FITS fa 5276 columnes; no es retalla res."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

T0 = time.time()
cau = mc.obre_cau()
MA = mc.MassaAire()
CEL = mc.coef_cel()
Z = mc.zones()
PLE = mc.MAPA / 'ple'; PLE.mkdir(parents=True, exist_ok=True)
H, W = mc.H, mc.W
Hb, Wb = H // 2, (W + 1) // 2
o_msb = np.lib.format.open_memmap(PLE / 'msb_ple.npy', mode='w+', dtype=np.float32, shape=(H, W))
o_noe = np.lib.format.open_memmap(PLE / 'msb_noext_ple.npy', mode='w+', dtype=np.float32, shape=(H, W))
o_flg = np.lib.format.open_memmap(PLE / 'flags_ple.npy', mode='w+', dtype=np.uint8, shape=(H, W))
plans_f = ['MSB', 'MSB_NOEXT', 'SIGMA_STAT', 'SIGMA_SYS', 'SIGMA_SKY', 'SKY', 'AIRMASS', 'WVIXEN']
B = {p: np.full((Hb, Wb), np.nan, np.float32) for p in plans_f}
B['FLAGS'] = np.zeros((Hb, Wb), np.uint8)
recompte = {k: 0 for k in mc.BITS}
BL = 512


def pad(a, val):
    out = np.full((a.shape[0], W + 1), val, dtype=a.dtype)
    out[:, :W] = a
    return out


def agrupa_mitjana(a):              # mitjana de 4 (NaN si en falta algun)
    a = pad(a.astype(np.float64), np.nan)
    return a.reshape(a.shape[0] // 2, 2, Wb, 2).mean(axis=(1, 3))


def agrupa_mitjana_disponible(a):   # mitjana dels píxels del llenç (la columna afegida no compta)
    a = pad(a.astype(np.float64), np.nan)
    return np.nanmean(a.reshape(a.shape[0] // 2, 2, Wb, 2), axis=(1, 3))


def agrupa_quad(a):                 # √(Σσ²)/4
    a = pad(a.astype(np.float64), np.nan)
    return np.sqrt((a * a).reshape(a.shape[0] // 2, 2, Wb, 2).sum(axis=(1, 3))) / 4.0


def agrupa_or(f):
    f = pad(f, np.uint8(mc.BITS['NO_DATA']))
    f = f.reshape(f.shape[0] // 2, 2, Wb, 2)
    return f[:, 0, :, 0] | f[:, 0, :, 1] | f[:, 1, :, 0] | f[:, 1, :, 1]


import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
for y0 in range(0, H, BL):
    y1 = min(y0 + BL, H)
    o = mc.calcul_bloc(y0, y1, cau, MA, CEL, Z)
    o_msb[y0:y1] = o['msb']; o_noe[y0:y1] = o['msb_noext']; o_flg[y0:y1] = o['flags']
    for k, b in mc.BITS.items():
        recompte[k] += int(((o['flags'] & b) > 0).sum())
    b0, b1 = y0 // 2, y1 // 2
    B['MSB'][b0:b1] = agrupa_mitjana(o['msb'])
    B['MSB_NOEXT'][b0:b1] = agrupa_mitjana(o['msb_noext'])
    B['SIGMA_STAT'][b0:b1] = agrupa_quad(o['sigma_stat'])
    B['SIGMA_SYS'][b0:b1] = agrupa_mitjana(o['sigma_sys'])
    B['SIGMA_SKY'][b0:b1] = agrupa_mitjana(o['sigma_sky_msb'])
    B['SKY'][b0:b1] = agrupa_mitjana_disponible(mc.FAC_G * o['sky'].astype(np.float64))
    B['AIRMASS'][b0:b1] = agrupa_mitjana_disponible(o['X'])
    B['WVIXEN'][b0:b1] = agrupa_mitjana_disponible(o['wv'])
    B['FLAGS'][b0:b1] = agrupa_or(o['flags'])
    print(f'files {y0}-{y1} ({time.time() - T0:.0f} s)', flush=True)
o_msb.flush(); o_noe.flush(); o_flg.flush()
# σ_stat on MSB és NaN (sense dada) ja surt NaN; on el MSB agrupat és NaN, tots els plans d'incertesa també
for p in ('SIGMA_STAT', 'SIGMA_SYS', 'SIGMA_SKY', 'MSB_NOEXT'):
    B[p][~np.isfinite(B['MSB'])] = np.nan

# ---------------------------------------------------------------- WCS helioprojectiu (manual)
import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from sunpy.coordinates import HeliographicStonyhurst, Helioprojective, frames

g = mc.geo_llenc()
k = mc.RSOL_ARCSEC / (mc.RSOL_PX * g.det)            # ″ per píxel del llenç / det
n, e = g.n, g.e
CD = np.array([[2 * k * n[1], -2 * k * n[0]],
               [2 * k * e[1], -2 * k * e[0]]])
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
wcs = WCS(hdr)

# ---------------------------------------------------------------- prova d'anada i tornada del WCS
from astropy.coordinates import SkyCoord as SC_
rr = np.array([1.0, 1.15, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]); pp = np.arange(0.0, 360.0, 22.5)
R_, P_ = np.meshgrid(rr, pp, indexing='ij'); R_ = R_.ravel(); P_ = P_.ravel()
x, y = g.px(R_, P_)
p1 = (x - 0.5) / 2 + 1; p2 = (y - 0.5) / 2 + 1
fhdr = hdr.copy(); fhdr['NAXIS'] = 2; fhdr['NAXIS1'] = Wb; fhdr['NAXIS2'] = Hb
import sunpy.map
m_ = sunpy.map.Map(np.zeros((Hb, Wb), np.float32), fhdr)
coord = m_.pixel_to_world((p1 - 1) * u.pix, (p2 - 1) * u.pix)          # sunpy: píxels 0-based
cen = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=coord.frame)
sep = cen.separation(coord).to(u.rad).value
r_back = np.tan(sep) * 206264.80624709636 / mc.RSOL_ARCSEC          # projecció gnòmica (TAN)
pa_ast = cen.position_angle(coord).to(u.deg).value                   # des de +Ty cap a +Tx (oest)
pa_back = (-pa_ast) % 360                                            # PA solar: cap a l'est
dpa = (pa_back - P_ + 180) % 360 - 180
pix_back = m_.world_to_pixel(coord)
dpix = np.hypot(pix_back.x.value - (p1 - 1), pix_back.y.value - (p2 - 1))
prova_wcs = dict(n=int(R_.size), max_err_r=float(np.max(np.abs(r_back - R_))), max_err_r_rel=float(np.max(np.abs(r_back / R_ - 1))),
                 max_err_pa_deg=float(np.max(np.abs(dpa))), max_err_pixel_anada_tornada=float(np.max(dpix)),
                 passa=bool(np.max(np.abs(r_back - R_)) < 1e-6 and np.max(np.abs(dpa)) < 1e-6 and np.max(dpix) < 1e-6),
                 observador_sunpy=str(m_.observer_coordinate), rsun_sunpy_arcsec=float(m_.rsun_obs.to(u.arcsec).value),
                 nota='r i PA de pixel_to_world (sunpy) amb la projecció gnòmica, contra els (r, PA) de partida a msb_comu.Geo.px')
print('prova WCS', prova_wcs, flush=True)

# ---------------------------------------------------------------- FITS
ks = mc.K_EXT
com_primari = [
    'Calibrated map of the 2026-08-12 total-eclipse corona in mean solar brightness.',
    'BUNIT MSB = B/Bsun, Bsun = mean brightness of the solar disc.',
    'TOTAL brightness (K + F corona), UNPOLARIZED, camera GREEN channel (native, not sRGB).',
    'Sky subtracted (constant + plane model, b); EXTINCTION-CORRECTED to the airmass of',
    'the Sun: MSB = FACG * (G_cam - SKY) * 10**(0.4*KEXT*(X - XSUN)).',
    'Zero point from field stars (green channel; 14 stars; colour term at solar B-V).',
    'Input: linear composite fusion_total_v42 (Vixen R6 III + Sony A7R IIIA, Vixen units).',
    'NaN = no data: Moon disc, the 1-2 px gap at the limb, outside the sensors.',
    'Nothing is filled, extrapolated or modelled in place of data.',
    'Lunar-motion band (FLAGS bit 4): within 496 px (canvas) of the lunar centre; frames',
    'of different instants are mixed there; exclude it from any fit or comparison.',
    'Binning 2x2: mean of the 4 canvas pixels if all 4 have data, else NaN.',
    'Uncertainty extensions: SIGMA_STAT (statistical), SIGMA_SYS (systematic, 1 sigma),',
    'SIGMA_SKY (sky-model part of SIGMA_SYS). Halo / stray light of our optics: NOT',
    'modelled and NOT included (LASCO-C2 comparison bounds an excess of x1.2-1.8 at',
    '2.4-5.5 Rsun). PRELIMINARY: not for publication without the author\'s consent.',
]
def cap_comu(h, extname, bunit, desc):
    h = h.copy()
    h['EXTNAME'] = extname
    h['BUNIT'] = (bunit, desc[:47])
    return h
h0 = hdr.copy()
h0['BUNIT'] = ('MSB', 'B/Bsun (mean solar brightness)')
h0['BTYPE'] = 'total brightness K+F unpolarized camera green'
h0['FACG'] = (mc.FAC_G, 'MSB per ADU/s per native green pixel (stars)')
h0['FACGERR'] = (mc.FAC_G_REL_ERR, 'relative 1-sigma of FACG')
h0['KEXT'] = (ks, '[mag/airmass] adopted extinction (model)')
h0['KEXTLO'] = (mc.K_BANDA[0], 'k band low (systematic layer)')
h0['KEXTHI'] = (mc.K_BANDA[1], 'k band high (stars, vignetting-contaminated)')
h0['XSUN'] = (MA.X_sol, 'Kasten-Young airmass of the Sun at DATE-OBS')
h0['HSUN'] = (MA.h_sol, '[deg] apparent (refracted) altitude of the Sun')
h0['AIRMMOD'] = ('Kasten-Young 1989', 'apparent altitude, T 20 C, P 930 hPa, 550 nm')
h0['ZPXSUN'] = (mc.ZP_X_SOL, 'airmass at which the star ZP was evaluated')
h0['PAZENITH'] = (33.21, '[deg] solar PA of the zenith at DATE-OBS')
h0['SKYMODEL'] = ('b: constant + plane', 'alternatives a (constant), c (quadratic)')
h0['SKYC0'] = (CEL['b']['c0'], '[ADU/s G_cam] sky constant')
h0['SKYGU'] = (CEL['b']['gu'], '[ADU/s per Rsun] gradient along +x')
h0['SKYGV'] = (CEL['b']['gv'], '[ADU/s per Rsun] gradient along +row')
h0['SKYFLOOR'] = (mc.SIGMA_SKY_FLOOR_BSOL, '[Bsun] floor of the sky uncertainty')
h0['SYSRELC'] = (mc.sis_rel_constant(), 'constant relative systematic (quadrature)')
for i, (kk, vv) in enumerate(mc.SIS_REL.items()):
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
for i, (kk, vv) in enumerate(mc.BITS.items()):
    h0[f'FLAGB{int(math.log2(vv))}'] = (kk, f'bit value {vv}')
for c in com_primari:
    h0['COMMENT'] = c
h0['COMMENT'] = 'Extensions: MSB_NOEXT, SIGMA_STAT, SIGMA_SYS, SIGMA_SKY, SKY, AIRMASS, WVIXEN, FLAGS.'
h0['COMMENT'] = 'Code: 4-Photoshop/3-RECERCA/tools/msb_calibrat_20261011 (msb_comu.py, p2_mapa.py).'
hdus = [fits.PrimaryHDU(B['MSB'], header=h0)]
desc = {
    'MSB_NOEXT': ('MSB', 'same map WITHOUT the extinction correction (E = 1)'),
    'SIGMA_STAT': ('MSB', 'statistical 1-sigma: kappa*sqrt(wv^2 vV + ws^2 vS)*G_cam*FACG*E, binned sqrt(sum s^2)/4'),
    'SIGMA_SYS': ('MSB', 'systematic 1-sigma: zero point, drift, colour, flat, linearity, extinction band, sky'),
    'SIGMA_SKY': ('MSB', 'sky-model part of SIGMA_SYS: max|alt - adopted| (floor 1e-9 Bsun) * FACG * E'),
    'SKY': ('Bsun', 'adopted sky model (b) in Bsun, NOT extinction corrected (atmospheric light)'),
    'AIRMASS': ('', 'Kasten-Young airmass per pixel (refracted altitude) at DATE-OBS'),
    'WVIXEN': ('', 'Vixen weight of the fusion (1 = Vixen only; < 0.99 Sony scaled by rho)'),
    'FLAGS': ('', 'uint8 bit field, see FLAGB* keywords in the primary header'),
}
for nom, (bu, dd) in desc.items():
    h = cap_comu(hdr, nom, bu, dd)
    h['COMMENT'] = dd
    if nom == 'FLAGS':
        for kk, vv in mc.BITS.items():
            h['COMMENT'] = f'bit {int(math.log2(vv))} (value {vv}) {kk}: {mc.DESC_BITS[kk]}'
    hdus.append(fits.ImageHDU(B[nom], header=h))
FITS = mc.MAPA / 'msb_mapa_2x2.fits'
fits.HDUList(hdus).writeto(FITS, overwrite=True, output_verify='exception')
print(f'FITS escrit ({time.time() - T0:.0f} s)', flush=True)
# relectura amb sunpy: la mateixa prova sobre el fitxer escrit
with fits.open(FITS) as hl:
    m2 = sunpy.map.Map(np.asarray(hl[0].data), hl[0].header)
    noms_ext = [hh.name for hh in hl]
c2 = m2.pixel_to_world((p1 - 1) * u.pix, (p2 - 1) * u.pix)
sep2 = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=c2.frame).separation(c2).to(u.rad).value
prova_wcs['fitxer_relegit_max_err_r'] = float(np.max(np.abs(np.tan(sep2) * 206264.80624709636 / mc.RSOL_ARCSEC - R_)))
prova_wcs['fitxer_relegit_unitat_sunpy'] = str(m2.unit)
prova_wcs['extensions'] = noms_ext
rep = dict(guio='p2_mapa.py', data_execucio=time.strftime('%Y-%m-%dT%H:%M:%S'), temps_s=time.time() - T0,
           forma_ple=[H, W], forma_agrupat=[Hb, Wb], recompte_flags_ple=recompte, prova_wcs=prova_wcs,
           CD=CD.tolist(), CRPIX=CRPIX, observador=dict(HGLN_OBS=float(obs.lon.deg), HGLT_OBS=float(obs.lat.deg), DSUN_OBS=float(obs.radius.to(u.m).value)),
           X_sol=MA.X_sol, h_sol=MA.h_sol)
json.dump(rep, open(mc.MAPA / 'PROVES_P2.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('fet', json.dumps(rep, ensure_ascii=False, default=float)[:2000])
