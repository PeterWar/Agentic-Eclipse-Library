"""Pilot Vixen · constants, lectura i calibratge.

Traspàs `.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md`, amb les portes F0 i F1
REFORMULADES el 23-08 al vespre després que el preflight de Codex (`research/98`)
demostrés que, tal com estaven escrites, no les pot passar cap dada de la Vixen:

* **F0 antiga**: «el flat aplicat ha de reproduir el que es va mesurar,
  coef. 1,00 ± 0,05». Aquella mesura és de la SONY i existeix perquè la seva
  muntura va saltar 750 px. La Vixen només mou el Sol 27,6 px en tota la
  totalitat i el flat radial hi canvia un 0,11 %: no hi ha palanca, i no n'hi
  pot haver. La porta no era estricta, era impossible.
* **F1 antiga**: «residu ≤ 0,3 px rms al llenç comú». Codex la va avaluar contra
  el residu de la SOLUCIÓ DE PLACA (0,424 px sobre 22 estrelles). Aquell error és
  COMÚ als 68 fotogrames —una sola solució per a tots— i per tant no desenfoca
  l'apilat: el que el desenfoca és el centre PER FOTOGRAMA.

Reformulació, a `portes.py`:

* **F0'** = coherència entre esglaons d'exposició al mateix anell, que sí que té
  palanca i que caça les dues coses que la Vixen pot equivocar (fosc i temps
  d'exposició); més una fita d'amplitud sobre el flat, que s'aplica com a
  CANDIDAT DECLARAT i es publica també la composició sense ell.
* **F1'** = precisió del centre per fotograma amb oracle held-out leave-one-out,
  ledger d'exclusions i cota del gir de camp.

⚠️ TROBALLA D'AQUEST PILOT: els temps d'exposició del manifest són els NOMINALS
del menú i el cos no els fa. L'escala física surt de `TargetExposureTime` del
MakerNote i difereix fins a un **6,25 %** (1/60, 1/30 i 1/15 nominals són de fet
1/64, 1/32 i 1/16). Un error d'escala entre esglaons és exactament el que fa
els anells de fusió, o sigui que això no és cosmètic.
"""
from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HOME = Path.home()
DESK = HOME / "Desktop" / "Eclipse 2026"
REPO = HOME / "Downloads" / "Eclipse 2026"

SRC = DESK / "Vixen R6III" / "Vixen Fase totalitat"
MASTERS = SRC / "Masters_v2"
MANIFEST = DESK / "Derivats" / "Vixen" / "Corona_HDR_Vixen" / "manifest.csv"
PLACA = (DESK / "Derivats" / "Astrometria" / "Estrelles"
         / "Resultats_acceptacio_2026-08-17" / "final_solution.json")
# ⛔ Quin camp òptic del màster s'aplica. Els 28 flats amb el cos girat del
# 24-08 (`research/100`) donen el veredicte de cadascun, mesurat entre dos cels
# independents com a fracció de la seva pròpia amplitud:
#
#   RADIAL    2,2-3,4 %  →  ÒPTICA, validat. És el que s'aplica per defecte.
#   EVEN180   2,3-3,0 %  →  ÒPTICA, validat. Val 0,05 % més a 1 R☉ i fins a
#                           0,9 % de dispersió azimutal a 5-7 R☉, que és on
#                           s'ajusta el model de cel: allà sí que compta.
#   SMOOTH2D  18-20 %    →  ⛔ EN QUARANTENA: una cinquena part és el cel del
#                           vespre del 22 d'agost. No es pot triar.
_FLATS = {
    "radial": "MASTER_OPTICAL_RADIAL_CFA4.npy",
    "even180": "MASTER_OPTICAL_EVEN180_CFA4.npy",
}
_CAMP = os.environ.get("PILOT_FLAT", "radial").lower()
if _CAMP not in _FLATS:
    raise SystemExit(f"PILOT_FLAT ha de ser {' o '.join(_FLATS)}; SMOOTH2D és en quarantena")
FLAT_CAMP = _CAMP
FLAT_RADIAL = (REPO / "output" / "flats_20260822" / "vixen_r6iii_posterior_v1"
               / _FLATS[_CAMP])

