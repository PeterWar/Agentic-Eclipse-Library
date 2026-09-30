#!/usr/bin/env python3
"""Reproducció controlada de la branca Druckmüller amb el centre solar corregit.

Ordre expressa de Pere, 22-08-2026 al vespre: «refés les proves que m'han
agradat amb el centre correcte, sobre un build ID nou i sense tocar el
workspace congelat».

QUÈ FA I QUÈ NO FA
------------------
Reprodueix, **algorisme per algorisme**, el darrer constructor de la branca
Gemini —`build_full_rectangular_masters.py`, del workspace congelat a
`output/auditoria_kimi_gemini_20260822/antigravity_workspace_snapshot/`— i en
canvia **una sola cosa**: el centre solar del qual penja tota la geometria
radial.

L'original escrivia a mà `sun_v = [3479.0, 2319.0]`, que és exactament el
centre geomètric de `hdr_vixen_countss.npy` (6958/2, 4638/2). No és cap
mesura. Passat per la matriu M cau a (3822,96, 2764,34), a **71,18 px =
0,238 R☉** del centre astromètric mesurat del projecte.

Aquesta eina emet les DUES variants en la mateixa execució i amb el mateix
codi, perquè la comparació sigui honesta:

  A) `centre_original`     — (3479, 2319) passat per M. El que Pere ja ha vist.
  B) `centre_astrometric`  — (3894,0057, 2768,6726) llegit de
     `final_solution.json` (`sony_radial`, n=38, rms=0,713 px).

Tota la resta —blanc Daylight, matriu M, calibració fotomètrica a la zona de
solapament, apodització de vores, sigmoide de fusió, MGN a sis escales, corba
de to i quantització— és idèntica a l'original.

NO promociona res. Els productes continuen `EXPERIMENTAL_NOT_CANONICAL`:
parteixen dels apilats històrics, no dels paquets S6 acceptats, i l'apilat
Sony v3 ja fon `DSC06987` amb `DSC06993`. El pilot S6 amb les dues 8 s
separades continua sent el gate següent.

SEGURETAT
---------
- No-clobber estricte: si el directori de build ja existeix, avorta.
- No escriu enlloc més que al seu build ID i a `IA/output/`.
- No toca el workspace congelat, ni `~/Downloads/Eclipse Antigravity`, ni cap
  PSB, RAW, màster S6 o rebut existent.
"""

from __future__ import annotations

import argparse
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
        "  python3 research/tools/druckmuller_centre_corregit/detecta_python.py --check\n"
        "i fes servir l'intèrpret que digui."
    )

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop", "Eclipse 2026")
WORKTREE = os.path.join(HOME, "Downloads", "Eclipse 2026")

SONY_STACK = os.path.join(
    DESKTOP, "Derivats/Sony/Apilats/300mm_apilat_v3",
    "Sony300_apilat_v3_10fotogrames_ADUs_float32.tif",
)
VIXEN_HDR = os.path.join(DESKTOP, "Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_countss.npy")
ASTROMETRIA = os.path.join(
    DESKTOP, "Derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17",
    "final_solution.json",
)

# --- constants copiades literalment de l'original ------------------------------
SONY_PTS = np.array(
    [[3242.5, 765.8], [5806.9, 3498.2], [3233.8, 3192.6],
     [4834.3, 1878.4], [1570.6, 2039.3], [3448.1, 3224.8]], dtype=np.float32)
VIXEN_PTS = np.array(
    [[1131.67, 297.92], [6548.42, 1622.32], [3091.35, 3333.33],
     [4021.3, 391.57], [82.26, 3243.41], [3385.56, 3198.57]], dtype=np.float32)

SUN_VIXEN_ORIGINAL = (3479.0, 2319.0)   # centre geomètric de la matriu: l'error
R_SOL_VIXEN_PX = 446.15
EDGE_APOD_PX = 200.0
FUSIO_R0, FUSIO_SOFT = 2.8, 0.4
LIMB_R0, LIMB_SOFT = 0.985, 0.015
OVERLAP_LO, OVERLAP_HI = 1.5, 2.8
MGN_SIGMA = [3.0, 6.0, 12.0, 24.0, 48.0, 96.0]
MGN_K, MGN_GAMMA, MGN_H = 1.0, 2.2, 0.8
MGN_PAD = 128
TONE_GAIN = 40.0
LUMA = (0.299, 0.587, 0.114)


