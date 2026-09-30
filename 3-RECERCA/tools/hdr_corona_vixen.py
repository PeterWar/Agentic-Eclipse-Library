#!/usr/bin/env python3
"""HDR de la corona solar amb el tren Vixen (VSD90SS + Canon R6 Mark III).

Eclipsi total del 12 d'agost de 2026, MIRADOR FINAL 2. Composa els 68
fotogrames de dins de la totalitat —quinze exposicions de 1/3200 a 10,3 s,
15,0 EV— en una sola imatge lineal centrada al SOL.

Decisions que segueixen `research/73`, `74` i `75`:

* **cap desbayerat.** Es treballa amb els quatre plans del mosaic (R, G1, G2,
  B). Interpolar correlaciona píxels veïns, barreja canals i falsifica tant el
  recompte de saturació com la sigma per píxel.
* **cap retall.** Ni a zero ni al blanc. El fons amb soroll ha de tenir mostres
  negatives; si es retallen, la mediana queda esbiaixada.
* **cap balanç de blancs ni matriu de color.** Amb els guanys de la R6 el canal
  vermell es retallaria 1,00 EV per sota del pou real.
* **pedestal real del master**, no el negre de metadata de libraw, que per a
  aquest cos (`[0,31,94,63]`) és fals.
* **drizzle sobre la reixa crua.** Cada pla de Bayer va submostrejat 1,7× i la
  deriva de la muntura (0,61 ″/s, constant) és el ditherat que cal per
  recuperar-ho. Les mostres es dipositen a la reixa de 2,1495 ″/px amb una
  gota de `pixfrac`; com que el registre és una translació pura, els pesos de
  solapament són els mateixos per a tots els píxels d'un pla i el dipòsit és
  una suma de llesques.
* **pesos òptims** `w = t² / (S/g + RN²)`, no trapezoïdals, amb el guany
  mesurat i el soroll de lectura que depèn del mode (la R6 canvia de mode de
  lectura entre 0,5 s i 1 s).
* **corona i Lluna no comparteixen alineació.** Es registra al Sol; el disc
  lunar de cada fotograma s'emmascara.

Etapes: `geometria` → `escala` → `hdr` → `vis`.
"""
from __future__ import annotations

import argparse
import csv
import os
import datetime as dt
import json
import math
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import rawpy

# ---------------------------------------------------------------- constants

SRC = Path.home() / "Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat"
MASTERS = SRC / "Masters_v2"
# CORONA_OUT permet fer una passada de prova en un altre directori sense tocar
# el producte viu (skill postprocessat-corona, 17-08-2026). Sense la variable,
# usa el derivat canònic.
OUT = Path(
    os.environ.get("CORONA_OUT")
    or (Path.home() / "Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen")
)
EFEMERIDE = Path(
    os.environ.get("EFEMERIDE") or (Path.home() / ".cache/skyfield/de440s.bsp")
).expanduser()


def carrega_efemeride():
    """Carrega DE440s de manera explícita; no baixa dades al cwd."""
    from skyfield.api import load

    if not EFEMERIDE.is_file():
        raise FileNotFoundError(
            f"falta l'efemèride {EFEMERIDE}; defineix EFEMERIDE o instal·la "
            "de440s.bsp a ~/.cache/skyfield/"
        )
    return load(str(EFEMERIDE))

# research/75 §5.1 — camp resolt amb 22 estrelles, residu 0,32 px
ESCALA = 2.1495          # ″/px a la reixa crua
PA_NORD = 57.19          # graus
PA_EST = 325.59
R_SOL_PX = 959.0 / ESCALA        # 446,15 px (radi solar aparent)
R_LLUNA_PX = 460.0               # research/75 §6

# research/75 §3 — guany i soroll de lectura mesurats
GUANY = {"R": 5.08, "G": 5.08, "B": 4.33}      # e⁻/ADU
RN_CURT, RN_LLARG = 2.72, 1.05                 # ADU, segons el mode de lectura
LLINDAR_MODE_S = 1.0

POU = 16383.0
PEDESTAL = 511.5
SOSTRE = 0.85 * (POU - PEDESTAL)   # 13 490,8 comptes útils per damunt del fosc

# Contactes reals, research/71: C2 −1,0 s del predit, totalitat 103,7 s.
C2_LOCAL = dt.datetime(2026, 8, 12, 20, 28, 45, 0)
TOTALITAT_S = 103.7
UTC_OFFSET_H = 2.0
LLOC = (42.299407, -5.02503, 798.0)   # MIRADOR FINAL 2

# L'esglaó profund declara 10,0 s a l'EXIF; el programa és l'autoritat.
EXP_REAL = {0.0003125: 1 / 3200, 10.0: 10.3}

# Amplada de la gota del drizzle, en píxels de SORTIDA. Compte amb la unitat:
# un píxel d'entrada d'un pla de Bayer fa DOS píxels de sortida, o sigui que el
# `pixfrac` clàssic de Fruchter i Hook val PIXFRAC/2. Per sota d'una gota d'un
# píxel de sortida apareix un escaquer a la diagonal de Nyquist: els plans cauen
# en caselles alternades i les que reben la gota de ple queden nítides mentre
# que les altres només en toquen la cua.
PIXFRAC = float(os.environ.get("PIXFRAC", "2.0"))

# Nivells de realçat. ⛔ La regla física que els fixa: el tren té un FWHM de
# 5,8 ″ = 2,70 px, o sigui una sigma de PSF d'1,15 px, i **per sota d'això no hi
# pot haver res real**. Realçar a sigma 1,25 i 2,5 px —com feia la primera
# versió— és amplificar soroll i la textura correlacionada del drizzle fins al
# mateix contrast que la corona, i el resultat sembla una imatge a la qual han
# tret el filtre antialiàsing. Les escales han de començar per damunt de 2×
# la sigma de la PSF, i el suavitzat final de 0,9 px torna a posar el filtre.
REALCATS = {
    "suau":  ([6, 12, 24, 48, 64], 0.50, 0.28, 0.9),
    "mitja": ([4, 8, 16, 32, 64],  0.60, 0.35, 0.0),
    "fort":  ([2.5, 5, 10, 20, 40, 80], 0.70, 0.45, 0.0),
}

# Retall (y0, y1, x0, x1) sense cap píxel sense aportació. ⛔ Es calcula amb
# ELS TRES canals: el vermell i el blau tenen menys cobertura que el verd i hi
# ha una franja on el verd ja té dades i ells no. Mirant només el verd, allà la
# cromaticitat es dispara i la vora surt magenta.
RETALL = (85, 4595, 40, 6830)

# research/75 §5.1 — el centre del Sol resolt amb 22 estrelles sobre 572A2983
ANCORA_NOM = "572A2983.CR3"
ANCORA_SOL = (3570.8, 2267.1)


def exp_real(e: float) -> float:
    return EXP_REAL.get(e, e)


def clau_master(e: float) -> str:
    return f"{e:.10g}"


def parell(a: np.ndarray) -> np.ndarray:
    return a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]


# ---------------------------------------------------------------- manifest

@dataclass
class Fotograma:
    nom: str
    t_rel_c2: float          # instant del mig de l'exposició, s des de C2 real
    exp_nominal: float
    exp_s: float
    temp_C: float
    lluna_x: float = math.nan     # centre lunar del MODEL, reixa crua
    lluna_y: float = math.nan
    lluna_mes_x: float = math.nan  # centre lunar MESURAT al limbe (o NaN)
    lluna_mes_y: float = math.nan
    limbe_n: int = 0
    limbe_rms: float = math.nan
    sol_x: float = math.nan       # centre solar derivat
    sol_y: float = math.nan
    n_sat: int = 0
    escala_rel: float = 1.0
    usat: bool = True
    nota: str = ""


def llegeix_exif() -> list[Fotograma]:
    fitxers = sorted(SRC.glob("*.CR3"))
    out = subprocess.run(
        ["exiftool", "-q", "-n", "-T", "-FileName", "-SubSecDateTimeOriginal",
         "-ExposureTime", "-CameraTemperature", *map(str, fitxers)],
        capture_output=True, text=True, check=True).stdout
    fg = []
    for linia in out.splitlines():
        nom, ts, exp, temp = linia.split("\t")
        t = dt.datetime.strptime(ts[:22], "%Y:%m:%d %H:%M:%S.%f")
        e_nom = float(exp)
        e = exp_real(e_nom)
        # l'EXIF de la R6 marca l'INICI de l'exposició (verificat: amb el
        # final, els dos fotogrames de 2 s se solaparien)
        t_mig = (t - C2_LOCAL).total_seconds() + e / 2
        fg.append(Fotograma(nom=nom, t_rel_c2=t_mig, exp_nominal=e_nom,
                            exp_s=e, temp_C=float(temp)))
    fg.sort(key=lambda f: f.t_rel_c2)
    return fg


def dins_totalitat(fg: list[Fotograma]) -> list[Fotograma]:
    return [f for f in fg if 0.0 <= f.t_rel_c2 <= TOTALITAT_S]


# ---------------------------------------------------------------- lectura

_cache_master: dict[str, np.ndarray] = {}


def master(e_nom: float) -> np.ndarray:
    k = clau_master(e_nom)
    if k not in _cache_master:
        _cache_master[k] = np.load(MASTERS / f"master_{k}.npy")
    return _cache_master[k]


_prnu: dict | None = None


def prnu() -> dict | None:
    """Mapa de guany píxel a píxel del sensor, mesurat a les pròpies dades.

    ⛔ Sense això surt **walking noise**: el PRNU val 1,3-1,6 % i, com que la
    muntura deriva en línia recta i monòtona sense cap ditherat aleatori, no es
    promitja sinó que queda escombrat en traços diagonals de 7,2 px a 46,7°,
    que és exactament la direcció i el recorregut de la deriva entre el primer
    i l'últim fotograma de 10,3 s. El detall és a `research/tools/prnu_vixen.py`.
    """
    global _prnu
    if _prnu is None:
        cami = MASTERS / "prnu.npz"
        if not cami.exists():
            print("⚠️ falta prnu.npz: executa research/tools/prnu_vixen.py")
            _prnu = {}
        else:
            z = np.load(cami)
            _prnu = {(int(k[0]), int(k[1])): z[k] for k in z.files}
    return _prnu or None


def calibra(f: Fotograma) -> tuple[np.ndarray, int]:
    """Mosaic calibrat en comptes crus per damunt del fosc (NO dividit pel
    temps) i recompte de fotolocalitats al pou."""
    with rawpy.imread(str(SRC / f.nom)) as raw:
        cru = parell(raw.raw_image_visible)
    n_sat = int((cru >= POU).sum())
    mos = cru.astype(np.float32) - master(f.exp_nominal)
    if os.environ.get("SENSE_PRNU") != "1":
        g = prnu()
        if g:
            for (oy, ox), m in g.items():
                mos[oy::2, ox::2] /= (1.0 + m)
    return mos, n_sat


def plans(mosaic: np.ndarray) -> dict[str, tuple[np.ndarray, int, int]]:
    """Els quatre plans del patró RGGB amb el seu desplaçament a la reixa."""
    return {
        "R":  (mosaic[0::2, 0::2], 0, 0),
        "G1": (mosaic[0::2, 1::2], 0, 1),
        "G2": (mosaic[1::2, 0::2], 1, 0),
        "B":  (mosaic[1::2, 1::2], 1, 1),
    }


# ---------------------------------------------------------------- geometria

def punts_limbe(g: np.ndarray, cy: float, cx: float, r: float,
                n_ang: int = 360) -> np.ndarray:
    """Creuament al 50 % entre l'interior del disc i la corona de fora."""
    ang = np.linspace(0, 2 * np.pi, n_ang, endpoint=False)
    rr = np.arange(r - 40, r + 40, 0.5)
    H, W = g.shape
    pts = []
    for a in ang:
        ys, xs = cy + rr * np.sin(a), cx + rr * np.cos(a)
        ok = (ys > 1) & (ys < H - 2) & (xs > 1) & (xs < W - 2)
        if ok.sum() < 40:
            continue
        prof = g[ys[ok].astype(int), xs[ok].astype(int)]
        dins, fora = np.median(prof[:15]), np.median(prof[-15:])
        if fora <= dins * 1.15:
            continue
        llindar = 0.5 * (dins + fora)
        i = int(np.argmax(prof > llindar))
        if i == 0 or i >= len(prof) - 1:
            continue
        p0, p1 = prof[i - 1], prof[i]
        frac = (llindar - p0) / (p1 - p0) if p1 != p0 else 0.0
        rc = rr[ok][i - 1] + frac * 0.5
        pts.append((cy + rc * math.sin(a), cx + rc * math.cos(a)))
    return np.asarray(pts)


def ajusta_cercle(pts: np.ndarray) -> tuple[float, float, float, int, float]:
    y, x = pts[:, 0].copy(), pts[:, 1].copy()
    cy = cx = r = 0.0
    d = np.zeros_like(x)
    for _ in range(5):
        A = np.c_[x, y, np.ones(len(x))]
        sol, *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
        cx, cy = sol[0] / 2, sol[1] / 2
        r = math.sqrt(sol[2] + cx ** 2 + cy ** 2)
        d = np.hypot(x - cx, y - cy) - r
        med = np.median(d)
        s = 1.4826 * np.median(np.abs(d - med))
        keep = np.abs(d - med) < 3 * max(s, 0.3)
        if keep.sum() < 40 or keep.all():
            break
        x, y = x[keep], y[keep]
    return cy, cx, r, len(x), float(np.std(d))


def vector_nord_est() -> tuple[np.ndarray, np.ndarray]:
    """Direccions nord i est al sensor, en (x, y) amb y cap avall."""
    def v(pa):
        a = math.radians(pa)
        return np.array([math.sin(a), -math.cos(a)])
    return v(PA_NORD), v(PA_EST)


def desplacament_lluna_sol(t_rel: np.ndarray) -> np.ndarray:
    """Offset Lluna − Sol al sensor, en píxels de la reixa crua, per efemèride.

    Retorna un array (N, 2) de (dx, dy). Requereix skyfield amb DE440s.
    """
    from skyfield.api import load, wgs84
    eph = carrega_efemeride()
    ts = load.timescale()
    terra, sol, lluna = eph["earth"], eph["sun"], eph["moon"]
    lloc = terra + wgs84.latlon(LLOC[0], LLOC[1], elevation_m=LLOC[2])
    base = C2_LOCAL - dt.timedelta(hours=UTC_OFFSET_H)
    n_hat, e_hat = vector_nord_est()
    out = np.empty((len(t_rel), 2))
    for i, dtr in enumerate(t_rel):
        inst = base + dt.timedelta(seconds=float(dtr))
        t = ts.utc(inst.year, inst.month, inst.day, inst.hour, inst.minute,
                   inst.second + inst.microsecond * 1e-6)
        obs = lloc.at(t)
        ra_l, de_l, _ = obs.observe(lluna).apparent().radec()
        ra_s, de_s, _ = obs.observe(sol).apparent().radec()
        d_est = (ra_l.radians - ra_s.radians) * math.cos(de_s.radians)
        d_nord = de_l.radians - de_s.radians
        arcsec = 206264.806
        vec = (d_est * arcsec) * e_hat + (d_nord * arcsec) * n_hat
        out[i] = vec / ESCALA
    return out


def etapa_geometria(args) -> None:
    fg = dins_totalitat(llegeix_exif())
    print(f"{len(fg)} fotogrames dins la totalitat "
          f"({len({f.exp_s for f in fg})} exposicions úniques)")

    cy0, cx0 = 2267.1 / 2, 3570.8 / 2      # llavor: research/75, mitja resolució
    for f in fg:
        mos, f.n_sat = calibra(f)
        g = 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2])
        cy, cx = cy0, cx0
        n = 0
        rms = math.nan
        for _ in range(3):
            pts = punts_limbe(g, cy, cx, R_LLUNA_PX / 2)
            if len(pts) < 60:
                break
            cy, cx, _r, n, rms = ajusta_cercle(pts)
        if n >= 200 and rms < 1.5:          # rms en píxels de mitja resolució
            f.lluna_mes_x, f.lluna_mes_y = 2 * cx, 2 * cy
            f.limbe_n, f.limbe_rms = n, 2 * rms
        else:
            f.limbe_n, f.limbe_rms = n, 2 * rms
            f.nota = "limbe no fiable"
        print(f"  {f.nom} C2{f.t_rel_c2:+7.2f} {f.exp_s:<9.6g} "
              f"lluna=({f.lluna_mes_x:8.2f},{f.lluna_mes_y:8.2f}) n={f.limbe_n:3d} "
              f"rms={f.limbe_rms:5.2f} sat={f.n_sat}")

    # --- model de deriva: recta robusta sobre els centres fiables
    bo = [f for f in fg if not math.isnan(f.lluna_mes_x)]
    t = np.array([f.t_rel_c2 for f in bo])
    px = np.array([f.lluna_mes_x for f in bo])
    py = np.array([f.lluna_mes_y for f in bo])
    coef = {}
    for eix, val in (("x", px), ("y", py)):
        m = np.ones(len(t), bool)
        for _ in range(4):
            a, b = np.polyfit(t[m], val[m], 1)
            res = val - (a * t + b)
            s = 1.4826 * np.median(np.abs(res[m] - np.median(res[m])))
            m = np.abs(res) < 3 * max(s, 0.2)
        coef[eix] = (a, b, float(np.std(res[m])), int(m.sum()))
    print(f"\nderiva lunar al sensor: dx/dt={coef['x'][0]:+.5f} px/s  "
          f"dy/dt={coef['y'][0]:+.5f} px/s")
    v_lluna = math.hypot(coef['x'][0], coef['y'][0])
    print(f"  |v| = {v_lluna:.4f} px/s = {v_lluna*ESCALA:.4f} ″/s   "
          f"residus: x {coef['x'][2]:.2f} px ({coef['x'][3]} punts), "
          f"y {coef['y'][2]:.2f} px ({coef['y'][3]})")

    # --- centre solar = centre lunar − offset d'efemèride
    tt = np.array([f.t_rel_c2 for f in fg])
    rel = desplacament_lluna_sol(tt)
    lluna_mod = np.c_[coef['x'][0] * tt + coef['x'][1],
                      coef['y'][0] * tt + coef['y'][1]]
    sol = lluna_mod - rel
    # Ancoratge absolut: la traça relativa surt del limbe i de l'efemèride,
    # però el ZERO el posa la placa estel·lar de research/75 §5.1, que és molt
    # més forta (22 estrelles, residu 0,32 px). Sense això el centre queda 3,6
    # px desplaçat i tots els radis en R☉ hereten el biaix.
    i_anc = [f.nom for f in fg].index(ANCORA_NOM)
    print(f"\n  ancoratge: centre del Sol a {ANCORA_NOM} = "
          f"({sol[i_anc,0]:.1f},{sol[i_anc,1]:.1f}) mesurat → "
          f"({ANCORA_SOL[0]}, {ANCORA_SOL[1]}) de la placa estel·lar "
          f"(desplaçament {math.hypot(sol[i_anc,0]-ANCORA_SOL[0], sol[i_anc,1]-ANCORA_SOL[1]):.2f} px)")
    sol = sol + (np.array(ANCORA_SOL) - sol[i_anc])
    # el centre lunar de treball és sempre el del MODEL: als 26 fotogrames
    # de 1/3200 el limbe no es pot mesurar (perles i anell de diamant) i una
    # màscara lunar que hi faltés deixaria entrar el disc a la composició
    lluna_anc = lluna_mod + (sol - (lluna_mod - rel))[0]   # mateix ancoratge
    for i, f in enumerate(fg):
        f.sol_x, f.sol_y = float(sol[i, 0]), float(sol[i, 1])
        f.lluna_x, f.lluna_y = float(lluna_anc[i, 0]), float(lluna_anc[i, 1])

    vs = (sol[-1] - sol[0]) / (tt[-1] - tt[0])
    vr = (rel[-1] - rel[0]) / (tt[-1] - tt[0])
    print(f"\n  Lluna−Sol per efemèride: {math.hypot(*vr)*ESCALA:.4f} ″/s "
          f"(esperat 0,5905)")
    print(f"  deriva de la muntura   : {math.hypot(*vs)*ESCALA:.4f} ″/s "
          f"(research/75: 0,610 ± 0,010)  direcció "
          f"{math.degrees(math.atan2(-vs[1], vs[0])):+.1f}° al sensor")
    print(f"  centre del Sol a 572A2983 = ({sol[[f.nom for f in fg].index('572A2983.CR3')][0]:.1f}, "
          f"{sol[[f.nom for f in fg].index('572A2983.CR3')][1]:.1f}) "
          f"— placa estel·lar: (3570.8, 2267.1)")

    OUT.mkdir(parents=True, exist_ok=True)
    desa_manifest(fg)
    (OUT / "geometria.json").write_text(json.dumps({
        "deriva_lluna_px_s": {k: v[0] for k, v in coef.items()},
        "residu_px": {k: v[2] for k, v in coef.items()},
        "v_lluna_arcsec_s": v_lluna * ESCALA,
        "v_muntura_arcsec_s": float(math.hypot(*vs) * ESCALA),
        "v_lluna_sol_arcsec_s": float(math.hypot(*vr) * ESCALA),
        "escala_arcsec_px": ESCALA, "pa_nord": PA_NORD, "pa_est": PA_EST,
    }, indent=1))
    print(f"\n→ {OUT/'manifest.csv'}")