# ---------------------------------------------------------------- constants
# Escala i orientació: solució de placa r6_radial, 22 estrelles. El seu residu
# de 0,424 px és COMÚ als 68 fotogrames i no entra a la porta de registre.
_PL = json.loads(PLACA.read_text())["r6_radial"]
ESCALA = float(_PL["scale"])            # 2,1494813525884373 ″/px
PA_NORD = float(_PL["pa_north"])        # 57,194988546068025°

RSOL_ARCSEC = 947.068                   # radi solar aparent del dia (⛔ no 959,7)
R_SOL_PX = RSOL_ARCSEC / ESCALA         # 440,60 px
R_LLUNA_PX = 460.0                      # research/75 §6

FB = 2.772e-11                          # B/B☉ per ADU/s (research/75 §5.2)

POU = 16383.0                           # nivell de blanc de la R6 III
PEDESTAL = 511.5                        # pedestal pla real (⛔ no el de libraw)
# ⛔ El sostre és configurable NOMÉS per a la prova de moure les fronteres: si
# es baixa, cada exposició satura més enfora i **totes les fronteres de fusió es
# desplacen**. És la manera de decidir sense estadística si un arc és artefacte:
# es refà el compost amb un sostre diferent i es mira si l'arc s'hi ha mogut.
# ⚠️ El valor de producció és 0,85; qualsevol altre és NOMÉS per a la prova.
_FSOS = float(os.environ.get("PILOT_SOSTRE", "0.85"))
SOSTRE = _FSOS * (POU - PEDESTAL)       # 13.490,8 comptes útils sobre el fosc
RAMPA_SOSTRE = float(os.environ.get("PILOT_RAMPA", "0.80"))                     # rampa de sortida; 0,25 deixava graó d'1,6 %

GUANY = {"R": 5.08, "G1": 5.08, "G2": 5.08, "B": 4.33}   # e⁻/ADU, research/75 §3
RN_CURT, RN_LLARG = 2.72, 1.05                            # ADU segons mode de lectura
LLINDAR_MODE_S = 1.0

FONS_ANELL = (4.2, 5.1)                 # anell d'anivellament de cel, en R☉
F0_ANELL = (1.6, 3.2)                   # anell de comparació entre esglaons

MARGE_LLENC = 8                         # px de coixí al perímetre

# Escala física d'exposició, de `TargetExposureTime` (MakerNote Canon). La clau
# és l'`exp_nominal` del manifest; el valor, els segons que el cos fa de veritat.
EXP_FISICA = {
    0.0003125: 0.000307597912571991,
    0.0005: 0.00048828125,
    0.001: 0.0009765625,
    0.002: 0.001953125,
    0.004: 0.00390625,
    0.008: 0.0078125,
    0.01666666667: 0.015625,
    0.03333333333: 0.03125,
    0.06666666667: 0.0625,
    0.125: 0.125,
    0.25: 0.25,
    0.5: 0.5,
    1.0: 1.0,
    2.0: 2.0,
    10.0: 10.079368399159,
}


def clau_master(e_nom: float) -> str:
    """El nom del màster dark, que va indexat pel nominal i no pel físic."""
    s = f"{e_nom:.10g}"
    return s.rstrip("0").rstrip(".") if "." in s else s


@dataclass
class Fotograma:
    nom: str
    t_rel_c2: float
    exp_nominal: float
    exp_manifest: float
    exp_s: float                 # física, de TargetExposureTime
    temp_C: float
    sol_x: float
    sol_y: float
    lluna_x: float
    lluna_y: float
    limbe_n: int
    limbe_rms: float
    n_sat: int
    nota: str
    sigma_centre: float = math.nan   # error formal del centre, px
    origen_centre: str = ""          # "limbe" o "model"
    sol_usat: tuple[float, float] = (math.nan, math.nan)
    diagnostic: dict = field(default_factory=dict)


