"""msb_comu · Mòdul comú del mapa calibrat de la corona en brillantor solar mitjana (MSB = B/B☉).

Eclipsi total del 12-08-2026, Mirador Final 2 (42,299407 N; −5,02503 E; 798 m). Encàrrec «mapa-msb» (11-10-2026).
Proposta rebuda en la revisió de l'article: la corona en unitats de la brillantor mitjana del disc solar, fins al Sol.

El fan servir altres guions (import msb_comu). Importar-lo no escriu res ni llegeix cap fitxer gros.

Què hi ha:
  - rutes (ARREL = 4-Photoshop) i la memòria cau b3 de la V42 (a la Paperera de Pere, NOMÉS LECTURA, amb mmap);
  - geometria del llenç: centre del Sol, R☉ en px, nord i est solars afins (90,5° entre ells), amb polar() inversa exacta;
  - Lluna, franja del moviment lunar, buit del limbe, fantasma de la Sony, protuberàncies, cercle inscrit;
  - inversió del color als canals natius de la càmera: u_cam = M⁻¹·(u/g) ⊘ wb (exacta i lineal per píxel);
  - factor del punt zero (verd de la càmera) a MSB, extinció diferencial, massa d'aire per píxel (Kasten–Young);
  - models de cel i bits de FLAGS;
  - calcul_bloc(): tots els plans d'un bloc de files.

Unitats: el compost és en ADU/s per píxel natiu de la R6 III (Vixen), per canal, sRGB lineal (CIENCIA).
⛔ Normes: res inventat (NaN on no hi ha dada), la franja lunar i el buit del limbe no entren a cap ajust ni comparació.
"""
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

# ------------------------------------------------------------------------------------------------ rutes
ARREL = Path(__file__).resolve().parents[3]                       # …/4-Photoshop
EINES = Path(__file__).resolve().parent
RES = ARREL / '3-RECERCA/resultats/msb_calibrat_20261011'
MAPA = RES / 'mapa'
_GEOF = ARREL / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001/GEOMETRIA_FINAL.json'
_MARS = ARREL / '3-RECERCA/resultats/ia_output/apod_anotada_20260918/mars_final.json'
_ESTR = ARREL / '3-RECERCA/resultats/ia_output/apod_anotada_20260918/estrelles_final.json'
_ZPDIR = ARREL / '3-RECERCA/resultats/derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17'
CR3_MATRIU = ARREL / '0-RAW/Vixen R6III/Vixen Fase totalitat/572A2955.CR3'   # primer CR3 de la totalitat (comu.matriu_srgb)
_GHOST_GEOM = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v36_rgb_dependencies/geometry.json'

# Memòria cau b3 de la V42. Des del 03-10 és a la Paperera de Pere. ⛔ Només lectura: mai escriure, moure ni esborrar res.
_CAU_SUB = 'Desktop/Eclipse/4-Photoshop/3-RECERCA/resultats/v97_refundacio_20260924/cadena_raw/b3_baseline/cau'
SHA_CAU = {   # = B3_V42_FROZEN.json «references» (2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/)
    'fusion_total_v42.npy': '38998f9bcdbd5880e88990d07b502573dcf1916c109b554ffd24d61e3dea3072',
    'weight_vixen_v42.npy': 'f0d57ad2eba4ad2dbcac19072708edcde306265a2beaa248f239e8c0f7f02b42',
    'support_v42.npy': '72f67465aa43a26931a96a016c5a72e67ecf0fa66599bdd3d97abd947cfd8e4a',
    'var_vixen_v42.npy': '82b9ee6cca2e3a91c30708090aa9c9f21beccefd6a6c120e9d91b2c1bf70ac0f',
    'var_sony_v42.npy': 'e840e392f2a566323d40724f412d3048e8cb59bbd3c311c296bbe900a09ee630',
    'rho_v42.npy': 'c0ed7a022b461a089f2a81b163a4e94f2050597a5f64a43ab65adee13b6d8fe6',
    'sony_corrected_total_v42.npy': '2642f2a6880481140abf63ac31a673790cc8e85ca208b18c029eaff8cf021bbb',
}
H, W = 7506, 10551