CAMPS = list(Fotograma.__dataclass_fields__)


def desa_manifest(fg: list[Fotograma]) -> None:
    with open(OUT / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, CAMPS)
        w.writeheader()
        for f in fg:
            w.writerow(asdict(f))


def llegeix_manifest() -> list[Fotograma]:
    fg = []
    with open(OUT / "manifest.csv") as fh:
        for row in csv.DictReader(fh):
            d = {}
            for k, v in row.items():
                tipus = Fotograma.__dataclass_fields__[k].type
                if k in ("nom", "nota"):
                    d[k] = v
                elif k == "usat":
                    d[k] = v == "True"
                elif k in ("limbe_n", "n_sat"):
                    d[k] = int(v)
                else:
                    d[k] = float(v)
            fg.append(Fotograma(**d))
    return fg


# ---------------------------------------------------------------- escala

def anells(h: int, w: int, cy: float, cx: float) -> np.ndarray:
    y = (np.arange(h) - cy)[:, None]
    x = (np.arange(w) - cx)[None, :]
    return np.hypot(x, y)


def normalitza_radial(g: np.ndarray, cy: float, cx: float,
                      r_int: float, r_ext: float) -> np.ndarray:
    """Imatge auxiliar de registre: corona dividida pel seu perfil radial.

    El gradient radial de la corona és enorme i suau; una correlació el
    persegueix a ell i no a les estructures. Dividint pel perfil azimutal
    medià queden les bagues i els plomalls, que és el que s'ha d'alinear.
    ⚠️ Aquesta imatge NO és el producte: només serveix per trobar el
    desplaçament (Druckmüller 2009 fa el mateix amb un filtre tangencial).
    """
    r = anells(*g.shape, cy, cx)
    ib = np.clip(((r - r_int) / 2.0).astype(int), 0, None)
    n_b = int((r_ext - r_int) / 2.0) + 1
    dins = (r >= r_int) & (r < r_ext) & np.isfinite(g)
    perfil = np.ones(n_b + 2)
    for k in range(n_b):
        m = dins & (ib == k)
        if m.sum() > 200:
            perfil[k] = max(np.median(g[m]), 1e-6)
    aux = np.zeros_like(g)
    idx = np.clip(ib, 0, n_b + 1)
    aux[dins] = g[dins] / perfil[idx[dins]] - 1.0
    return np.clip(aux, -1.0, 1.0)


def etapa_deriva(args) -> None:
    """Mesura la deriva del SOL directament de la corona, sense efemèrides.

    Per a cada esglaó d'exposició amb més d'un fotograma dins la totalitat es
    correlacionen les imatges auxiliars normalitzades. El resultat és el
    desplaçament de la corona al sensor, o sigui la deriva de la muntura, i és
    independent tant del limbe lunar com de skyfield.
    """
    from skimage.registration import phase_cross_correlation

    fg = [f for f in llegeix_manifest() if f.usat]
    per_exp: dict[float, list[Fotograma]] = {}
    for f in fg:
        per_exp.setdefault(f.exp_s, []).append(f)

    # mig camp al voltant del Sol, a mitja resolució
    L = 1000
    aux_cache: dict[str, np.ndarray] = {}
    finestra = np.outer(np.hanning(2 * L), np.hanning(2 * L)).astype(np.float32)

    def auxiliar(f: Fotograma) -> np.ndarray | None:
        if f.nom in aux_cache:
            return aux_cache[f.nom]
        mos, _ = calibra(f)
        g = 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2]) / f.exp_s
        sat = (mos[0::2, 1::2] > SOSTRE) | (mos[1::2, 0::2] > SOSTRE)
        g = np.where(sat, np.nan, g)
        cy, cx = f.sol_y / 2, f.sol_x / 2
        a = normalitza_radial(g, cy, cx, (R_LLUNA_PX + 30) / 2, 2000 / 2)
        y0, x0 = int(round(cy)) - L, int(round(cx)) - L
        if y0 < 0 or x0 < 0 or y0 + 2 * L > a.shape[0] or x0 + 2 * L > a.shape[1]:
            pad = np.zeros((2 * L, 2 * L), np.float32)
            ys, xs = max(y0, 0), max(x0, 0)
            sub = a[ys:y0 + 2 * L, xs:x0 + 2 * L]
            pad[ys - y0:ys - y0 + sub.shape[0], xs - x0:xs - x0 + sub.shape[1]] = sub
            a = pad
        else:
            a = a[y0:y0 + 2 * L, x0:x0 + 2 * L]
        # el retall va referit al centre solar arrodonit: cal recordar-ne el residu
        a = np.nan_to_num(a) * finestra
        aux_cache[f.nom] = a
        return a

    # ⚠️ R5 de research/74: qualsevol patró fix al sensor —pols, un reflex
    # intern, un gradient d'amplificador— correlaciona molt més fort que unes
    # estructures coronals de contrast baixíssim, i el màxim surt a
    # desplaçament zero *en coordenades de sensor*. Els esglaons amb el nucli
    # cremat en són les víctimes: no hi queda estructura de corona per guiar.
    SAT_MAX = 12000

    mesures, descartades = [], []
    print("parella          exp        Δt    mesurat (px cru)   model      "
          "residu del model")
    for e in sorted(per_exp):
        grup = per_exp[e]
        if len(grup) < 2:
            continue
        ref = grup[0]
        if ref.n_sat > SAT_MAX:
            descartades.append((e, "nucli cremat"))
            continue
        a_ref = auxiliar(ref)
        oy_ref = int(round(ref.sol_y / 2)) * 2
        ox_ref = int(round(ref.sol_x / 2)) * 2
        for f in grup[1:]:
            dt_s = f.t_rel_c2 - ref.t_rel_c2
            if abs(dt_s) < 8 or f.n_sat > SAT_MAX:
                continue
            a = auxiliar(f)
            desp, _err, _ = phase_cross_correlation(
                a_ref, a, upsample_factor=20, normalization="phase")
            # `desp` és el residu (dy,dx) a mitja resolució; el retall ja porta
            # la diferència dels centres solars arrodonits del model
            dy = -desp[0] * 2 + (int(round(f.sol_y / 2)) * 2 - oy_ref)
            dx = -desp[1] * 2 + (int(round(f.sol_x / 2)) * 2 - ox_ref)
            px, py = f.sol_x - ref.sol_x, f.sol_y - ref.sol_y
            if math.hypot(dx, dy) < 2.0 and math.hypot(px, py) > 4.0:
                print(f"  {ref.nom[-8:-4]}→{f.nom[-8:-4]} {e:<9.6g} {dt_s:+7.2f}"
                      f"  ({dx:+6.2f},{dy:+6.2f})  ⛔ enganxat al flare fix")
                continue
            mesures.append((ref.t_rel_c2, f.t_rel_c2, dx, dy, e))
            print(f"  {ref.nom[-8:-4]}→{f.nom[-8:-4]} {e:<9.6g} {dt_s:+7.2f}"
                  f"  ({dx:+6.2f},{dy:+6.2f}) ({px:+6.2f},{py:+6.2f})"
                  f"  ({dx-px:+5.2f},{dy-py:+5.2f})")
    for e, motiu in descartades:
        print(f"  {e:<9.6g} exclòs: {motiu}")

    if len(mesures) < 3:
        print("⛔ cap parella utilitzable")
        return
    dtv = np.array([m[1] - m[0] for m in mesures])
    bx = np.array([m[2] for m in mesures])
    by = np.array([m[3] for m in mesures])
    vx = float((dtv @ bx) / (dtv @ dtv))
    vy = float((dtv @ by) / (dtv @ dtv))
    rx, ry = bx - dtv * vx, by - dtv * vy
    v = math.hypot(vx, vy)
    print(f"\nderiva de la muntura MESURADA a la corona ({len(mesures)} parelles):")
    print(f"  ({vx:+.5f},{vy:+.5f}) px/s → |v| = {v*ESCALA:.4f} ″/s   "
          f"direcció {math.degrees(math.atan2(-vy, vx)):+.1f}° al sensor")
    print(f"  research/75, estrelles i traços: 0,610 ± 0,010 ″/s a 45,0°")
    print(f"  residu contra el model d'efemèrides: "
          f"x {rx.std():.2f} px, y {ry.std():.2f} px")
    (OUT / "deriva_corona.json").write_text(json.dumps({
        "vx_px_s": vx, "vy_px_s": vy, "v_arcsec_s": v * ESCALA,
        "direccio_graus": math.degrees(math.atan2(-vy, vx)),
        "residu_model_x_px": float(rx.std()), "residu_model_y_px": float(ry.std()),
        "n_parelles": len(mesures),
        "parelles": [{"t0": float(a), "t1": float(b), "dx": float(c),
                      "dy": float(d), "exp_s": float(e)}
                     for a, b, c, d, e in mesures],
    }, indent=1))
    print(f"→ {OUT/'deriva_corona.json'}")


def etapa_escala(args) -> None:
    """Calibratge relatiu de les exposicions, mesurat a les dades.

    L'obturació nominal no és la real. Per a cada parella d'esglaons
    consecutius es mesura la raó de les medianes anulars on totes dues estan
    ben exposades, i se'n deriva un factor per esglaó encadenat a 1/3200 = 1.
    """
    fg = [f for f in llegeix_manifest() if f.usat]
    radis = np.arange(1.06, 6.6, 0.04) * R_SOL_PX
    n_an = len(radis) - 1
    # el terme independent de la regressió ja absorbeix el fons, o sigui
    # que el terra pot ser baix: el que cal és PALANCA, o sigui rang
    SENYAL_MIN = 3.0
    SENYAL_MAX = 0.70 * SOSTRE        # lluny de la zona de rampa

    # perfil anular en ADU CRUS de cada fotograma (no dividit pel temps)
    perfils: dict[str, np.ndarray] = {}
    for f in fg:
        mos, _ = calibra(f)
        g = 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2])
        r = anells(*g.shape, f.sol_y / 2, f.sol_x / 2) * 2
        rl = anells(*g.shape, f.lluna_y / 2, f.lluna_x / 2) * 2
        ib = np.digitize(r, radis) - 1
        val = np.full(n_an, np.nan)
        bo = (ib >= 0) & (ib < n_an) & (rl > R_LLUNA_PX + 10)
        for i in range(n_an):
            m = bo & (ib == i)
            if m.sum() > 400:
                val[i] = np.median(g[m])
        perfils[f.nom] = val

    per_exp: dict[float, list[Fotograma]] = {}
    for f in fg:
        per_exp.setdefault(f.exp_s, []).append(f)
    exps = sorted(per_exp)

    # --- ajust global: p_f(r) = k_e(f)·t_f·C(r) + c_f
    #
    # Encadenar raons entre esglaons veïns fa un passeig aleatori: catorze
    # graons amb un 2-3 % d'error cadascun donen un 9 % al final, i llavors el
    # número que surt a l'esglaó profund és soroll acumulat i no pas obturador.
    # Aquí tots els esglaons s'ajusten alhora contra el MATEIX perfil de corona
    # i el fons difús de cada fotograma és un paràmetre propi.
    noms = [f.nom for f in fg]
    P = np.array([perfils[n] for n in noms])                    # (F, anells)
    T = np.array([f.exp_s for f in fg])
    IE = np.array([exps.index(f.exp_s) for f in fg])
    VAL = np.isfinite(P) & (P > SENYAL_MIN) & (P < SENYAL_MAX)

    k = np.ones(len(exps))
    c = np.zeros(len(fg))
    C = np.nanmedian(np.where(VAL, P / T[:, None], np.nan), axis=0)
    for _ in range(30):
        # perfil comú, mitjana ponderada pel senyal (que és el senyal/soroll)
        est = (P - c[:, None]) / (k[IE] * T)[:, None]
        pes = np.where(VAL, np.sqrt(np.maximum(P, 1.0)), 0.0)
        C = np.nansum(np.where(VAL, est * pes, 0), 0) / np.maximum(pes.sum(0), 1e-9)
        C = np.where(pes.sum(0) > 0, C, np.nan)
        # (k, c) de cada fotograma contra el perfil comú
        kf = np.ones(len(fg))
        for i in range(len(fg)):
            m = VAL[i] & np.isfinite(C)
            if m.sum() < 6:
                continue
            x, y = C[m], P[i][m]
            for _ in range(3):
                A = np.c_[x, np.ones(len(x))]
                (kk, cc), *_ = np.linalg.lstsq(A, y, rcond=None)
                res = y - (kk * x + cc)
                s = 1.4826 * np.median(np.abs(res - np.median(res)))
                keep = np.abs(res - np.median(res)) < 3 * max(s, 1e-6)
                if keep.sum() < 6 or keep.all():
                    break
                x, y = x[keep], y[keep]
            kf[i], c[i] = kk / T[i], cc
        for j in range(len(exps)):
            sel = IE == j
            if sel.any():
                k[j] = float(np.median(kf[sel]))
        k /= np.median(k)

    escala_glob = {e: float(1.0 / k[j]) for j, e in enumerate(exps)}
    print("ajust global (sense cadena):")
    print("  esglaó      factor    n fot.  anells vàlids  fons difús mitjà")
    for j, e in enumerate(exps):
        sel = IE == j
        print(f"  {e:<10.6g}  {escala_glob[e]:7.4f}   {sel.sum():3d}      "
              f"{VAL[sel].sum():5d}         {c[sel].mean():+8.1f} ADU")
    (OUT / "escala_global.json").write_text(json.dumps(
        {str(kk): vv for kk, vv in escala_glob.items()}, indent=1))

    escala = {exps[0]: 1.0}
    print("\nencadenat, només com a contrast:")
    print("esglaó                Δt     pendent/nominal  cel dif.  anells  palanca  acumulat")
    for a, b in zip(exps, exps[1:]):
        # La parella més junta en el temps: entre els dos fotogrames el cel
        # difús ha de canviar el mínim possible (research/74 el mesura caient
        # del 7 % al 23 % al llarg de la totalitat).
        millor = min(
            ((abs(fb.t_rel_c2 - fa.t_rel_c2), fa, fb)
             for fa in per_exp[a] for fb in per_exp[b]),
            key=lambda z: z[0])
        dt_s, fa, fb = millor
        pa, pb = perfils[fa.nom], perfils[fb.nom]
        m = (np.isfinite(pa) & np.isfinite(pb)
             & (pa > SENYAL_MIN) & (pa < SENYAL_MAX)
             & (pb > SENYAL_MIN) & (pb < SENYAL_MAX))
        if m.sum() < 6 or dt_s > 14.0:
            escala[b] = escala[a]
            print(f"  {a:<9.5g}→{b:<9.5g} {dt_s:6.2f}  ⛔ només {m.sum()} anells "
                  f"→ s'hereta {escala[b]:.4f}")
            continue
        # pb = k·pa + c : el pendent és la raó d'exposició real i l'ordenada a
        # l'origen absorbeix la diferència de fons difús. Un sol número de raó
        # els confondria, i el fons pesa justament on l'esglaó llarg viu.
        x, y = pa[m], pb[m]
        for _ in range(4):
            A = np.c_[x, np.ones(len(x))]
            (k, c), *_ = np.linalg.lstsq(A, y, rcond=None)
            res = y - (k * x + c)
            s = 1.4826 * np.median(np.abs(res - np.median(res)))
            keep = np.abs(res - np.median(res)) < 3 * max(s, 1e-6)
            if keep.sum() < 6 or keep.all():
                break
            x, y = x[keep], y[keep]
        rao = float(k) / (b / a)
        palanca = float(x.max() / max(x.min(), 1e-3))
        avis = "  ⚠️ poca palanca" if palanca < 5 else ""
        escala[b] = escala[a] * rao
        print(f"  {a:<9.5g}→{b:<9.5g} {dt_s:6.2f} {rao:11.4f}   "
              f"{c:+9.1f}   {len(x):3d}  ×{palanca:7.1f}  {escala[b]:.4f}{avis}")

    for f in fg:
        f.escala_rel = escala_glob[f.exp_s]
    tots = llegeix_manifest()
    mapa = {f.nom: f.escala_rel for f in fg}
    for f in tots:
        f.escala_rel = mapa.get(f.nom, 1.0)
    desa_manifest(tots)
    (OUT / "escala.json").write_text(json.dumps(
        {str(k): v for k, v in escala.items()}, indent=1))
    print(f"\n→ {OUT/'escala.json'}")


# ---------------------------------------------------------------- HDR

def pesos_gota(frac: float) -> tuple[int, np.ndarray]:
    """Pesos de solapament 1-D d'una gota de PIXFRAC centrada a `frac`.

    Retorna (índex del primer píxel de sortida, pesos normalitzats).
    """
    c = frac
    a, b = c - PIXFRAC / 2, c + PIXFRAC / 2
    k0 = math.floor(a)
    k1 = math.floor(b)
    ks = list(range(k0, k1 + 1))
    w = np.array([max(0.0, min(b, k + 1) - max(a, k)) for k in ks])
    return k0, w / w.sum()


