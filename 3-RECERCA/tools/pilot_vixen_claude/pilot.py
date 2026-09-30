"""Pilot Vixen des de zero: fase 0 Calibració · 1 Registre · 2 Composició LDIC.

Ordre de Pere del 23-08-2026 (D2 de `research/97`). Un sol tren, una sola
tirada, portes amb dents i rebuts.

ARQUITECTURA DE LA FASE 2 — **una sola suma ponderada**, mai apilar per
exposició i després fusionar:

    N = Σ_f w_f · J_f          D = Σ_f w_f          g = N / D

amb `w = t² / (S/g + RN²)`, que és el pes òptim d'inversa de la variància per a
una magnitud mesurada en comptes/s, i `J = S/t`. Els 68 fotogrames de les 15
exposicions hi entren tots alhora. `N` i `D` es persisteixen: són l'autoritat
del que Photoshop haurà de reproduir, i el numerador i el denominador han
d'existir per separat perquè la composició alfa **no** calcula Σ(wI)/Σw.

⛔ El flat va abans del warp (no commuten) i cap producte lineal no es
multiplica per cap màscara.

REIXA. La suma es fa a la reixa del sensor centrada al Sol —translacions
subpíxel pures, que és el que la muntura fa— i el gir a nord amunt del llenç
comú s'aplica **una sola vegada al final**, al compost. Girar cada fotograma
costaria 68 interpolacions en lloc d'una i no compra res: la rotació és la
mateixa per a tots.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu as C
import portes as P

# ⛔ Els productes són no-clobber: per refer una fase sense trepitjar la tirada
# d'abans, es dona un arrel nou per entorn i s'hi enllacen les entrades que no
# es refan. Per defecte, la tirada del 23-08.
_ARREL = os.environ.get("PILOT_SORTIDA", "pilot_vixen_claude_20260823")
_PREV = os.environ.get("PILOT_PREVIS", _ARREL)
OUT_ARREL = C.REPO / "output" / _ARREL
PREV_ARREL = C.DESK / "IA" / "output" / _PREV
PES_SUAU = float(os.environ.get("PILOT_PES_SUAU", "0"))   # px de pla; 0 = com sempre
PIXFRAC = 2.0            # amplada de la gota, en px de SORTIDA (= pixfrac 1,0 clàssic)

_t0 = time.time()


def log(*a):
    print(f"[{time.time() - _t0:7.1f}s]", *a, flush=True)


def parametres_del_pilot() -> dict:
    """Els paràmetres efectius, per tren. Viu a `comu` perquè les eines de
    diagnòstic l'han de poder estampar igual que el pilot."""
    return C.parametres_efectius()


def desa(nom: str, valor) -> Path:
    OUT_ARREL.mkdir(parents=True, exist_ok=True)
    return C.desa_json(OUT_ARREL / nom, valor)


def pesos_gota(frac: float) -> tuple[int, np.ndarray]:
    a, b = frac - PIXFRAC / 2, frac + PIXFRAC / 2
    k0, k1 = math.floor(a), math.floor(b)
    w = np.array([max(0.0, min(b, k + 1) - max(a, k)) for k in range(k0, k1 + 1)])
    return k0, w / w.sum()


# ================================================================ FASE 0
# ⛔ Comença a 1,15 R☉ pel mateix motiu que les portes E i E2 (§9): la màscara
# lunar arriba a 1,085 R☉ i la Lluna es mou ±14 px respecte del Sol, o sigui
# que en radi solar la seva vora queda escampada fins a **1,117 R☉**. Un anell
# que hi comenci mesura la màscara.
ANELLS_F0 = [(1.15, 1.30), (1.30, 1.60), (1.60, 2.20), (2.20, 3.20), (3.20, 4.20)]
SENYAL_MIN_ADU = 30.0        # per sota d'això l'esglaó no té senyal a l'anell
SAT_MAX = 0.01               # fracció de píxels saturats tolerada


def taxa_anell(f: C.Fotograma, mos: np.ndarray, r0: float, r1: float,
               exp_s: float, sat: np.ndarray | None = None,
               mos_sat: np.ndarray | None = None) -> dict[str, float]:
    """Taxa mediana (ADU/s) de cada pla dins un anell, en R☉ al voltant del Sol.

    ⚠️ El tall de saturació és `SOSTRE` (0,85 del pou), no el nivell de blanc.
    Mesurat el 23-08: al fotograma de 10,08 s, a 1,05–1,15 R☉ la mediana val
    **15.857 ADU sobre el fosc** —el pou n'és 15.872— i la màscara dura
    `cru >= 16383` només n'atrapa el **0,9 %**, perquè el cos no clava tots els
    píxels saturats al mateix valor enter. Fiar-se'n deixava entrar píxels del
    pou al mig d'una mesura de corona.
    """
    out = {}
    sx, sy = f.sol_usat if math.isfinite(f.sol_usat[0]) else (f.sol_x, f.sol_y)
    # ⛔ La saturació es jutja amb el mosaic CRU quan se n'hi ha restat el cel:
    # restar-lo abans del llindar torna admissibles píxels que són al pou.
    plans_sat = C.plans(mos if mos_sat is None else mos_sat)
    for nom, (pla, oy, ox) in C.plans(mos).items():
        rr = C.anells(*pla.shape, (sy - oy) / 2, (sx - ox) / 2) * 2
        m = ((rr > r0 * C.R_SOL_PX) & (rr < r1 * C.R_SOL_PX)
             & (plans_sat[nom][0] <= C.SOSTRE))
        if sat is not None:
            m &= ~C.plans(sat.astype(np.uint8))[nom][0].astype(bool)
        out[nom] = float(np.median(pla[m])) / exp_s if m.any() else math.nan
    return out


def _perfil_frame(f, mos, sat, exp, resta_fons=True, mos_sat=None):
    """Taxa verda per anell, ja anivellada de cel, i fracció saturada.

    ⛔ `resta_fons=False` quan el cel ja s'ha restat amb el model 2-D: restar
    també l'anell exterior seria treure'l dues vegades, i el que quedaria a
    l'anell exterior —que és corona de veritat— es restaria de tots els altres.
    """
    if not resta_fons:
        nivell = 0.0
    else:
        fons = taxa_anell(f, mos, *C.FONS_ANELL, exp, sat, mos_sat)
        nivell = 0.5 * (fons["G1"] + fons["G2"])
    out = []
    for r0, r1 in ANELLS_F0:
        t = taxa_anell(f, mos, r0, r1, exp, sat, mos_sat)
        brut = 0.5 * (t["G1"] + t["G2"])
        pla, oy, ox = C.plans(mos)["G1"]
        sx, sy = f.sol_usat if math.isfinite(f.sol_usat[0]) else (f.sol_x, f.sol_y)
        rr = C.anells(*pla.shape, (sy - oy) / 2, (sx - ox) / 2) * 2
        m = (rr > r0 * C.R_SOL_PX) & (rr < r1 * C.R_SOL_PX)
        pla_s = C.plans(mos if mos_sat is None else mos_sat)["G1"][0]
        alt = (pla_s > C.SOSTRE) | C.plans(sat.astype(np.uint8))["G1"][0].astype(bool)
        fs = float(alt[m].mean()) if m.any() else 1.0
        out.append({"anell": [r0, r1], "taxa_bruta": brut, "senyal": brut - nivell,
                    "senyal_adu": (brut - nivell) * exp, "frac_saturada": fs})
    return nivell, out


def fase0(args) -> dict:
    fg = C.llegeix_manifest()
    # ⚠️ El centre ve de la fase 1: el del manifest està 3,6 px fora (0,83 % de
    # R☉) i a 1,05 R☉ el gradient de la corona és prou fort perquè això biaixi
    # la mediana d'un anell. L'ordre real és registre → binning radial.
    centres_finals(fg)
    log(f"fase 0 · calibratge de {len(fg)} fotogrames (centre de la fase 1)")

    with __import__("rawpy").imread(str(C.SRC / fg[0].nom)) as raw:
        forma = C.parell(raw.raw_image_visible).shape
    flat = C.flat_mosaic(forma)
    rr = C.anells(*forma, fg[0].sol_y, fg[0].sol_x)
    dom = (rr >= 1.3 * C.R_SOL_PX) & (rr <= 7.0 * C.R_SOL_PX)
    amp = P.porta_f0_amplitud_flat(flat[dom])
    log(f"  flat radial dins 1,3–7 R☉: {amp['amplitud_percent']:.2f} % "
        f"({amp['amplitud_ev']:.4f} EV) → {amp['estat']}")

    per_frame = {"fisiques": {}, "manifest": {}}
    cels = []
    usa_model = getattr(args, "cel", "anell") == "model"
    if usa_model:
        S_cel, forma = carrega_model_cel()
        log("  cel: model 2-D restat abans de mesurar")
    for k, f in enumerate(fg, 1):
        mos, sat = C.calibra(f)
        mos_cru = None
        if usa_model:
            mos_cru = mos.copy()
            mos = mos - cel_del_fotograma(f, forma, S_cel, mos.shape)
        for etiq, e in (("fisiques", f.exp_s), ("manifest", f.exp_manifest)):
            niv, perf = _perfil_frame(f, mos, sat, e, resta_fons=not usa_model,
                                      mos_sat=mos_cru)
            per_frame[etiq].setdefault(e, []).append(perf)
            if etiq == "fisiques":
                cels.append((f.t_rel_c2, niv))
        del mos, sat
        if k % 20 == 0 or k == len(fg):
            log(f"  [{k:2d}/{len(fg)}] {f.nom}")
    c = np.array([v for _, v in cels])
    if usa_model:
        log("  (el cel ja s'ha restat amb el model 2-D; l'estadístic és la taxa directa)")
    else:
        log(f"  cel al fons: de {c.min():.1f} a {c.max():.1f} ADU/s "
            f"({100 * (c.max() - c.min()) / np.median(c):.0f} % de variació)")

    def avalua(etiq):
        exps = sorted(per_frame[etiq])
        detall = []
        pitjor = 0.0
        fallen = []
        for ia, (r0, r1) in enumerate(ANELLS_F0):
            dades = {}
            for e in exps:
                vs = [p[ia] for p in per_frame[etiq][e]]
                sa = float(np.median([v["senyal_adu"] for v in vs]))
                fs = float(np.median([v["frac_saturada"] for v in vs]))
                if sa >= SENYAL_MIN_ADU and fs <= SAT_MAX:
                    dades[e] = [float(v["senyal"]) for v in vs]
            if len(dades) < 3:
                detall.append({"anell": [r0, r1], "esglaons": len(dades),
                               "estat": "SENSE_PROU_ESGLAONS"})
                continue
            g = P.porta_f0_esglaons(dades)
            pitjor = max(pitjor, abs(g.get("pitjor_desviacio", 0.0)))
            if g["estat"] == "FAIL":
                fallen.append([r0, r1])
            detall.append({"anell": [r0, r1], "esglaons": len(dades),
                           "exposicions": [f"{e:.9g}" for e in sorted(dades)], **g})
        return detall, pitjor, fallen

    d_fis, p_fis, f_fis = avalua("fisiques")
    d_nom, p_nom, f_nom = avalua("manifest")
    ok = not f_fis
    log(f"  F0' amb temps FÍSICS   → {'PASS' if ok else 'FAIL'}  "
        f"pitjor desviació {100 * p_fis:+.2f} %, {len(f_fis)} anells fallen")
    log(f"  F0' amb temps NOMINALS → {'PASS' if not f_nom else 'FAIL'}  "
        f"pitjor desviació {100 * p_nom:+.2f} %, {len(f_nom)} anells fallen")
    for a in d_fis:
        if "pitjor_desviacio" in a:
            log(f"    {a['anell'][0]:.2f}–{a['anell'][1]:.2f} R☉  "
                f"{a['esglaons']:2d} esglaons  pitjor {100 * a['pitjor_desviacio']:+6.2f} %  "
                f"rms {100 * a['rms_desviacio']:.2f} % contra terra "
                f"{100 * (a.get('terra_de_precisio') or 0):.2f} %  {a['estat']}")

    res = {"fase": "0_calibratge",
           "ordre": "fosc → PRNU → flat radial (⛔ sempre abans de qualsevol warp)",
           "estadistic": ("senyal = taxa(anell) − taxa(4,2–5,1 R☉), o sigui corona menys "
                          "cel: és cec a un cel additiu, que varia un ±20 % durant la "
                          "totalitat, i sensible a qualsevol error MULTIPLICATIU (temps "
                          "d'exposició, escala del fosc, guany)"),
           "criteri_d_inclusio": {"senyal_minim_adu": SENYAL_MIN_ADU,
                                  "fraccio_saturada_maxima": SAT_MAX,
                                  "motiu": ("a 2 R☉ una pose d'1/3250 s recull 0,2 ADU de "
                                            "corona: el que s'hi mesuraria és un sistemàtic "
                                            "de sub-ADU amplificat per 1/t, no el calibratge. "
                                            "Cada esglaó es jutja a l'anell on TÉ senyal.")},
           "porta_f0_amplitud_flat": amp,
           "porta_f0_esglaons_temps_fisics": {"estat": "PASS" if ok else "FAIL",
                                              "pitjor_desviacio": round(p_fis, 6),
                                              "anells_que_fallen": f_fis, "per_anell": d_fis},
           "control_temps_nominals": {"estat": "PASS" if not f_nom else "FAIL",
                                      "pitjor_desviacio": round(p_nom, 6),
                                      "anells_que_fallen": f_nom, "per_anell": d_nom,
                                      "nota": ("la diferència física↔nominal és del 2 al "
                                               "6 %, i el terra de precisió d'aquesta prova "
                                               "és del 2,5 al 4,3 %: la prova NO té potència "
                                               "per decidir-ho. L'escala física s'adopta per "
                                               "autoritat del MakerNote.")},
           "cel_al_fons_adu_s": ({"restat_amb_model_2d": True} if usa_model else
                                 {"minim": round(float(c.min()), 3),
                                  "maxim": round(float(c.max()), 3),
                                  "variacio_percent": round(
                                      100 * float(c.max() - c.min())
                                      / max(float(np.median(c)), 1e-9), 2)}),
           "cel": "model_2d" if usa_model else "anivellament_per_anell",
           "escala_exposicio_fisica": {f"{k:.10g}": v for k, v in C.EXP_FISICA.items()}}
    desa("fase0_calibratge.json", res)
    return res


# ================================================================ FASE 1
EXP_MAX_AJUST = 1.0     # per damunt d'això el limbe va arrossegat i el centre és biaixat


def _dades_registre(fg: list[C.Fotograma]):
    import csv as _csv
    mes = {}
    for r in _csv.DictReader(C.MANIFEST.open()):
        vx, vy = r["lluna_mes_x"], r["lluna_mes_y"]
        mes[r["nom"]] = (math.nan if vx in ("", "nan") else float(vx),
                         math.nan if vy in ("", "nan") else float(vy))
    t = np.array([f.t_rel_c2 for f in fg])
    mx = np.array([mes[f.nom][0] for f in fg])
    my = np.array([mes[f.nom][1] for f in fg])
    return t, mx, my


def _model_deriva(fg: list[C.Fotograma]):
    """Model de deriva ajustat NOMÉS als limbes mesurats de les exposicions curtes.

    L'exclusió té mesura pròpia: respecte del model dels curts, el centre del
    limbe surt desplaçat **+0,538 px als 2 s i +1,185 px als 10,08 s**. És
    l'arrossegament, que a 0,610 ″/s deixa 2,92 px de traça en una pose llarga,
    més el vessament de la corona interior sobre el limbe. Un centre biaixat
    que entri a l'ajust arrossega el model de TOTS els fotogrames.
    """
    t, mx, my = _dades_registre(fg)
    ex = np.array([f.exp_s for f in fg])
    a, b = mx.copy(), my.copy()
    a[ex > EXP_MAX_AJUST] = np.nan
    b[ex > EXP_MAX_AJUST] = np.nan
    o = np.flatnonzero(np.isfinite(a))
    A = np.vstack([np.ones(o.size), t[o]]).T
    cx, *_ = np.linalg.lstsq(A, a[o], rcond=None)
    cy, *_ = np.linalg.lstsq(A, b[o], rcond=None)
    return t, mx, my, a, b, cx, cy


def centres_finals(fg: list[C.Fotograma], font: str = "efemerides") -> dict:
    """Centre solar adoptat.

    `font="limbe"`: model ajustat al limbe lunar MESURAT + desplaçament
    Sol−Lluna d'efemèrides. `font="efemerides"`: el `sol_x, sol_y` del manifest
    tal qual, que surt del model lunar d'efemèrides.
    """
    if font == "efemerides":
        for f in fg:
            f.sol_usat = (float(f.sol_x), float(f.sol_y))
            f.origen_centre = "efemerides_del_manifest"
            f.sigma_centre = (f.limbe_rms / math.sqrt(f.limbe_n)) if f.limbe_n else math.nan
        return {"coeficients": {"font": "efemerides_del_manifest"},
                "exp_max_a_l_ajust_s": None, "detall": []}
    t, mx, my, a, b, cx, cy = _model_deriva(fg)
    detall = []
    for i, f in enumerate(fg):
        lx_m = cx[0] + cx[1] * t[i]
        ly_m = cy[0] + cy[1] * t[i]
        # el desplaçament Sol−Lluna és efemèride i es conserva del manifest
        off_x, off_y = f.sol_x - f.lluna_x, f.sol_y - f.lluna_y
        f.sol_usat = (float(lx_m + off_x), float(ly_m + off_y))
        f.origen_centre = ("model_limbe_mesurat" if np.isfinite(a[i])
                           else ("model_extrapolat_exp_llarga" if np.isfinite(mx[i])
                                 else "model_sense_limbe_mesurat"))
        f.sigma_centre = (f.limbe_rms / math.sqrt(f.limbe_n)) if f.limbe_n else math.nan
        detall.append({
            "nom": f.nom, "exp_s": f.exp_s, "t_rel_c2": round(f.t_rel_c2, 4),
            "limbe_mesurat": bool(np.isfinite(mx[i])), "a_l_ajust": bool(np.isfinite(a[i])),
            "origen_centre": f.origen_centre,
            "sol_manifest": [round(f.sol_x, 4), round(f.sol_y, 4)],
            "sol_adoptat": [round(f.sol_usat[0], 4), round(f.sol_usat[1], 4)],
            "correccio_px": round(math.hypot(f.sol_usat[0] - f.sol_x,
                                             f.sol_usat[1] - f.sol_y), 4)})
    return {"coeficients": {"x0": float(cx[0]), "vx_px_s": float(cx[1]),
                            "y0": float(cy[0]), "vy_px_s": float(cy[1]),
                            "v_arcsec_s": float(math.hypot(cx[1], cy[1]) * C.ESCALA)},
            "exp_max_a_l_ajust_s": EXP_MAX_AJUST, "detall": detall}


