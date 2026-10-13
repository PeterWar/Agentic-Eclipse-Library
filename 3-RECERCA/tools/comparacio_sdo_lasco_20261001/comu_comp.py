"""Mòdul comú de la comparació amb SDO/AIA, SOHO/LASCO i K-Cor (01-10-2026).

Tota imatge es descriu amb la seva geometria solar:
  centre del Sol (x, fila) en píxels de l'array tal com es carrega,
  R☉ en píxels (vist des del seu observador),
  vectors unitaris del nord solar i de l'est solar en coordenades (x, fila) de l'array.
Un punt de la corona es dona com (r en R☉, PA en graus des del nord solar cap a l'est).
Així el SOHO (a L1, R☉ = 957,2″) i la Terra (946,7″) es comparen sense biaix d'escala.
Cap píxel de cap font no es modifica: només es remostreja per comparar."""
import json, math, warnings
from pathlib import Path
import numpy as np
from scipy import ndimage as nd
warnings.filterwarnings('ignore')

ARREL = Path(__file__).resolve().parents[3]
DADES = ARREL / '3-RECERCA/data/externes_20261001'
RES = ARREL / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001'
VISTES = RES / 'vistes'
GEO = json.load(open(RES / 'GEOMETRIA_FINAL.json'))


class Geo:
    def __init__(s, nom, cx, cy, rsun_px, nord, est, data_utc, observador):
        s.nom, s.cx, s.cy, s.R = nom, float(cx), float(cy), float(rsun_px)
        s.n = np.asarray(nord, float) / np.linalg.norm(nord)
        s.e = np.asarray(est, float) / np.linalg.norm(est)
        s.data, s.obs = data_utc, observador

    def px(s, r, pa_deg):
        """(r R☉, PA°) -> (x, fila) a l'array."""
        pa = np.radians(pa_deg)
        dx = r * s.R * (np.cos(pa) * s.n[0] + np.sin(pa) * s.e[0])
        dy = r * s.R * (np.cos(pa) * s.n[1] + np.sin(pa) * s.e[1])
        return s.cx + dx, s.cy + dy

    def polar(s, x, y):
        """(x, fila) -> (r R☉, PA°): inversa exacta de px().
        ⛔ Revisió de Codex (01-10): a la final, el nord i l'est formen 90,43° (la placa és afí per la refracció amb el Sol a 9°).
        Amb productes escalars, polar(px()) fallava fins a 0,43° i 0,75 % en radi (3,3 px al limbe, 19,9 px a 6 R☉).
        Es resol el sistema [n e]·(a, b) = (dx, dy) amb la inversa de la matriu."""
        dx, dy = (np.asarray(x) - s.cx) / s.R, (np.asarray(y) - s.cy) / s.R
        det = s.n[0] * s.e[1] - s.e[0] * s.n[1]
        a = (s.e[1] * dx - s.e[0] * dy) / det
        b = (-s.n[1] * dx + s.n[0] * dy) / det
        return np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360


def prova_geo():
    """Prova d'anada i tornada polar(px(r, PA)) == (r, PA) per a la geometria afí de la final i per a una d'ortogonal."""
    rr = np.array([1.0, 1.05, 2.0, 6.0, 9.0]); pp = np.array([0.0, 37.0, 116.0, 277.0, 359.0])
    g = Geo('final', GEO['sol_px_efemeride'][0], GEO['sol_px_efemeride'][1], GEO['R_sol_px'], GEO['nord_solar'], GEO['est_solar'], '', '')
    for gg in (g, Geo('ortogonal', 511.5, 511.5, 394.7, (0, 1), (-1, 0), '', '')):
        x, y = gg.px(rr, pp); r2, p2 = gg.polar(x, y)
        dp = (p2 - pp + 180) % 360 - 180
        assert np.allclose(r2, rr, rtol=1e-12, atol=1e-12) and np.allclose(dp, 0, atol=1e-9), (gg.nom, r2, p2)
    ang = np.degrees(np.arccos(np.clip(np.dot(g.n, g.e), -1, 1)))
    return f'prova_geo OK (angle nord–est de la final: {ang:.4f}°)'


def mostreja(img, geo, r, pa, ordre=1, fora=np.nan):
    """Valors de img (2D) a les posicions (r, PA) donades (arrays de la mateixa forma)."""
    x, y = geo.px(r, pa)
    return nd.map_coordinates(img.astype(np.float32), [y, x], order=ordre, mode='constant', cval=fora, prefilter=False)


def a_marc(img, geo_font, geo_desti, forma, ordre=1, pas=1.0, x0=0.0, y0=0.0):
    """Remostreja img (geo_font) al marc de geo_desti (forma = (files, columnes)).
    pas > 1: graella reduïda del destí (cada píxel nou = pas píxels del destí, començant a (x0, y0))."""
    yy, xx = np.mgrid[0:forma[0], 0:forma[1]].astype(np.float64)
    r, pa = geo_desti.polar(x0 + xx * pas, y0 + yy * pas)
    return mostreja(img, geo_font, r, pa, ordre=ordre)


