#!/usr/bin/env python3
"""Build exposure-separated, linear Vixen/R6 eclipse masters with S6 receipts.

This is a reversible wrapper around the already validated CFA calibration,
solar geometry, atmospheric-extinction correction and drizzle code in
``apila_hdr4_vixen.py``.  Unlike the historical HDR4 delivery, it keeps every
compatible totality exposure group separate and preserves image, inverse-
variance weight, variance, coverage, saturation, A/B controls, transforms and
provenance.  The RAW files and historical products are read-only.

The first intended run is ``--exposure 0.125`` (the four 1/8-s frames).  Use
``--all`` only after that pilot receipt is accepted.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import tifffile


HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))

import hdr_corona_vixen as H  # noqa: E402
import apila_hdr4_vixen as A  # noqa: E402


SCHEMA = "VIXEN_R6_STACK_RECEIPT_S6_V2"
# DE440 topocentric distance at the acquisition site/time with IAU nominal
# R_sun=695700 km gives 946.6598 arcsec.  Override only this S6 process: the
# historical helper's generic 959" value is 1.303% too large and shifts its
# 4.2--5.1 R sky ring by 24--30 native pixels.
SOLAR_RADIUS_ARCSEC = 946.6598
SOLAR_RADIUS_PX = SOLAR_RADIUS_ARCSEC / H.ESCALA
SOLAR_RADIUS_AUTHORITY = (
    "DE440 topocentric at 2026-08-12 totality, site 42.299407N 5.02503W "
    "798 m; IAU nominal solar radius 695700 km"
)
H.R_SOL_PX = SOLAR_RADIUS_PX
CHANNEL_SAMPLE_FACTOR = np.array([4.0, 8.0, 4.0], np.float32)
# Star-field audit, 22-08-2026.  This is a weak smooth prior (0.76 sigma), not
# a claimed detection.  It is applied per frame and always compared with the
# translation-only control.  The fit reference is the midpoint of 572A2982.
ROTATION_RATE_DEG_S = -4.69e-5
ROTATION_RATE_SIGMA_DEG_S = 6.18e-5
ROTATION_REFERENCE_NAME = "572A2982.CR3"
# Canon MakerNote authority for 572A2982--572A2984.  The historical pipeline
# rounded the programmed 10.0 s step to 10.3 s, but the recorded physical
# exposure is 10.079368399159 s.  The 2.19 % difference is photometrically
# material and shifts the exposure midpoint by 0.1103158 s.
CANON_LONG_EXPOSURE_S = 10.079368399159


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exp_tag(exposure: float) -> str:
    if exposure >= 1:
        return f"{exposure:g}s"
    return f"1-{round(1 / exposure):d}s"


def physical_manifest() -> list[H.Fotograma]:
    """Return a corrected in-memory manifest; never mutate the historical CSV."""
    manifest = H.llegeix_manifest()
    finite = [f for f in manifest
              if np.isfinite(f.lluna_x) and np.isfinite(f.lluna_y)]
    times = np.asarray([f.t_rel_c2 for f in finite], np.float64)
    fit_x = np.polyfit(times, [f.lluna_x for f in finite], 1)
    fit_y = np.polyfit(times, [f.lluna_y for f in finite], 1)
    corrected = [f for f in manifest if abs(f.exp_nominal - 10.0) < 1e-9]
    for frame in corrected:
        frame.t_rel_c2 += 0.5 * (CANON_LONG_EXPOSURE_S - frame.exp_s)
        frame.exp_s = CANON_LONG_EXPOSURE_S
        frame.lluna_x = float(np.polyval(fit_x, frame.t_rel_c2))
        frame.lluna_y = float(np.polyval(fit_y, frame.t_rel_c2))
    if corrected:
        relative = H.desplacament_lluna_sol(
            np.asarray([f.t_rel_c2 for f in corrected], np.float64))
        for frame, rel in zip(corrected, relative):
            frame.sol_x = float(frame.lluna_x - rel[0])
            frame.sol_y = float(frame.lluna_y - rel[1])
    return manifest


def atomic_json(path: Path, value: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def save_tiff(path: Path, image: np.ndarray) -> None:
    tifffile.imwrite(
        path,
        image.astype(np.float32, copy=False),
        photometric="rgb",
        compression="zlib",
        compressionargs={"level": 4},
        metadata={"axes": "YXS", "unit": "ADU/s", "linear": True},
        software="stack_vixen_s6.py",
        bigtiff=True,
    )


def preview(path: Path, image: np.ndarray, width: int = 1800) -> None:
    finite = np.all(np.isfinite(image), axis=2)
    lum = np.nanmean(image, axis=2)
    vals = lum[finite]
    lo = max(float(np.percentile(vals, 2)), 1e-3)
    hi = max(float(np.percentile(vals, 99.85)), lo * 10)
    x = np.clip((np.log1p(np.maximum(image, 0) / lo)
                 / np.log1p(hi / lo)), 0, 1)
    # Neutral preview only.  It is not a scientific output or a colour grade.
    x = np.nan_to_num(x, nan=0.0)
    scale = min(1.0, width / image.shape[1])
    p = cv2.resize(x, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(path), np.clip(p[..., ::-1] * 255, 0, 255).astype(np.uint8))


def frame_hashes(frames: list[H.Fotograma]) -> list[dict]:
    out = []
    for f in frames:
        p = H.SRC / f.nom
        out.append({"name": f.nom, "path": str(p), "bytes": p.stat().st_size,
                    "sha256": sha256(p)})
    return out


def calibrator_hashes(frames: list[H.Fotograma]) -> list[dict]:
    paths = {H.MASTERS / f"master_{H.clau_master(f.exp_nominal)}.npy" for f in frames}
    paths.add(H.MASTERS / "prnu.npz")
    out = []
    for p in sorted(paths):
        out.append({"path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)})
        sidecar = p.with_suffix(".json")
        if sidecar.exists():
            out.append({"path": str(sidecar), "bytes": sidecar.stat().st_size,
                        "sha256": sha256(sidecar)})
    return out


def split_balanced(frames: list[H.Fotograma]) -> tuple[list[H.Fotograma], list[H.Fotograma]]:
    """Temporal odd/even split; each side samples the whole interval."""
    a, b = frames[0::2], frames[1::2]
    if not b:  # a one-frame group has no independent split
        b = []
    return a, b


def run_stack(frames: list[H.Fotograma], data: dict[str, tuple[np.ndarray, np.ndarray]],
              reference: H.Fotograma, label: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    ap = {"nom": label, "ref": reference, "exp_s": reference.exp_s,
          "membres": frames, "hdr": True}
    info: dict = {
        "name": label,
        "reference": reference.nom,
        "exposure_s": reference.exp_s,
        "members": [f.nom for f in frames],
        "t_rel_c2_s": {f.nom: f.t_rel_c2 for f in frames},
    }
    image, invvar_weight, coverage = A.apila(ap, data, info, mode="comuna")
    # A.apila keeps the reference Moon for the historical HDR-layer workflow.
    # This wrapper is a CORONA_SOLAR authority: the other frames were already
    # lunar-gated during the one-pass drizzle, and the reference support is
    # explicitly changed to no-data here (without another interpolation).
    geometry = info["geometria"]
    if math.isfinite(reference.lluna_mes_x):
        lunar_x, lunar_y = reference.lluna_mes_x, reference.lluna_mes_y
        lunar_source = "measured limb"
    else:
        offset = A.offset_limbe_model()
        lunar_x, lunar_y = reference.lluna_x + offset[0], reference.lluna_y + offset[1]
        lunar_source = "model plus measured mean offset"
    lunar_x += geometry["sol_x"] - reference.sol_x
    lunar_y += geometry["sol_y"] - reference.sol_y
    yy = np.arange(image.shape[0], dtype=np.float32)[:, None]
    xx = np.arange(image.shape[1], dtype=np.float32)[None, :]
    exclusion_radius = A.R_LLUNA + A.MARGE_LLUNA + A.TRANSICIO_LLUNA
    lunar_valid = np.hypot(xx - lunar_x, yy - lunar_y) >= exclusion_radius
    image[~lunar_valid] = np.nan
    invvar_weight[~lunar_valid] = 0.0
    coverage[~lunar_valid] = 0
    info["corona_lunar_no_data"] = {
        "reference": reference.nom,
        "centre_output_px": [float(lunar_x), float(lunar_y)],
        "exclusion_radius_px": float(exclusion_radius),
        "centre_source": lunar_source,
        "policy": "all contributions lunar-gated; reference support set to no-data after the same drizzle",
    }
    return image, invvar_weight, coverage, info


def rotation_model(frame: H.Fotograma, manifest: list[H.Fotograma]) -> tuple[float, float]:
    reference = next(f for f in manifest if f.nom == ROTATION_REFERENCE_NAME)
    source_angle = ROTATION_RATE_DEG_S * (frame.t_rel_c2 - reference.t_rel_c2)
    source_sigma = ROTATION_RATE_SIGMA_DEG_S * abs(frame.t_rel_c2 - reference.t_rel_c2)
    # The measured angle describes current-frame orientation relative to the
    # reference.  Mapping current data to the reference uses the opposite sign.
    return -source_angle, source_sigma


def image_rotation_matrix(cx: float, cy: float, angle_deg: float) -> np.ndarray:
    """Source-to-destination image-coordinate rotation around (cx, cy)."""
    angle = math.radians(angle_deg)
    c, s = math.cos(angle), math.sin(angle)
    linear = np.array([[c, -s], [s, c]], np.float64)
    centre = np.array([cx, cy], np.float64)
    offset = centre - linear @ centre
    return np.c_[linear, offset]


def combine(num: np.ndarray, den: np.ndarray, coverage: np.ndarray
            ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    image = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan).astype(np.float32)
    return image, den.astype(np.float32), coverage.astype(np.uint16)


def run_stack_rotation_model(
    frames: list[H.Fotograma], data: dict[str, tuple[np.ndarray, np.ndarray]], label: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict, dict, list[dict], np.ndarray]:
    """Drizzle each frame independently, apply the theta(t) prior, then sum.

    Keeping the per-frame drizzle ahead of the affine rotation preserves the
    calibrated Bayer sampling.  All lunar discs are excluded here because this
    is a CORONA_SOLAR master; lunar/earthshine products are separate.
    """
    manifest = H.llegeix_manifest()
    common = next(f for f in manifest if f.nom == A.NOM_EPOCA_COMUNA)
    height, width = data[frames[0].nom][0].shape
    totals = {
        "num": np.zeros((height, width, 3), np.float64),
        "den": np.zeros((height, width, 3), np.float64),
        "coverage": np.zeros((height, width, 3), np.uint16),
    }
    split = {key: {
        "num": np.zeros((height, width, 3), np.float64),
        "den": np.zeros((height, width, 3), np.float64),
        "coverage": np.zeros((height, width, 3), np.uint16),
    } for key in ("A", "B")}
    sat_output = np.zeros((height, width), np.uint16)
    small: list[dict] = []
    info = {
        "name": label,
        "members": [f.nom for f in frames],
        "geometry": {"frame": common.nom, "solar_x_px": common.sol_x,
                     "solar_y_px": common.sol_y},
        "rotation_model": {
            "rate_deg_s": ROTATION_RATE_DEG_S,
            "rate_sigma_deg_s": ROTATION_RATE_SIGMA_DEG_S,
            "reference": ROTATION_REFERENCE_NAME,
            "status": "MODELLED_QUARANTINE; 0.76 sigma star-field fit",
        },
        "factor_extincio": {},
        "per_frame": {},
    }
    yy = np.arange(height, dtype=np.float32)[:, None]
    xx = np.arange(width, dtype=np.float32)[None, :]
    for index, frame in enumerate(frames):
        one, one_weight, one_coverage, one_info = run_stack(
            [frame], data, frame, label + "_" + frame.nom[:8])
        angle_deg, angle_sigma = rotation_model(frame, manifest)
        matrix = image_rotation_matrix(common.sol_x, common.sol_y, angle_deg)
        numerator = np.nan_to_num(one, nan=0.0) * one_weight
        warped_num = cv2.warpAffine(numerator, matrix, (width, height),
                                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                    borderValue=0)
        warped_den = cv2.warpAffine(one_weight, matrix, (width, height),
                                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                    borderValue=0)
        warped_cov = cv2.warpAffine(one_coverage, matrix, (width, height),
                                    flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT,
                                    borderValue=0)

        # Lunar centre after solar translation and theta correction.
        before = np.array([frame.lluna_x + common.sol_x - frame.sol_x,
                           frame.lluna_y + common.sol_y - frame.sol_y])
        after = matrix[:, :2] @ before + matrix[:, 2]
        distance = np.hypot(xx - after[0], yy - after[1])
        lunar_gate = np.clip((distance - (H.R_LLUNA_PX + 4.0)) / 14.0, 0.0, 1.0)
        warped_num *= lunar_gate[..., None]
        warped_den *= lunar_gate[..., None]
        warped_cov *= (lunar_gate[..., None] >= 0.999)

        totals["num"] += warped_num
        totals["den"] += warped_den
        totals["coverage"] += warped_cov
        half = "A" if index % 2 == 0 else "B"
        split[half]["num"] += warped_num
        split[half]["den"] += warped_den
        split[half]["coverage"] += warped_cov

        # Sensor saturation transferred directly through the same solar affine.
        linear = matrix[:, :2]
        source_to_output = np.c_[linear, np.array([common.sol_x, common.sol_y])
                                - linear @ np.array([frame.sol_x, frame.sol_y])]
        sat = cv2.warpAffine(data[frame.nom][1].astype(np.uint8), source_to_output,
                             (width, height), flags=cv2.INTER_NEAREST,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        sat_output += sat.astype(np.uint16)

        stride = 16
        small.append({
            "frame": frame.nom,
            "half": half,
            "num": warped_num[::stride, ::stride].astype(np.float32),
            "den": warped_den[::stride, ::stride].astype(np.float32),
            "coverage": warped_cov[::stride, ::stride].astype(np.uint16),
        })
        info["factor_extincio"][frame.nom] = one_info["factor_extincio"][frame.nom]
        info["per_frame"][frame.nom] = {
            "theta_correction_deg": angle_deg,
            "theta_1sigma_deg": angle_sigma,
            "lunar_output_x_px": float(after[0]),
            "lunar_output_y_px": float(after[1]),
            "solar_translation_dx_px": common.sol_x - frame.sol_x,
            "solar_translation_dy_px": common.sol_y - frame.sol_y,
            "single_stack": one_info,
        }
        del one, one_weight, one_coverage, numerator, warped_num, warped_den, warped_cov
    return (*combine(totals["num"], totals["den"], totals["coverage"]),
            info, split, small, sat_output)


def empirical_split_metrics(a: np.ndarray, b: np.ndarray, va: np.ndarray,
                            vb: np.ndarray, coverage: np.ndarray) -> dict:
    stride = 8
    aa = a[::stride, ::stride]
    bb = b[::stride, ::stride]
    vv = va[::stride, ::stride] + vb[::stride, ::stride]
    cc = coverage[::stride, ::stride]
    valid = np.all(np.isfinite(aa) & np.isfinite(bb) & np.isfinite(vv), axis=2)
    valid &= np.all(cc > 0, axis=2)
    z = np.where(vv > 0, (aa - bb) / np.sqrt(vv), np.nan)
    vals = z[valid]
    if not vals.size:
        return {"status": "INCONCLUSIVE", "reason": "no common split coverage"}
    med = np.nanmedian(vals, axis=0)
    mad = 1.4826 * np.nanmedian(np.abs(vals - med), axis=0)
    # A perfectly modelled independent split has robust sigma about one.
    return {
        "status": "MEASURED",
        "downsample": stride,
        "common_pixels": int(valid.sum()),
        "z_median_rgb": med.tolist(),
        "z_sigma_robust_rgb": mad.tolist(),
        "variance_scale_rgb": np.square(mad).tolist(),
    }


def contribution_metrics_from_small(small: list[dict]) -> list[dict]:
    """Low-cost leave-one-out influence on a 1/16 grid.

    Full leave-one-out TIFFs would multiply storage by the group size.  The
    numeric gate needs the influence, not another deliverable image, so each
    LOO stack is evaluated on a fixed sparse grid and discarded.
    """
    if len(small) < 2:
        return [{"frame": small[0]["frame"], "decision": "ONLY_FRAME",
                 "inclusion_test": "INCONCLUSIVE"}]
    total_num = sum((x["num"] for x in small), np.zeros_like(small[0]["num"]))
    total_den = sum((x["den"] for x in small), np.zeros_like(small[0]["den"]))
    total_coverage = sum((x["coverage"] for x in small),
                         np.zeros_like(small[0]["coverage"]))
    base = np.where(total_den > 0, total_num / np.maximum(total_den, 1e-30), np.nan)
    out = []
    for excluded in small:
        den = total_den - excluded["den"]
        remaining_coverage = total_coverage - excluded["coverage"]
        loo = np.where(den > 0, (total_num - excluded["num"]) / np.maximum(den, 1e-30), np.nan)
        d = loo - base
        valid = (np.all(np.isfinite(d), axis=2) & np.all(den > 0, axis=2)
                 & np.all(remaining_coverage > 0, axis=2))
        vals = d[valid]
        out.append({
            "frame": excluded["frame"],
            "decision": "MEASURED_PENDING_STRUCTURED_RESIDUAL_REVIEW",
            "common_pixels": int(valid.sum()),
            "loo_delta_median_adu_s_rgb": np.nanmedian(vals, axis=0).tolist(),
            "loo_delta_mad_adu_s_rgb": (1.4826 * np.nanmedian(
                np.abs(vals - np.nanmedian(vals, axis=0)), axis=0)).tolist(),
        })
        del loo
    return out


def contribution_metrics(frames: list[H.Fotograma], full: np.ndarray,
                         data: dict[str, tuple[np.ndarray, np.ndarray]]) -> list[dict]:
    """Sparse leave-one-out for the explicit theta=0 control path."""
    if len(frames) < 2:
        return [{"frame": frames[0].nom, "decision": "ONLY_FRAME",
                 "inclusion_test": "INCONCLUSIVE"}]
    stride = 16
    base = full[::stride, ::stride]
    out = []
    for excluded in frames:
        subset = [f for f in frames if f.nom != excluded.nom]
        reference = min(subset, key=lambda f: abs(
            f.t_rel_c2 - frames[len(frames) // 2].t_rel_c2))
        loo, _, coverage, _ = run_stack(
            subset, data, reference, f"loo_without_{excluded.nom[:8]}")
        delta = loo[::stride, ::stride] - base
        valid = np.all(np.isfinite(delta), axis=2)
        valid &= np.all(coverage[::stride, ::stride] > 0, axis=2)
        values = delta[valid]
        centre = np.nanmedian(values, axis=0)
        out.append({
            "frame": excluded.nom,
            "decision": "ACCEPTED",
            "common_pixels": int(valid.sum()),
            "loo_delta_median_adu_s_rgb": centre.tolist(),
            "loo_delta_mad_adu_s_rgb": (
                1.4826 * np.nanmedian(np.abs(values - centre), axis=0)).tolist(),
        })
        del loo, coverage
    return out


def contribution_metrics_translation_sparse(
    frames: list[H.Fotograma], data: dict[str, tuple[np.ndarray, np.ndarray]],
    reference: H.Fotograma,
) -> list[dict]:
    """Exact additive LOO on a fixed 1/16 grid with one extra pass per frame.

    Rebuilding N stacks of N-1 members is quadratic (and especially wasteful
    for the 26-frame short-exposure group).  Each independently drizzled
    numerator and inverse-variance denominator is additive in the common
    theta=0 geometry, so the same LOO result is obtained by subtraction.
    """
    stride = 16
    small = []
    for index, frame in enumerate(frames):
        image, weight, coverage, _ = run_stack(
            [frame], data, reference, f"loo_component_{frame.nom[:8]}")
        small.append({
            "frame": frame.nom,
            "half": "A" if index % 2 == 0 else "B",
            "num": (np.nan_to_num(image[::stride, ::stride], nan=0.0)
                    * weight[::stride, ::stride]).astype(np.float32),
            "den": weight[::stride, ::stride].astype(np.float32),
            "coverage": coverage[::stride, ::stride].astype(np.uint16),
        })
        del image, weight, coverage
    return contribution_metrics_from_small(small)


def write_group(outdir: Path, frames: list[H.Fotograma], do_loo: bool,
                translation_control: bool, temporal_segment: str) -> dict:
    outdir.mkdir(parents=True, exist_ok=False)
    reference = min(frames, key=lambda f: abs(f.t_rel_c2 - np.median(
        [x.t_rel_c2 for x in frames])))
    data = {f.nom: A.carrega(f) for f in frames}
    if translation_control:
        image, weight, coverage, info = run_stack(frames, data, reference, outdir.name)
        split_components = None
        small = []
        saturated_any = np.zeros(data[reference.nom][1].shape, np.uint16)
    else:
        image, weight, coverage, info, split_components, small, saturated_any = \
            run_stack_rotation_model(frames, data, outdir.name)
    variance = np.where(weight > 0, 1.0 / weight, np.nan).astype(np.float32)
    effective_s = (coverage.astype(np.float32) / CHANNEL_SAMPLE_FACTOR) * reference.exp_s
    raw_saturation = {}
    common = next(x for x in H.llegeix_manifest() if x.nom == A.NOM_EPOCA_COMUNA)
    for f in frames:
        sat = data[f.nom][1]
        raw_saturation[f.nom] = int(sat.sum())
        if translation_control:
            dx, dy = common.sol_x - f.sol_x, common.sol_y - f.sol_y
            affine = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], np.float64)
            sat_output = cv2.warpAffine(
                sat.astype(np.uint8), affine, (sat.shape[1], sat.shape[0]),
                flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            saturated_any += sat_output.astype(np.uint16)

    save_tiff(outdir / "MASTER_linear_float32_ADU_s.tif", image)
    np.save(outdir / "VARIANCE_ADU2_s2.npy", variance)
    np.save(outdir / "INVVAR_WEIGHT.npy", weight.astype(np.float32))
    np.save(outdir / "COVERAGE_SAMPLES.npy", coverage)
    np.save(outdir / "COVERAGE_EFFECTIVE_S.npy", effective_s)
    np.save(outdir / "SATURATION_OUTPUT_COUNT.npy", saturated_any)
    preview(outdir / "MASTER_preview_neutral.jpg", image)

    split_a, split_b = split_balanced(frames)
    split_info: dict
    if split_b:
        if translation_control:
            ref_a = min(split_a, key=lambda f: abs(f.t_rel_c2 - reference.t_rel_c2))
            ref_b = min(split_b, key=lambda f: abs(f.t_rel_c2 - reference.t_rel_c2))
            ia, wa, ca, ia_info = run_stack(split_a, data, ref_a, outdir.name + "_A")
            ib, wb, cb, ib_info = run_stack(split_b, data, ref_b, outdir.name + "_B")
        else:
            ia, wa, ca = combine(split_components["A"]["num"], split_components["A"]["den"],
                                 split_components["A"]["coverage"])
            ib, wb, cb = combine(split_components["B"]["num"], split_components["B"]["den"],
                                 split_components["B"]["coverage"])
            ia_info = ib_info = info
        va = np.where(wa > 0, 1.0 / wa, np.nan).astype(np.float32)
        vb = np.where(wb > 0, 1.0 / wb, np.nan).astype(np.float32)
        save_tiff(outdir / "SPLIT_A_linear_float32_ADU_s.tif", ia)
        save_tiff(outdir / "SPLIT_B_linear_float32_ADU_s.tif", ib)
        split_info = empirical_split_metrics(ia, ib, va, vb, np.minimum(ca, cb))
        split_info.update({"A": [f.nom for f in split_a], "B": [f.nom for f in split_b],
                           "A_geometry": ia_info.get("geometria"),
                           "B_geometry": ib_info.get("geometria")})
        # Store the standardized difference sparsely for QA, not as a display layer.
        z = ((ia[::4, ::4] - ib[::4, ::4])
             / np.sqrt(va[::4, ::4] + vb[::4, ::4]))
        np.savez_compressed(outdir / "SPLIT_difference_z_ds4.npz", z=z.astype(np.float32))
        del ia, ib, wa, wb, ca, cb, va, vb, z
    else:
        split_info = {"status": "INCONCLUSIVE", "reason": "single-frame exposure group",
                      "A": [f.nom for f in split_a], "B": []}

    loo = (contribution_metrics_from_small(small) if do_loo and not translation_control else
           contribution_metrics_translation_sparse(frames, data, reference) if do_loo else [
        {"frame": f.nom, "decision": "ACCEPTED",
         "inclusion_test": "deferred to sparse all-groups QA"} for f in frames])

    transforms = []
    common = next(f for f in H.llegeix_manifest() if f.nom == A.NOM_EPOCA_COMUNA)
    for f in frames:
        transforms.append({
            "frame": f.nom,
            "t_rel_c2_s": f.t_rel_c2,
            "dx_output_px": common.sol_x - f.sol_x,
            "dy_output_px": common.sol_y - f.sol_y,
            "theta_deg": (0.0 if translation_control else info["per_frame"][f.nom]["theta_correction_deg"]),
            "theta_status": ("theta=0 ACCEPTED; weak rotation prior quarantined" if translation_control else
                             "MODELLED_QUARANTINE applied per frame; compare theta=0 control"),
            "solar_x_px": f.sol_x,
            "solar_y_px": f.sol_y,
            "lunar_x_px": f.lluna_x,
            "lunar_y_px": f.lluna_y,
            "extinction_factor": info["factor_extincio"][f.nom],
            "raw_saturated_pixels": raw_saturation[f.nom],
        })
    with (outdir / "TRANSFORMS.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(transforms[0]))
        writer.writeheader()
        writer.writerows(transforms)

    products = [p for p in sorted(outdir.iterdir()) if p.is_file()
                and p.name not in {"STACK_RECEIPT.json", "SHA256SUMS.txt"}]
    receipt = {
        "schema": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "train": "VIXEN_VSD90SS_CANON_R6_MARK_III",
        "frame": "CORONA_SOLAR",
        "temporal_segment": temporal_segment,
        "phenomenon_policy": ("contact sequence kept separate; this corona-frame stack "
                              "is not authority for beads/prominences/chromosphere"
                              if temporal_segment in {"C2", "C3"}
                              else ("temporal sweep kept independent after a structured "
                                    "early-versus-late split residual"
                                    if temporal_segment in {"EARLY", "LATE", "LATE1", "LATE2"}
                                    else "totality exposure group")),
        "exposure_s": reference.exp_s,
        "exposure_authority": ({
            "source": "Canon MakerNote numeric ExposureTime",
            "value_s": CANON_LONG_EXPOSURE_S,
            "historical_10.3s_manifest_overridden_in_memory": True,
        } if abs(reference.exp_nominal - 10.0) < 1e-9 else {
            "source": "canonical manifest/EXIF",
            "value_s": reference.exp_s,
        }),
        "members": [f.nom for f in frames],
        "candidates": [f.nom for f in frames],
        "accepted": [],
        "rejected": [],
        "duplicates": [],
        "calibration": "linear CFA; temperature-selected trimmed-mean dark; PRNU v2; no clipping/debayer before drizzle",
        "registration": ("per-frame solar translation from lunar limb + DE440 + stellar absolute anchor; "
                         + ("theta=0 accepted; one-pass CFA drizzle; reference lunar support no-data" if translation_control else
                             "smooth theta(t) star-field prior applied about common solar centre; all lunar discs excluded")),
        "solar_radius_model": {"radius_arcsec": SOLAR_RADIUS_ARCSEC,
                               "radius_px": SOLAR_RADIUS_PX,
                               "plate_scale_arcsec_px": H.ESCALA,
                               "authority": SOLAR_RADIUS_AUTHORITY,
                               "historical_959_arcsec_overridden_in_process": True},
        "photometry": "ADU/s; k=0.402 mag/airmass normalized to 572A2969; common measured sky pedestal",
        "weighting": "per-pixel inverse variance t^2/(S/g+RN^2), saturation and lunar validity gates",
        "stack_info": info,
        "split": split_info,
        "leave_one_out": loo,
        "leave_one_out_method": {
            "method": "fixed-reference additive numerator/denominator subtraction",
            "stride": 16,
            "reference": reference.nom,
            "decision_status": "MEASURED_PENDING_STRUCTURED_RESIDUAL_REVIEW",
        },
        "input_hashes": frame_hashes(frames),
        "calibrator_hashes": calibrator_hashes(frames),
        "software": {
            "argv": sys.argv,
            "stack_vixen_s6.py": {"path": str(Path(__file__).resolve()),
                                   "sha256": sha256(Path(__file__).resolve())},
            "apila_hdr4_vixen.py": {"path": str(Path(A.__file__).resolve()),
                                     "sha256": sha256(Path(A.__file__).resolve())},
            "hdr_corona_vixen.py": {"path": str(Path(H.__file__).resolve()),
                                     "sha256": sha256(Path(H.__file__).resolve())},
        },
        "products": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
                     for p in products],
        "qa": {
            "finite_fraction_rgb": [float(np.isfinite(image[..., c]).mean()) for c in range(3)],
            "coverage_median_rgb": [float(np.median(coverage[..., c])) for c in range(3)],
            "variance_median_finite_rgb": [float(np.nanmedian(variance[..., c])) for c in range(3)],
            "raw_saturated_pixels": raw_saturation,
        },
        "verdict": ("STACK_PENDING_SPLIT_LOO_VISUAL_ACCEPTANCE; THETA0_GEOMETRY_ACCEPTED" if translation_control else
                    "PILOT_PENDING_THETA0_DIFFERENCE_AND_VISUAL_NULL_REVIEW"),
        "source_mutations": 0,
    }
    atomic_json(outdir / "STACK_RECEIPT.json", receipt)
    receipt_hash = sha256(outdir / "STACK_RECEIPT.json")
    with (outdir / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for p in sorted(outdir.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                fh.write(f"{sha256(p)}  {p.name}\n")
    print(f"{outdir}: {len(frames)} frames; receipt {receipt_hash}", flush=True)
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--exposure", type=float)
    sel.add_argument("--exposures", type=float, nargs="+",
                     help="explicit set of exposure groups")
    sel.add_argument("--all", action="store_true")
    ap.add_argument("--leave-one-out", action="store_true",
                    help="run sparse LOO influence (recommended for the pilot)")
    ap.add_argument("--temporal-segment",
                    choices=("all", "C2", "EARLY", "LATE", "LATE1", "LATE2", "C3"),
                    default="all",
                    help="split the 1/3200-s contact sequence; never mix C2 and C3 phenomena")
    geometry = ap.add_mutually_exclusive_group()
    geometry.add_argument("--translation-control", action="store_true",
                          help="deprecated alias: theta=0 is now the safe default")
    geometry.add_argument("--experimental-theta-model", action="store_true",
                          help="apply the quarantined theta(t) prior for null testing only")
    args = ap.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    frames = [f for f in physical_manifest() if f.usat]
    if args.temporal_segment == "C2":
        frames = [f for f in frames if 2958 <= int(f.nom[4:8]) <= 2966]
    elif args.temporal_segment == "EARLY":
        frames = [f for f in frames if 6.0 <= f.t_rel_c2 < 30.0]
    elif args.temporal_segment == "LATE":
        frames = [f for f in frames if 65.0 <= f.t_rel_c2 < 93.0]
    elif args.temporal_segment == "LATE1":
        frames = [f for f in frames if 65.0 <= f.t_rel_c2 < 80.0]
    elif args.temporal_segment == "LATE2":
        frames = [f for f in frames if 80.0 <= f.t_rel_c2 < 93.0]
    elif args.temporal_segment == "C3":
        frames = [f for f in frames if 3009 <= int(f.nom[4:8]) <= 3025]
    groups: dict[float, list[H.Fotograma]] = {}
    for f in frames:
        groups.setdefault(f.exp_s, []).append(f)
    selected = sorted(groups)
    if args.exposure is not None:
        selected = [min(groups, key=lambda e: abs(e - args.exposure))]
        if abs(selected[0] - args.exposure) > 1e-8:
            raise SystemExit(f"exposure not found: {args.exposure}")
    elif args.exposures is not None:
        selected = []
        for requested in args.exposures:
            exposure = min(groups, key=lambda e: abs(e - requested))
            if abs(exposure - requested) > 1e-8:
                raise SystemExit(f"exposure not found: {requested}")
            if exposure not in selected:
                selected.append(exposure)
        selected.sort()

    translation_control = not args.experimental_theta_model
    summary = []
    for exposure in selected:
        group = sorted(groups[exposure], key=lambda f: f.t_rel_c2)
        dest = args.out / exp_tag(exposure)
        summary.append(write_group(dest, group, args.leave_one_out,
                                   translation_control, args.temporal_segment))
    atomic_json(args.out / "RUN_RECEIPT.json", {
        "schema": "VIXEN_R6_S6_RUN_V2",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "temporal_segment": args.temporal_segment,
        "groups": [{"path": exp_tag(r["exposure_s"]), "exposure_s": r["exposure_s"],
                    "n": len(r["members"]), "verdict": r["verdict"]} for r in summary],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