def fase1(args) -> dict:
    fg = C.llegeix_manifest()
    t, mx, my, a, b, cx, cy = _model_deriva(fg)
    noms = [f.nom for f in fg]
    log(f"fase 1 · registre · {int(np.isfinite(mx).sum())} limbes mesurats de {len(fg)}")

    g_tot = P.porta_f1_registre(t, mx, my, noms)
    g_curt = P.porta_f1_registre(t, a, b, noms)
    log(f"  amb TOTS els mesurats  → {g_tot['estat']}  ruptura "
        f"{g_tot.get('salt_de_ruptura_px')} px, p={g_tot.get('salt_p_valor')}")
    log(f"  amb exp ≤ {EXP_MAX_AJUST} s        → {g_curt['estat']}  split-half "
        f"{g_curt.get('separacio_maxima_px')} px")

    # biaix mesurat de cada exposició respecte del model dels curts
    biaix = {}
    ex = np.array([f.exp_s for f in fg])
    for e in sorted(set(ex[np.isfinite(mx)])):
        k = np.flatnonzero((ex == e) & np.isfinite(mx))
        dx = float((mx[k] - (cx[0] + cx[1] * t[k])).mean())
        dy = float((my[k] - (cy[0] + cy[1] * t[k])).mean())
        biaix[f"{e:.9g}"] = {"n": len(k), "dx_px": round(dx, 4), "dy_px": round(dy, 4),
                             "modul_px": round(math.hypot(dx, dy), 4)}

    cen = centres_finals(fg)
    corr = [d["correccio_px"] for d in cen["detall"]]
    log(f"  correcció respecte del centre del manifest: mediana {np.median(corr):.3f} px "
        f"({100*np.median(corr)/C.R_SOL_PX:.2f} % de R☉)")

    res = {"fase": "1_registre",
           "que_no_entra_a_la_porta": {
               "residu_solucio_de_placa_px": 0.4241932989610208,
               "motiu": ("una sola solució de placa per als 68 fotogrames: el seu error és "
                         "COMÚ, desplaça/gira/escala el llenç sencer igual per a tothom i "
                         "no desenfoca l'apilat."),
               "sol_x_sol_y_del_manifest": ("NO és una mesura: surt d'un model lineal exacte "
                                            "(residu 0,000000 px). Avaluar-hi un oracle "
                                            "seria una porta vàcua.")},
           "porta_f1": g_curt,
           "control_dolent_amb_llargues_a_l_ajust": g_tot,
           "biaix_del_limbe_per_exposicio": biaix,
           "model_adoptat": cen["coeficients"],
           "exp_max_a_l_ajust_s": EXP_MAX_AJUST,
           "correccio_del_centre": {
               "mediana_px": round(float(np.median(corr)), 4),
               "maxim_px": round(float(np.max(corr)), 4),
               "percent_de_rsol": round(100 * float(np.median(corr)) / C.R_SOL_PX, 4),
               "nota": ("el centre del manifest surt del model lunar d'efemèrides i està "
                        "desplaçat respecte del limbe realment mesurat; és un biaix COMÚ, "
                        "no desenfoca però mou l'origen de tot perfil radial.")},
           "gir_de_camp": {
               "radi_vora_px": 4181.0,
               "gir_equivalent_al_split_half_graus": round(
                   P.cota_gir_camp(g_curt.get("separacio_maxima_px", math.nan), 4181.0), 6),
               "nota": ("no s'aplica cap terme de gir: el model de translació ja tanca la "
                        "porta. Si un dia no la tanqués, el terme que falta és aquest.")},
           "ledger": cen["detall"]}
    desa("fase1_registre.json", res)
    return res


# ================================================================ FASE 2
def anivella_fons(fg: list[C.Fotograma], exp_attr: str) -> dict[str, np.ndarray]:
    """Desplaçament de cel a restar a cada pla, en comptes crus.

    El cel de la totalitat NO és estacionari: la seva taxa fa una V de ±20 %
    perquè prop de C2 i C3 el punt d'observació és a tocar de la vora de
    l'ombra. Com que cada radi del compost el domina un esglaó diferent, i cada
    esglaó és d'un instant diferent, sense això el compost porta un nivell de
    cel diferent a cada radi. Es corregeix la DIFERÈNCIA, no el nivell: la
    corona no canvia en 100 s i el nivell comú es conserva.
    """
    ordre = ["R", "G1", "G2", "B"]
    taxes = {}
    for f in fg:
        mos, _ = C.calibra(f)
        t = getattr(f, exp_attr)
        taxes[f.nom] = np.array([taxa_anell(f, mos, *C.FONS_ANELL, t)[n] for n in ordre])
        del mos
    ref = np.median(np.array([taxes[f.nom] for f in fg]), axis=0)
    v = np.array([taxes[f.nom][1] for f in fg])
    log(f"  cel: verd de {v.min():.1f} a {v.max():.1f} ADU/s "
        f"({100 * (v.max() - v.min()) / ref[1]:.1f} % de variació)")
    return {f.nom: (taxes[f.nom] - ref) * getattr(f, exp_attr) for f in fg}


# ================================================================ coherència
# ⛔ **El terra són 1,15 R☉ i no es pot abaixar.** La temptació hi és: a 1,16 R☉
# el fotograma d'1/3251 s només porta 12 ADU i el de 1/2048 s 18, per sota del
# terra de senyal, o sigui que els quatre esglaons més curts no s'hi ajusten.
# Però **la Lluna es mou 28,7 px = 0,065 R☉ durant la totalitat**, i el seu
# limbe, que és a 1,043 R☉, arriba fins a 1,108: per sota d'1,15 els fotogrames
# ja no comparen la mateixa escena, i l'ajust ho paga. Mesurat el 24-08-2026:
# baixant el terra a 1,09 el residu de l'ajust puja de 0,15-0,17 % a 0,31-0,37 %.
# Els esglaons que es queden sense ajust NO es queden a c = 1 en silenci: agafen
# el valor de la corba temporal al seu instant, i el rebut ho diu.
COH_R = (1.15, 7.0)     # rang radial de l'ajust, en R☉
COH_N = 220             # anells (uniformes en log r)


def perfil_per_fotograma(f: "C.Fotograma", amb_flat: bool, exp_attr: str):
    """Perfil radial per pla d'un fotograma, en ADU/s i amb la seva validesa."""
    mos, sat = C.calibra(f, amb_flat=amb_flat)
    t = getattr(f, exp_attr)
    sx, sy = f.sol_usat if math.isfinite(f.sol_usat[0]) else (f.sol_x, f.sol_y)
    vores = np.exp(np.linspace(math.log(COH_R[0]), math.log(COH_R[1]), COH_N + 1))
    plans_sat = C.plans(sat.astype(np.uint8))
    out = {}
    for nom, (pla, oy, ox) in C.plans(mos).items():
        rr = C.anells(*pla.shape, (sy - oy) / 2, (sx - ox) / 2) * 2 / C.R_SOL_PX
        # ⛔ el tall de saturació és SOSTRE, no el nivell de blanc (research/99)
        bo = (pla <= C.SOSTRE) & (plans_sat[nom][0] == 0) & np.isfinite(pla)
        idx_tot = np.digitize(rr.ravel(), vores) - 1
        dins = (idx_tot >= 0) & (idx_tot < COH_N)
        ntot = np.bincount(idx_tot[dins], minlength=COH_N)
        v = (pla / t).ravel()
        m = bo.ravel() & dins
        idx, v = idx_tot[m], v[m]
        o = np.argsort(idx, kind="stable")
        idx_s, v_s = idx[o], v[o]
        talls = np.searchsorted(idx_s, np.arange(COH_N + 1))
        med = np.full(COH_N, np.nan)
        npx = np.zeros(COH_N, np.int64)
        for i in range(COH_N):
            a, b = talls[i], talls[i + 1]
            # ⛔ Tres criteris, i cap no és nou: són els de la fase 0. (1) prou
            # mostra; (2) la MAJORIA de l'anell vàlida —un anell mig saturat és
            # un anell esbiaixat cap avall—; (3) **senyal de veritat**: per sota
            # de SENYAL_MIN_ADU el que es mesura és el residu del fosc i del
            # flat, no la corona. Sense el (3) l'ajust agafava els anells buits
            # de les exposicions curtes i donava transparències del 0,52 al
            # 1,28, o sigui un 65 % d'amplitud: impossible.
            if (b - a) >= 300 and (b - a) >= 0.5 * ntot[i]:
                mm = float(np.median(v_s[a:b]))
                if mm * t >= SENYAL_MIN_ADU:
                    med[i] = mm; npx[i] = b - a
        out[nom] = (med, npx)
    del mos, sat
    return out, np.exp(0.5 * (np.log(vores[:-1]) + np.log(vores[1:])))


def ajusta_coherencia(perfils: dict, noms: list[str], t_fg: np.ndarray,
                      plans: list[str], log_pref: str = "  "):
    """El solucionador, compartit pels DOS trens.

    `perfils[nom][pla] = (medianes_per_anell, n_px_per_anell)`. Retorna
    `(factors, cels, diagnostic)`. Vegeu `fase_coherencia` per al perquè.
    """
    factors = {n: {} for n in noms}
    cels = {n: {} for n in noms}
    diag = {}
    for pla in plans:
        P = np.array([perfils[n][pla][0] for n in noms])          # (n_fg, COH_N)
        N = np.array([perfils[n][pla][1] for n in noms])
        val = np.isfinite(P) & (N > 0)
        c = np.ones(len(noms)); s = np.zeros(len(noms))
        ajustat = np.zeros(len(noms), bool)
        Cr = np.nanmedian(np.where(val, P, np.nan), axis=0)
        for it in range(40):
            # --- per fotograma: regressió ponderada de P_i sobre (C, 1)
            for i in range(len(noms)):
                m = val[i] & np.isfinite(Cr) & (Cr > 0)
                if m.sum() < 20:
                    continue
                # ⛔ Es fa en forma de QUOCIENT: y/C = c + (c·s)·(1/C). La
                # dispersió d'un anell la domina la corona, que és la MATEIXA a
                # tots els fotogrames i per tant es cancel·la al quocient; usar-la
                # com si fos error (pesos 1/σ²) seria pesar per una cosa que no
                # hi és. Aquí cada anell pesa igual i el residu del quocient diu
                # sol quina precisió té la mesura.
                u = P[i][m] / Cr[m]
                z = 1.0 / Cr[m]
                bo_i = np.ones(u.size, bool)
                a = b = float("nan")
                for _ in range(3):
                    if bo_i.sum() < 10:
                        break
                    A = np.vstack([np.ones(bo_i.sum()), z[bo_i]]).T
                    sol, *_ = np.linalg.lstsq(A, u[bo_i], rcond=None)
                    a, b = float(sol[0]), float(sol[1])
                    r_ = u - (a + b * z)
                    mad = float(np.median(np.abs(r_ - np.median(r_)))) * 1.4826
                    if not (mad > 0):
                        break
                    bo_i = np.abs(r_ - np.median(r_)) <= 3.0 * mad
                if math.isfinite(a) and a > 0:
                    # ⛔ **`s` POT ser negatiu, i clavar-lo a zero trenca l'ajust.**
                    # Aquí `s` no és el cel absolut sinó la **desviació** respecte
                    # del cel mitjà, que ja viu dins de `C(r)` pel gauge
                    # `mitjana(s) = 0`. I el cel de la totalitat fa una V amb el
                    # mínim al mig, o sigui que els fotogrames de mig eclipsi en
                    # tenen MENYS que la mitjana i els toca un `s` negatiu.
                    # Mesurat el 24-08-2026: amb el clip posat, els tres
                    # fotogrames de 10,079 s —tots de t = 33 a 60 s, o sigui just
                    # al mínim del cel, i vàlids només més enllà de 1,97 R☉ on el
                    # cel mana— es menjaven la desviació dins de `c` i queien a
                    # **0,947-0,994** quan els seus veïns de 2 s tenien 1,03-1,05.
                    # El resultat era una costura NOVA a 1,97 R☉ de 0,147 % a
                    # 11,8 σ, que el producte sense correcció no tenia.
                    c[i], s[i] = a, b / a
                    ajustat[i] = True
            # --- gauge: el fotograma típic no es mou, i el cel mitjà va a C(r)
            g = math.exp(float(np.median(np.log(np.maximum(c, 1e-12)))))
            # ⛔ El gauge escala c, s I el perfil comú alhora: P = c·(C+s), o
            # sigui que si c baixa un factor g, (C+s) l'ha de pujar SENCER.
            c /= g; s *= g; Cr = Cr * g
            d = float(np.mean(s)); s -= d
            # --- corona comuna
            Q = np.where(val, (P - (c * s)[:, None]) / c[:, None], np.nan)
            Cr_nou = np.nanmedian(Q, axis=0)   # ja hi porta el +d del gauge
            Cr = np.where(np.isfinite(Cr_nou), Cr_nou, Cr)
        # ⛔ Un fotograma que no s'ha pogut ajustar NO es queda a c = 1 en
        # silenci: la transparència és una corba suau en el TEMPS —mesurat, el
        # mateix 1/128 s val 1,0598 a t = 8 s i 0,9779 a t = 89 s—, i el que li
        # toca és el valor d'aquella corba al seu instant, dit al rebut.
        interpolats = []
        if ajustat.sum() >= 4 and (~ajustat).any():
            o_ = np.argsort(t_fg[ajustat])
            tt, cc = t_fg[ajustat][o_], c[ajustat][o_]
            for i in np.flatnonzero(~ajustat):
                c[i] = float(np.interp(t_fg[i], tt, cc)); s[i] = 0.0
                interpolats.append(noms[i])
            # ⛔ i el gauge es torna a aplicar DESPRÉS d'interpolar: si no, la
            # mediana de tots els fotogrames ja no val 1 i l'escala absoluta,
            # que aquest ajust no ha de tocar, es mouria.
            g2 = math.exp(float(np.median(np.log(np.maximum(c, 1e-12)))))
            # ⛔ i aquí el perfil comú TAMBÉ. Sense la línia de `Cr`, el model
            # deixava de quadrar just al final i el residu declarat saltava de
            # 0,17 % a 9 % — un rebut que canta un defecte que no és a la dada
            # sinó al llibre de comptes.
            c /= g2; s *= g2; Cr = Cr * g2
        res, nan_ = [], []
        for i in range(len(noms)):
            m = val[i] & np.isfinite(Cr) & (Cr > 0)
            nan_.append(int(m.sum()))
            if m.sum() >= 20:
                res.append(float(np.median(np.abs(P[i][m] / (c[i] * (Cr[m] + s[i])) - 1.0))))
        if not res:
            res = [float("nan")]
        for i, n in enumerate(noms):
            factors[n][pla] = float(c[i]); cels[n][pla] = float(s[i])
        diag[pla] = {"rms_ln_c": float(np.std(np.log(c))),
                     "anells_usats_min": int(min(nan_)), "anells_usats_max": int(max(nan_)),
                     "n_ajustats": int(ajustat.sum()),
                     "n_interpolats_de_la_corba_temporal": len(interpolats),
                     "interpolats": interpolats,
                     "amplitud_percent": round(100 * float(c.max() - c.min()), 3),
                     "residu_median_percent": round(100 * float(np.median(res)), 4)}
        log(f"{log_pref}{pla}: transparència de {c.min():.4f} a {c.max():.4f} "
            f"(amplitud {100*(c.max()-c.min()):.2f} %)  residu {100*np.median(res):.3f} %  "
            f"{int(ajustat.sum())} ajustats, {len(interpolats)} interpolats")

    return factors, cels, diag


def desacord_entre_esglaons(perfils: dict, noms: list[str], exps_de: dict,
                            cels: dict, factors: dict, aplica_c: bool,
                            pla: str = "G1") -> dict:
    """Desacord entre esglaons d'exposició VEÏNS, per anell i en quocient.

    És l'instrument de la porta H3 sense haver de compondre res: com que la
    corona és la MATEIXA a tots els fotogrames, el quocient de dues medianes
    d'anell del mateix radi la cancel·la i el que queda és el desacord. Amb
    `aplica_c` posat, mesura el que queda **després** de corregir.

    ⛔ **El cel es resta SEMPRE, també a la mesura d'abans.** El cel de la
    totalitat varia un 85 % entre fotogrames i és ADDITIU: si es deixa a dins,
    el quocient entre una exposició curta —on el cel és una engruna— i una de
    llarga —on al radi de solapament el cel ja mana— no mesura cap desacord
    d'esglaó, mesura el cel. Mesurat el 24-08-2026: sense restar-lo aquesta
    funció declarava un desacord del **10 %** allà on la mesura píxel a píxel
    del mateix compost en donava **1,2**. L'estadístic ha de ser **corona menys
    cel**, exactament com a la porta F0, o no és cec al que ha de ser cec.
    """
    per_esglao = {}
    for n in noms:
        e = exps_de[n]
        med = np.asarray(perfils[n][pla][0], float).copy()
        # ⛔ I es resta EN UNITATS DEL FOTOGRAMA, o sigui `c·s` i no `s`. El
        # model és P = c·(C + s): restar `s` a seques deixa un terme `(c−1)·s`
        # que a 7 R☉, on el cel val cent vegades la corona, torna a ser el que
        # mana. L'ordre correcte és restar `c·s` i, si escau, dividir després.
        cc = float(factors[n][pla])
        med = med - float(cels[n][pla]) * cc
        if aplica_c:
            med = med / cc
        per_esglao.setdefault(e, []).append(med)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mitj = {e: np.nanmedian(np.vstack(v), axis=0) for e, v in per_esglao.items()}
    # ⛔ Les VORES del rang vàlid de cada esglaó no serveixen per comparar: a
    # dalt hi ha el genoll de la saturació i a baix el terra de senyal, i just
    # allà és on dos esglaons veïns se solapen. Mesurat el 24-08-2026, sense
    # retallar-les el desacord declarat era del 10 al 12 % quan la mesura
    # píxel a píxel del mateix compost en donava 1,2: el que es mesurava eren
    # les vores, no els esglaons. Es llencen dues cinquenes parts del rang.
    RETALL = 0.20
    for e, v in list(mitj.items()):
        j = np.flatnonzero(np.isfinite(v) & (v > 0))
        if j.size == 0:
            del mitj[e]; continue
        k = int(math.floor(RETALL * j.size))
        bo = np.zeros_like(v, bool)
        bo[j[k:j.size - k] if j.size > 2 * k + 2 else j] = True
        mitj[e] = np.where(bo, v, np.nan)
    exps = sorted(mitj)
    ratios, sigmes = {}, {}
    for a, b in zip(exps[:-1], exps[1:]):
        u, v = mitj[a], mitj[b]
        m = np.isfinite(u) & np.isfinite(v) & (u > 0) & (v > 0)
        # ⛔ i calen prou anells compartits: amb dos, el que es mesura és soroll
        if m.sum() < 8:
            continue
        q = v[m] / u[m] - 1.0
        nom = f"{a:.5g}→{b:.5g}"
        ratios[nom] = float(np.median(q))
        sigmes[nom] = float(np.std(q, ddof=1) / math.sqrt(q.size)) if q.size > 2 else math.nan
    return {"ratios": ratios, "sigmes": sigmes}


