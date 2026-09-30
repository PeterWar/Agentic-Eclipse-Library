#!/usr/bin/env python3
"""HDR4: apilats per exposició del tren Vixen (VSD90SS + Canon R6 Mark III).

Pere va triar a `~/Desktop/HDR3` dotze CR3 de la totalitat del 12 d'agost de
2026, un per esglaó d'exposició, per fer-ne un HDR. Un sol fotograma va bé per a
les protuberàncies —canvien en segons— però no per a la corona: aquí es
substitueixen els de 572A2970 en endavant per l'APILAT de TOTS els fotogrames
de dins de la totalitat que tenen la mateixa exposició, i els tres primers
(1/3200, 1/500 i 1/125) es conserven tal qual.

Cada apilat es registra sobre la CORONA (el Sol) i no sobre la Lluna, i tots
surten en UNA MATEIXA geometria —el Sol al lloc on era a 572A2969, l'últim CR3
que es conserva sencer—, o sigui que els nou DNG i aquell CR3 queden alineats
en corona entre ells sense que el merge hagi d'alinear res (`--geometria
propia` dona, en canvi, cada apilat en la geometria del seu propi CR3). El
disc lunar de cada apilat és el del seu fotograma de referència, desplaçat
amb la seva corona. Mateixa escala de comptes que el CR3.

Aprenentatges de `research/71`, `75` i `76` que s'apliquen aquí:

* **la corona deriva a la taxa del Sol, no a la de les estrelles** (0,578 i no
  0,610 ″/s). El desplaçament de cada fotograma és el del model de centre solar
  del manifest de `Corona_HDR_Vixen` —limbe lunar + efemèride Lluna−Sol,
  ancorat a la placa estel·lar—, que la correlació de la corona valida a
  0,06–0,27 px. Aquí es torna a mesurar, apilat per apilat, com a comprovació.
* **corona i Lluna no comparteixen alineació.** El disc lunar de cada
  fotograma s'emmascara amb transició suau; el disc que es veu al resultat és
  el del fotograma de referència, i dins seu només hi contribueix ell.
* **calibratge en espai cru**: master de fosc per exposició amb el pedestal
  real (511,5, no el negre de libraw), mapa de PRNU, cap retall, cap balanç de
  blancs, cap desbayerat abans d'apilar.
* **drizzle sobre la reixa crua amb gota de 2,0 píxels de sortida**: és
  l'única amplada que dona partició de la unitat i no deixa escaquer.
* **el cel de la totalitat no és estacionari** (±20 %): abans de sumar
  s'anivella el fons de cada fotograma a un mateix valor, comú a TOTS els
  apilats (el de 572A2972), perquè dos apilats amb èpoques mitjanes diferents
  no portin cels diferents a la frontera on l'HDR canvia de l'un a l'altre.
* **i la transparència tampoc**: el Sol es pon i la massa d'aire puja de 6,02
  a 6,20 entre C2 i C3; els fotogrames tardans surten un 4–6 % més fluixos,
  multiplicativament i uniforme en azimut, i ho explica k = 0,40 mag per
  massa d'aire (mesurat aquí, 14 parelles). Cada membre es normalitza a la
  massa d'aire d'un instant comú, el de 572A2969, abans de sumar.
* **el pou d'aquest cos clava a 16382, no a 16383** (un fotograma de 10,3 s té
  1,26 milions de píxels a 16382 i 43.000 a 16383), **però Adobe posa el blanc
  a 13995** i Camera Raw tracta com a cremat tot el que hi passa: els apilats
  exclouen el mateix i declaren el mateix blanc, perquè es vegin com els CR3.

Etapes: `mesura` (QA del registre i de l'extinció) · `apila` (composa i
escriu els DNG) · `munta` (copia els tres CR3 i escriu el manifest) · `tot`.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import rawpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdr_corona_vixen as H  # noqa: E402  (manifest, masters, PRNU, constants)

# ---------------------------------------------------------------- constants

HDR3 = Path.home() / "Desktop/HDR3"
# HDR4_OUT permet una passada de prova en un altre directori (skill
# postprocessat-corona, 17-08-2026); sense la variable, usa el derivat canònic.
HDR4 = Path(
    os.environ.get("HDR4_OUT")
    or (Path.home() / "Desktop/Eclipse 2026/Derivats/Vixen/HDR4")
)
APILATS = HDR4 / "apilats"      # els DNG, a part dels CR3 perquè la carpeta es llegeixi
QA = HDR4 / "qa"

# Retall del sensor segons Canon (SensorLeft/TopBorder 172/108, 6960×4640).
# Els masters i el manifest van amb l'origen a (108, 172): és el mateix.
CROP_Y0, CROP_X0, ALT, AMPLE = 108, 172, 4640, 6960

# El pou físic clava a 16382 (mesurat: 1,26 M de píxels a 16382 contra 43 k a
# 16383 al fotograma de 10,3 s), però **Adobe posa el blanc de la R6 III a
# 13995** (llegit del DNG que en fa el DNG Converter 18.5: BlackLevel 512,
# WhiteLevel 13995, LinearResponseLimit 1) i Camera Raw tracta com a cremat
# tot el que hi passa. Perquè els apilats es vegin com els CR3 al mateix
# programa, s'exclou de la mitjana la mateixa cosa que Adobe descarta i el DNG
# declara el mateix blanc: un píxel cremat a tots els fotogrames surt blanc.
POU_FISIC = 16382
SAT_RAW = 13995             # llindar d'exclusió de mostres = blanc d'Adobe
POU_DNG = 13995             # WhiteLevel del DNG (el d'Adobe per a la R6 III)
PEDESTAL_DNG = 512          # BlackLevel; el pedestal real és 511,5

# Primer CR3 de l'HDR3 que se substitueix per un apilat
PRIMER_APILAT = "572A2970"

# Màscara lunar: radi operatiu del disc i transició suau (research/76 §5 bis)
R_LLUNA = H.R_LLUNA_PX          # 460 px
MARGE_LLUNA = 4.0
TRANSICIO_LLUNA = 14.0

# Anell on es mesura el fons de cada fotograma per anivellar-lo (research/76)
FONS_ANELL = H.FONS_ANELL       # (4,2 – 5,1 R☉)

# ⛔ Extinció atmosfèrica DINS de la totalitat. El Sol es pon: passa de 9,23°
# a 8,92° d'altura entre C2 i C3 i la massa d'aire de 6,02 a 6,20. Mesurat
# aquí, parella a parella dins de cada apilat (mateixos píxels, mateixa
# exposició, 60–80 s de diferència; ajust conjunt membre = a·referència + b
# sobre els perfils anulars d'1,05 a 4,8 R☉): els fotogrames tardans surten
# un 4–6 % més fluixos, i el factor és multiplicatiu i uniforme en azimut. Ho
# expliquen k = 0,402 ± 0,036 mag per massa d'aire (14 parelles, set
# exposicions), sense cap vinyetatge pel mig. Cada fotograma es normalitza a
# la massa d'aire d'un instant comú, el de 572A2969 —l'últim CR3 que HDR4
# conserva sencer—, perquè els dotze fitxers de l'HDR quedin a la mateixa
# escala fotomètrica.
K_EXTINCIO = 0.402              # mag per massa d'aire
NOM_EPOCA_COMUNA = "572A2969.CR3"


def massa_aire(t_rel: float) -> tuple[float, float]:
    """Massa d'aire (Kasten-Young) i altura aparent del Sol a C2 + t_rel s."""
    from skyfield.api import load, wgs84
    eph = H.carrega_efemeride()
    ts = load.timescale()
    terra, sol = eph["earth"], eph["sun"]
    lloc = terra + wgs84.latlon(H.LLOC[0], H.LLOC[1], elevation_m=H.LLOC[2])
    inst = (H.C2_LOCAL - dt.timedelta(hours=H.UTC_OFFSET_H)
            + dt.timedelta(seconds=float(t_rel)))
    t = ts.utc(inst.year, inst.month, inst.day, inst.hour, inst.minute,
               inst.second + inst.microsecond * 1e-6)
    h = lloc.at(t).observe(sol).apparent().altaz()[0].degrees
    X = 1.0 / (math.sin(math.radians(h)) + 0.50572 * (h + 6.07995) ** -1.6364)
    return X, h


def factor_extincio(t_rel: float, t_ref: float) -> float:
    """Factor pel qual s'ha de multiplicar un fotograma pres a C2+t_rel per
    portar-lo a la massa d'aire de C2+t_ref."""
    X, _ = massa_aire(t_rel)
    X0, _ = massa_aire(t_ref)
    return 10 ** (0.4 * K_EXTINCIO * (X - X0))


