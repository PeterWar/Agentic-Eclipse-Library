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

SRC = Path.home() / "Desktop/Eclipse 2026/Vixen Unfiltered"
MASTERS = SRC / "Masters_v2"
OUT = Path.home() / "Desktop/Eclipse 2026/Corona_HDR_Vixen"

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


def calibra(f: Fotograma) -> tuple[np.ndarray, int]:
    """Mosaic calibrat en comptes crus per damunt del fosc (NO dividit pel
    temps) i recompte de fotolocalitats al pou."""
    with rawpy.imread(str(SRC / f.nom)) as raw:
        cru = parell(raw.raw_image_visible)
    n_sat = int((cru >= POU).sum())
    return cru.astype(np.float32) - master(f.exp_nominal), n_sat


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
    eph = load("de440s.bsp")
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

    escala_unitat = os.environ.get("ESCALA_UNITAT") == "1"
    rampa = float(os.environ.get("RAMPA_SOSTRE", "0.25"))
    for k, f in enumerate(fg, 1):
        mos, _ = calibra(f)
        rn = RN_CURT if f.exp_s < LLINDAR_MODE_S else RN_LLARG
        t = f.exp_s * (1.0 if escala_unitat else f.escala_rel)
        # posició del disc lunar dins la reixa de sortida (centrada al Sol)
        dlx = f.lluna_x - f.sol_x + cx_out
        dly = f.lluna_y - f.sol_y + cy_out
        mask_lluna = np.hypot(rx - (dlx - cx_out), ry - (dly - cy_out)) < R_LLUNA_PX + 8

        for nom_pla, (pla, oy, ox) in plans(mos).items():
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
                    ml = mask_lluna[par_y::2, par_x::2][vy, vx]
                    ww = np.where(ml, 0.0, ww)
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

def perfil_azimutal(img: np.ndarray, r: np.ndarray, r_complet: float
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
            perfil[k] = np.median(img[m])
    idx = np.arange(n)
    ok = np.isfinite(perfil)
    perfil = np.interp(idx, idx[ok], perfil[ok])
    perfil = np.convolve(np.pad(perfil, 8, mode="edge"), np.ones(17) / 17, "valid")
    # extrapolació en llei de potència ajustada al 20 % exterior mesurat
    a0, a1 = int(0.55 * lim), lim
    lx = np.log(idx[a0:a1] + 1.0)
    ly = np.log(np.maximum(perfil[a0:a1], 1e-6))
    pend, ord0 = np.polyfit(lx, ly, 1)
    ext = np.exp(ord0 + pend * np.log(idx[lim:] + 1.0))
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


def etapa_vis(args) -> None:
    hdr = np.load(OUT / "hdr_vixen_countss.npy")
    cob = np.load(OUT / "hdr_vixen_cobertura.npy")
    varm = np.load(OUT / "hdr_vixen_var.npy")
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

    det = realca(norm, [1.25, 2.5, 5, 10, 20, 40, 80], sig_norm)
    disc = ~valid
    mix = np.clip(0.55 * gamma + 0.45 * (det * 0.5 + 0.5), 0, 1)
    desa_png("corona_vixen_detall", np.where(disc, 0.10, mix))

    # --- retalls a resolució completa: aquí és on es veu si el drizzle ha
    #     comprat detall, perquè la reixa de sortida és la del sensor
    for nom, r_max, barreja in (("3Rsol", 3.0, 0.45), ("15Rsol", 1.55, 0.35)):
        m = int(r_max * R_SOL_PX)
        sl = (slice(int(cy) - m, int(cy) + m), slice(int(cx) - m, int(cx) + m))
        n_ = norm[sl]
        d_ = realca(n_, [1.0, 2, 4, 8, 16, 32], sig_norm[sl])
        g_ = gamma[sl]
        v_ = np.clip((1 - barreja) * g_ + barreja * (d_ * 0.5 + 0.5), 0, 1)
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
        "sigmes_realcat": [1.25, 2.5, 5, 10, 20, 40, 80],
        "factor_B_Bsol_per_ADU_s": 2.772e-11,
        "continuitat_max_pct": pitjor * 100,
        "nota": "el blau queda fora de la luminància: 4,33 e-/ADU contra 5,08 "
                "(research/75 §3) i FWHM 1,4× més gran",
    }, indent=1, ensure_ascii=False))



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["geometria", "deriva", "escala", "hdr", "vis"])
    args = ap.parse_args()
    {"geometria": etapa_geometria, "deriva": etapa_deriva, "escala": etapa_escala,
     "hdr": etapa_hdr, "vis": etapa_vis}[args.etapa](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