# Anell on es mesura el fons de cada fotograma. Ha de caber SENCER dins el
# fotograma (el semieix curt són 5,20 R☉) i ser prou enfora perquè hi dominin
# el cel i la corona F i no l'estructura de la corona K.
FONS_ANELL = (4.2, 5.1)


def anivella_fons(fg: list[Fotograma]) -> dict[str, np.ndarray]:
    """Anivella el fons de cel dels 68 fotogrames abans de composar-los.

    ⛔ Aquesta és la correcció que treu els anells concèntrics, i el motiu és
    mesurat: **el cel de la totalitat no és estacionari**. La seva taxa al
    Vixen fa una V —509 ADU/s a C2+8, 335 al mig, 491 a C2+92, o sigui ±20 %—
    perquè prop de C2 i de C3 el punt d'observació és a tocar de la vora de
    l'ombra. Els tres fotogrames de 10,3 s cauen tots al fons d'aquella V.

    Com que cada radi del compost el domina un esglaó d'exposició diferent, i
    cada esglaó es va prendre en un instant diferent, **el compost portava un
    nivell de cel diferent a cada radi**, i els salts eren als radis on canvia
    l'esglaó dominant: les isofotes de saturació a 1,03 · 1,09 · 1,18 · 1,30 ·
    1,44 i 1,96 R☉.

    Es corregeix la DIFERÈNCIA entre fotogrames, no el nivell absolut: la
    corona no canvia en 100 s, o sigui que tot el que varia és cel. El nivell
    comú es conserva i la fotometria del compost no es toca.

    Retorna, per fotograma, el desplaçament a restar a cada pla de Bayer en
    comptes crus.
    """
    print(f"anivellament del fons a {FONS_ANELL[0]}–{FONS_ANELL[1]} R☉ "
          f"(el cel de la totalitat varia un ±20 %)")
    taxes: dict[str, np.ndarray] = {}
    ordre = ["R", "G1", "G2", "B"]
    for f in fg:
        mos, _ = calibra(f)
        t = f.exp_s * f.escala_rel
        v = []
        for nom in ordre:
            pla, oy, ox = plans(mos)[nom]
            rr = anells(*pla.shape, (f.sol_y - oy) / 2, (f.sol_x - ox) / 2) * 2
            m = (rr > FONS_ANELL[0] * R_SOL_PX) & (rr < FONS_ANELL[1] * R_SOL_PX)
            v.append(float(np.median(pla[m])) / t)
        taxes[f.nom] = np.array(v)
    ref = np.median(np.array([taxes[f.nom] for f in fg]), axis=0)
    print(f"  taxa de referència per pla (ADU/s): "
          f"{' '.join(f'{n}={r:.1f}' for n, r in zip(ordre, ref))}")
    rang = np.array([taxes[f.nom][1] for f in fg])
    print(f"  el verd va de {rang.min():.1f} a {rang.max():.1f} ADU/s "
          f"({100*(rang.max()-rang.min())/ref[1]:.1f} % de variació)")
    return {f.nom: (taxes[f.nom] - ref) * (f.exp_s * f.escala_rel) for f in fg}