def fase_coherencia(args) -> dict:
    """Transparència per fotograma: l'ARREL de les costures de fusió HDR.

    ## Què s'ha mesurat, i per què cap porta no ho havia vist

    El 24-08-2026, component **cada esglaó d'exposició per separat** i comparant
    els veïns **píxel a píxel** als milions de píxels on tots dos són vàlids, el
    desacord surt així:

        1/512 →1/256   +0,519 %      1/64 →1/32   −1,095 %
        1/256 →1/128   −1,105 %      1/32 →1/16   +1,301 %
        1/128 →1/64    +1,275 %      1/16 →1/8    −1,062 %

    ⛔ **El signe ALTERNA.** Això no és soroll ni un error de temps d'obturació:
    vol dir que els esglaons **senars** i els **parells** formen dues famílies
    que no s'ajusten entre elles, cadascuna coherent per dins.

    I la causa surt sola de l'ordre de captura: el programa de la R6 fa
    **dues escales de 2 EV entrellaçades** per mostrejar 1 EV, i cada escala és
    un **pas diferent en el temps**. Els esglaons senars són del pas de
    t = 6,6–11,6 s i els parells del de t = 12,7–16,5 s. Entremig, l'atmosfera
    ha canviat: el cel d'aquell run varia un **85,5 %** durant la totalitat i
    l'extinció hi va amb ell. **La transparència no és la mateixa als dos
    passos**, i el compost n'ajunta els dos.

    La porta F0 fa aquesta mateixa pregunta, però amb medianes d'anell sencer i
    dos a quatre fotogrames per esglaó: el seu terra de precisió és del 2,5 al
    4,3 %, o sigui que **no podia veure un desacord de l'1,2 %**. El codi de la
    fase 2 ja deia des del 23-08 que «la causa arrel va per la coherència entre
    esglaons, no per la rampa»; el que faltava era un instrument prou fi.

    ## L'ajust, i per què no pot inventar-se res

    Model: `P_i(r) = c_i · (C(r) + s_i)` — perfil mesurat del fotograma i =
    transparència × (corona comuna + cel d'aquell instant). **Dos escalars per
    fotograma i per pla**, contra 220 anells de dada. La corona no canvia en
    100 s; el que canvia és l'aire i el cel.

    ⛔ **Un escalar global no pot fabricar estructura**: només puja o baixa el
    fotograma sencer. Aquesta és la salvaguarda que fa l'ajust legítim, i és la
    mateixa raó per la qual ⛔ `k(φ)` lliure entre trens **no** ho és (research/97):
    allà els paràmetres eren per sector angular i s'hi imposava l'acord.

    ⚠️ **L'escala ABSOLUTA no es toca**: el gauge és `mediana(ln c) = 0`, o sigui
    que el fotograma típic queda igual i el que es corregeix és només la
    DISPERSIÓ entre fotogrames. La incertesa absoluta del ±14 % de research/99
    continua exactament on era.
    """
    fg = C.llegeix_manifest()
    centres_finals(fg, getattr(args, "centre", "efemerides"))
    exp_attr = "exp_s" if args.exposicions == "fisiques" else "exp_manifest"
    amb_flat = args.flat == "si"
    log(f"coherència · {len(fg)} fotogrames · exposicions {args.exposicions} · flat {args.flat}")

    perfils, r_c = {}, None
    for k, f in enumerate(fg, 1):
        perfils[f.nom], r_c = perfil_per_fotograma(f, amb_flat, exp_attr)
        if k % 10 == 0 or k == len(fg):
            log(f"  [{k:2d}/{len(fg)}] perfils")

    plans = ["R", "G1", "G2", "B"]
    noms = [f.nom for f in fg]
    t_fg = np.array([f.t_rel_c2 for f in fg])
    factors, cels, diag = ajusta_coherencia(perfils, noms, t_fg, plans)

    # ── el que decideix si això és atmosfera o electrònica: c contra el TEMPS
    ordre = sorted(range(len(fg)), key=lambda i: fg[i].t_rel_c2)
    cg = np.array([0.5 * (factors[f.nom]["G1"] + factors[f.nom]["G2"]) for f in fg])
    exps = sorted({getattr(f, exp_attr) for f in fg})
    idx_e = np.array([exps.index(getattr(f, exp_attr)) for f in fg])
    parell = idx_e % 2 == 0
    dif = float(np.median(cg[parell]) / np.median(cg[~parell]) - 1.0)
    log(f"  esglaons PARELLS contra SENARS: {100*dif:+.3f} %  "
        f"(era el patró que alternava)")

    exps_de = {f.nom: getattr(f, exp_attr) for f in fg}
    d0 = desacord_entre_esglaons(perfils, noms, exps_de, cels, factors, False)
    d1 = desacord_entre_esglaons(perfils, noms, exps_de, cels, factors, True)
    h3_0 = P.porta_h_esglaons_px(d0["ratios"], d0["sigmes"])
    h3_1 = P.porta_h_esglaons_px(d1["ratios"], d1["sigmes"])
    log(f"  H3 (desacord entre esglaons veïns) abans {h3_0['estat']} "
        f"pitjor {100*h3_0['pitjor_desacord']:+.3f} %  →  després {h3_1['estat']} "
        f"pitjor {100*h3_1['pitjor_desacord']:+.3f} %")
    # ⛔ El directori encara pot no existir: aquesta és la PRIMERA escriptura de
    # la fase i `desa()` ve després. Amb un arrel nou per entorn, tres minuts de
    # perfils es perdien aquí mateix (25-08-2026).
    OUT_ARREL.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT_ARREL / f"perfils_coherencia_{args.exposicions}.npz",
                        **{f"{n}|{q}": perfils[n][q][0] for n in noms
                           for q in ("R", "G1", "G2", "B")}, r_centres=r_c)

    res = {"fase": "1b_coherencia", "exposicions": args.exposicions,
           "porta_h3_abans": h3_0, "porta_h3_despres": h3_1,
           "flat_radial": args.flat, "n_fotogrames": len(fg),
           "model": "P_i(r) = c_i · (C(r) + s_i) — dos escalars per fotograma i per pla",
           "gauge": "mediana(ln c) = 0 i mitjana(s) = 0: ⛔ l'escala absoluta NO es toca",
           "rang_r_Rsol": list(COH_R), "n_anells": COH_N,
           "per_pla": diag,
           "diferencia_parells_senars": round(dif, 6),
           "per_fotograma": [
               {"nom": f.nom, "t_rel_c2": f.t_rel_c2,
                "exposicio_s": getattr(f, exp_attr),
                "esglao": int(idx_e[i]),
                "transparencia": {k: round(v, 6) for k, v in factors[f.nom].items()},
                "cel_adu_s": {k: round(v, 4) for k, v in cels[f.nom].items()}}
               for i, f in enumerate(fg)],
           "factors": factors}
    desa(f"coherencia_{args.exposicions}_flat-{args.flat}.json", res)
    log("  → coherència desada")
    return res



def perfil_sony(nom: str, v: dict):
    """Perfil radial per pla d'un fotograma de la Sony, en ADU/s."""
    import sony as SY
    mos, sat = SY.calibra(nom)
    t = float(v["exp_s"])
    sol = (SY.SOL_REF[0] + v["dx"], SY.SOL_REF[1] + v["dy"])
    rs = C.RSOL_ARCSEC / SY.ESCALA          # R☉ en píxels de la Sony
    vores = np.exp(np.linspace(math.log(COH_R[0]), math.log(COH_R[1]), COH_N + 1))
    plans_sat = C.plans(sat.astype(np.uint8))
    out = {}
    for nom_pla, (pla, oy, ox) in C.plans(mos).items():
        rr = C.anells(*pla.shape, (sol[1] - oy) / 2, (sol[0] - ox) / 2) * 2 / rs
        bo = (pla <= SY.SOSTRE) & (plans_sat[nom_pla][0] == 0) & np.isfinite(pla)
        idx_tot = np.digitize(rr.ravel(), vores) - 1
        dins = (idx_tot >= 0) & (idx_tot < COH_N)
        ntot = np.bincount(idx_tot[dins], minlength=COH_N)
        vv = (pla / t).ravel()
        m = bo.ravel() & dins
        idx, vv = idx_tot[m], vv[m]
        o = np.argsort(idx, kind="stable")
        idx_s, v_s = idx[o], vv[o]
        talls = np.searchsorted(idx_s, np.arange(COH_N + 1))
        med = np.full(COH_N, np.nan); npx = np.zeros(COH_N, np.int64)
        for i in range(COH_N):
            a, b = talls[i], talls[i + 1]
            if (b - a) >= 300 and (b - a) >= 0.5 * ntot[i]:
                mm = float(np.median(v_s[a:b]))
                if mm * t >= SENYAL_MIN_ADU:
                    med[i] = mm; npx[i] = b - a
        out[nom_pla] = (med, npx)
    del mos, sat
    return out


def fase_coherencia_sony(args) -> dict:
    """La mateixa coherència de transparència, al tren SONY.

    ⛔ **La malaltia no és d'un cos, és de la fusió HDR amb aire que canvia**, o
    sigui que els dos trens la tenen. La Sony té la seva pròpia costura, mesurada
    el 24-08-2026 a **1,525-1,547 R☉** —i cau DINS de la banda interior que Pere
    va marcar—, de manera que arreglar només la Vixen no hauria netejat la seva
    marca. El que canvia és el joc d'exposicions i els instants; el mètode és
    idèntic i el solucionador, el mateix (`ajusta_coherencia`).
    """
    import sony as SY
    reg = SY.registre()
    admesos = sorted([(n, v) for n, v in reg["fotogrames"].items()
                      if v["estat"] == "ADMES"], key=lambda kv: kv[1]["t"])
    log(f"coherència Sony · {len(admesos)} fotogrames admesos")
    perfils = {}
    for k, (nom, v) in enumerate(admesos, 1):
        perfils[nom] = perfil_sony(nom, v)
        if k % 5 == 0 or k == len(admesos):
            log(f"  [{k:2d}/{len(admesos)}] perfils")
    noms = [n for n, _ in admesos]
    t_fg = np.array([float(v["t"]) for _, v in admesos])
    factors, cels, diag = ajusta_coherencia(perfils, noms, t_fg,
                                            ["R", "G1", "G2", "B"])
    exps_de = {n: float(v["exp_s"]) for n, v in admesos}
    d0 = desacord_entre_esglaons(perfils, noms, exps_de, cels, factors, False)
    d1 = desacord_entre_esglaons(perfils, noms, exps_de, cels, factors, True)
    h3_0 = P.porta_h_esglaons_px(d0["ratios"], d0["sigmes"])
    h3_1 = P.porta_h_esglaons_px(d1["ratios"], d1["sigmes"])
    log(f"  H3 (desacord entre esglaons veïns) abans {h3_0['estat']} "
        f"pitjor {100*h3_0['pitjor_desacord']:+.3f} %  →  després {h3_1['estat']} "
        f"pitjor {100*h3_1['pitjor_desacord']:+.3f} %")

    res = {"fase": "1b_coherencia_sony", "tren": "sony_a7r3a_300gm",
           "porta_h3_abans": h3_0, "porta_h3_despres": h3_1,
           "n_fotogrames": len(admesos),
           "model": "P_i(r) = c_i · (C(r) + s_i) — dos escalars per fotograma i per pla",
           "gauge": "mediana(ln c) = 0: ⛔ l'escala absoluta NO es toca",
           "rang_r_Rsol": list(COH_R), "n_anells": COH_N, "per_pla": diag,
           "per_fotograma": [
               {"nom": n, "t_rel_c2": float(v["t"]), "exposicio_s": float(v["exp_s"]),
                "transparencia": {k2: round(x, 6) for k2, x in factors[n].items()},
                "cel_adu_s": {k2: round(x, 4) for k2, x in cels[n].items()}}
               for n, v in admesos],
           "factors": factors}
    desa("coherencia_sony.json", res)
    log("  → coherència Sony desada")
    return res