# Matrius de color d'Adobe per a aquest cos, llegides del perfil
# «Canon EOS R6 Mark III Adobe Standard.dcp» del Camera Raw d'aquest Mac
# (l'Adobe DNG Converter 17.5 instal·lat no coneix la R6 III i no pot
# convertir-ne cap CR3). Il·luminants: 1 = StdA (17), 2 = D65 (21).
UNIQUE_CAMERA_MODEL = "Canon EOS R6 Mark III"
COLOR_MATRIX_1 = [1.0273, -0.4611, 0.0139, -0.3922, 1.1425, 0.2856, -0.0231, 0.0839, 0.6645]
COLOR_MATRIX_2 = [0.8309, -0.1786, -0.1095, -0.4851, 1.2736, 0.2353, -0.0956, 0.1911, 0.5534]
FORWARD_MATRIX_1 = [0.4995, 0.3266, 0.1382, 0.2485, 0.7091, 0.0424, 0.108, 0.0004, 0.7167]
FORWARD_MATRIX_2 = [0.5045, 0.2415, 0.2184, 0.2854, 0.6442, 0.0704, 0.1324, 0.001, 0.6917]
# Exposició base d'Adobe per a la R6 III: 0,26, llegida del DNG que en fa el
# DNG Converter 18.5 (juntament amb BaselineNoise 0,8 i BaselineSharpness
# 1,25, que es copien perquè Camera Raw tracti l'apilat com un CR3 del cos).
BASELINE_EXPOSURE = (26, 100)
BASELINE_NOISE = (8, 10)
BASELINE_SHARPNESS = (125, 100)


def log(*a) -> None:
    print(*a, flush=True)


# ---------------------------------------------------------------- lectura

_master_cache: dict[str, np.ndarray] = {}
_prnu_cache: dict | None = None


def master_4640(e_nom: float) -> np.ndarray:
    """Master de fosc estès de 4638×6958 a 4640×6960 (dues files i dues
    columnes de vora, repetides: són pedestal i cap corona no hi arriba)."""
    k = H.clau_master(e_nom)
    if k not in _master_cache:
        m = H.master(e_nom)
        _master_cache[k] = np.pad(m, ((0, ALT - m.shape[0]), (0, AMPLE - m.shape[1])),
                                  mode="edge")
    return _master_cache[k]


def prnu_4640() -> dict | None:
    global _prnu_cache
    if _prnu_cache is None:
        g = H.prnu()
        _prnu_cache = {}
        if g:
            for (oy, ox), m in g.items():
                h_pla = (ALT - oy + 1) // 2
                w_pla = (AMPLE - ox + 1) // 2
                _prnu_cache[(oy, ox)] = np.pad(
                    m, ((0, h_pla - m.shape[0]), (0, w_pla - m.shape[1])), mode="edge")
    return _prnu_cache or None


def carrega(f: H.Fotograma) -> tuple[np.ndarray, np.ndarray]:
    """Mosaic calibrat en comptes per damunt del fosc (float32, 4640×6960) i
    màscara de saturació del sensor."""
    with rawpy.imread(str(H.SRC / f.nom)) as raw:
        cru = raw.raw_image[CROP_Y0:CROP_Y0 + ALT, CROP_X0:CROP_X0 + AMPLE]
        sat = cru >= SAT_RAW
        mos = cru.astype(np.float32) - master_4640(f.exp_nominal)
    g = prnu_4640()
    if g:
        for (oy, ox), m in g.items():
            mos[oy::2, ox::2] /= (1.0 + m)
    return mos, sat


def plans(mos: np.ndarray) -> dict[str, tuple[np.ndarray, int, int]]:
    return H.plans(mos)


def verd_mig(mos: np.ndarray) -> np.ndarray:
    """Pla verd a mitja resolució: el píxel (i,j) és el centre de la cel·la
    (2i+0,5, 2j+0,5) del sensor."""
    return 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2])


# ---------------------------------------------------------------- selecció

def apilats() -> list[dict]:
    """Un diccionari per CR3 de l'HDR3 a partir de PRIMER_APILAT: referència,
    exposició i tots els fotogrames de dins de la totalitat amb la mateixa."""
    fg = [f for f in H.llegeix_manifest() if f.usat]
    per_nom = {f.nom: f for f in fg}
    noms_hdr3 = sorted(p.name for p in HDR3.glob("*.CR3"))
    out = []
    for nom in noms_hdr3:
        if nom[:8] < PRIMER_APILAT:
            continue
        if nom not in per_nom:
            raise SystemExit(f"⛔ {nom} no és al manifest de la totalitat")
        ref = per_nom[nom]
        membres = sorted((f for f in fg if f.exp_s == ref.exp_s),
                         key=lambda f: f.t_rel_c2)
        out.append({"ref": ref, "exp_s": ref.exp_s, "membres": membres})
    return out


def etiqueta_exp(e: float) -> str:
    """1/30 → «1-30s», 10,3 → «10.3s», 2 → «2s»."""
    if e >= 1.0:
        return f"{e:g}s"
    return f"1-{round(1.0 / e):d}s"


_rang: dict[str, tuple[int, float]] | None = None


def rang_exposicio() -> dict[str, tuple[int, float]]:
    """Ordre global dels dotze fitxers de l'HDR3 per exposició DECREIXENT
    (01 = la més llarga) i la seva exposició real.

    ⛔ Photoshop, a «Load Files into Stack», posa la PRIMERA imatge de la
    llista a la capa de DALT (comprovat al Photoshop 27.9 amb tres fitxers de
    prova; el codi de `CreateImageStack.jsx` fa `stackElements.reverse()` i
    apila l'últim com a base). Amb els noms ordenats així, i la llista
    ordenada per nom, l'exposició més llarga queda a dalt.
    """
    global _rang
    if _rang is None:
        out = subprocess.run(
            ["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime",
             *map(str, sorted(HDR3.glob("*.CR3")))],
            capture_output=True, text=True, check=True).stdout
        exps = {}
        for linia in out.splitlines():
            nom, e = linia.split("\t")
            exps[nom[:8]] = H.exp_real(float(e))
        ordre = sorted(exps, key=lambda n: (-exps[n], n))
        _rang = {n: (i + 1, exps[n]) for i, n in enumerate(ordre)}
    return _rang


def sortida_nom(ap: dict) -> str:
    """«06_1-8s_572A2971_apilat4»: ordre global per exposició decreixent,
    exposició, CR3 de referència i nombre de fotogrames apilats. Els grups de
    protuberàncies porten el nom explícit."""
    if "nom" in ap:
        return ap["nom"]
    idx, e = rang_exposicio()[ap["ref"].nom[:8]]
    return f"{idx:02d}_{etiqueta_exp(e)}_{ap['ref'].nom[:8]}_apilat{len(ap['membres'])}"


def nom_copia_cr3(nom: str) -> str:
    """«10_1-125s_572A2969.CR3» per als CR3 que es conserven sencers."""
    idx, e = rang_exposicio()[nom[:8]]
    return f"{idx:02d}_{etiqueta_exp(e)}_{nom}"


# ---------------------------------------------------------------- mesura

def finestra(a: np.ndarray, cy: int, cx: int, L: int) -> np.ndarray:
    """Retall (2L×2L) centrat a (cy,cx), amb zeros on surt del fotograma."""
    out = np.zeros((2 * L, 2 * L), np.float32)
    y0, x0 = cy - L, cx - L
    ys, xs = max(y0, 0), max(x0, 0)
    ye, xe = min(y0 + 2 * L, a.shape[0]), min(x0 + 2 * L, a.shape[1])
    if ye > ys and xe > xs:
        out[ys - y0:ye - y0, xs - x0:xe - x0] = a[ys:ye, xs:xe]
    return out


# Suavitzat de les imatges auxiliars abans de correlacionar, píxels de mitja
# resolució (vegeu mesura_registre)
SIGMA_MESURA = 3.0

# Radi interior de la imatge auxiliar de registre, píxels de sensor des del
# centre solar. ⛔ Amb 490 px (el disc lunar més 30) la mesura de l'apilat de
# 1/8 s sortia +0,2 px desplaçada en x a les tres parelles i la de 1/4 s +0,35:
# entre 490 i 600 px hi ha les protuberàncies —saturades a partir de 1/8 s— i
# el que la Lluna en va descobrint entre un fotograma i el següent, que és
# estructura que es mou amb la LLUNA i no amb la corona. Amb 600 px les
# mateixes parelles cauen a ±0,04 px.
R_INT_MESURA = 600.0

# Finestres de mesura, en píxels de SENSOR relatius al centre solar (dx, dy, L).
# ⚠️ Només el centre és fiable: als costats, a 2–4 R☉, la corona de les
# exposicions curtes ja és soroll i la de les llargues queda dominada pel
# patró fix del sensor (pols i vinyetatge: no hi ha flats), i la correlació
# s'hi enganxa (mesurat: desplaçament ≈ 0 en coordenades de sensor a totes
# les exposicions). Per això la rotació de camp i el canvi de refracció
# diferencial no es poden mesurar aquí, i s'estimen: fins a 0,28 i 0,54 px
# a 3 R☉ sobre els 81 s de l'apilat més llarg. Per sota del FWHM (2,7 px).
FINESTRES = {
    "centre": (0, 0, 1000),
}


def radi_saturacio(f: H.Fotograma, sat: np.ndarray) -> float:
    """Radi (px de sensor des del centre solar) fins on el nucli és cremat:
    l'últim anell de 4 px amb més d'un 2 % de píxels saturats."""
    s = sat[0::2, 1::2] | sat[1::2, 0::2]
    r = H.anells(*s.shape, (f.sol_y - 0.5) / 2, (f.sol_x - 0.5) / 2) * 2
    r_max = 0.0
    for r0 in np.arange(R_LLUNA, 3.0 * H.R_SOL_PX, 4.0):
        m = (r >= r0) & (r < r0 + 4.0)
        if m.sum() and s[m].mean() > 0.02:
            r_max = r0 + 4.0
    return r_max


