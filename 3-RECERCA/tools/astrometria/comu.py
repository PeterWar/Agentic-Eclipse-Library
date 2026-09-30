"""Rutes i constants comunes de la cadena d'astrometria (placa d'estrelles,
calibratge absolut, deflexió) de l'eclipsi del 12-08-2026.

Contracte per a tots els scripts promoguts de `research/tools/astrometria/`:

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import comu

- Cap ruta de dades escrita a pèl als scripts: tot surt d'aquí, i tot es pot
  redirigir per variable d'entorn (és el que fa `pipeline_estrelles.sh --prova`).
- Cap intèrpret escrit a pèl (regla global de Pere).
- Els originals (RAW, darks) es llegeixen i prou.

Variables d'entorn (totes opcionals; el valor per defecte és la disposició de
l'Escriptori reorganitzada el 22-08-2026):

    DADES_300MM       ARW Sony A7RIIIA + 300 GM          ~/Desktop/Eclipse 2026/300mm A7RIIIA
    DADES_VIXEN_UNF   CR3 Vixen dins totalitat           ~/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat
    DADES_VIXEN       CR3 Vixen sencers                  ~/Desktop/Eclipse 2026/Vixen R6III
    DARKS_SONY        darks A7RIIIA                      ~/Desktop/Eclipse 2026/300mm A7RIIIA/Darks A7RIIIA Eclipse
    DARKS_R6          darks R6 III                       ~/Desktop/Eclipse 2026/Vixen R6III/Darks Canon R6III Eclipse
    CATALEGS          catàlegs astromètrics              ~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/catalegs
    HALO_PARAMS       paràmetres earthshine              ~/Desktop/Eclipse 2026/Derivats/Earthshine/Earthshine_FINAL/…
    EFEMERIDE         de440s.bsp                          ~/.cache/skyfield/de440s.bsp
    ESTRELLES_WORK    intermedis mutables                 ~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/_work
    ESTRELLES_OUT     productes vius                      ~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles
    APOD_OUT          lliurables de l'APOD                ~/Desktop/Eclipse 2026/Publicacio/APOD
"""
from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
ARREL_DADES = HOME / "Desktop/Eclipse 2026"


def _env(nom: str, defecte: Path) -> Path:
    v = os.environ.get(nom)
    return Path(v).expanduser() if v else defecte


# ---------------------------------------------------------------- dades (només lectura)
DADES_300MM = _env("DADES_300MM", ARREL_DADES / "300mm A7RIIIA")
DADES_VIXEN_UNF = _env(
    "DADES_VIXEN_UNF", ARREL_DADES / "Vixen R6III/Vixen Fase totalitat"
)
DADES_VIXEN = _env("DADES_VIXEN", ARREL_DADES / "Vixen R6III")
DARKS_SONY = _env(
    "DARKS_SONY", ARREL_DADES / "300mm A7RIIIA/Darks A7RIIIA Eclipse"
)
DARKS_R6 = _env(
    "DARKS_R6", ARREL_DADES / "Vixen R6III/Darks Canon R6III Eclipse"
)
CATALEGS = _env(
    "CATALEGS", ARREL_DADES / "Derivats/Astrometria/Estrelles/catalegs"
)
HALO_PARAMS = _env(
    "HALO_PARAMS",
    ARREL_DADES / "Derivats/Earthshine/Earthshine_FINAL/earthshine_FINAL_halo_params.json",
)
EFEMERIDE = _env("EFEMERIDE", HOME / ".cache/skyfield/de440s.bsp")
HIP_MAIN = CATALEGS / "hip_main.dat"          # CDS I/239, 53 MB
TYC2 = CATALEGS / "tyc2.tsv"                  # VizieR I/259, 4,2°, VT<9
TYC2_DEEP = CATALEGS / "tyc2_deep.tsv"        # VizieR I/259, més profund (el del creuament)

# ---------------------------------------------------------------- sortides
ESTRELLES_WORK = _env(
    "ESTRELLES_WORK", ARREL_DADES / "Derivats/Astrometria/Estrelles/_work"
)
ESTRELLES_OUT = _env(
    "ESTRELLES_OUT",
    ARREL_DADES / "Derivats/Astrometria/Estrelles",
)
APOD_OUT = _env("APOD_OUT", ARREL_DADES / "Publicacio/APOD")


def work(sub: str) -> Path:
    """Directori de treball d'una subàrea (prediccio, sony, vixen, xmatch, esceptic, deflexio, apod). El crea."""
    p = ESTRELLES_WORK / sub
    p.mkdir(parents=True, exist_ok=True)
    return p


def out() -> Path:
    ESTRELLES_OUT.mkdir(parents=True, exist_ok=True)
    return ESTRELLES_OUT


def apod() -> Path:
    APOD_OUT.mkdir(parents=True, exist_ok=True)
    return APOD_OUT


def efemeride():
    """Carrega DE440s des de la cau (mai un load() relatiu, que baixa 32 MB al cwd)."""
    from skyfield.api import load
    if not EFEMERIDE.exists():
        raise FileNotFoundError(f"falta l'efemèride {EFEMERIDE}; baixa-la a ~/.cache/skyfield/")
    return load(str(EFEMERIDE))


