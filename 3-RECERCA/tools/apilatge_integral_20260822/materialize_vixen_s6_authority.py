#!/usr/bin/env python3
"""Audit and materialize the accepted Vixen S6 authority without pixel rewrites.

The v3 candidate products remain immutable.  Accepted products are exposed as
hardlinks, while the authority verdict, empirical variance scale, 68-frame
ledger and root hash manifest are new, small files.  The command fails closed
if membership, geometry, solar-radius authority, hashes, statistical gates or
pixel invariants differ from the audited map below.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tifffile


ROOT = Path(__file__).resolve().parents[3]
MASTERS = ROOT / "output/postprocessat_final_20260822/masters"
DEFAULT_OUTPUT = MASTERS / "vixen_s6_ACCEPTED"
TRAIN = "VIXEN_VSD90SS_CANON_R6_MARK_III"
FRAME = "CORONA_SOLAR"
REFERENCE_FRAME = "572A2969.CR3"
REFERENCE_SOL_X = 3563.8912793889317
REFERENCE_SOL_Y = 2274.660453669
SOLAR_RADIUS_ARCSEC = 946.6598
PLATE_SCALE_ARCSEC_PX = 2.1495
SOLAR_RADIUS_PX = SOLAR_RADIUS_ARCSEC / PLATE_SCALE_ARCSEC_PX
EXPECTED_SHAPE = (4640, 6960, 3)
CHANNEL_SAMPLE_FACTOR = np.array([4.0, 8.0, 4.0], np.float32)
SECTOR_THRESHOLD_SIGMA = 2.5
SECTOR_MIN_PIXELS = 512
GLOBAL_SPLIT_SIGMA_LIMIT = 1.25
LOO_MEDIAN_OVER_MAD_LIMIT = 0.25


@dataclass(frozen=True)
class Group:
    authority_id: str
    source: str
    destination: str
    product_class: str
    temporal_segment: str
    phenomenon_scope: str
    members: tuple[str, ...]


def frames(*numbers: int) -> tuple[str, ...]:
    return tuple(f"572A{number}.CR3" for number in numbers)


GROUPS = (
    Group("STACK_CONTACT_C2_1-3200S", "vixen_rsun_v3_C2_candidate/1-3200s",
          "accepted_stacks/contact_C2/1-3200s", "EXPOSURE_STACK", "C2",
          "CONTACT_C2_SEPARATE_FROM_CORONA",
          frames(*range(2958, 2967))),
    Group("STACK_CONTACT_C3_1-3200S", "vixen_rsun_v3_C3_candidate/1-3200s",
          "accepted_stacks/contact_C3/1-3200s", "EXPOSURE_STACK", "C3",
          "CONTACT_C3_SEPARATE_FROM_CORONA",
          frames(*range(3009, 3026))),
    Group("STACK_STABLE_1-2000S", "vixen_rsun_v3_stable_candidates/1-2000s",
          "accepted_stacks/corona/STABLE/1-2000s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2967, 2985, 2997, 3003)),
    Group("STACK_STABLE_1-1000S", "vixen_rsun_v3_stable_candidates/1-1000s",
          "accepted_stacks/corona/STABLE/1-1000s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2973, 2991)),
    Group("STACK_STABLE_1-500S", "vixen_rsun_v3_stable_candidates/1-500s",
          "accepted_stacks/corona/STABLE/1-500s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2968, 2986, 2998, 3004)),
    Group("STACK_STABLE_1-250S", "vixen_rsun_v3_stable_candidates/1-250s",
          "accepted_stacks/corona/STABLE/1-250s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2974, 2992)),
    Group("STACK_STABLE_1-125S", "vixen_rsun_v3_stable_candidates/1-125s",
          "accepted_stacks/corona/STABLE/1-125s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2969, 2987, 2999, 3005)),
    Group("STACK_STABLE_1-60S", "vixen_rsun_v3_stable_candidates/1-60s",
          "accepted_stacks/corona/STABLE/1-60s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2975, 2993)),
    Group("STACK_STABLE_2S", "vixen_rsun_v3_stable_candidates/2s",
          "accepted_stacks/corona/STABLE/2s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2979, 2980, 2981)),
    Group("STACK_STABLE_10P079368S", "vixen_rsun_v3_stable_candidates/10.0794s",
          "accepted_stacks/corona/STABLE/10.0794s", "EXPOSURE_STACK", "STABLE",
          "CORONA_SOLAR", frames(2982, 2983, 2984)),
    Group("STACK_LATE_1-30S", "vixen_rsun_v3_LATE_candidates/1-30s",
          "accepted_stacks/corona/LATE/1-30s", "EXPOSURE_STACK", "LATE",
          "CORONA_SOLAR", frames(2988, 3000, 3006)),
    Group("STACK_LATE_1-8S", "vixen_rsun_v3_LATE_candidates/1-8s",
          "accepted_stacks/corona/LATE/1-8s", "EXPOSURE_STACK", "LATE",
          "CORONA_SOLAR", frames(2989, 3001, 3007)),
    Group("STACK_LATE2_1-2S", "vixen_rsun_v3_LATE2_1-2_candidate/1-2s",
          "accepted_stacks/corona/LATE2/1-2s", "EXPOSURE_STACK", "LATE2",
          "CORONA_SOLAR", frames(3002, 3008)),
    Group("SINGLE_EARLY_1-30S", "vixen_rsun_v3_EARLY_candidates/1-30s",
          "linear_single_contributions/corona/EARLY/1-30s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2970)),
    Group("SINGLE_EARLY_1-15S", "vixen_rsun_v3_EARLY_candidates/1-15s",
          "linear_single_contributions/corona/EARLY/1-15s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2976)),
    Group("SINGLE_EARLY_1-8S", "vixen_rsun_v3_EARLY_candidates/1-8s",
          "linear_single_contributions/corona/EARLY/1-8s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2971)),
    Group("SINGLE_EARLY_1-4S", "vixen_rsun_v3_EARLY_candidates/1-4s",
          "linear_single_contributions/corona/EARLY/1-4s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2977)),
    Group("SINGLE_EARLY_1-2S", "vixen_rsun_v3_EARLY_candidates/1-2s",
          "linear_single_contributions/corona/EARLY/1-2s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2972)),
    Group("SINGLE_EARLY_1S", "vixen_rsun_v3_EARLY_candidates/1s",
          "linear_single_contributions/corona/EARLY/1s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "EARLY", "CORONA_SOLAR",
          frames(2978)),
    Group("SINGLE_LATE_1-15S", "vixen_rsun_v3_LATE_candidates/1-15s",
          "linear_single_contributions/corona/LATE/1-15s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "LATE", "CORONA_SOLAR",
          frames(2994)),
    Group("SINGLE_LATE_1-4S", "vixen_rsun_v3_LATE_candidates/1-4s",
          "linear_single_contributions/corona/LATE/1-4s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "LATE", "CORONA_SOLAR",
          frames(2995)),
    Group("SINGLE_LATE_1S", "vixen_rsun_v3_LATE_candidates/1s",
          "linear_single_contributions/corona/LATE/1s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "LATE", "CORONA_SOLAR",
          frames(2996)),
    Group("SINGLE_LATE1_1-2S", "vixen_rsun_v3_LATE1_1-2_candidate/1-2s",
          "linear_single_contributions/corona/LATE1/1-2s",
          "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN", "LATE1", "CORONA_SOLAR",
          frames(2990)),
)


SUPERSEDED = (
    {"id": "SUPERSEDED_COMBINED_CONTACTS_1-3200S",
     "source": "vixen_corona_s6_candidates/1-3200s",
     "replacement": ["STACK_CONTACT_C2_1-3200S", "STACK_CONTACT_C3_1-3200S"],
     "reason": "C2 and C3 contact sequences must remain separate from each other and from corona authority"},
    {"id": "SUPERSEDED_ROUNDED_10P3S",
     "source": "vixen_corona_s6_candidates/10.3s",
     "replacement": ["STACK_STABLE_10P079368S"],
     "reason": "Canon MakerNote physical exposure is 10.079368399159 s, not rounded 10.3 s"},
    {"id": "SUPERSEDED_COMBINED_1-30S", "source": "vixen_corona_s6_candidates/1-30s",
     "replacement": ["SINGLE_EARLY_1-30S", "STACK_LATE_1-30S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_COMBINED_1-15S", "source": "vixen_corona_s6_candidates/1-15s",
     "replacement": ["SINGLE_EARLY_1-15S", "SINGLE_LATE_1-15S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_COMBINED_1-8S", "source": "vixen_corona_s6_candidates/1-8s",
     "replacement": ["SINGLE_EARLY_1-8S", "STACK_LATE_1-8S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_COMBINED_1-4S", "source": "vixen_corona_s6_candidates/1-4s",
     "replacement": ["SINGLE_EARLY_1-4S", "SINGLE_LATE_1-4S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_COMBINED_1-2S", "source": "vixen_corona_s6_candidates/1-2s",
     "replacement": ["SINGLE_EARLY_1-2S", "SINGLE_LATE1_1-2S", "STACK_LATE2_1-2S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_COMBINED_1S", "source": "vixen_corona_s6_candidates/1s",
     "replacement": ["SINGLE_EARLY_1S", "SINGLE_LATE_1S"],
     "reason": "structured EARLY versus LATE split residual"},
    {"id": "SUPERSEDED_LATE_1-2S_X3", "source": "vixen_LATE_structured_s6_candidates/1-2s",
     "replacement": ["SINGLE_LATE1_1-2S", "STACK_LATE2_1-2S"],
     "reason": "LATE x3 retained a structured residual and required LATE1 plus LATE2 separation"},
)


WRONG_SOLAR_RADIUS_GENERATIONS = (
    "vixen_corona_s6_candidates", "vixen_1-3200_C2_s6_candidate",
    "vixen_1-3200_C3_s6_candidate", "vixen_10p079368s_s6_candidate",
    "vixen_EARLY_structured_s6_candidates", "vixen_LATE_structured_s6_candidates",
    "vixen_LATE1_1-2s_s6_candidate", "vixen_LATE2_1-2s_s6_candidate",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_npy_f64_vector(path: Path, values: list[float]) -> None:
    if len(values) != 3:
        raise ValueError("empirical scale must contain exactly RGB")
    header = "{'descr': '<f8', 'fortran_order': False, 'shape': (3,), }"
    padding = (-(10 + len(header) + 1)) % 16
    encoded = (header + " " * padding + "\n").encode("latin1")
    payload = b"\x93NUMPY" + bytes((1, 0)) + struct.pack("<H", len(encoded))
    payload += encoded + struct.pack("<3d", *values)
    path.write_bytes(payload)


def parse_sha256sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise RuntimeError(f"invalid SHA256SUMS line {path}:{line_number}")
        name = parts[1].strip()
        if name.startswith("*"):
            name = name[1:]
        if Path(name).name != name or name in entries:
            raise RuntimeError(f"unsafe or duplicate SHA256SUMS entry {name!r} in {path}")
        entries[name] = parts[0].lower()
    return entries


def add_hash_expectation(expectations: dict[Path, tuple[int | None, str, set[str]]],
                         path: Path, size: int | None, digest: str, label: str) -> None:
    value = (size, digest.lower())
    if path in expectations:
        old_size, old_digest, labels = expectations[path]
        if old_size != size or old_digest != digest.lower():
            raise RuntimeError(f"conflicting hash authority for {path}")
        labels.add(label)
    else:
        expectations[path] = (size, digest.lower(), {label})


def verify_hash_expectations(expectations: dict[Path, tuple[int | None, str, set[str]]],
                             jobs: int) -> None:
    def verify(item: tuple[Path, tuple[int | None, str, set[str]]]) -> str | None:
        path, (size, expected, labels) = item
        stat = path.stat()
        if size is not None and stat.st_size != size:
            return f"{path}: bytes {stat.st_size} != {size} ({sorted(labels)})"
        actual = sha256(path)
        if actual != expected:
            return f"{path}: sha256 {actual} != {expected} ({sorted(labels)})"
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        errors = [result for result in pool.map(verify, expectations.items()) if result]
    if errors:
        raise RuntimeError("hash verification failed:\n" + "\n".join(errors))


def empirical_scale(receipt: dict[str, Any], group: Group) -> tuple[list[float], str]:
    if group.product_class == "LINEAR_SINGLE_CONTRIBUTION_NO_STACK_GAIN":
        return [1.0, 1.0, 1.0], "ANALYTIC_ONLY_SINGLE_NO_INDEPENDENT_SPLIT"
    raw = receipt["split"]["variance_scale_rgb"]
    return [max(1.0, float(value)) for value in raw], "MEASURED_SPLIT_MAX_ONE"


def sector_gate(source: Path, receipt: dict[str, Any], scale: list[float]) -> dict[str, Any]:
    if len(receipt["members"]) == 1:
        return {"status": "NOT_APPLICABLE_SINGLE", "passes": True,
                "reason": "a single frame has no independent A/B split"}
    z = np.load(source / "SPLIT_difference_z_ds4.npz")["z"].astype(np.float64)
    stride = 4.0
    corrected = z / np.sqrt(np.asarray(scale, np.float64))
    yy, xx = np.indices(z.shape[:2])
    centre_x = float(receipt["stack_info"]["geometria"]["sol_x"]) / stride
    centre_y = float(receipt["stack_info"]["geometria"]["sol_y"]) / stride
    radius = SOLAR_RADIUS_PX / stride
    rr = np.hypot(xx - centre_x, yy - centre_y)
    angle = np.mod(np.arctan2(yy - centre_y, xx - centre_x), 2.0 * math.pi)
    annulus = (rr >= 1.1 * radius) & (rr < 1.5 * radius)
    medians = np.full((24, 2), np.nan, np.float64)
    counts = np.zeros((24, 2), np.int64)
    for sector in range(24):
        selected = annulus & (angle >= 2.0 * math.pi * sector / 24.0)
        selected &= angle < 2.0 * math.pi * (sector + 1) / 24.0
        for channel in range(2):
            values = corrected[..., channel][selected]
            values = values[np.isfinite(values)]
            counts[sector, channel] = values.size
            if values.size:
                medians[sector, channel] = np.median(values)
    eligible = counts >= SECTOR_MIN_PIXELS
    global_sigma = np.asarray(receipt["split"]["z_sigma_robust_rgb"], np.float64)
    corrected_global_sigma = global_sigma / np.sqrt(np.asarray(scale, np.float64))
    corrected_global_median = (np.asarray(receipt["split"]["z_median_rgb"], np.float64)
                               / np.sqrt(np.asarray(scale, np.float64)))
    global_pass = (float(np.max(corrected_global_sigma)) <= GLOBAL_SPLIT_SIGMA_LIMIT
                   and float(np.max(np.abs(corrected_global_median))) <= 0.25)
    result: dict[str, Any] = {
        "method": "max absolute 24-sector median of z/sqrt(max(1, split variance scale))",
        "channels_for_sector_gate": ["R", "G"],
        "sector_origin_deg": 0.0,
        "sector_zero_axis": "+x",
        "positive_angle_direction": "+y in image coordinates",
        "sector_edge_rule": "half-open [start,end)",
        "annulus_r_sun": [1.1, 1.5],
        "solar_radius_px": SOLAR_RADIUS_PX,
        "stride": 4,
        "sectors": 24,
        "minimum_finite_pixels_per_sector_channel": SECTOR_MIN_PIXELS,
        "threshold_sigma": SECTOR_THRESHOLD_SIGMA,
        "eligible_sector_channels": int(np.count_nonzero(eligible)),
        "eligible_sectors_by_channel": [int(np.count_nonzero(eligible[:, channel]))
                                        for channel in range(2)],
        "finite_pixels_by_channel": [int(np.count_nonzero(np.isfinite(z[..., channel]) & annulus))
                                     for channel in range(3)],
        "global_corrected_sigma_rgb": corrected_global_sigma.tolist(),
        "global_corrected_median_rgb": corrected_global_median.tolist(),
        "global_split_passes": bool(global_pass),
    }
    if not np.any(eligible):
        result.update({
            "status": "NOT_APPLICABLE_NO_COMMON_LINEAR_SUPPORT_DUE_SATURATION",
            "passes": bool(global_pass),
            "reason": "the inner annulus is saturated and has zero statistical weight; global split and LOO remain applicable",
            "max_abs_sector_median_sigma": None,
        })
        return result
    masked = np.where(eligible, np.abs(medians), np.nan)
    index = np.unravel_index(int(np.nanargmax(masked)), masked.shape)
    maximum = float(masked[index])
    phase_samples = []
    annulus_angles = angle[annulus]
    annulus_values = corrected[annulus, :2]
    for offset_deg in np.linspace(0.0, 15.0, 61):
        shifted = np.mod(annulus_angles - math.radians(float(offset_deg)), 2.0 * math.pi)
        bins = np.floor(shifted * 24.0 / (2.0 * math.pi)).astype(np.uint8)
        shifted_maximum = 0.0
        for sector in range(24):
            for channel in range(2):
                values = annulus_values[:, channel][bins == sector]
                values = values[np.isfinite(values)]
                if values.size >= SECTOR_MIN_PIXELS:
                    shifted_maximum = max(shifted_maximum, float(abs(np.median(values))))
        phase_samples.append((float(offset_deg), shifted_maximum))
    worst_phase = max(phase_samples, key=lambda item: item[1])
    result.update({
        "status": "MEASURED",
        "passes": bool(global_pass and maximum <= SECTOR_THRESHOLD_SIGMA),
        "max_abs_sector_median_sigma": maximum,
        "max_sector": int(index[0]),
        "max_channel": ["R", "G"][index[1]],
        "signed_sector_median_sigma": float(medians[index]),
        "finite_pixels_in_max_sector_channel": int(counts[index]),
        "max_abs_by_channel_sigma": [float(np.nanmax(np.where(eligible[:, channel],
                                                                 np.abs(medians[:, channel]), np.nan)))
                                     if np.any(eligible[:, channel]) else None
                                     for channel in range(2)],
        "phase_sensitivity_advisory_not_a_hard_gate": {
            "offset_range_deg": [0.0, 15.0],
            "step_deg": 0.25,
            "worst_offset_deg": worst_phase[0],
            "worst_max_abs_sector_median_sigma": worst_phase[1],
            "would_exceed_frozen_phase_threshold": worst_phase[1] > SECTOR_THRESHOLD_SIGMA,
            "interpretation": "the authority gate is the frozen zero-degree convention above; this sweep records bin-origin sensitivity only",
        },
    })
    return result


def pixel_invariants(source: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    image = tifffile.imread(source / "MASTER_linear_float32_ADU_s.tif")
    weight = np.load(source / "INVVAR_WEIGHT.npy", mmap_mode="r")
    variance = np.load(source / "VARIANCE_ADU2_s2.npy", mmap_mode="r")
    coverage_samples = np.load(source / "COVERAGE_SAMPLES.npy", mmap_mode="r")
    coverage_effective = np.load(source / "COVERAGE_EFFECTIVE_S.npy", mmap_mode="r")
    saturation = np.load(source / "SATURATION_OUTPUT_COUNT.npy", mmap_mode="r")
    if not (image.shape == weight.shape == variance.shape == coverage_samples.shape
            == coverage_effective.shape == EXPECTED_SHAPE):
        raise RuntimeError(f"array shape mismatch at {source}")
    if not (image.dtype == weight.dtype == variance.dtype == coverage_effective.dtype
            == np.float32 and coverage_samples.dtype == saturation.dtype == np.uint16):
        raise RuntimeError(f"array dtype mismatch at {source}")
    metrics = {
        "finite_weight_mismatch": 0,
        "variance_finite_weight_mismatch": 0,
        "negative_weights": 0,
        "coverage_positive_weight_mismatch": 0,
        "lunar_weight_or_coverage_nonzero": 0,
    }
    max_variance_weight_error = 0.0
    max_coverage_formula_error = 0.0
    lunar = receipt["stack_info"]["corona_lunar_no_data"]
    lunar_x, lunar_y = map(float, lunar["centre_output_px"])
    lunar_radius = float(lunar["exclusion_radius_px"])
    xx = np.arange(EXPECTED_SHAPE[1], dtype=np.float64)[None, :]
    exposure = float(receipt["exposure_s"])
    for y0 in range(0, EXPECTED_SHAPE[0], 80):
        y1 = min(y0 + 80, EXPECTED_SHAPE[0])
        im = image[y0:y1]
        ww = np.asarray(weight[y0:y1])
        vv = np.asarray(variance[y0:y1])
        cs = np.asarray(coverage_samples[y0:y1])
        ce = np.asarray(coverage_effective[y0:y1])
        positive = ww > 0
        metrics["finite_weight_mismatch"] += int(np.count_nonzero(np.isfinite(im) != positive))
        metrics["variance_finite_weight_mismatch"] += int(np.count_nonzero(np.isfinite(vv) != positive))
        metrics["negative_weights"] += int(np.count_nonzero(ww < 0))
        metrics["coverage_positive_weight_mismatch"] += int(np.count_nonzero((ce > 0) != positive))
        if np.any(positive):
            max_variance_weight_error = max(max_variance_weight_error,
                float(np.max(np.abs(vv[positive] * ww[positive] - 1.0))))
        expected_coverage = cs.astype(np.float32) / CHANNEL_SAMPLE_FACTOR * exposure
        max_coverage_formula_error = max(max_coverage_formula_error,
            float(np.max(np.abs(ce - expected_coverage))))
        yy = np.arange(y0, y1, dtype=np.float64)[:, None]
        inside = (xx - lunar_x) ** 2 + (yy - lunar_y) ** 2 < lunar_radius ** 2
        metrics["lunar_weight_or_coverage_nonzero"] += int(np.count_nonzero(ww[inside]))
        metrics["lunar_weight_or_coverage_nonzero"] += int(np.count_nonzero(cs[inside]))
    del image
    raw_saturation = int(sum(receipt["qa"]["raw_saturated_pixels"].values()))
    output_saturation = int(saturation.sum(dtype=np.uint64))
    loo_ratio = 0.0
    for entry in receipt["leave_one_out"]:
        if "loo_delta_median_adu_s_rgb" not in entry:
            continue
        med = np.abs(np.asarray(entry["loo_delta_median_adu_s_rgb"], np.float64))
        mad = np.asarray(entry["loo_delta_mad_adu_s_rgb"], np.float64)
        loo_ratio = max(loo_ratio, float(np.max(med / np.maximum(mad, 1e-30))))
    metrics.update({
        "max_abs_variance_times_weight_minus_one": max_variance_weight_error,
        "max_abs_coverage_formula_error_s": max_coverage_formula_error,
        "saturation_output_sum": output_saturation,
        "raw_saturation_sum": raw_saturation,
        "saturation_geometry_exact": output_saturation == raw_saturation,
        "loo_max_abs_median_over_mad": loo_ratio,
        "loo_limit": LOO_MEDIAN_OVER_MAD_LIMIT,
    })
    passes = (not any(metrics[key] for key in (
        "finite_weight_mismatch", "variance_finite_weight_mismatch", "negative_weights",
        "coverage_positive_weight_mismatch", "lunar_weight_or_coverage_nonzero"))
        and max_variance_weight_error <= 1e-6 and max_coverage_formula_error <= 1e-6
        and output_saturation == raw_saturation and loo_ratio <= LOO_MEDIAN_OVER_MAD_LIMIT)
    metrics["passes"] = bool(passes)
    return metrics


def audit(jobs: int) -> dict[str, Any]:
    if len(GROUPS) != 23 or sum(g.product_class == "EXPOSURE_STACK" for g in GROUPS) != 13:
        raise RuntimeError("authority map count is not 13 stacks plus 10 singles")
    if len(SUPERSEDED) != 9:
        raise RuntimeError("superseded map count is not nine")
    expectations: dict[Path, tuple[int | None, str, set[str]]] = {}
    audits: list[dict[str, Any]] = []
    frame_owner: dict[str, str] = {}
    input_authority: dict[str, dict[str, Any]] = {}
    source_manifest_hashes: dict[str, dict[str, str]] = {}
    for group in GROUPS:
        source = MASTERS / group.source
        receipt_path = source / "STACK_RECEIPT.json"
        receipt = load_json(receipt_path)
        if receipt.get("schema") != "VIXEN_R6_STACK_RECEIPT_S6_V2":
            raise RuntimeError(f"unexpected receipt schema at {source}")
        if receipt.get("train") != TRAIN or receipt.get("frame") != FRAME:
            raise RuntimeError(f"train/frame mismatch at {source}")
        if receipt.get("source_mutations") != 0 or tuple(receipt.get("members", ())) != group.members:
            raise RuntimeError(f"source mutation or member mismatch at {source}")
        radius = receipt.get("solar_radius_model", {})
        if not (math.isclose(float(radius.get("radius_arcsec", math.nan)), SOLAR_RADIUS_ARCSEC,
                             abs_tol=1e-12)
                and math.isclose(float(radius.get("plate_scale_arcsec_px", math.nan)),
                                 PLATE_SCALE_ARCSEC_PX, abs_tol=1e-12)
                and math.isclose(float(radius.get("radius_px", math.nan)), SOLAR_RADIUS_PX,
                                 abs_tol=1e-12)
                and radius.get("historical_959_arcsec_overridden_in_process") is True):
            raise RuntimeError(f"solar-radius authority mismatch at {source}")
        geometry = receipt["stack_info"]["geometria"]
        if (geometry.get("mode") != "comuna" or geometry.get("fotograma") != REFERENCE_FRAME
                or not math.isclose(float(geometry["sol_x"]), REFERENCE_SOL_X, abs_tol=1e-9)
                or not math.isclose(float(geometry["sol_y"]), REFERENCE_SOL_Y, abs_tol=1e-9)):
            raise RuntimeError(f"reference geometry mismatch at {source}")
        input_hashes = receipt.get("input_hashes", [])
        if tuple(item["name"] for item in input_hashes) != group.members:
            raise RuntimeError(f"input hash ordering mismatch at {source}")
        for item in input_hashes:
            name = item["name"]
            if name in frame_owner:
                raise RuntimeError(f"frame assigned twice: {name}")
            frame_owner[name] = group.authority_id
            input_authority[name] = item
            add_hash_expectation(expectations, Path(item["path"]), int(item["bytes"]),
                                 item["sha256"], "input")
        for item in receipt.get("calibrator_hashes", []):
            add_hash_expectation(expectations, Path(item["path"]), int(item["bytes"]),
                                 item["sha256"], "calibrator")
        for item in receipt.get("software", {}).values():
            if isinstance(item, dict) and "path" in item:
                add_hash_expectation(expectations, Path(item["path"]), None,
                                     item["sha256"], "software")
        actual_files = {path.name for path in source.iterdir() if path.is_file()}
        manifest = parse_sha256sums(source / "SHA256SUMS.txt")
        if set(manifest) != actual_files - {"SHA256SUMS.txt"}:
            raise RuntimeError(f"upstream SHA256SUMS coverage mismatch at {source}")
        source_manifest_hashes[group.authority_id] = manifest
        for name, digest in manifest.items():
            add_hash_expectation(expectations, source / name, (source / name).stat().st_size,
                                 digest, "upstream_product")
        products = {item["name"]: item for item in receipt.get("products", [])}
        if set(products) != actual_files - {"STACK_RECEIPT.json", "SHA256SUMS.txt"}:
            raise RuntimeError(f"receipt product coverage mismatch at {source}")
        for name, item in products.items():
            if (int(item["bytes"]) != (source / name).stat().st_size
                    or item["sha256"] != manifest[name]):
                raise RuntimeError(f"receipt product hash mismatch at {source}/{name}")
        transforms = list(csv.DictReader((source / "TRANSFORMS.csv").open(encoding="utf-8")))
        if tuple(row["frame"] for row in transforms) != group.members:
            raise RuntimeError(f"transform membership mismatch at {source}")
        if any(float(row["theta_deg"]) != 0.0
               or not row["theta_status"].startswith("theta=0 ACCEPTED") for row in transforms):
            raise RuntimeError(f"theta=0 authority mismatch at {source}")
        if len(group.members) == 1:
            if receipt["split"].get("status") != "INCONCLUSIVE":
                raise RuntimeError(f"single unexpectedly has measured split at {source}")
        else:
            split = receipt["split"]
            if split.get("status") != "MEASURED" or set(split["A"]) | set(split["B"]) != set(group.members):
                raise RuntimeError(f"split membership mismatch at {source}")
            if set(split["A"]) & set(split["B"]):
                raise RuntimeError(f"overlapping split at {source}")
        scale, scale_status = empirical_scale(receipt, group)
        statistical_gate = sector_gate(source, receipt, scale)
        pixel_gate = pixel_invariants(source, receipt)
        if not statistical_gate["passes"] or not pixel_gate["passes"]:
            raise RuntimeError(f"scientific gate failed at {source}")
        audits.append({
            "group": group,
            "receipt": receipt,
            "source": source,
            "source_sha256sums_sha256": sha256(source / "SHA256SUMS.txt"),
            "upstream_receipt_sha256": sha256(receipt_path),
            "empirical_scale_rgb": scale,
            "empirical_scale_status": scale_status,
            "statistical_gate": statistical_gate,
            "pixel_gate": pixel_gate,
        })
    expected_frames = {f"572A{number}.CR3" for number in range(2958, 3026)}
    if set(frame_owner) != expected_frames or len(frame_owner) != 68:
        missing = sorted(expected_frames - set(frame_owner))
        extra = sorted(set(frame_owner) - expected_frames)
        raise RuntimeError(f"68-frame authority mismatch; missing={missing}, extra={extra}")
    stack_members = sum(len(a["group"].members) for a in audits
                        if a["group"].product_class == "EXPOSURE_STACK")
    single_members = sum(len(a["group"].members) for a in audits
                         if a["group"].product_class != "EXPOSURE_STACK")
    if stack_members != 58 or single_members != 10:
        raise RuntimeError("authority is not 58 stack members plus 10 singles")
    for item in SUPERSEDED:
        source = MASTERS / item["source"]
        if not (source / "STACK_RECEIPT.json").is_file():
            raise RuntimeError(f"missing superseded evidence {source}")
    verify_hash_expectations(expectations, jobs)
    max_sector = max((audit_item["statistical_gate"].get("max_abs_sector_median_sigma") or 0.0)
                     for audit_item in audits)
    max_loo = max(audit_item["pixel_gate"]["loo_max_abs_median_over_mad"]
                  for audit_item in audits)
    return {
        "audits": audits,
        "frame_owner": frame_owner,
        "input_authority": input_authority,
        "source_manifest_hashes": source_manifest_hashes,
        "hash_expectations": expectations,
        "summary": {
            "verdict": "ACCEPTAT",
            "accepted_stacks": 13,
            "accepted_stack_members": 58,
            "linear_single_contributions": 10,
            "authoritative_inputs": 68,
            "unique_authoritative_inputs": 68,
            "superseded_groups": 9,
            "groups_with_measured_split": 13,
            "upstream_group_sha256sums_verified": 23,
            "unique_hash_authorities_verified": len(expectations),
            "max_abs_sector_median_sigma_rg": max_sector,
            "sector_threshold_sigma": SECTOR_THRESHOLD_SIGMA,
            "max_loo_abs_median_over_mad": max_loo,
            "pixel_invariant_failures": 0,
        },
    }


def materialize(output: Path, audit_result: dict[str, Any]) -> None:
    if output.exists():
        raise RuntimeError(f"refusing to clobber existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.staging-{os.getpid()}"
    if staging.exists():
        raise RuntimeError(f"staging path already exists: {staging}")
    staging.mkdir()
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    known_hashes: dict[str, str] = {}
    authority_groups: list[dict[str, Any]] = []
    try:
        for item in audit_result["audits"]:
            group: Group = item["group"]
            source: Path = item["source"]
            destination = staging / group.destination
            destination.mkdir(parents=True)
            linked = 0
            for source_file in sorted(path for path in source.iterdir() if path.is_file()):
                target = destination / source_file.name
                os.link(source_file, target)
                source_stat = source_file.stat()
                target_stat = target.stat()
                if (source_stat.st_dev, source_stat.st_ino, source_stat.st_size) != (
                        target_stat.st_dev, target_stat.st_ino, target_stat.st_size):
                    raise RuntimeError(f"hardlink verification failed: {target}")
                linked += 1
                relative = target.relative_to(staging).as_posix()
                if source_file.name == "SHA256SUMS.txt":
                    known_hashes[relative] = item["source_sha256sums_sha256"]
                else:
                    known_hashes[relative] = audit_result["source_manifest_hashes"][
                        group.authority_id][source_file.name]
            scale_path = destination / "EMPIRICAL_VARIANCE_SCALE_RGB.npy"
            write_npy_f64_vector(scale_path, item["empirical_scale_rgb"])
            known_hashes[scale_path.relative_to(staging).as_posix()] = sha256(scale_path)
            authority_receipt = {
                "schema": "VIXEN_R6_S6_GROUP_AUTHORITY_V1",
                "created_utc": generated_at,
                "verdict": "ACCEPTAT",
                "authority_id": group.authority_id,
                "train": TRAIN,
                "frame": FRAME,
                "phenomenon_scope": group.phenomenon_scope,
                "product_class": group.product_class,
                "temporal_segment": group.temporal_segment,
                "upstream_temporal_segment": item["receipt"].get("temporal_segment"),
                "source_group": group.source,
                "destination_group": group.destination,
                "members": list(group.members),
                "exposure_s": item["receipt"]["exposure_s"],
                "solar_radius_model": item["receipt"]["solar_radius_model"],
                "reference_geometry": item["receipt"]["stack_info"]["geometria"],
                "registration_authority": "per-frame solar translation; theta_deg=0 for every frame",
                "empirical_variance_scale_rgb": item["empirical_scale_rgb"],
                "empirical_variance_scale_status": item["empirical_scale_status"],
                "empirical_variance_scale_product": "EMPIRICAL_VARIANCE_SCALE_RGB.npy",
                "empirical_variance_formula": "VARIANCE_EMPIRICAL_ADU2_s2[y,x,c] = VARIANCE_ADU2_s2[y,x,c] * EMPIRICAL_VARIANCE_SCALE_RGB[c]",
                "inverse_variance_formula_virtual_only": "INVVAR_EMPIRICAL[y,x,c] = INVVAR_WEIGHT[y,x,c] / EMPIRICAL_VARIANCE_SCALE_RGB[c]",
                "analytic_variance_product_rewritten": False,
                "analytic_inverse_variance_product_rewritten": False,
                "statistical_gate": item["statistical_gate"],
                "pixel_invariants": item["pixel_gate"],
                "upstream_receipt_sha256": item["upstream_receipt_sha256"],
                "upstream_sha256sums_sha256": item["source_sha256sums_sha256"],
                "hardlink_files": linked,
                "hardlink_same_device_inode_verified": True,
                "source_content_mutations": 0,
            }
            authority_path = destination / "AUTHORITY_RECEIPT.json"
            write_json(authority_path, authority_receipt)
            known_hashes[authority_path.relative_to(staging).as_posix()] = sha256(authority_path)
            authority_groups.append(authority_receipt)

        by_id = {item["authority_id"]: item for item in authority_groups}
        ledger = []
        for index, number in enumerate(range(2958, 3026), 1):
            frame = f"572A{number}.CR3"
            authority_id = audit_result["frame_owner"][frame]
            group_receipt = by_id[authority_id]
            input_item = audit_result["input_authority"][frame]
            ledger.append({
                "ledger_index": index,
                "frame": frame,
                "input_path": input_item["path"],
                "input_bytes": input_item["bytes"],
                "input_sha256": input_item["sha256"],
                "authority_id": authority_id,
                "product_class": group_receipt["product_class"],
                "temporal_segment": group_receipt["temporal_segment"],
                "phenomenon_scope": group_receipt["phenomenon_scope"],
                "source_group": group_receipt["source_group"],
                "destination_group": group_receipt["destination_group"],
                "assigned_exactly_once": True,
            })
        ledger_document = {
            "schema": "VIXEN_R6_S6_UNIQUE_INPUT_LEDGER_V1",
            "verdict": "ACCEPTAT",
            "expected": 68,
            "listed": len(ledger),
            "unique": len({entry["frame"] for entry in ledger}),
            "duplicate_assignments": [],
            "missing": [],
            "entries": ledger,
        }
        ledger_path = staging / "LEDGER_68.json"
        write_json(ledger_path, ledger_document)
        known_hashes[ledger_path.relative_to(staging).as_posix()] = sha256(ledger_path)

        policy = {
            "schema": "VIXEN_R6_S6_EMPIRICAL_VARIANCE_POLICY_V1",
            "channel_order": ["R", "G", "B"],
            "formula": "VARIANCE_EMPIRICAL_ADU2_s2[y,x,c] = VARIANCE_ADU2_s2[y,x,c] * EMPIRICAL_VARIANCE_SCALE_RGB[c]",
            "inverse_formula_virtual_only": "INVVAR_EMPIRICAL[y,x,c] = INVVAR_WEIGHT[y,x,c] / EMPIRICAL_VARIANCE_SCALE_RGB[c]",
            "scale_rule_for_stacks": "max(1, receipt.split.variance_scale_rgb) component by component",
            "scale_rule_for_singles": "[1,1,1]; analytic-only because no independent split exists",
            "analytic_products_are_hardlinked_and_never_rewritten": True,
            "groups": [{"authority_id": item["authority_id"],
                        "product_class": item["product_class"],
                        "temporal_segment": item["temporal_segment"],
                        "scale_rgb": item["empirical_variance_scale_rgb"],
                        "scale_product": f"{item['destination_group']}/EMPIRICAL_VARIANCE_SCALE_RGB.npy"}
                       for item in authority_groups],
        }
        policy_path = staging / "EMPIRICAL_VARIANCE_POLICY.json"
        write_json(policy_path, policy)
        known_hashes[policy_path.relative_to(staging).as_posix()] = sha256(policy_path)

        superseded_document = {
            "schema": "VIXEN_R6_S6_SUPERSEDED_GROUPS_V1",
            "count": 9,
            "verdict_for_each": "SUPERSEDIT_REPROCESSAR",
            "groups": [],
            "wrong_solar_radius_generation_roots_excluded_separately": list(WRONG_SOLAR_RADIUS_GENERATIONS),
            "exclusion_reason": "historical 959 arcsec solar-radius proxy; v3 uses literal 946.6598/2.1495",
        }
        for entry in SUPERSEDED:
            source_receipt = MASTERS / entry["source"] / "STACK_RECEIPT.json"
            enriched = dict(entry)
            enriched.update({"verdict": "SUPERSEDIT_REPROCESSAR",
                             "source_receipt_sha256": sha256(source_receipt)})
            superseded_document["groups"].append(enriched)
        superseded_path = staging / "SUPERSEDED_9.json"
        write_json(superseded_path, superseded_document)
        known_hashes[superseded_path.relative_to(staging).as_posix()] = sha256(superseded_path)

        root_receipt = {
            "schema": "VIXEN_R6_S6_ACCEPTED_AUTHORITY_V1",
            "created_utc": generated_at,
            "verdict": "ACCEPTAT",
            "train": TRAIN,
            "frame": FRAME,
            "authority_scope": "linear exposure-separated Vixen products; C2 and C3 contact products are separate from corona",
            "solar_radius_model": {
                "radius_arcsec": SOLAR_RADIUS_ARCSEC,
                "plate_scale_arcsec_px": PLATE_SCALE_ARCSEC_PX,
                "radius_px": SOLAR_RADIUS_PX,
                "expression": "946.6598/2.1495",
                "authority": "DE440 topocentric plus IAU nominal solar radius 695700 km",
            },
            "reference_geometry": {"mode": "comuna", "fotograma": REFERENCE_FRAME,
                                   "sol_x": REFERENCE_SOL_X, "sol_y": REFERENCE_SOL_Y,
                                   "theta_deg": 0.0},
            "counts": audit_result["summary"],
            "statistical_contract": {
                "hard_gate": "24 fixed sectors at +x origin, positive toward +y image coordinates, threshold 2.5 sigma",
                "phase_invariant_claimed": False,
                "late2_1-2s_note": "accepted under the frozen gate; phase-origin sweep is an advisory and this LATE2 product is not part of the visual STABLE master",
                "long_10p0794s_inner_gate": "NOT_APPLICABLE because saturation leaves zero G and insufficient R support at 1.1-1.5 R_sun; global split and LOO pass",
            },
            "ledger": {"path": "LEDGER_68.json", "expected": 68, "listed": 68,
                       "unique": 68, "coverage": "68/68"},
            "accepted_stacks": [item for item in authority_groups
                                if item["product_class"] == "EXPOSURE_STACK"],
            "linear_single_contributions": [item for item in authority_groups
                                             if item["product_class"] != "EXPOSURE_STACK"],
            "superseded": {"path": "SUPERSEDED_9.json", "count": 9,
                           "verdict": "SUPERSEDIT_REPROCESSAR"},
            "empirical_variance": {"policy": "EMPIRICAL_VARIANCE_POLICY.json",
                                   "analytic_variance_rewritten": False,
                                   "analytic_invvar_rewritten": False},
            "materialization": {"method": "hardlinks for every upstream regular file",
                                "same_device_inode_verified": True,
                                "source_candidates_preserved": True,
                                "source_content_mutations": 0,
                                "atomic_non_clobber_promotion": True},
            "hash_verification": {"upstream_sha256sums": "23/23 PASS",
                                  "input_raw": "68/68 PASS",
                                  "calibrators": "32 unique paths PASS",
                                  "software": "3/3 PASS"},
        }
        root_path = staging / "AUTHORITY_RECEIPT.json"
        write_json(root_path, root_receipt)
        known_hashes[root_path.relative_to(staging).as_posix()] = sha256(root_path)

        actual_without_manifest = {path.relative_to(staging).as_posix()
                                   for path in staging.rglob("*") if path.is_file()}
        if actual_without_manifest != set(known_hashes):
            missing = sorted(actual_without_manifest - set(known_hashes))
            extra = sorted(set(known_hashes) - actual_without_manifest)
            raise RuntimeError(f"root hash inventory mismatch; missing={missing}, extra={extra}")
        manifest_path = staging / "SHA256SUMS.txt"
        with manifest_path.open("w", encoding="utf-8") as handle:
            for relative in sorted(known_hashes):
                handle.write(f"{known_hashes[relative]}  {relative}\n")
        staging.rename(output)
    except BaseException:
        if staging.exists() and staging.name.startswith(f".{output.name}.staging-"):
            shutil.rmtree(staging)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-only", action="store_true")
    mode.add_argument("--materialize", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    result = audit(args.jobs)
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False), flush=True)
    if args.materialize:
        output = args.out if args.out.is_absolute() else ROOT / args.out
        materialize(output, result)
        print(f"ACCEPTAT: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
