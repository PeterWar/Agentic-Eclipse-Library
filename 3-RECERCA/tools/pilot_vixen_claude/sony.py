"""El tren Sony al mateix llenç comú: registre per ràfega i configuració del tren.

⚠️ **La Sony no és la Vixen i el seu problema no és el mateix.** Aquí la muntura
va **patinar 750 px** a mig de la totalitat (`research/96`), o sigui que els 30
fotogrames de dins la totalitat són a **dos apuntaments**, i el segon encara
s'estava assentant quan es van fer els primers fotogrames de després.

El registre NO surt d'un model global de deriva —no n'hi ha cap de vàlid que
travessi el salt— sinó de dues coses:

1. els **deu fotogrames ancorats per estrelles** de `registre_v3_sony.json`,
   que són evidència directa i no es toquen;
2. per als altres, **la ràfega**: cada pulsació de l'obturador dona tres
   subfotogrames, i dins d'una ràfega el cos no es mou més del que la deriva
   permet en els pocs segons que dura. Els fotogrames sense estrelles hereten
   la posició dels seus germans de ràfega, i el que la porta ha de fitar és
   **quant pot valer aquesta herència**.

⛔ Els fotogrames de contacte (1/6400, 1/800, 1/100) **no entren**: no tenen ni
estrelles ni limbe net, i amb `w = t²/…` la seva aportació a la corona és
menyspreable. Són per a les perles i l'anell, no per a la corona.
⛔ `DSC06989` **queda exclosa**: la seva ràfega és la del salt i els seus dos
germans ja estaven exclosos (`DSC06988` amb traços d'estrelles de 25 px i
`DSC06990` moguda). No té cap àncora possible.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import subprocess
from pathlib import Path

import numpy as np

HOME = Path.home()
DESK = HOME / "Desktop" / "Eclipse 2026"
REPO = HOME / "Downloads" / "Eclipse 2026"

SRC = DESK / "300mm A7RIIIA"
MASTERS = SRC / "calibrated" / "_masters"
REGISTRE = REPO / "output" / "salt_muntura_20260823" / "registre_v3_sony.json"
PLACA = (DESK / "Derivats" / "Astrometria" / "Estrelles"
         / "Resultats_acceptacio_2026-08-17" / "final_solution.json")
FLAT_RADIAL = (REPO / "output" / "flats_20260822" / "sony_a7r3a_300mm_posterior_v1"
               / "MASTER_OPTICAL_RADIAL_CFA4.npy")

_PL = json.loads(PLACA.read_text())["sony_radial"]
ESCALA = float(_PL["scale"])          # 3,2019913768 ″/px
PA_NORD = float(_PL["pa_north"])      # 90,2705969°
SOL_REF = (float(_PL["sun_x"]), float(_PL["sun_y"]))   # al fotograma de referència

POU = 16383.0
PEDESTAL = 512.0
# ⛔ La Sony té el SEU tall de saturació i la seva variable. Fins al 25-08-2026
# era el literal `0.85` aquí dins, i llavors `PILOT_SOSTRE=0.80` movia el tall de
# la Vixen **i no el d'aquest tren**, mentre el rebut estampava el número de la
# Vixen als dos. Un tall per tren, una variable per tren, i el rebut els diu tots
# dos. El valor de producció és 0,85 als dos trens.
_FSOS = float(os.environ.get("PILOT_SOSTRE_SONY", "0.85"))
SOSTRE = _FSOS * (POU - PEDESTAL)
# research/75 §... — mesurats al cos, ISO 100. ⛔ No són els de la R6.
GUANY = {"R": 3.41, "G1": 3.41, "G2": 3.41, "B": 3.41}   # e⁻/ADU
RN = 1.22                                                 # ADU
FB = 1.134e-11        # B/B☉ per ADU/s (research/75 §5.2). ⛔ no el de la Vixen

C2_LOCAL = dt.datetime(2026, 8, 12, 20, 28, 45, 0)
CONTACTE_MAX_S = 0.02        # per sota d'això és bloc de contacte i no entra
EXCLOSES = {
    "DSC06988": "1 s amb traços d'estrelles de ~25 px: és l'inici del salt 2",
    "DSC06990": "8 s moguda pel salt 2 de muntura (research/72)",
    "DSC06989": ("0,125 s de la mateixa ràfega que 06988 i 06990, totes dues "
                 "exclosos: no té cap àncora d'estrelles possible"),
}


def exif() -> dict[str, tuple[float, float, float]]:
    """{nom sense extensió: (t respecte de C2, exposició FÍSICA, nominal)}.

    ⚠️ Calen totes dues: la **física** escala el senyal i la **nominal** indexa
    el màster dark, que es va construir amb el nom del menú. Confondre-les fa
    que el màster no es trobi (o, pitjor, que se'n triï un altre).

    ⚠️ L'exposició és la del **MakerNote** (`SonyExposureTime`), no la de
    l'`ExposureTime` de l'EXIF. La Sony té la mateixa trampa que la Canon: el
    que el menú diu **1/30 és de fet 1/32**, un **−6,25 %**. Els tres
    fotogrames de 1/30 de dins la totalitat en van afectats. La resta de
    l'escala d'aquest cos (1/8, 1/4, 1, 2, 8 s) sí que és exacta.
    """
    fitxers = sorted(SRC.glob("*.ARW"))
    out = subprocess.run(
        ["exiftool", "-q", "-n", "-T", "-FileName", "-SonyExposureTime",
         "-ExposureTime", "-SubSecDateTimeOriginal", *map(str, fitxers)],
        capture_output=True, text=True, check=True).stdout
    d = {}
    for linia in out.splitlines():
        nom, e_mk, e_nom, t = linia.split("\t")
        e = e_mk if e_mk not in ("", "-") else e_nom
        m = re.match(r"(\d{4}:\d\d:\d\d \d\d:\d\d:\d\d)(\.\d+)?", t)
        ts = dt.datetime.strptime(m.group(1), "%Y:%m:%d %H:%M:%S")
        if m.group(2):
            ts += dt.timedelta(seconds=float(m.group(2)))
        d[nom.replace(".ARW", "")] = ((ts - C2_LOCAL).total_seconds(),
                                      float(e), float(e_nom))
    return d


# Les tres tríades que el programa de l'A7RIIIA dispara, cadascuna d'una sola
# pulsació (research/70 i §3 de CLAUDE.md). El cos entrega la base primer i
# després −3 i +3 EV, o sigui que una ràfega d'àncora dura 1 + 0,125 + 8 s i
# **s'estén nou segons llargs**.
# ⚠️ Valors FÍSICS del MakerNote, no els nominals del menú: 1/30 és 1/32.
TRIADES = {
    "contacte": {0.00015625, 0.00125, 0.01},
    "muntanya": {0.03125, 0.25, 2.0},
    "ancora": {0.125, 1.0, 8.0},
}


def _quina_triada(e: float) -> str | None:
    for nom, s in TRIADES.items():
        if any(abs(e - v) < 1e-6 * max(v, 1e-6) for v in s):
            return nom
    return None


def rafegues(tt: dict[str, tuple[float, float]], totalitat_s: float = 105.0,
             forat_s: float = 15.0) -> list[list[str]]:
    """Agrupa en ràfegues: una pulsació dona tres subfotogrames.

    ⛔ **No es pot agrupar per un forat de temps sol.** Una ràfega d'àncora dura
    més de nou segons —1 + 0,125 + 8— i el descans entre ràfegues n'és de deu:
    amb un llindar de 5 s la ràfega es parteix i el fotograma del mig es queda
    sense la seva segona àncora; amb un de 12 s, dues ràfegues es fonen. El que
    les separa de debò és **l'estructura del programa**: cada ràfega és una
    tríada i no repeteix exposició.
    """
    dins = sorted(((v[0], n) for n, v in tt.items() if -1 <= v[0] <= totalitat_s))
    grups: list[list[str]] = []
    vistes: set[float] = set()
    triada_oberta: str | None = None
    for t, n in dins:
        e = tt[n][1]
        tri = _quina_triada(e)
        nova = (not grups
                or tri != triada_oberta
                or any(abs(e - x) < 1e-9 for x in vistes)
                or t - tt[grups[-1][-1]][0] > forat_s)
        if nova:
            grups.append([n]); vistes = {e}; triada_oberta = tri
        else:
            grups[-1].append(n); vistes.add(e)
    return grups


def registre() -> dict:
    """Posició del Sol per fotograma, amb l'origen de cada valor.

    Tres orígens possibles, i la porta els tracta diferent:
    `estrelles` (evidència directa), `rafega_interpolat` (entre dos germans
    ancorats) i `rafega_extrapolat` (a partir d'un de sol, amb el model del
    grup). Cap fotograma sense àncora a la seva ràfega no s'admet.
    """
    tt = exif()
    R = json.loads(REGISTRE.read_text())["registre"]
    anc = {n: (v["dx"], v["dy"], v["grup"]) for n, v in R.items()}

    # model de deriva per grup, ajustat NOMÉS als ancorats del grup
    models = {}
    for g in sorted({v[2] for v in anc.values()}):
        ns = [n for n in anc if anc[n][2] == g]
        t = np.array([tt[n][0] for n in ns])
        x = np.array([anc[n][0] for n in ns])
        y = np.array([anc[n][1] for n in ns])
        A = np.vstack([np.ones_like(t), t]).T
        cx, *_ = np.linalg.lstsq(A, x, rcond=None)
        cy, *_ = np.linalg.lstsq(A, y, rcond=None)
        rx, ry = x - A @ cx, y - A @ cy
        models[g] = {"cx": cx.tolist(), "cy": cy.tolist(),
                     "n": len(ns), "t_min": float(t.min()), "t_max": float(t.max()),
                     "residu_rms_px": float(np.sqrt((rx ** 2 + ry ** 2).mean())),
                     "residu_max_px": float(np.hypot(rx, ry).max()),
                     "deriva_px_s": [float(cx[1]), float(cy[1])],
                     "deriva_arcsec_s": float(math.hypot(cx[1], cy[1]) * ESCALA)}

    out = {}
    for grup in rafegues(tt):
        ancorats = [n for n in grup if n in anc]
        for n in grup:
            t, e, e_nom = tt[n]
            if n in EXCLOSES:
                out[n] = {"estat": "EXCLOS", "motiu": EXCLOSES[n], "t": t, "exp_s": e}
                continue
            if e < CONTACTE_MAX_S:
                out[n] = {"estat": "FORA_D_ABAST", "t": t, "exp_s": e,
                          "motiu": ("bloc de contacte: sense estrelles ni limbe net, i amb "
                                    "w = t²/… la seva aportació a la corona és menyspreable")}
                continue
            if n in anc:
                dx, dy, g = anc[n]
                out[n] = {"estat": "ADMES", "origen": "estrelles", "grup": g,
                          "t": t, "exp_s": e, "dx": dx, "dy": dy,
                          "incertesa_px": 0.0}
                continue
            if not ancorats:
                out[n] = {"estat": "EXCLOS", "t": t, "exp_s": e,
                          "motiu": "cap àncora d'estrelles a la seva ràfega"}
                continue
            g = anc[ancorats[0]][2]
            abans = sorted((a for a in ancorats if tt[a][0] <= t), key=lambda k: tt[k][0])
            despres = sorted((a for a in ancorats if tt[a][0] >= t), key=lambda k: tt[k][0])
            a = abans[-1] if abans else None
            b = despres[0] if despres else None
            if a is not None and b is not None and tt[b][0] > tt[a][0]:
                ta, tb = tt[a][0], tt[b][0]
                f = (t - ta) / (tb - ta)
                dx = anc[a][0] + f * (anc[b][0] - anc[a][0])
                dy = anc[a][1] + f * (anc[b][1] - anc[a][1])
                origen, base = "rafega_interpolat", [a, b]
            else:
                a = min(ancorats, key=lambda k: abs(tt[k][0] - t))
                cx, cy = models[g]["cx"], models[g]["cy"]
                dx = anc[a][0] + cx[1] * (t - tt[a][0])
                dy = anc[a][1] + cy[1] * (t - tt[a][0])
                origen, base = "rafega_extrapolat", [a]
            # ⚠️ L'EXIF de la Sony **no porta subsegon**: el segon és la unitat
            # de temps que hi ha, i el que la posició heretada pot equivocar-se
            # és la deriva d'un segon.
            #
            # ⛔ I aquesta deriva NO pot sortir del model global del grup. Al
            # grup C el model dona 0,24 px/s, però entre 06991 (t=59) i 06993
            # (t=67) la posició es mou **4,18 px en 8 s = 0,52 px/s**: la
            # muntura encara s'assentava del salt. Un model llis ajustat a sis
            # punts que travessen un assentament infravalora la taxa allà on
            # més gran és. Es fa servir la taxa **local** entre les àncores que
            # envolten el fotograma, que és la que el pot moure de veritat.
            veins = sorted(ancorats, key=lambda k: abs(tt[k][0] - t))[:2]
            if len(veins) == 2 and tt[veins[0]][0] != tt[veins[1]][0]:
                v0, v1 = veins
                dtv = abs(tt[v1][0] - tt[v0][0])
                taxa = math.hypot(anc[v1][0] - anc[v0][0], anc[v1][1] - anc[v0][1]) / dtv
                font_taxa = f"local entre {v0} i {v1}"
            else:
                taxa = math.hypot(*models[g]["deriva_px_s"])
                font_taxa = f"model del grup {g} (sense parella local)"
            inc = taxa * 1.0
            estat = "ADMES" if inc <= 0.3 else "EXCLOS"
            out[n] = {"estat": estat, "origen": origen, "grup": g, "base": base,
                      "t": t, "exp_s": e, "dx": float(dx), "dy": float(dy),
                      "incertesa_px": round(inc, 4), "taxa_px_s": round(taxa, 4),
                      "font_de_la_taxa": font_taxa}
            if estat == "EXCLOS":
                out[n]["motiu"] = (f"la posició heretada pot equivocar-se {inc:.2f} px "
                                   f"—la muntura es movia a {taxa:.2f} px/s i l'EXIF de la "
                                   f"Sony no porta subsegon—, per damunt del límit de 0,3")
    return {"models_per_grup": models, "sol_referencia": list(SOL_REF),
            "escala_arcsec_px": ESCALA, "pa_north": PA_NORD, "fotogrames": out}


_cache: dict = {}


def master_dark(e: float) -> np.ndarray:
    """El màster del seu temps d'exposició, resolt pel VALOR i no pel nom.

    ⚠️ El nom del fitxer és `master_0.0333333333.npy` (deu tresos) i l'EXIF
    en dona `0.03333333333` (onze). Comparar cadenes falla, i falla en silenci
    fins que no hi ha fitxer. Es resol pel número, amb tolerància relativa, i
    es rebutja si no hi ha cap màster prou a prop.
    """
    if "index" not in _cache:
        idx = {}
        for q in MASTERS.glob("master_*.npy"):
            try:
                idx[float(q.stem.split("_", 1)[1])] = q
            except ValueError:
                continue
        _cache["index"] = idx
    idx = _cache["index"]
    millor = min(idx, key=lambda v: abs(v - e))
    if abs(millor - e) > 1e-4 * max(e, 1e-9):
        raise SystemExit(f"cap màster dark Sony per a {e} s (el més proper: {millor})")
    if millor not in _cache:
        _cache[millor] = np.load(idx[millor])
    return _cache[millor]


def flat_mosaic(shape: tuple[int, int]) -> np.ndarray:
    if "flat" not in _cache:
        c = np.load(FLAT_RADIAL)
        h, w = c.shape[1] * 2, c.shape[2] * 2
        m = np.empty((h, w), np.float32)
        m[0::2, 0::2] = c[0]; m[0::2, 1::2] = c[1]
        m[1::2, 0::2] = c[2]; m[1::2, 1::2] = c[3]
        _cache["flat"] = m
    return _cache["flat"][: shape[0], : shape[1]]


def calibra(nom: str) -> tuple[np.ndarray, np.ndarray]:
    """Mosaic en ADU sobre el fosc i màscara de saturació dura (dilatada).

    ⚠️ El màster dark de la Sony és 5320×8000 —tot el `raw_image`— i la part
    visible n'és 5320×7968 des del mateix origen (marges 0,0), o sigui que
    n'hi ha prou de retallar-lo. Ordre obligat: fosc → flat, i el flat sempre
    abans de qualsevol warp.
    """
    import cv2
    import rawpy
    tt = exif()
    e_nom = tt[nom][2]      # el màster dark va indexat pel NOMINAL
    with rawpy.imread(str(SRC / f"{nom}.ARW")) as raw:
        cru = raw.raw_image_visible.astype(np.float32)
    cru = cru[: cru.shape[0] // 2 * 2, : cru.shape[1] // 2 * 2]
    sat = cru >= POU
    mos = cru - master_dark(e_nom)[: cru.shape[0], : cru.shape[1]]
    mos /= flat_mosaic(mos.shape)
    sat = cv2.dilate(sat.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return mos, sat


def afi(sol_xy, centre) -> np.ndarray:
    """px del fotograma Sony → px del llenç comú (nord amunt, escala de la Vixen)."""
    import comu as C
    pa = math.radians(PA_NORD)
    R = np.array([[math.cos(pa), math.sin(pa)], [-math.sin(pa), math.cos(pa)]], float)
    A = (ESCALA / C.ESCALA) * R
    t = np.array(centre, float) - A @ np.array(sol_xy, float)
    return np.hstack([A, t[:, None]])


def porta_registre_sony(reg: dict, *, limit_px: float = 0.3) -> dict:
    """El registre Sony passa si cap fotograma admès no supera el límit.

    Dues fonts d'error i cadascuna es fita a part:

    * els **ancorats per estrelles** paguen el residu del model del seu grup
      —que aquí NO s'usa per posicionar-los, o sigui que és diagnòstic—;
    * els **heretats** paguen la quantització d'un segon de l'EXIF multiplicada
      per la deriva del seu grup. La Sony no escriu subsegon.
    """
    admesos = {n: v for n, v in reg["fotogrames"].items() if v["estat"] == "ADMES"}
    if not admesos:
        return {"estat": "FAIL", "motiu": "cap fotograma admès"}
    heretats = {n: v for n, v in admesos.items() if v["origen"] != "estrelles"}
    pitjor = max(admesos.values(), key=lambda v: v["incertesa_px"])
    ok = pitjor["incertesa_px"] <= limit_px
    return {"estat": "PASS" if ok else "FAIL", "limit_px": limit_px,
            "n_admesos": len(admesos), "n_per_estrelles": len(admesos) - len(heretats),
            "n_heretats_de_rafega": len(heretats),
            "n_exclosos": sum(1 for v in reg["fotogrames"].values() if v["estat"] == "EXCLOS"),
            "n_fora_d_abast": sum(1 for v in reg["fotogrames"].values()
                                  if v["estat"] == "FORA_D_ABAST"),
            "pitjor_incertesa_px": pitjor["incertesa_px"],
            "residu_dels_models_per_grup": {g: {"rms_px": round(m["residu_rms_px"], 4),
                                                "max_px": round(m["residu_max_px"], 4),
                                                "n": m["n"],
                                                "deriva_arcsec_s": round(m["deriva_arcsec_s"], 4)}
                                            for g, m in reg["models_per_grup"].items()},
            "nota": ("el model per grup NO posiciona cap fotograma ancorat: aquells van amb "
                     "la seva mesura d'estrelles. El del grup C té 1,9 px de residu perquè "
                     "la muntura encara s'assentava del salt, i per això només s'hi "
                     "INTERPOLA entre germans, mai s'hi extrapola una deriva llisa.")}