# ---------------------------------------------------------------- lloc, instants
LLOC = dict(lat=42.299407, lon=-5.02503, alt_m=798.0)   # MIRADOR FINAL 2
T_PREDICCIO_UTC = (2026, 8, 12, 18, 29, 38)             # mig de la totalitat, predicció del camp
T_PLACA_SONY_UTC = (2026, 8, 12, 18, 29, 48.0)         # època de la placa Sony (final_solve)
T_PLACA_R6_UTC = (2026, 8, 12, 18, 29, 18.6)           # època de la placa R6 (final_solve)
C2_UTC = (2026, 8, 12, 18, 28, 46.0)
C3_UTC = (2026, 8, 12, 18, 30, 29.7)
TOTALITAT_S = 103.7
REFRACCIO = dict(temp_C=20.0, pressio_mbar=930.0)
CENTRE_CERCA_J2000 = dict(ra_deg=142.10549, dec_deg=14.90721)  # centre del Sol J2000
RADI_CERCA_DEG = dict(prefiltre=6.0, prediccio=4.0, xmatch=5.0)

# ---------------------------------------------------------------- Sol
R_SOL_ARCSEC = 947.07        # suns.json 947,068 (retall_estrella/animacio duen 946,66)
M_SOL = -26.75
BV_SOL = 0.653
DEFLEXIO_LIMBE_ARCSEC = 1.7516   # 4GM/(c²R☉) (deflexio.py 1,7508; APOD 1,7512)

# ---------------------------------------------------------------- sensors
SONY = dict(
    nom="Sony A7RIIIA + FE 300 mm f/2,8 GM",
    escala_vella=3.234, escala=3.2020,           # ″/px: la vella (radi lunar) i la de la placa (research/75)
    pedestal=512.0, sostre_valid=15600, blanc=16383, pixel_um=4.51, mida=(7968, 5320),
    guany_cadena=3.323, guany_publicat=3.41,     # e⁻/ADU: el que la cadena usa (gain.py) i el de research/75
    ref="DSC06993", centre_lluna_ref=(3894.1, 2765.6), r_sol_ref_px=293,
    centre_sol_placa=(3894.7, 2768.7), pa_nord=90.27, pa_est=358.64,
    fotogrames=[("DSC06984", 2.0), ("DSC06985", 1.0), ("DSC06987", 8.0), ("DSC06988", 1.0),
                ("DSC06991", 1.0), ("DSC06993", 8.0), ("DSC06996", 2.0), ("DSC06999", 2.0)],
    exclosos=["DSC06990 (moguda: la muntura va cedir durant l'exposició)",
              "DSC06988 (4,0σ sobre 6561 al scan)"],
    salt_px=(-227.6, +706.5), rotacio_salt_deg=0.138,
    zp=14.167, b_bsol_per_adu_s=1.134e-11, cel_mag_arcsec2=9.34,
)
R6 = dict(
    nom="Vixen VSD90SS + Canon R6 Mark III",
    escala_vella=2.158, escala=2.1495,
    pedestal=511.5, sostre_valid=15800, blanc=16383, pixel_um=5.17, mida=(6960, 4640), retall=(4638, 6958),
    guany_cadena=3.05, guany_publicat=5.08,      # wings.py duu 3,05; research/75 mesura 5,08 (verd)
    ref="572A2982", mascara="572A2983", centre_lluna_ref=(3577.1, 2266.1), r_lluna_ref_px=451,
    centre_sol_placa=(3570.8, 2267.1), pa_nord=57.19, pa_est=325.59,
    fotogrames=[("572A2978", 1.0), ("572A2979", 2.0), ("572A2980", 2.0), ("572A2981", 2.0),
                ("572A2982", 10.3), ("572A2983", 10.3), ("572A2984", 10.3), ("572A2996", 1.0)],
    deriva_arcsec_s=0.610, deriva_dir_deg=-45.0,
    zp=14.205, b_bsol_per_adu_s=2.772e-11, cel_mag_arcsec2=9.15,
)

# ---------------------------------------------------------------- números d'acceptació (research/75 §5, 77 §1)
ACCEPTACIO = dict(
    fonts_sony=38, fonts_r6=24, identificades_sony=38, identificades_r6=22,
    escala_sony=(3.2020, 0.002), escala_r6=(2.1495, 0.002),
    pa_nord_sony=(90.27, 0.05), pa_nord_r6=(57.19, 0.05),
    residu_med_px_sony=(0.54, 0.05), residu_med_px_r6=(0.32, 0.05),
    zp_sony=(14.167, 0.03), zp_r6=(14.205, 0.03),
    b_bsol_sony=(1.134e-11, 0.10), b_bsol_r6=(2.772e-11, 0.10),      # tolerància relativa
    quocient_corona_r6_sony=(0.95, 0.03),
    sigma_eps=(0.53, 0.05), deflexio_hip46345_arcsec=(0.662, 0.005),
    ales_psf_px_sony=13, ales_psf_px_r6=30, mag_limit=9.18,
)
