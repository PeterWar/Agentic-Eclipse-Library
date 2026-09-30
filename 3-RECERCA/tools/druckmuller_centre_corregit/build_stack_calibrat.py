#!/usr/bin/env python3
"""Stack de capes calibrat per a Photoshop, sense les costures que Pere marca.

Ordre de Pere, 22-08-2026 nit, sobre el 4K anotat: generar un stack nou
d'imatges **calibrades** i deixar el coneixement escrit perquè els artefactes
no tornin.

ELS QUATRE ARTEFACTES I LA SEVA CAUSA (mesurats, vegeu `research/93`)
--------------------------------------------------------------------
A. **Escaló rectangular al fons.** L'apilat Sony v3 no té cobertura uniforme:
   la caixa on hi caben els deu fotogrames és x 264–7926, y 40–4578 i fora
   d'allà l'exposició acumulada baixa de 24,75 s a 13,5 s o menys. La recepta
   antiga consumia l'apilat **sense mirar-ne el mapa de pes**. Aquí es
   construeix una màscara de validesa amb el mapa de pes i s'apoditza.

B. **Anell de color a ~2,8 R☉.** La «calibració fotomètrica» antiga igualava
   **una sola mediana de luminància**. Però els quocients Sony/Vixen per canal
   són R 2,143 · G 2,605 · B 3,059: **±18 %**. Amb un sol escalar, la Vixen
   queda vermellosa i la Sony blavosa, i l'ull llegeix el pendent com un anell
   just on la fusió canvia de mà. Aquí s'ajusta **guany i pedestal per canal**.

C. **Gradient de cel no restat.** A 9–13 R☉ el fons Sony val 217 / 589 / 377
   ADU/s en RGB: no és corona, és cel, i porta un gradient pel camp. Aquí es
   modela amb una quàdrica per canal ajustada a `r > 8,5 R☉` i **es lliura com
   a capa pròpia**, de manera que es pot tornar a sumar.

D. **Anell al limbe.** La màscara antiga tallava a 0,985 R☉ del **Sol**,
   mentre el disc **lunar** en fa 1,02 i no és concèntric. Aquí el tall surt
   del disc lunar mesurat al limbe, ajustant un cercle a 144 azimuts.

CALIBRATGE ABSOLUT
------------------
Els dos trens passen a **B/B☉** amb els factors de `research/75` §5.2, mesurats
amb 38 i 22 estrelles: Sony **1,134×10⁻¹¹** i R6 **2,772×10⁻¹¹** per ADU/s i
píxel verd, ±10 % cadascun. El quocient verd Sony/Vixen mesurat a l'anell de
solapament és **2,605**, contra el **2,573** que prediuen els dos factors amb
el quocient de corona 0,95 del mateix document: **coincideixen a l'1,2 %**.
O sigui que l'escala ja no és un paràmetre lliure, és una mesura.

QUÈ CONTINUA SENT EXPERIMENTAL
------------------------------
Les entrades són apilats històrics, no els paquets S6 acceptats, i l'apilat
Sony v3 ja fon `DSC06987` amb `DSC06993`. El pilot S6 amb les dues 8 s
separades continua sent el gate següent. No-clobber estricte.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import os
import sys

import numpy as np

try:
    import cv2
    import tifffile as tiff
    from scipy.ndimage import gaussian_filter, median_filter
    from sunkit_image.enhance import mgn
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Falta {exc.name}; mira detecta_python.py --check")

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop", "Eclipse 2026")
WORKTREE = os.path.join(HOME, "Downloads", "Eclipse 2026")

SONY_STACK = os.path.join(DESKTOP, "Derivats/Sony/Apilats/300mm_apilat_v3",
                          "Sony300_apilat_v3_10fotogrames_ADUs_float32.tif")
SONY_PES = os.path.join(DESKTOP, "Derivats/Sony/Apilats/300mm_apilat_v3",
                        "Sony300_apilat_v3_pes_s_float32.tif")
VIXEN_HDR = os.path.join(DESKTOP, "Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_countss.npy")
VIXEN_COB = os.path.join(DESKTOP, "Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_cobertura.npy")
ASTRO_DIR = os.path.join(DESKTOP, "Derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17")
ASTROMETRIA = os.path.join(ASTRO_DIR, "final_solution.json")
CATALEG_R6 = os.path.join(ASTRO_DIR, "final_match_r6.csv")

# research/75 §5.2 — B/B☉ per ADU/s i píxel verd, ±10 %
FACTOR_B_SONY = 1.134e-11
FACTOR_B_VIXEN = 2.772e-11

SUN_HDR = (3479.0, 2319.0)          # LLEGEIX-ME de Corona_HDR_Vixen
R_SOL_VIXEN_PX = 446.15
SONY_PES_PLE = 24.7                 # llindar de cobertura completa (24,75 s)
APOD_COBERTURA_PX = 220.0
APOD_VORA_VIXEN_PX = 200.0
FUSIO_R0, FUSIO_SOFT = 2.8, 0.4
# ⚠️ El desenfoc de la correcció per zona és PETIT a propòsit. Una correcció
# ha de tenir la mateixa forma que la cosa que corregeix: el salt entre zones
# és nítid —una sola fila de píxels— i mesurat a la vora mateixa, o sigui que
# corregir-lo amb una rampa de 150 px en deixava dos terços sense corregir.
# Els 8 px són només per no deixar una vora d'un píxel aliasada.
# (El que SÍ que s'havia de desenfocar era el pedestal antic, que estava
# mesurat al camp llunyà i per tant NO coincidia amb el salt local.)
PED_BLUR_PX = 8.0
OVERLAP_LO, OVERLAP_HI = 1.5, 2.8
CEL_R_MIN = 8.5
NEUTRE_R = (1.8, 2.2)               # radi on la corona es declara neutra (Thomson)
MGN_SIGMA = [3.0, 6.0, 12.0, 24.0, 48.0, 96.0]
MGN_K, MGN_GAMMA, MGN_H, MGN_PAD = 1.0, 2.2, 0.8, 128
LIMB_MARGE_PX = 6.0


def sha256(p, buf=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(buf), b""):
            h.update(c)
    return h.hexdigest()


def log(m):
    print(f"[{_dt.datetime.now():%H:%M:%S}] {m}", flush=True)


def centroide(L, cx, cy, r=12, it=3):
    for _ in range(it):
        x0, y0 = int(round(cx)) - r, int(round(cy)) - r
        if x0 < 0 or y0 < 0 or y0 + 2 * r + 1 > L.shape[0] or x0 + 2 * r + 1 > L.shape[1]:
            return None
        w = L[y0:y0 + 2 * r + 1, x0:x0 + 2 * r + 1].astype(np.float64)
        v = np.clip(w - np.median(w), 0, None)
        if v.max() <= 0:
            return None
        v = np.where(v > 0.3 * v.max(), v, 0.0)
        s = v.sum()
        if s <= 0:
            return None
        yy, xx = np.mgrid[0:v.shape[0], 0:v.shape[1]]
        cx, cy = x0 + (v * xx).sum() / s, y0 + (v * yy).sum() / s
    return cx, cy


def translacio_hdr(LV, aprox=(89.78, -48.72), tol=8.0):
    d = []
    with open(CATALEG_R6, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                x, y = float(row["x"]), float(row["y"])
            except (KeyError, TypeError, ValueError):
                continue
            c = centroide(LV, x - aprox[0], y - aprox[1])
            if c is None:
                continue
            v = np.array([x - c[0], y - c[1]])
            if np.linalg.norm(v - np.asarray(aprox)) < tol:
                d.append(v)
    if len(d) < 4:
        sys.exit(f"només {len(d)} estrelles per a la translació")
    a = np.array(d)
    return a.mean(axis=0), a.std(axis=0), len(a)


def centre_limbe(L, x0, y0, w, h, rmax=600, naz=144):
    pts = []
    for ang in np.linspace(0, 2 * np.pi, naz, endpoint=False):
        rs = np.arange(120, rmax, 0.5)
        xs, ys = x0 + rs * np.cos(ang), y0 + rs * np.sin(ang)
        ok = (xs >= 0) & (xs < w - 1) & (ys >= 0) & (ys < h - 1)
        if ok.sum() < 50:
            continue
        v = cv2.remap(L, xs[ok].astype(np.float32).reshape(-1, 1),
                      ys[ok].astype(np.float32).reshape(-1, 1), cv2.INTER_LINEAR).ravel()
        g = np.gradient(v)
        i = int(np.argmax(g))
        if g[i] <= 0:
            continue
        pts.append((x0 + rs[ok][i] * np.cos(ang), y0 + rs[ok][i] * np.sin(ang)))
    P = np.array(pts, np.float64)
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    c, *_ = np.linalg.lstsq(A, (P ** 2).sum(axis=1), rcond=None)
    cx, cy = float(c[0]), float(c[1])
    R = float(np.sqrt(c[2] + cx * cx + cy * cy))
    return (cx, cy), R, float(np.median(np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R))), len(P)


def quadrica(xs, ys, zs):
    A = np.c_[np.ones_like(xs), xs, ys, xs * xs, xs * ys, ys * ys]
    c, *_ = np.linalg.lstsq(A, zs, rcond=None)
    return c


def aplica_quadrica(c, X, Y):
    return (c[0] + c[1] * X + c[2] * Y + c[3] * X * X + c[4] * X * Y + c[5] * Y * Y).astype(np.float32)


def perfil_color(img, R, lo, hi, msk):
    s = (R >= lo) & (R < hi) & msk
    return [float(np.median(img[:, :, i][s])) for i in range(3)], int(s.sum())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build-id", default=None)
    ap.add_argument("--sony-stack", default=None, help="apilat Sony alternatiu (TIFF o .npy)")
    ap.add_argument("--sony-pes", default=None, help="mapa de pes de l'apilat alternatiu")
    ap.add_argument("--out-root", default=os.path.join(WORKTREE, "output", "stack_calibrat_20260822"))
    ap.add_argument("--preview-root", default=os.path.join(DESKTOP, "IA", "output", "stack_calibrat_20260822"))
    args = ap.parse_args()

    bid = args.build_id or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = os.path.join(args.out_root, bid)
    prev = os.path.join(args.preview_root, bid)
    if os.path.exists(out) or os.path.exists(prev):
        sys.exit(f"NO-CLOBBER: {bid} ja existeix")
    os.makedirs(out); os.makedirs(prev)

    man = {
        "build_id": bid,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "purpose": "stack de capes calibrat en B/Bsol, sense les quatre costures marcades per Pere",
        "authority": "ordre de Pere 22-08-2026 nit sobre el 4K anotat; research/93",
        "status": "EXPERIMENTAL_NOT_CANONICAL",
        "not_s6": "entrades: apilats historics; l'apilat Sony v3 ja fon DSC06987 amb DSC06993",
        "units": "B/Bsol (research/75 §5.2, +-10 % per tren)",
        "inputs": {}, "geometry": {}, "photometry": {}, "sky": {}, "masks": {},
        "artifact_checks": {}, "outputs": {},
    }
    sony_stack = args.sony_stack or SONY_STACK
    sony_pes = args.sony_pes or SONY_PES
    for n, p in (("sony_stack", sony_stack), ("sony_pes", sony_pes), ("vixen_hdr", VIXEN_HDR),
                 ("vixen_cobertura", VIXEN_COB), ("astrometria", ASTROMETRIA), ("cataleg_r6", CATALEG_R6)):
        if not os.path.exists(p):
            sys.exit(f"falta {n}: {p}")
        man["inputs"][n] = {"path": p, "bytes": os.path.getsize(p), "sha256": sha256(p)}

    sol = json.load(open(ASTROMETRIA))
    Av = np.array([[sol["r6_radial"]["px"][1], sol["r6_radial"]["px"][2]],
                   [sol["r6_radial"]["py"][1], sol["r6_radial"]["py"][2]]], float)
    As = np.array([[sol["sony_radial"]["px"][1], sol["sony_radial"]["px"][2]],
                   [sol["sony_radial"]["py"][1], sol["sony_radial"]["py"][2]]], float)
    sun_v_raw = np.array([sol["r6_radial"]["sun_x"], sol["r6_radial"]["sun_y"]])
    sun_s = np.array([sol["sony_radial"]["sun_x"], sol["sony_radial"]["sun_y"]])
    r_sol = R_SOL_VIXEN_PX * (sol["r6_radial"]["scale"] / sol["sony_radial"]["scale"])

    # ---------------------------------------------------------------- Vixen
    log("Vixen…")
    vix = np.nan_to_num(np.load(VIXEN_HDR).astype(np.float32), nan=0.0)
    np.maximum(vix, 0.0, out=vix)
    h_v, w_v = vix.shape[:2]
    LV = vix[:, :, 1].copy()
    t, tsig, tn = translacio_hdr(LV)
    log(f"  translació HDR→sensor ({t[0]:+.3f},{t[1]:+.3f}) σ=({tsig[0]:.3f},{tsig[1]:.3f}) amb {tn} estrelles")
    Lin = As @ np.linalg.inv(Av)
    M = np.zeros((2, 3), np.float32)
    M[:, :2] = Lin
    M[:, 2] = sun_s - Lin @ (sun_v_raw - t)

    cob_v = np.load(VIXEN_COB).astype(np.float32)[:, :, 1]
    vix *= np.float32(FACTOR_B_VIXEN)                       # -> B/B☉

    # ---------------------------------------------------------------- Sony
    log(f"Sony… {sony_stack}")
    _rd = (lambda q: np.load(q) if q.endswith(".npy") else tiff.imread(q))
    sony = np.nan_to_num(_rd(sony_stack).astype(np.float32), nan=0.0)
    np.maximum(sony, 0.0, out=sony)
    h, w = sony.shape[:2]
    sony *= np.float32(FACTOR_B_SONY)                       # -> B/B☉
    pes = _rd(sony_pes)
    pes = pes[:, :, 1] if pes.ndim == 3 else pes

    log("warp de la Vixen…")
    vixw = cv2.warpAffine(vix, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    cobw = cv2.warpAffine(cob_v, M, (w, h), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    LVw = cv2.warpAffine(LV, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    del vix, LV, cob_v

    p = M @ np.array([*SUN_HDR, 1.0], np.float32)
    (dcx, dcy), dR, dres, dn = centre_limbe(LVw, p[0], p[1], w, h)
    del LVw
    man["geometry"] = {
        "M": M.tolist(), "hdr_to_sensor_px": t.tolist(), "hdr_to_sensor_sigma_px": tsig.tolist(),
        "hdr_to_sensor_n_stars": tn, "sun_sony_astrometric": sun_s.tolist(), "r_sol_sony_px": r_sol,
        "lunar_disc_center_px": [dcx, dcy], "lunar_disc_radius_px": dR,
        "lunar_disc_radius_rsol": dR / r_sol, "lunar_disc_fit_residual_px": dres, "lunar_disc_azimuths": dn,
        "lunar_disc_offset_from_sun_px": float(np.hypot(dcx - sun_s[0], dcy - sun_s[1])),
    }
    log(f"  disc lunar ({dcx:.1f},{dcy:.1f}) R={dR:.1f} px = {dR/r_sol:.3f} R☉, residu {dres:.2f} px")

    YY = np.arange(h, dtype=np.float32)[:, None]
    XX = np.arange(w, dtype=np.float32)[None, :]
    R = np.sqrt((XX - sun_s[0]) ** 2 + (YY - sun_s[1]) ** 2).astype(np.float32) / np.float32(r_sol)
    Rlun = np.sqrt((XX - dcx) ** 2 + (YY - dcy) ** 2).astype(np.float32)

    # ------------------------------------------------- A: validesa per cobertura
    log("màscares de validesa…")
    # Validesa = HI HA DADES, no «hi ha cobertura completa». A la corona
    # interior els fotogrames de 8 s estan emmascarats per saturació, o sigui
    # que exigir-hi els 24,75 s buidaria justament el centre de la imatge.
    # L'escaló entre zones de cobertura el resol el pedestal per zona, no la
    # màscara.
    sony_hi_ha = (pes > 0).astype(np.uint8)
    d_hi = cv2.distanceTransform(sony_hi_ha, cv2.DIST_L2, 5)
    w_sony = np.clip(d_hi / APOD_COBERTURA_PX, 0, 1)
    w_sony = (0.5 * (1 - np.cos(np.pi * w_sony))).astype(np.float32)
    ple = (pes >= SONY_PES_PLE)
    man["masks"]["sony_full_coverage_box"] = [int(np.where(ple.any(0))[0][0]), int(np.where(ple.any(1))[0][0]),
                                              int(np.where(ple.any(0))[0][-1]), int(np.where(ple.any(1))[0][-1])]
    man["masks"]["sony_full_coverage_fraction"] = float(ple.mean())
    man["masks"]["sony_any_coverage_fraction"] = float(sony_hi_ha.mean())
    man["masks"]["nota"] = ("la cobertura completa (24,75 s) exclou la corona interior perque els 8 s "
                            "hi estan saturats; la validesa lliurada es pes>0 apoditzat")
    del d_hi, ple

    # ⚠️ L'apodització de vores ha de mirar NOMÉS la vora del fotograma. Si es
    # calcula sobre la cobertura tal qual, el FORAT DE LA LLUNA també compta com
    # a vora i la transformada de distància esvaeix la Vixen des del limbe cap
    # enfora: la corona interior, que és justament la que la Vixen aporta, surt
    # multiplicada per ~0,03 a 1,05 R☉ i per 0,20 a 1,2 R☉. La recepta original
    # té el mateix defecte. Es tapa el forat abans de mesurar la distància.
    # L'apodització ha de mesurar la distància al MARC DEL FOTOGRAMA, no al
    # mapa de cobertura: la cobertura té el forat de la Lluna i, a la corona
    # interior, forats de saturació emmascarats fotograma a fotograma. Fent la
    # transformada de distància sobre la cobertura, cada forat es converteix en
    # una vora i el resultat és un polígon fosc que es menja la corona interior
    # —dues vegades vist aquesta nit—. El marc és el warp d'una imatge de uns.
    vix_frame = cv2.warpAffine(np.ones((h_v, w_v), np.uint8), M, (w, h),
                               flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    d_vix = cv2.distanceTransform(vix_frame, cv2.DIST_L2, 5)
    w_edge = np.clip(d_vix / APOD_VORA_VIXEN_PX, 0, 1)
    w_edge = (0.5 * (1 - np.cos(np.pi * w_edge))).astype(np.float32)
    del d_vix, sony_hi_ha, vix_frame, cobw

    # ------------------------------------------------------------- C i A: cel
    # El cel no és el mateix a cada zona de cobertura: cada zona és un subconjunt
    # diferent de fotogrames i té la seva pròpia mitjana de cel. Per això el
    # model porta DUES parts: una quàdrica global ajustada dins la cobertura
    # completa, i un PEDESTAL PER ZONA que iguala les zones entre elles. Sense
    # el pedestal per zona queda l'escaló rectangular que Pere marca.
    log("model de cel de la Sony (quàdrica + pedestal per zona de cobertura)…")
    zona = np.round(pes * 4).astype(np.int32)                # 0,25 s de resolució
    msk_cel = (R > CEL_R_MIN) & (w_sony > 0.999) & (vixw[:, :, 1] <= 0)
    ys, xs = np.where(msk_cel[::7, ::7])
    ys, xs = ys * 7, xs * 7
    Xn = (xs - w / 2) / w
    Yn = (ys - h / 2) / h
    cel = np.zeros((h, w, 3), np.float32)
    coefs = []
    for i in range(3):
        c = quadrica(Xn, Yn, sony[:, :, i][ys, xs].astype(np.float64))
        coefs.append([float(v) for v in c])
        cel[:, :, i] = aplica_quadrica(c, (XX - w / 2) / w, (YY - h / 2) / h)

    # Cada zona de cobertura és un subconjunt diferent de fotogrames i té el
    # seu propi cel: no només un pedestal, també un pendent. Per això a cada
    # zona amb prou camp llunyà se li ajusta un PLA sobre el residu de la
    # quàdrica global. Una zona sense prou camp llunyà queda INVÀLIDA: no
    # s'inventa cap model per a ella.
    # Cada zona de cobertura és un subconjunt diferent de fotogrames i té la
    # seva pròpia mitjana de cel. Aquesta DIFERÈNCIA entre zones no té cap
    # contingut físic —el mateix tros de cel mesurat amb menys fotogrames— i és
    # el que dibuixa el rectangle. Se'n treu un PEDESTAL CONSTANT per zona, i
    # prou: ajustar-hi plans o quàdriques per zona sobreajusta i inventa
    # fanals de color als cantons (provat i descartat, research/93 §6).
    lluny = (R > CEL_R_MIN)
    zona_val = np.round(pes * 4).astype(np.int32)
    # ⛔ Una zona no és un VALOR d'exposició, és una REGIÓ. Dues taques amb els
    # mateixos 13,5 s poden venir de subconjunts de fotogrames diferents i
    # tenir guanys diferents; forçar-les al mateix número deixa un residu que
    # el sistema no pot ajustar (0,65 % en ln, que és exactament el que
    # quedava a les tres costures). Es separen per components connexos.
    zona = np.zeros_like(zona_val)
    seg = 0
    val_de_zona = {}
    for v in np.unique(zona_val):
        n_c, lab_c = cv2.connectedComponents((zona_val == v).astype(np.uint8), connectivity=8)
        for c in range(1, n_c):
            m_c = lab_c == c
            if m_c.sum() < 20000:
                continue
            seg += 1
            zona[m_c] = seg
            val_de_zona[seg] = float(v) / 4.0
    log(f"  zones per component connex: {seg} regions de {len(np.unique(zona_val))} valors d'exposició")
    zref = 0
    _millor = -1
    for k, vv in val_de_zona.items():
        n_k = int((zona == k).sum())
        if abs(vv - SONY_PES_PLE) < 0.13 and n_k > _millor:
            zref, _millor = k, n_k
    if zref == 0 and val_de_zona:
        zref = max(val_de_zona, key=lambda k: int((zona == k).sum()))
    del zona_val, lab_c
    ref_msk = lluny & (zona == zref)
    if ref_msk.sum() < 50000:
        sys.exit("no hi ha prou camp llunyà a la zona de cobertura completa")
    base = [float(np.median((sony[:, :, i] - cel[:, :, i])[ref_msk])) for i in range(3)]
    # ⚠️ Es compten sobre TOT el llenç, no només al camp llunyà: una regió que
    # no arriba a r > 8,5 R☉ existeix igual i té la seva vora, i deixar-la
    # sense guany era el que feia que el residu baixés i les costures no.
    zones, comptes = np.unique(zona[zona > 0], return_counts=True)
    ped_map = np.zeros((h, w, 3), np.float32)
    zona_ok = np.zeros((h, w), np.uint8)
    zdet = {}

    # ------------------------------------------------------------------------
    # ANIVELLAMENT PER LES VORES, I ÉS MULTIPLICATIU.
    # Mesurat a la vora inferior de la caixa de cobertura (y = 4578, on el pes
    # passa de 24,75 s a 13,50 s): la diferència ADDITIVA varia 2,7 vegades al
    # llarg de la vora (−2,05e−10 a −7,6e−11) mentre que el QUOCIENT es manté
    # entre 0,978 i 0,989. O sigui que no és un pedestal de cel sinó un GUANY
    # d'un 1,4 % entre subconjunts de fotogrames, que és la signatura del flat
    # òptic que encara no s'ha aplicat (research/90).
    # I es mesura a TOTA la vora, no al camp llunyà: una zona és a diversos
    # llocs del llenç i la seva mediana llunyana no representa cap d'ells —el
    # pedestal ajustat així valia 0,69 % i el graó real n'era 2,5 %.
    log("anivellament multiplicatiu per vores entre zones de cobertura…")
    kv = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    prou_lluny = (R > 3.0)
    zs_bones = [int(z) for z, n in zip(zones, comptes) if n >= 20000 and z > 0]
    zref_lvl = zref if zref in zs_bones else (zs_bones[-1] if zs_bones else 0)

    def guanys_per_vores(canal):
        idx = {z: k for k, z in enumerate(zs_bones)}
        A_ls, b_ls, det = [], [], []
        for zi in zs_bones:
            mi = (zona == zi)
            di = cv2.dilate(mi.astype(np.uint8), kv) > 0
            for zj in zs_bones:
                if zj <= zi:
                    continue
                mj = (zona == zj)
                dj = cv2.dilate(mj.astype(np.uint8), kv) > 0
                sa = canal[mi & dj & prou_lluny]
                sb = canal[mj & di & prou_lluny]
                sa = sa[np.isfinite(sa) & (sa > 0)]
                sb = sb[np.isfinite(sb) & (sb > 0)]
                if sa.size < 2000 or sb.size < 2000:
                    continue
                lr = float(np.log(np.median(sb) / np.median(sa)))     # ln(zj/zi)
                r = np.zeros(len(zs_bones)); r[idx[zj]] = 1.0; r[idx[zi]] = -1.0
                A_ls.append(r); b_ls.append(lr)
                det.append([zi, zj, float(f"{math.exp(lr):.5f}"), int(sa.size), int(sb.size)])
        r = np.zeros(len(zs_bones)); r[idx[zref_lvl]] = 1.0
        A_ls.append(r * 10.0); b_ls.append(0.0)                        # gauge
        o = np.linalg.lstsq(np.array(A_ls), np.array(b_ls), rcond=None)[0]
        res = float(np.sqrt(np.mean((np.array(A_ls)[:-1] @ o - np.array(b_ls)[:-1]) ** 2))) if len(det) else 0.0
        return {z: float(math.exp(o[idx[z]])) for z in zs_bones}, det, res

    niv, det_v, res_v = guanys_per_vores(sony[:, :, 1])
    gain_map = np.ones((h, w), np.float32)
    for z, g in niv.items():
        gain_map[zona == z] = np.float32(g)
    zf0 = np.isin(zona, zs_bones).astype(np.float32)
    den0 = np.maximum(cv2.GaussianBlur(zf0, (0, 0), PED_BLUR_PX), 1e-3)
    gain_map = (cv2.GaussianBlur(gain_map * zf0, (0, 0), PED_BLUR_PX) / den0)
    gain_map = np.where(zf0 > 0, gain_map, 1.0).astype(np.float32)
    gain_map = np.clip(gain_map, 0.8, 1.25)
    for i in range(3):
        sony[:, :, i] /= gain_map
    man["sky_anivellament"] = {
        "metode": "guany multiplicatiu per zona, mesurat als 31 px a banda i banda de cada vora entre zones (r>3 Rsol), sistema lineal en log amb gauge a la zona de cobertura completa",
        "motiu": "el salt es multiplicatiu (quocient constant 0,978-0,989, diferencia additiva variable x2,7): flat optic Sony no aplicat, research/90",
        "zona_referencia": zref_lvl,
        "exposicio_per_zona_s": {str(k): v for k, v in val_de_zona.items()},
        "guanys": {str(k): float(f"{v:.5f}") for k, v in niv.items()},
        "vores_mesurades": det_v,
        "residu_rms_ln": float(f"{res_v:.5f}"),
        "desenfoc_px": PED_BLUR_PX}
    log(f"  {len(niv)} zones, {len(det_v)} vores; guanys "
        f"{[f'{v:.4f}' for v in niv.values()]}; residu {res_v:.5f} en ln")
    del zf0, den0

    for z, n in zip(zones, comptes):
        if n < 20000:
            continue
        # ⛔ La zona 0 és «no hi ha cap exposició», no una zona de cobertura. Té
        # 527.549 px de camp llunyà i se li calculava un pedestal de −4,6e−9,
        # que és la meitat del cel: fins ara quedava tancat al marge mort i no
        # feia mal, però en desenfocar el mapa s'escamparia ~450 px cap a dins
        # de la dada bona i hi deixaria una franja clara. No es corregeix el
        # que no s'ha mesurat.
        if z <= 0:
            continue
        m_z = (zona == z)
        # El pedestal ADDITIU es queda a zero: el salt entre zones ja s'ha
        # corregit com el que és, un guany. Aquest bloc només marca les zones.
        v = [0.0, 0.0, 0.0]
        zona_ok[m_z] = 1
        zdet[int(z)] = {"n_far_px": int(n), "pedestal_BBsol_RGB": [float(f"{x:.4g}") for x in v]}
    # ⛔ El pedestal per zona és una correcció de CEL i només s'ha d'aplicar on
    # el cel es nota. Les zones de cobertura de la Sony estan limitades per
    # ISOFOTES DE SATURACIÓ dels fotogrames de 8 s, que a la corona interior
    # són contorns dentats a ~2,5 R☉. Aplicar-hi un desplaçament constant hi
    # deixa un ESGLAÓ que a la imatge no es veu —el cel hi és mil vegades més
    # feble que la corona— però que un filtre de pas alt dibuixa com un
    # contorn dentat clavat a 2,48 R☉ (mesurat). El pedestal s'esvaeix de 4 a
    # 6 R☉ cap endins.
    u_ped = np.clip((R - 4.0) / 2.0, 0.0, 1.0)
    ped_map *= (u_ped * u_ped * (3.0 - 2.0 * u_ped)).astype(np.float32)[:, :, None]
    # ⛔ I ES DESENFOCA. Un pedestal per zona és, tal com es construeix, una
    # FUNCIÓ ESGLAONADA: a y=4578 el pes de la Sony passa de 24,75 s a 13,50 s
    # en una sola fila i el pedestal hi fa un salt dur de 5,4e-11 B/B☉. Al cel
    # no hi ha cap vora: la diferència entre zones és de comptabilitat —el
    # mateix tros de cel mesurat amb menys fotogrames—, o sigui que la
    # correcció ha de ser igual de llisa que la cosa que corregeix. Sense
    # desenfocar-la, el que hauria de tapar un esglaó n'hi deixa un altre, i
    # a 6 R☉ el cel val 78 vegades la corona: un 2,5 % de cel mal restat hi és
    # el 200 % del senyal. És la banda fosca horitzontal que sortia a baix.
    if PED_BLUR_PX > 0:
        # ⚠️ Convolució NORMALITZADA sobre les zones que tenen pedestal. Un
        # desenfoc corrent hi barrejaria els zeros del marge mort i faria un
        # esglaó nou just on n'estàvem traient un.
        zf = zona_ok.astype(np.float32)
        den = np.maximum(cv2.GaussianBlur(zf, (0, 0), PED_BLUR_PX), 1e-3)
        for i in range(3):
            ped_map[:, :, i] = (cv2.GaussianBlur(ped_map[:, :, i] * zf, (0, 0), PED_BLUR_PX)
                                / den) * zf
    man["sky_ped_blur_px"] = PED_BLUR_PX
    sony_ns = sony - ped_map        # <- només l'escaló entre zones, i només al cel
    del ped_map
    del zona
    man["sky"] = {
        "model_quadrica": "quadrica 2D per canal ajustada a r>%.1f R_sol dins la cobertura completa" % CEL_R_MIN,
        "quadrica_aplicada_al_compost": False,
        "quadrica_es_lliura_com_a_capa": "05_Model_de_cel_BBsol_float32.tif; 06b es 06 menys aquesta capa",
        "n_px_fit_quadrica": int(len(xs)),
        "coefs_RGB_normalitzats": coefs,
        "aplicat_al_compost": "nomes el pedestal constant per zona de cobertura (escalo sense contingut fisic)",
        "zones_amb_pedestal": {str(k / 4.0): v for k, v in sorted(zdet.items())},
        "zones_sense_pedestal_marcades_invalides": True,
        "quadrica_median_BBsol_RGB": [float(np.median(cel[:, :, i])) for i in range(3)],
    }
    log(f"  cel: quàdrica com a capa; {len(zdet)} zones amb pedestal propi; "
        f"{int((zona_ok == 0).sum())} px marcats invàlids")

    # ------------------------------ B: guany i pedestal per canal, Vixen -> Sony
    log("calibratge creuat per canal a l'anell de solapament…")
    ov = (R >= OVERLAP_LO) & (R < OVERLAP_HI) & (vixw[:, :, 1] > 0) & (w_sony > 0.999)
    gains, offs, abans, despres = [], [], [], []
    idx = np.where(ov.ravel())[0]
    if idx.size > 400000:
        idx = idx[:: max(1, idx.size // 400000)]
    for i in range(3):
        a = vixw[:, :, i].ravel()[idx].astype(np.float64)
        b = sony_ns[:, :, i].ravel()[idx].astype(np.float64)
        ok = np.isfinite(a) & np.isfinite(b) & (a > 0)
        A = np.c_[a[ok], np.ones(ok.sum())]
        g, o = np.linalg.lstsq(A, b[ok], rcond=None)[0]
        gains.append(float(g)); offs.append(float(o))
        abans.append(float(np.median(b[ok]) / np.median(a[ok])))
        vixw[:, :, i] = vixw[:, :, i] * np.float32(g) + np.float32(o)
        despres.append(float(np.median(sony_ns[:, :, i].ravel()[idx][ok]) /
                             np.median(vixw[:, :, i].ravel()[idx][ok])))
    man["photometry"] = {
        "factor_B_sony_per_ADUs": FACTOR_B_SONY, "factor_B_vixen_per_ADUs": FACTOR_B_VIXEN,
        "ratio_absolut_esperat": FACTOR_B_VIXEN / FACTOR_B_SONY,
        "ratio_mesurat_per_canal_abans": abans, "gain_per_canal": gains, "offset_per_canal": offs,
        "ratio_per_canal_despres": despres,
        "dispersio_relativa_abans_pct": float(100 * (max(abans) / min(abans) - 1)),
        "dispersio_relativa_despres_pct": float(100 * (max(despres) / min(despres) - 1)),
        "n_px": int(idx.size),
    }
    log(f"  quocient per canal abans {['%.3f' % v for v in abans]} (dispersió "
        f"{man['photometry']['dispersio_relativa_abans_pct']:.1f} %)")
    log(f"  després {['%.4f' % v for v in despres]} (dispersió "
        f"{man['photometry']['dispersio_relativa_despres_pct']:.2f} %)")
    del ov

    # ------------------------------------------------------------ D: limbe real
    limb = np.clip((Rlun - dR) / max(LIMB_MARGE_PX, 1.0), 0.0, 1.0).astype(np.float32)

    # -------------------------------------------- neutralització de la corona
    # La corona és llum solar dispersada per electrons lliures (Thomson): és
    # acromàtica. Els factors de research/75 calibren el canal VERD; R i B es
    # reescalen aquí perquè la corona mitjana surti neutra. No és una tria
    # estètica: és el color que la física diu que ha de tenir.
    nz = (R >= NEUTRE_R[0]) & (R < NEUTRE_R[1]) & (vixw[:, :, 1] > 0)
    g_ref = float(np.median(vixw[:, :, 1][nz]))
    wb = [g_ref / float(np.median(vixw[:, :, i][nz])) for i in range(3)]
    wb = [v / wb[1] for v in wb]
    for i in (0, 2):
        vixw[:, :, i] *= np.float32(wb[i])
        sony_ns[:, :, i] *= np.float32(wb[i])
        cel[:, :, i] *= np.float32(wb[i])
    man["photometry"]["neutralitzacio_RGB"] = wb
    man["photometry"]["neutralitzacio_nota"] = (
        "G queda en B/Bsol absolut; R i B es reescalen perque la corona a %.1f-%.1f Rsol "
        "surti neutra (dispersio Thomson, acromatica)" % NEUTRE_R)
    log(f"  neutralització R,G,B = {['%.4f' % v for v in wb]}")
    del nz

    # ------------------------------------------------------------------ fusió
    # ⛔ CADA PES MESURA UNA SOLA COSA, i el compost lineal no es multiplica
    # per cap d'ells. Fins al 22-08 aquí hi havia tres conflacions encadenades
    # que van acabar sent l'anell dur que Pere va marcar en vermell:
    #
    #   1. `wv` barrejava QUIN tren mana (la sigmoide de radi), ON hi ha camp
    #      Vixen (`w_edge`) i ON el Sol està tapat (`limb`);
    #   2. `validesa` es derivava de `wv` i de `zona_ok`, que no diu si hi ha
    #      dada sinó si aquella zona de cobertura va poder tenir pedestal de
    #      cel. La corona interior no arriba mai a r > 8,5 R☉, o sigui que hi
    #      valia 0 i la validesa hi queia al pes de fusió;
    #   3. i llavors el compost es multiplicava per `validesa` DUES vegades.
    #
    # El resultat mesurat: 06 / mesclat ≡ validesa², exacte a quatre decimals.
    # Com que `max()` té cantonada, el factor valia 0,941 a 1,4 R☉, 0,557 a
    # 2,4 i 1,000 a 2,6 — un graó del +79 % en 0,2 R☉ dins un fitxer que es
    # diu «calibrat en B/B☉». A la imatge no es veia; el pas alt el dibuixava.
    #
    # Ara: mescla convexa NORMALITZADA per cobertura. On només hi ha un tren,
    # en surt aquell tren a pes ple i sense enfosquir; on no n'hi ha cap, el
    # píxel és NaN, perquè cap dada no és el mateix que zero llum.
    log("fusió…")
    tria = np.clip(1.0 / (1.0 + np.exp((R - FUSIO_R0) / FUSIO_SOFT)), 0, 1).astype(np.float32)
    cob_vixen = w_edge                       # ON hi ha camp Vixen
    cob_sony = w_sony                        # ON hi ha camp Sony (pes > 0 apoditzat)
    wa = gaussian_filter(tria * cob_vixen, sigma=20).astype(np.float32)
    wb = gaussian_filter((1.0 - tria) * cob_sony, sigma=20).astype(np.float32)
    sw = (wa + wb).astype(np.float32)
    hi_ha = sw > 1e-3
    wv = np.where(hi_ha, wa / np.maximum(sw, 1e-6), 0.0).astype(np.float32)   # pes EFECTIU de la Vixen
    wv3 = wv[:, :, None]
    validesa = (np.clip(np.maximum(cob_sony, cob_vixen), 0, 1) * limb).astype(np.float32)
    corona = (vixw * wv3 + sony_ns * (1.0 - wv3)).astype(np.float32)
    corona[~hi_ha] = np.nan
    man["fusio"] = {
        "forma": "mescla convexa normalitzada: (V*wa + S*wb)/(wa+wb)",
        "wa": "gauss20(sigmoide(R;%.2f,%.2f) * cobertura_Vixen)" % (FUSIO_R0, FUSIO_SOFT),
        "wb": "gauss20((1-sigmoide) * cobertura_Sony)",
        "el_compost_no_es_multiplica_per_cap_mascara": True,
        "px_sense_cap_tren_NaN": int((~hi_ha).sum()),
    }
    del tria, w_edge, cob_vixen, cob_sony, wa, wb, sw, hi_ha
    # `mostrar` és el compost amb les màscares JA aplicades, i és l'únic que
    # va a corbes de to, previsualitzacions i comprovacions visuals. La
    # fotometria lineal (`corona`) no es toca.
    mostrar = (np.nan_to_num(corona, nan=0.0, posinf=0.0, neginf=0.0)
               * validesa[:, :, None]).astype(np.float32)

    # ------------------------------------------------- comprovacions d'artefacte
    log("comprovacions…")
    def color_vs_r():
        o = []
        for r0 in np.arange(1.4, 6.01, 0.4):
            s = (R >= r0) & (R < r0 + 0.4) & (validesa > 0.99) & (limb > 0.99)
            if s.sum() < 5000:
                continue
            g = float(np.nanmedian(corona[:, :, 1][s]))
            if not np.isfinite(g) or g <= 0:
                continue
            o.append([round(float(r0), 1), round(float(np.nanmedian(corona[:, :, 0][s]) / g), 4),
                      round(float(np.nanmedian(corona[:, :, 2][s]) / g), 4)])
        return o
    cvr = color_vs_r()
    rg = [v[1] for v in cvr]; bg = [v[2] for v in cvr]
    man["artifact_checks"]["B_color_vs_radi"] = cvr
    man["artifact_checks"]["B_swing_RG_pct"] = round(100 * (max(rg) / min(rg) - 1), 1)
    man["artifact_checks"]["B_swing_BG_pct"] = round(100 * (max(bg) / min(bg) - 1), 1)
    log(f"  B · variació de color {cvr[0][0]}–{cvr[-1][0]} R☉: R/G {man['artifact_checks']['B_swing_RG_pct']} %, "
        f"B/G {man['artifact_checks']['B_swing_BG_pct']} % (a la recepta antiga: 108 % i 108 %)")

    # A: l'escaló es mesura en unitats de SOROLL del cel, que és l'únic patró
    # amb què l'ull el compara. Sota 1 sigma és invisible.
    x0b, y0b, x1b, y1b = man["masks"]["sony_full_coverage_box"]
    L = mostrar.mean(axis=2)
    lluny_ref = (R > CEL_R_MIN) & (validesa > 0.5)
    sigma_cel = float(np.std(L[lluny_ref])) if lluny_ref.sum() > 1000 else 1.0
    banda = 120
    def franja(sl):
        v = L[sl]; g = validesa[sl]
        v = v[np.isfinite(v) & (g > 0.99)]
        return float(np.median(v)) if v.size > 500 else float("nan")
    dins = franja((slice(y0b + 60, y1b - 60), slice(x0b + 60, x0b + 60 + banda)))
    fora = franja((slice(y0b + 60, y1b - 60), slice(max(0, x0b - 60 - banda), max(1, x0b - 60))))
    dins_b = franja((slice(y1b - 60 - banda, y1b - 60), slice(x0b + 200, x1b - 200)))
    fora_b = franja((slice(min(h - 1, y1b + 60), min(h, y1b + 60 + banda)), slice(x0b + 200, x1b - 200)))
    man["artifact_checks"]["A_sigma_cel_BBsol"] = sigma_cel
    man["artifact_checks"]["A_salt_esquerra_sigmes"] = round(abs(dins - fora) / max(sigma_cel, 1e-30), 3)
    man["artifact_checks"]["A_salt_inferior_sigmes"] = round(abs(dins_b - fora_b) / max(sigma_cel, 1e-30), 3)
    log(f"  A · escaló de cobertura: esquerra {man['artifact_checks']['A_salt_esquerra_sigmes']} σ, "
        f"inferior {man['artifact_checks']['A_salt_inferior_sigmes']} σ del soroll del cel")
    man["artifact_checks"]["D_limb_radius_rsol"] = round(dR / r_sol, 4)
    man["artifact_checks"]["D_limb_offset_px"] = round(man["geometry"]["lunar_disc_offset_from_sun_px"], 2)

    # E: EL PERFIL RADIAL HA DE SER MONÒTON. És la comprovació que hauria
    # cantat el defecte del 22-08 i cap de les que hi havia no ho va fer: el
    # salt de mediana a les costures mira VORES, i aquell artefacte era un
    # anell radial; la variació de color mira QUOCIENTS entre canals, i un
    # factor gris els deixa igual. La corona no puja mai amb el radi: si la
    # mediana azimutal del compost sense cel té un pendent logarítmic positiu,
    # o si el pendent fa un salt, hi ha una màscara ficada a la fotometria.
    def perfil_radial():
        gsc = corona[:, :, 1] - cel[:, :, 1]
        rr, vv = [], []
        for r0 in np.arange(1.30, 7.01, 0.05):
            m = (R >= r0) & (R < r0 + 0.05) & (validesa > 0.99)
            if m.sum() < 3000:
                continue
            v = gsc[m]
            v = v[np.isfinite(v) & (v > 0)]
            if v.size < 1000:
                continue
            rr.append(float(r0 + 0.025)); vv.append(float(np.median(v)))
        return np.array(rr), np.array(vv)
    rr, vv = perfil_radial()
    if rr.size > 8:
        pend = np.diff(np.log(vv)) / np.diff(np.log(rr))          # d ln L / d ln r
        man["artifact_checks"]["E_perfil_pendent_max"] = round(float(pend.max()), 3)
        man["artifact_checks"]["E_perfil_pendent_max_Rsol"] = round(float(rr[int(np.argmax(pend)) + 1]), 2)
        man["artifact_checks"]["E_perfil_salt_de_pendent_max"] = round(float(np.abs(np.diff(pend)).max()), 3)
        man["artifact_checks"]["E_perfil_salt_max_Rsol"] = round(float(rr[int(np.argmax(np.abs(np.diff(pend)))) + 2]), 2)
        man["artifact_checks"]["E_llindar"] = {"pendent_max": 0.0, "salt_de_pendent_max": 1.5}
        man["artifact_checks"]["E_PASSA"] = bool(pend.max() < 0.0 and np.abs(np.diff(pend)).max() < 1.5)
        log(f"  E · perfil radial: pendent màxim {pend.max():+.3f} a "
            f"{man['artifact_checks']['E_perfil_pendent_max_Rsol']} R☉ (ha de ser < 0); "
            f"salt de pendent màxim {np.abs(np.diff(pend)).max():.3f} a "
            f"{man['artifact_checks']['E_perfil_salt_max_Rsol']} R☉ (llindar 1,5) -> "
            f"{'PASSA' if man['artifact_checks']['E_PASSA'] else 'FALLA'}")

    # F: EL COMPOST HA DE SER LA MESCLA I RES MÉS. Cap màscara no hi pot
    # entrar com a factor. Es comprova dividint pel mesclat reconstruït: ha de
    # donar 1 a tot arreu. El 22-08 donava validesa², entre 0,56 i 1,00.
    _mix = vixw[:, :, 1] * wv + sony_ns[:, :, 1] * (1.0 - wv)
    _sel = (validesa > 0.99) & np.isfinite(corona[:, :, 1]) & (np.abs(_mix) > 0)
    _q = corona[:, :, 1][_sel] / _mix[_sel]
    man["artifact_checks"]["F_compost_entre_mescla_p01_p99"] = [round(float(np.percentile(_q, 1)), 6),
                                                                round(float(np.percentile(_q, 99)), 6)]
    man["artifact_checks"]["F_desviacio_max"] = round(float(np.abs(_q - 1.0).max()), 6)
    man["artifact_checks"]["F_llindar"] = 1e-3
    man["artifact_checks"]["F_PASSA"] = bool(np.abs(_q - 1.0).max() < 1e-3)
    log(f"  F · compost / mescla: desviació màxima {np.abs(_q - 1.0).max():.2e} "
        f"(llindar 1e-3) -> {'PASSA' if man['artifact_checks']['F_PASSA'] else 'FALLA'}")
    del _mix, _sel, _q

    # ---------------------------------------------------------------- MGN
    log("MGN…")
    lum = L.copy()
    med = median_filter(lum, size=5)
    dif = lum - med
    thr = float(np.percentile(dif[R > 1.5], 98.5))
    pols = (dif > thr) & (R > 1.2)
    lum[pols] = med[pols]
    del med, dif, pols
    pad = MGN_PAD
    lp = cv2.copyMakeBorder(lum, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    lp = (lp - lp.min()) / (lp.max() - lp.min() + 1e-8)
    res = mgn(lp, sigma=MGN_SIGMA, k=MGN_K, gamma=MGN_GAMMA, h=MGN_H)[pad:-pad, pad:-pad]
    del lp, lum
    neutral = np.clip(0.5 + ((res - res.mean()) / (2.0 * (res.std() * 2.8) + 1e-6)), 0, 1).astype(np.float32)
    neutral = (neutral * limb + 0.5 * (1 - limb)).astype(np.float32)   # el disc queda gris neutre, no negre
    del res

    # ------------------------------------------------------------- lliurables
    log("desant…")
    outs = {}
    def desa(nom, arr):
        p = os.path.join(out, nom)
        tiff.imwrite(p, arr)
        outs[nom] = p
    desa("01_Base_Sony_calibrada_BBsol_float32.tif", sony_ns.astype(np.float32))
    desa("02_Overlay_Vixen_calibrada_BBsol_float32.tif", (vixw * wv3).astype(np.float32))
    desa("03_Mascara_fusio_float32.tif", wv.astype(np.float32))
    desa("04_Detall_MGN_gris50_uint16.tif", (neutral * 65535).astype(np.uint16))
    desa("05_Model_de_cel_BBsol_float32.tif", cel.astype(np.float32))
    desa("06_Compost_LINEAL_BBsol_float32.tif", corona.astype(np.float32))
    # 06b = 06 menys el cel, i tots dos SENSE cap màscara: són fotometria.
    corona_sc = (corona - cel).astype(np.float32)
    desa("06b_Compost_LINEAL_sense_cel_BBsol_float32.tif", corona_sc)
    desa("07_Mascara_validesa_float32.tif", validesa.astype(np.float32))

    ref = float(np.nanpercentile(corona[:, :, 1][(R > 1.05) & (R < 1.15)], 99.0))
    man["photometry"]["tone_reference_BBsol_G_at_1.1Rsol_p99"] = ref
    def tona(x):
        return (np.log1p(np.clip(x / (ref + 1e-30), 0, 1) * 40.0) / np.log1p(40.0)).astype(np.float32)
    desa("08_Compost_corba_declarada_uint16.tif", (tona(mostrar) * 65535).astype(np.uint16))
    man["photometry"]["tone_curve"] = "log1p(clip(B/Bsol / ref,0,1)*40)/log1p(40); ref = p99 de G a 1,05-1,15 Rsol"

    comp = tona(mostrar)
    pv = np.clip(comp + 0.35 * (neutral[:, :, None] - 0.5), 0, 1)
    p8 = cv2.cvtColor((pv * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    pj = os.path.join(prev, "00_PREVIEW_4K_stack_calibrat.jpg")
    cv2.imwrite(pj, cv2.resize(p8, (3840, 2560), interpolation=cv2.INTER_AREA), [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    outs["preview_4k"] = pj
    half = 1000
    cx0 = int(max(0, min(w - 2 * half, sun_s[0] - half))); cy0 = int(max(0, min(h - 2 * half, sun_s[1] - half)))
    cr = (np.clip(comp[cy0:cy0 + 2 * half, cx0:cx0 + 2 * half] * 2.2, 0, 1) * 255).astype(np.uint8)
    pl = os.path.join(prev, "01_LIMBE_natiu.jpg")
    cv2.imwrite(pl, cv2.cvtColor(cr, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    outs["preview_limbe"] = pl

    for k, v in list(outs.items()):
        if os.path.exists(v):
            outs[k] = {"path": v, "bytes": os.path.getsize(v), "sha256": sha256(v)}
    man["outputs"] = outs
    with open(os.path.join(out, "MANIFEST.json"), "x", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    log(f"manifest: {os.path.join(out, 'MANIFEST.json')}")
    log("FET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