def auxiliar(f: H.Fotograma, mos: np.ndarray, sat: np.ndarray,
             r_int: float = R_INT_MESURA) -> np.ndarray:
    """Corona dividida pel seu perfil radial, a mitja resolució: el que s'ha
    d'alinear són les bagues i els plomalls, no el gradient. `r_int` és el
    radi interior en píxels de sensor."""
    g = verd_mig(mos) / f.exp_s
    s = sat[0::2, 1::2] | sat[1::2, 0::2]
    g = np.where(s, np.nan, g)
    cy, cx = (f.sol_y - 0.5) / 2, (f.sol_x - 0.5) / 2
    r_ext = min(cy, cx, g.shape[0] - cy, g.shape[1] - cx) - 2
    return H.normalitza_radial(g, cy, cx, r_int / 2, r_ext)


def mesura_registre(ap: dict, dades: dict[str, tuple]) -> list[dict]:
    """Residu del registre (mesurat − model) per fotograma i finestra.

    El desplaçament mesurat és el de la CORONA al sensor entre la referència i
    el fotograma; el model és `sol_f − sol_ref`. Es mesura per correlació de
    fase de les imatges auxiliars a la finestra central.

    ⛔ El radi interior s'adapta al nucli cremat: a les exposicions llargues el
    forat de saturació (NaN → 0) i el que hi ha just al seu voltant dominen la
    correlació i la mesura surt d'1 a 4 px del model. Amb r_int = 1,25 × radi
    de saturació (1 s → ~725, 2 s → ~800, 10,3 s → ~1100 px) i una finestra i
    un suavitzat més grans per als forats grans, els residus tornen a ≤ 0,1 px.
    """
    from scipy.ndimage import gaussian_filter
    from skimage.registration import phase_cross_correlation
    ref = ap["ref"]
    r_sat = {f.nom: radi_saturacio(f, dades[f.nom][1]) for f in ap["membres"]}
    r_int = max(R_INT_MESURA, 1.25 * max(r_sat.values()))
    aux_ref = auxiliar(ref, *dades[ref.nom], r_int=r_int)
    files = []
    for f in ap["membres"]:
        if f.nom == ref.nom:
            continue
        aux_f = auxiliar(f, *dades[f.nom], r_int=r_int)
        model = (f.sol_x - ref.sol_x, f.sol_y - ref.sol_y)
        for nom_w, (wx, wy, L) in FINESTRES.items():
            sig = SIGMA_MESURA
            if r_int > 800:
                L, sig = max(L, 1400), 2 * SIGMA_MESURA
            Lh = L // 2
            cy_r = int(round((ref.sol_y - 0.5) / 2 + wy / 2))
            cx_r = int(round((ref.sol_x - 0.5) / 2 + wx / 2))
            cy_f = int(round((f.sol_y - 0.5) / 2 + wy / 2))
            cx_f = int(round((f.sol_x - 0.5) / 2 + wx / 2))
            han = np.outer(np.hanning(2 * Lh), np.hanning(2 * Lh)).astype(np.float32)
            # ⛔ Sense suavitzar, la correlació de fase pesa igual totes les
            # freqüències i el soroll a escala de píxel —i el patró fix del
            # sensor— la tiben 0,25 px; amb σ = 3 px (mitja resolució) el
            # residu contra el model cau per sota de 0,1 px. La corona és
            # llisa: el que s'alinea són les bagues, no el gra.
            a = gaussian_filter(np.nan_to_num(finestra(aux_ref, cy_r, cx_r, Lh)), sig) * han
            b = gaussian_filter(np.nan_to_num(finestra(aux_f, cy_f, cx_f, Lh)), sig) * han
            if a.std() < 1e-6 or b.std() < 1e-6:
                continue
            desp, err, _ = phase_cross_correlation(a, b, upsample_factor=100,
                                                   normalization="phase")
            # desp = −(desplaçament del contingut de b respecte d'a) a mitja
            # resolució; el retall ja porta la diferència de centres del model
            mes_x = -desp[1] * 2 + (cx_f - cx_r) * 2
            mes_y = -desp[0] * 2 + (cy_f - cy_r) * 2
            files.append({"apilat": sortida_nom(ap), "ref": ref.nom, "fotograma": f.nom,
                          "exp_s": f.exp_s, "dt_s": f.t_rel_c2 - ref.t_rel_c2,
                          "finestra": nom_w, "r_int_px": r_int, "L_px": L, "sigma": sig,
                          "model_dx": model[0], "model_dy": model[1],
                          "mes_dx": mes_x, "mes_dy": mes_y,
                          "res_dx": mes_x - model[0], "res_dy": mes_y - model[1],
                          "error": float(err)})
    return files


def mesura_extincio(ap: dict, dades: dict[str, tuple]) -> list[dict]:
    """Per a cada membre, ajust conjunt `membre = a·referència + b` sobre els
    perfils anulars (mediana, anells de 0,05 R☉ d'1,05 a 4,8 R☉, fora del disc
    lunar i sense saturació) del pla verd, amb el membre registrat a la
    referència. `a` és la raó de transparència i `b` la diferència de cel;
    amb la massa d'aire de cadascun en surt el coeficient d'extinció."""
    from scipy.ndimage import shift as ndshift
    ref = ap["ref"]
    Gr = verd_mig(dades[ref.nom][0])
    sr = dades[ref.nom][1]
    sr = sr[0::2, 1::2] | sr[1::2, 0::2]
    h, w = Gr.shape
    yy = np.arange(h)[:, None]
    xx = np.arange(w)[None, :]
    rr = np.hypot(xx - (ref.sol_x - 0.5) / 2, yy - (ref.sol_y - 0.5) / 2) * 2 / H.R_SOL_PX
    lx = ref.lluna_mes_x if math.isfinite(ref.lluna_mes_x) else ref.lluna_x
    ly = ref.lluna_mes_y if math.isfinite(ref.lluna_mes_y) else ref.lluna_y
    rl = np.hypot(xx - (lx - 0.5) / 2, yy - (ly - 0.5) / 2) * 2
    Xr, hr = massa_aire(ref.t_rel_c2)
    files = []
    for f in ap["membres"]:
        if f.nom == ref.nom:
            continue
        G = verd_mig(dades[f.nom][0])
        s = dades[f.nom][1]
        s = s[0::2, 1::2] | s[1::2, 0::2]
        dx, dy = (ref.sol_x - f.sol_x) / 2, (ref.sol_y - f.sol_y) / 2
        Gs = ndshift(G, (dy, dx), order=1, mode="nearest")
        ss = ndshift(s.astype(np.float32), (dy, dx), order=0) > 0
        pr, pm = [], []
        for r0 in np.arange(1.05, 4.8, 0.05):
            m = (rr >= r0) & (rr < r0 + 0.05) & (rl > R_LLUNA + 15) & ~sr & ~ss
            if m.sum() > 300:
                pr.append(np.median(Gr[m]))
                pm.append(np.median(Gs[m]))
        x, y = np.array(pr), np.array(pm)
        a = b = math.nan
        for _ in range(4):
            if len(x) < 6:
                break
            (a, b), *_ = np.linalg.lstsq(np.c_[x, np.ones(len(x))], y, rcond=None)
            r_ = y - (a * x + b)
            sd = 1.4826 * np.median(np.abs(r_ - np.median(r_)))
            keep = np.abs(r_ - np.median(r_)) < 3 * max(sd, 1e-6)
            if keep.all() or keep.sum() < 6:
                break
            x, y = x[keep], y[keep]
        Xf, hf = massa_aire(f.t_rel_c2)
        dX = Xf - Xr
        k = -2.5 * math.log10(a) / dX if (abs(dX) > 1e-6 and a > 0) else math.nan
        files.append({"apilat": sortida_nom(ap), "ref": ref.nom, "fotograma": f.nom,
                      "exp_s": f.exp_s, "dt_s": f.t_rel_c2 - ref.t_rel_c2,
                      "X_ref": Xr, "X_fot": Xf, "dX": dX, "alt_ref_graus": hr,
                      "alt_fot_graus": hf, "a_transparencia": a,
                      "b_cel_ADU": b, "b_cel_ADU_s": b / f.exp_s, "k_mag_X": k,
                      "n_anells": int(len(x))})
    return files