def fase2(args) -> dict:
    fg = C.llegeix_manifest()
    # ⛔ MEITATS A/B, per a la prova d'estructura real: es reparteixen els
    # fotogrames de manera ALTERNADA DINS DE CADA ESGLAÓ d'exposició, de manera
    # que les dues meitats tenen el mateix joc d'exposicions i, per tant, les
    # mateixes fronteres de fusió. El que hi ha de comú entre les dues és senyal;
    # el que no, soroll. És l'única manera de decidir si un patró és corona.
    # ⛔ FAMÍLIA D'ESGLAONS. La R6 entrellaça dues escales de 2 EV que són dos
    # passos diferents en el temps; compondre'n només una dona **la meitat de
    # fronteres de fusió i cap desacord entre passos**, al preu d'un 30 % de
    # senyal/soroll. És atacar l'arrel en lloc de corregir el símptoma.
    _fam = os.environ.get("PILOT_FAMILIA")
    if _fam in ("senars", "parells"):
        _e = sorted({f.exp_s for f in fg})
        _vol = {e for i, e in enumerate(_e)
                if (i % 2 == 1) == (_fam == "senars") or i in (0, len(_e) - 1)}
        fg = [f for f in fg if f.exp_s in _vol]
        log(f"  ⚠️ FAMÍLIA {_fam}: {len(fg)} fotogrames de {len(_vol)} esglaons")
    # ⛔ APRIMAT: treu N fotogrames repartits per TOTS els esglaons. És el
    # control aparellat en senyal/soroll que la família d'esglaons necessita:
    # sense ell, el jutge creuat **confon perdre S/N amb perdre corona**
    # —mesurat el 25-08-2026, les meitats A/B, que no treuen gens de corona,
    # cauen −0,0169 i −0,0236, cinc vegades més que la família senar—.
    _apr = int(os.environ.get("PILOT_APRIMA", "0"))
    if _apr > 0:
        _per = {}
        for f in sorted(fg, key=lambda x: (x.exp_s, x.t_rel_c2)):
            _per.setdefault(f.exp_s, []).append(f)
        _fora = []
        _ordre = sorted(_per, key=lambda e: -len(_per[e]))
        while len(_fora) < _apr:
            _mou = False
            for e in _ordre:
                if len(_per[e]) > 1 and len(_fora) < _apr:
                    _fora.append(_per[e].pop()); _mou = True
            if not _mou:
                break
        fg = sorted([f for l in _per.values() for f in l], key=lambda x: x.t_rel_c2)
        log(f"  ⚠️ APRIMAT: fora {len(_fora)} fotogrames, queden {len(fg)} "
            f"amb els {len(_per)} esglaons sencers")
    _mei = os.environ.get("PILOT_MEITAT")
    if _mei in ("A", "B"):
        _per_exp = {}
        for _f in sorted(fg, key=lambda x: (x.exp_s, x.t_rel_c2)):
            _per_exp.setdefault(_f.exp_s, []).append(_f)
        _tria = []
        for _e, _l in _per_exp.items():
            _tria += _l[0::2] if _mei == "A" else _l[1::2]
        fg = sorted(_tria, key=lambda x: x.t_rel_c2)
        log(f"  ⚠️ MEITAT {_mei}: {len(fg)} fotogrames de {len(_per_exp)} esglaons")
    model = centres_finals(fg, getattr(args, "centre", "efemerides"))
    exp_attr = "exp_s" if args.exposicions == "fisiques" else "exp_manifest"
    amb_flat = args.flat == "si"
    etiqueta = f"{args.exposicions}_flat-{args.flat}"
    if _fam in ("senars", "parells"):
        etiqueta += f"_{_fam}"
    if _apr > 0:
        etiqueta += f"_aprima{_apr}"
    if _mei in ("A", "B"):
        etiqueta += f"_meitat{_mei}"
    # ⛔ La coherència de transparència per fotograma. Sense això el compost
    # ajunta DUES escales entrellaçades que discrepen un 1,2 % —els esglaons
    # senars són d'un pas en el temps i els parells d'un altre—, i cada frontera
    # de fusió entre les dues famílies deixa la vall que Pere va marcar el
    # 24-08-2026. Vegeu `fase_coherencia`.
    coh = None
    if getattr(args, "coherencia", None):
        _cj = json.loads(Path(args.coherencia).read_text())
        coh = _cj["factors"]
        etiqueta += "_coh"
        log(f"  coherència per fotograma: {len(coh)} fotogrames, "
            f"amplitud {_cj['per_pla']['G1']['amplitud_percent']} % al verd")
    if getattr(args, "centre", "efemerides") != "efemerides":
        etiqueta += f"_centre-{args.centre}"
    if getattr(args, "cel", "anell") != "anell":
        etiqueta += f"_cel-{args.cel}"
    log(f"fase 2 · LDIC · exposicions {args.exposicions} · flat {args.flat}")

    mos0, _ = C.calibra(fg[0], amb_flat=amb_flat)
    H, W = mos0.shape
    cy_out, cx_out = H / 2.0, W / 2.0
    del mos0
    ry = (np.arange(H) - cy_out)[:, None]
    rx = (np.arange(W) - cx_out)[None, :]

    canals = ["R", "G", "B"]
    num = {c: np.zeros((H, W), np.float64) for c in canals}
    den = {c: np.zeros((H, W), np.float64) for c in canals}
    ncon = {c: np.zeros((H, W), np.uint16) for c in canals}

    # ⛔ DIAGNÒSTIC de coherència entre esglaons, píxel a píxel. La porta F0 fa
    # la mateixa pregunta amb medianes d'anell sencer i té un terra de precisió
    # del 2,5 al 4,3 %; les costures que Pere va marcar valen 0,2 %, o sigui
    # DEU vegades per sota. L'única manera de veure-les és compondre cada esglaó
    # per separat i comparar-los píxel a píxel a la zona on tots dos són vàlids.
    # Es desa al disc com a memmap perquè són 15 esglaons × 2 × 129 MiB.
    _pe = os.environ.get("PILOT_ESGLAONS_SEPARATS")
    per_esglao = None
    if _pe:
        _ped = Path(_pe)
        _ped.mkdir(parents=True, exist_ok=True)
        per_esglao = {"dir": _ped, "num": {}, "den": {}}
        log(f"  ⚠️ diagnòstic: esglaons separats a {_ped}")
    wmax = {c: np.zeros((H, W), np.float32) for c in canals}
    emax = {c: np.full((H, W), -1, np.int8) for c in canals}
    exps = sorted({getattr(f, exp_attr) for f in fg})

    # mostres per a la porta F: píxels de sortida triats abans de compondre
    rng = np.random.default_rng(20260823)
    n_mostres = 400
    smp_y = rng.integers(int(0.15 * H), int(0.85 * H), n_mostres)
    smp_x = rng.integers(int(0.15 * W), int(0.85 * W), n_mostres)
    mostres = [{"id": f"G_{int(a)}_{int(b)}", "y": int(a), "x": int(b),
                "canal": "G", "pesos": [], "valors": []}
               for a, b in zip(smp_y, smp_x)]

    usa_model = getattr(args, "cel", "anell") == "model"
    if usa_model:
        # ⛔ Amb el model 2-D no s'ha de fer també l'anivellament per anell:
        # el model ja porta la variació temporal I la forma espacial, i els dos
        # junts restarien el cel dues vegades.
        S_cel, forma = carrega_model_cel()
        nivells = {f.nom: np.zeros(4) for f in fg}
        log("  cel: model 2-D per fotograma (l'anivellament per anell queda fora)")
    else:
        nivells = anivella_fons(fg, exp_attr)

    for k, f in enumerate(fg, 1):
        mos, sat = C.calibra(f, amb_flat=amb_flat)
        t = getattr(f, exp_attr)
        # ⛔ El cel es resta del VALOR, però la saturació es jutja amb el valor
        # CRU: un píxel que és al pou hi és tant si el cel hi és com si no, i
        # restar-li el cel abans del llindar el torna admissible. Provat: sense
        # aquesta separació el compost a 1,18 R☉ perdia el 94,7 % —entraven
        # píxels saturats de les exposicions llargues— i el «cel restat» valia
        # trenta mil ADU/s on el model en diu tres-cents seixanta-nou.
        # ⛔ I la coherència tampoc no hi entra: un píxel és al pou pels comptes
        # que hi van caure, no pels que li quedin després de corregir l'aire.
        mos_brut = mos if not (usa_model or coh) else mos.copy()
        if coh is not None:
            mos = C.aplica_coherencia(mos, coh[f.nom])
        if usa_model:
            mos = mos - cel_del_fotograma(f, forma, S_cel, mos.shape)
        rn = C.RN_CURT if t < C.LLINDAR_MODE_S else C.RN_LLARG
        ie = exps.index(t)
        sx, sy = f.sol_usat
        # màscara lunar SUAU: la Lluna es mou 28,7 px respecte del Sol al llarg
        # de la totalitat, i amb un tall dur cada píxel d'un anell de 30 px al
        # voltant del limbe es compondria d'un subconjunt diferent de fotogrames.
        # ⛔ I l'earthshine no es barreja amb la corona: el disc no hi aporta.
        dlx = f.lluna_x - sx
        dly = f.lluna_y - sy
        d_ll = np.hypot(rx - dlx, ry - dly)
        # ⛔ smoothstep, pel mateix motiu que el `taper` de saturació: un clip
        # lineal deixa DOS colzes C⁰ —a d_ll = 464 i 478 px, o sigui 1,053 i
        # 1,085 R☉ de cada fotograma, i la deriva Lluna-Sol de ±14 px els
        # esbarria fins a 1,02-1,117 R☉—. Avui no mossega el producte declarat,
        # que talla a 1,12 R☉, però viu dins del llenç i de les previsualitzacions
        # i és el primer que apareix si algú abaixa el límit interior.
        pes_lluna = C.rampa((d_ll - (C.R_LLUNA_PX + 4)) / 14.0)
        desp = dict(zip(["R", "G1", "G2", "B"], nivells[f.nom]))

        plans_bruts = C.plans(mos_brut)
        for nom_pla, (pla, oy, ox) in C.plans(mos).items():
            pla = pla - desp[nom_pla]
            # ⛔ El cel es resta del VALOR, però la SATURACIÓ i la VARIÀNCIA es
            # jutgen amb el valor CRU. Un píxel que és al pou hi és tant si el
            # cel hi és com si no, i restar-li el cel abans del llindar el torna
            # admissible. Mesurat: sense aquesta separació, a 1,15–1,25 R☉ el
            # fotograma de 10,08 s —saturat allà— passava a ser el dominant, el
            # denominador es multiplicava per 61 i el compost queia un 94 %.
            # I la variància del soroll la fixa el senyal que hi va caure al
            # sensor, no el que en queda després de restar-ne el cel.
            brut = plans_bruts[nom_pla][0]
            spl = C.plans(sat.astype(np.uint8))[nom_pla][0] > 0
            c = "G" if nom_pla.startswith("G") else nom_pla
            # ⛔ El PES es pot calcular amb el senyal SUAVITZAT en lloc del valor
            # sorollós de cada píxel. Amb el valor cru, el pes anticorrelaciona
            # amb el soroll —un píxel que fluctua amunt té més variància i menys
            # taper, o sigui menys pes— i la mitjana ponderada surt esbiaixada
            # cap avall. El biaix és petit arreu, però **canvia de pressa allà on
            # canvia la barreja de fotogrames**, o sigui a les fronteres de fusió.
            # ⚠️ La saturació de veritat es continua jutjant amb el valor CRU.
            brut_pes = (gaussian_filter(brut, PES_SUAU) if PES_SUAU > 0 else brut)
            s = np.maximum(brut_pes, 0.0)
            var = s / C.GUANY[nom_pla] + rn * rn
            w = (t * t) / var
            # ⛔ Rampa SMOOTHSTEP i no lineal. Una rampa lineal arriba a zero amb
            # pendent NO nul: el pes d'una exposició desapareix amb un colze C⁰, i
            # el passa-alt de la fase 3 el converteix en una vall fosca de 0,07 a
            # 0,14 % de contrast i ~15 px d'ample que segueix una isofota —el que
            # Pere va marcar el 24-08-2026 com a «artefacte subtil»—. La família
            # en té una per esglaó d'exposició que se satura; la més externa és la
            # dels tres fotogrames de 10,079 s, a 1,59-2,38 R☉.
            # ⚠️ Això NO és la cura de fons: l'amplitud del colze és proporcional
            # al DESACORD entre esglaons d'exposició (porta F0). La smoothstep
            # només impedeix que aquell desacord es concentri en una línia i el
            # reparteix per tota la rampa. La causa arrel va per la coherència
            # entre esglaons, no per la rampa.
            taper = C.rampa((C.SOSTRE - brut_pes) / (C.RAMPA_SOSTRE * C.SOSTRE))
            w = (w * taper).astype(np.float32)
            w[brut > C.SOSTRE] = 0.0
            w[spl] = 0.0
            val = (pla / t).astype(np.float32)

            base_y = oy - (sy_ := (sy - cy_out))
            base_x = ox - (sx_ := (sx - cx_out))
            ky, wy = pesos_gota(base_y % 1.0)
            kx, wx = pesos_gota(base_x % 1.0)
            iy0, ix0 = math.floor(base_y), math.floor(base_x)
            h, wd = pla.shape
            for a_i, wa in enumerate(wy):
                if wa <= 0:
                    continue
                Y = iy0 + ky + a_i
                for b_i, wb in enumerate(wx):
                    if wb <= 0:
                        continue
                    X = ix0 + kx + b_i
                    py, sty = Y % 2, Y // 2
                    px, stx = X % 2, X // 2
                    vy = slice(max(sty, 0), min(sty + h, (H - py + 1) // 2))
                    vx = slice(max(stx, 0), min(stx + wd, (W - px + 1) // 2))
                    if vy.stop <= vy.start or vx.stop <= vx.start:
                        continue
                    ay = slice(vy.start - sty, vy.stop - sty)
                    ax = slice(vx.start - stx, vx.stop - stx)
                    ml = pes_lluna[py::2, px::2][vy, vx]
                    ww = w[ay, ax] * np.float32(wa * wb) * ml
                    vv = val[ay, ax]
                    num[c][py::2, px::2][vy, vx] += ww * vv
                    den[c][py::2, px::2][vy, vx] += ww
                    if per_esglao is not None and c == "G":
                        if ie not in per_esglao["num"]:
                            for _q in ("num", "den"):
                                per_esglao[_q][ie] = np.lib.format.open_memmap(
                                    per_esglao["dir"] / f"{_q}_{ie:02d}.npy", mode="w+",
                                    dtype=np.float32, shape=(H, W))
                        per_esglao["num"][ie][py::2, px::2][vy, vx] += (ww * vv).astype(np.float32)
                        per_esglao["den"][ie][py::2, px::2][vy, vx] += ww.astype(np.float32)
                    ncon[c][py::2, px::2][vy, vx] += (ww > 0)
                    dmax = wmax[c][py::2, px::2]
                    de = emax[c][py::2, px::2]
                    mill = ww > dmax[vy, vx]
                    sub = dmax[vy, vx]; sub[mill] = ww[mill]; dmax[vy, vx] = sub
                    sube = de[vy, vx]; sube[mill] = ie; de[vy, vx] = sube
                    if c == "G":
                        for m in mostres:
                            if m["y"] % 2 != py or m["x"] % 2 != px:
                                continue
                            jy, jx = m["y"] // 2 - vy.start, m["x"] // 2 - vx.start
                            if 0 <= jy < ww.shape[0] and 0 <= jx < ww.shape[1]:
                                m["pesos"].append(float(ww[jy, jx]))
                                m["valors"].append(float(vv[jy, jx]))
        if k % 5 == 0 or k == len(fg):
            log(f"  [{k:2d}/{len(fg)}] {f.nom} {t:<12.9g} sol=({sx:.1f},{sy:.1f}) "
                f"{f.origen_centre}")
        del mos, sat, pes_lluna

    if per_esglao is not None:
        for _q in ("num", "den"):
            for _k in per_esglao[_q]:
                per_esglao[_q][_k].flush()
        C.desa_json(per_esglao["dir"] / "exposicions.json",
                    {"exposicions": {str(i): e for i, e in enumerate(exps)}})
        log(f"  ⚠️ diagnòstic: {len(per_esglao['num'])} esglaons desats per separat")

    hdr = np.full((H, W, 3), np.nan, np.float32)
    varm = np.full((H, W, 3), np.nan, np.float32)
    cob = np.zeros((H, W, 3), np.uint16)
    dom = np.zeros((H, W, 3), np.int8)
    for i, c in enumerate(canals):
        d = den[c]; bo = d > 0
        hdr[..., i] = np.where(bo, num[c] / np.maximum(d, 1e-30), np.nan)
        varm[..., i] = np.where(bo, 1.0 / np.maximum(d, 1e-30), np.nan)
        cob[..., i] = ncon[c]
        dom[..., i] = emax[c]

    dst = OUT_ARREL / etiqueta
    dst.mkdir(parents=True, exist_ok=True)
    np.save(dst / "HDR_adu_s.npy", hdr)
    np.save(dst / "VAR_adu_s2.npy", varm)
    np.save(dst / "COBERTURA.npy", cob)
    np.save(dst / "ESGLAO_DOMINANT.npy", dom)
    np.save(dst / "N_verd.npy", num["G"].astype(np.float32))
    np.save(dst / "D_verd.npy", den["G"].astype(np.float32))
    log(f"  compost desat a {dst}")

    porta_f = P.porta_f_mescla([{"id": m["id"], "pesos": m["pesos"], "valors": m["valors"],
                                 "compost": float(hdr[m["y"], m["x"], 1])}
                                for m in mostres if m["pesos"]])
    log(f"  F (compost ≡ mescla) → {porta_f['estat']}  "
        f"desviació {porta_f.get('desviacio_relativa_maxima')}")

    res = {"fase": "2_composicio_ldic", "etiqueta": etiqueta,
           "exposicions": args.exposicions, "flat_radial": args.flat,
           "arquitectura": "g = Σ(w·J)/Σw amb w = t²/(S/g + RN²), una sola suma",
           "reixa": {"h": H, "w": W, "sol": [cx_out, cy_out],
                     "escala_arcsec_px": C.ESCALA, "gir_aplicat": "cap (nord amunt al final)"},
           "unitats": "ADU/s; a B/B☉ multiplicant per FB",
           "FB_B_per_Bsol_per_adu_s": C.FB,
           "pixfrac_px_de_sortida": PIXFRAC,
           "coherencia_per_fotograma": (None if coh is None else
                                        {"fitxer": str(args.coherencia),
                                         "n_fotogrames": len(coh)}),
           "n_fotogrames": len(fg), "exposicions_uniques": len(exps),
           "model_de_registre": model["coeficients"],
           "porta_f": porta_f,
           "fitxers": {p.name: {"bytes": p.stat().st_size, "sha256": C.sha256(p)}
                       for p in sorted(dst.glob("*.npy"))}}
    desa(f"fase2_{etiqueta}.json", res)
    return res


# ================================================================ portes E/G
def perfil_radial(hdr: np.ndarray, canal: int, cy: float, cx: float,
                  r0: float, r1: float, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    H, W = hdr.shape[:2]
    rr = C.anells(H, W, cy, cx) / C.R_SOL_PX
    v = hdr[..., canal]
    vores = np.linspace(r0, r1, n + 1)
    idx = np.digitize(rr.ravel(), vores) - 1
    val = v.ravel()
    bo = (idx >= 0) & (idx < n) & np.isfinite(val)
    perfil = np.full(n, np.nan); pes = np.zeros(n)
    o = np.argsort(idx[bo]); ii = idx[bo][o]; vv = val[bo][o]
    talls = np.searchsorted(ii, np.arange(n + 1))
    for a in range(n):
        seg = vv[talls[a]:talls[a + 1]]
        if seg.size:
            perfil[a] = np.median(seg); pes[a] = seg.size
    return 0.5 * (vores[:-1] + vores[1:]), perfil, pes


def radis_de_transicio(dom: np.ndarray, canal: int, cy: float, cx: float,
                       r0: float, r1: float, n: int = 400) -> list[float]:
    """Radis on canvia l'esglaó d'exposició que mana. És on viuen els graons."""
    H, W = dom.shape[:2]
    rr = C.anells(H, W, cy, cx) / C.R_SOL_PX
    d = dom[..., canal]
    vores = np.linspace(r0, r1, n + 1)
    idx = np.digitize(rr.ravel(), vores) - 1
    dv = d.ravel()
    bo = (idx >= 0) & (idx < n) & (dv >= 0)
    o = np.argsort(idx[bo]); ii = idx[bo][o]; vv = dv[bo][o]
    talls = np.searchsorted(ii, np.arange(n + 1))
    md = np.full(n, -1.0)
    for a in range(n):
        seg = vv[talls[a]:talls[a + 1]]
        if seg.size:
            md[a] = np.median(seg)
    cen = 0.5 * (vores[:-1] + vores[1:])
    out = []
    for a in range(1, n):
        if md[a] >= 0 and md[a - 1] >= 0 and md[a] != md[a - 1]:
            out.append(float(cen[a]))
    # agrupa transicions consecutives
    agr, ult = [], -1e9
    for r in out:
        if r - ult > 0.05:
            agr.append(r)
        ult = r
    return agr


def fase_portes(args) -> dict:
    dst = OUT_ARREL / args.etiqueta
    hdr = np.load(dst / "HDR_adu_s.npy")
    dom = np.load(dst / "ESGLAO_DOMINANT.npy")
    H, W = hdr.shape[:2]
    cy, cx = H / 2.0, W / 2.0
    log(f"portes sobre {args.etiqueta}")

    # ⛔ El domini NO pot començar a 1,05 R☉. La màscara lunar val zero fins a
    # `R_LLUNA + 4` i puja en 14 px, o sigui fins a 478 px = 1,085 R☉; i la
    # Lluna es mou ±14 px respecte del Sol al llarg de la totalitat, de manera
    # que **en radi solar la vora de la màscara queda escampada fins a 1,117
    # R☉**. Un perfil que hi comenci mesura la màscara, no la corona: amb el
    # domini a 1,05 la porta E2 cantava un «graó» de −2,8 % a 1,066 R☉ que és
    # exactament això.
    R_INICI = 1.15
    r, perfil, pes = perfil_radial(hdr, 1, cy, cx, R_INICI, 5.2, 120)
    gE = P.porta_e_monotonia(r, perfil)
    trans = radis_de_transicio(dom, 1, cy, cx, R_INICI, 5.2)
    r2, perfil2, _ = perfil_radial(hdr, 1, cy, cx, R_INICI, 5.2, 400)
    gE2 = P.porta_e_graons_de_fusio(r2, perfil2, trans)
    gG = P.porta_g_envolupant(r, perfil, pes)
    gR = P.porta_rectangle(hdr[..., 1])
    log(f"  E  monotonia         → {gE['estat']}  puja màx {gE.get('pujada_maxima_relativa')}")
    log(f"  E2 graons de fusió   → {gE2['estat']}  pitjor {gE2.get('pitjor_grao')} "
        f"a {gE2.get('pitjor_radi_rsol')} R☉  ({len(trans)} transicions)")
    log(f"  G  envolupant        → {gG['estat']}  excés {gG.get('exces_maxim')}")
    log(f"  rectangle            → {gR['estat']}")

    res = {"etiqueta": args.etiqueta, "domini_rsol": [R_INICI, 5.2],
           "per_que_no_comenca_a_1_05": ("la màscara lunar arriba a 1,085 R☉ i la Lluna es mou "
                                         "±14 px respecte del Sol: en radi solar la seva vora "
                                         "queda escampada fins a 1,117 R☉"),
           "radis_de_transicio_rsol": [round(x, 4) for x in trans],
           "porta_e_monotonia": gE, "porta_e2_graons_de_fusio": gE2,
           "porta_g_envolupant": gG, "porta_rectangle": gR,
           "perfil": {"radis_rsol": [round(float(v), 5) for v in r],
                      "verd_adu_s": [None if not math.isfinite(v) else float(f"{v:.6g}")
                                     for v in perfil]}}
    desa(f"portes_{args.etiqueta}.json", res)
    return res


# ================================================================ model de cel
BIN_CEL = 16          # binning per estimar el cel; el cel és llis, el soroll no
EXP_MIN_CEL = 0.125   # per sota, la mesura del cel és soroll dividit per t


def _binna(a: np.ndarray, b: int) -> np.ndarray:
    h, w = a.shape[0] // b * b, a.shape[1] // b * b
    return a[:h, :w].reshape(h // b, b, w // b, b).mean(axis=(1, 3))


def fase_cel(args) -> dict:
    """Model de cel 2-D per fotograma, mesurat per la seva signatura TEMPORAL.

    ⛔ `anivella_fons` **no treu el cel**: l'iguala entre fotogrames amb un sol
    número per pla. Si el cel té forma —i en té: creix cap enfora perquè mires
    més lluny del centre de l'ombra— aquell número deixa un residu que és
    diferent a cada radi i a cada instant, i és exactament el que fa fallar la
    porta F0 a 3,2–4,2 R☉.

    Aquí es mesura de veritat, i **sense assumir res sobre la corona**: el cel
    varia un 29,9 % al llarg de la totalitat i la corona no varia gens. Per a
    cada píxel (binnat, perquè el cel és llis) s'ajusta

        taxa_f(p) = C(p) + S(p) · f(t_f)

    on `f` és la forma temporal treta de l'anell exterior. `S·f(t)` és el cel
    variable de cada fotograma i és el que es resta. ⚠️ La part CONSTANT del cel
    queda dins `C` i aquesta via no la veu: el que se'n treu és una fita
    inferior del cel i `C` una fita superior de la corona.
    """
    fg = C.llegeix_manifest()
    centres_finals(fg, "efemerides")
    llargs = [f for f in fg if f.exp_s >= EXP_MIN_CEL]
    log(f"fase cel · {len(llargs)} fotogrames de {EXP_MIN_CEL} s o més, binning {BIN_CEL}")

    # ⛔ El cel s'ha de mesurar PER PLA DE BAYER. Els quatre plans no veuen el
    # mateix cel —el cel de la totalitat és llum solar dispersada i és molt més
    # blava que la corona—, i restar-los a tots la mitjana del mosaic deixa un
    # residu de color enorme: provat, el compost sortia **verd** de 2 R☉ enfora.
    PLANS = ["R", "G1", "G2", "B"]
    mapes = {n: [] for n in PLANS}
    for k, f in enumerate(llargs, 1):
        mos, sat = C.calibra(f)
        alt = (mos > C.SOSTRE) | sat
        r = np.where(alt, np.nan, mos / f.exp_s).astype(np.float32)
        for n, (pla, oy, ox) in C.plans(r).items():
            mapes[n].append(_binna(np.nan_to_num(pla, nan=0.0), BIN_CEL // 2))
        if k % 6 == 0 or k == len(llargs):
            log(f"  [{k:2d}/{len(llargs)}] {f.nom}")
        del mos, sat, r
    Mp = {n: np.stack(v) for n, v in mapes.items()}
    del mapes
    Mx = Mp["G1"]
    t = np.array([f.t_rel_c2 for f in llargs])

    # forma temporal: de l'anell exterior, on la corona és el mínim possible
    hb, wb = Mx.shape[1:]
    sy, sx = fg[0].sol_usat[1] / BIN_CEL, fg[0].sol_usat[0] / BIN_CEL
    rb = C.anells(hb, wb, sy, sx) * BIN_CEL / C.R_SOL_PX
    ext = (rb > 4.4) & (rb < 5.1)
    ft = np.array([np.median(m[ext]) for m in Mx])
    fn = ft / np.median(ft)
    log(f"  forma temporal del cel: de {fn.min():.4f} a {fn.max():.4f} "
        f"({100 * (fn.max() - fn.min()):.1f} % de recorregut), mínim a t={t[np.argmin(fn)]:.1f} s")

    A = np.vstack([np.ones_like(fn), fn]).T
    Smaps = {}
    for n in PLANS:
        sol, *_ = np.linalg.lstsq(A, Mp[n].reshape(len(fn), -1), rcond=None)
        Smaps[n] = sol[1].reshape(hb, wb)
        if n == "G1":
            Cmap = sol[0].reshape(hb, wb)
            res = Mp[n] - np.einsum("ij,jkl->ikl", A, sol.reshape(2, hb, wb))
            rms = np.sqrt(np.nanmean(res ** 2, axis=0))
            del res
    Smap = Smaps["G1"]
    del Mx

    # ⛔⛔ El model de cel NO pot ser el `S` cru. A dins de 2 R☉ la corona també
    # varia entre fotogrames —per la rampa de saturació i pels sistemàtics de
    # cada esglaó—, l'ajust li ho atribueix al terme variable, i restar-lo
    # s'emporta la corona: provat, el perfil sortia **negatiu de 1,18 a 1,99
    # R☉** i a 1,45 R☉ es restava tres vegades el que hi havia.
    #
    # El cel és una superfície LLISA i no té cap motiu per tenir estructura
    # justament al voltant del Sol. Per tant `S` s'ajusta a una quàdrica 2-D
    # **només on la corona és petita** (r > `R_MIN_AJUST_CEL`) i s'avalua a tot
    # el camp. Això també compleix la norma del rectangle: el model existeix a
    # tot arreu, no s'atura a cap circumferència.
    R_MIN_AJUST_CEL = 2.5
    yb, xb = np.mgrid[0:hb, 0:wb]
    u = (xb - sx) / wb
    w_ = (yb - sy) / hb
    base = [np.ones_like(u), u, w_, u * u, u * w_, w_ * w_]
    k = np.isfinite(Smap) & (rb > R_MIN_AJUST_CEL)
    Mq = np.column_stack([b[k].ravel() for b in base])
    cq, *_ = np.linalg.lstsq(Mq, Smap[k].ravel(), rcond=None)
    Ss = sum(c * b for c, b in zip(cq, base)).astype(np.float32)
    resq = Smap[k] - Ss[k]
    log(f"  quàdrica de cel (verd) a r > {R_MIN_AJUST_CEL} R☉ ({int(k.sum())} cel·les): "
        f"residu {100 * np.std(resq) / np.median(Smap[k]):.2f} %")

    # ⛔ El COLOR del cel NO es pot treure de l'ajust temporal de cada pla.
    # `f(t)` es mesura al verd, i si el cel canvia de color amb el temps —i en
    # canvia, la vora de l'ombra no és neutra— l'ajust del blau surt esbiaixat
    # amb una palanca d'1/0,30 = 3,3×. Provat: el blau sortia **negatiu de
    # 3,2 R☉ enfora** i el verd a 4,64.
    #
    # Es mesura on el cel MANA: a l'anell exterior, on n'és el 96 % del senyal.
    # Allà el quocient entre plans és el color del cel, i el poc de corona que
    # hi queda és de color solar i amb un pes del 4 %.
    # ⛔⛔ I TAMPOC de la mediana per fotograma dels mapes per pla. Mesurat el
    # 24-08-2026, aquella via dona **B/G = 0,6330** a 4,4-5,1 R☉ mentre que el
    # compost, al MATEIX anell i al mateix espai, en dona **0,4662**: el vermell
    # hi coincideix al 0,8 % i el blau hi difereix un **36 %**. I el bo és el del
    # compost, perquè convergeix: B/G val 0,4481 a 3,0-3,6 R☉, 0,4662 a 4,4-5,1,
    # 0,4706 a 5,5-6,5 i 0,4718 a 6,5-7,5, una asímptota neta.
    #
    # ⛔ Conseqüència del número dolent, i no és petita: amb el blau sobre-restat
    # un 36 %, el producte `cel-model` surt amb el **19,9 % dels píxels de blau
    # negatius a 3,0-3,6 R☉ i el 64,5 % a 4,4-5,1**, i allà el seu R/G val −0,70.
    # `research/99` atribuïa aquell fracàs al fet que restar el cel deixi un
    # producte sorollós; la causa era aquest color.
    #
    # La regla que se'n treu: **el color es mesura on es restarà i amb el mateix
    # pes amb què es restarà**, o sigui al compost. Si el compost encara no hi és
    # es cau al camí antic, però dient-ho.
    ext_b = (rb > 4.4) & (rb < 5.1)
    colors = None
    for etiq in ("fisiques_flat-si", "manifest_flat-si", "fisiques_flat-no"):
        f_hdr = OUT_ARREL / etiq / "HDR_adu_s.npy"
        if not f_hdr.exists():
            continue
        hdrc = np.load(f_hdr, mmap_mode="r")
        Hh, Wh = hdrc.shape[:2]
        yh = np.arange(Hh, dtype=np.float32)[:, None] - Hh / 2
        xh = np.arange(Wh, dtype=np.float32)[None, :] - Wh / 2
        rh = np.hypot(yh, xh) / C.R_SOL_PX
        mh = (rh >= 6.5) & (rh < 7.5)          # l'asímptota: el cel hi és >98 %
        if mh.sum() < 20000:
            mh = (rh >= 4.4) & (rh < 5.1)
        vv = [float(np.nanmedian(np.where(mh, np.asarray(hdrc[..., i], np.float32), np.nan)))
              for i in range(3)]
        if np.isfinite(vv).all() and vv[1] > 0:
            colors = {"R": vv[0] / vv[1], "G1": 1.0, "G2": 1.0, "B": vv[2] / vv[1]}
            log(f"  color del cel MESURAT AL COMPOST ({etiq}) a l'asímptota: "
                f"R/G {colors['R']:.4f}  B/G {colors['B']:.4f}")
        break
    if colors is None:
        ref_g = float(np.median(np.median(Mp["G1"], axis=0)[ext_b]))
        colors = {n: float(np.median(np.median(Mp[n], axis=0)[ext_b]) / ref_g) for n in PLANS}
        log("  ⚠️ sense compost: color del cel per la via antiga (mediana per "
            "fotograma), que al blau surt un 36 % massa alt")
    Sq = {n: (Ss * colors[n]).astype(np.float32) for n in PLANS}
    log("  color del cel a 4,4–5,1 R☉ (verd = 1): "
        + "  ".join(f"{n}={colors[n]:.4f}" for n in PLANS))
    bo = np.isfinite(rb) & (rb > 1.9)
    log(f"  cel S: mediana {np.median(Ss[bo]):.2f} ADU/s, "
        f"de {np.percentile(Ss[bo], 5):.2f} a {np.percentile(Ss[bo], 95):.2f} "
        f"(residu de l'ajust {100 * np.median(rms[bo]) / max(np.median(Ss[bo]), 1e-9):.2f} %)")

    dst = OUT_ARREL / "model_de_cel"
    dst.mkdir(parents=True, exist_ok=True)
    np.savez(dst / "S_cel_per_pla.npz", **{n: Sq[n].astype(np.float32) for n in PLANS})
    np.save(dst / "S_cel_adu_s_binnat.npy", Ss.astype(np.float32))
    np.save(dst / "C_constant_adu_s_binnat.npy", Cmap.astype(np.float32))
    np.savez(dst / "forma_temporal.npz", t=t, f=fn,
             noms=np.array([f.nom for f in llargs]))
    out = {"fase": "cel", "binning": BIN_CEL, "exp_minima_s": EXP_MIN_CEL,
           "n_fotogrames": len(llargs),
           "model_espacial": {"forma": "quàdrica 2-D (6 termes)",
                              "ajustada_a_r_major_que_rsol": R_MIN_AJUST_CEL,
                              "n_celles": int(k.sum()),
                              "residu_percent": round(
                                  100 * float(np.std(resq)) / float(np.median(Smap[k])), 3),
                              "coeficients": [float(x) for x in cq],
                              "motiu": ("el S cru segueix la corona a dins de 2 R☉ i "
                                        "restar-lo la fa negativa")},
           "forma_temporal": {"t": t.tolist(), "f": fn.tolist(),
                              "recorregut_percent": round(100 * float(fn.max() - fn.min()), 2),
                              "minim_a_t_s": float(t[np.argmin(fn)]),
                              "anell_rsol": [4.4, 5.1]},
           "cel_S_adu_s_per_pla": {n: {"mediana": float(np.median(Sq[n][bo])),
                                       "p05": float(np.percentile(Sq[n][bo], 5)),
                                       "p95": float(np.percentile(Sq[n][bo], 95))}
                                   for n in PLANS},
           "color_del_cel": {"anell_rsol": [4.4, 5.1], "respecte_del_verd": colors,
                             "motiu": ("mesurat on el cel és el 96 % del senyal; deduir-lo "
                                       "de l'ajust temporal de cada pla feia sortir el blau "
                                       "negatiu de 3,2 R☉ enfora")},
           "avis": ("S·f(t) és el cel VARIABLE. La part constant queda dins C i "
                    "aquesta via no la veu: el cel que se'n treu és una fita "
                    "inferior i C una fita superior de la corona."),
           "fitxers": {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                       for q in sorted(dst.iterdir())}}
    desa("model_de_cel.json", out)
    return out


_cel_cache: dict = {}


def carrega_model_cel():
    if "m" not in _cel_cache:
        dst = OUT_ARREL / "model_de_cel"
        z = np.load(dst / "forma_temporal.npz")
        pl = np.load(dst / "S_cel_per_pla.npz")
        _cel_cache["m"] = ({n: pl[n] for n in pl.files}, {"t": z["t"], "f": z["f"]})
    return _cel_cache["m"]


def cel_del_fotograma(f: C.Fotograma, forma: dict, S: dict,
                      shape: tuple[int, int]) -> np.ndarray:
    """Cel variable d'aquest fotograma, en ADU, a la reixa del mosaic.

    ⛔ Per pla de Bayer: el cel és molt més blau que la corona i restar la
    mitjana del mosaic als quatre plans deixa un residu de color que es menja
    l'exterior de la imatge.
    """
    import cv2
    fv = float(np.interp(f.t_rel_c2, forma["t"], forma["f"]))
    out = np.empty(shape, np.float32)
    hp, wp = shape[0] // 2, shape[1] // 2
    for n, (oy, ox) in (("R", (0, 0)), ("G1", (0, 1)), ("G2", (1, 0)), ("B", (1, 1))):
        out[oy::2, ox::2] = cv2.resize(S[n], (wp, hp), interpolation=cv2.INTER_CUBIC)
    return (out * (fv * f.exp_s)).astype(np.float32)


# ================================================================ Sony al llenç
def llenc_dos_trens(reg_sony: dict) -> tuple[int, int]:
    """Mida del llenç comú: la unió de les petjades dels DOS trens.

    ⛔ Mai un número escrit a mà: es projecta el perímetre de cada fotograma que
    hi entra i el llenç és el rectangle mínim, centrat al Sol, que els conté.
    """
    import sony as SY
    pts = []

    def perimetre(h, w, sol, pa, esc):
        pa = math.radians(pa)
        R = np.array([[math.cos(pa), math.sin(pa)], [-math.sin(pa), math.cos(pa)]])
        A = (esc / C.ESCALA) * R
        c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float)
        return (A @ (c - np.array(sol)).T).T

    pts.append(perimetre(4638, 6958, (6958 / 2, 4638 / 2), C.PA_NORD, C.ESCALA))
    for v in reg_sony["fotogrames"].values():
        if v["estat"] == "ADMES":
            pts.append(perimetre(5320, 7968, (SY.SOL_REF[0] + v["dx"], SY.SOL_REF[1] + v["dy"]),
                                 SY.PA_NORD, SY.ESCALA))
    P = np.vstack(pts)
    W = int(2 * math.ceil(np.abs(P[:, 0]).max() + C.MARGE_LLENC))
    H = int(2 * math.ceil(np.abs(P[:, 1]).max() + C.MARGE_LLENC))
    return W, H


def desplacament_lluna_al_llenc() -> tuple[np.ndarray, np.ndarray]:
    """(dx, dy) de la Lluna respecte del Sol al llenç, com a model lineal en t.

    És **efemèride**, o sigui que no depèn del tren: es mesura al manifest de la
    Vixen, es gira al llenç amb el seu `pa_north` i ja val per a la Sony.
    ⚠️ 61,24 ″ = 28,5 px de recorregut: corona i earthshine no comparteixen
    alineació, i per això el disc lunar es treu i no s'apila.
    """
    fg = C.llegeix_manifest()
    pa = math.radians(C.PA_NORD)
    R = np.array([[math.cos(pa), math.sin(pa)], [-math.sin(pa), math.cos(pa)]])
    t = np.array([f.t_rel_c2 for f in fg])
    d = np.array([[f.lluna_x - f.sol_x, f.lluna_y - f.sol_y] for f in fg])
    q = (R @ d.T).T
    A = np.vstack([np.ones_like(t), t]).T
    cx, *_ = np.linalg.lstsq(A, q[:, 0], rcond=None)
    cy, *_ = np.linalg.lstsq(A, q[:, 1], rcond=None)
    return cx, cy


def fase_cel_sony(args) -> dict:
    """Model de cel de la Sony, ajustat en coordenades de LLENÇ.

    ⛔ **No es pot ajustar per píxel de sensor.** La Sony va saltar 750 px =
    **2,5 R☉** entre els dos apuntaments, o sigui que un mateix píxel del sensor
    mira dos punts del cel diferents; l'ajust temporal confon el salt amb la
    variació del cel i la quàdrica en surt amb un residu del **51,5 %** (provat).
    El cel és fix al CEL, no al sensor, i és allà on s'ha d'ajustar.

    ⛔ I la **forma temporal** es pren de la VIXEN: el cel és el mateix i la
    Vixen el mostreja amb divuit fotogrames repartits per tota la totalitat,
    mentre que la Sony n'aporta onze partits entre dos apuntaments que no
    cobreixen bé la V. La Sony sí que dona l'amplitud i la forma espacial.

    El domini d'ajust és **r > 5 R☉**, on el camp enorme de la Sony —13 R☉—
    deixa moltíssima àrea i la corona és menys del 5 % del cel.
    """
    import cv2
    import sony as SY
    reg = SY.registre()["fotogrames"]
    admesos = [(n, v) for n, v in reg.items()
               if v["estat"] == "ADMES" and v["exp_s"] >= EXP_MIN_CEL]
    admesos.sort(key=lambda kv: kv[1]["t"])
    zv = np.load(OUT_ARREL / "model_de_cel" / "forma_temporal.npz")
    forma = {"t": zv["t"], "f": zv["f"]}
    log(f"cel Sony · {len(admesos)} fotogrames, forma temporal presa de la Vixen")

    PLANS = ["R", "G1", "G2", "B"]
    B2 = BIN_CEL // 2
    files_A, files_y, per_pla = [], [], {n: [] for n in PLANS}
    Wc, Hc = llenc_dos_trens(SY.registre())
    for k, (nom, v) in enumerate(admesos, 1):
        mos, sat = SY.calibra(nom)
        alt = (mos > SY.SOSTRE) | sat
        r = np.where(alt, np.nan, mos / v["exp_s"]).astype(np.float32)
        sol = (SY.SOL_REF[0] + v["dx"], SY.SOL_REF[1] + v["dy"])
        A = SY.afi(sol, (Wc / 2.0, Hc / 2.0))
        fv = float(np.interp(v["t"], forma["t"], forma["f"]))
        for n, (pla, oy, ox) in C.plans(r).items():
            b = _binna(np.nan_to_num(pla, nan=0.0), B2)
            hb, wb = b.shape
            yy, xx = np.mgrid[0:hb, 0:wb]
            my = (yy + 0.5) * B2 * 2 + oy
            mx = (xx + 0.5) * B2 * 2 + ox
            cx_ = A[0, 0] * mx + A[0, 1] * my + A[0, 2] - Wc / 2.0
            cy_ = A[1, 0] * mx + A[1, 1] * my + A[1, 2] - Hc / 2.0
            rc = np.hypot(cx_, cy_) / C.R_SOL_PX
            m = (rc > 5.0) & (b > 0)
            if n == "G1":
                u, w_ = cx_[m] / Wc, cy_[m] / Hc
                files_A.append(np.column_stack([
                    np.ones(m.sum()), fv * np.ones(m.sum()), fv * u, fv * w_,
                    fv * u * u, fv * u * w_, fv * w_ * w_]))
                files_y.append(b[m])
            per_pla[n].append(float(np.median(b[m])) if m.sum() > 100 else np.nan)
        if k % 4 == 0 or k == len(admesos):
            log(f"  [{k:2d}/{len(admesos)}] {nom}")
        del mos, sat, r
    Am = np.vstack(files_A); ym = np.concatenate(files_y)
    if Am.shape[0] > 800000:
        idx = np.arange(0, Am.shape[0], Am.shape[0] // 800000)
        Am, ym = Am[idx], ym[idx]
    cq, *_ = np.linalg.lstsq(Am, ym, rcond=None)
    # ⚠️ Amb només un 30 % de variació temporal i onze fotogrames, la separació
    # entre el terme constant i el que va amb f(t) està mal condicionada: el
    # constant surt **−206 ADU/s**, que és impossible —és corona, no pot ser
    # negativa— i val el 18 % del senyal. Es fixa a zero, cosa que atribueix
    # tot el que hi ha a r > 5 R☉ al cel. ⚠️ Això vol dir que aquest model
    # **pot sobre-restar fins a un ~18 %**, i és el deute d'aquesta passada.
    constant_lliure = float(cq[0])
    if constant_lliure < 0:
        cq2, *_ = np.linalg.lstsq(Am[:, 1:], ym, rcond=None)
        cq = np.concatenate([[0.0], cq2])
    res = ym - Am @ cq
    log(f"  quàdrica al llenç a r > 5 R☉ ({len(ym)} mostres): residu "
        f"{100 * np.std(res) / np.median(ym):.2f} %  ·  constant lliure "
        f"{constant_lliure:.1f} ADU/s → fixada a {cq[0]:.1f} "
        f"({100 * abs(constant_lliure) / np.median(ym):.0f} % del senyal)")
    colors = {n: float(np.nanmedian(per_pla[n]) / np.nanmedian(per_pla["G1"]))
              for n in PLANS}
    log("  color del cel a r > 5 R☉ (verd = 1): "
        + "  ".join(f"{n}={colors[n]:.4f}" for n in PLANS))

    dst = OUT_ARREL / "model_de_cel_sony"
    dst.mkdir(parents=True, exist_ok=True)
    np.savez(dst / "quadrica_al_llenc.npz", coef=cq[1:], corona_residual=cq[0],
             llenc=np.array([Wc, Hc]), colors=np.array([colors[n] for n in PLANS]))
    out = {"fase": "cel_sony", "n_fotogrames": len(admesos),
           "ajust": "quàdrica 2-D en coordenades de LLENÇ, r > 5 R☉",
           "forma_temporal": "presa de la Vixen (18 fotogrames, tota la totalitat)",
           "coeficients": [float(x) for x in cq[1:]],
           "corona_residual_adu_s": float(cq[0]),
           "constant_lliure_adu_s": constant_lliure,
           "avis_sobreresta": ("el terme constant lliure surt negatiu —impossible, és "
                               "corona— i val el %.0f %% del senyal; fixat a zero, el model "
                               "pot SOBRE-RESTAR fins a aquest %%"
                               % (100 * abs(constant_lliure) / float(np.median(ym)))),
           "residu_percent": round(100 * float(np.std(res)) / float(np.median(ym)), 3),
           "color_del_cel": colors, "llenc": [Wc, Hc],
           "per_que_al_llenc": ("ajustat per píxel de sensor, els dos apuntaments separats "
                                "750 px = 2,5 R☉ confonen el salt amb la variació del cel i "
                                "la quàdrica dona un residu del 51,5 %"),
           "fitxers": {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                       for q in sorted(dst.glob("quadrica*"))}}
    desa("model_de_cel_sony.json", out)
    return out


def fase_sony(args) -> dict:
    """Compost LDIC del tren Sony, directament al llenç comú.

    ⛔ Aquí SÍ que es gira cada fotograma, al contrari que a la Vixen: la Sony
    va a una escala i una orientació diferents (3,2020 ″/px i PA 90,27° contra
    2,1495 i 57,19), o sigui que no hi ha cap reixa comuna on sumar sense
    transformar. El que es conserva és l'arquitectura: una sola suma ponderada.
    """
    import cv2
    import sony as SY
    reg = SY.registre()
    porta = SY.porta_registre_sony(reg)
    log(f"Sony · registre {porta['estat']}: {porta['n_admesos']} admesos "
        f"({porta['n_per_estrelles']} per estrelles + {porta['n_heretats_de_rafega']} heretats), "
        f"pitjor incertesa {porta['pitjor_incertesa_px']} px")
    if porta["estat"] != "PASS":
        raise SystemExit("el registre de la Sony no passa la porta")

    Wc, Hc = llenc_dos_trens(reg)
    log(f"llenç dels dos trens: {Wc} × {Hc} px "
        f"({Wc * C.ESCALA / C.RSOL_ARCSEC:.2f} × {Hc * C.ESCALA / C.RSOL_ARCSEC:.2f} R☉)")
    clx, cly = desplacament_lluna_al_llenc()

    canals = ["R", "G", "B"]
    num = {c: np.zeros((Hc, Wc), np.float64) for c in canals}
    den = {c: np.zeros((Hc, Wc), np.float64) for c in canals}
    ncon = {c: np.zeros((Hc, Wc), np.uint16) for c in canals}

    admesos = [(n, v) for n, v in reg["fotogrames"].items() if v["estat"] == "ADMES"]
    admesos.sort(key=lambda kv: kv[1]["t"])

    # ⛔ La coherència de transparència, igual que a la Vixen: la malaltia no és
    # d'un cos, és de la fusió HDR amb aire que canvia. Vegeu `fase_coherencia`.
    coh = None
    if getattr(args, "coherencia", None):
        coh = json.loads(Path(args.coherencia).read_text())["factors"]
        log(f"  coherència per fotograma: {len(coh)} fotogrames")

    # Anivellament de cel, igual que a la Vixen: el cel de la totalitat NO és
    # estacionari i cada esglaó és d'un instant diferent, o sigui que sense
    # això el compost porta un nivell diferent a cada radi. L'anell va a
    # 6–8 R☉, que a l'escala de la Sony hi cap de sobres (el camp són 26,9 R☉).
    usa_model = getattr(args, "cel", "anell") == "model"
    if usa_model:
        zq = np.load(OUT_ARREL / "model_de_cel_sony" / "quadrica_al_llenc.npz")
        coef_cel = zq["coef"]; colors_cel = zq["colors"]
        zv = np.load(OUT_ARREL / "model_de_cel" / "forma_temporal.npz")
        forma_sony = {"t": zv["t"], "f": zv["f"]}
        log("  cel: model 2-D per fotograma (l'anivellament per anell queda fora)")
        nivells = {n: np.zeros(4) for n, _ in admesos}
        ref_niv = np.zeros(4)
    else:
        log("  anivellament de cel a 6–8 R☉…")
        nivells = {}
    for nom, v in ([] if usa_model else admesos):
        mos, sat = SY.calibra(nom)
        if coh is not None and nom in coh:
            mos = C.aplica_coherencia(mos, coh[nom])
        sol = (SY.SOL_REF[0] + v["dx"], SY.SOL_REF[1] + v["dy"])
        rs = C.RSOL_ARCSEC / SY.ESCALA
        vals = []
        for nom_pla, (pla, oy, ox) in C.plans(mos).items():
            rr = C.anells(*pla.shape, (sol[1] - oy) / 2, (sol[0] - ox) / 2) * 2
            m = (rr > 6.0 * rs) & (rr < 8.0 * rs) & (pla <= SY.SOSTRE)
            vals.append(float(np.median(pla[m])) / v["exp_s"] if m.any() else math.nan)
        nivells[nom] = np.array(vals)
        del mos, sat
    if not usa_model:
        ref_niv = np.median(np.array([nivells[n] for n, _ in admesos]), axis=0)
        vv = np.array([nivells[n][1] for n, _ in admesos])
        log(f"    verd de {vv.min():.1f} a {vv.max():.1f} ADU/s "
            f"({100 * (vv.max() - vv.min()) / ref_niv[1]:.1f} % de variació)")
    yy = np.arange(Hc, dtype=np.float32)[:, None] - Hc / 2.0
    xx = np.arange(Wc, dtype=np.float32)[None, :] - Wc / 2.0

    rng = np.random.default_rng(20260823)
    smp = [{"id": f"G_{int(a)}_{int(b)}", "y": int(a), "x": int(b), "pesos": [], "valors": []}
           for a, b in zip(rng.integers(int(0.35 * Hc), int(0.65 * Hc), 300),
                           rng.integers(int(0.35 * Wc), int(0.65 * Wc), 300))]

    for k, (nom, v) in enumerate(admesos, 1):
        mos, sat = SY.calibra(nom)
        t = v["exp_s"]
        sol = (SY.SOL_REF[0] + v["dx"], SY.SOL_REF[1] + v["dy"])
        # ⛔ La saturació i la variància es jutgen SENSE corregir: un píxel és al
        # pou pels comptes que hi van caure, no pels que li quedin després.
        mos_brut = mos.copy() if coh is not None else mos
        if coh is not None and nom in coh:
            mos = C.aplica_coherencia(mos, coh[nom])
        if usa_model:
            # el cel s'avalua on és fix: al llenç, i es porta a la reixa del cos
            fv = float(np.interp(v["t"], forma_sony["t"], forma_sony["f"]))
            Aq = SY.afi(sol, (Wc / 2.0, Hc / 2.0))
            my, mx = np.mgrid[0:mos.shape[0], 0:mos.shape[1]].astype(np.float32)
            cxq = Aq[0, 0] * mx + Aq[0, 1] * my + Aq[0, 2] - Wc / 2.0
            cyq = Aq[1, 0] * mx + Aq[1, 1] * my + Aq[1, 2] - Hc / 2.0
            del mx, my
            u = cxq / Wc; w_ = cyq / Hc
            del cxq, cyq
            base_cel = (coef_cel[0] + coef_cel[1] * u + coef_cel[2] * w_
                        + coef_cel[3] * u * u + coef_cel[4] * u * w_
                        + coef_cel[5] * w_ * w_).astype(np.float32)
            del u, w_
            cel = np.empty_like(base_cel)
            for ic, (oy, ox) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                cel[oy::2, ox::2] = base_cel[oy::2, ox::2] * colors_cel[ic]
            del base_cel
            mos_brut = mos.copy()
            mos = mos - cel * np.float32(fv * t)
            del cel
        A = SY.afi(sol, (Wc / 2.0, Hc / 2.0))
        # disc lunar al llenç, per aquest instant
        mlx = clx[0] + clx[1] * v["t"]
        mly = cly[0] + cly[1] * v["t"]
        d_ll = np.hypot(xx - mlx, yy - mly)
        # ⛔ smoothstep, pel mateix motiu que el `taper` de saturació: un clip
        # lineal deixa DOS colzes C⁰ —a d_ll = 464 i 478 px, o sigui 1,053 i
        # 1,085 R☉ de cada fotograma, i la deriva Lluna-Sol de ±14 px els
        # esbarria fins a 1,02-1,117 R☉—. Avui no mossega el producte declarat,
        # que talla a 1,12 R☉, però viu dins del llenç i de les previsualitzacions
        # i és el primer que apareix si algú abaixa el límit interior.
        pes_lluna = C.rampa((d_ll - (C.R_LLUNA_PX + 4)) / 14.0)

        desp = dict(zip(["R", "G1", "G2", "B"], (nivells[nom] - ref_niv) * t))
        plans_bruts = C.plans(mos_brut)
        for nom_pla, (pla, oy, ox) in C.plans(mos).items():
            pla = pla - desp[nom_pla]
            # ⛔ Saturació i variància amb el valor CRU, com a la Vixen.
            brut = plans_bruts[nom_pla][0]
            spl = C.plans(sat.astype(np.uint8))[nom_pla][0] > 0
            c = "G" if nom_pla.startswith("G") else nom_pla
            brut_pes = (gaussian_filter(brut, PES_SUAU) if PES_SUAU > 0 else brut)
            s = np.maximum(brut_pes, 0.0)
            w = (t * t) / (s / SY.GUANY[nom_pla] + SY.RN * SY.RN)
            # ⛔ smoothstep, pel mateix motiu que el bessó de la Vixen (l. 510).
            taper = C.rampa((SY.SOSTRE - brut_pes) / (C.RAMPA_SOSTRE * SY.SOSTRE))
            w = (w * taper).astype(np.float32)
            w[brut > SY.SOSTRE] = 0.0
            w[spl] = 0.0
            val = (pla / t).astype(np.float32)
            M = A.copy()
            M[:, 2] = A[:, :2] @ np.array([ox, oy], float) + A[:, 2]
            M[:, :2] = A[:, :2] * 2.0
            wv = cv2.warpAffine(w * val, M, (Wc, Hc), flags=cv2.INTER_LANCZOS4,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
            ww = cv2.warpAffine(w, M, (Wc, Hc), flags=cv2.INTER_LANCZOS4,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
            # ⛔ Interpolar el pes i el producte pes×valor per separat i després
            # dividir és correcte ON HI HA PES, i **basura on no n'hi ha**: el
            # nucli de Lanczos té lòbuls negatius, i a la vora del fotograma i a
            # la vora de la màscara lunar deixa píxels amb `w` pràcticament zero
            # i numerador no nul. Sense terra, el compost hi treia valors de
            # **−3,3 B/B☉** —trenta mil vegades el màxim real— i la porta F
            # fallava perquè aquells píxels entraven al numerador i no al
            # denominador. El terra és relatiu al pes màxim del mateix pla.
            terra = 1e-6 * float(ww.max()) if ww.size else 0.0
            fora = ww < terra
            ww[fora] = 0.0
            wv[fora] = 0.0
            np.clip(ww, 0.0, None, out=ww)
            ww *= pes_lluna
            wv *= pes_lluna
            num[c] += wv
            den[c] += ww
            ncon[c] += (ww > 0)
            if c == "G":
                for m in smp:
                    a = float(ww[m["y"], m["x"]])
                    if a > 0:
                        m["pesos"].append(a)
                        m["valors"].append(float(wv[m["y"], m["x"]] / a))
            del wv, ww
        log(f"  [{k:2d}/{len(admesos)}] {nom} {t:<10g} {v['origen']}")
        del mos, sat, pes_lluna

    hdr = np.full((Hc, Wc, 3), np.nan, np.float32)
    cob = np.zeros((Hc, Wc, 3), np.uint16)
    for i, c in enumerate(canals):
        d = den[c]; bo = d > 0
        hdr[..., i] = np.where(bo, num[c] / np.maximum(d, 1e-30), np.nan)
        cob[..., i] = ncon[c]
    hdr *= np.float32(SY.FB)

    _sfx = ("_cel-model" if usa_model else "") + ("_coh" if coh is not None else "")
    dst = OUT_ARREL / f"sony_llenc_comu{_sfx}"
    dst.mkdir(parents=True, exist_ok=True)
    np.save(dst / "SONY_LLENC_BBsol.npy", hdr)
    np.save(dst / "SONY_COBERTURA.npy", cob)
    np.save(dst / "SONY_D_verd.npy", den["G"].astype(np.float32))
    # ⏭️ 26-08-2026 (cua 2 del research/107 §5): la variància PER CANAL. Sense
    # aquestes dues, cap producte per canal de la Sony no passa de diagnòstic
    # (els filtres han d'aprofitar la D del verd, amb les portes de soroll
    # ~√2 generoses). El G ja es desava; R i B són el mateix denominador.
    np.save(dst / "SONY_D_R.npy", den["R"].astype(np.float32))
    np.save(dst / "SONY_D_B.npy", den["B"].astype(np.float32))
    porta_f = P.porta_f_mescla([{"id": m["id"], "pesos": m["pesos"], "valors": m["valors"],
                                 "compost": float(hdr[m["y"], m["x"], 1] / SY.FB)}
                                for m in smp if m["pesos"]])
    gR = P.porta_rectangle(hdr[..., 1])
    log(f"  F (compost ≡ mescla) → {porta_f['estat']}  {porta_f.get('desviacio_relativa_maxima')}")
    log(f"  rectangle → {gR['estat']}")

    res = {"tren": "sony_a7r3a_300gm", "llenc": [Wc, Hc],
           "escala_arcsec_px": C.ESCALA, "pa_north_sony": SY.PA_NORD,
           "escala_sony_arcsec_px": SY.ESCALA,
           "unitats": "B/B☉", "FB": SY.FB, "guany_e_adu": SY.GUANY["G1"], "rn_adu": SY.RN,
           "integracio_admesa_s": round(sum(v["exp_s"] for _, v in admesos), 4),
           "porta_registre": porta, "porta_f": porta_f, "porta_rectangle": gR,
           "anivellament_de_cel": {"anell_rsol": [6.0, 8.0],
                                   "referencia_adu_s": [round(float(x), 4) for x in ref_niv],
                                   "per_fotograma": {n: [round(float(x), 4) for x in nivells[n]]
                                                     for n, _ in admesos}},
           "desplacament_lluna_al_llenc": {"x0": float(clx[0]), "vx_px_s": float(clx[1]),
                                           "y0": float(cly[0]), "vy_px_s": float(cly[1])},
           "registre": reg,
           "fitxers": {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                       for q in sorted(dst.glob("*.npy"))}}
    desa(f"sony_llenc_comu{_sfx}.json", res)
    return res


# ================================================================ llenç comú
def fase_llenc(args) -> dict:
    """El compost al llenç comú: nord amunt, Sol al centre, una sola rotació.

    ⛔ Es gira **el compost**, no cada fotograma. La rotació és la mateixa per a
    tots els 68, o sigui que fer-la a l'entrada costaria 68 interpolacions en
    lloc d'una i no compraria res.
    """
    import cv2
    import tifffile
    dst = OUT_ARREL / args.etiqueta
    hdr = np.load(dst / "HDR_adu_s.npy")
    cob = np.load(dst / "COBERTURA.npy")
    H, W = hdr.shape[:2]
    A = C.afi((W / 2.0, H / 2.0), (0.0, 0.0))
    c = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
    q = (A[:, :2] @ c.T).T + A[:, 2]
    Wc = int(2 * math.ceil(np.abs(q[:, 0]).max() + C.MARGE_LLENC))
    Hc = int(2 * math.ceil(np.abs(q[:, 1]).max() + C.MARGE_LLENC))
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    log(f"llenç comú {Wc} × {Hc} px  ({Wc * C.ESCALA / C.RSOL_ARCSEC:.2f} × "
        f"{Hc * C.ESCALA / C.RSOL_ARCSEC:.2f} R☉), nord amunt, Sol al centre")

    valid = np.isfinite(hdr[..., 1]).astype(np.float32)
    dades = np.nan_to_num(hdr, nan=0.0).astype(np.float32)
    out = cv2.warpAffine(dades * valid[..., None], A, (Wc, Hc),
                         flags=cv2.INTER_LANCZOS4,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    # ⛔ L'alfa s'ha de warpar amb el MATEIX nucli que les dades i s'hi ha de
    # DIVIDIR: si no, el numerador es barreja amb els zeros de fora del pes i la
    # vora hereta el biaix cap avall. Mesurat el 24-08-2026 reproduint el warp:
    # la mediana no es movia, però al percentil 1 el valor sortia **−42,9 % a
    # 1,02-1,04 R☉** i −15,3 % a 1,04-1,06 —una vora fosca al voltant de la
    # màscara lunar i al perímetre del sensor—. El camí de la Sony (l. 1198-1205)
    # ja ho feia bé i aquests dos no.
    alfa = cv2.warpAffine(valid, A, (Wc, Hc), flags=cv2.INTER_LANCZOS4,
                          borderValue=0.0)
    out = np.where(alfa[..., None] > 1e-3, out / np.maximum(alfa[..., None], 1e-3), 0.0)
    ncob = cv2.warpAffine(cob[..., 1].astype(np.float32), A, (Wc, Hc),
                          flags=cv2.INTER_NEAREST, borderValue=0.0)
    out[alfa < 0.5] = np.nan
    out *= np.float32(C.FB)                       # ADU/s → B/B☉

    tif = dst / "LLENC_COMU_BBsol_float32.tif"
    tifffile.imwrite(tif, out, photometric="rgb")
    np.save(dst / "LLENC_COBERTURA.npy", ncob.astype(np.uint16))
    log(f"  → {tif.name}  ({tif.stat().st_size / 1e6:.0f} MB)")

    gR = P.porta_rectangle(out[..., 1])
    log(f"  rectangle al llenç → {gR['estat']}  ({gR.get('frontera')})")

    # ---- previsualitzacions. ⚠️ NOMÉS PER MIRAR: el producte és el TIFF lineal.
    # El pipeline no aplica balanç de blancs ni matriu de color a propòsit, o
    # sigui que el lineal surt verd; aquí es neutralitza per a la vista i el
    # factor queda escrit al rebut per poder-lo desfer.
    prev_dir = PREV_ARREL
    prev_dir.mkdir(parents=True, exist_ok=True)
    Hc2, Wc2 = out.shape[:2]
    rr = C.anells(Hc2, Wc2, Hc2 / 2.0, Wc2 / 2.0) / C.R_SOL_PX
    anell = (rr > 2.0) & (rr < 3.0) & np.isfinite(out[..., 1])
    wb = [float(np.nanmedian(out[..., 1][anell]) / np.nanmedian(out[..., i][anell]))
          for i in range(3)]
    neutre = out * np.array(wb, np.float32)

    ref = float(np.nanpercentile(neutre[..., 1], 99.9))
    g = np.log1p(np.clip(neutre / ref, 0, 1) * 2000.0) / math.log1p(2000.0)
    png = prev_dir / f"{args.etiqueta}_lineal.png"
    cv2.imwrite(str(png), cv2.cvtColor(
        (np.clip(np.nan_to_num(g), 0, 1) * 65535).astype(np.uint16), cv2.COLOR_RGB2BGR))
    log(f"  → {png.name}")

    # vista normalitzada radialment (envolupant de la mediana per anell).
    # ⛔ Això NO és una fase 3 ni entra a cap producte: és el mirall que deixa
    # veure si hi ha anells de fusió a ull nu. I es fa a TOT el rectangle.
    nb = 700
    ib = np.clip((rr / rr.max() * nb).astype(int), 0, nb - 1)
    vis = np.empty_like(neutre)
    for ch in range(3):
        v = neutre[..., ch]
        bo = np.isfinite(v)
        med = np.full(nb, np.nan)
        o = np.argsort(ib[bo]); ii = ib[bo][o]; vv = v[bo][o]
        talls = np.searchsorted(ii, np.arange(nb + 1))
        for a in range(nb):
            seg = vv[talls[a]:talls[a + 1]]
            if seg.size > 200:
                med[a] = np.median(seg)
        bons = np.isfinite(med)
        med = np.interp(np.arange(nb), np.flatnonzero(bons), med[bons])
        # ⛔ per interpolació contínua en r, mai `med[ib]`: aquest mirall existeix
        # justament perquè s'hi vegin els anells de fusió, i dividir per un perfil
        # per calaix n'hi posava 700 de falsos, amb dents de serra. (24-08-2026)
        centres_r = (np.arange(nb) + 0.5) * rr.max() / nb
        vis[..., ch] = v / np.maximum(np.interp(rr, centres_r, med), 1e-30)
    lo, hi = np.nanpercentile(vis[..., 1], [1, 99.5])
    png2 = prev_dir / f"{args.etiqueta}_normalitzat_radialment.png"
    cv2.imwrite(str(png2), cv2.cvtColor(
        (np.clip(np.nan_to_num((vis - lo) / max(hi - lo, 1e-9)), 0, 1) * 65535
         ).astype(np.uint16), cv2.COLOR_RGB2BGR))
    log(f"  → {png2.name}")

    res = {"etiqueta": args.etiqueta, "llenc": [Wc, Hc],
           "escala_arcsec_px": C.ESCALA, "pa_north_aplicat": C.PA_NORD,
           "rsol_px": C.R_SOL_PX, "camp_rsol": [round(Wc * C.ESCALA / C.RSOL_ARCSEC, 3),
                                                round(Hc * C.ESCALA / C.RSOL_ARCSEC, 3)],
           "unitats": "B/B☉", "factor_aplicat": C.FB,
           "fraccio_valida": round(float(np.isfinite(out[..., 1]).mean()), 6),
           "porta_rectangle": gR,
           "previsualitzacions": {
               "lineal": {"fitxer": str(png), "balanc_aplicat_rgb": wb,
                          "corba": f"log1p(clip(B/B☉·wb / {ref:.6g}, 0, 1)*2000)/log1p(2000)",
                          "ref_BBsol": ref},
               "normalitzat_radialment": {
                   "fitxer": str(png2), "que_es": "cada píxel dividit per la mediana del seu anell",
                   "avis": ("NOMÉS PER MIRAR: no és cap fase 3, no entra a cap producte i "
                            "no conserva fotometria. Serveix per veure si hi ha anells."),
                   "retall_percentils": [float(lo), float(hi)]}},
           "fitxers": {p.name: {"bytes": p.stat().st_size, "sha256": C.sha256(p)}
                       for p in (tif, dst / "LLENC_COBERTURA.npy")}}
    desa(f"llenc_{args.etiqueta}.json", res)
    return res


def sufix_sony(etiqueta: str) -> str:
    """El sufix del compost Sony que correspon a una etiqueta de la Vixen.

    ⛔ Funció pura i provada a part perquè el 25-08-2026 aquesta lògica es va
    menjar el `_coh` en silenci: `filtres_sony --coh` construïa el sufix,
    aquí es descartava, i el producte etiquetat `filtres_sony_coh` sortia del
    compost **sense** coherència —els dos rebuts de fase 3 de la Sony deien
    `etiqueta: "sony_llenc_comu"`—. O sigui que la cura de les costures de fusió
    no s'havia aplicat mai a aquest tren, i la seva frontera de 1,271 R☉ és
    exactament l'arc que Pere va marcar en verd.
    """
    sufix = ""
    for cand in ("_cel-model", "_cel-color"):
        if cand in etiqueta:
            sufix = cand
            break
    if "_coh" in etiqueta:
        sufix += "_coh"
    return sufix


def _dir_sony(etiqueta: str) -> Path:
    """El compost Sony que CORRESPON a la variant de cel de la Vixen.

    ⛔ Fins al 24-08-2026 `dos_trens`, `filtres_sony` i `dos_trens_filtrats`
    llegien **sempre** `sony_llenc_comu`, també quan la Vixen venia de la
    variant `_cel-model`: o sigui que es comparava una Vixen amb el cel 2-D
    restat contra una Sony **només anivellada per anell**, en silenci. El
    quocient `anell/model` de la Sony val ×1,25 a 1,5-2 R☉, **×2,51 a 2-3**,
    ×5,72 a 3-4, **×16,3 a 4-5,5** i ×74 a 5,5-8: qualsevol quocient
    Sony/Vixen calculat així és soroll pur més enllà de 2 R☉, i és exactament
    el número del qual penja el ±14 % de `research/99` §15.

    Falla tancat: si la variant que toca no hi és, no se n'agafa una altra.
    """
    sufix = sufix_sony(etiqueta)
    d = OUT_ARREL / f"sony_llenc_comu{sufix}"
    if not (d / "SONY_LLENC_BBsol.npy").exists():
        raise SystemExit(
            f"⛔ falta el compost Sony de la variant que toca: {d}\n"
            f"   la Vixen ve de `{etiqueta}`; executa primer:\n"
            + ("   cel_per_color.py --resta-sony <sony_llenc_comu>"
               if sufix == "_cel-color" else "   sony"
               + ("  --cel model" if sufix else "")))
    return d


def fase_dos_trens(args) -> dict:
    """Els dos trens al mateix llenç, i què diuen l'un de l'altre.

    ⛔ **Aquesta comparació NO porta cap paràmetre lliure.** Cada tren arriba
    amb el seu propi factor absolut a B/B☉ —2,772e-11 la Vixen i 1,134e-11 la
    Sony, `research/75` §5.2— i el que es mesura és el quocient tal com surt.
    Amb `k(φ)` lliure l'acord s'hi imposaria, que és exactament el motiu pel
    qual `research/97` declara que **el producte fusionat no és una mesura**.
    """
    import cv2
    import sony as SY
    import tifffile
    d_sony = _dir_sony(args.etiqueta)
    sony = np.load(d_sony / "SONY_LLENC_BBsol.npy")
    Hc, Wc = sony.shape[:2]
    log(f"llenç dels dos trens: {Wc} × {Hc} px")

    vx = np.load(OUT_ARREL / args.etiqueta / "HDR_adu_s.npy")
    H, W = vx.shape[:2]
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    valid = np.isfinite(vx[..., 1]).astype(np.float32)
    vix = cv2.warpAffine(np.nan_to_num(vx, nan=0.0).astype(np.float32)
                         * valid[..., None], A, (Wc, Hc),
                         flags=cv2.INTER_LANCZOS4, borderValue=0.0)
    # ⛔ L'alfa s'ha de warpar amb el MATEIX nucli que les dades i s'hi ha de
    # DIVIDIR: si no, el numerador es barreja amb els zeros de fora del pes i la
    # vora hereta el biaix cap avall. Mesurat el 24-08-2026 reproduint el warp:
    # la mediana no es movia, però al percentil 1 el valor sortia **−42,9 % a
    # 1,02-1,04 R☉** i −15,3 % a 1,04-1,06 —una vora fosca al voltant de la
    # màscara lunar i al perímetre del sensor—. El camí de la Sony (l. 1198-1205)
    # ja ho feia bé i aquests dos no.
    al = cv2.warpAffine(valid, A, (Wc, Hc), flags=cv2.INTER_LANCZOS4,
                        borderValue=0.0)
    vix = np.where(al[..., None] > 1e-3, vix / np.maximum(al[..., None], 1e-3), 0.0)
    vix[al < 0.5] = np.nan
    vix *= np.float32(C.FB)
    del vx, valid

    yy = np.arange(Hc, dtype=np.float32)[:, None] - Hc / 2.0
    xx = np.arange(Wc, dtype=np.float32)[None, :] - Wc / 2.0
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    a, b = vix[..., 1], sony[..., 1]
    tots = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    log(f"  solapament: {100 * tots.mean():.2f} % del llenç")

    vores = np.linspace(1.05, 5.5, 30)
    files = []
    for i in range(len(vores) - 1):
        m = tots & (rr >= vores[i]) & (rr < vores[i + 1])
        if m.sum() < 2000:
            continue
        q = float(np.median(b[m] / a[m]))
        files.append({"r_rsol": round(0.5 * (vores[i] + vores[i + 1]), 4),
                      "n": int(m.sum()),
                      "vixen_BBsol": float(f"{np.median(a[m]):.5g}"),
                      "sony_BBsol": float(f"{np.median(b[m]):.5g}"),
                      "sony_entre_vixen": round(q, 5)})
    qs = np.array([f["sony_entre_vixen"] for f in files])
    log(f"  Sony/Vixen: mediana {np.median(qs):.4f}  de {qs.min():.4f} a {qs.max():.4f}")
    for f in files[::3]:
        log(f"    {f['r_rsol']:.2f} R☉  Vixen {f['vixen_BBsol']:.3g}  "
            f"Sony {f['sony_BBsol']:.3g}  ×{f['sony_entre_vixen']:.4f}")

    dst = OUT_ARREL / "dos_trens"
    dst.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(dst / "VIXEN_al_llenc_BBsol_float32.tif", vix, photometric="rgb")
    prev = PREV_ARREL
    prev.mkdir(parents=True, exist_ok=True)
    # ⛔ La previsualització NO fusiona: pinta cada tren al seu lloc perquè es
    # vegi la costura, que és el que s'ha de mirar abans de decidir res.
    # ⛔ El pipeline no aplica balanç de blancs ni matriu de color a propòsit, o
    # sigui que el lineal surt VERD: mesurat al PNG que verdejava, el verd hi era
    # +47,1 % sobre el vermell i +16,1 % sobre el blau. La previsualització d'un
    # tren sol ja ho neutralitzava i aquesta no ho feia. ⛔ No és cap error de
    # CFA: l'ordre RGGB és correcte, i una permutació R↔B deixa el verd al mateix
    # lloc, o sigui que donaria un biaix vermell/blau i no un domini verd.
    # (Detectat per Pere el 24-08-2026.)
    #
    # ⛔ I CADA TREN PER SEPARAT, mai un factor comú: a 2-3 R☉ la Vixen té
    # G/R 1,642 i G/B 2,360 i la Sony 2,037 i 1,936, o sigui que un sol `wb`
    # deixaria una costura de color del 24 % en R/G i del 22 % en B/G justament
    # on es toquen els dos trens.
    Hc3, Wc3 = vix.shape[:2]
    rr3 = C.anells(Hc3, Wc3, Hc3 / 2.0, Wc3 / 2.0) / C.R_SOL_PX
    def _wb(a):
        an = (rr3 > 2.0) & (rr3 < 3.0) & np.isfinite(a[..., 1])
        return [float(np.nanmedian(a[..., 1][an]) / np.nanmedian(a[..., i][an]))
                for i in range(3)]
    wb_v, wb_s = _wb(vix), _wb(sony)
    comp = np.where(np.isfinite(sony), sony * np.array(wb_s, np.float32),
                    vix * np.array(wb_v, np.float32))
    wb3 = {"vixen": wb_v, "sony": wb_s}
    ref = float(np.nanpercentile(comp[..., 1], 99.9))
    g = np.log1p(np.clip(np.nan_to_num(comp) / ref, 0, 1) * 2000.0) / math.log1p(2000.0)
    png = prev / "dos_trens_lineal.png"
    cv2.imwrite(str(png), cv2.cvtColor((np.clip(g, 0, 1) * 65535).astype(np.uint16),
                                       cv2.COLOR_RGB2BGR))
    log(f"  → {png.name}")

    res = {"balanc_de_blancs_de_la_previsualitzacio_rgb_per_tren": wb3,
           "llenc": [Wc, Hc], "escala_arcsec_px": C.ESCALA,
           "camp_rsol": [round(Wc * C.ESCALA / C.RSOL_ARCSEC, 3),
                         round(Hc * C.ESCALA / C.RSOL_ARCSEC, 3)],
           "solapament_percent": round(100 * float(tots.mean()), 4),
           "quocient_sony_entre_vixen": {
               "mediana": round(float(np.median(qs)), 5),
               "minim": round(float(qs.min()), 5), "maxim": round(float(qs.max()), 5),
               "per_radi": files,
               "avis": ("cap paràmetre lliure: cada tren ve amb el seu factor absolut. "
                        "⛔ I aquest acord NO valida la fotometria del producte fusionat: "
                        "research/97 declara que el fusionat no és una mesura.")},
           "previsualitzacio": str(png)}
    desa("dos_trens.json", res)
    return res


# ================================================================ FASE 3
SIGMES_ACHF = [2.0, 4.0, 8.0, 16.0, 32.0]
N_SOROLL = (6.0, 5.0, 4.0, 3.0, 2.0)


def _compara_bandes(control: dict, detall: np.ndarray, w: np.ndarray,
                    rr: np.ndarray, limit: float = 0.30) -> dict:
    """Quant del detall declarat, a cada banda, podria ser artefacte nostre."""
    fila = {}; pitjor = 0.0; on = None
    for clau, art in (control.get("per_banda") or {}).items():
        a, b = (float(x) for x in clau.split("-"))
        m = (w > 0) & (rr >= a) & (rr < b)
        if m.sum() < 500:
            continue
        real = float(np.std(detall[m]))
        q = art / max(real, 1e-12)
        fila[clau] = {"artefacte_rms_ln": round(art, 7),
                      "detall_declarat_rms_ln": round(real, 7),
                      "fraccio": round(q, 4)}
        if q > pitjor:
            pitjor, on = q, clau
    return {"per_banda_comparada": fila, "pitjor_fraccio": round(pitjor, 4),
            "pitjor_banda_rsol": on, "limit": limit,
            "estat": "PASS" if pitjor < limit else "FAIL"}


def _vista_de_caca(dir_detall, etiqueta: str, prev: Path) -> Path:
    """La vista amb realçat per anell i les fronteres de fusió dibuixades.

    ⛔ Es genera SEMPRE, a cada fase 3 i als dos trens. És la vista que el
    24-08-2026 va destapar que els arcs seguien els contorns de fusió quan tots
    els meus números deien que ja no hi eren.
    """
    import subprocess
    eina = Path(__file__).resolve().parent / "vista_arcs.py"
    hdr = OUT_ARREL / etiqueta / "HDR_adu_s.npy"
    if not hdr.exists():
        raise FileNotFoundError(hdr)
    fg = C.llegeix_manifest()
    exps = sorted({f.exp_s for f in fg})
    dst = prev / f"caca_arcs_{etiqueta}.png"
    subprocess.run([sys.executable, str(eina), str(dir_detall), "--comp", str(hdr),
                    "--sostre", f"{C.SOSTRE:.6g}", "--exposicions",
                    *[f"{e:.9g}" for e in exps], "-o", str(dst),
                    "--titol", f"cacera d'arcs · {etiqueta}"],
                   check=True, capture_output=True)
    return dst


def _filtra(I, V, rr, etiqueta, sufix, log_pref=""):
    """Nucli comú de la fase 3, per a qualsevol producte a qualsevol reixa."""
    import cv2
    import filtres as F
    import tifffile
    H, W = I.shape
    SNR_MIN = 5.0
    snr = np.where((I > 0) & np.isfinite(V) & (V > 0),
                   I / np.sqrt(np.maximum(V, 1e-30)), 0.0)
    # ⛔ NORMA DEL RECTANGLE. Aquí hi havia un `rr > 1,12`, que és un CERCLE
    # imposat i no una manca de dada. Mesurat el 24-08-2026, la banda que
    # llençava —1,085 a 1,120 R☉— té S/N mediana **298** i p5 **255**, i el
    # **100 %** dels seus píxels passen el llindar: és indistingible de
    # 1,12-1,20. El que ha d'aturar el filtre és no tenir dada, i això ja ho
    # diuen el pes —que porta la màscara lunar de la fase 2— i el llindar de
    # senyal/soroll. El terra interior queda a `R_LLUNA_PX + 4 + 14`, que és on
    # la màscara lunar acaba de pujar: allà sí que és una manca de dada física,
    # i és un cercle perquè la Lluna ho és.
    r_terra = (C.R_LLUNA_PX + 4.0 + 14.0) / C.R_SOL_PX
    w = (np.isfinite(I) & (I > 0) & np.isfinite(V)
         & (rr > r_terra) & (snr >= SNR_MIN)).astype(np.float32)
    log(f"{log_pref}{100 * w.mean():.1f} % del rectangle amb dada i S/N ≥ {SNR_MIN:.0f}")
    lnI = np.where(w > 0, np.log(np.maximum(I, 1e-12)), 0.0).astype(np.float32)
    var_ln = np.where((w > 0) & (I > 0), V / np.maximum(I, 1e-12) ** 2, 0.0).astype(np.float32)
    resid = F.treu_perfil_radial(lnI, w, rr)[0]
    detall, diag = F.achf(resid, w, SIGMES_ACHF, variancia=var_ln, n_soroll=N_SOROLL)
    # ⛔ SEGONA PASSADA NRGF, i va DESPRÉS de l'ACHF. La primera ha de suavitzar
    # el perfil —a ln I la dispersió d'un anell la domina la corona i restar la
    # mediana crua injectaria un 0,65 %—, i el suavitzat és el que deixa lòbuls:
    # mesurat el 24-08-2026 refent la fase 3 amb finestres de 9, 29 i 61
    # calaixos, els lòbuls **es mouen amb la finestra** (+0,179 / +0,074 /
    # −0,038 % a 1,182 R☉) i cap finestra no els mata. Després de l'ACHF la
    # dispersió d'un anell ja és el detall, l'error típic de la mediana cau a
    # 0,005 % i la mediana crua es pot restar exacta: la component circular
    # queda a zero **per construcció**. Detall: `filtres.treu_residu_circular`.
    circ_abans = F.rms_circular(detall, w, rr)
    niv_abans = F.rms_per_nivell(detall, w, I)
    # ⛔ DUES passades, i ALTERNADES. Les dues famílies d'artefactes que Pere va
    # marcar tenen la mateixa forma en dos espais diferents: els anells són
    # constants en RADI i les costures de fusió ho són en NIVELL —una frontera
    # HDR és una isofota per construcció, perquè el pes només depèn del valor
    # cru—. Cap de les dues no és funció de l'altra, però tampoc no són
    # independents (el nivell baixa amb el radi), i per això s'han d'alternar
    # fins que les dues baixin alhora. ⚠️ La circular va SEMPRE l'última, perquè
    # és la que té el terra de precisió més fi (0,005 % contra ~0,05 %).
    # ⛔ **Fins que CONVERGEIXI, no un nombre fix de voltes.** Els dos espais
    # —funcions del radi i funcions del nivell— se solapen molt (el nivell baixa
    # amb el radi), i l'alternança de projeccions hi convergeix a poc a poc:
    # mesurat el 24-08-2026, tres voltes baixaven la component de nivell del
    # 88,6 % al 22,6 % i s'aturaven allà perquè el bucle s'acabava, no perquè
    # hagués convergit. El que es treu és la suma f(r) + h(nivell), que és
    # exactament la unió de les dues famílies d'artefactes.
    iteracions = []
    perfil_circ = np.zeros(0)
    for _k in range(int(os.environ.get("PILOT_VOLTES", "20"))):
        detall, _, _ = F.treu_residu_per_nivell(detall, w, I)
        detall, perfil_circ, _ = F.treu_residu_circular(detall, w, rr)
        _c = F.rms_circular(detall, w, rr); _n = F.rms_per_nivell(detall, w, I)
        iteracions.append({"volta": _k + 1, "circular": round(_c["fraccio"], 5),
                           "per_nivell": round(_n["fraccio"], 5),
                           "rms_detall": round(float(np.std(detall[w > 0])), 8)})
        if _n["fraccio"] < 0.03 and _c["fraccio"] < 0.03:
            break
        if _k >= 2 and iteracions[-2]["per_nivell"] > 0 and \
                iteracions[-1]["per_nivell"] / iteracions[-2]["per_nivell"] > 0.97:
            break            # ja no baixa: aturar-se i dir-ho al rebut
    circ_despres = F.rms_circular(detall, w, rr)
    niv_despres = F.rms_per_nivell(detall, w, I)
    log(f"  {len(iteracions)} voltes d'alternança")
    gH1 = P.porta_h_circular(circ_despres["rms_circular"], circ_despres["rms_detall"])
    log(f"  anells concèntrics: {100 * circ_abans['fraccio']:.1f} % → "
        f"{100 * circ_despres['fraccio']:.1f} %   ·  costures (per nivell): "
        f"{100 * niv_abans['fraccio']:.1f} % → {100 * niv_despres['fraccio']:.1f} %"
        f"   H1 {gH1['estat']}")
    log(f"  detall: rms {np.std(detall[w > 0]):.5f} en ln "
        f"(= {100 * (math.exp(float(np.std(detall[w > 0]))) - 1):.2f} % de contrast)")
    r_a, amp, pes_a = F.perfil_amplitud(detall, w, rr, 1.2, 5.0, 80)
    gG = P.porta_g_envolupant(r_a, amp, pes_a)
    gR = P.porta_rectangle(np.where(w > 0, detall, np.nan),
                           r_ocultador_px=C.R_LLUNA_PX, marge_ocultador=1.045)
    n4 = (max(H // 4, 64), max(W // 4, 64))
    u4 = np.ones(n4, np.float32)
    c_llis = F.control_entrada_llisa(n4, u4, [x / 4 for x in SIGMES_ACHF], C.R_SOL_PX / 4)
    c_sor = F.control_soroll_pur(n4, u4, [x / 4 for x in SIGMES_ACHF],
                                 float(np.sqrt(np.median(var_ln[w > 0]))), N_SOROLL)
    log(f"  G {gG['estat']} (excés {gG.get('exces_maxim')})  ·  rectangle {gR['estat']}  ·  "
        f"llisa {100 * c_llis['relacio']:.2f} %  ·  soroll {c_sor['relacio']:.2f} σ")
    dsf = OUT_ARREL / f"filtres_{sufix}"
    dsf.mkdir(parents=True, exist_ok=True)
    np.save(dsf / "DETALL_ln.npy", detall)
    np.save(dsf / "PES.npy", w)
    res = {"fase": "3_filtres", "etiqueta": etiqueta, "snr_minim": SNR_MIN,
           "fraccio_del_rectangle": round(float(w.mean()), 5),
           "sigmes_px": SIGMES_ACHF, "n_soroll_per_sigma": list(N_SOROLL),
           "detall_rms_ln": float(np.std(detall[w > 0])),
           "contrast_percent": round(100 * (math.exp(float(np.std(detall[w > 0]))) - 1), 3),
           "per_escala": diag, "porta_g": gG, "porta_rectangle": gR,
           "porta_h_circular": gH1,
           "costures_per_nivell": {"abans": niv_abans, "despres": niv_despres,
                                   "iteracions": iteracions,
                                   "nota": ("una frontera de fusió HDR és una isofota per "
                                            "construcció: el pes d'un fotograma només depèn "
                                            "del seu valor cru, o sigui del NIVELL")},
           "anells_concentrics": {"abans_de_la_segona_passada": circ_abans,
                                  "despres": circ_despres,
                                  "nota": ("la primera passada NRGF ha de suavitzar el "
                                           "perfil i el suavitzat deixa lòbuls; la segona, "
                                           "després de l'ACHF, resta la mediana d'anell "
                                           "exacta i deixa la component circular a zero")},
           # ⛔ El criteri NO pot ser `rms(detall)/rms(entrada)`: la dispersió de
           # l'entrada està dominada pel perfil radial que acabem de treure, o
           # sigui que divideix per un número enorme i el control queda cec. Amb
           # l'escala d'esglaons del 24-08 posada, aquesta relació donava 0,33 %
           # contra un límit de l'1 %: PASS, i el que hi havia era un artefacte
           # que valia més de la meitat del detall declarat. El que decideix és
           # **quina fracció del detall que declarem podria ser artefacte**, i
           # ⛔ **banda per banda**: l'artefacte viu al limbe i una mitjana sobre
           # tot el camp l'hi dilueix amb els milions de píxels de fora.
           "control_entrada_llisa": {**c_llis, **_compara_bandes(c_llis, detall, w, rr)},
           "control_soroll_pur": {**c_sor,
                                  "estat": "PASS" if c_sor["relacio"] < 1.0 else "FAIL"}}
    return detall, w, res, dsf


def fase_filtres_sony(args) -> dict:
    """Fase 3 sobre el compost Sony, que ja viu al llenç comú."""
    import sony as SY
    _c = getattr(args, "cel", "anell")
    sufix_cel = {"model": "_cel-model", "color": "_cel-color"}.get(_c, "")
    if getattr(args, "coh", False):
        sufix_cel += "_coh"
    dst = _dir_sony(sufix_cel)
    hdr = np.load(dst / "SONY_LLENC_BBsol.npy")
    D = np.load(dst / "SONY_D_verd.npy")
    H, W = hdr.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    I = hdr[..., 1].astype(np.float32) / np.float32(SY.FB)     # tornem a ADU/s
    V = np.where(D > 0, 1.0 / np.maximum(D, 1e-30), np.inf).astype(np.float32)
    log("fase 3 Sony · ")
    detall, w, res, dsf = _filtra(I, V, rr, dst.name, "sony" + sufix_cel, "  ")
    res["tren"] = "sony_a7r3a_300gm"
    res["fitxers"] = {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                      for q in sorted(dsf.iterdir())}
    # ⛔ el rebut porta el sufix de la variant: si no, la tirada amb coherència
    # trepitjava el rebut de la de sense i el producte quedava sense certificat
    desa(f"fase3_sony{sufix_cel}.json", res)
    return res


def fase_filtres(args) -> dict:
    """Fase 3 · ACHF multi-σ amb porta de soroll de la variància pròpia.

    ⛔ **NORMA DEL RECTANGLE**: el filtre s'avalua a TOT el rectangle. L'única
    cosa que el limita és que no hi hagi dada, i això entra per la **convolució
    incompleta normalitzada pel pes** de la tesi de Brno §5.2 —no per cap
    circumferència—. Un ACHF retallat a un cercle hi deixaria el halo que la
    norma prohibeix.
    """
    import cv2
    dst = OUT_ARREL / args.etiqueta
    hdr = np.load(dst / "HDR_adu_s.npy")
    var = np.load(dst / "VAR_adu_s2.npy")
    H, W = hdr.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    log(f"fase 3 · filtres sobre {args.etiqueta}: ")
    detall, w, res, dsf = _filtra(hdr[..., 1].astype(np.float32),
                                 var[..., 1].astype(np.float32), rr,
                                 args.etiqueta, args.etiqueta, "  ")
    res["ordre"] = ("ln I → treure el perfil radial (NRGF) → ACHF. ⛔ Sense treure el "
                    "radial, l'ACHF s'inventa estructura: la curvatura del perfil és el "
                    "que un passa-alt gaussià llegeix com a detall")
    res["filtre"] = "ACHF multi-σ (tesi Brno §5.2) amb convolució incompleta i porta de soroll"
    import tifffile
    tifffile.imwrite(dsf / "DETALL_ln_float32.tif", np.where(w > 0, detall, np.nan))
    prev = PREV_ARREL
    prev.mkdir(parents=True, exist_ok=True)
    lo, hi = np.percentile(detall[w > 0], [0.5, 99.5])
    g = np.clip((detall - lo) / max(hi - lo, 1e-9), 0, 1)
    png = prev / f"fase3_achf_{args.etiqueta}.png"
    cv2.imwrite(str(png), (np.where(w > 0, g, 0.0) * 65535).astype(np.uint16))
    log(f"  → {png.name}")
    res["previsualitzacio"] = str(png)
    # ⛔ NORMA ZERO: la vista de caça surt SOLA. El 24-08-2026, tres artefactes de
    # quatre els va trobar Pere mirant imatges i cap va sortir de llegir codi; i
    # el quart, el meu número el declarava arreglat. Que la imatge existeixi no
    # pot dependre de si a algú se li acut generar-la.
    try:
        _cv = _vista_de_caca(dsf, args.etiqueta, prev)
        res["vista_de_caca"] = str(_cv)
        log(f"  → {_cv.name}")
    except Exception as _e:                      # mai ha d'aturar la fase
        log(f"  ⚠️ vista de caça no generada: {_e}")
    res["fitxers"] = {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                      for q in sorted(dsf.iterdir())}
    desa(f"fase3_{args.etiqueta}.json", res)
    return res


def fase_dos_trens_filtrats(args) -> dict:
    """El detall dels DOS trens al llenç comú.

    ⛔⛔ **I aquí el problema del ±14 % desapareix.** El §15 diu que l'escala
    absoluta del producte fusionat és incerta al ±14 % perquè els dos factors a
    B/B☉ ho són. Però un filtre passa-alt sobre `ln I` lliura **contrast
    relatiu**, i el contrast relatiu **no depèn de l'escala absoluta**: un
    factor multiplicatiu és una constant additiva en logaritme, i un passa-alt
    la treu. O sigui que **la via de la FOTO no pateix el problema que la via de
    la mesura sí que té**, i això és el millor argument tècnic que la decisió D1
    de `research/97` ha rebut.

    La combinació és per **inversa de la variància** de cada tren: la Vixen mana
    on el seu detall és més fi (2,15 ″/px contra 3,20) i la Sony on la Vixen no
    arriba. ⛔ Cap tall circular ni cap frontera dibuixada a mà.
    """
    import cv2
    import sony as SY
    import tifffile
    dv = np.load(OUT_ARREL / f"filtres_{args.etiqueta}" / "DETALL_ln.npy")
    wv = np.load(OUT_ARREL / f"filtres_{args.etiqueta}" / "PES.npy")
    # ⛔ El MATEIX defecte que `_dir_sony` tenia: aquí el sufix es construïa a
    # mà i també es menjava el `_coh`, o sigui que una Vixen coherent es
    # fusionava amb una Sony que no ho era, en silenci. Una sola funció per als
    # dos llocs (25-08-2026).
    sufix_s = sufix_sony(args.etiqueta)
    d_fs = OUT_ARREL / f"filtres_sony{sufix_s}"
    if not (d_fs / "DETALL_ln.npy").exists():
        raise SystemExit(f"⛔ falta {d_fs}; executa primer:  filtres_sony"
                         + ("  --cel model" if sufix_s else ""))
    ds = np.load(d_fs / "DETALL_ln.npy")
    ws = np.load(d_fs / "PES.npy")
    Hc, Wc = ds.shape
    log(f"dos trens filtrats · llenç {Wc} × {Hc}")

    # soroll de cada tren en el domini del logaritme
    hv = np.load(OUT_ARREL / args.etiqueta / "HDR_adu_s.npy")[..., 1].astype(np.float32)
    vv = np.load(OUT_ARREL / args.etiqueta / "VAR_adu_s2.npy")[..., 1].astype(np.float32)
    nv = np.where((hv > 0) & (vv > 0), vv / np.maximum(hv, 1e-12) ** 2, np.inf).astype(np.float32)
    d_sony = _dir_sony(args.etiqueta)
    hs = np.load(d_sony / "SONY_LLENC_BBsol.npy")[..., 1]
    hs = hs.astype(np.float32) / np.float32(SY.FB)
    Ds = np.load(d_sony / "SONY_D_verd.npy")
    ns = np.where((hs > 0) & (Ds > 0), (1.0 / np.maximum(Ds, 1e-30))
                  / np.maximum(hs, 1e-12) ** 2, np.inf).astype(np.float32)

    H, W = dv.shape
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    def al_llenc(x, ordre=cv2.INTER_LANCZOS4):
        return cv2.warpAffine(np.nan_to_num(x).astype(np.float32), A, (Wc, Hc),
                              flags=ordre, borderValue=0.0)
    dvc = al_llenc(dv * wv)
    wvc = al_llenc(wv, cv2.INTER_LINEAR)
    nvc = al_llenc(np.where(np.isfinite(nv), nv, 0.0) * wv, cv2.INTER_LINEAR)
    bo_v = wvc > 0.5
    dvc = np.where(bo_v, dvc / np.maximum(wvc, 1e-6), 0.0)
    nvc = np.where(bo_v, nvc / np.maximum(wvc, 1e-6), np.inf)

    # ⛔ **La combinació NO pot anar per inversa de la variància.** Els dos trens
    # tenen mostreig diferent —2,1495 contra 3,2020 ″/px— i el compost de la
    # Sony s'ha remostrejat 1,49× cap amunt en portar-lo al llenç: el seu Σw per
    # píxel queda inflat un factor ~2,2 que **no és senyal/soroll, és
    # mostreig**. Provat: amb inversa de variància la Sony guanyava el 80,6 %
    # del llenç i la Vixen es quedava amb el 0,2 %, que és absurd.
    #
    # La regla és **declarada, no mesurada**: mana la **Vixen** on té dada
    # —mostreja 1,49× més fi i integra 24,975 s de corona amb 68 fotogrames
    # contra 14— i la **Sony** omple més enllà. La transició és una rampa suau
    # a la vora de la petjada de la Vixen perquè no hi quedi costura.
    AMPLE_RAMPA_PX = 200.0
    from scipy.ndimage import binary_fill_holes, distance_transform_edt
    # ⛔⛔ LA TRAMPA CANÒNICA DEL PROJECTE, i hi havia tornat a caure.
    # `distance_transform_edt` mesura la distància al zero MÉS PROPER, i `bo_v`
    # val 0 **dins del disc lunar**: per a la corona interior el zero més proper
    # és el forat de la Lluna, o sigui que la rampa sortia del limbe cap enfora
    # en lloc de la vora de la petjada. Mesurat al llenç (24-08-2026): el pes de
    # la Vixen valia **0,090 a 1,12-1,20 R☉**, 0,288 a 1,20-1,30, 0,508 a
    # 1,30-1,40 i no arribava a 1 fins a 1,60 — o sigui que a la corona interior
    # el detall el posava la **Sony al 91 %**, exactament el contrari de la regla
    # declarada aquí dalt. I la rampa era una **circumferència de 200 px
    # centrada al Sol**, en una funció que declara que no hi ha cap tall circular.
    # El fix és omplir els forats interiors abans: llavors els únics zeros són
    # els de FORA de la petjada, i la rampa segueix la vora del sensor, que és
    # un rectangle girat i no un cercle.
    exterior = binary_fill_holes(bo_v)
    dist = distance_transform_edt(exterior).astype(np.float32)
    u_r = np.clip(dist / AMPLE_RAMPA_PX, 0.0, 1.0)
    # ⛔ i smoothstep, pel mateix motiu que el `taper` de saturació: un clip
    # lineal deixa un colze C⁰ a `dist = 200` que el passa-alt pinta com una vora.
    pv = (u_r * u_r * (3.0 - 2.0 * u_r)).astype(np.float32)
    pv = np.where(bo_v, pv, 0.0).astype(np.float32)   # el forat continua sent forat
    ps = np.where(ws > 0, 1.0, 0.0).astype(np.float32) * (1.0 - pv)
    ps = np.where(ws > 0, np.maximum(ps, np.where(bo_v, 0.0, 1.0)), 0.0).astype(np.float32)
    den = pv + ps
    det = np.where(den > 0, (pv * dvc + ps * ds) / np.maximum(den, 1e-30), np.nan)
    cob = np.where(den > 0, np.where(pv > ps, 1, 2), 0).astype(np.uint8)
    m = np.isfinite(det)
    log(f"  cobertura: {100 * m.mean():.1f} % del rectangle  ·  "
        f"mana la Vixen al {100 * (cob == 1).mean():.1f} %, la Sony al {100 * (cob == 2).mean():.1f} %")

    yy = np.arange(Hc, dtype=np.float32)[:, None] - Hc / 2
    xx = np.arange(Wc, dtype=np.float32)[None, :] - Wc / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    import filtres as F
    # ⛔ El domini de la porta G arriba fins a 5 R☉ i no més. Mesurat:
    # l'amplitud del passa-alt baixa net de **0,0222 a 1,24 R☉** fins a un terra
    # de **0,000133 a 4,3–4,9** —cent seixanta vegades menys— i a partir d'allà
    # torna a pujar lentament. Aquell terra **és el soroll**, i el que puja
    # després no és corona. Amb el domini fins a 8 R☉ la G falla amb 1,545, i és
    # ella qui ho diu.
    R_MAX_G = 5.0
    r_a, amp, pes_a = F.perfil_amplitud(np.nan_to_num(det), m.astype(np.float32),
                                        rr, 1.2, R_MAX_G, 80)
    gG = P.porta_g_envolupant(r_a, amp, pes_a)
    r_t, amp_t, _ = F.perfil_amplitud(np.nan_to_num(det), m.astype(np.float32), rr, 1.2, 8.0, 90)
    i_terra = int(np.nanargmin(amp_t))
    gR = P.porta_rectangle(det)
    log(f"  G {gG['estat']} (excés {gG.get('exces_maxim')})  ·  rectangle {gR['estat']}")
    # ⛔ Cap costura: el quocient d'amplitud entre les zones on mana l'un i l'altre
    vora = m & (np.abs(cv2.GaussianBlur((cob == 1).astype(np.float32), (0, 0), 8)
                       - (cob == 1)) > 0.05)
    log(f"  frontera Vixen/Sony: {100 * vora.mean():.2f} % del rectangle, "
        f"amplitud a banda i banda "
        f"{np.median(np.abs(det[m & (cob == 1)])):.5f} / {np.median(np.abs(det[m & (cob == 2)])):.5f}")

    dst = OUT_ARREL / "dos_trens_filtrats"
    dst.mkdir(parents=True, exist_ok=True)
    np.save(dst / "DETALL_ln.npy", det.astype(np.float32))
    np.save(dst / "QUI_MANA.npy", cob)
    tifffile.imwrite(dst / "DETALL_ln_float32.tif", det.astype(np.float32))
    prev = PREV_ARREL
    prev.mkdir(parents=True, exist_ok=True)
    lo, hi = np.nanpercentile(det, [0.5, 99.5])
    g = np.clip((np.nan_to_num(det) - lo) / max(hi - lo, 1e-9), 0, 1)
    png = prev / "fase3_dos_trens.png"
    cv2.imwrite(str(png), (np.where(m, g, 0.0) * 65535).astype(np.uint16))
    log(f"  → {png.name}")

    res = {"fase": "3_filtres_dos_trens", "llenc": [int(Wc), int(Hc)],
           "combinacio": ("rampa de %g px a la vora de la petjada de la Vixen; mana la "
                          "Vixen on té dada perquè mostreja 1,49× més fi i integra 24,975 s "
                          "amb 68 fotogrames contra 14. ⛔ NO per inversa de variància: el "
                          "remostreig de la Sony li infla el Σw un factor ~2,2 que no és "
                          "senyal/soroll" % AMPLE_RAMPA_PX),
           "per_que_no_hi_ha_problema_d_escala": (
               "un passa-alt sobre ln I lliura contrast RELATIU, i un factor multiplicatiu és "
               "una constant additiva en logaritme que el passa-alt treu. El ±14 % d'incertesa "
               "de l'escala absoluta (§15) NO afecta aquest producte."),
           "cobertura_percent": round(100 * float(m.mean()), 3),
           "mana_vixen_percent": round(100 * float((cob == 1).mean()), 3),
           "mana_sony_percent": round(100 * float((cob == 2).mean()), 3),
           "amplitud_mediana": {"on_mana_vixen": float(np.median(np.abs(det[m & (cob == 1)]))),
                                "on_mana_sony": float(np.median(np.abs(det[m & (cob == 2)])))},
           "porta_g": gG, "porta_rectangle": gR, "previsualitzacio": str(png),
           "domini_de_la_porta_g_rsol": [1.2, R_MAX_G],
           "terra_de_soroll": {"amplitud": float(amp_t[i_terra]),
                               "radi_rsol": round(float(r_t[i_terra]), 3),
                               "amplitud_a_1_24_rsol": float(amp_t[0]),
                               "contrast_dinamic": round(float(amp_t[0] / amp_t[i_terra]), 1),
                               "nota": ("el terra és el soroll; el detall del producte val "
                                        "fins on l'amplitud hi arriba, no més enllà")},
           "fitxers": {q.name: {"bytes": q.stat().st_size, "sha256": C.sha256(q)}
                       for q in sorted(dst.iterdir())}}
    desa("fase3_dos_trens.json", res)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="etapa", required=True)
    p0 = sub.add_parser("f0")
    p0.add_argument("--cel", choices=["anell", "model"], default="anell")
    sub.add_parser("f1")
    pc = sub.add_parser("coherencia")
    pc.add_argument("--exposicions", choices=["fisiques", "manifest"], default="fisiques")
    pc.add_argument("--flat", choices=["si", "no"], default="si")
    pc.add_argument("--centre", choices=["efemerides", "limbe"], default="efemerides")
    sub.add_parser("coherencia_sony")
    p2 = sub.add_parser("f2")
    p2.add_argument("--exposicions", choices=["fisiques", "manifest"], default="fisiques")
    p2.add_argument("--flat", choices=["si", "no"], default="si")
    # ⛔ Per defecte, EFEMÈRIDES. El centre del limbe MESURAT està 3,7 px (8,0 ″)
    # desplaçat, i **els dos trens hi coincideixen a 0,21 px**: no és un defecte
    # d'un instrument, és què vol dir «el centre del limbe» quan la corona
    # asimètrica vessa per damunt. El detall és a research/99 §9.
    p2.add_argument("--centre", choices=["efemerides", "limbe"], default="efemerides")
    p2.add_argument("--cel", choices=["anell", "model"], default="anell")
    # ⛔ La coherència de transparència per fotograma: és l'ARREL de les costures
    # de fusió HDR que Pere va marcar el 24-08-2026. Vegeu `fase_coherencia`.
    p2.add_argument("--coherencia", default=None,
                    help="JSON de fase_coherencia amb els factors per fotograma")
    pp = sub.add_parser("portes")
    pp.add_argument("etiqueta")
    pl = sub.add_parser("llenc")
    pl.add_argument("etiqueta")
    ps = sub.add_parser("sony")
    ps.add_argument("--cel", choices=["anell", "model"], default="anell")
    ps.add_argument("--coherencia", default=None,
                    help="JSON de coherencia_sony amb els factors per fotograma")
    sub.add_parser("cel_sony")
    sub.add_parser("cel")
    pd = sub.add_parser("dos_trens")
    pd.add_argument("etiqueta")
    pf = sub.add_parser("filtres")
    pf.add_argument("etiqueta")
    pfs = sub.add_parser("filtres_sony")
    pfs.add_argument("--cel", choices=["anell", "model", "color"], default="anell")
    pfs.add_argument("--coh", action="store_true",
                     help="fer servir el compost Sony amb coherència aplicada")
    pdf = sub.add_parser("dos_trens_filtrats")
    pdf.add_argument("etiqueta")
    a = ap.parse_args()
    {"f0": fase0, "f1": fase1, "coherencia": fase_coherencia,
     "coherencia_sony": fase_coherencia_sony, "f2": fase2,
     "portes": fase_portes,
     "llenc": fase_llenc, "sony": fase_sony, "cel": fase_cel,
     "cel_sony": fase_cel_sony,
     "dos_trens": fase_dos_trens, "filtres": fase_filtres,
     "filtres_sony": fase_filtres_sony,
     "dos_trens_filtrats": fase_dos_trens_filtrats}[a.etapa](a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