def llegeix_manifest() -> list[Fotograma]:
    fg: list[Fotograma] = []
    for r in csv.DictReader(MANIFEST.open()):
        if r["usat"] != "True":
            continue
        e_nom = float(r["exp_nominal"])
        if e_nom not in EXP_FISICA:
            raise SystemExit(f"exposició nominal sense equivalent físic: {e_nom}")
        fg.append(Fotograma(
            nom=r["nom"], t_rel_c2=float(r["t_rel_c2"]), exp_nominal=e_nom,
            exp_manifest=float(r["exp_s"]), exp_s=EXP_FISICA[e_nom],
            temp_C=float(r["temp_C"]), sol_x=float(r["sol_x"]), sol_y=float(r["sol_y"]),
            lluna_x=float(r["lluna_x"]), lluna_y=float(r["lluna_y"]),
            limbe_n=int(r["limbe_n"]), limbe_rms=float(r["limbe_rms"]),
            n_sat=int(r["n_sat"]), nota=r["nota"]))
    fg.sort(key=lambda f: f.t_rel_c2)
    return fg


# ---------------------------------------------------------------- calibratge
_cache: dict[str, np.ndarray] = {}


def master_dark(e_nom: float) -> np.ndarray:
    k = clau_master(e_nom)
    if k not in _cache:
        _cache[k] = np.load(MASTERS / f"master_{k}.npy")
    return _cache[k]


def prnu() -> dict[tuple[int, int], np.ndarray]:
    """PRNU per pla. Sense això surt walking noise: la muntura deriva en línia
    recta i el PRNU d'1,3-1,6 % queda escombrat en traços diagonals."""
    if "prnu" not in _cache:
        z = np.load(MASTERS / "prnu.npz")
        _cache["prnu"] = {(int(k[0]), int(k[1])): z[k] for k in z.files}
    return _cache["prnu"]


def flat_mosaic(shape: tuple[int, int]) -> np.ndarray:
    """El màster radial CFA4 desplegat al mosaic RGGB, retallat a `shape`.

    El CFA4 va sobre la reixa autoritzada 4640x6960 des del mateix origen
    (108,172) que `raw_image_visible`, o sigui que la fase de Bayer coincideix i
    n'hi ha prou de retallar. Es queda a 4638x6958, que és el que cobreix el
    màster dark: així **no hi ha cap vora sense dada** i no cal replicar res —
    replicar la vora del fosc costa fins a 64 ADU a 10 s (`research/98`).
    """
    if "flat" not in _cache:
        c = np.load(FLAT_RADIAL)          # (4, 2320, 3480) ordre R, G1, G2, B
        h, w = c.shape[1] * 2, c.shape[2] * 2
        m = np.empty((h, w), np.float32)
        m[0::2, 0::2] = c[0]
        m[0::2, 1::2] = c[1]
        m[1::2, 0::2] = c[2]
        m[1::2, 1::2] = c[3]
        _cache["flat"] = m
    return _cache["flat"][: shape[0], : shape[1]]


def parell(a: np.ndarray) -> np.ndarray:
    return a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]