def sha256(path: str, buf: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(f"[{_dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def wb_canon(rgb: np.ndarray) -> np.ndarray:
    mults = np.array([1.94335, 1.0, 1.65918], dtype=np.float32)
    m = np.array([[1.45, -0.35, -0.10], [-0.15, 1.25, -0.10], [0.02, -0.22, 1.20]], np.float32)
    return _wb(rgb, mults, m)


def wb_sony(rgb: np.ndarray) -> np.ndarray:
    mults = np.array([2.45, 1.0, 1.85], dtype=np.float32)
    m = np.array([[1.50, -0.40, -0.10], [-0.18, 1.30, -0.12], [0.00, -0.25, 1.25]], np.float32)
    return _wb(rgb, mults, m)


def _wb(rgb: np.ndarray, mults: np.ndarray, mat: np.ndarray) -> np.ndarray:
    h, w, _ = rgb.shape
    out = (rgb * mults[None, None, :]).reshape(-1, 3) @ mat.T
    return np.maximum(out.reshape(h, w, 3), 0.0).astype(np.float32)


def luma(img: np.ndarray) -> np.ndarray:
    return (LUMA[0] * img[:, :, 0] + LUMA[1] * img[:, :, 1] + LUMA[2] * img[:, :, 2]).astype(np.float32)


def tona(x: np.ndarray, ref: float) -> np.ndarray:
    """Corba de to de l'original: normalitza per percentil, clip, log1p."""
    n = np.clip(x / (ref + 1e-6), 0.0, 1.0)
    return (np.log1p(n * TONE_GAIN) / np.log1p(TONE_GAIN)).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build-id", default=None, help="per defecte, marca de temps UTC")
    ap.add_argument("--out-root", default=os.path.join(WORKTREE, "output", "druckmuller_centre_corregit_20260822"))
    ap.add_argument("--preview-root", default=os.path.join(DESKTOP, "IA", "output", "druckmuller_centre_corregit_20260822"))
    ap.add_argument("--variants", default="centre_original,centre_astrometric")
    args = ap.parse_args()

    build_id = args.build_id or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(args.out_root, build_id)
    if os.path.exists(out_dir):
        sys.exit(f"NO-CLOBBER: {out_dir} ja existeix. Tria un --build-id nou.")
    os.makedirs(out_dir, exist_ok=False)
    prev_dir = os.path.join(args.preview_root, build_id)
    os.makedirs(prev_dir, exist_ok=False)

    manifest: dict = {
        "build_id": build_id,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "purpose": "reproduccio controlada de la branca Druckmuller amb el centre solar corregit",
        "authority": "ordre expressa de Pere 22-08-2026 vespre; auditoria research/91 §2.4",
        "status": "EXPERIMENTAL_NOT_CANONICAL",
        "no_s6": "parteix d'apilats historics, no dels paquets S6 acceptats; l'apilat Sony v3 ja fon DSC06987 amb DSC06993",
        "reproduces": "output/auditoria_kimi_gemini_20260822/antigravity_workspace_snapshot/scripts/build_full_rectangular_masters.py",
        "single_change": "centre solar del qual penja tota la geometria radial",
        "inputs": {},
        "geometry": {},
        "variants": {},
        "outputs": {},
    }

    # ---------------------------------------------------------------- entrades
    for nom, ruta in (("sony_stack", SONY_STACK), ("vixen_hdr", VIXEN_HDR), ("astrometria", ASTROMETRIA)):
        if not os.path.exists(ruta):
            sys.exit(f"Falta l'entrada {nom}: {ruta}")
        log(f"hash de {nom}…")
        st = os.stat(ruta)
        manifest["inputs"][nom] = {"path": ruta, "bytes": st.st_size, "sha256": sha256(ruta)}

    sol = json.load(open(ASTROMETRIA))
    sun_sony_astro = (float(sol["sony_radial"]["sun_x"]), float(sol["sony_radial"]["sun_y"]))
    escala_v = float(sol["r6_radial"]["scale"])
    escala_s = float(sol["sony_radial"]["scale"])
    r_sol_px = R_SOL_VIXEN_PX * (escala_v / escala_s)

    log(f"carregant Sony: {SONY_STACK}")
    sony = np.nan_to_num(tiff.imread(SONY_STACK).astype(np.float32), nan=0.0)
    np.maximum(sony, 0.0, out=sony)
    h_s, w_s = sony.shape[:2]
    sony_day = wb_sony(sony)
    del sony

    log(f"carregant Vixen: {VIXEN_HDR}")
    vix = np.nan_to_num(np.load(VIXEN_HDR).astype(np.float32), nan=0.0)
    np.maximum(vix, 0.0, out=vix)
    h_v, w_v = vix.shape[:2]
    vix_day = wb_canon(vix)
    del vix

    M, _ = cv2.estimateAffinePartial2D(VIXEN_PTS, SONY_PTS)
    resid = (M @ np.hstack([VIXEN_PTS, np.ones((6, 1), np.float32)]).T).T - SONY_PTS
    resid_px = np.linalg.norm(resid, axis=1)
    sun_from_original = M @ np.array([*SUN_VIXEN_ORIGINAL, 1.0], np.float32)
    sun_from_vixen_astro = M @ np.array([sol["r6_radial"]["sun_x"], sol["r6_radial"]["sun_y"], 1.0], np.float32)

    manifest["geometry"] = {
        "M": M.tolist(),
        "M_scale_vixen_to_sony": float(np.hypot(M[0, 0], M[0, 1])),
        "M_rotation_deg": float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))),
        "star_residuals_px": [round(float(x), 4) for x in resid_px],
        "star_residual_rms_px": round(float(np.sqrt((resid_px ** 2).mean())), 4),
        "sony_canvas_wh": [w_s, h_s],
        "vixen_canvas_wh": [w_v, h_v],
        "vixen_geometric_center": [w_v / 2.0, h_v / 2.0],
        "sun_original_hardcoded_vixen": list(SUN_VIXEN_ORIGINAL),
        "sun_original_projected_sony": [float(sun_from_original[0]), float(sun_from_original[1])],
        "sun_astrometric_sony": list(sun_sony_astro),
        "sun_astrometric_vixen_projected_sony": [float(sun_from_vixen_astro[0]), float(sun_from_vixen_astro[1])],
        "control_vixen_astro_vs_sony_astro_px": round(
            float(np.linalg.norm(np.array(sun_from_vixen_astro) - np.array(sun_sony_astro))), 4),
        "error_px": round(float(np.linalg.norm(np.array(sun_from_original[:2]) - np.array(sun_sony_astro))), 4),
        "r_sol_sony_px": round(r_sol_px, 4),
        "plate_scales_arcsec_px": {"vixen": escala_v, "sony": escala_s},
    }
    manifest["geometry"]["error_rsol"] = round(manifest["geometry"]["error_px"] / r_sol_px, 4)
    log("geometria: error del centre original = "
        f"{manifest['geometry']['error_px']} px = {manifest['geometry']['error_rsol']} R_sol; "
        f"control vixen_astro->sony_astro = {manifest['geometry']['control_vixen_astro_vs_sony_astro_px']} px")

    log("warp de la Vixen al llenç Sony…")
    vix_warp = cv2.warpAffine(vix_day, M, (w_s, h_s), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    del vix_day

    # apodització de vores: no depèn del centre, es calcula una sola vegada
    valid = (vix_warp[:, :, 0] > 0).astype(np.uint8)
    dist_edge = cv2.distanceTransform(valid, cv2.DIST_L2, 5)
    edge_w = np.clip(dist_edge / EDGE_APOD_PX, 0.0, 1.0)
    edge_w = (0.5 * (1.0 - np.cos(np.pi * edge_w))).astype(np.float32)
    del dist_edge, valid

    lum_s = luma(sony_day)
    sony_ref = float(np.percentile(sony_day[sony_day > 0], 99.8))
    lum_v_warp = luma(vix_warp)
    manifest["geometry"]["sony_tone_reference_p998"] = sony_ref

    YY = np.arange(h_s, dtype=np.float32)[:, None]
    XX = np.arange(w_s, dtype=np.float32)[None, :]

    centres = {
        "centre_original": (float(sun_from_original[0]), float(sun_from_original[1])),
        "centre_astrometric": sun_sony_astro,
    }
    demanades = [v.strip() for v in args.variants.split(",") if v.strip()]

    for variant in demanades:
        if variant not in centres:
            sys.exit(f"Variant desconeguda: {variant}")
        sun_x, sun_y = centres[variant]
        log(f"=== variant {variant}: centre ({sun_x:.3f}, {sun_y:.3f}) ===")
        vdir = os.path.join(out_dir, variant)
        os.makedirs(vdir, exist_ok=False)

        dist_rsol = (np.sqrt((XX - sun_x) ** 2 + (YY - sun_y) ** 2) / r_sol_px).astype(np.float32)

        overlap = (dist_rsol >= OVERLAP_LO) & (dist_rsol <= OVERLAP_HI) & (vix_warp[:, :, 0] > 0)
        escala_fot = float(np.median(lum_s[overlap]) / (np.median(lum_v_warp[overlap]) + 1e-6))
        log(f"  escala fotomètrica a la zona de solapament: {escala_fot:.6f} ({int(overlap.sum())} px)")
        del overlap

        vix_cal = vix_warp * escala_fot

        snr_v = np.clip(1.0 / (1.0 + np.exp((dist_rsol - FUSIO_R0) / FUSIO_SOFT)), 0.0, 1.0).astype(np.float32)
        w_vix = gaussian_filter(snr_v * edge_w, sigma=20).astype(np.float32)
        del snr_v
        limb = np.clip((dist_rsol - LIMB_R0) / LIMB_SOFT, 0.0, 1.0).astype(np.float32)
        w_vix *= limb
        w3 = w_vix[:, :, None]

        corona = vix_cal * w3 + sony_day * (1.0 - w3)
        corona *= limb[:, :, None]

        # ---- màsters 01..03, corba de to idèntica a l'original ---------------
        outs: dict[str, str] = {}
        p = os.path.join(vdir, "01_Base_GranCamp_Sony_Corona_Daylight.tif")
        tiff.imwrite(p, (tona(sony_day, sony_ref) * 65535.0).astype(np.uint16)); outs["01_base_sony"] = p
        p = os.path.join(vdir, "02_Overlay_Corona_HDR_Vixen_Daylight.tif")
        tiff.imwrite(p, (tona(vix_cal * w3, sony_ref) * 65535.0).astype(np.uint16)); outs["02_overlay_vixen"] = p
        p = os.path.join(vdir, "03_Mascara_Transicio_Corona_Fuzzy.tif")
        tiff.imwrite(p, (w_vix * 65535.0).astype(np.uint16)); outs["03_mascara"] = p
        del vix_cal

        # ---- capa de detall MGN ---------------------------------------------
        log("  MGN sobre el sensor sencer…")
        lum_c = luma(corona)
        lum_med = median_filter(lum_c, size=5)
        diff = lum_c - lum_med
        llindar = float(np.percentile(diff[dist_rsol > 1.5], 98.5))
        pols = (diff > llindar) & (dist_rsol > 1.2)
        lum_clean = lum_c.copy()
        lum_clean[pols] = lum_med[pols]
        del lum_med, diff, pols

        pad = MGN_PAD
        lp = cv2.copyMakeBorder(lum_clean, pad, pad, pad, pad, cv2.BORDER_REFLECT)
        lp = (lp - lp.min()) / (lp.max() - lp.min() + 1e-8)
        res = mgn(lp, sigma=MGN_SIGMA, k=MGN_K, gamma=MGN_GAMMA, h=MGN_H)[pad:-pad, pad:-pad]
        del lp, lum_clean

        neutral = np.clip(0.5 + ((res - res.mean()) / (2.0 * (res.std() * 2.8) + 1e-6)), 0, 1).astype(np.float32)
        neutral *= limb
        del res
        p = os.path.join(vdir, "04_Capa_Detall_Druckmuller_MGN.tif")
        tiff.imwrite(p, (neutral * 65535.0).astype(np.uint16)); outs["04_detall_mgn"] = p

        # ---- extra, només informatiu: el compost LINEAL en float32 -----------
        # No forma part de l'A/B. El Handoff §7.3 demanava float32 i el codi
        # original quantitzava a uint16 amb corba de to; això és el mateix
        # compost SENSE corba, per si Pere el vol muntar en lineal.
        p = os.path.join(vdir, "EXTRA_Compost_LINEAL_float32_ADUs.tif")
        tiff.imwrite(p, corona.astype(np.float32)); outs["extra_compost_lineal"] = p

        # ---- previsualització 4K --------------------------------------------
        comp = tona(corona, sony_ref)
        prev = np.clip(comp + 0.35 * (neutral[:, :, None] - 0.5), 0, 1)
        prev8 = cv2.cvtColor((prev * 255.0).astype(np.uint8), cv2.COLOR_RGB2BGR)
        pj = os.path.join(prev_dir, f"00_PREVIEW_4K_{variant}.jpg")
        cv2.imwrite(pj, cv2.resize(prev8, (3840, 2560), interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        outs["preview_4k"] = pj

        # retall del limbe a resolució nativa: és on es veu l'error
        half = 1100
        x0 = int(max(0, min(w_s - 2 * half, sun_x - half)))
        y0 = int(max(0, min(h_s - 2 * half, sun_y - half)))
        crop = (np.clip(comp[y0:y0 + 2 * half, x0:x0 + 2 * half] * 3.0, 0, 1) * 255).astype(np.uint8)
        pc = os.path.join(prev_dir, f"01_LIMBE_natiu_{variant}.jpg")
        cv2.imwrite(pc, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        outs["preview_limbe"] = pc
        del comp, prev, prev8, crop

        manifest["variants"][variant] = {
            "sun_center_sony_px": [sun_x, sun_y],
            "photometric_scale": escala_fot,
            "mgn_threshold_starmask": llindar,
            "limb_mask_r0_rsol": LIMB_R0,
            "fusion_sigmoid_r0_rsol": FUSIO_R0,
            "crop_origin_xy": [x0, y0],
        }
        manifest["outputs"][variant] = outs
        del corona, w_vix, w3, limb, neutral, dist_rsol
        log(f"  variant {variant} feta")

    # ---- diferència entre variants, si s'han fet totes dues -------------------
    if len(demanades) == 2 and all(v in manifest["outputs"] for v in centres):
        log("comparant les dues variants…")
        a = tiff.imread(manifest["outputs"]["centre_original"]["03_mascara"]).astype(np.float32) / 65535.0
        b = tiff.imread(manifest["outputs"]["centre_astrometric"]["03_mascara"]).astype(np.float32) / 65535.0
        d = np.abs(a - b)
        manifest["diff_mascara"] = {
            "max": float(d.max()), "mean": float(d.mean()),
            "px_diff_gt_0p01": int((d > 0.01).sum()),
            "px_diff_gt_0p50": int((d > 0.50).sum()),
        }
        heat = cv2.applyColorMap((np.clip(d, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
        pd_ = os.path.join(prev_dir, "02_DIFERENCIA_mascara_original_vs_astrometric.jpg")
        cv2.imwrite(pd_, cv2.resize(heat, (3840, 2560), interpolation=cv2.INTER_AREA),
                    [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        manifest["outputs"]["diff"] = {"mascara_heatmap": pd_}
        del a, b, d, heat

    # ---- hashes de sortida i manifest ----------------------------------------
    log("hashes de sortida…")
    for variant, outs in manifest["outputs"].items():
        for clau, ruta in outs.items():
            if os.path.exists(ruta):
                outs[clau] = {"path": ruta, "bytes": os.path.getsize(ruta), "sha256": sha256(ruta)}
    mpath = os.path.join(out_dir, "MANIFEST.json")
    with open(mpath, "x", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    log(f"manifest: {mpath}")
    log("FET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