def etapa_mesura(args) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    tots, tots_ext = [], []
    for ap in apilats():
        if args.nomes and not ap["ref"].nom.startswith(args.nomes):
            continue
        log(f"\n=== {sortida_nom(ap)}  exp {ap['exp_s']:.6g} s  "
            f"{len(ap['membres'])} fotogrames: "
            f"{', '.join(f.nom[:8] for f in ap['membres'])}")
        dades = {f.nom: carrega(f) for f in ap["membres"]}
        files = mesura_registre(ap, dades)
        for r in files:
            flag = ""
            if math.hypot(r["mes_dx"], r["mes_dy"]) < 1.5 and \
                    math.hypot(r["model_dx"], r["model_dy"]) > 4:
                flag = "  ⛔ enganxat al patró fix"
            elif math.hypot(r["res_dx"], r["res_dy"]) > 0.5:
                flag = "  ⚠️"
            log(f"  {r['fotograma'][:8]} Δt{r['dt_s']:+6.1f}s {r['finestra']:<6} "
                f"model ({r['model_dx']:+6.2f},{r['model_dy']:+6.2f}) "
                f"mesurat ({r['mes_dx']:+6.2f},{r['mes_dy']:+6.2f}) "
                f"residu ({r['res_dx']:+5.2f},{r['res_dy']:+5.2f}){flag}")
        tots.extend(files)
        ext = mesura_extincio(ap, dades)
        for r in ext:
            log(f"  {r['fotograma'][:8]} Δt{r['dt_s']:+6.1f}s ΔX {r['dX']:+.4f}  "
                f"transparència a={r['a_transparencia']:.4f}  cel b={r['b_cel_ADU_s']:+7.1f} ADU/s  "
                f"k={r['k_mag_X']:.3f} mag/X")
        tots_ext.extend(ext)
    with open(QA / "registre_mesures.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(tots[0].keys()))
        w.writeheader()
        w.writerows(tots)
    with open(QA / "extincio_mesures.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(tots_ext[0].keys()))
        w.writeheader()
        w.writerows(tots_ext)
    ks = np.array([r["k_mag_X"] for r in tots_ext if r["dt_s"] > 20 and np.isfinite(r["k_mag_X"])])
    if len(ks):
        log(f"\nk d'extinció (parelles amb Δt > 20 s): {ks.mean():.3f} ± {ks.std():.3f} "
            f"mag per massa d'aire (n={len(ks)}); el codi fa servir {K_EXTINCIO}")
    log(f"\n→ {QA/'registre_mesures.csv'}\n→ {QA/'extincio_mesures.csv'}")


# ---------------------------------------------------------------- apilat

def gota(pos0: float) -> tuple[int, list[float]]:
    """Gota d'amplada 2 (píxels de sortida) per a un pla de període 2.

    La mostra i del pla és a la posició `2i + pos0` de la reixa de sortida
    (pos0 = desplaçament del pla + 0,5, perquè la mostra és al centre del seu
    píxel). La gota [2i+pos0−1, 2i+pos0+1) cau sobre les files 2i+k0, 2i+k0+1
    i 2i+k0+2 amb uns pesos que NO depenen de i. Amb amplada exactament 2 sobre
    una reixa de període 2, cada píxel de sortida rep pes total 1 sigui quina
    sigui la fase: partició de la unitat, cap escaquer (research/76 §3).
    """
    a, b = pos0 - 1.0, pos0 + 1.0
    k0 = math.floor(a)
    ws = [max(0.0, min(b, k0 + k + 1) - max(a, k0 + k)) for k in range(3)]
    return k0, ws


def talls(n_in: int, off: int, n_out: int) -> tuple[slice, slice] | None:
    """Files de sortida `2i + off` (i = 0..n_in−1) que cauen dins [0, n_out):
    retorna (tall d'entrada, tall de sortida amb pas 2) o None."""
    i0 = max(0, math.ceil(-off / 2))
    i1 = min(n_in - 1, math.floor((n_out - 1 - off) / 2))
    if i1 < i0:
        return None
    return slice(i0, i1 + 1), slice(off + 2 * i0, off + 2 * i1 + 1, 2)


def fons_fotograma(f: H.Fotograma, mos: np.ndarray, escala: float) -> np.ndarray:
    """Fons per pla [R, G1, G2, B] a l'anell FONS_ANELL, en comptes, ja escalat
    per extinció."""
    v = []
    for nom in ["R", "G1", "G2", "B"]:
        pla, oy, ox = plans(mos)[nom]
        rr = H.anells(*pla.shape, (f.sol_y - oy) / 2, (f.sol_x - ox) / 2) * 2
        m = (rr > FONS_ANELL[0] * H.R_SOL_PX) & (rr < FONS_ANELL[1] * H.R_SOL_PX)
        v.append(float(np.median(pla[m])) * escala)
    return np.array(v)


# El fons comú de tots els apilats es pren del fotograma de 0,5 s 572A2972
# (C2+11,6 s): és la primera exposició prou llarga perquè el fons es mesuri
# amb precisió (265 comptes) i té el cel de tocar de C2, que és el més clar
# —anivellar-hi tots els altres vol dir AFEGIR pedestal, mai treure'n, o sigui
# que cap fotograma no queda amb el cel per sota de zero.
NOM_FONS_COMU = "572A2972.CR3"
_fons_comu: np.ndarray | None = None


def fons_comu() -> np.ndarray:
    """Fons objectiu per pla en comptes PER SEGON, comú a tots els apilats.

    ⛔ Sense un objectiu comú cada apilat es queda amb el cel de la seva època
    mitjana i els cels difereixen fins a un 20 % (la V de research/76): entre
    l'apilat de 2 s (C2+20–26 s) i el de 10,3 s (C2+34–60 s) hi hauria 50
    comptes/s de diferència, un 6 % de la corona allà on l'HDR canvia d'un a
    l'altre (1,96 R☉), i això és exactament el mecanisme dels arcs concèntrics.
    """
    global _fons_comu
    if _fons_comu is None:
        f = next(x for x in H.llegeix_manifest() if x.nom == NOM_FONS_COMU)
        t0 = next(x.t_rel_c2 for x in H.llegeix_manifest() if x.nom == NOM_EPOCA_COMUNA)
        mos, _ = carrega(f)
        _fons_comu = fons_fotograma(f, mos, factor_extincio(f.t_rel_c2, t0)) / f.exp_s
    return _fons_comu


def anivellament(ap: dict, dades: dict, escala: dict[str, float]):
    """Fons de cel per pla i fotograma (ja escalat per extinció), i el que cal
    restar a cadascun perquè tots els apilats quedin al fons comú."""
    fons = {f.nom: fons_fotograma(f, dades[f.nom][0], escala[f.nom]) for f in ap["membres"]}
    objectiu = fons_comu() * ap["exp_s"]
    return {f.nom: fons[f.nom] - objectiu for f in ap["membres"]}, fons, objectiu


def geometria_sortida(ap: dict, mode: str) -> tuple[float, float, str]:
    """Centre solar de la reixa de sortida (coordenades de sensor 6960×4640).

    * `comuna` (per defecte): el Sol al lloc on era a NOM_EPOCA_COMUNA
      (572A2969, C2+8,4 s). Tots els apilats queden alineats en corona entre
      ells i amb aquell CR3; 572A2968 hi queda a 0,25 px i 572A2956 a 2,5.
      El disc lunar de cada apilat continua essent el del seu fotograma de
      referència, desplaçat amb la seva corona.
    * `propia`: cada apilat en la geometria del seu CR3 de referència, o sigui
      un substitut «al seu lloc» com a l'HDR3, on el merge ha d'alinear.
      ⚠️ Si el merge alinea per la Lluna, la corona queda fins a 9 px
      desalineada entre extrems: era la primera versió, retirada.
    """
    if mode == "propia":
        return ap["ref"].sol_x, ap["ref"].sol_y, ap["ref"].nom
    f0 = next(f for f in H.llegeix_manifest() if f.nom == NOM_EPOCA_COMUNA)
    return f0.sol_x, f0.sol_y, f0.nom


_offset_lm: tuple[float, float] | None = None


def offset_limbe_model() -> tuple[float, float]:
    """Mitjana de (centre lunar mesurat al limbe − centre del model) sobre els
    fotogrames que tenen totes dues coses."""
    global _offset_lm
    if _offset_lm is None:
        fg = [f for f in H.llegeix_manifest() if f.usat and math.isfinite(f.lluna_mes_x)]
        _offset_lm = (float(np.mean([f.lluna_mes_x - f.lluna_x for f in fg])),
                      float(np.mean([f.lluna_mes_y - f.lluna_y for f in fg])))
    return _offset_lm


# Grups de protuberàncies: fotogrames prou junts en el temps perquè la
# protuberància no canviï ni la Lluna en descobreixi res de nou, però amb la
# deriva de la muntura entre ells (0,17 px per fotograma consecutiu) que fa de
# ditherat per recuperar el mostreig del pla vermell (Hα). El disc lunar
# s'emmascara cenyit al limbe real (453,8 px + 2, transició 4 px), no com als
# apilats de corona, perquè aquí el que interessa és justament la base de la
# protuberància.
R_LLUNA_REAL = 453.8
GRUPS_PROTUBERANCIES = [
    ("prot_C2_1-3200s_x9",   [f"572A{n}" for n in range(2958, 2967)], "572A2962"),
    ("prot_C3_1-3200s_x17",  [f"572A{n}" for n in range(3009, 3026)], "572A3017"),
    ("prot_tard_1-2000s_x3", ["572A2985", "572A2997", "572A3003"], "572A2997"),
    ("prot_tard_1-500s_x3",  ["572A2986", "572A2998", "572A3004"], "572A2998"),
    ("prot_tard_1-125s_x3",  ["572A2987", "572A2999", "572A3005"], "572A2999"),
]
PROTUBERANCIES = HDR4 / "protuberancies"


def grups_protuberancies() -> list[dict]:
    fg = {f.nom[:8]: f for f in H.llegeix_manifest() if f.usat}
    out = []
    for nom, membres, ref in GRUPS_PROTUBERANCIES:
        ms = [fg[m] for m in membres if m in fg]
        if len(ms) != len(membres):
            raise SystemExit(f"⛔ {nom}: falten fotogrames al manifest")
        out.append({"nom": nom, "ref": fg[ref], "exp_s": fg[ref].exp_s,
                    "membres": sorted(ms, key=lambda f: f.t_rel_c2),
                    "r_lluna": R_LLUNA_REAL, "marge": 2.0, "transicio": 4.0})
    return out


def apila(ap: dict, dades: dict, info: dict, mode: str = "comuna"
          ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Composa l'apilat en la geometria de sortida triada (vegeu
    `geometria_sortida`).

    Retorna (mitjana RGB en comptes per damunt del fosc, pes total, nombre
    d'aportacions), tot 4640×6960.
    """
    ref = ap["ref"]
    sol_out_x, sol_out_y, nom_geo = geometria_sortida(ap, mode)
    info["geometria"] = {"mode": mode, "fotograma": nom_geo,
                         "sol_x": sol_out_x, "sol_y": sol_out_y}
    canals = ["R", "G", "B"]
    num = {c: np.zeros((ALT, AMPLE), np.float64) for c in canals}
    den = {c: np.zeros((ALT, AMPLE), np.float64) for c in canals}
    ncon = {c: np.zeros((ALT, AMPLE), np.uint16) for c in canals}
    yy = np.arange(ALT, dtype=np.float32)[:, None]
    xx = np.arange(AMPLE, dtype=np.float32)[None, :]

    # centre lunar de cada fotograma: el MESURAT al limbe si hi és; si no (els
    # de 1/3200: perles), el del model més l'offset mitjà mesurat entre limbe i
    # model (l'ancoratge a la placa estel·lar desplaça el model uns 3,5 px del
    # limbe real; per a la màscara mana el limbe). En coordenades de sortida el
    # disc del fotograma f és a lluna_f + (sol_out − sol_f).
    off = offset_limbe_model()

    def centre_lluna(f):
        if math.isfinite(f.lluna_mes_x):
            return f.lluna_mes_x, f.lluna_mes_y
        return f.lluna_x + off[0], f.lluna_y + off[1]

    r_ll = ap.get("r_lluna", R_LLUNA)
    marge = ap.get("marge", MARGE_LLUNA)
    trans = ap.get("transicio", TRANSICIO_LLUNA)
    lx_r, ly_r = centre_lluna(ref)
    lx_r += sol_out_x - ref.sol_x
    ly_r += sol_out_y - ref.sol_y
    d_ref = np.hypot(xx - lx_r, yy - ly_r)
    # dins del disc de la referència (més marge) només hi contribueix ella
    zona_ref = np.clip((d_ref - (r_ll + marge)) / trans, 0.0, 1.0)

    # extinció: cada membre es porta a la massa d'aire de l'època comuna
    t0 = next(f.t_rel_c2 for f in H.llegeix_manifest() if f.nom == NOM_EPOCA_COMUNA)
    escala = {f.nom: factor_extincio(f.t_rel_c2, t0) for f in ap["membres"]}
    info["epoca_comuna"] = {"fotograma": NOM_EPOCA_COMUNA, "t_rel_c2_s": t0,
                            "massa_aire": massa_aire(t0)[0], "k_mag_X": K_EXTINCIO}
    info["factor_extincio"] = {f.nom: escala[f.nom] for f in ap["membres"]}
    info["massa_aire"] = {f.nom: massa_aire(f.t_rel_c2)[0] for f in ap["membres"]}

    desplac, fons, objectiu = anivellament(ap, dades, escala)
    info["fons_ADU"] = {f.nom: fons[f.nom].tolist() for f in ap["membres"]}
    info["fons_objectiu_ADU"] = objectiu.tolist()
    info["fons_comu_ADU_s"] = {"fotograma": NOM_FONS_COMU, "valor_RG1G2B": fons_comu().tolist()}

    for f in ap["membres"]:
        mos, sat = dades[f.nom]
        dx, dy = sol_out_x - f.sol_x, sol_out_y - f.sol_y
        es_ref = f.nom == ref.nom
        if es_ref:
            pes_ll = np.ones((ALT, AMPLE), np.float32)
        else:
            lx, ly = centre_lluna(f)
            d_f = np.hypot(xx - (lx + dx), yy - (ly + dy))
            pes_ll = (np.clip((d_f - (r_ll + marge)) / trans, 0.0, 1.0)
                      * zona_ref).astype(np.float32)
        info.setdefault("desplacament_px", {})[f.nom] = [dx, dy]
        for nom_pla, (pla, oy, ox) in plans(mos).items():
            c = "G" if nom_pla.startswith("G") else nom_pla
            val = pla * escala[f.nom] - desplac[f.nom][["R", "G1", "G2", "B"].index(nom_pla)]
            if ap.get("hdr"):
                # època amb exposicions diferents: comptes PER SEGON i pes òptim
                # w = t²/(S/g + RN²) (research/76), amb rampa suau al sostre
                t = f.exp_s
                g = H.GUANY[c]
                rn = H.RN_CURT if t < H.LLINDAR_MODE_S else H.RN_LLARG
                var = np.maximum(pla, 0.0) / g + rn * rn
                w = (t * t / var).astype(np.float32)
                w *= np.clip((SAT_RAW - PEDESTAL_DNG - pla) / (0.25 * (SAT_RAW - PEDESTAL_DNG)), 0.0, 1.0)
                w[sat[oy::2, ox::2]] = 0.0
                val = val / t
            else:
                w = np.where(sat[oy::2, ox::2], 0.0, 1.0).astype(np.float32)
            h, wd = pla.shape
            # la mostra (i,j) del pla és al centre del píxel (2i+oy, 2j+ox) del
            # sensor de f, o sigui a (2i+oy+0,5+dy, 2j+ox+0,5+dx) de la sortida
            ky0, wy = gota(oy + 0.5 + dy)
            kx0, wx = gota(ox + 0.5 + dx)
            for a_i, wa in enumerate(wy):
                if wa <= 0:
                    continue
                ty = talls(h, ky0 + a_i, ALT)
                if ty is None:
                    continue
                for b_i, wb in enumerate(wx):
                    if wb <= 0:
                        continue
                    tx = talls(wd, kx0 + b_i, AMPLE)
                    if tx is None:
                        continue
                    (iy, sy), (ix, sx) = ty, tx
                    ww = (w[iy, ix] * (wa * wb)) * pes_ll[sy, sx]
                    num[c][sy, sx] += ww * val[iy, ix]
                    den[c][sy, sx] += ww
                    ncon[c][sy, sx] += (ww > 0)
        log(f"    {f.nom[:8]} {'REF' if es_ref else '   '} desplaçament "
            f"({dx:+6.2f},{dy:+6.2f}) px  extinció ×{escala[f.nom]:.4f}  "
            f"fons {fons[f.nom][1]:8.1f} ADU (anivellat {desplac[f.nom][1]:+6.1f})  "
            f"saturats {int(sat.sum())}")

    mitja = np.zeros((ALT, AMPLE, 3), np.float32)
    pes = np.zeros((ALT, AMPLE, 3), np.float32)
    n = np.zeros((ALT, AMPLE, 3), np.uint16)
    for i, c in enumerate(canals):
        d = den[c]
        mitja[..., i] = np.where(d > 0, num[c] / np.maximum(d, 1e-30), np.nan)
        pes[..., i] = d
        n[..., i] = ncon[c]
    return mitja, pes, n


# ---------------------------------------------------------------- DNG

def _rat(v: float, den: int = 10000) -> tuple[int, int]:
    return int(round(v * den)), den


def escriu_dng(cami: Path, mitja: np.ndarray, ref: H.Fotograma, ap: dict,
               previa: np.ndarray, geo: str) -> None:
    """DNG lineal (LinearRaw, 3 mostres, 16 bits) en l'escala de comptes del
    CR3: BlackLevel 512, WhiteLevel 13995 (el d'Adobe per a la R6 III), els
    píxels sense cap mostra vàlida (cremats a tots els fotogrames) a blanc.
    IFD0 porta una previsualització petita i el raw va al SubIFD, que és
    l'estructura canònica que els lectors d'Adobe esperen."""
    import tifffile

    dades = np.rint(mitja + PEDESTAL_DNG)
    buit = ~np.isfinite(mitja)
    dades = np.where(buit, POU_DNG, dades)
    dades16 = np.clip(dades, 0, POU_DNG).astype(np.uint16)

    with rawpy.imread(str(H.SRC / ref.nom)) as raw:
        wb = raw.camera_whitebalance
    as_shot = [(1024, int(round(wb[0]))), (1, 1), (1024, int(round(wb[2])))]
    ara = dt.datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    descripcio = (f"Apilat de {len(ap['membres'])} fotogrames de {ref.exp_s:g} s "
                  f"({', '.join(f.nom[:8] for f in ap['membres'])}), registrat "
                  f"a la corona en la geometria de {geo}, cada membre "
                  f"normalitzat a la massa d'aire de {NOM_EPOCA_COMUNA[:8]} "
                  f"(k={K_EXTINCIO} mag/X). research/tools/apila_hdr4_vixen.py")
    ifd0 = [
        (50706, 1, 4, (1, 4, 0, 0), True),                    # DNGVersion
        (50707, 1, 4, (1, 1, 0, 0), True),                    # DNGBackwardVersion
        (50708, 2, None, UNIQUE_CAMERA_MODEL, True),          # UniqueCameraModel
        (271, 2, None, "Canon", True),                        # Make
        (272, 2, None, UNIQUE_CAMERA_MODEL, True),            # Model
        (274, 3, 1, 1, True),                                 # Orientation
        (306, 2, None, ara, True),                            # DateTime
        (270, 2, None, descripcio, True),                     # ImageDescription
        (50721, 10, 9, [_rat(v) for v in COLOR_MATRIX_1], True),
        (50722, 10, 9, [_rat(v) for v in COLOR_MATRIX_2], True),
        (50778, 3, 1, 17, True),                              # CalibrationIlluminant1
        (50779, 3, 1, 21, True),                              # CalibrationIlluminant2
        (50964, 10, 9, [_rat(v) for v in FORWARD_MATRIX_1], True),
        (50965, 10, 9, [_rat(v) for v in FORWARD_MATRIX_2], True),
        (50727, 5, 3, [(1, 1), (1, 1), (1, 1)], True),        # AnalogBalance
        (50728, 5, 3, as_shot, True),                         # AsShotNeutral
        (50730, 10, 1, [BASELINE_EXPOSURE], True),            # BaselineExposure
        (50731, 5, 1, [BASELINE_NOISE], True),                # BaselineNoise
        (50732, 5, 1, [BASELINE_SHARPNESS], True),            # BaselineSharpness
        (50734, 5, 1, [(1, 1)], True),                        # LinearResponseLimit
        (50827, 1, None, (ref.nom + "\0").encode(), True),    # OriginalRawFileName
        (50735, 2, None, "[SÈRIE]", True),               # CameraSerialNumber
    ]
    sub = [
        (50714, 3, 3, (PEDESTAL_DNG,) * 3, True),             # BlackLevel
        (50717, 4, 3, (POU_DNG,) * 3, True),                  # WhiteLevel
        (50719, 4, 2, (0, 0), True),                          # DefaultCropOrigin
        (50720, 4, 2, (AMPLE, ALT), True),                    # DefaultCropSize
        (50829, 4, 4, (0, 0, ALT, AMPLE), True),              # ActiveArea
    ]
    programari = "apila_hdr4_vixen.py (drizzle 2,0 px; tifffile)"
    with tifffile.TiffWriter(cami, byteorder="<", bigtiff=False) as tw:
        tw.write(previa, photometric="rgb", subfiletype=1, subifds=1,
                 metadata=None, extratags=ifd0, compression=None,
                 software=programari)
        # ⛔ extrasamples=False: sense això tifffile hi posa ExtraSamples (0,0)
        # per a les tres mostres del LinearRaw, i un lector podria prendre dues
        # de les tres com a canals auxiliars.
        tw.write(dades16, photometric=34892, subfiletype=0, metadata=None,
                 extratags=sub, compression=None, planarconfig="contig",
                 rowsperstrip=64, extrasamples=False, software=programari)
    # EXIF del CR3 de referència: exposició, ISO, instant, cos, sèrie
    cmd = ["exiftool", "-q", "-overwrite_original", "-tagsFromFile", str(H.SRC / ref.nom),
           "-EXIF:ExposureTime", "-EXIF:FNumber", "-EXIF:ISO", "-EXIF:SensitivityType",
           "-EXIF:RecommendedExposureIndex", "-EXIF:ExposureProgram", "-EXIF:ExposureMode",
           "-EXIF:DateTimeOriginal", "-EXIF:CreateDate", "-EXIF:OffsetTime",
           "-EXIF:OffsetTimeOriginal", "-EXIF:OffsetTimeDigitized",
           "-EXIF:SubSecTime", "-EXIF:SubSecTimeOriginal", "-EXIF:SubSecTimeDigitized",
           "-EXIF:ShutterSpeedValue", "-EXIF:FocalLength", "-EXIF:SerialNumber",
           "-EXIF:LensModel", "-EXIF:LensInfo", "-EXIF:WhiteBalance",
           "-EXIF:FocalPlaneXResolution", "-EXIF:FocalPlaneYResolution",
           "-EXIF:FocalPlaneResolutionUnit", "-EXIF:ExifVersion",
           str(cami)]
    subprocess.run(cmd, check=True)


ADOBE_DNG_CONVERTER = Path("/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter")


def compacta_amb_adobe(cami: Path) -> str:
    """Passa el DNG pel DNG Converter d'Adobe (18.5 o posterior: el 17.5 no
    coneix la R6 III): el rellegeix, el comprimeix sense pèrdua (JPEG lossless,
    de 194 a ~64 MB) i hi posa la previsualització d'Adobe. Només se substitueix
    l'original si els píxels tornen idèntics; si el convertidor no hi és o
    falla, es conserva el DNG sense comprimir i es diu."""
    if not ADOBE_DNG_CONVERTER.exists():
        return "sense DNG Converter: DNG sense comprimir"
    tmp = cami.with_name(cami.stem + "_adobe_tmp.dng")
    if tmp.exists():
        tmp.unlink()
    r = subprocess.run([str(ADOBE_DNG_CONVERTER), "-c", "-p1", "-d", str(cami.parent),
                        "-o", tmp.name, str(cami)], capture_output=True, text=True)
    if not tmp.exists():
        return f"el DNG Converter ha fallat ({r.stdout.strip()[-80:]}): DNG sense comprimir"
    with rawpy.imread(str(cami)) as a, rawpy.imread(str(tmp)) as b:
        iguals = np.array_equal(a.raw_image[..., :3], b.raw_image[..., :3])
    if not iguals:
        tmp.unlink()
        return "⛔ el DNG Converter ha canviat píxels: es conserva el sense comprimir"
    tmp.replace(cami)
    return f"comprimit sense pèrdua pel DNG Converter ({cami.stat().st_size/1e6:.0f} MB)"


def previsualitzacio(mitja: np.ndarray, sol: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Petita per a l'IFD0 (256 px) i gran per a la carpeta qa (2400 px),
    amb un estirament logarítmic de la luminància i color neutre."""
    import cv2
    R, G, B = mitja[..., 0], mitja[..., 1], mitja[..., 2]
    lum = 0.5 * (G + 1.2 * R)
    bo = np.isfinite(lum)
    lo = max(np.percentile(lum[bo], 1.0), 0.5)
    hi = max(np.percentile(lum[bo], 99.9), lo * 10)
    lum = np.where(bo, lum, hi)          # el nucli cremat es mostra blanc, com al DNG
    est = np.clip((np.log10(np.maximum(lum, lo)) - math.log10(lo))
                  / (math.log10(hi) - math.log10(lo)), 0, 1)
    rgb = np.stack([est] * 3, -1)
    a8 = (rgb * 255).astype(np.uint8)
    gran = cv2.resize(a8, (2400, int(round(2400 * ALT / AMPLE))), interpolation=cv2.INTER_AREA)
    petita = cv2.resize(a8, (256, int(round(256 * ALT / AMPLE))), interpolation=cv2.INTER_AREA)
    return petita, gran


def etapa_apila(args, grups: list[dict] | None = None, carpeta: Path | None = None,
                resum_nom: str = "apilats.json") -> None:
    import cv2
    HDR4.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    resum = []
    for ap in (grups if grups is not None else apilats()):
        if args.nomes and not (ap["ref"].nom.startswith(args.nomes)
                               or sortida_nom(ap).startswith(args.nomes)):
            continue
        nom = sortida_nom(ap)
        log(f"\n=== {nom}  exp {ap['exp_s']:.6g} s  ({len(ap['membres'])} fotogrames)")
        dades = {f.nom: carrega(f) for f in ap["membres"]}
        info = {"nom": nom, "referencia": ap["ref"].nom, "exp_s": ap["exp_s"],
                "membres": [f.nom for f in ap["membres"]],
                "t_rel_c2_s": {f.nom: f.t_rel_c2 for f in ap["membres"]}}
        mitja, pes, n = apila(ap, dades, info, args.geometria)
        buits = int((~np.isfinite(mitja[..., 1])).sum())
        info["pixels_sense_dada_verd"] = buits
        info["aportacions_mediana_verd"] = float(np.median(n[..., 1]))
        petita, gran = previsualitzacio(mitja, (ap["ref"].sol_x, ap["ref"].sol_y))
        desti = carpeta if carpeta is not None else APILATS
        desti.mkdir(parents=True, exist_ok=True)
        cami = desti / f"{nom}.dng"
        escriu_dng(cami, mitja, ap["ref"], ap, petita, info["geometria"]["fotograma"])
        cv2.imwrite(str(QA / f"{nom}_previa.jpg"), gran[..., ::-1],
                    [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        info["adobe"] = compacta_amb_adobe(cami)
        info["dng"] = cami.name
        info["mida_MB"] = round(cami.stat().st_size / 1e6, 1)
        resum.append(info)
        log(f"  → {cami.name}  ({info['mida_MB']} MB; {info['adobe']})  sense dada: {buits} px  "
            f"aportacions verd (mediana): {info['aportacions_mediana_verd']:.0f}")
        (QA / f"{nom}.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    (QA / resum_nom).write_text(json.dumps(resum, indent=1, ensure_ascii=False))


def etapa_protuberancies(args) -> None:
    grups = grups_protuberancies()
    etapa_apila(args, grups=grups, carpeta=PROTUBERANCIES, resum_nom="protuberancies.json")
    files = []
    for ap in grups:
        files.append({"fitxer": f"protuberancies/{sortida_nom(ap)}.dng",
                      "exposicio_s": f"{ap['exp_s']:g}",
                      "fotogrames": " ".join(f.nom[:8] for f in ap["membres"]),
                      "referencia": ap["ref"].nom[:8],
                      "finestra_s": f"{ap['membres'][0].t_rel_c2:.1f}–{ap['membres'][-1].t_rel_c2:.1f} (C2+)"})
    with open(PROTUBERANCIES / "manifest_protuberancies.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(files[0].keys()))
        w.writeheader()
        w.writerows(files)
    log(f"→ {PROTUBERANCIES/'manifest_protuberancies.csv'}")


# ---------------------------------------------------------------- munta

def etapa_munta(args) -> None:
    HDR4.mkdir(parents=True, exist_ok=True)
    aps = apilats()
    noms_apilats = {ap["ref"].nom for ap in aps}
    files = []
    for cr3 in sorted(HDR3.glob("*.CR3")):
        if cr3.name in noms_apilats:
            continue
        dest = HDR4 / nom_copia_cr3(cr3.name)
        if not dest.exists():
            shutil.copy2(cr3, dest)
        _, e = rang_exposicio()[cr3.name[:8]]
        files.append({"fitxer": dest.name, "tipus": "CR3 original (una sola foto)",
                      "exposicio_s": f"{e:g}", "fotogrames": cr3.name[:8],
                      "referencia": cr3.name[:8]})
        log(f"  copiat {cr3.name} → {dest.name}")
    resum = json.loads((QA / "apilats.json").read_text()) if (QA / "apilats.json").exists() else []
    per_nom = {r["nom"]: r for r in resum}
    for ap in aps:
        nom = sortida_nom(ap)
        r = per_nom.get(nom, {})
        files.append({"fitxer": f"apilats/{nom}.dng",
                      "tipus": f"apilat de {len(ap['membres'])} (DNG lineal)",
                      "exposicio_s": f"{ap['exp_s']:g}",
                      "fotogrames": " ".join(f.nom[:8] for f in ap["membres"]),
                      "referencia": ap["ref"].nom[:8]})
    files.sort(key=lambda r: Path(r["fitxer"]).name)
    with open(HDR4 / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(files[0].keys()))
        w.writeheader()
        w.writerows(files)
    log(f"→ {HDR4/'manifest.csv'}")


# ---------------------------------------------------------------- capes

# Èpoques per a les capes de protuberàncies: TOTES les exposicions preses en
# uns quants segons al voltant de cada contacte, combinades en HDR (comptes per
# segon, pesos òptims): els nuclis brillants i la cromosfera surten dels
# 1/3200 i les protuberàncies febles —les que la corona amaga a ull nu— dels
# 1/125, 1/30 i 1/8. La Lluna es mou < 3 px dins de cada època.
EPOQUES_CAPES = {
    "C2": {"membres": [f"572A{n}" for n in range(2958, 2973)], "ref": "572A2969"},
    "C3": {"membres": [f"572A{n}" for n in range(2997, 3026)], "ref": "572A3005"},
}


def cam_a_srgb() -> np.ndarray:
    """Matriu càmera → sRGB lineal (mètode dcraw) a partir de la ColorMatrix2
    (XYZ → càmera, D65) d'Adobe per a la R6 III. Files normalitzades perquè el
    blanc de càmera (després del balanç) surti neutre."""
    xyz_rgb = np.array([[0.412453, 0.357580, 0.180423],
                        [0.212671, 0.715160, 0.072169],
                        [0.019334, 0.119193, 0.950227]])
    cam_xyz = np.array(COLOR_MATRIX_2).reshape(3, 3)
    cam_rgb = cam_xyz @ xyz_rgb
    cam_rgb /= cam_rgb.sum(axis=1, keepdims=True)
    return np.linalg.pinv(cam_rgb)


def hdr_epoca(nom: str, args) -> tuple[np.ndarray, dict]:
    """HDR de comptes per segon d'una època de contacte, en la geometria comuna."""
    fg = {f.nom[:8]: f for f in H.llegeix_manifest() if f.usat}
    ep = EPOQUES_CAPES[nom]
    membres = sorted((fg[m] for m in ep["membres"] if m in fg), key=lambda f: f.t_rel_c2)
    ap = {"nom": f"epoca_{nom}", "ref": fg[ep["ref"]], "exp_s": fg[ep["ref"]].exp_s,
          "membres": membres, "r_lluna": R_LLUNA_REAL, "marge": 2.0, "transicio": 4.0,
          "hdr": True}
    log(f"=== època {nom}: {len(membres)} fotogrames, {membres[0].t_rel_c2:.1f}–"
        f"{membres[-1].t_rel_c2:.1f} s, {len({f.exp_s for f in membres})} exposicions")
    dades = {f.nom: carrega(f) for f in membres}
    info = {"nom": ap["nom"], "referencia": ap["ref"].nom,
            "membres": [f.nom for f in membres]}
    mitja, pes, n = apila(ap, dades, info, args.geometria)
    return mitja, info


def capa_protuberancies(nom_epoca: str, args, s_asinh: float = 0.01) -> dict:
    """Capa de Photoshop amb TOTES les protuberàncies d'un contacte: TIFF RGB
    de 16 bits sRGB, 6960×4640 en la geometria comuna, tot el que no és
    protuberància ni cromosfera a NEGRE (fusió «Pantalla»/«Aclarir» directa),
    i la màscara suau a part.

    ⛔ La màscara NO és de brillantor: una protuberància feble és deu vegades
    més fluixa que la corona que té al darrere, i només se'n distingeix pel
    color. És l'**excés d'Hα**: E = R − ρ·G en comptes de càmera, amb ρ el
    color de la corona mesurat a la mateixa imatge (research/76: 0,816); la
    corona (continu K) i el cel s'hi anul·len, i queden les protuberàncies i
    la cromosfera. Es llinda respecte del soroll de E i es suavitza 1,5 px.
    Dues sortides: la lineal (per estirar-la a Photoshop) i una asinh
    (`s_asinh` de la màxima) per veure-les totes de cop.
    """
    from scipy.ndimage import gaussian_filter
    import tifffile
    hdr, info = hdr_epoca(nom_epoca, args)
    R_, G_, B_ = hdr[..., 0], hdr[..., 1], hdr[..., 2]
    sol = (info["geometria"]["sol_x"], info["geometria"]["sol_y"])
    yy = np.arange(ALT, dtype=np.float32)[:, None]
    xx = np.arange(AMPLE, dtype=np.float32)[None, :]
    rs = np.hypot(xx - sol[0], yy - sol[1]) / H.R_SOL_PX
    ref = next(f for f in H.llegeix_manifest() if f.nom == info["referencia"])
    off = offset_limbe_model()
    lx = (ref.lluna_mes_x if math.isfinite(ref.lluna_mes_x) else ref.lluna_x + off[0]) + sol[0] - ref.sol_x
    ly = (ref.lluna_mes_y if math.isfinite(ref.lluna_mes_y) else ref.lluna_y + off[1]) + sol[1] - ref.sol_y
    rl = np.hypot(xx - lx, yy - ly)
    bo = np.isfinite(R_) & np.isfinite(G_)
    # color de la corona (R/G cru), mesurat a 1,05–1,4 R☉ fora del disc
    z = bo & (rs > 1.05) & (rs < 1.4) & (rl > R_LLUNA_REAL + 6)
    rho = float(np.median(R_[z] / np.maximum(G_[z], 1e-3)))
    E = np.where(bo, R_ - rho * G_, 0.0).astype(np.float32)
    # ⛔ El soroll de E no és de fotons: és el residu suau del model de color
    # (la corona no és exactament del mateix color a tot arreu, ±700 comptes/s
    # en taques de centenars de px), i no baixa en suavitzar. Se li resta el
    # seu fons suau (σ = 40 px, sense el disc ni les protuberàncies fortes) i
    # el que queda sí que és soroll de píxel: 3× més baix. Les protuberàncies
    # són compactes o primes i sobreviuen al passa-alt.
    ok = (rl > R_LLUNA_REAL + 4) & (E < 6.0 * 858.0)
    fons_E = (gaussian_filter(np.where(ok, E, 0.0), 40.0)
              / np.maximum(gaussian_filter(ok.astype(np.float32), 40.0), 1e-3))
    E_hp = np.where(rl > R_LLUNA_REAL - 2, E - fons_E, 0.0).astype(np.float32)
    E_s = gaussian_filter(E_hp, 2.0)
    neg = E_s[z][E_s[z] < 0]
    sig = float(np.sqrt(np.mean(neg * neg))) if neg.size else 1.0
    # Llindar per píxel sobre E passa-alt suavitzat 2 px, amb confirmació a
    # 4 px (mata les taques de soroll aïllades i conserva el que és extens).
    # ⛔ Provat i retirat: llindar per histèresi amb llavors a 3,5 σ i
    # creixement fins a 1,5 σ. La cromosfera és llavor a tot el limbe i el
    # soroll que la toca creixia en confeti. Les extensions molt febles (la cua
    # de 40 px de la punxa de dalt de C2, a 1–2 σ per píxel) queden per a la
    # capa d'excés d'Hα sense màscara.
    E_s4 = gaussian_filter(E_hp, 4.0)
    neg4 = E_s4[z][E_s4[z] < 0]
    sig4 = float(np.sqrt(np.mean(neg4 * neg4))) if neg4.size else sig
    zona = (rl > R_LLUNA_REAL - 2.0) & (rs < 1.6)
    masc = (np.clip((E_s - 2.0 * sig) / (2.0 * sig), 0, 1)
            * np.clip((E_s4 - 1.5 * sig4) / (1.0 * sig4), 0, 1) * zona)
    masc *= np.clip((rl - (R_LLUNA_REAL - 2.0)) / 3.0, 0, 1)      # dins de la Lluna, zero
    masc = gaussian_filter(masc, 1.5)
    # color: balanç del cos i matriu càmera → sRGB lineal
    with rawpy.imread(str(H.SRC / ref.nom)) as raw:
        wb = raw.camera_whitebalance
    cam = np.stack([np.nan_to_num(R_) * wb[0] / wb[1], np.nan_to_num(G_), np.nan_to_num(B_) * wb[2] / wb[1]], -1)
    rgb = np.clip(cam @ cam_a_srgb().T, 0, None)
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    prot = masc > 0.5
    lmax = float(np.percentile(lum[prot], 99.9)) if prot.any() else float(lum.max())
    lin = np.clip(rgb / lmax, 0, 1)
    # asinh sobre la luminància, color conservat
    ln = np.clip(lum / lmax, 0, None)
    y = np.arcsinh(ln / s_asinh) / math.asinh(1.0 / s_asinh)
    asinh_rgb = np.clip(lin * (y / np.maximum(ln, 1e-9))[..., None], 0, 1)
    PROTUBERANCIES.mkdir(parents=True, exist_ok=True)
    nom = f"capa_prot_{nom_epoca}"
    H.escriu_tiff(PROTUBERANCIES / f"{nom}.tif", asinh_rgb * masc[..., None], "srgb")
    H.escriu_tiff(PROTUBERANCIES / f"{nom}_lineal.tif", lin * masc[..., None], "srgb")
    # capa d'excés d'Hα SENSE màscara: tot el que és més vermell que la corona,
    # amb el seu soroll, per caçar-hi protuberàncies febles a mà. Color: el
    # de la protuberància més brillant; to: asinh amb 2 σ a ~0,15.
    col_prot = rgb[prot].mean(axis=0) if prot.any() else np.array([1.0, 0.4, 0.5])
    col_prot = col_prot / max(col_prot.max(), 1e-9)
    e_pos = np.clip(np.where(zona, E_hp, 0.0), 0, None)
    e_max = float(np.percentile(e_pos[prot], 99.9)) if prot.any() else float(e_pos.max())
    from scipy.optimize import brentq
    a2 = 2.0 * sig / e_max                      # 2 σ en unitats de la màxima
    f = lambda sv: math.asinh(a2 / sv) - 0.15 * math.asinh(1.0 / sv)
    s_e = brentq(f, 1e-7, 10.0) if f(1e-7) * f(10.0) < 0 else 0.01
    ye = np.arcsinh(e_pos / (s_e * e_max)) / math.asinh(1.0 / s_e)
    H.escriu_tiff(PROTUBERANCIES / f"{nom}_Halpha.tif", np.clip(ye[..., None] * col_prot, 0, 1), "srgb")
    tifffile.imwrite(PROTUBERANCIES / f"{nom}_mascara.tif",
                     (np.clip(masc, 0, 1) * 65535 + 0.5).astype(np.uint16),
                     photometric="minisblack", compression="zlib", metadata=None)
    return {"capa": f"{nom}.tif", "lineal": f"{nom}_lineal.tif", "halpha": f"{nom}_Halpha.tif",
            "mascara": f"{nom}_mascara.tif",
            "epoca": nom_epoca, "membres": info["membres"], "referencia": info["referencia"],
            "rho_RG_corona": rho, "sigma_E_countss": sig, "s_asinh": s_asinh,
            "normalitzacio_lineal_countss": lmax, "pixels_protuberancia": int(prot.sum()),
            "centre_lunar_capa": [float(lx), float(ly)], "geometria": info["geometria"]}


def etapa_capes(args) -> None:
    resum = []
    for ep in ("C2", "C3"):
        r = capa_protuberancies(ep, args)
        log(f"  → {r['capa']}, {r['lineal']}, {r['mascara']}  ρ(R/G corona)={r['rho_RG_corona']:.3f} "
            f"σ_E={r['sigma_E_countss']:.0f} comptes/s  píxels de protuberància {r['pixels_protuberancia']}")
        resum.append(r)
    (QA / "capes.json").write_text(json.dumps(resum, indent=1, ensure_ascii=False))


def capa_protuberancies_burst_antiga(nom_dng: str, nom_capa: str, gamma: float = 0.7) -> dict:
    """Capa de Photoshop amb les protuberàncies d'un apilat de 1/3200 s: TIFF
    RGB de 16 bits sRGB, 6960×4640 en la geometria comuna, desenvolupat amb el
    balanç del cos, amb tot el que no és protuberància ni cromosfera a NEGRE
    (fusió «Pantalla»/«Aclarir» directa) i la màscara suau a part (per si es
    vol en «Normal» amb màscara de capa).

    La màscara surt del pla vermell cru de l'apilat: a 1/3200 s la corona hi
    val ≲ 15 comptes i les protuberàncies i la cromosfera de 50 a 2.000; la
    rampa va de 25 a 60 comptes, dins del disc lunar val zero i s'ha suavitzat
    1,5 px. El to: lineal normalitzat al percentil 99,9 de la protuberància,
    gamma `gamma`, i codificació sRGB.
    """
    import cv2
    from scipy.ndimage import gaussian_filter
    cami = PROTUBERANCIES / f"{nom_dng}.dng"
    with rawpy.imread(str(cami)) as raw:
        R_cru = raw.raw_image[..., 0].astype(np.float32) - PEDESTAL_DNG
        rgb = raw.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16,
                              use_camera_wb=True, output_color=rawpy.ColorSpace.sRGB,
                              user_flip=0).astype(np.float32) / 65535.0
    info = json.loads((QA / f"{nom_dng}.json").read_text())
    ref = next(f for f in H.llegeix_manifest() if f.nom == info["referencia"])
    off = offset_limbe_model()
    lx = (ref.lluna_mes_x if math.isfinite(ref.lluna_mes_x) else ref.lluna_x + off[0])
    ly = (ref.lluna_mes_y if math.isfinite(ref.lluna_mes_y) else ref.lluna_y + off[1])
    lx += info["geometria"]["sol_x"] - ref.sol_x
    ly += info["geometria"]["sol_y"] - ref.sol_y
    yy = np.arange(ALT, dtype=np.float32)[:, None]
    xx = np.arange(AMPLE, dtype=np.float32)[None, :]
    rl = np.hypot(xx - lx, yy - ly)
    R_suau = gaussian_filter(R_cru, 1.5)
    masc = np.clip((R_cru - 25.0) / 35.0, 0, 1) * np.clip((R_suau - 20.0) / 20.0, 0, 1)
    masc *= np.clip((rl - (R_LLUNA_REAL - 2.0)) / 3.0, 0, 1)      # dins de la Lluna, zero
    masc *= (rl < 800)
    masc = gaussian_filter(masc, 1.5)
    prot = masc > 0.5
    lmax = float(np.percentile(rgb[prot].max(axis=1), 99.9)) if prot.any() else 1.0
    lin = np.clip(rgb / lmax, 0, 1) ** gamma * masc[..., None]
    H.escriu_tiff(PROTUBERANCIES / f"{nom_capa}.tif", lin, "srgb")
    import tifffile
    tifffile.imwrite(PROTUBERANCIES / f"{nom_capa}_mascara.tif",
                     (np.clip(masc, 0, 1) * 65535 + 0.5).astype(np.uint16),
                     photometric="minisblack", compression="zlib", metadata=None)
    return {"capa": f"{nom_capa}.tif", "mascara": f"{nom_capa}_mascara.tif",
            "dng": cami.name, "gamma": gamma, "normalitzacio_lineal": lmax,
            "pixels_protuberancia": int(prot.sum()),
            "centre_lunar_capa": [float(lx), float(ly)]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("etapa", choices=["mesura", "apila", "munta", "protuberancies", "capes", "tot"])
    p.add_argument("--nomes", help="només l'apilat que comença per aquest nom (572A2970)")
    p.add_argument("--geometria", choices=["comuna", "propia"], default="comuna",
                   help="reixa de sortida: comuna (el Sol al lloc de 572A2969, tots "
                        "els apilats alineats en corona; per defecte) o propia (la del "
                        "CR3 de referència de cada apilat)")
    args = p.parse_args()
    if args.etapa in ("mesura", "tot"):
        etapa_mesura(args)
    if args.etapa in ("apila", "tot"):
        etapa_apila(args)
    if args.etapa in ("munta", "tot"):
        etapa_munta(args)
    if args.etapa in ("protuberancies", "tot"):
        etapa_protuberancies(args)
    if args.etapa in ("capes", "tot"):
        etapa_capes(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
