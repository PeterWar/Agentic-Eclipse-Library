#!/usr/bin/env python3
"""Reproducció controlada de la branca Druckmüller amb el REGISTRE corregit.

Ordre expressa de Pere, 22-08-2026 al vespre: refer les proves que li han
agradat amb la geometria correcta, sobre un build ID nou i sense tocar el
workspace congelat.

EL DEFECTE, DIT BÉ
------------------
`hdr_vixen_countss.npy` està construït **amb el Sol al centre exacte
(3479, 2319)** —ho declara el seu propi `LLEGEIX-ME.md`—, o sigui que el valor
que la branca Gemini escriu a mà és correcte **per a aquella matriu**. El que
no encaixa és una altra cosa:

  la matriu `M` de Gemini està ajustada amb sis estrelles mesurades a la
  **graella del sensor** (la de l'astrometria del projecte), i després
  s'aplica a la matriu HDR, que viu en una graella **desplaçada**.

Desplaçament mesurat amb 19 estrelles del catàleg `final_match_r6.csv`:
**(+89,775, −48,647) px**, amb σ = (0,25, 0,13). Conseqüència: la capa Vixen
queda desregistrada **~69 px = 0,23 R☉** respecte de la base Sony, i les
màscares radials segueixen la Vixen desplaçada en lloc del Sol de la Sony.

LA CORRECCIÓ
------------
En comptes d'ajustar sis estrelles amb residus de fins a 1,27 px, la matriu
nova surt de les **dues solucions de placa** del projecte —`r6_radial` amb 22
estrelles i rms 0,42 px, i `sony_radial` amb 38 i rms 0,71—, compostes pel
pla tangent al Sol:

    M_lineal = A_sony · A_vixen⁻¹

i la translació HDR → graella del sensor es mesura amb les estrelles del
catàleg dins la mateixa matriu HDR. Escala i rotació resultants (0,67125 i
33,089°) coincideixen amb les de Gemini (0,671927 i 33,075°): el que canvia
és **només la translació**.

VALIDACIÓ INDEPENDENT
---------------------
Es mesura el limbe del disc lunar de la Vixen ja deformada, ajustant un cercle
a 144 azimuts, i es compara amb el Sol astromètric de la Sony. Amb el warp de
Gemini surt a ~69 px; amb el corregit, a ~0,3 px.

QUÈ NO FA
---------
No promociona res. Els productes continuen `EXPERIMENTAL_NOT_CANONICAL`:
parteixen dels apilats històrics, no dels paquets S6 acceptats, i l'apilat
Sony v3 ja fon `DSC06987` amb `DSC06993`. El pilot S6 amb les dues 8 s
separades continua sent el gate següent. No-clobber estricte.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import sys

import numpy as np

try:
    import cv2
    import tifffile as tiff
    from scipy.ndimage import gaussian_filter, median_filter
    from sunkit_image.enhance import mgn
except ImportError as exc:  # pragma: no cover
    sys.exit(
        f"Falta una dependència ({exc.name}). Executa primer\n"
        "  python3 research/tools/druckmuller_centre_corregit/detecta_python.py --check"
    )

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop", "Eclipse 2026")
WORKTREE = os.path.join(HOME, "Downloads", "Eclipse 2026")

SONY_STACK = os.path.join(DESKTOP, "Derivats/Sony/Apilats/300mm_apilat_v3",
                          "Sony300_apilat_v3_10fotogrames_ADUs_float32.tif")
VIXEN_HDR = os.path.join(DESKTOP, "Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_countss.npy")
ASTRO_DIR = os.path.join(DESKTOP, "Derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17")
ASTROMETRIA = os.path.join(ASTRO_DIR, "final_solution.json")
CATALEG_R6 = os.path.join(ASTRO_DIR, "final_match_r6.csv")

# --- constants literals de l'original -----------------------------------------
SONY_PTS = np.array([[3242.5, 765.8], [5806.9, 3498.2], [3233.8, 3192.6],
                     [4834.3, 1878.4], [1570.6, 2039.3], [3448.1, 3224.8]], np.float32)
VIXEN_PTS = np.array([[1131.67, 297.92], [6548.42, 1622.32], [3091.35, 3333.33],
                      [4021.3, 391.57], [82.26, 3243.41], [3385.56, 3198.57]], np.float32)
SUN_HDR = (3479.0, 2319.0)          # el Sol al centre exacte de la matriu HDR
R_SOL_VIXEN_PX = 446.15
EDGE_APOD_PX = 200.0
FUSIO_R0, FUSIO_SOFT = 2.8, 0.4
LIMB_R0, LIMB_SOFT = 0.985, 0.015
OVERLAP_LO, OVERLAP_HI = 1.5, 2.8
MGN_SIGMA = [3.0, 6.0, 12.0, 24.0, 48.0, 96.0]
MGN_K, MGN_GAMMA, MGN_H = 1.0, 2.2, 0.8
MGN_PAD, TONE_GAIN = 128, 40.0
LUMA = (0.299, 0.587, 0.114)


def sha256(path: str, buf: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def log(m: str) -> None:
    print(f"[{_dt.datetime.now():%H:%M:%S}] {m}", flush=True)


def _wb(rgb, mults, mat):
    h, w, _ = rgb.shape
    out = (rgb * mults[None, None, :]).reshape(-1, 3) @ mat.T
    return np.maximum(out.reshape(h, w, 3), 0.0).astype(np.float32)


def wb_canon(rgb):
    return _wb(rgb, np.array([1.94335, 1.0, 1.65918], np.float32),
               np.array([[1.45, -.35, -.10], [-.15, 1.25, -.10], [.02, -.22, 1.20]], np.float32))


def wb_sony(rgb):
    return _wb(rgb, np.array([2.45, 1.0, 1.85], np.float32),
               np.array([[1.50, -.40, -.10], [-.18, 1.30, -.12], [.00, -.25, 1.25]], np.float32))


def luma(img):
    return (LUMA[0] * img[:, :, 0] + LUMA[1] * img[:, :, 1] + LUMA[2] * img[:, :, 2]).astype(np.float32)


def tona(x, ref):
    n = np.clip(x / (ref + 1e-6), 0.0, 1.0)
    return (np.log1p(n * TONE_GAIN) / np.log1p(TONE_GAIN)).astype(np.float32)


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


def mesura_translacio_hdr(LV, aprox=(89.78, -48.72), tol=8.0):
    """Translació HDR → graella del sensor, amb les estrelles del catàleg."""
    dts = []
    with open(CATALEG_R6, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                x, y = float(row["x"]), float(row["y"])
            except (KeyError, TypeError, ValueError):
                continue
            c = centroide(LV, x - aprox[0], y - aprox[1])
            if c is None:
                continue
            d = np.array([x - c[0], y - c[1]])
            if np.linalg.norm(d - np.asarray(aprox)) < tol:
                dts.append(d)
    if len(dts) < 4:
        raise SystemExit(f"Només {len(dts)} estrelles per a la translació: massa poques.")
    a = np.array(dts)
    return a.mean(axis=0), a.std(axis=0), len(a)


def centre_limbe(L, x0, y0, w, h, rmax=600, naz=144):
    """Ajusta un cercle al limbe lunar mirant el gradient a `naz` azimuts."""
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
        r = rs[ok][i]
        pts.append((x0 + r * np.cos(ang), y0 + r * np.sin(ang)))
    P = np.array(pts, np.float64)
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    c, *_ = np.linalg.lstsq(A, (P ** 2).sum(axis=1), rcond=None)
    cx, cy = float(c[0]), float(c[1])
    R = float(np.sqrt(c[2] + cx * cx + cy * cy))
    resid = float(np.median(np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R)))
    return (cx, cy), R, resid, len(P)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build-id", default=None)
    ap.add_argument("--out-root", default=os.path.join(WORKTREE, "output", "druckmuller_centre_corregit_20260822"))
    ap.add_argument("--preview-root", default=os.path.join(DESKTOP, "IA", "output", "druckmuller_centre_corregit_20260822"))
    ap.add_argument("--variants", default="warp_original,warp_corregit")
    args = ap.parse_args()

    build_id = args.build_id or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(args.out_root, build_id)
    prev_dir = os.path.join(args.preview_root, build_id)
    if os.path.exists(out_dir) or os.path.exists(prev_dir):
        sys.exit(f"NO-CLOBBER: {build_id} ja existeix.")
    os.makedirs(out_dir); os.makedirs(prev_dir)

    man: dict = {
        "build_id": build_id,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "purpose": "branca Druckmuller amb el registre Vixen->Sony corregit",
        "authority": "ordre expressa de Pere 22-08-2026 vespre; rectificacio de research/91 §2.4 a research/92",
        "status": "EXPERIMENTAL_NOT_CANONICAL",
        "not_s6": "entrades: apilats historics. L'apilat Sony v3 ja fon DSC06987 amb DSC06993; el pilot S6 amb les dues 8 s separades continua sent el gate seguent",
        "reproduces": "antigravity_workspace_snapshot/scripts/build_full_rectangular_masters.py",
        "single_change": "la matriu de warp Vixen->Sony (translacio de graella); tota la resta identica",
        "inputs": {}, "geometry": {}, "validation": {}, "variants": {}, "outputs": {},
    }

    for nom, ruta in (("sony_stack", SONY_STACK), ("vixen_hdr", VIXEN_HDR),
                      ("astrometria", ASTROMETRIA), ("cataleg_r6", CATALEG_R6)):
        if not os.path.exists(ruta):
            sys.exit(f"Falta l'entrada {nom}: {ruta}")
        man["inputs"][nom] = {"path": ruta, "bytes": os.path.getsize(ruta), "sha256": sha256(ruta)}

    sol = json.load(open(ASTROMETRIA))
    Av = np.array([[sol["r6_radial"]["px"][1], sol["r6_radial"]["px"][2]],
                   [sol["r6_radial"]["py"][1], sol["r6_radial"]["py"][2]]], float)
    As = np.array([[sol["sony_radial"]["px"][1], sol["sony_radial"]["px"][2]],
                   [sol["sony_radial"]["py"][1], sol["sony_radial"]["py"][2]]], float)
    sun_v_raw = np.array([sol["r6_radial"]["sun_x"], sol["r6_radial"]["sun_y"]])
    sun_s = np.array([sol["sony_radial"]["sun_x"], sol["sony_radial"]["sun_y"]])
    r_sol_px = R_SOL_VIXEN_PX * (sol["r6_radial"]["scale"] / sol["sony_radial"]["scale"])

    log(f"carregant Vixen: {VIXEN_HDR}")
    vix = np.nan_to_num(np.load(VIXEN_HDR).astype(np.float32), nan=0.0)
    np.maximum(vix, 0.0, out=vix)
    h_v, w_v = vix.shape[:2]
    LV = vix[:, :, 1].copy()
    vix_day = wb_canon(vix)
    del vix

    log("mesurant la translació HDR → graella del sensor amb el catàleg d'estrelles…")
    t, t_sig, t_n = mesura_translacio_hdr(LV)
    log(f"  t = ({t[0]:+.3f}, {t[1]:+.3f}) px  σ=({t_sig[0]:.3f},{t_sig[1]:.3f})  amb {t_n} estrelles")

    Lin = As @ np.linalg.inv(Av)
    M_nova = np.zeros((2, 3)); M_nova[:, :2] = Lin; M_nova[:, 2] = sun_s - Lin @ (sun_v_raw - t)
    M_gem, _ = cv2.estimateAffinePartial2D(VIXEN_PTS, SONY_PTS)

    sun_gem = M_gem @ np.array([*SUN_HDR, 1.0], np.float32)
    sun_new = M_nova @ np.array([*SUN_HDR, 1.0])
    man["geometry"] = {
        "M_gemini": M_gem.tolist(),
        "M_corregida": M_nova.tolist(),
        "M_gemini_scale_rot": [float(np.hypot(M_gem[0, 0], M_gem[0, 1])),
                               float(np.degrees(np.arctan2(M_gem[1, 0], M_gem[0, 0])))],
        "M_corregida_scale_rot": [float(np.hypot(Lin[0, 0], Lin[0, 1])),
                                  float(np.degrees(np.arctan2(Lin[1, 0], Lin[0, 0])))],
        "hdr_to_sensor_translation_px": t.tolist(),
        "hdr_to_sensor_translation_sigma_px": t_sig.tolist(),
        "hdr_to_sensor_translation_n_stars": t_n,
        "sun_hdr_declared": list(SUN_HDR),
        "sun_hdr_source": "Derivats/Vixen/Corona_HDR_Vixen/LLEGEIX-ME.md: «El Sol al centre exacte (3479, 2319)»",
        "sun_astrometric_sony": sun_s.tolist(),
        "sun_projected_gemini": [float(sun_gem[0]), float(sun_gem[1])],
        "sun_projected_corregida": sun_new.tolist(),
        "misregistration_px": float(np.linalg.norm(np.asarray(sun_gem[:2], float) - sun_new)),
        "r_sol_sony_px": r_sol_px,
        "plate_solutions": {"r6_radial_n": sol["r6_radial"]["n"], "r6_radial_rms": sol["r6_radial"]["rms"],
                            "sony_radial_n": sol["sony_radial"]["n"], "sony_radial_rms": sol["sony_radial"]["rms"]},
    }
    man["geometry"]["misregistration_rsol"] = man["geometry"]["misregistration_px"] / r_sol_px
    log(f"desregistre de la branca original: {man['geometry']['misregistration_px']:.2f} px "
        f"= {man['geometry']['misregistration_rsol']:.4f} R_sol")

    log(f"carregant Sony: {SONY_STACK}")
    sony = np.nan_to_num(tiff.imread(SONY_STACK).astype(np.float32), nan=0.0)
    np.maximum(sony, 0.0, out=sony)
    h_s, w_s = sony.shape[:2]
    sony_day = wb_sony(sony)
    del sony
    lum_s = luma(sony_day)
    sony_ref = float(np.percentile(sony_day[sony_day > 0], 99.8))

    YY = np.arange(h_s, dtype=np.float32)[:, None]
    XX = np.arange(w_s, dtype=np.float32)[None, :]

    trans = {
        "warp_original": (np.asarray(M_gem, np.float64), (float(sun_gem[0]), float(sun_gem[1]))),
        "warp_corregit": (M_nova, (float(sun_s[0]), float(sun_s[1]))),
    }

    for variant in [v.strip() for v in args.variants.split(",") if v.strip()]:
        if variant not in trans:
            sys.exit(f"Variant desconeguda: {variant}")
        M, (sun_x, sun_y) = trans[variant]
        log(f"=== {variant}: centre de màscares ({sun_x:.2f}, {sun_y:.2f}) ===")
        vdir = os.path.join(out_dir, variant); os.makedirs(vdir)

        vix_warp = cv2.warpAffine(vix_day, M.astype(np.float32), (w_s, h_s), flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        # validació independent: on cau el disc lunar de la Vixen deformada
        LVw = cv2.warpAffine(LV, M.astype(np.float32), (w_s, h_s), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        p = M @ np.array([*SUN_HDR, 1.0])
        (dcx, dcy), dR, dres, dn = centre_limbe(LVw, p[0], p[1], w_s, h_s)
        del LVw
        man["validation"][variant] = {
            "lunar_disc_center_px": [dcx, dcy], "lunar_disc_radius_px": dR,
            "lunar_disc_radius_rsol": dR / r_sol_px, "circle_fit_residual_px": dres, "azimuths": dn,
            "distance_to_sony_astrometric_sun_px": float(np.hypot(dcx - sun_s[0], dcy - sun_s[1])),
        }
        log(f"  disc lunar a ({dcx:.2f},{dcy:.2f}) R={dR:.2f} px; "
            f"del Sol astromètric Sony: {man['validation'][variant]['distance_to_sony_astrometric_sun_px']:.2f} px")

        valid = (vix_warp[:, :, 0] > 0).astype(np.uint8)
        edge_w = np.clip(cv2.distanceTransform(valid, cv2.DIST_L2, 5) / EDGE_APOD_PX, 0.0, 1.0)
        edge_w = (0.5 * (1.0 - np.cos(np.pi * edge_w))).astype(np.float32)
        del valid

        dist_rsol = (np.sqrt((XX - sun_x) ** 2 + (YY - sun_y) ** 2) / r_sol_px).astype(np.float32)
        lum_v = luma(vix_warp)
        ov = (dist_rsol >= OVERLAP_LO) & (dist_rsol <= OVERLAP_HI) & (vix_warp[:, :, 0] > 0)
        esc = float(np.median(lum_s[ov]) / (np.median(lum_v[ov]) + 1e-6))
        log(f"  escala fotomètrica: {esc:.6f} ({int(ov.sum())} px)")
        del ov, lum_v
        vix_cal = vix_warp * esc
        del vix_warp

        snr = np.clip(1.0 / (1.0 + np.exp((dist_rsol - FUSIO_R0) / FUSIO_SOFT)), 0.0, 1.0).astype(np.float32)
        w_vix = gaussian_filter(snr * edge_w, sigma=20).astype(np.float32)
        del snr, edge_w
        limb = np.clip((dist_rsol - LIMB_R0) / LIMB_SOFT, 0.0, 1.0).astype(np.float32)
        w_vix *= limb
        w3 = w_vix[:, :, None]
        corona = vix_cal * w3 + sony_day * (1.0 - w3)
        corona *= limb[:, :, None]

        outs = {}
        p1 = os.path.join(vdir, "01_Base_GranCamp_Sony_Corona_Daylight.tif")
        tiff.imwrite(p1, (tona(sony_day, sony_ref) * 65535.0).astype(np.uint16)); outs["01_base_sony"] = p1
        p2 = os.path.join(vdir, "02_Overlay_Corona_HDR_Vixen_Daylight.tif")
        tiff.imwrite(p2, (tona(vix_cal * w3, sony_ref) * 65535.0).astype(np.uint16)); outs["02_overlay_vixen"] = p2
        p3 = os.path.join(vdir, "03_Mascara_Transicio_Corona_Fuzzy.tif")
        tiff.imwrite(p3, (w_vix * 65535.0).astype(np.uint16)); outs["03_mascara"] = p3
        del vix_cal

        log("  MGN…")
        lum_c = luma(corona)
        med = median_filter(lum_c, size=5)
        diff = lum_c - med
        thr = float(np.percentile(diff[dist_rsol > 1.5], 98.5))
        pols = (diff > thr) & (dist_rsol > 1.2)
        clean = lum_c.copy(); clean[pols] = med[pols]
        del med, diff, pols, lum_c
        pad = MGN_PAD
        lp = cv2.copyMakeBorder(clean, pad, pad, pad, pad, cv2.BORDER_REFLECT)
        lp = (lp - lp.min()) / (lp.max() - lp.min() + 1e-8)
        res = mgn(lp, sigma=MGN_SIGMA, k=MGN_K, gamma=MGN_GAMMA, h=MGN_H)[pad:-pad, pad:-pad]
        del lp, clean
        neutral = np.clip(0.5 + ((res - res.mean()) / (2.0 * (res.std() * 2.8) + 1e-6)), 0, 1).astype(np.float32)
        neutral *= limb
        del res
        p4 = os.path.join(vdir, "04_Capa_Detall_Druckmuller_MGN.tif")
        tiff.imwrite(p4, (neutral * 65535.0).astype(np.uint16)); outs["04_detall_mgn"] = p4

        p5 = os.path.join(vdir, "EXTRA_Compost_LINEAL_float32_ADUs.tif")
        tiff.imwrite(p5, corona.astype(np.float32)); outs["extra_compost_lineal"] = p5

        comp = tona(corona, sony_ref)
        prev = np.clip(comp + 0.35 * (neutral[:, :, None] - 0.5), 0, 1)
        prev8 = cv2.cvtColor((prev * 255.0).astype(np.uint8), cv2.COLOR_RGB2BGR)
        pj = os.path.join(prev_dir, f"00_PREVIEW_4K_{variant}.jpg")
        cv2.imwrite(pj, cv2.resize(prev8, (3840, 2560), interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 92]); outs["preview_4k"] = pj

        half = 1000
        x0 = int(max(0, min(w_s - 2 * half, sun_s[0] - half)))
        y0 = int(max(0, min(h_s - 2 * half, sun_s[1] - half)))
        crop = (np.clip(comp[y0:y0 + 2 * half, x0:x0 + 2 * half] * 3.0, 0, 1) * 255).astype(np.uint8)
        pc = os.path.join(prev_dir, f"01_LIMBE_natiu_{variant}.jpg")
        cv2.imwrite(pc, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        outs["preview_limbe"] = pc
        del comp, prev, prev8, crop

        man["variants"][variant] = {
            "M": M.tolist(), "mask_center_px": [sun_x, sun_y], "photometric_scale": esc,
            "star_mask_threshold": thr, "limb_crop_origin_xy": [x0, y0],
        }
        man["outputs"][variant] = outs
        del corona, w_vix, w3, limb, neutral, dist_rsol
        log(f"  {variant} feta")

    log("hashes de sortida…")
    for outs in man["outputs"].values():
        for k, ruta in outs.items():
            if isinstance(ruta, str) and os.path.exists(ruta):
                outs[k] = {"path": ruta, "bytes": os.path.getsize(ruta), "sha256": sha256(ruta)}
    with open(os.path.join(out_dir, "MANIFEST.json"), "x", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    log(f"manifest: {os.path.join(out_dir, 'MANIFEST.json')}")
    log("FET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