def etapa_hdr(args) -> None:
    fg = [f for f in llegeix_manifest() if f.usat]
    OUT.mkdir(parents=True, exist_ok=True)
    mos0, _ = calibra(fg[0])
    H, W = mos0.shape
    cy_out, cx_out = H / 2.0, W / 2.0

    canals = ["R", "G", "B"]
    num = {c: np.zeros((H, W), np.float64) for c in canals}
    den = {c: np.zeros((H, W), np.float64) for c in canals}
    ncon = {c: np.zeros((H, W), np.uint16) for c in canals}

    ry = (np.arange(H) - cy_out)[:, None]
    rx = (np.arange(W) - cx_out)[None, :]
    r_out = np.hypot(rx, ry)

    # ⛔ Els factors de escala_global.json (±7 %) NO són obturador: un cos amb
    # obturador electrònic i rellotge de quars no falla un 7 %. Són el residu
    # de la variació del cel colada dins la separació k/c del seu ajust, i
    # multiplicaven el graó de les fronteres de saturació per 1,63.
    escala_unitat = os.environ.get("ESCALA_UNITAT", "1") == "1"
    # Rampa de sortida per saturació. Amb 0,25 el canvi d'esglaó dominant deixa
    # un graó de l'1,6 % al llarg de la isofota; amb 0,80 baixa al 0,66 %.
    rampa = float(os.environ.get("RAMPA_SOSTRE", "0.80"))
    nivells = None if os.environ.get("SENSE_FONS") == "1" else anivella_fons(fg)
    for k, f in enumerate(fg, 1):
        mos, _ = calibra(f)
        rn = RN_CURT if f.exp_s < LLINDAR_MODE_S else RN_LLARG
        t = f.exp_s * (1.0 if escala_unitat else f.escala_rel)
        # posició del disc lunar dins la reixa de sortida (centrada al Sol)
        dlx = f.lluna_x - f.sol_x + cx_out
        dly = f.lluna_y - f.sol_y + cy_out
        # ⚠️ Màscara lunar SUAU. La Lluna es desplaça **28,7 px** respecte del
        # Sol al llarg de la totalitat —de (+14,6, +3,7) a (−10,8, −9,8)—, o
        # sigui que amb un tall dur 0/1 cada píxel de la corona d'un anell
        # d'uns 30 px al voltant del limbe es componia d'un subconjunt
        # diferent de fotogrames, i hi sortia un anell del 20 %. La transició
        # de 14 px reparteix el canvi en lloc de concentrar-lo.
        # ⛔ I no s'ha de fer més ampla per treure les línies radials: no són
        # de la màscara. Recomposant sense màscara, el compost surt bit a bit
        # idèntic d'1,20 a 1,75 R☉, que és on viuen.
        d_ll = np.hypot(rx - (dlx - cx_out), ry - (dly - cy_out))
        pes_lluna = np.clip((d_ll - (R_LLUNA_PX + 4)) / 14.0, 0.0, 1.0)

        desp = ({"R": 0.0, "G1": 0.0, "G2": 0.0, "B": 0.0} if nivells is None
                else dict(zip(["R", "G1", "G2", "B"], nivells[f.nom])))
        for nom_pla, (pla, oy, ox) in plans(mos).items():
            pla = pla - desp[nom_pla]        # anivellament del cel del dia
            c = "G" if nom_pla.startswith("G") else nom_pla
            g = GUANY[c]
            s = np.maximum(pla, 0.0)
            var = s / g + rn * rn                       # ADU² per fotograma
            w = (t * t) / var                           # pes òptim en comptes/s
            # portes dures: saturació del sensor i sostre de linealitat
            fora = pla > SOSTRE
            taper = np.clip((SOSTRE - pla) / (rampa * SOSTRE), 0.0, 1.0)
            w = w * taper
            w[fora] = 0.0
            val = pla / t                                # comptes/s

            # posició de la mostra (i,j) a la reixa de sortida
            base_y = oy - (f.sol_y - cy_out)
            base_x = ox - (f.sol_x - cx_out)
            ky, wy = pesos_gota(base_y % 1.0)
            kx, wx = pesos_gota(base_x % 1.0)
            iy0 = math.floor(base_y)
            ix0 = math.floor(base_x)
            h, wd = pla.shape
            for a_i, wa in enumerate(wy):
                if wa <= 0:
                    continue
                Y = iy0 + ky + a_i
                for b_i, wb in enumerate(wx):
                    if wb <= 0:
                        continue
                    X = ix0 + kx + b_i
                    par_y, st_y = Y % 2, Y // 2
                    par_x, st_x = X % 2, X // 2
                    vy = slice(max(st_y, 0), min(st_y + h, (H - par_y + 1) // 2))
                    vx = slice(max(st_x, 0), min(st_x + wd, (W - par_x + 1) // 2))
                    sy = slice(vy.start - st_y, vy.stop - st_y)
                    sx = slice(vx.start - st_x, vx.stop - st_x)
                    if vy.stop <= vy.start or vx.stop <= vx.start:
                        continue
                    ww = w[sy, sx] * (wa * wb)
                    # el disc lunar no aporta corona
                    dest_num = num[c][par_y::2, par_x::2]
                    dest_den = den[c][par_y::2, par_x::2]
                    dest_n = ncon[c][par_y::2, par_x::2]
                    ml = pes_lluna[par_y::2, par_x::2][vy, vx]
                    ww = ww * ml
                    dest_num[vy, vx] += ww * val[sy, sx]
                    dest_den[vy, vx] += ww
                    dest_n[vy, vx] += (ww > 0)
        print(f"  [{k:2d}/{len(fg)}] {f.nom} {f.exp_s:<9.6g} "
              f"sol=({f.sol_x:.1f},{f.sol_y:.1f})", flush=True)

    hdr = np.zeros((H, W, 3), np.float32)
    var = np.zeros((H, W, 3), np.float32)
    cob = np.zeros((H, W, 3), np.uint16)
    for i, c in enumerate(canals):
        d = den[c]
        bo = d > 0
        hdr[..., i] = np.where(bo, num[c] / np.maximum(d, 1e-30), np.nan)
        var[..., i] = np.where(bo, 1.0 / np.maximum(d, 1e-30), np.nan)
        cob[..., i] = ncon[c]

    suf = os.environ.get("SUFIX", "")
    np.save(OUT / f"hdr_vixen_countss{suf}.npy", hdr)
    np.save(OUT / f"hdr_vixen_var{suf}.npy", var)
    np.save(OUT / f"hdr_vixen_cobertura{suf}.npy", cob)
    rs = r_out / R_SOL_PX
    zona = (rs > 1.05) & (rs < 6.0)
    buits = int((cob[..., 1][zona] == 0).sum())
    print(f"\nreixa {W}×{H}, Sol al centre ({cx_out:.1f},{cy_out:.1f})")
    print(f"cobertura verd 1,05–6,0 R☉: mediana {np.median(cob[...,1][zona]):.0f} "
          f"aportacions, píxels buits {buits}")
    print(f"→ {OUT/'hdr_vixen_countss.npy'}")


# ---------------------------------------------------------------- vis

def perfil_azimutal(img: np.ndarray, r: np.ndarray, r_complet: float,
                    cy: float | None = None, cx: float | None = None
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Mediana azimutal per anell.

    ⚠️ Només es mesura on l'anell cap SENCER dins el fotograma. Més enllà
    l'anell només trepitja les cantonades i, amb un cel que té gradient, la
    seva mediana fa un graó: són els arcs que sortien a la primera versió.
    A partir d'allà s'extrapola amb la llei de potència del tram exterior.
    """
    ib = r.astype(np.int32)
    n = int(ib.max()) + 1
    perfil = np.full(n, np.nan)
    bo = np.isfinite(img)
    lim = int(r_complet)
    for k in range(min(lim, n)):
        m = bo & (ib == k)
        if m.sum() > 60:
            # ⛔ MITJANA, no mediana: sobre desenes de milers de píxels la
            # mediana d'una distribució asimètrica salta d'un valor a l'altre
            # entre anells veïns i el quocient se'n queda els graons. El
            # suavitzat de 17 taps de sota SÍ que s'ha de conservar: treure'l
            # empitjora els anells un 36 %.
            perfil[k] = float(img[m].mean())
    idx = np.arange(n)
    ok = np.isfinite(perfil)
    perfil = np.interp(idx, idx[ok], perfil[ok])
    perfil = np.convolve(np.pad(perfil, 8, mode="edge"), np.ones(17) / 17, "valid")
    # ⛔ Més enllà del cercle inscrit NO s'extrapola amb una llei de potència.
    # La feia curta —el que hi ha allà baix ja no és corona sinó halo i cel, que
    # s'aplanen— i el quocient `L/perfil` passava d'1,000 exacte a **1,125** a
    # 7,6 R☉. Aquell colze a 5,20 R☉ el veuen totes les bandes amples del
    # detall i en surt un GRADIENT CIRCULAR al fons (Pere, 17-08).
    #
    # Es continua amb el perfil mesurat als MATEIXOS SECTORS azimutals a tots
    # els radis —els que encara queden coberts a la cantonada— i s'enganxa per
    # raó al valor de dins. Fixant els sectors no hi ha ni graó de nivell ni
    # canvi de pendent: el biaix del gradient de cel és el mateix als dos
    # costats de la unió i se'n va a la divisió.
    ext = None
    if lim < n - 4:
        c_y = img.shape[0] / 2.0 if cy is None else cy
        c_x = img.shape[1] / 2.0 if cx is None else cx
        yy = (np.arange(img.shape[0], dtype=np.float32) - c_y)[:, None]
        xx = (np.arange(img.shape[1], dtype=np.float32) - c_x)[None, :]
        bins = 720
        az = ((np.arctan2(yy, xx) + math.pi) * (bins / (2 * math.pi))
              ).astype(np.int32) % bins
        rmax = min(int(ib.max()), n - 1)
        sect = bo & (ib > int(0.96 * rmax))
        usats = np.zeros(bins, bool)
        usats[np.unique(az[sect])] = True
        m_sect = usats[az]
        k0 = int(0.80 * lim)
        pc = np.full(n, np.nan)
        for k in range(k0, rmax + 1):
            m = bo & m_sect & (ib == k)
            if m.sum() > 60:
                pc[k] = float(img[m].mean())
        bo_pc = np.isfinite(pc)
        if bo_pc[k0:lim].sum() > 20 and bo_pc[lim:].sum() > 20:
            pc = np.interp(idx, idx[bo_pc], pc[bo_pc])
            pc = np.convolve(np.pad(pc, 8, mode="edge"), np.ones(17) / 17, "valid")
            if pc[lim - 1] > 0:
                ext = perfil[lim - 1] * pc[lim:] / pc[lim - 1]
    if ext is None:
        # recanvi històric: llei de potència ajustada al 45 % exterior mesurat,
        # enganxada al valor de dins perquè no hi quedi un graó
        a0, a1 = int(0.55 * lim), lim
        pend, ord0 = np.polyfit(np.log(idx[a0:a1] + 1.0),
                                np.log(np.maximum(perfil[a0:a1], 1e-6)), 1)
        ext = np.exp(ord0 + pend * np.log(idx[lim:] + 1.0))
        if len(ext) and ext[0] > 0:
            ext = ext * (perfil[lim - 1] / ext[0])
    perfil[lim:] = ext
    return perfil[np.clip(ib, 0, n - 1)], perfil


def desa_png(nom: str, a: np.ndarray, previa: int = 2400) -> None:
    import cv2
    a8 = np.clip(a * 255.0, 0, 255).astype(np.uint8)
    if a8.ndim == 3:
        a8 = a8[..., ::-1]                        # RGB → BGR per a cv2
    cv2.imwrite(str(OUT / f"{nom}.png"), a8)
    if a8.shape[1] > previa:
        esc = previa / a8.shape[1]
        cv2.imwrite(str(OUT / f"{nom}_{previa}.jpg"),
                    cv2.resize(a8, None, fx=esc, fy=esc,
                               interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 93])
    print(f"  → {nom}.png  ({a8.shape[1]}×{a8.shape[0]})")


def realca(x: np.ndarray, sigmes: list[float], sigma_soroll: np.ndarray | None = None,
           k: float = 0.7) -> np.ndarray:
    """Normalització gaussiana multiescala, l'esperit de l'MGN de Morgan i
    Druckmüller (2014). Va SEMPRE després de l'HDR i sobre una còpia: és una
    operació no lineal i dependent del contingut, i aplicada abans d'apilar
    convertiria la mitjana de brillantors en una mitjana de contrastos.

    `sigma_soroll` és el soroll esperat per píxel, del mapa de variància del
    G5. Amb ell cada escala porta **porta de significació**: on la dispersió
    local no supera el soroll, el realçat s'apaga. Sense aquesta porta el
    filtre estira el soroll fins al mateix contrast que la corona, que és el
    defecte que el WOW d'Auchère (2023) ataca amb un criteri objectiu.
    """
    from scipy.ndimage import gaussian_filter
    acum = np.zeros_like(x)
    for s in sigmes:
        mu = gaussian_filter(x, s)
        v = np.maximum(gaussian_filter((x - mu) ** 2, s), 1e-12)
        sd = np.sqrt(v)
        realc = np.arctan(k * (x - mu) / sd)
        if sigma_soroll is not None:
            # variància de senyal = observada − esperada del soroll; el pes és
            # el de Wiener i va a zero on tot el que hi ha és soroll
            vn = gaussian_filter(sigma_soroll ** 2, s)
            realc = realc * np.clip(1.0 - vn / v, 0.0, 1.0)
        acum += realc
    return acum / len(sigmes)


# ---------------------------------------------------------------- detall
#
# ⛔ Per què `realca` NO pot fer la foto final, amb els números mesurats el
# 17-08 sobre el compost viu (anell 2,05–2,55 R☉, contrast rms per banda de
# freqüència azimutal m):
#
#   banda m      amplada       LINEAL     FOTO amb realca    factor
#      5–  20   18°–72°       0,11908        0,08312          0,7×
#     20–  60    6°–18°       0,03225        0,06222          1,9×
#     60– 180    2°– 6°       0,00615        0,06104          9,9×
#    180– 400  0,9°– 2°       0,00183        0,04162         22,8×
#    400– 900  0,4°–0,9°      0,00119        0,03545         29,7×
#    900–2000 0,18°–0,4°      0,00096        0,03070         31,9×
#
# La jerarquia real del cel és **124 : 1** entre l'estructura gran i la fina;
# `realca` la deixa en **2,7 : 1**. Divideix per la desviació local, o sigui
# que iguala el contrast a totes les escales: és la definició d'un filtre de
# pas alt. D'aquí surten les tres coses que Pere veu —radis rectilinis, vores
# massa dures i una trama fina com d'aliasing—: **cap d'elles no és al compost
# lineal**, on per damunt de m=180 no hi ha ni un 0,2 % de la potència.
#
# I la porta de soroll no ho salvava: mira la variància MITJANA d'una regió,
# però l'amplificació és PÍXEL A PÍXEL. Allà on hi ha estructura de veritat la
# porta s'obre del tot i el soroll que hi cavalca a sobre s'amplifica igual.
#
# La substitució conserva l'amplitud: bandes d'una piràmide de diferències de
# gaussianes, guany DECLARAT per banda i encongiment de Wiener amb el soroll
# MESURAT de cada banda. Mai es divideix per l'amplitud local.

SIG_PSF_PX = 1.147          # FWHM òptica mesurada 2,70 px
# Escala de bandes en píxels de sortida. A 2 R☉ (r = 892 px) 1° són 15,6 px:
# les bandes fines (≤ 11 px) són sub-grau i és on viu el soroll; els radis
# reals de `research/76` §5 octies fan 0,62–1,94° de FWHM i cauen a 11–29 px;
# el relleu de les serpentines que dona la forma de la corona és a 76–324 px.
BANDES_PX = [1.6, 2.6, 4.2, 6.8, 11.0, 18.0, 29.0, 47.0, 76.0, 123.0, 200.0, 324.0]


def desenfoca(x: np.ndarray, s: float) -> np.ndarray:
    """Gaussiana ràpida. Per damunt de σ=6 baixa de resolució, desenfoca i
    torna a pujar: l'error d'un desenfocament suau és molt per sota del
    soroll i estalvia un ordre de magnitud de temps sobre 32 Mpx."""
    import cv2
    a = np.ascontiguousarray(x, np.float32)
    if s <= 6.0:
        k = int(2 * math.ceil(3 * s) + 1)
        return cv2.GaussianBlur(a, (k, k), s, borderType=cv2.BORDER_REPLICATE)
    f = max(1, int(s / 4.0))
    h, w = a.shape
    pt = cv2.resize(a, (w // f, h // f), interpolation=cv2.INTER_AREA)
    sp = s / f
    k = int(2 * math.ceil(3 * sp) + 1)
    pt = cv2.GaussianBlur(pt, (k, k), sp, borderType=cv2.BORDER_REPLICATE)
    return cv2.resize(pt, (w, h), interpolation=cv2.INTER_LINEAR)


def desenfoca_valid(x, m, s):
    """Convolució normalitzada: la vora morta del fotograma no sagna cap dins."""
    num = desenfoca(np.where(m, x, 0.0), s)
    den = desenfoca(m.astype(np.float32), s)
    return num / np.maximum(den, 1e-6)


def transferencia_soroll(escales: list[float], n: int = 2048,
                         llavor: int = 20260812,
                         s_calib: float = 2.0) -> tuple[list[float], float]:
    """Quant soroll deixa passar cada banda, per unitat de soroll per píxel.

    ⛔ No es pot mesurar com l'rms de la banda al cel: per a les bandes amples
    això mesura ESTRUCTURA —a 200–324 px l'rms del cel surt 1,7 vegades el
    soroll per píxel, quan una banda que promitja 10⁵ píxels n'hauria de deixar
    passar mil vegades menys—. Prendre-ho per soroll tanca la porta de Wiener
    justament on hi ha senyal.

    Es mesura sobre una realització sintètica amb l'ESTRUCTURA DE CORRELACIÓ
    del compost: soroll blanc convolucionat amb la gota de drizzle, que amb
    PIXFRAC = 2,0 és una caixa de 2×2 píxels de sortida. Es normalitza a
    dispersió 1 per píxel i es passa per la mateixa descomposició.

    Retorna també la transferència del passa-alt de σ=`s_calib` que es fa
    servir per calibrar el soroll al cel: `std(x − G(x, s))` d'un camp
    correlacionat NO és la seva dispersió per píxel, i prendre-ho per tal
    subestima el soroll i torna a obrir la porta.
    """
    import cv2
    rng = np.random.default_rng(llavor)
    z = rng.standard_normal((n, n)).astype(np.float32)
    z = cv2.blur(z, (2, 2), borderType=cv2.BORDER_REFLECT)   # gota de drizzle
    z /= float(z.std())
    ks = []
    prev = desenfoca(z, escales[0])
    for s0, s1 in zip(escales[:-1], escales[1:]):
        seg = desenfoca(z, s1)
        b = prev - seg
        prev = seg
        vora = int(min(4 * s1, n // 2 - 8))
        ks.append(float(b[vora:n - vora, vora:n - vora].std()))
    hp = z - desenfoca(z, s_calib)
    v = int(4 * s_calib)
    return ks, float(hp[v:n - v, v:n - v].std())


def detall_bandes(norm: np.ndarray, valid: np.ndarray, sig: np.ndarray,
                  zona_soroll: np.ndarray, guanys: list[float],
                  escales: list[float] | None = None) -> np.ndarray:
    """Contrast local additiu que CONSERVA la jerarquia del compost lineal.

    `norm` és la luminància dividida pel perfil radial (mitjana ≈ 1), o sigui
    que cada banda ja és un contrast relatiu i es pot sumar directament.
    `sig` és el soroll per píxel en aquestes mateixes unitats i `zona_soroll`
    l'anell on es mesura el guany de soroll de cada banda.

    Per a cada banda j:
        b_j = G(norm, s_j) − G(norm, s_{j+1})
        n_j = k_j · sig            k_j mesurat a `zona_soroll`
        w_j = max(0, 1 − n_j²/v_j) v_j = potència local de la banda
        D  += g_j · w_j · b_j

    El pes de Wiener només MULTIPLICA per un número entre 0 i 1: mai divideix
    per l'amplitud. Per això la banda de 18°–72° surt amb el seu contrast i la
    de 0,2° surt a zero, en comptes de totes dues amb el mateix.
    """
    esc = escales if escales is not None else BANDES_PX
    assert len(guanys) == len(esc) - 1, "un guany per banda"
    ks, _ = transferencia_soroll(esc)
    sig_cel = max(float(np.median(sig[zona_soroll])), 1e-12)
    D = np.zeros(norm.shape, np.float32)
    prev = desenfoca_valid(norm, valid, esc[0])
    # ⛔ El compost porta un sistemàtic d'escala fina PER DAMUNT del soroll de
    # fotons —PRNU residual i la reixa del drizzle—. Es mesura a la banda més
    # fina de totes, allà on a 4–5 R☉ no hi pot haver corona resolta (1,6–2,6
    # px són 0,06° a aquell radi), i s'escala tot el terra de soroll per aquell
    # factor. És conservador: a les bandes amples el senyal/soroll és de
    # centenars i no els toca, i a les fines tanca la porta que cal tancar.
    b0 = desenfoca_valid(norm, valid, esc[1])
    f_sist = float(np.sqrt(np.mean(((prev - b0)[zona_soroll]).astype(np.float64) ** 2))
                   ) / max(ks[0] * sig_cel, 1e-12)
    f_sist = max(f_sist, 1.0)
    print(f"  sistemàtic d'escala fina: ×{f_sist:.2f} sobre el soroll de fotons")
    ks = [k * f_sist for k in ks]
    print("     banda       k soroll   soroll banda   rms al cel   S/N   "
          "pes mitjà   aportació")
    for j, (s0, s1) in enumerate(zip(esc[:-1], esc[1:])):
        seg = desenfoca_valid(norm, valid, s1)
        b = prev - seg
        prev = seg
        rms_cel = float(np.sqrt(np.mean(b[zona_soroll].astype(np.float64) ** 2)))
        n_cel = ks[j] * sig_cel
        if guanys[j] == 0.0:
            print(f"  {s0:5.1f}–{s1:5.1f} px  {ks[j]:9.5f}   {n_cel:12.6f}   "
                  f"{rms_cel:10.6f}  {rms_cel/max(n_cel,1e-12):4.1f}   "
                  f"guany 0, descartada")
            continue
        n2 = (ks[j] * sig) ** 2
        # potència local de la banda, suavitzada generosament perquè
        # l'estimador no es mengi la pròpia banda
        v = desenfoca(b.astype(np.float32) ** 2, 4.0 * s1)
        w = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
        D += guanys[j] * w * b
        print(f"  {s0:5.1f}–{s1:5.1f} px  {ks[j]:9.5f}   {n_cel:12.6f}   "
              f"{rms_cel:10.6f}  {rms_cel/max(n_cel,1e-12):4.1f}   "
              f"{float(w[valid].mean()):7.3f}   "
              f"{float(np.std((guanys[j]*w*b)[valid])):9.6f}")
    return np.where(valid, D, 0.0)


# ---------------------------------------------------------------- detall log-polar
#
# ⛔ Per què les bandes en píxels fixos no poden fer bé la foto, i per què el
# perfil radial extrapolat deixa un anell (Pere, 17-08, tres iteracions):
#
# 1. La corona té estructura ANGULAR: plomalls de 0,62–1,94° de FWHM,
#    serpentines de 5–20°. Una banda de 10 px és 1,1° a 1,2 R☉ —corona real— i
#    0,3° a 4 R☉ —només soroll—. Cap joc de guanys en píxels no pot ser bo als
#    dos radis alhora: si dona detall a dins, embruta a fora, i si és net a
#    fora, aplana a dins. Aquesta és la raó de fons del «massa detall / massa
#    poc» que ha anat oscil·lant.
# 2. El fons `L/perfil` s'ha d'extrapolar més enllà del cercle inscrit (5,20
#    R☉) i qualsevol unió deixa un colze de 8–20 px que les bandes amples
#    amplifiquen: mesurat a la FOTO, vall-cim de ±1,7 % entre 4,97 i 5,22 R☉.
#    La correcció 2-D de σ = 250 px treu la rampa, no el colze.
#
# En coordenades LOG-POLARS les dues coses cauen soles: una gaussiana de σ fix
# en polars és una gaussiana que ESCALA amb el radi en la imatge (és l'esperit
# de l'ACHF de Druckmüller), i el fons de la piràmide és el propi desenfocament
# gran —normalitzat amb la màscara de validesa, o sigui que les cantonades
# sense dades no s'extrapolen enlloc—. No hi ha perfil, no hi ha unió, no hi
# pot haver anell.
#
# El que NO es fa: allargar el nucli radialment (ANISO = 1 → isòtrop en la
# imatge). Un desenfocament radial de soroll fabrica ratlles radials rectes,
# que és exactament el que Pere no vol veure.

NA_POLAR = int(os.environ.get("NA_POLAR", "8192"))     # mostres d'angle
NR_POLAR = int(os.environ.get("NR_POLAR", "2048"))     # mostres de log-radi
R_MIN_POLAR = 400.0                                    # px: just dins del disc lunar
# Bandes en GRAUS: la mateixa escala que BANDES_PX a 2 R☉ (r = 892 px).
BANDES_DEG = [0.10, 0.17, 0.27, 0.44, 0.71, 1.16, 1.86, 3.0, 4.9, 7.9, 12.8, 20.8]
GUANYS_DEG = [float(v) for v in os.environ.get(
    "GUANYS_DEG", "0,2.0,4.0,6.0,6.0,5.5,4.5,3.5,2.5,1.4,0").split(",")]
ANISO = float(os.environ.get("ANISO", "1.0"))          # 1 = isòtrop en la imatge
SIG_MIN_IMG_PX = 1.6   # per sota d'aquesta σ d'imatge la banda s'apaga (PSF 2,70 px FWHM)


def desenfoca_polar(x: np.ndarray, s_rho: float, s_ang: float) -> np.ndarray:
    """Gaussiana anisòtropa sobre una imatge polar (files = angle, PERIÒDIC;
    columnes = log-radi). L'angle s'embolcalla amb farciment cíclic perquè no
    hi quedi cap costura a 0°/360°."""
    import cv2
    a = np.ascontiguousarray(x, np.float32)
    pad = int(math.ceil(3 * s_ang)) + 1
    ap = np.concatenate([a[-pad:], a, a[:pad]], axis=0)
    s_min = min(s_rho, s_ang)

    def k(s):
        return int(2 * math.ceil(3 * max(s, 0.5)) + 1)

    if s_min <= 6.0:
        out = cv2.GaussianBlur(ap, (k(s_rho), k(s_ang)), sigmaX=s_rho, sigmaY=s_ang,
                               borderType=cv2.BORDER_REPLICATE)
    else:
        f = max(1, int(s_min / 4.0))
        h, w = ap.shape
        pt = cv2.resize(ap, (max(8, w // f), max(8, h // f)), interpolation=cv2.INTER_AREA)
        sr, sa = s_rho / f, s_ang / f
        pt = cv2.GaussianBlur(pt, (k(sr), k(sa)), sigmaX=sr, sigmaY=sa,
                              borderType=cv2.BORDER_REPLICATE)
        out = cv2.resize(pt, (w, h), interpolation=cv2.INTER_LINEAR)
    return out[pad:pad + a.shape[0]]


def mapes_logpolars(H: int, W: int, cy: float, cx: float, r_max: float):
    """Mapes de remostreig imatge → log-polar i log-polar → imatge.

    rho = K·ln(r / R_MIN_POLAR), K = NR/ln(r_max/R_MIN_POLAR); angle = 2π·i/NA.
    """
    K = NR_POLAR / math.log(r_max / R_MIN_POLAR)
    th = (2 * math.pi * np.arange(NA_POLAR, dtype=np.float64) / NA_POLAR)[:, None]
    rr = (R_MIN_POLAR * np.exp(np.arange(NR_POLAR, dtype=np.float64) / K))[None, :]
    map_x = (cx + rr * np.cos(th)).astype(np.float32)
    map_y = (cy + rr * np.sin(th)).astype(np.float32)
    yy = (np.arange(H, dtype=np.float32) - cy)[:, None]
    xx = (np.arange(W, dtype=np.float32) - cx)[None, :]
    r = np.hypot(xx, yy)
    t = np.arctan2(yy, xx)
    t = np.where(t < 0, t + 2 * np.pi, t)
    imap_x = (K * np.log(np.maximum(r, R_MIN_POLAR) / R_MIN_POLAR)).astype(np.float32)
    imap_y = (t / (2 * math.pi) * NA_POLAR).astype(np.float32)
    return K, rr[0], map_x, map_y, imap_x, imap_y


def inpaint_radial(xp: np.ndarray, mp: np.ndarray, n_pend: int = 30) -> np.ndarray:
    """Omple, fila a fila (angle a angle), el que hi ha per DINS del primer
    píxel vàlid continuant el pendent local en log-radi.

    ⛔ El forat de la Lluna no és concèntric amb el Sol —el disc és més gran
    que el Sol i s'hi mou 28 px en 100 s—, o sigui que en polars la seva vora
    és ondulada i qualsevol estadística per columna hi canvia de composició al
    llarg de ~70 mostres. Omplert per dins amb el pendent local (la corona és
    quasi una llei de potència, LINEAL en ln r), la columna és completa i la
    mitjana no deriva. Cap enfora NO s'omple: es va provar amb el pendent i el
    desplaçament respecte del cel real de les cantonades sortia com un anell
    gegant; allà es fa servir la màscara.
    """
    na, nr = xp.shape
    ok = mp > 0.5
    te = ok.any(axis=1)
    c0 = np.where(te, np.argmax(ok, axis=1), 0)
    c1 = np.where(te, nr - 1 - np.argmax(ok[:, ::-1], axis=1), nr - 1)
    fila = np.arange(na)
    col = np.arange(nr)[None, :]
    a = xp[fila, c0]
    b = xp[fila, np.minimum(c0 + n_pend, c1)]
    pend_in = np.where(c1 - c0 > n_pend, (b - a) / n_pend, 0.0)
    dins = col < c0[:, None]
    return np.where(dins, a[:, None] + pend_in[:, None] * (col - c0[:, None]),
                    xp).astype(np.float32)


def fons_fourier(xp: np.ndarray, mp: np.ndarray, r_of: np.ndarray,
                 m_max: int = 4, ridge: float = 5.0) -> tuple[np.ndarray, int]:
    """Fons per columna de log-radi: ajust robust de 1, cos kθ, sin kθ (k ≤ m_max)
    sobre les files vàlides, EXACTE mentre totes les files són vàlides i
    EXTRAPOLAT en ρ amb un polinomi de grau 2 més enllà.

    ⛔ Les tres coses que es van provar i no serveixen, mesurades:
    (1) l'ajust per columna sobre el conjunt d'angles vàlids a cada radi: la
        seva FORMA canvia quan les files de dalt i de baix van caient passat
        el cercle inscrit, i el canvi és un graó en ρ a cada angle → arcs
        (l'amplitud de banda saltava ×10–40 just passat 5,0 R☉);
    (2) omplir cap enfora amb el pendent local → desplaça la mitjana → anell;
    (3) omplir cap enfora amb l'extensió harmònica → suau, però el farciment
        no té l'estadística del cel real de les cantonades i les bandes
        amples ho veuen fins a 4 R☉ cap a dins.
    Extrapolar els COEFICIENTS de l'ajust exacte no depèn de cap composició i
    és suau per construcció; les bandes són passa-banda i un error suau del
    fons no el veuen. Retorna el fons i l'índex de l'última columna sencera.
    """
    from scipy.ndimage import gaussian_filter1d
    na, nr = xp.shape
    th = 2 * math.pi * np.arange(na) / na
    cols = [np.ones(na)]
    for k in range(1, m_max + 1):
        cols += [np.cos(k * th), np.sin(k * th)]
    A = np.stack(cols, axis=1).astype(np.float32)          # (na, p)
    p_ = A.shape[1]
    M = mp.astype(np.float32)
    coef = None
    for passada in range(2):
        S = np.einsum('ia,ib,ic->cab', A, A, M, optimize=True).astype(np.float64)
        T = np.einsum('ia,ic->ca', A, (M * xp).astype(np.float32), optimize=True).astype(np.float64)
        S[:, np.arange(1, p_), np.arange(1, p_)] += ridge
        S[:, 0, 0] += 1e-6
        coef = np.linalg.solve(S, T[..., None])[..., 0]      # (nr, p)
        if passada == 0:
            F0 = (A @ coef.T.astype(np.float32))
            res = np.where(mp > 0.5, xp - F0, np.nan)
            med = np.nanmedian(res, axis=0)
            mad = 1.4826 * np.nanmedian(np.abs(res - med[None, :]), axis=0) + 1e-6
            M = M * (np.abs(np.nan_to_num(res)) < 4.0 * mad[None, :])
            del F0, res
    frac = mp.mean(axis=0)
    plenes = np.where(frac >= 0.999)[0]
    c_ple = int(plenes.max()) if plenes.size else nr - 1
    # suavitzat lleu al llarg de ρ (el soroll de coeficient per columna
    # faria anells fins) i extrapolació polinòmica més enllà de c_ple
    coef = gaussian_filter1d(coef, 3.0, axis=0, mode="nearest")
    c_a = int(np.searchsorted(r_of, 3.5 * R_SOL_PX))
    c_a = min(c_a, c_ple - 50)
    # ⛔ Continuïtat C¹ a la unió, per construcció. Amb un fos de 40 columnes
    # entre l'ajust exacte i el polinomi, un desajust de només 0,05 % al fons
    # es convertia, ×guany 4–6, en un arc de ±0,35 % als sectors de dalt i de
    # baix (mesurat a la capa de pas alt). Ara el valor i el pendent a c_ple
    # són els de dins, i fora només s'ajusten els termes de grau 2 i 3.
    xt = np.arange(nr, dtype=np.float64)
    x_out = xt - c_ple
    ext = coef.copy()
    amb = np.where(frac > 0.05)[0]
    c_fi = int(amb.max()) if amb.size else nr - 1
    n_p = 20
    for j in range(p_):
        v0 = float(coef[c_ple, j])
        s0 = float(coef[c_ple, j] - coef[max(c_ple - n_p, 0), j]) / n_p
        if j <= 4 and c_fi > c_ple + 60:
            # m = 0, 1, 2: les cantonades ho determinen; residu sobre v0 + s0·x
            xo = np.arange(c_ple + 1, c_fi + 1, dtype=np.float64) - c_ple
            wo = np.sqrt(np.clip(frac[c_ple + 1:c_fi + 1], 0, 1))
            res = coef[c_ple + 1:c_fi + 1, j] - (v0 + s0 * xo)
            A2 = np.stack([xo ** 2, xo ** 3], axis=1) * wo[:, None]
            ab, *_ = np.linalg.lstsq(A2, res * wo, rcond=None)
            fora = v0 + s0 * x_out + ab[0] * x_out ** 2 + ab[1] * x_out ** 3
        else:
            # m ≥ 3: continuació amb el pendent de dins, esmorteïda (τ = 150)
            fora = v0 + s0 * 150.0 * (1.0 - np.exp(-np.clip(x_out, 0, None) / 150.0))
        ext[:, j] = np.where(x_out > 0, fora, coef[:, j])
    coef = ext
    print(f"  fons de Fourier m≤{m_max}: exacte fins a la columna {c_ple} "
          f"({r_of[c_ple]/R_SOL_PX:.2f} R☉), extrapolat en ρ més enllà")
    return (A @ coef.T.astype(np.float32)).astype(np.float32), c_ple


def detall_logpolar(lnL: np.ndarray, valid: np.ndarray, sig_log: np.ndarray,
                    zona_soroll: np.ndarray, cy: float, cx: float,
                    guanys: list[float] | None = None,
                    bandes_deg: list[float] | None = None) -> np.ndarray:
    """Contrast local additiu amb bandes que ESCALEN amb el radi.

    `lnL` és el logaritme de la luminància lineal, `sig_log` el seu soroll per
    píxel (σ_L/L), `zona_soroll` l'anell on es calibra el sistemàtic. Retorna D
    en la reixa d'imatge; la foto fa L·exp(D).

    En log-polars (files = angle, columnes = ln r):
        x    = ln L, omplert per dins del limbe (`inpaint_radial`)
        F    = fons de Fourier m ≤ 4 per columna sobre les files vàlides
        R    = (x − F)·màscara                  contrast azimutal en log
        b_j  = Gn(R, σ_j) − Gn(R, σ_{j+1})       gaussianes ISÒTROPES en la imatge,
                                                 normalitzades amb la màscara
        n_j  = f_sist · k_j(ρ) · sig_log         k_j mesurat sobre soroll sintètic
                                                 remostrejat igual
        w_j  = max(0, 1 − n_j²/v_j)              Wiener, v_j potència local
        g_j(ρ) = g_j · rampa(σ_img/1,6 px) · rampa exterior
        D   += g_j(ρ) · w_j · b_j
    """
    import cv2
    H, W = lnL.shape
    guanys = GUANYS_DEG if guanys is None else guanys
    bandes = BANDES_DEG if bandes_deg is None else bandes_deg
    assert len(guanys) == len(bandes) - 1, "un guany per banda"
    r_max = math.hypot(max(cy, H - cy), max(cx, W - cx)) + 4.0
    K, r_of, map_x, map_y, imap_x, imap_y = mapes_logpolars(H, W, cy, cx, r_max)
    px_deg = NA_POLAR / 360.0
    # px d'imatge per mostra: radial r/K, azimutal 2π·r/NA. Per ser isòtrop
    # en la imatge, σ_ρ = σ_θ · (2πK/NA).
    iso = 2 * math.pi * K / NA_POLAR

    def cap_a_polar(a):
        return cv2.remap(np.ascontiguousarray(a, np.float32), map_x, map_y,
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    mp0 = cap_a_polar(valid.astype(np.float32))
    xp = cap_a_polar(np.where(valid, lnL, 0.0)) / np.maximum(mp0, 1e-3)
    sp = cap_a_polar(np.where(valid, sig_log, 0.0)) / np.maximum(mp0, 1e-3)
    mp0 = (mp0 > 0.5).astype(np.float32)
    cz = cap_a_polar(zona_soroll.astype(np.float32)) > 0.5
    xp = inpaint_radial(xp, mp0)
    # màscara per al fons i les gaussianes: l'ompliment interior compta com a
    # vàlid (és continuació suau); l'exterior del fotograma, no
    ok = mp0.copy()
    c0 = np.argmax(mp0 > 0.5, axis=1)
    ok[np.arange(NR_POLAR)[None, :] < c0[:, None]] = 1.0
    F, _c_ple = fons_fourier(xp, ok, r_of)
    R = ((xp - F) * ok).astype(np.float32)
    if os.environ.get("DIAG_LP") == "1":
        vv0 = mp0 > 0.5
        mitj = np.where(vv0.sum(0) > 0, (R * vv0).sum(0) / np.maximum(vv0.sum(0), 1), np.nan)
        print("  desviació del fons extrapolat respecte de la mitjana REAL de les files vàlides:")
        for rr_ in (4.5, 4.9, 5.1, 5.3, 5.6, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5):
            c = int(np.searchsorted(r_of, rr_ * R_SOL_PX))
            if c < NR_POLAR:
                print(f"     {rr_:4.1f} R☉: {100*float(np.nanmean(mitj[max(c-5,0):c+5])):+.3f} %  "
                      f"(vàlides {100*float(vv0[:, c].mean()):.0f} %)")
    del xp, F
    print(f"  log-polar {NA_POLAR}×{NR_POLAR}: r de {R_MIN_POLAR:.0f} a {r_max:.0f} px, "
          f"K = {K:.1f}, mostreig radial {r_of[0]/K:.2f} px al limbe i "
          f"{r_of[-1]/K:.2f} px a la cantonada; σ_ρ/σ_θ = {iso:.3f}")

    # camp de soroll sintètic amb la correlació del drizzle, remostrejat igual
    rng = np.random.default_rng(20260812)
    z = rng.standard_normal((H, W)).astype(np.float32)
    z = cv2.blur(z, (2, 2), borderType=cv2.BORDER_REFLECT)
    z /= float(z.std())
    zp = cap_a_polar(z) * ok
    del z

    def blur(a, s_ang):
        return desenfoca_polar(a, s_ang * iso * ANISO, s_ang)

    def blur_n(a, s_ang):
        return blur(a, s_ang) / np.maximum(blur(ok, s_ang), 1e-3)

    esc = [d * px_deg for d in bandes]
    prev = blur_n(R, esc[0])
    prev_z = blur_n(zp, esc[0])
    D = np.zeros_like(R)
    f_sist = 1.0
    # rampa exterior: cap realçat més enllà de 5,6 R☉ i esvaïment des de 4,9.
    # La vora de dalt del fotograma és a 5,007 R☉ i la de baix a 5,10: més
    # enllà només hi ha els sectors laterals amb el fons extrapolat, i el que
    # s'hi guanya no compensa el risc.
    r_ext = np.clip((5.6 * R_SOL_PX - r_of) / (0.7 * R_SOL_PX), 0.0, 1.0)
    # ⛔ FINESTRA PER DISTÀNCIA A LA VORA de la màscara, per banda. Mesurat a
    # la capa de pas alt (17-08 tarda): als sectors de dalt i de baix la
    # mitjana de D feia +0,3 % a 4,7 R☉ i −0,7…−1,1 % a 5,0–5,3 —un arc just
    # on la vora del fotograma talla el cercle—, i al sector lateral res. Són
    # les bandes amples amb la finestra a mig fer sobre la vora (biaix d'un sol
    # costat) i el fons extrapolat a l'altre costat. Cada banda s'apaga suau
    # dins de 2,5 σ (de la seva σ exterior) de la vora, en mostres polars.
    dist_vora = cv2.distanceTransform((ok > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    i1 = int(np.searchsorted(r_of, 1.2 * R_SOL_PX))
    i2 = int(np.searchsorted(r_of, 2 * R_SOL_PX))
    i4 = int(np.searchsorted(r_of, 4 * R_SOL_PX))
    vv = mp0 > 0.5
    print("     banda (°)     k@2R☉    S/N cel   pes mitjà   aportació   σ img @1,2/2/4 R☉ (px)")
    for j, (d0, d1) in enumerate(zip(bandes[:-1], bandes[1:])):
        seg = blur_n(R, esc[j + 1])
        b = prev - seg
        prev = seg
        seg_z = blur_n(zp, esc[j + 1])
        bz = prev_z - seg_z
        prev_z = seg_z
        k_r = np.sqrt(np.sum(bz.astype(np.float64) ** 2 * mp0, axis=0)
                      / np.maximum(mp0.sum(axis=0), 1.0)).astype(np.float32)
        n_col = k_r[None, :] * sp
        rms_cel = float(np.sqrt(np.mean(b[cz].astype(np.float64) ** 2)))
        n_cel = max(float(np.median(n_col[cz])), 1e-12)
        if j == 0:
            # ⛔ sistemàtic d'escala fina (PRNU residual, reixa del drizzle),
            # mesurat a la banda més fina a 4–5 R☉ on no hi ha corona resolta
            f_sist = max(1.0, rms_cel / n_cel)
            print(f"  sistemàtic d'escala fina: ×{f_sist:.2f} sobre el soroll de fotons")
        sig_img = np.deg2rad(d0) * r_of
        if guanys[j] == 0.0:
            print(f"  {d0:5.2f}–{d1:5.2f}   {k_r[i2]:8.5f}   {rms_cel/(n_cel*f_sist):6.1f}"
                  f"   guany 0, descartada")
            continue
        n2 = (f_sist * n_col) ** 2
        v = blur_n(b * b, 4.0 * esc[j + 1])
        w = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
        g_r = (guanys[j] * np.clip(sig_img / SIG_MIN_IMG_PX - 1.0, 0.0, 1.0) * r_ext
               ).astype(np.float32)
        w_vora = np.clip(dist_vora / (2.5 * esc[j + 1]), 0.0, 1.0)
        w_vora = (w_vora * w_vora * (3.0 - 2.0 * w_vora)).astype(np.float32)   # smoothstep
        cont = g_r[None, :] * w * w_vora * b
        D += cont
        print(f"  {d0:5.2f}–{d1:5.2f}   {k_r[i2]:8.5f}   {rms_cel/(n_cel*f_sist):6.1f}"
              f"   {float(w[vv].mean()):7.3f}   "
              f"{float(np.std(cont[vv])):9.6f}"
              f"   {sig_img[i1]:4.1f} / {sig_img[i2]:4.1f} / {sig_img[i4]:5.1f}")
        if os.environ.get("DIAG_LP") == "1":
            for r0, r1 in ((4.5, 5.0), (5.1, 5.3), (5.5, 6.0), (6.5, 7.0)):
                cc = (r_of > r0 * R_SOL_PX) & (r_of < r1 * R_SOL_PX)
                zz = vv & cc[None, :]
                print(f"        {r0}–{r1} R☉: cont mitjana {float(cont[zz].mean()):+.4f} sd {float(cont[zz].std()):.4f}"
                      f" · b sd {float(b[zz].std()):.4f} · w mitjà {float(w[zz].mean()):.3f}"
                      f" · k_r {float(k_r[cc].mean()):.5f}±{float(k_r[cc].std()):.5f}")
    # ⛔ compressió SUAU i no retall dur: amb el retall a ±0,7 més d'un 1 % dels
    # píxels de cada extrem hi topaven i quedaven taques planes a la corona
    # interior. tanh porta el mateix sostre (×2,5) sense cap cantonada.
    A_TOPALL = 0.9
    D = (A_TOPALL * np.tanh(D / A_TOPALL)).astype(np.float32)
    # tornada a la imatge: farciment cíclic de dues files per a la interpolació
    Dp = np.concatenate([D[-2:], D, D[:2]], axis=0)
    Dimg = cv2.remap(Dp, imap_x, imap_y + 2.0, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return np.where(valid, Dimg, 0.0).astype(np.float32)


def etapa_vis(args) -> None:
    sufix = os.environ.get("HDR_SUFIX", "")
    hdr = np.load(OUT / f"hdr_vixen_countss{sufix}.npy")
    cob = np.load(OUT / f"hdr_vixen_cobertura{sufix}.npy")
    varm = np.load(OUT / f"hdr_vixen_var{sufix}.npy")
    H, W, _ = hdr.shape
    cy, cx = H / 2.0, W / 2.0
    r = anells(H, W, cy, cx)
    rs = r / R_SOL_PX
    r_complet = min(H, W) / 2.0

    # ⛔ El pla blau del R6 dona 4,33 e⁻/ADU contra 5,08 del verd
    # (research/75 §3), repetible i sense explicar, i a sobre va 1,4× més
    # gruixut: la luminància ha de sortir del vermell i el verd.
    R_, G_ = hdr[..., 0], hdr[..., 1]
    ref = (rs > 1.3) & (rs < 1.5) & np.isfinite(G_) & np.isfinite(R_)
    kr = float(np.median(G_[ref]) / np.median(R_[ref]))
    lum = np.where(np.isfinite(R_) & np.isfinite(G_), 0.5 * (G_ + kr * R_),
                   np.where(np.isfinite(G_), G_, kr * R_))
    valid = np.isfinite(lum)
    print(f"luminància = (verd + {kr:.3f}·vermell)/2   "
          f"[el blau queda fora: guany anòmal i 1,4× més tou]")

    # --- fons del cel: constant MÉS un pla inclinat.
    #     El cel de la totalitat no és radialment simètric —depèn de la
    #     distància a la vora de l'ombra— i el seu gradient s'emporta la
    #     corona a partir d'uns 3 R☉. Un pla no pot absorbir una corona
    #     radialment simètrica, o sigui que és la resta més segura que hi ha.
    #     ⚠️ Això és VISUALITZACIÓ: la component difusa física —halo
    #     instrumental més cel— és feina del model del G3.
    fora = valid & (rs > 3.5)
    base_r, _ = perfil_azimutal(np.where(valid, lum, np.nan), r, r_complet)
    resid = lum - base_r
    yy = (np.arange(H) - cy)[:, None] / R_SOL_PX
    xx = (np.arange(W) - cx)[None, :] / R_SOL_PX
    A = np.c_[np.ones(fora.sum()),
              np.broadcast_to(xx, (H, W))[fora],
              np.broadcast_to(yy, (H, W))[fora]]
    coef, *_ = np.linalg.lstsq(A, resid[fora], rcond=None)
    cel_pla = coef[0] + coef[1] * xx + coef[2] * yy
    cel_const = float(np.median(lum[valid & (rs > 7.2)] - 0))
    print(f"cel: constant {cel_const:.1f} ADU/s, gradient "
          f"({coef[1]:+.1f},{coef[2]:+.1f}) ADU/s per R☉ "
          f"→ {math.hypot(coef[1],coef[2])/max(cel_const,1)*100:.1f} % per R☉")
    net = lum - cel_const - (coef[1] * xx + coef[2] * yy)
    net_f = np.where(valid, net, 0.0)

    base_r, perfil = perfil_azimutal(np.where(valid, net, np.nan), r, r_complet)
    norm = np.where(valid, net / np.maximum(base_r, 1e-6), 1.0)
    # soroll de la luminància normalitzada, propagat del mapa de variància
    vR, vG = varm[..., 0], varm[..., 1]
    var_lum = np.where(np.isfinite(vR) & np.isfinite(vG),
                       0.25 * (vG + kr * kr * np.nan_to_num(vR)),
                       np.nan_to_num(vG, nan=0.0))
    sig_norm = np.sqrt(np.maximum(np.nan_to_num(var_lum), 0)) / np.maximum(base_r, 1e-6)
    # el drizzle correlaciona el soroll dels veïns: la dispersió observada al
    # cel és menor que la del mapa, i el factor es calibra a les dades
    from scipy.ndimage import gaussian_filter as _gf
    # ⚠️ dins del cercle inscrit: més enllà el perfil està extrapolat i la
    # divisió es dispara (κ sortia 60 en lloc de 0,6)
    cel_z = valid & (rs > 3.6) & (rs < 4.6)
    obs = float(np.std((norm - _gf(norm, 2.0))[cel_z]))
    esp = float(np.median(sig_norm[cel_z]))
    kappa = obs / esp if esp > 0 else 1.0
    sig_norm = sig_norm * kappa
    print(f"soroll: mapa {esp:.4f}, observat al cel {obs:.4f} → "
          f"factor de correlació del drizzle {kappa:.3f}")

    lo = 1.5
    hi = float(np.percentile(net[valid & (rs < 1.06)], 99.5))
    def log_estirat(a):
        return np.clip((np.log10(np.maximum(a, lo)) - math.log10(lo))
                       / (math.log10(hi) - math.log10(lo)), 0, 1)

    gamma = log_estirat(net_f) ** 0.9
    desa_png("corona_vixen_log", gamma)

    p1, p99 = np.percentile(norm[valid & (rs > 1.05) & (rs < 6)], [0.5, 99.5])
    desa_png("corona_vixen_radial",
             np.clip((norm - p1) / (p99 - p1), 0, 1) ** 0.85)

    nivell = os.environ.get("REALCAT", "suau")
    sigmes, k_realc, mescla, antialias = REALCATS[nivell]
    print(f"realçat «{nivell}»: sigmes {sigmes}, k={k_realc}, "
          f"mescla {mescla:.0%}, antialiàsing {antialias} px")
    det = realca(norm, sigmes, sig_norm, k_realc)
    disc = ~valid
    mix = np.clip((1 - mescla) * gamma + mescla * (det * 0.5 + 0.5), 0, 1)
    if antialias > 0:
        from scipy.ndimage import gaussian_filter as _gf2
        mix = _gf2(mix, antialias)
    desa_png("corona_vixen_detall", np.where(disc, 0.10, mix))
    # la luminància de pantalla, perquè l'etapa `tiff` la pugui pintar amb la
    # cromaticitat de la corona en lloc de tornar a calcular-la
    np.save(OUT / "vis_luminancia.npy", mix.astype(np.float32))

    # --- retalls a resolució completa: aquí és on es veu si el drizzle ha
    #     comprat detall, perquè la reixa de sortida és la del sensor
    for nom, r_max in (("3Rsol", 3.0), ("15Rsol", 1.55)):
        m = int(r_max * R_SOL_PX)
        sl = (slice(int(cy) - m, int(cy) + m), slice(int(cx) - m, int(cx) + m))
        n_ = norm[sl]
        d_ = realca(n_, sigmes, sig_norm[sl], k_realc)
        g_ = gamma[sl]
        v_ = np.clip((1 - mescla) * g_ + mescla * (d_ * 0.5 + 0.5), 0, 1)
        if antialias > 0:
            v_ = _gf2(v_, antialias)
        desa_png(f"corona_vixen_retall_{nom}",
                 np.where(disc[sl], 0.10, v_), previa=2000)

    # --- color
    rgb = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        c = hdr[..., i]
        v = np.isfinite(c)
        b_i, _ = perfil_azimutal(np.where(v, c, np.nan), r, r_complet)
        res_i = np.where(v, c - b_i, 0.0)
        Ai = np.c_[np.ones(fora.sum()), np.broadcast_to(xx, (H, W))[fora],
                   np.broadcast_to(yy, (H, W))[fora]]
        ci, *_ = np.linalg.lstsq(Ai, res_i[fora], rcond=None)
        cel_i = float(np.median(c[v & (rs > 7.2)]))
        rgb[..., i] = np.where(v, c - cel_i - (ci[1] * xx + ci[2] * yy), 0.0)
    esc_c = [float(np.median(rgb[..., i][ref])) for i in range(3)]
    for i in range(3):
        rgb[..., i] *= esc_c[1] / esc_c[i]
    hi2 = float(np.percentile(rgb[..., 1][valid & (rs < 1.06)], 99.5))
    rgbl = np.clip((np.log10(np.maximum(rgb, lo)) - math.log10(lo))
                   / (math.log10(hi2) - math.log10(lo)), 0, 1) ** 0.9
    desa_png("corona_vixen_color", rgbl)

    # --- diagnòstic: perfil radial absolut i cerca d'anells de composició
    print("\nperfil radial de la luminància neta:")
    print("   R☉      ADU/s       B/B☉     cobertura")
    for rr in [1.02, 1.05, 1.1, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        m = (rs > rr) & (rs < rr + 0.02) & valid
        if m.sum() < 100:
            continue
        v = float(np.median(net[m]))
        print(f"  {rr:4.2f}  {v:11.1f}  {v*2.772e-11:9.2e}      "
              f"{np.median(cob[...,1][m]):.0f}")

    # un graó entre esglaons d'exposició sortiria com un salt del perfil
    # respecte de la seva pròpia tendència suau
    # ⚠️ La tendència s'ha de mesurar amb un ajust QUADRÀTIC local en
    # log(r)-log(I): la corona hi és quasi una recta però amb curvatura, i una
    # mitjana mòbil confon aquella curvatura amb un graó (donava un 11 % fals
    # a 1,15 R☉, que és on el perfil gira més).
    ir = np.arange(len(perfil))
    rr_ = ir / R_SOL_PX
    ok = np.isfinite(perfil) & (rr_ > 1.10) & (rr_ < 5.0) & (ir < r_complet)
    lr_, lp_ = np.log(rr_[ok]), np.log(np.maximum(perfil[ok], 1e-9))
    suau_ = np.empty_like(lp_)
    for i in range(len(lp_)):
        a, b = max(0, i - 50), min(len(lp_), i + 51)
        suau_[i] = np.polyval(np.polyfit(lr_[a:b], lp_[a:b], 2), lr_[i])
    salt = np.abs(lp_ - suau_)
    pitjor = float(salt.max())
    print(f"\ncontinuïtat del perfil (criteri 2 del G5, ≤3 %): mitjana "
          f"{salt.mean()*100:.2f} %, màxima {pitjor*100:.2f} % a "
          f"{rr_[ok][int(np.argmax(salt))]:.2f} R☉ "
          f"{'✅' if pitjor < 0.03 else '⚠️'}")
    (OUT / "vis_params.json").write_text(json.dumps({
        "k_vermell": kr, "cel_constant_ADU_s": cel_const,
        "cel_gradient_ADU_s_per_Rsol": [float(coef[1]), float(coef[2])],
        "nivell_realcat": nivell, "sigmes_realcat": sigmes,
        "k_realcat": k_realc, "mescla": mescla, "antialias_px": antialias,
        "factor_B_Bsol_per_ADU_s": 2.772e-11,
        "continuitat_max_pct": pitjor * 100,
        "nota": "el blau queda fora de la luminància: 4,33 e-/ADU contra 5,08 "
                "(research/75 §3) i FWHM 1,4× més gran",
    }, indent=1, ensure_ascii=False))



# ---------------------------------------------------------------- earthshine

def etapa_earthshine(args) -> None:
    """Disc lunar il·luminat per la Terra, alineat a la LLUNA.

    ⛔ Aquesta pila NO comparteix alineació amb la de corona: la Lluna es mou
    28,7 px respecte del Sol al llarg de la totalitat. Es fa a part i es
    composa al final, que és la regla de `research/74` §5 punt 2.

    Dins del disc, el que es mesura és earthshine MÉS el halo de la corona que
    l'envolta. El halo es treu ajustant un model suau —radial des del limbe cap
    a dins, més un pla— a la corona d'anell de just per dins del limbe, i
    extrapolant-lo. ⚠️ El nivell absolut queda degenerat amb aquell model
    (`research/74` §0.1): d'aquí en surt el RELLEU, no una fotometria.
    """
    from scipy.ndimage import gaussian_filter, shift as despl

    fg = [f for f in llegeix_manifest() if f.usat and f.exp_s > 5]
    print(f"{len(fg)} fotogrames profunds: {', '.join(f.nom for f in fg)}")
    ref = fg[len(fg) // 2]
    acc = None
    for f in fg:
        mos, _ = calibra(f)
        g = 0.5 * (mos[0::2, 1::2] + mos[1::2, 0::2]) / f.exp_s
        dy = (f.lluna_y - ref.lluna_y) / 2.0
        dx = (f.lluna_x - ref.lluna_x) / 2.0
        acc = despl(g, (-dy, -dx), order=3, mode="nearest") if acc is None \
            else acc + despl(g, (-dy, -dx), order=3, mode="nearest")
    disc = acc / len(fg)
    cy, cx = ref.lluna_y / 2, ref.lluna_x / 2
    rl = R_LLUNA_PX / 2
    r = anells(*disc.shape, cy, cx)

    # ⛔ El halo de dins del disc el genera la corona de fora, i és MOLT més
    # gran que l'earthshine. Ajustar-lo a l'anell exterior i extrapolar cap a
    # dins sobre-resta (primer intent: mediana −1027 ADU/s). El que funciona és
    # ajustar un polinomi 2D DINS del disc i restar-lo: el halo hi és llis i
    # l'albedo no. És el que `research/72` §4 va fer amb grau 4 a la Sony.
    # ⚠️ Això dona el RELLEU, no el nivell: el nivell és degenerat amb el
    # model (`research/74` §0.1) i es fixa a la presentació.
    ys, xs = np.where(r < rl * 1.05)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = disc[y0:y1 + 1, x0:x1 + 1].astype(np.float64)
    rr = r[y0:y1 + 1, x0:x1 + 1]
    yy = (np.arange(y0, y1 + 1)[:, None] - cy) / rl
    xx = (np.arange(x0, x1 + 1)[None, :] - cx) / rl
    yy, xx = np.broadcast_arrays(yy, xx)
    dins = rr < rl * 0.90
    termes = [xx ** i * yy ** j for g in range(5) for i in range(g + 1)
              for j in [g - i]]
    A = np.stack([t[dins] for t in termes], 1)
    for _ in range(3):
        coef, *_ = np.linalg.lstsq(A, sub[dins], rcond=None)
        mod = sum(c * t for c, t in zip(coef, termes))
        res = sub - mod
        sd = 1.4826 * np.median(np.abs(res[dins] - np.median(res[dins])))
        keep = dins & (np.abs(res - np.median(res[dins])) < 3 * sd)
        A = np.stack([t[keep] for t in termes], 1)
        dins = keep
    net = res
    m = rr < rl * 0.90
    print(f"disc: relleu rms {net[m].std():.2f} ADU/s sobre un halo de "
          f"{np.median(mod[m]):.0f} ADU/s "
          f"({100*net[m].std()/max(np.median(mod[m]),1):.2f} % de contrast)")
    np.savez(OUT / "earthshine_disc.npz", disc=net.astype(np.float32),
             y0=y0, x0=x0, cy=cy - y0, cx=cx - x0, rl=rl,
             lluna_x=ref.lluna_x, lluna_y=ref.lluna_y, sol_x=ref.sol_x,
             sol_y=ref.sol_y, nom=ref.nom)
    import cv2
    v = gaussian_filter(net, 2.0)
    lo, hi = np.percentile(v[m], [2, 98])
    im = np.clip((v - lo) / max(hi - lo, 1e-6), 0, 1)
    im[rr > rl] = 0
    cv2.imwrite(str(OUT / "earthshine_disc.png"), (im * 255).astype(np.uint8))
    print(f"→ earthshine_disc.npz i .png  (referència {ref.nom})")


# ---------------------------------------------------------------- tiff

# Camí de color de la R6 III, tret del CR3 amb rawpy i muntat amb l'algorisme
# de dcraw (`cam_xyz_coeff`): normalitzar les files de cam_xyz·xyz_rgb a suma 1
# i invertir. Les files sumen 1, o sigui que un blanc de càmera ja equilibrat
# surt blanc a sRGB.
CAM_A_SRGB = np.array([
    [1.5595, -0.5902,  0.0306],
    [-0.1770,  1.6854, -0.5083],
    [-0.0250, -0.4964,  1.5214],
])
# `daylight_whitebalance` de libraw: el blanc D65 implícit a la matriu. És el
# que fa que una font de espectre solar —la corona n'és una— surti neutra.
WB_DIURN = np.array([2.1678, 1.0, 1.3555])


_D50 = (0.9642, 1.0000, 0.8249)
_PRIM = {
    "srgb": ((0.4360747, 0.2225045, 0.0139322),
             (0.3850649, 0.7168786, 0.0971045),
             (0.1430804, 0.0606169, 0.7141733)),
    "prophoto": ((0.7976749, 0.2880402, 0.0), (0.1351917, 0.7118741, 0.0),
                 (0.0313534, 0.0000857, 0.8252100)),
}


def icc(espai: str = "srgb", trc: str = "srgb") -> bytes:
    """Perfil ICC v2 mínim però VÀLID.

    ⛔ La capçalera ha de fer 128 bytes EXACTES i la taula de tags ha de
    començar al byte 128. La primera versió d'aquesta funció posava
    l'il·luminant del PCS al byte 84 en lloc del 68 i deixava una capçalera de
    144 bytes: qualsevol lector hi llegia ZERO tags, o sigui cap primària i
    cap corba. Validat contra littlecms i ColorSync.
    """
    import struct

    def s15(v):
        return int(round(v * 65536.0))

    def xyz(x, y, z):
        return b"XYZ " + b"\0" * 4 + struct.pack(">3i", s15(x), s15(y), s15(z))

    def desc(t):
        b = t.encode("ascii") + b"\0"
        return b"desc" + b"\0" * 4 + struct.pack(">I", len(b)) + b + b"\0" * 81

    if trc == "lineal":
        corba = b"curv" + b"\0" * 4 + struct.pack(">I", 1) + struct.pack(">H", 256)
    else:
        n = 1024
        t = [min(65535, max(0, round((u / 12.92 if u <= 0.04045
                                      else ((u + 0.055) / 1.055) ** 2.4) * 65535)))
             for u in (i / (n - 1) for i in range(n))]
        corba = b"curv" + b"\0" * 4 + struct.pack(">I", n) + struct.pack(f">{n}H", *t)
    r, g, b = _PRIM[espai]
    nom = {"srgb": "sRGB", "prophoto": "ProPhoto RGB"}[espai] + \
        (" (lineal)" if trc == "lineal" else "")
    tags = [(b"desc", desc(nom)), (b"wtpt", xyz(*_D50)), (b"rXYZ", xyz(*r)),
            (b"gXYZ", xyz(*g)), (b"bXYZ", xyz(*b)), (b"rTRC", corba),
            (b"gTRC", corba), (b"bTRC", corba),
            (b"cprt", b"text" + b"\0" * 4 + b"public domain\0")]
    base = 128 + 4 + len(tags) * 12
    taula, dades, vist = b"", b"", {}
    for sig, d in tags:
        if d not in vist:
            vist[d] = (base + len(dades), len(d))
            dades += d + b"\0" * ((4 - len(d) % 4) % 4)
        taula += sig + struct.pack(">II", *vist[d])
    cos = struct.pack(">I", len(tags)) + taula + dades
    h = bytearray(128)
    struct.pack_into(">I", h, 0, 128 + len(cos))
    h[4:8], h[8:12] = b"lcms", b"\x02\x40\x00\x00"
    h[12:16], h[16:20], h[20:24] = b"mntr", b"RGB ", b"XYZ "
    h[36:40], h[40:44] = b"acsp", b"APPL"
    struct.pack_into(">3i", h, 68, *(s15(v) for v in _D50))
    return bytes(h) + cos


def a_srgb(u: np.ndarray) -> np.ndarray:
    """Codificació sRGB (OETF) sobre dades lineals 0–1."""
    u = np.clip(u, 0.0, 1.0)
    return np.where(u <= 0.0031308, u * 12.92,
                    1.055 * np.power(u, 1 / 2.4) - 0.055)


def escriu_tiff(cami: Path, dades01: np.ndarray, trc: str) -> None:
    """TIFF RGB de 16 bits amb l'ICC al tag 34675.

    ⛔ `metadata=None` és obligatori: sense això tifffile hi afegeix el seu
    propi `ImageDescription` i, amb el tag 270 duplicat, macOS refusa el
    fitxer sencer amb «Cannot extract image from file».
    """
    import tifffile
    perfil = icc("srgb", trc)
    tifffile.imwrite(
        cami, (np.clip(dades01, 0, 1) * 65535 + 0.5).astype(np.uint16),
        photometric="rgb", compression="zlib", metadata=None,
        resolution=(300, 300),
        extratags=[(34675, 7, len(perfil), perfil, False)])


# Aspecte objectiu, MESURAT sobre ~/Desktop/POWAAAH3.tif (el muntatge que
# Pere va fer amb el tren Sony i que fixa l'estètica). ⚠️ Del seu aspecte
# només se'n pot copiar el COLOR: el 84 % de la seva corona està cremat a
# blanc pur —tot el que hi ha dins de 1,84 R☉— i el daurat viu només a l'anell
# de 1,86 a 3,2 R☉. Aquests són els valors d'allà, en sRGB lineal.
POWAAAH_RG, POWAAAH_BG = 1.55, 0.45
# El seu cel: blau i aixecat, no pas negre (mesurat als anells de 8 a 17 R☉).
CEL_RGB = (0.055, 0.075, 0.098)


def etapa_tiff(args) -> None:
    """Escriu el compost en TIFF de 16 bits, amb color de veritat.

    Surten tres fitxers i tenen usos ben diferents:

    * `..._lineal_16b.tif` — LINEAL i de color NEUTRE. Conserva els valors:
      cada nivell és proporcional a la brillantor i es pot tornar a B/B☉ amb
      el factor del capçal. És el que s'ha de fer servir per treballar-hi.
    * `..._natural.tif` — el color TAL COM EL VA VEURE LA CÀMERA, amb la
      vermellor que li posa l'atmosfera a massa d'aire 6,4. Amb corba de to.
    * `..._FINAL.tif` — el color del POWAAAH3. També amb corba de to.

    ⛔ Els dos últims destrueixen la fotometria a propòsit.
    """
    sufix = os.environ.get("HDR_SUFIX", "")
    hdr = np.load(OUT / f"hdr_vixen_countss{sufix}.npy")
    H, W, _ = hdr.shape
    r = anells(H, W, H / 2.0, W / 2.0)
    rs = r / R_SOL_PX
    valid = np.all(np.isfinite(hdr), axis=2)
    disc = ~valid

    cel = np.array([float(np.nanmedian(hdr[..., i][valid & (rs > 4.6) & (rs < 5.1)]))
                    for i in range(3)])
    lin = np.nan_to_num(hdr) - cel
    print(f"cel restat (ADU/s): R={cel[0]:.1f} G={cel[1]:.1f} B={cel[2]:.1f}")

    # --- balanç de blancs mesurat SOBRE LA PRÒPIA CORONA, a 1,1-1,3 R☉.
    #     No és maquillatge: la corona K és dispersió Thomson del continu
    #     fotosfèric i la F és pols, o sigui que el seu color intrínsec ÉS el
    #     del Sol. Fer-la neutra és calibrar contra el Sol. ⚠️ S'ha de mesurar
    #     a prop del limbe: a 2,6-3,4 R☉ el resultat depèn del cel restat i
    #     es dispara.
    ref = valid & (rs > 1.1) & (rs < 1.3)
    cru = np.array([float(np.median(lin[..., i][ref])) for i in range(3)])
    wb = np.linalg.solve(CAM_A_SRGB, np.ones(3)) / cru
    wb /= wb[1]
    print(f"WB de la corona: R={wb[0]:.4f} G=1 B={wb[2]:.4f}   "
          f"(color cru R/G={cru[0]/cru[1]:.4f} B/G={cru[2]/cru[1]:.4f})")
    print(f"  a comparar: as-shot {1.9434:.4f}/{1.6592:.4f}, "
          f"D65 de la matriu {WB_DIURN[0]:.4f}/{WB_DIURN[2]:.4f}")

    neutre = (lin * wb) @ CAM_A_SRGB.T
    q = [float(np.median(neutre[..., i][valid & (rs > 1.5) & (rs < 2.5)]))
         for i in range(3)]
    print(f"comprovació a 1,5-2,5 R☉ (fora de la zona d'ajust): "
          f"R/G={q[0]/q[1]:.3f} B/G={q[2]/q[1]:.3f}  — han de ser ~1")

    esc = float(np.percentile(neutre[..., 1][valid & (rs < 1.06)], 99.7))

    # 1) LINEAL i NEUTRE: el producte de treball
    lin16 = (neutre / esc)[RETALL[0]:RETALL[1] + 1, RETALL[2]:RETALL[3] + 1]
    escriu_tiff(OUT / "corona_vixen_lineal_16b.tif", lin16, "lineal")
    print(f"→ corona_vixen_lineal_16b.tif   65535 = {esc:.0f} ADU/s verd = "
          f"{esc*2.772e-11:.2e} B/B☉")

    # 2) i 3) versions amb corba de to.
    #
    # ⛔ Dues coses que s'han de fer bé i que és fàcil equivocar:
    #
    # a) la corba va sobre la LUMINÀNCIA i després es reparteix als tres
    #    canals amb el mateix factor. Estirar cada canal per separat fa que
    #    toquin el terra a radis diferents i surten franges de color falses
    #    —blau a dalt, groc i vermell a baix— que no són de la corona.
    # b) el fitxer declara TRC sRGB, o sigui que el valor emmagatzemat JA és
    #    el valor de pantalla. Encadenar-hi la codificació sRGB per damunt
    #    d'una corba logarítmica ho crema tot.
    #
    # I la corba cobreix els 15 EV sencers. Copiar la del POWAAAH3 —una
    # finestra de només 1,9 EV— cremaria tot el que hi ha dins de 1,84 R☉,
    # que és justament el que aquest HDR existeix per evitar.
    lo, hi, gam = 3.0, esc, 1.6

    def to(L):
        u = np.clip((np.log10(np.maximum(L, lo)) - math.log10(lo))
                    / (math.log10(hi) - math.log10(lo)), 0, 1)
        return u ** gam

    import cv2

    def desa(nom, v):
        # ⛔ TERRA per damunt de zero. La cromaticitat regularitzada pot sortir
        # negativa on el senyal creua el zero, i un sol píxel a 0 exacte fa
        # petar qualsevol eina de gradient amb una divisió per zero. Aquí en
        # sortien 3.893 al vermell i 14.041 al blau.
        v = np.clip(v, 0, 1)
        v[disc] = np.array(CEL_RGB) * 0.30
        v = np.maximum(v, np.array(CEL_RGB) * 0.22)
        # ⛔ i RETALL de la vora morta. La reixa de sortida està centrada al SOL,
        # que al fotograma queia 83-102 px a la dreta i 43-63 px avall del
        # centre: per això hi ha 41 files mortes a dalt i 84 columnes mortes a
        # la dreta, sense cap aportació. Es perden 0,10 R☉ de camp.
        v = v[RETALL[0]:RETALL[1] + 1, RETALL[2]:RETALL[3] + 1]
        escriu_tiff(OUT / f"corona_vixen_{nom}.tif", v, "srgb")
        cv2.imwrite(str(OUT / f"corona_vixen_{nom}_2400.jpg"),
                    cv2.resize((np.clip(v, 0, 1)[..., ::-1] * 255).astype(np.uint8),
                               (2400, 1600), interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 93])
        print(f"→ corona_vixen_{nom}.tif  i  _2400.jpg")

    from scipy.ndimage import gaussian_filter
    LUMA = np.array([0.2126, 0.7152, 0.0722])
    sig_cel = float(np.std(hdr[..., 1][valid & (rs > 4.6) & (rs < 5.1)]))

    def pinta(base, L_pantalla):
        """Reparteix una luminància de pantalla sobre els tres canals.

        Dues coses que s'han de fer i que no són òbvies:

        a) **conservar la cromaticitat, no estirar cada canal.** Estirats per
           separat, els canals toquen el terra a radis diferents i surten
           franges de color falses que no són de la corona.
        b) **regularitzar la cromaticitat amb el senyal/soroll.** A partir
           d'uns 3 R☉ el senyal per píxel és comparable al soroll i la
           cromaticitat mesurada és soroll pur: pintada, dona el confeti blau
           i vermell de la vora. Aquí es suavitza pesant per la luminància
           —que conserva la protuberància, que és brillant i de color propi—
           i es porta cap al color mitjà de la corona allà on no hi ha senyal.
        """
        L = base @ LUMA
        c = base / np.maximum(L, 1e-9)[..., None]
        Lp = np.maximum(L, 0.0)
        num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (6, 6, 0))
        den = gaussian_filter(Lp, 6)
        c_suau = num / np.maximum(den, 1e-9)[..., None]
        c0 = np.array([float(np.median(c[..., i][valid & (rs > 1.2) & (rs < 2.0)]))
                       for i in range(3)])
        w = np.clip(Lp / (Lp + 8.0 * sig_cel), 0, 1)[..., None]
        c_fin = c_suau * w + c0 * (1 - w)
        # ⚠️ i el FONS ha de tornar a ser cel. El realçat multiescala té valor
        # neutre 0,5 fins i tot on no hi ha res, i pintat amb el color de la
        # corona deixa una taca torrada per tot el camp en lloc de cel fosc.
        corona = c_fin * np.maximum(L_pantalla, 0.0)[..., None]
        return corona * w + np.array(CEL_RGB) * (1 - w)

    natural = (lin * WB_DIURN) @ CAM_A_SRGB.T
    calid = neutre * np.array([POWAAAH_RG, 1.0, POWAAAH_BG])

    desa("natural", pinta(natural, to(np.maximum(
        natural @ np.array([0.2126, 0.7152, 0.0722]), 1e-6))))

    # El lliurable principal: la cromaticitat del POWAAAH3 sobre la luminància
    # REALÇADA, que és on hi ha els serpentins. Si no, queda una taca llisa.
    cami_lum = OUT / "vis_luminancia.npy"
    if cami_lum.exists():
        desa("FINAL", pinta(calid, np.load(cami_lum).astype(np.float64)))
    else:
        print("⚠️ falta vis_luminancia.npy: executa abans l'etapa `vis`")
        desa("FINAL", pinta(calid, to(np.maximum(
            calid @ np.array([0.2126, 0.7152, 0.0722]), 1e-6))))


# ---------------------------------------------------------------- foto

# Jerarquia del lliurable, tal com la van demanar els dos contrastos
# independents (Fable 5 i Codex, 17-08):
#   (i)  el compost LINEAL és l'autoritat i no es toca;
#   (ii) la FOTO surt d'una corba declarada, contrast local ACOTAT, color propi
#        i earthshine real;
#   (iii) qualsevol estètica de tercers és una variant etiquetada.
#
# ⛔ El defecte que això corregeix: dividir per la desviació local, com fa
# l'MGN, IGUALA el contrast a tots els radis, i llavors el cel a 5 R☉ té el
# mateix gra que la corona a 2. Per això semblava un filtre de pas alt i no una
# foto. Aquí el detall és ADDITIU i acotat: `L·(1 + β·D)` amb |β·D| ≤ 0,30.
GAMMA_RADIAL = float(os.environ.get("G_RAD", "0.0"))   # compressió PARCIAL del gradient: 1,0 el mataria del tot
BETA_DETALL = 0.35    # (retirat: el guany viu ara a GUANYS_BANDA)
ESCALES_DETALL = [4, 8, 16, 32]   # (retirat amb `realca`; el `vis` encara l'usa)
# Guany per banda de `BANDES_PX`, un per interval. La gepa va a 6,8–29 px, que
# és on viuen els radis confirmats al segon tren (0,62–1,94° de FWHM).
# ⛔ La banda més fina va a ZERO: 1,6–2,6 px és per sota del límit òptic
# (FWHM mesurada 2,70 px) i allà no hi pot haver res que la lent hagi resolt.
# ⛔ Les dues més amples també: 123–324 px són 8°–21° a 2 R☉, o sigui la FORMA
# de la corona, que ja la renderitza la corba de to. I amplificaven el colze
# que el perfil deixa al cercle inscrit → el gradient circular del fons.
GUANYS_BANDA = [float(v) for v in os.environ.get(
    "GUANYS", "0,2,6,10,12,11,9,6,4,2,0").split(",")]
# Adaptació cromàtica: fracció de la vermellor atmosfèrica que es desfà.
# research/75 §5.2 mesura +0,61 mag d'excés al vermell i −0,78 al blau a massa
# d'aire 6,4. Amb 1,0 la corona queda com des de fora de l'atmosfera; amb 0,0,
# tal com el sensor la va veure. L'ull adaptat era pel mig.
# Ancoratges de color, MESURATS al sketch de Pere (Sketchaprox.tif): la corona
# a 1,5-2,2 R☉ i el cel a 3,8-4,6 R☉, com a (R/G, 1, B/G).
# ⚠️ (17-08, auditoria del sketch) el (1,28 / 0,68) anterior era la MATEIXA
# mesura feta en Display P3 sense convertir; en sRGB el sketch a 1,5–2,2 R☉
# dona 1,349 / 0,667, i a 1,2–1,5 tira cap a 0,62–0,64 de B/G.
def _obj(nom, per_defecte):
    v = os.environ.get(nom)
    return tuple(float(x) for x in v.split(",")) if v else per_defecte
OBJ_CORONA = _obj("OBJ_CORONA", (1.35, 1.0, 0.64))
OBJ_MIG = _obj("OBJ_MIG", (1.17, 1.0, 0.865))          # sketch a 3,0 R☉ (2,7–3,3)
OBJ_CEL = _obj("OBJ_CEL", (0.90, 1.0, 1.09))
# Exponent del pes d'interpolació per canal (R, G, B). El sketch queda groc
# fins a 2,2 R☉ i el blau no arriba a neutre fins a 4,1 R☉; amb un sol pes
# lineal en log L la FOTO era neutra en blau a 3,24 R☉ (a 3 R☉: 0,97 contra
# 0,865). Un exponent < 1 manté el color de la corona més estona.
EXP_U = tuple(float(v) for v in os.environ.get("EXP_U", "1,1,1").split(","))   # (retirat: ara hi ha OBJ_MIG)
# Corba de to: `sketch` = spline monòton en log-log pels nivells de pantalla
# (Y) MESURATS al Sketchaprox de Pere per radi, ancorats a la mediana anular
# del compost lineal a cada radi (rim pintat de 1,02–1,08 exclòs);
# `logquad` = la log-quadràtica de tres ancoratges anterior.
CORBA = os.environ.get("CORBA", "sketch")
# els tres primers van +5 % respecte del mesurat perquè el detall a pantalla
# (mediana d'exp(D) < 1 dins de 2 R☉) i l'espatlla els fan baixar; comprovat
# a la sortida: 0,96 / 0,93 / 0,93 del sketch a 1,3 / 1,5 / 2,0 R☉ sense això
NIVELLS_SKETCH = ((1.15, 0.79), (1.5, 0.66), (2.0, 0.585), (2.5, 0.36), (3.0, 0.28),
                  (4.0, 0.218), (5.0, 0.192), (6.8, 0.180), (8.0, 0.171))
# Per entorn: NIVELLS="1.02:0.61,1.15:0.59,..." substitueix la taula; OBJ_CORONA,
# OBJ_MIG i OBJ_CEL com "R/G,1,B/G"; LLUNA=negra deixa el disc negre (sense
# earthshine), que és la tria de Pere per a l'híbrid del 17-08.
if os.environ.get("NIVELLS"):
    NIVELLS_SKETCH = tuple((float(a), float(b)) for a, b in
                           (x.split(":") for x in os.environ["NIVELLS"].split(",")))
LLUNA = os.environ.get("LLUNA", "earthshine")
# Compressió de la desviació del color MESURAT respecte del color esperat al
# radi (corona ↔ cel per u): la corona real és més vermella cap a dins (R/G
# 1,90 a 1,3 R☉ contra 1,61 a 1,5–2,2) i el sketch de Pere la vol groga
# uniforme (1,28–1,36). 1 = tal com és; 0 = només el mapa de dos ancoratges.
EXP_C = float(os.environ.get("EXP_C", "0.35"))
# Nivells de pantalla, mesurats al mateix sketch: el cel a 5 R☉ i la corona a
# 1,8 R☉. Són el que li dona l'aire de fotografia i no de mapa de dades.
NIV_CEL, NIV_CORONA, NIV_NUCLI = (
    float(os.environ.get("N_CEL", "0.15")),
    float(os.environ.get("N_COR", "0.60")),
    float(os.environ.get("N_NUC", "0.82")))


def etapa_foto(args) -> None:
    from scipy.ndimage import gaussian_filter
    import cv2

    sufix = os.environ.get("HDR_SUFIX", "")
    hdr = np.load(OUT / f"hdr_vixen_countss{sufix}.npy")
    varm = np.load(OUT / f"hdr_vixen_var{sufix}.npy")
    H, W, _ = hdr.shape
    cy, cx = H / 2.0, W / 2.0
    r = anells(H, W, cy, cx)
    rs = r / R_SOL_PX
    valid = np.all(np.isfinite(hdr), axis=2)
    # ⛔ «finit» NO vol dir bo: les files 41–84 de dalt del compost tenen
    # cobertura de 3 a 260 aportacions en lloc de 306 i valors de brossa (fila
    # 41: sd 6314 ADU/s). El retall final les amagava però ENTRAVEN als
    # càlculs, i en polars són exactament les que apareixen just passat el
    # cercle inscrit: estiraven l'ajust del fons de tota la columna i en
    # sortien arcs concèntrics. La validesa és la caixa RETALL, que és el que
    # es lliura.
    caixa = np.zeros_like(valid)
    caixa[RETALL[0]:RETALL[1] + 1, RETALL[2]:RETALL[3] + 1] = True
    valid &= caixa
    del caixa
    r_complet = min(H, W) / 2.0

    # --- 1. luminància lineal, AMB el cel de veritat a dins
    R_, G_ = hdr[..., 0], hdr[..., 1]
    ref = valid & (rs > 1.3) & (rs < 1.5)
    kr = float(np.median(G_[ref]) / np.median(R_[ref]))
    L = np.where(valid, 0.5 * (np.nan_to_num(G_) + kr * np.nan_to_num(R_)), np.nan)
    # --- 2. detall que CONSERVA la jerarquia de contrastos
    #
    # Dos camins. `DETALL=logpolar` (viu): bandes que escalen amb el radi i
    # sense cap perfil radial —vegeu el bloc de `detall_logpolar`—.
    # `DETALL=px`: el camí anterior, bandes en píxels fixos sobre L/perfil amb
    # correcció 2-D; es conserva per comparar i per reproduir el que Pere ha
    # vist. El perfil radial només es calcula si algú el necessita.
    mode_detall = os.environ.get("DETALL", "logpolar")
    cel_z = valid & (rs > 4.0) & (rs < 5.1)
    vG = np.nan_to_num(varm[..., 1])
    del varm
    if mode_detall == "logpolar" and GAMMA_RADIAL == 0.0:
        base = None
        # soroll relatiu σ_L/L: el denominador és L una mica desenfocat, per no
        # dividir per la pròpia fluctuació
        Ls = desenfoca_valid(np.where(valid, L, 0.0).astype(np.float32), valid, 6.0)
        Ls = np.maximum(Ls, 1e-3 * float(np.median(np.nan_to_num(L)[cel_z])))
        sig_log = (np.sqrt(np.maximum(vG, 0)) / Ls).astype(np.float32)
        lnL = np.log(np.maximum(np.nan_to_num(L), 1e-3 * float(np.median(np.nan_to_num(L)[cel_z])))
                     ).astype(np.float32)
        # calibratge del soroll per píxel: el mapa de variància no sap que el
        # drizzle correlaciona els veïns; es mesura al cel amb un passa-alt
        _ks, t_hp = transferencia_soroll(BANDES_PX)
        # ⛔ passa-alt EMMASCARAT i estimador ROBUST. La zona de calibratge
        # (4–5,1 R☉) toca la vora de dalt de la caixa RETALL (5,007 R☉); amb
        # una gaussiana sense màscara s'hi barrejava el ln(floor) de fora i
        # 1819 píxels de vora sortien amb salts de 7 unitats: std ×28, i la
        # porta de Wiener 7× massa tancada a tots els renders del 17-08 tarda
        # (la sistemàtica sortia ×1,00 per això). MAD ho fa immune.
        hp = (lnL - desenfoca_valid(lnL, valid, 2.0))[cel_z]
        obs = 1.4826 * float(np.median(np.abs(hp - np.median(hp)))) / t_hp
        esp = float(np.median(sig_log[cel_z]))
        sig_log = sig_log * (obs / esp if esp > 0 else 1.0)
        print(f"soroll relatiu per píxel al cel: mapa {esp:.5f} · mesurat {obs:.5f} "
              f"(passa-alt emmascarat, MAD, ÷{t_hp:.3f}) → ×{obs/esp:.3f}")
        del hp
        print(f"detall LOG-POLAR, bandes {BANDES_DEG} °, guanys {GUANYS_DEG}:")
        D = detall_logpolar(lnL, valid, sig_log, cel_z, cy, cx)
        del lnL, sig_log, Ls, vG
    else:
        base, perfil = perfil_azimutal(np.where(valid, L, np.nan), r, r_complet, cy, cx)
        # ⛔ El fons del detall NO pot ser només el perfil radial. Fora del cercle
        # inscrit el perfil és extrapolat i `L/perfil` hi deixa una rampa —+12,5 %
        # amb la llei de potència, +2,4 % amb els sectors— que qualsevol realçat
        # que conservi l'amplitud converteix en un GRADIENT CIRCULAR al fons.
        # S'hi afegeix una correcció 2-D: el residu `L/perfil` desenfocat a
        # σ = 250 px. ⚠️ Treu la rampa però NO el colze de 8–20 px de la unió:
        # a la FOTO del 17-08 quedava un vall-cim de ±1,7 % a 4,97–5,22 R☉. Per
        # això el camí viu és el log-polar.
        q = np.where(valid, L / np.maximum(base, 1e-9), 1.0).astype(np.float32)
        corr = desenfoca_valid(q, valid, 250.0)
        print(f"correcció 2-D del fons: {float(np.nanmin(corr[valid])):.3f}"
              f"–{float(np.nanmax(corr[valid])):.3f}")
        base = base * np.maximum(corr, 1e-3)
        del q, corr
        norm = np.where(valid, L / np.maximum(base, 1e-6), 1.0).astype(np.float32)
        sig = (np.sqrt(np.maximum(vG, 0)) / np.maximum(base, 1e-6)).astype(np.float32)
        del vG
        _ks, t_hp = transferencia_soroll(BANDES_PX)
        obs = float(np.std((norm - desenfoca(norm, 2.0))[cel_z])) / t_hp
        esp = float(np.median(sig[cel_z]))
        sig = sig * (obs / esp if esp > 0 else 1.0)
        print(f"soroll per píxel al cel: mapa {esp:.5f} · mesurat {obs:.5f} "
              f"(passa-alt ÷{t_hp:.3f}) → ×{obs/esp:.3f}")
        print(f"detall per bandes en px, guanys {GUANYS_BANDA}:")
        # les bandes es prenen del LOGARITME del contrast: guany igual a
        # qualsevol brillantor i resultat acotat sense retallar
        lnorm = np.log(np.maximum(norm, 1e-3)).astype(np.float32)
        sig_log = (sig / np.maximum(norm, 1e-3)).astype(np.float32)
        D = detall_bandes(lnorm, valid, sig_log, cel_z, GUANYS_BANDA)
        D = np.clip(D, -0.7, 0.7)
        del lnorm, sig_log, norm, sig

    # ⛔ ON s'aplica el detall, i per què ha canviat dues vegades.
    # (a) Amb l'MGN vell (dividir per σ local) el detall anava sobre `t` i la
    #     jerarquia sortia invertida: però la causa era l'MGN, no el lloc.
    # (b) Es va passar a L·exp(D) abans de la corba «perquè la compressió fos
    #     la mateixa per a tot». Mesurat el 17-08 (contrast extern): NO ho és.
    #     El pendent local de la corba d ln t/d ln L val 0,00–0,07 entre 1,03 i
    #     1,5 R☉ (l'altiplà brillant del sketch), 0,34 a 2 R☉, 0,8 a 2,5 i
    #     2,0–2,3 al cel de 4 R☉ enfora. O sigui: tot el detall afegit a L
    #     s'ESBORRAVA a la corona interior (×12 nominal → ×0,4 a pantalla) i es
    #     DOBLAVA al cel — d'aquí els plomalls tous i la trama i l'anell tan
    #     visibles al fons.
    # Ara D —contrast local en log, amb la jerarquia de bandes ja dins— es posa
    # sobre `t`, el valor de pantalla: t·exp(D). Els guanys són el que es vol
    # VEURE, iguals a tots els radis, i la corba governa només el gradient.
    L0 = L
    print(f"  modulació del detall: ×{float(np.exp(np.nanpercentile(D[valid], 1))):.3f} "
          f"a ×{float(np.exp(np.nanpercentile(D[valid], 99))):.3f} "
          f"(1r–99è percentil)")

    # --- 2 bis. la capa de PAS ALT sola (etapa `passalt`, o PASSALT=1)
    #
    # El mateix camp D que la foto porta a sobre, sobre gris neutre al 50 %,
    # per barrejar-la a Photoshop (Linear Light: afegeix 2·(capa − 0,5) =
    # D/A_TOPALL; Overlay o Soft Light, més suau). Cap corba, cap color: només
    # el contrast local, amb la mateixa porta de soroll i les mateixes bandes
    # en graus. Es guarda també D en float32 per si es vol reescalar.
    if getattr(args, "etapa", "") == "passalt" or os.environ.get("PASSALT") == "1":
        A_T = 0.9
        capa = 0.5 + 0.5 * np.clip(np.where(valid, D, 0.0), -A_T, A_T) / A_T
        capa = capa[RETALL[0]:RETALL[1] + 1, RETALL[2]:RETALL[3] + 1].astype(np.float32)
        nom_s = os.environ.get("FOTO_SUFIX", "")
        escriu_tiff(OUT / f"corona_vixen_PASSALT{nom_s}.tif",
                    np.repeat(capa[..., None], 3, axis=2), "srgb")
        np.save(OUT / f"corona_vixen_PASSALT{nom_s}_D.npy",
                np.where(valid, D, 0.0)[RETALL[0]:RETALL[1] + 1,
                                        RETALL[2]:RETALL[3] + 1].astype(np.float32))
        cv2.imwrite(str(OUT / f"corona_vixen_PASSALT{nom_s}_2400.jpg"),
                    cv2.resize((capa * 255).astype(np.uint8), (2400, 1600),
                               interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 94])
        print(f"→ corona_vixen_PASSALT{nom_s}.tif  (gris 0,5 ± D/{A_T}; 16 bits, sRGB, "
              f"mateix retall que la FOTO), _D.npy i _2400.jpg")
        if getattr(args, "etapa", "") == "passalt":
            return

    # --- 3. compressió PARCIAL del gradient radial
    # ⚠️ La corba de to es CALIBRA sobre la luminància sense realçar i s'APLICA
    # a la realçada. Si es calibra sobre la realçada, canviar un guany mou els
    # ancoratges i la corba sencera: amb els guanys d'avui el pendent passava
    # de −0,26 a −1,55 i la corona interior sortia cremada de banda a banda.
    if base is None:
        Lc, Lc0 = L, L0
    else:
        Lc = np.where(valid, L / np.maximum(base, 1e-6) ** GAMMA_RADIAL, np.nan)
        Lc0 = np.where(valid, L0 / np.maximum(base, 1e-6) ** GAMMA_RADIAL, np.nan)
    del L0

    # --- 4. corba de to global, monotònica i declarada
    dins = valid & (rs > 1.03) & (rs < 6.0)
    # ⛔ el punt negre no pot retallar corona: amb el percentil 0,5 quedaven
    # 111.806 píxels a negre pur entre 1 i 3 R☉ (una taca sota la Lluna que
    # semblava un forat). Es baixa i s'hi posa un peu suau.
    lo = float(np.percentile(Lc0[dins], 0.02)) * 0.85
    hi = float(np.percentile(Lc0[valid & (rs < 1.06)], 99.6))
    gam = float(os.environ.get("GAMMA_TO", "0.62"))

    def a_u0(x):
        u = (np.log10(np.maximum(np.nan_to_num(x), lo * 0.5)) - math.log10(lo)) \
            / (math.log10(hi) - math.log10(lo))
        # peu suau: en lloc de retallar a zero, comprimeix el que queda per sota
        u = np.where(u > 0.06, u, 0.06 * np.exp(np.minimum(u - 0.06, 0) / 0.06))
        return np.clip(u, 1e-4, None)

    u0 = a_u0(Lc)
    u0_ref = a_u0(Lc0)
    del Lc0
    # ⛔ La corba s'ANCORA als dos nivells mesurats al sketch de Pere: el cel a
    # 5 R☉ i la corona a 1,8 R☉. Així la foto té la mateixa presència que la
    # referència sense haver de tocar cap número a ull.
    # ⛔ TRES ancoratges sobre la luminància REAL, sense normalització radial.
    # El primer intent dividia pel perfil radial elevat a 0,7-0,9 i allò
    # aplanava la corona —i a 0,92 fins i tot la invertia—: la caiguda radial
    # de la corona és el que fa que sembli una foto, i s'ha de comprimir amb la
    # CORBA, no esborrar-la abans. Els tres nivells són els mesurats al sketch
    # de Pere, i el del nucli el que hi caldria si no estigués tapat.
    if CORBA == "sketch":
        # ⛔ Per què no la log-quadràtica: té la curvatura negativa i el pendent
        # li CREIX cap al cel per construcció (2,3–2,5 de 4 R☉ enfora), i el
        # sketch de Pere demana ~1: el seu cel cau −7 % de 6,5 a 8 R☉, la
        # log-quadràtica en dona −15 %. Amb pendent ~1 al cel, qualsevol
        # residu del compost —vinyeta, cel no estacionari, l'anell de 0,09 %—
        # surt a pantalla amb la meitat d'amplitud. I l'altiplà del sketch a
        # 1,3–1,9 R☉ ja no esborra el detall, perquè D va DESPRÉS.
        from scipy.interpolate import PchipInterpolator
        xs_, ys_ = [], []
        for r0, niv in NIVELLS_SKETCH:
            m = valid & (rs > r0 * 0.97) & (rs < r0 * 1.03)
            if m.sum() > 500:
                xs_.append(math.log(max(float(np.median(u0_ref[m])), 1e-9)))
                ys_.append(math.log(niv))
        xs_, ys_ = np.array(xs_)[::-1], np.array(ys_)[::-1]     # creixent en u
        pch = PchipInterpolator(xs_, ys_, extrapolate=True)
        lu = np.log(np.maximum(u0, 1e-6))
        lt = pch(lu)
        # per damunt del primer ancoratge (1,15 R☉): el pendent del primer tram
        # continua fins al nucli; l'espatlla de sota s'ocupa de no retallar
        pend0 = float(pch.derivative()(xs_[-1]))
        lt = np.where(lu > xs_[-1], ys_[-1] + max(pend0, 0.05) * (lu - xs_[-1]), lt)
        # per sota de l'últim (8 R☉): pendent de l'últim tram, mai per sota de 0
        pend1 = float(pch.derivative()(xs_[0]))
        lt = np.where(lu < xs_[0], ys_[0] + max(pend1, 0.0) * (lu - xs_[0]), lt)
        t = np.clip(np.exp(lt), 0, 1)
        pend = {r0: float(pch.derivative()(x)) for (r0, _), x in zip(NIVELLS_SKETCH[::-1], xs_)}
        print("corba del SKETCH (spline monòton log-log): pendent d ln t/d ln u a "
              + " · ".join(f"{r0:.1f} R☉ {pend[r0]:.2f}" for r0, _ in NIVELLS_SKETCH))
    else:
        ancs = []
        for r0, niv in ((1.05, NIV_NUCLI), (2.0, NIV_CORONA), (6.8, NIV_CEL)):
            m = valid & (rs > r0 * 0.97) & (rs < r0 * 1.03)
            ancs.append((math.log(max(float(np.median(u0_ref[m])), 1e-9)), math.log(niv)))
        A = np.array([[1.0, a, a * a] for a, _ in ancs])
        coef = np.linalg.solve(A, np.array([b for _, b in ancs]))
        lu = np.log(u0)
        t = np.exp(coef[0] + coef[1] * lu + coef[2] * lu ** 2)
        # monotonia: per damunt del nucli la quadràtica podria girar
        t = np.where(u0 > math.exp(ancs[0][0]), NIV_NUCLI +
                     (1 - NIV_NUCLI) * (1 - np.exp(-(u0 / math.exp(ancs[0][0]) - 1) * 3)), t)
        t = np.clip(t, 0, 1)
        print(f"corba ancorada: cel {NIV_CEL:.3f} a 5 R☉, corona {NIV_CORONA:.3f} "
              f"a 1,8 R☉ i nucli {NIV_NUCLI:.2f} → log-quadràtica {coef[1]:+.3f}·lnu {coef[2]:+.3f}·ln²u")
    # detall SOBRE la pantalla, i espatlla suau perquè les protuberàncies i el
    # nucli no retallin: per damunt de 0,88 comprimeix cap a 1 sense cantonada
    t = t * np.exp(np.where(valid, D, 0.0))
    genoll = 0.88
    t = np.where(t > genoll, genoll + (1 - genoll) * (1 - np.exp(-(t - genoll) / (1 - genoll))), t)
    t = np.clip(t, 0, 1)
    del D

    # --- 5. color: mapa DECLARAT de dos ancoratges
    #
    # ⚠️ Això és PRESENTACIÓ i es declara com a tal; l'autoritat fotomètrica és
    # `corona_vixen_lineal_16b.tif`. El motiu de no deixar-hi el color mesurat:
    # amb el Sol a 9° i massa d'aire 6,4 el cel de la totalitat és un cel de
    # POSTA —taronja— i la corona surt encara més vermella. L'ull fosc-adaptat
    # no ho veia així: el desplaçament de Purkinje li fa la penombra més blava.
    # S'ancoren dos punts mesurats al sketch de Pere i s'interpola entre ells
    # amb el senyal, que és una funció monòtona i suau del radi.
    srgb = (np.nan_to_num(hdr) * WB_DIURN) @ CAM_A_SRGB.T
    Lr = np.maximum(srgb @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)
    c = srgb / Lr[..., None]
    # ⚠️ el pes ha de portar la VALIDESA: si no, la vora morta del fotograma
    # sagna cap a dins pel suavitzat i deixa una franja magenta
    Lp = np.where(valid, np.maximum(np.nan_to_num(L), 0.0), 0.0)
    num = gaussian_filter(np.nan_to_num(c * Lp[..., None]), (10, 10, 0))
    den = gaussian_filter(Lp, 10)
    c = num / np.maximum(den, 1e-9)[..., None]
    # ⛔ El recanvi de cromaticitat només ha de mirar la vora MORTA del
    # fotograma, no el disc lunar: al voltant del disc la corona té color
    # perfectament bo, i marcar-lo com a dolent hi posava color de cel amb la
    # corona brillant a sobre — d'aquí el cercle cian que envoltava la Lluna.
    val_ext = valid | (rs < 1.30)
    prou = gaussian_filter(val_ext.astype(np.float32), 10) > 0.995
    zc = valid & (rs > 1.5) & (rs < 2.2)
    # ⚠️ l'ancoratge de color del CEL ha d'anar ben enfora: a 3,8-4,6 R☉ encara
    # hi ha corona, i posant-l'hi la imatge es tornava blava a partir de 3 R☉
    zs = valid & (rs > 6.2) & (rs < 7.0)
    mc = np.array([float(np.median(c[..., i][zc])) for i in range(3)])
    ms = np.array([float(np.median(c[..., i][zs])) for i in range(3)])
    mc, ms = mc / mc[1], ms / ms[1]
    print(f"  color MESURAT: corona R/G={mc[0]:.3f} B/G={mc[2]:.3f} · "
          f"cel R/G={ms[0]:.3f} B/G={ms[2]:.3f}")
    print(f"  objectiu del sketch: corona {OBJ_CORONA} · cel {OBJ_CEL}")
    # ⛔ el recanvi de la zona sense dades ha de ser la cromaticitat del CEL
    # MESURAT, no blanc: amb blanc, el mapa de dos ancoratges li aplicava el
    # multiplicador de blau del cel (×3,5) i la vora sortia blava saturada.
    c = np.where(prou[..., None], c, ms)
    kc = np.array(OBJ_CORONA) / mc
    ks = np.array(OBJ_CEL) / ms
    # pes d'interpolació: 1 a la corona, 0 al cel, per senyal per damunt del cel
    cel_lin = float(np.median(np.nan_to_num(L)[zs]))
    u = np.clip(np.log10(np.maximum(np.nan_to_num(L), cel_lin) / cel_lin)
                / math.log10(max(float(np.median(np.nan_to_num(L)[zc])) / cel_lin, 1.2)),
                0, 1)[..., None]
    # ⛔ TRES ancoratges de color, no dos, i el camí DECLARAT entre ells.
    # Amb dos (corona i cel) i un pes lineal en log L, el blau de la FOTO
    # arribava a neutre a 3,24 R☉ i el sketch de Pere a 4,14; els exponents
    # per canal (EXP_U) actuaven al revés del que sembla perquè el color
    # mesurat és més vermell que l'objectiu a la corona i menys al cel. Amb un
    # ancoratge al mig (3 R☉: sketch 1,17 / 0,865) el camí és el que es vol,
    # a cada zona la mediana de sortida és exactament l'objectiu, i entre
    # zones és log-lineal en u. El color mesurat només hi posa la desviació
    # LOCAL respecte del seu propi camí, comprimida per EXP_C (protuberàncies,
    # el forat coronal, els raigs).
    zm = valid & (rs > 2.7) & (rs < 3.3)
    mm = np.array([float(np.median(c[..., i][zm])) for i in range(3)])
    mm = mm / mm[1]
    u_mid = float(np.median(u[zm]))
    print(f"  color MESURAT al mig (3 R☉): R/G={mm[0]:.3f} B/G={mm[2]:.3f}, u_mid={u_mid:.3f}"
          f" · objectiu {OBJ_MIG}")
    nodes_u = np.array([0.0, u_mid, 1.0])
    ln_mes = np.log(np.stack([ms, mm, mc]))              # (3 nodes, 3 canals)
    ln_obj = np.log(np.array([OBJ_CEL, OBJ_MIG, OBJ_CORONA], dtype=np.float64))
    uu = u[..., 0]
    c_ref = np.exp(np.stack([np.interp(uu, nodes_u, ln_mes[:, i]) for i in range(3)], axis=2))
    cami = np.exp(np.stack([np.interp(uu, nodes_u, ln_obj[:, i]) for i in range(3)], axis=2))
    # ⛔ les PROTUBERÀNCIES no es comprimeixen: on el vermell mesurat supera
    # el seu camí en més d'un 25 % (H-alfa: raons de 2–4), l'exponent puja
    # cap a 1 i el rosa es conserva. Pere ho va veure al seu compost manual,
    # on surten més roses i nítides que a la FOTO.
    dlc = np.log(np.maximum(c, 1e-6)) - np.log(c_ref)
    prom = np.clip((dlc[..., 0] - 0.25) / 0.35, 0.0, 1.0)[..., None]
    exp_loc = EXP_C + (1.0 - EXP_C) * prom
    img = cami * np.exp(exp_loc * dlc)
    del c_ref, cami, dlc, prom, exp_loc
    img = img / np.maximum(img @ np.array([0.2126, 0.7152, 0.0722]), 1e-9)[..., None]
    img = img * t[..., None]

    # --- 6. earthshine real al disc de l'instant de referència
    cami = OUT / "earthshine_disc.npz"
    if LLUNA == "negra":
        # la zona que cap fotograma no va veure (la unió del disc lunar) va a
        # negre amb la mateixa ploma de 14 px que l'earthshine
        buit = (~valid).astype(np.uint8)
        buit[rs > 1.35] = 0
        dist = cv2.distanceTransform(1 - buit, cv2.DIST_L2, 5).astype(np.float32)
        pes = np.clip(1.0 - dist / 14.0, 0, 1)[..., None]
        img = img * (1 - pes)
        print("Lluna NEGRA (LLUNA=negra): sense earthshine")
    elif cami.exists():
        z = np.load(cami)
        d = z["disc"].astype(np.float64)
        dcy, dcx, rl = float(z["cy"]), float(z["cx"]), float(z["rl"])
        # posició del disc a la reixa centrada al Sol, a l'instant de referència
        oy = float(z["lluna_y"]) - float(z["sol_y"]) + cy
        ox = float(z["lluna_x"]) - float(z["sol_x"]) + cx
        yy = (np.arange(H) - oy)[:, None]
        xx = (np.arange(W) - ox)[None, :]
        rd = np.hypot(xx, yy)
        sy = (np.arange(H) - oy + dcy * 2) / 2.0
        sx = (np.arange(W) - ox + dcx * 2) / 2.0
        gy = np.clip(sy, 0, d.shape[0] - 1).astype(int)
        gx = np.clip(sx, 0, d.shape[1] - 1).astype(int)
        relleu = gaussian_filter(d, 1.5)[np.ix_(gy, gx)]
        # ⛔ l'ajust polinòmic es dispara a la vora del disc: el relleu s'ha
        # d'esvair cap a la seva mediana abans d'arribar-hi, o al voltant de la
        # Lluna hi queda un anell clar que no és de ningú
        cua = np.clip((rl * 2 * 0.965 - rd) / (rl * 2 * 0.06), 0, 1)
        relleu = relleu * cua + np.median(relleu[rd < rl * 1.6]) * (1 - cua)
        q = np.percentile(relleu[rd < rl * 1.5], [3, 97])
        u = np.clip((relleu - q[0]) / max(q[1] - q[0], 1e-9), 0, 1)
        # nivell: el disc ha de quedar clarament per damunt del cel i per sota
        # de la corona. ⚠️ el nivell absolut de l'earthshine és degenerat amb
        # el model de halo, o sigui que això és PRESENTACIÓ i es declara.
        cel_t = float(np.median(t[valid & (rs > 6.2) & (rs < 7.0)]))
        # (17-08, auditoria del sketch) la mediana ja hi era (1,54× el cel) però
        # el rang era quatre vegades el del sketch (p95/p5 1,63 contra 1,12):
        # el disc del sketch és PLA amb un lleu escalfament cap al limbe
        n0, n1 = cel_t * 1.50, cel_t * 1.68
        disc_t = n0 + (n1 - n0) * u
        c_es = np.array([1.07, 1.0, 0.93])
        # ⛔ El disc ha de cobrir EXACTAMENT la zona que el compost de corona
        # no té. Allà la Lluna hi era a tots els fotogrames i el que hi surti
        # és interpolació: si el disc s'hi queda curt, entre les dues vores hi
        # queda un anell d'11 px sense amo, que és d'on sortia el cercle cian.
        buit = (~valid).astype(np.uint8)
        buit[rd > rl * 2 * 1.25] = 0
        dist = cv2.distanceTransform(1 - buit, cv2.DIST_L2, 5).astype(np.float32)
        pes = np.clip(1.0 - dist / 14.0, 0, 1)[..., None]
        img = img * (1 - pes) + (disc_t[..., None] * c_es) * pes
        print(f"earthshine: disc a {n0:.3f}-{n1:.3f} de pantalla, cel a {cel_t:.3f}")
    else:
        print("⚠️ falta earthshine_disc.npz: executa l'etapa `earthshine`")

    img = np.clip(img, 0, 1)
    img = np.maximum(img, 0.004)
    img = img[RETALL[0]:RETALL[1] + 1, RETALL[2]:RETALL[3] + 1]
    nom_s = os.environ.get("FOTO_SUFIX", "")
    escriu_tiff(OUT / f"corona_vixen_FOTO{nom_s}.tif", img, "srgb")
    cv2.imwrite(str(OUT / f"corona_vixen_FOTO{nom_s}_2400.jpg"),
                cv2.resize((img[..., ::-1] * 255).astype(np.uint8), (2400, 1600),
                           interpolation=cv2.INTER_AREA),
                [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    (OUT / "foto_params.json").write_text(json.dumps({
        "gamma_radial": GAMMA_RADIAL,
        "gamma_to": gam, "obj_corona": OBJ_CORONA, "obj_cel": OBJ_CEL,
        "detall": mode_detall,
        "bandes_deg": BANDES_DEG, "guanys_deg": GUANYS_DEG,
        "bandes_px_(cami_px)": BANDES_PX, "guanys_banda_(cami_px)": GUANYS_BANDA,
        "detall_aplicat_sobre": "t (pantalla), t·exp(D), espatlla suau a 0,88",
        "lo": lo, "hi": hi,
        "nota": "el nivell de l'earthshine és presentació: el seu valor "
                "absolut és degenerat amb el model de halo",
    }, indent=1, ensure_ascii=False))
    print("→ corona_vixen_FOTO.tif  i  _2400.jpg")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["geometria", "deriva", "escala", "hdr", "vis", "tiff",
                                      "earthshine", "foto", "passalt"])
    args = ap.parse_args()
    {"geometria": etapa_geometria, "deriva": etapa_deriva, "escala": etapa_escala,
     "hdr": etapa_hdr, "vis": etapa_vis, "tiff": etapa_tiff,
     "earthshine": etapa_earthshine, "foto": etapa_foto, "passalt": etapa_foto}[args.etapa](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