def calibra(f: Fotograma, *, amb_flat: bool = True, amb_prnu: bool = True,
            dark: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Mosaic en ADU sobre el fosc i màscara de saturació dura (dilatada).

    Ordre obligat: fosc → PRNU → flat. ⛔ El flat va SEMPRE abans de qualsevol
    warp: un flat i un warp no commuten.
    """
    import cv2
    import rawpy
    with rawpy.imread(str(SRC / f.nom)) as raw:
        cru = parell(raw.raw_image_visible).astype(np.float32)
    sat = cru >= POU
    mos = cru - (master_dark(f.exp_nominal) if dark else np.float32(PEDESTAL))
    if amb_prnu:
        for (oy, ox), g in prnu().items():
            mos[oy::2, ox::2] /= (1.0 + g)
    if amb_flat:
        mos /= flat_mosaic(mos.shape)
    sat = cv2.dilate(sat.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return mos, sat


def plans(mosaic: np.ndarray) -> dict[str, tuple[np.ndarray, int, int]]:
    return {"R": (mosaic[0::2, 0::2], 0, 0), "G1": (mosaic[0::2, 1::2], 0, 1),
            "G2": (mosaic[1::2, 0::2], 1, 0), "B": (mosaic[1::2, 1::2], 1, 1)}


def afi(sun_xy: tuple[float, float], centre: tuple[float, float]) -> np.ndarray:
    """px del fotograma → px del llenç: gira perquè el nord quedi amunt.

    L'escala ja és la mateixa als dos costats (el llenç adopta la de la Vixen),
    o sigui que aquí només hi ha rotació i translació.
    """
    pa = math.radians(PA_NORD)
    R = np.array([[math.cos(pa), math.sin(pa)],
                  [-math.sin(pa), math.cos(pa)]], float)
    t = np.array(centre, float) - R @ np.array(sun_xy, float)
    return np.hstack([R, t[:, None]])


def anells(h: int, w: int, cy: float, cx: float) -> np.ndarray:
    y = (np.arange(h, dtype=np.float32) - cy)[:, None]
    x = (np.arange(w, dtype=np.float32) - cx)[None, :]
    return np.hypot(x, y)


def sha256(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# ⛔ ORDRE DE LA RAMPA de pes. Història, i cada graó el va destapar una imatge:
#   · clip LINEAL   → colze C⁰  → el passa-alt hi veu una vall de 0,07-0,14 %
#   · `smoothstep`  → colze C²  → **encara** hi veu un clot de 0,07-0,24 %
#   · `smootherstep`→ C²=0 als dos extrems
# El perfil transversal de la costura és un **CLOT**, no un graó: els dos
# extrems valen zero i el centre baixa. Un desajust de nivell faria un graó;
# un clot és la resposta d'un passa-alt a un canvi de CURVATURA.
_ORDRE_RAMPA = int(os.environ.get("PILOT_ORDRE_RAMPA", "5"))


def rampa(u: np.ndarray) -> np.ndarray:
    """Rampa suau de 0 a 1 sobre `u` ∈ [0, 1], amb l'ordre de continuïtat que
    demani `PILOT_ORDRE_RAMPA` (3 = smoothstep, 5 = smootherstep, 7 = següent).

    ⛔ Totes tenen `f(0)=0`, `f(1)=1` i `f'=0` als extrems; el que canvia és
    quantes derivades més s'hi anul·len. Cada ordre que s'hi afegeix treu una
    generació d'artefactes del passa-alt.
    """
    u = np.clip(u, 0.0, 1.0)
    if _ORDRE_RAMPA <= 3:
        return (u * u * (3.0 - 2.0 * u)).astype(np.float32)
    if _ORDRE_RAMPA <= 5:
        return (u * u * u * (u * (u * 6.0 - 15.0) + 10.0)).astype(np.float32)
    return (u ** 4 * (u * (u * (u * -20.0 + 70.0) - 84.0) + 35.0)).astype(np.float32)


# ⛔ TOTS els comandaments que canvien el producte, amb el seu valor per defecte.
# El 25-08-2026 dues sortides amb sostres diferents tenien rebuts indistingibles,
# i el traspàs a Codex va acabar anomenant una decisió amb el nom d'un altre
# paràmetre. Un rebut que no diu amb quins paràmetres s'ha fet no és un rebut.
# ⚠️ Si afegeixes una variable nova al pilot, afegeix-la AQUÍ o el rebut mentirà
# per omissió. La prova `test_cap_variable_del_pilot_no_queda_fora_del_rebut`
# falla si te'n deixes una.
COMANDAMENTS = (
    ("PILOT_SOSTRE", "0.85", "tall dur de saturació de la VIXEN, fracció del pou útil"),
    ("PILOT_SOSTRE_SONY", "0.85", "tall dur de saturació de la SONY, fracció del seu pou útil"),
    ("PILOT_RAMPA", "0.80", "amplada del degradat de pes, fracció del tall (COMPARTIDA pels dos trens)"),
    ("PILOT_ORDRE_RAMPA", "5", "ordre de continuïtat de la rampa de pes"),
    ("PILOT_FLAT", "radial", "màster de flat del camp"),
    ("PILOT_VOLTES", "20", "voltes d'alternança de les dues passades de resta"),
    ("PILOT_MEITAT", None, "meitat A/B dins de cada esglaó"),
    ("PILOT_FAMILIA", None, "família d'esglaons: senars o parells"),
    ("PILOT_APRIMA", "0", "fotogrames descartats conservant tots els esglaons"),
    ("PILOT_PES_SUAU", "0", "px de suavitzat del senyal per al mapa de pes"),
    ("PILOT_NRGF_SG", None, "finestra Savitzky-Golay del NRGF"),
    ("PILOT_ESGLAONS_SEPARATS", None, "desa numerador i denominador per esglaó"),
    ("PILOT_SORTIDA", "pilot_vixen_claude_20260823", "directori de sortida"),
    ("PILOT_PREVIS", "= PILOT_SORTIDA", "directori d'on es llegeixen les fases prèvies"),
)


def parametres_efectius() -> dict:
    """Els paràmetres reals d'aquesta execució, **per tren**.

    ⛔ Declara els DOS trens sempre, passi el que passi. La versió anterior
    estampava el sostre de la Vixen a tots els rebuts, inclosos els de la Sony,
    que té el seu tall i la seva variable: amb `PILOT_SOSTRE=0.80` un rebut de
    la Sony declarava 0,80 quan els píxels s'havien tallat a 0,85. Declarar-los
    tots dos treu la possibilitat d'equivocar-se en endevinar de qui és el rebut.

    ⚠️ `sostre_fraccio` és el **tall dur** de saturació; `rampa_amplada` és una
    cosa DIFERENT: l'amplada del degradat de pes com a fracció d'aquell tall, i
    és **compartida** pels dos trens. El pes val 1 per sota de
    `(1 − rampa_amplada)·sostre` i baixa a 0 en arribar al tall.
    """
    cmd = {}
    for clau, defecte, que in COMANDAMENTS:
        hi_es = clau in os.environ
        cmd[clau] = {"valor": os.environ[clau] if hi_es else defecte,
                     "per_defecte": not hi_es, "que": que}
    out = {"comandaments": cmd,
           "flat": _CAMP,
           "ordre_rampa": _ORDRE_RAMPA,
           "rampa_amplada": float(RAMPA_SOSTRE),
           "vixen": {"sostre_fraccio": float(_FSOS),
                     "sostre_adu": float(SOSTRE),
                     "pes_ple_per_sota_adu": float((1.0 - RAMPA_SOSTRE) * SOSTRE)}}
    try:                                    # import mandrós: sony importa comu
        import sony as _SY
        out["sony"] = {"sostre_fraccio": float(_SY._FSOS),
                       "sostre_adu": float(_SY.SOSTRE),
                       "pes_ple_per_sota_adu": float((1.0 - RAMPA_SOSTRE) * _SY.SOSTRE)}
    except Exception as e:                  # un tren absent no pot trencar un rebut
        out["sony"] = {"no_declarable": f"{type(e).__name__}: {e}"}
    return out


def desa_json(desti, valor, *, estampa: bool = True):
    """Escriu un JSON estampant-hi els paràmetres efectius.

    ⛔ És el pas obligat de **tots** els JSON del pilot, també els auxiliars de
    les eines de diagnòstic: un número sense els seus paràmetres al costat no es
    pot comparar amb cap altre d'un altre dia.
    """
    desti = Path(desti)
    desti.parent.mkdir(parents=True, exist_ok=True)
    if estampa and isinstance(valor, dict) and "parametres_del_pilot" not in valor:
        valor = {**valor, "parametres_del_pilot": parametres_efectius()}
    desti.write_text(json.dumps(valor, indent=1, ensure_ascii=False, allow_nan=False))
    return desti


def aplica_coherencia(mos: np.ndarray, factors: dict[str, float]) -> np.ndarray:
    """Divideix cada pla del mosaic pel seu factor de transparència.

    ⛔ Un sol número per pla i per fotograma. Aquesta és la salvaguarda: un
    escalar global no pot inventar-se estructura, només pot pujar o baixar el
    fotograma sencer. Vegeu `fase_coherencia` a `pilot.py`.
    """
    out = mos.astype(np.float32, copy=True)
    for nom, (_, oy, ox) in plans(mos).items():
        c = float(factors.get(nom, 1.0))
        if c > 0 and abs(c - 1.0) > 1e-12:
            out[oy::2, ox::2] /= np.float32(c)
    return out