# ------------------------------------------------------------ la imatge final (V121/V123)
def geo_final(via='efemeride'):
    """via='efemeride': centre de la Lluna mesurat − desplaçament DE421 (geometria de la Vixen, la de la corona interior);
    via='estrelles': centre del Sol de la placa del llenç portat amb les estrelles de la V120."""
    c = GEO['sol_px_efemeride'] if via == 'efemeride' else GEO['sol_px']
    return Geo('final', c[0], c[1], GEO['R_sol_px'], GEO['nord_solar'], GEO['est_solar'], '2026-08-12T18:28:49', 'Mirador Final 2')


def carrega_final(nom='e4_nova_v121.npy'):
    """La final de Pere (V123 = V121 + estrelles reals), 16 bits Adobe RGB, files avall."""
    return np.load(ARREL / 'Sortides/estrelles_reals_20260930' / nom, mmap_mode='r')


def lluminancia(rgb16):
    """Lluminància relativa (coeficients d'Adobe RGB sobre els valors codificats; només per comparar estructura)."""
    a = np.asarray(rgb16, dtype=np.float32) / 65535.0
    return 0.2974 * a[..., 0] + 0.6273 * a[..., 1] + 0.0753 * a[..., 2]


# ------------------------------------------------------------ SDO/AIA (sinòptiques de nivell 1,5)
def carrega_aia(hhmm, ona):
    from astropy.io import fits
    f = DADES / f'sdo_aia/AIA20260812_{hhmm}_{ona}.fits'
    h = fits.open(f)[-1]; d = h.data.astype(np.float32); hd = h.header
    rsun = float(hd['RSUN_OBS']) / float(hd['CDELT1'])
    # nivell 1,5: nord solar = +y (fila creixent), oest = +x; centre = CRPIX − 1
    g = Geo(f'AIA {ona}', hd['CRPIX1'] - 1, hd['CRPIX2'] - 1, rsun, (0, 1), (-1, 0), hd['T_OBS'], 'SDO')
    return d / float(hd['EXPTIME']), g


# ------------------------------------------------------------ SOHO/LASCO (nivell 0,5)
R_SOL_SOHO = 957.22   # ″, JPL Horizons (SOHO a 1,002097 UA), 12-08-2026 18:24–18:36 UTC


def carrega_lasco(fitxer):
    """Nivell 0,5 amb la geometria de la capçalera (centre CRPIX, gir CROTA, escala CDELT) llegida amb sunpy."""
    import sunpy.map
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    m = sunpy.map.Map(str(DADES / 'soho_lasco' / fitxer))
    c = m.world_to_pixel(SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=m.coordinate_frame))
    n = m.world_to_pixel(SkyCoord(0 * u.arcsec, 1000 * u.arcsec, frame=m.coordinate_frame))
    w = m.world_to_pixel(SkyCoord(1000 * u.arcsec, 0 * u.arcsec, frame=m.coordinate_frame))
    cx, cy = float(c.x.value), float(c.y.value)
    nord = (float(n.x.value) - cx, float(n.y.value) - cy); oest = (float(w.x.value) - cx, float(w.y.value) - cy)
    esc = float(m.scale.axis1.value)    # ″/px
    hd = m.meta
    d = m.data.astype(np.float32) - float(hd.get('offset', 0.0))
    d = d / float(hd['exptime'])
    g = Geo(f"LASCO {hd['detector']}", cx, cy, R_SOL_SOHO / esc, nord, (-oest[0], -oest[1]),
            m.date.isot, 'SOHO (L1)')
    return d, g, hd


# ------------------------------------------------------------ K-Cor (GIF del HAO; nord amunt, est a l'esquerra)
def carrega_kcor(nom):
    from PIL import Image
    a = np.asarray(Image.open(DADES / 'kcor' / nom).convert('L')).astype(np.float32)
    R = 127.791 if '_nrgf' in nom else 170.394       # cercle de punts «circle = photosphere», mesurat (residu 0,2 px)
    return a, Geo('K-Cor', 255.5, 255.5, R, (0, -1), (-1, 0), nom[:15], 'Mauna Loa')


# ------------------------------------------------------------ eines de visualització
def nrgf(img, geo, rmin, rmax, nr=400, npa=720, valid=None):
    """Filtre radial normalitzant (Morgan i Habbal): (I − mitjana a r) / desviació a r, calculat a la mateixa imatge.
    Retorna una funció que aplica la normalització a qualsevol (r, valor)."""
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    r, _ = geo.polar(xx, yy)
    m = np.isfinite(img) & (r >= rmin) & (r <= rmax)
    if valid is not None: m &= valid
    edges = np.linspace(rmin, rmax, nr + 1); k = np.digitize(r[m], edges) - 1
    v = img[m]; mu = np.array([np.nanmedian(v[k == i]) if np.any(k == i) else np.nan for i in range(nr)])
    sd = np.array([1.4826 * np.nanmedian(np.abs(v[k == i] - mu[i])) if np.any(k == i) else np.nan for i in range(nr)])
    rc = 0.5 * (edges[1:] + edges[:-1]); ok = np.isfinite(mu) & np.isfinite(sd) & (sd > 0)
    def aplica(rr, vv):
        return (vv - np.interp(rr, rc[ok], mu[ok])) / np.interp(rr, rc[ok], sd[ok])
    return aplica


def a8(a, lo, hi, gamma=1.0):
    t = np.clip((np.asarray(a, np.float32) - lo) / (hi - lo), 0, 1)
    t = np.where(np.isfinite(t), t, 0)
    return (255 * t ** gamma).astype(np.uint8)