def troba_cau():
    """La carpeta de la memòria cau: MSB_CAU (variable d'entorn) → la ruta original (si Pere la restaura) → la Paperera."""
    cands = []
    if os.environ.get('MSB_CAU'):
        cands.append(Path(os.environ['MSB_CAU']))
    cands.append(ARREL / '3-RECERCA/resultats/v97_refundacio_20260924/cadena_raw/b3_baseline/cau')
    cands.append(Path.home() / '.Trash/Eclipse_neteja_20261003/resultats_v' / _CAU_SUB)
    for c in cands:
        if (c / 'fusion_total_v42.npy').is_file():
            return c
    raise SystemExit("No trobo fusion_total_v42.npy. Si Pere ha buidat la Paperera, cal refer la memòria cau b3 "
                     "(cadena_raw a2 + a10) o dir on és amb MSB_CAU=<carpeta>.")


def obre_cau():
    """Les matrius de la cau, en mmap de NOMÉS LECTURA."""
    c = troba_cau()
    noms = ['fusion_total_v42', 'weight_vixen_v42', 'support_v42', 'var_vixen_v42', 'var_sony_v42']
    return {n: np.load(c / f'{n}.npy', mmap_mode='r') for n in noms}


def sha256(ruta, bloc=1 << 24):
    h = hashlib.sha256()
    with open(ruta, 'rb') as fh:
        for b in iter(lambda: fh.read(bloc), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ geometria
_GEO = json.load(open(_GEOF))
_MARSJ = json.load(open(_MARS))
OFF = np.array([1385.67, 1147.95 + 77])              # V121 → llenç de la V42 (c9_brillantor.py:24; g0_geometria.py:15)
SC = float(json.load(open(_ESTR))['plate_canvas']['arcsec_per_px'])   # 2,15035 ″/px del llenç (placa d'estrelles)
P_DEG = float(_GEO['P_deg'])                          # angle P del Sol (sunpy, 18:28:49)
RSOL_ARCSEC = float(_GEO['R_sol_arcsec'])             # 946,66″ (DE421, Mirador, 18:28:49)
SOL_XY = (float(_GEO['sol_px_efemeride'][0] + OFF[0]), float(_GEO['sol_px_efemeride'][1] + OFF[1]))
RSOL_PX = RSOL_ARCSEC / SC                            # 440,24 px
_N = np.array(_MARSJ['N'], float); _E = np.array(_MARSJ['E'], float)        # nord i est CELESTES al llenç (placa)
_cp, _sp = math.cos(math.radians(P_DEG)), math.sin(math.radians(P_DEG))
NORD_SOLAR = _cp * _N + _sp * _E                      # nord solar = nord celeste girat P cap a l'est (c9:26)
EST_SOLAR = -_sp * _N + _cp * _E
NORD_CEL = _N / np.linalg.norm(_N); EST_CEL = _E / np.linalg.norm(_E)
# Lluna de l'instant 18:28:49 (just després de C2) al llenç
LLUNA_XY = (float(_GEO['lluna_px'][0] + OFF[0]), float(_GEO['lluna_px'][1] + OFF[1]))
R_LLUNA_PX = float(_GEO['R_lluna_px'])                # 453,64 px
# Centres alternatius del Sol (per a la incertesa de geometria dels perfils; no s'adopten)
SOL_ALTERNATIUS = {
    'b3_a5_recompose': (5361.768111973117, 3775.747534140857),
    'placa_estrelles_llenc_V82_V114': (5361.8, 3775.0),
    'estrelles_V120_portat_GEOMETRIA_sol_px': (float(_GEO['sol_px'][0] + OFF[0]), float(_GEO['sol_px'][1] + OFF[1])),
}


class Geo:
    """Geometria solar d'una imatge (còpia de comu_comp.Geo, 01-10, amb la inversa exacta de Codex).
    (x, fila) ↔ (r en R☉, PA en graus des del nord solar cap a l'est). Eixos afins (no perpendiculars)."""

    def __init__(s, cx, cy, rsun_px, nord, est):
        s.cx, s.cy, s.R = float(cx), float(cy), float(rsun_px)
        s.n = np.asarray(nord, float) / np.linalg.norm(nord)
        s.e = np.asarray(est, float) / np.linalg.norm(est)
        s.det = s.n[0] * s.e[1] - s.e[0] * s.n[1]

    def px(s, r, pa_deg):
        pa = np.radians(pa_deg)
        a, b = r * np.cos(pa), r * np.sin(pa)
        return s.cx + s.R * (a * s.n[0] + b * s.e[0]), s.cy + s.R * (a * s.n[1] + b * s.e[1])

    def ab(s, x, y):
        """Components (nord solar, est solar) en R☉ (pla de projecció)."""
        dx, dy = (np.asarray(x, np.float64) - s.cx) / s.R, (np.asarray(y, np.float64) - s.cy) / s.R
        return (s.e[1] * dx - s.e[0] * dy) / s.det, (-s.n[1] * dx + s.n[0] * dy) / s.det

    def polar(s, x, y):
        a, b = s.ab(x, y)
        return np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360


def geo_llenc(centre=None):
    c = SOL_XY if centre is None else centre
    return Geo(c[0], c[1], RSOL_PX, NORD_SOLAR, EST_SOLAR)


def prova_geo():
    """Anada i tornada polar(px(r, PA)) == (r, PA) a 1e-12 (afí, exacta)."""
    g = geo_llenc()
    rr = np.array([1.0, 1.05, 1.5, 2.0, 6.0, 9.0, 12.0]); pp = np.array([0.0, 37.0, 116.0, 200.0, 277.0, 333.0, 359.9])
    x, y = g.px(rr, pp); r2, p2 = g.polar(x, y)
    dp = (p2 - pp + 180) % 360 - 180
    ok = bool(np.allclose(r2, rr, rtol=1e-12, atol=1e-12) and np.allclose(dp, 0, atol=1e-9))
    ang = float(np.degrees(np.arccos(np.clip(np.dot(g.n, g.e), -1, 1))))
    return dict(ok=ok, max_err_r=float(np.max(np.abs(r2 - rr))), max_err_pa_deg=float(np.max(np.abs(dp))), angle_nord_est_deg=ang)


# ------------------------------------------------------------------------------------------------ zones
R_BANDA_PX = 496.0          # franja del moviment lunar: fins a 496 px del centre lunar (AGENTS §4.6; research/165:7)
GAP_PX = 2.0                # buit sense dada a tocar del limbe (AGENTS §4.7): 2 px des de la zona lunar sense dada
GHOST_XY = (4878.66472396, 2549.20600753)   # GHOST_XY de la b3 = M_llenc_a_v23 · (2825, 3988, 1) (a5_recompose.py:44)
GHOST_R_PX = 320.0          # GHOST_OUT de la b3 (b3.py:9)
PROM_PA = (40.0, 116.0, 277.0)   # protuberàncies (RESULTAT 01-10, SDO 304 Å)
PROM_DPA = 6.0              # ± graus (predeclarat)
PROM_RMAX = 1.25            # R☉ (predeclarat)
# Sectors finals (PA central, ± graus). Els tres predeclarats, eixamplats perquè cobreixin TOTS els graus amb un excés de R/G de
# càmera > 10 % que va trobar la prova p0 (PROVES_P0.json, «protuberancies»): 116° fa 110–126° a 1,00–1,05 R☉; a 290–306° i a 334°
# hi ha excés vermell a 1,00–1,05 R☉ (no era a la llista del 01-10; probablement cromosfera a tocar del limbe, NO VERIFICAT).
# Tot plegat cau dins la franja lunar, que ja s'exclou; per sobre d'1,10 R☉ la prova no troba cap excés > 10 %.
PROM_SECTORS = ((40.0, 6.0), (116.0, 10.0), (277.0, 6.0), (298.0, 8.0), (334.0, 2.0))
WV_SONY = 0.99              # per sota, hi entra Sony·ρ
R_INSCRIT = None            # R☉; es mesura del suport (mesura_cercle_inscrit) i es desa a MAPA/ZONES.json

BITS = dict(NO_DATA=1, LIMB_GAP=2, MOON_BAND=4, PROMINENCE=8, SONY_GHOST=16, SONY_DOMINATED=32,
            OUTSIDE_INSCRIBED=64, SKY_LIMITED=128)
DESC_BITS = {
    'NO_DATA': 'no data: outside the sensor support, lunar disc, or a channel <= 0 (MSB = NaN)',
    'LIMB_GAP': f'within {GAP_PX:g} px of the lunar no-data region (the 1-2 px gap at the limb; MSB = NaN)',
    'MOON_BAND': f'lunar-motion band: data closer than {R_BANDA_PX:g} px to the lunar centre at 18:28:49 '
                 '(the Moon moved 28.5 px during totality; frames of different instants are mixed). Excluded from every fit and comparison',
    'PROMINENCE': f'H-alpha-dominated sectors (prominences at PA 40, 116, 277 deg and red limb excess), (PA, +/-deg) = {PROM_SECTORS}, '
                  f'r < {PROM_RMAX:g} Rsun: not scattered sunlight',
    'SONY_GHOST': f'Sony lens ghost zone (within {GHOST_R_PX:g} px of GHOST_XY)',
    'SONY_DOMINATED': f'Vixen weight wv < {WV_SONY:g}: Sony train scaled to Vixen units by a low-frequency rho (data, but a different camera)',
    'OUTSIDE_INSCRIBED': 'outside the largest Sun-centred circle fully covered by data (azimuthal statistics incomplete)',
    'SKY_LIMITED': 'MSB below the sky systematic (MSB < sigma_sky): informative only',
}
EXCLOU_PERFILS = (BITS['NO_DATA'] | BITS['LIMB_GAP'] | BITS['MOON_BAND'] | BITS['PROMINENCE'] |
                  BITS['SONY_GHOST'] | BITS['OUTSIDE_INSCRIBED'])


def zones():
    """Zones mesurades que escriu p0_zones_i_proves.py: cercle inscrit (ZONES.json) i buit del limbe (zona_lunar_gap.npz)."""
    f = MAPA / 'ZONES.json'
    d = json.load(open(f)) if f.is_file() else {}
    g = MAPA / 'zona_lunar_gap.npz'
    if g.is_file():
        z = np.load(g)
        d['gap'] = dict(x0=int(z['x0']), y0=int(z['y0']), mask=z['mask'])
    return d


# ------------------------------------------------------------------------------------------------ color
XYZ_SRGB = np.array([[3.24096994, -1.53738318, -0.49861076],
                     [-0.96924364, 1.87596750, 0.04155506],
                     [0.05563008, -0.20397696, 1.05697151]])
GUANY_CIENCIA = np.array([1.0 / 1.075, 1.0, 1.0 / 0.888])   # comu.MODES_COLOR['CIENCIA']['guany'] (blanc AM0)
# Valors verificats amb rawpy sobre 572A2955.CR3 (prova_color_matrius): M = càmera(balanç de dia) → sRGB lineal (dcraw)
M_R6 = np.array([[1.55964, -0.59029, 0.03065], [-0.17702, 1.68546, -0.50844], [-0.02502, -0.49626, 1.52128]])
WB_R6 = np.array([2.16776, 1.0, 1.35551])                    # daylight_whitebalance normalitzat a G


def matrius_rawpy(ruta=CR3_MATRIU):
    """Recalcula M i wb com comu.matriu_srgb i comu.balanc_dia (2-ARXIU/…/b3_v42_dependencies/comu.py:475-556)."""
    import rawpy
    with rawpy.imread(str(ruta)) as r:
        Mx = np.asarray(r.rgb_xyz_matrix)[:3, :3].astype(np.float64)
        dw = np.asarray(r.daylight_whitebalance, np.float64)
    cam_rgb = Mx @ np.linalg.inv(XYZ_SRGB)
    M = np.linalg.inv(cam_rgb / cam_rgb.sum(axis=1, keepdims=True))
    return M, np.array([dw[0] / dw[1], 1.0, dw[2] / dw[1]])


_MCACHE = {}


def matriu_inversa():
    """A = diag(1/wb) · M⁻¹ · diag(1/g): u_cam = A · u (per píxel). Es calcula de rawpy i es comprova amb les constants."""
    if 'A' not in _MCACHE:
        M, wb = matrius_rawpy()
        if not (np.allclose(M, M_R6, atol=6e-5) and np.allclose(wb, WB_R6, atol=6e-5)):
            raise SystemExit(f'La matriu de 572A2955.CR3 no és la verificada: {M} {wb}')
        _MCACHE['M'], _MCACHE['wb'] = M, wb
        _MCACHE['A'] = (np.diag(1.0 / wb) @ np.linalg.inv(M) @ np.diag(1.0 / GUANY_CIENCIA))
    return _MCACHE['A']


def canals_camera(F):
    """F (..., 3) del compost (sRGB lineal × guany CIENCIA) → canals natius de la càmera, ADU/s, sense balanç (float64)."""
    A = matriu_inversa()
    F = np.asarray(F, np.float64)
    return np.einsum('ij,...j->...i', A, F)


def verd_camera(F):
    """Només el verd natiu: G_cam = Σ_j A[1, j] · F_j (on hi ha el punt zero de les estrelles)."""
    A = matriu_inversa()
    F = np.asarray(F, np.float64)
    return A[1, 0] * F[..., 0] + A[1, 1] * F[..., 1] + A[1, 2] * F[..., 2]


# ------------------------------------------------------------------------------------------------ calibratge
FAC_G = 2.7714444383608502e-11      # B/B☉ per ADU/s i píxel verd (corona2.csv, r6, amb terme de color; research/75 §5.2)
FAC_G_REL_ERR = 0.10                # ±10 % declarat (75:279-280)
ZP_X_SOL = 6.0241478727562425       # massa d'aire del Sol a la qual es va avaluar el punt zero (zp2.json r6, Kasten–Young refractat)
ZP_EPOCA_UTC = '2026-08-12T18:29:18.6'   # època de zp.py per a la R6 (EPOCHS['r6'])


def factor_des_de_zp():
    """Recalcula FAC_G com corona2.py: π·(947,07″/escala)² / 10^(0,4·(ZP + 26,75 − 0,653·c))."""
    z = json.load(open(_ZPDIR / 'zp2.json'))['r6']
    s = json.load(open(_ZPDIR / 'final_solution.json'))['r6']['scale']
    rpx = 947.07 / s
    return math.pi * rpx ** 2 / 10 ** (0.4 * (z['ZPsun'] + 26.75 - 0.653 * z['c']))


# ------------------------------------------------------------------------------------------------ massa d'aire i extinció
LLOC = dict(lat=42.299407, lon=-5.02503, alt_m=798.0)
DATE_OBS = '2026-08-12T18:29:34'     # meitat de la totalitat (C2 18:28:41, C3 18:30:26)
DATE_BEG, DATE_END = '2026-08-12T18:28:41', '2026-08-12T18:30:26'
REFRACCIO = dict(pressure_hPa=930.0, temperature_C=20.0, relative_humidity=0.0, obswl_um=0.55)   # com zp.py (T 20 °C, P 930 hPa)
K_EXT = 0.40                         # mag per massa d'aire (model de comu.EXTINCIO, research/109 §12); predeclarat
K_BANDA = (0.35, 0.72)               # banda per a la capa sistemàtica (0,723 de les estrelles: contaminat de vinyetatge)


def kasten_young(h_deg):
    h = np.asarray(h_deg, np.float64)
    return 1.0 / (np.sin(np.radians(h)) + 0.50572 * (h + 6.07995) ** (-1.6364))


def altures_astropy(x, y, data=DATE_OBS, refractat=True):
    """Altura (graus) de punts del llenç, exacta amb astropy: (x, fila) → (r, PA solar) → separació i angle de posició
    celeste (PA + P) des del Sol topocèntric → AltAz. Projecció gnòmica: separació = atan(r·tan R☉)."""
    import astropy.units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body
    from astropy.time import Time
    loc = EarthLocation(lat=LLOC['lat'] * u.deg, lon=LLOC['lon'] * u.deg, height=LLOC['alt_m'] * u.m)
    t = Time(data, scale='utc')
    sol = get_body('sun', t, loc)
    g = geo_llenc()
    r, pa = g.polar(x, y)
    sep = np.degrees(np.arctan(np.asarray(r) * math.tan(math.radians(RSOL_ARCSEC / 3600.0))))
    p = sol.directional_offset_by((np.asarray(pa) + P_DEG) * u.deg, sep * u.deg)
    if refractat:
        fr = AltAz(obstime=t, location=loc, pressure=REFRACCIO['pressure_hPa'] * u.hPa,
                   temperature=REFRACCIO['temperature_C'] * u.deg_C, relative_humidity=REFRACCIO['relative_humidity'],
                   obswl=REFRACCIO['obswl_um'] * u.micron)
    else:
        fr = AltAz(obstime=t, location=loc, pressure=0 * u.hPa)
    aa = p.transform_to(fr)
    return aa.alt.deg, aa.az.deg


def altura_sol(data=DATE_OBS, refractat=True):
    h, az = altures_astropy(np.array([SOL_XY[0]]), np.array([SOL_XY[1]]), data=data, refractat=refractat)
    return float(h[0]), float(az[0])


class MassaAire:
    """Altura i massa d'aire per píxel: graella exacta d'astropy cada ~64 px i spline bicúbica (comprovada contra astropy)."""

    def __init__(s, fitxer=None):
        from scipy.interpolate import RectBivariateSpline
        f = Path(fitxer) if fitxer else MAPA / 'massa_aire_graella.npz'
        d = np.load(f)
        s.files, s.cols, s.alt = d['files'], d['cols'], d['alt']
        s.sp = RectBivariateSpline(s.files, s.cols, s.alt, kx=3, ky=3)
        s.h_sol = float(d['h_sol']); s.X_sol = float(kasten_young(s.h_sol))

    def altura_bloc(s, y0, y1, x0=0, x1=W):
        return s.sp(np.arange(y0, y1, dtype=np.float64), np.arange(x0, x1, dtype=np.float64), grid=True)

    def altura_punts(s, x, y):
        return s.sp.ev(np.asarray(y, np.float64), np.asarray(x, np.float64))


def construeix_graella_massa_aire(pas=64, refractat=True, data=DATE_OBS):
    files = np.unique(np.r_[np.arange(0, H, pas), H - 1]).astype(np.float64)
    cols = np.unique(np.r_[np.arange(0, W, pas), W - 1]).astype(np.float64)
    yy, xx = np.meshgrid(files, cols, indexing='ij')
    alt, _ = altures_astropy(xx.ravel(), yy.ravel(), data=data, refractat=refractat)
    h_sol, az_sol = altura_sol(data=data, refractat=refractat)
    return dict(files=files, cols=cols, alt=alt.reshape(yy.shape), h_sol=h_sol, az_sol=az_sol)


def factor_extincio(X, X_sol, k=K_EXT):
    """E = 10^(0,4·k·(X − X☉)): porta cada píxel a la massa d'aire del Sol, on viu el punt zero. S'aplica DESPRÉS de restar el cel."""
    return 10.0 ** (0.4 * k * (np.asarray(X) - X_sol))


# ------------------------------------------------------------------------------------------------ cel
def coef_cel():
    f = MAPA / 'CEL.json'
    if not f.is_file():
        raise SystemExit('Falta MAPA/CEL.json (l\'escriu mapa_msb.py, pas del cel)')
    return json.load(open(f))


def cel_model(x, y, model, c):
    """Cel en ADU/s de G_cam. Coordenades normalitzades: u = (x − cx)/R☉, v = (fila − cy)/R☉.
    a: constant · b: constant + pla (adoptat) · c: quadràtic ajustat fora de 4 R☉."""
    u = (np.asarray(x, np.float64) - SOL_XY[0]) / RSOL_PX
    v = (np.asarray(y, np.float64) - SOL_XY[1]) / RSOL_PX
    if model == 'a':
        return np.full(np.broadcast(u, v).shape, c['a']['c0'])
    if model == 'b':
        p = c['b']
        return p['c0'] + p['gu'] * u + p['gv'] * v
    if model == 'c':
        q = c['c']['coef']
        return q[0] + q[1] * u + q[2] * v + q[3] * u * u + q[4] * u * v + q[5] * v * v
    raise ValueError(model)


SIGMA_SKY_FLOOR_BSOL = 1e-9          # B☉, terra de la incertesa del cel (≈ 36 ADU/s de G_cam)

# ------------------------------------------------------------------------------------------------ incerteses
# Fraccions (1σ) del pressupost sistemàtic multiplicatiu. Cada una amb la seva font.
SIS_REL = {
    'zero_point_and_colour_term': 0.10,      # research/75 §5.2 (±10 %)
    'transparency_drift_in_totality': 0.04,  # f2.py:256: la transparència va baixar un 8 % → ±4 % (INFERIT)
    'colour_inversion_and_chain': 0.025,     # reproducció del perfil de research/76 a 1,5–5 R☉ (scout: −1,4…+2,4 %); es revisa al guió
    'flat_field': 0.016,                     # research/75:204
    'linearity': 0.0013,                     # research/75
}
KAPPA_DOG = 7.92   # σ per píxel = κ·√var per a soroll blanc: la var de la b3 és la del DoG(1,5−3 px) de ln G (var DoG/var = 0,0159)


def sis_rel_constant():
    return float(math.sqrt(sum(v * v for v in SIS_REL.values())))


# ------------------------------------------------------------------------------------------------ el bloc
def calcul_bloc(y0, y1, cau, ma, cel_c, zones_d, A=None, k=K_EXT, centre=None):
    """Tots els plans d'un bloc de files [y0, y1) a resolució plena. Retorna un dict de float32/uint8.
    cau: obre_cau(); ma: MassaAire(); cel_c: coef_cel(); zones_d: zones() (amb 'mascara_lluna' opcional)."""
    F = np.asarray(cau['fusion_total_v42'][y0:y1], np.float32)
    sup = np.asarray(cau['support_v42'][y0:y1])
    wv = np.asarray(cau['weight_vixen_v42'][y0:y1], np.float64)
    vV = np.asarray(cau['var_vixen_v42'][y0:y1], np.float64)
    vS = np.asarray(cau['var_sony_v42'][y0:y1], np.float64)
    hh = y1 - y0
    yy = np.arange(y0, y1, dtype=np.float64)[:, None] * np.ones((1, W))
    xx = np.ones((hh, 1)) * np.arange(W, dtype=np.float64)[None, :]
    g = geo_llenc(centre)
    r, pa = g.polar(xx, yy)
    dada = sup & np.all(np.isfinite(F), axis=2) & np.all(F > 0, axis=2)
    G = verd_camera(F)                                                 # ADU/s, total (corona + cel)
    A_ = matriu_inversa()
    Rc = A_[0, 0] * F[..., 0].astype(np.float64) + A_[0, 1] * F[..., 1] + A_[0, 2] * F[..., 2]   # vermell natiu (variants i proves)
    # cel adoptat (b) i dispersió entre models
    Sa, Sb, Sc = (cel_model(xx, yy, m, cel_c) for m in ('a', 'b', 'c'))
    S = Sb
    sig_sky = np.maximum(np.maximum(np.abs(Sa - Sb), np.abs(Sc - Sb)), SIGMA_SKY_FLOOR_BSOL / FAC_G)
    # massa d'aire i extinció
    h = ma.altura_bloc(y0, y1)
    X = kasten_young(h)
    E = factor_extincio(X, ma.X_sol, k)
    net = G - S
    msb_noext = FAC_G * net
    msb = msb_noext * E
    # incertesa estadística: var relativa de ln G al DoG(1,5−3 px), σ48 px, per tren; ponderada amb els pesos de la fusió
    ws = np.where(np.isfinite(vS), 1.0 - wv, 0.0)
    tv = np.where(wv > 0, wv * wv * vV, 0.0)
    ts = np.where(ws > 0, ws * ws * vS, 0.0)
    vf = tv + ts
    vf = np.where(((wv > 0) & ~np.isfinite(vV)) | ((ws > 0) & ~np.isfinite(vS)), np.nan, vf)
    sig_stat = FAC_G * E * KAPPA_DOG * np.sqrt(vf) * G
    # sistemàtica
    rel_c = sis_rel_constant()
    rel_ext = np.maximum(np.abs(10 ** (0.4 * (K_BANDA[0] - k) * (X - ma.X_sol)) - 1),
                         np.abs(10 ** (0.4 * (K_BANDA[1] - k) * (X - ma.X_sol)) - 1))
    sig_sky_msb = FAC_G * E * sig_sky
    sig_sys = np.sqrt((rel_c * msb) ** 2 + (rel_ext * msb) ** 2 + sig_sky_msb ** 2)
    # flags
    fl = np.zeros((hh, W), np.uint8)
    fl[~dada] |= BITS['NO_DATA']
    rm = np.hypot(xx - LLUNA_XY[0], yy - LLUNA_XY[1])
    if 'gap' in zones_d:                                                   # buit del limbe (precalculat a la caixa lunar)
        gx0, gy0, gap = zones_d['gap']['x0'], zones_d['gap']['y0'], zones_d['gap']['mask']
        a0, a1 = max(y0, gy0), min(y1, gy0 + gap.shape[0])
        if a1 > a0:
            sub = np.zeros((hh, W), bool)
            sub[a0 - y0:a1 - y0, gx0:gx0 + gap.shape[1]] = gap[a0 - gy0:a1 - gy0]
            fl[sub & dada] |= BITS['LIMB_GAP']
    fl[dada & (rm < R_BANDA_PX)] |= BITS['MOON_BAND']
    for p0, dpa in PROM_SECTORS:
        dp = np.abs((pa - p0 + 180) % 360 - 180)
        fl[dada & (dp <= dpa) & (r < PROM_RMAX)] |= BITS['PROMINENCE']
    fl[dada & (np.hypot(xx - GHOST_XY[0], yy - GHOST_XY[1]) < GHOST_R_PX)] |= BITS['SONY_GHOST']
    fl[dada & (wv < WV_SONY)] |= BITS['SONY_DOMINATED']
    rins = zones_d.get('R_inscrit_Rsol')
    if rins is not None:
        fl[r > rins] |= BITS['OUTSIDE_INSCRIBED']
    nul = (fl & (BITS['NO_DATA'] | BITS['LIMB_GAP'])) > 0
    fl[~nul & (msb < sig_sky_msb)] |= BITS['SKY_LIMITED']
    out = dict(G_cam=G, R_cam=Rc, sky=S, sky_a=Sa, sky_c=Sc, sigma_sky_adu=sig_sky, X=X, h=h, E=E, msb=msb, msb_noext=msb_noext,
               sigma_stat=sig_stat, sigma_sys=sig_sys, sigma_sky_msb=sig_sky_msb, wv=wv, r=r, pa=pa)
    for kk in ('G_cam', 'R_cam', 'msb', 'msb_noext', 'sigma_stat', 'sigma_sys', 'sigma_sky_msb'):
        out[kk] = np.where(nul, np.nan, out[kk])
    out = {kk: (v.astype(np.float32) if isinstance(v, np.ndarray) and v.dtype == np.float64 else v) for kk, v in out.items()}
    out['flags'] = fl
    out['dada'] = dada
    return out
