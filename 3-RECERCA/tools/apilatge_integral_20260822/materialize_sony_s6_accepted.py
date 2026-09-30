#!/usr/bin/env python3
"""Materialise the audited Sony S6 delivery without combining mount segments.

The destination is a catalogue, not a claim that every enclosed contribution
is accepted.  Only repeated segment-C stacks which pass the run-specific
CFA4 split/null gates receive the literal verdict ``ACCEPTAT``.  Segment-A
and other single-frame products remain independent ``QUARANTENA``
contributions.  Eight-second products keep variance factor 1.0 and the
literal reason ``QUARANTENA_COVARIANCIA_PENDENT``.

All upstream products are validated against their own manifests and linked
with hard links.  RAWs are never linked or modified: their current canonical
bytes, metadata and SHA-256 are recorded in an 18-frame ledger.  The build is
fail-closed and published by one atomic directory rename.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


PROJECT = Path(__file__).resolve().parents[3]
DEFAULT_TARGET = (
    PROJECT / "output/postprocessat_final_20260822/masters/sony_s6_ACCEPTED"
)
DEFAULT_RAW_ROOT = Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA")
DEFAULT_ROOTS = {
    ("A", "RGB_DERIVATIVE"): PROJECT / (
        "output/postprocessat_final_20260822/masters/"
        "sony_segment_A_rgb_s6_v2_candidates"
    ),
    ("C", "RGB_DERIVATIVE"): PROJECT / (
        "output/postprocessat_final_20260822/masters/"
        "sony_segment_C_rgb_s6_v2_candidates"
    ),
    ("A", "CFA4_PRIMARY"): PROJECT / (
        "output/postprocessat_final_20260822/masters/"
        "sony_segment_A_cfa4_s6_v2_candidates"
    ),
    ("C", "CFA4_PRIMARY"): PROJECT / (
        "output/postprocessat_final_20260822/masters/"
        "sony_segment_C_cfa4_s6_v2_candidates"
    ),
}

EXPECTED_RUN_HASHES = {
    ("A", "RGB_DERIVATIVE"):
        "b9aafc848e522fee1a19945bae63a823a49290470323798bed19a83ab33b28d5",
    ("C", "RGB_DERIVATIVE"):
        "6be9ae669f9d73874656c261cc8ed9ea535e3367ee9ced27ca09278d2e28fcae",
    ("A", "CFA4_PRIMARY"):
        "3202d5dd6339b69f2f58cf58ed1eb2e0066859364c20b2c89b30ad5a04dc4e30",
    ("C", "CFA4_PRIMARY"):
        "d3663231137037df90d011372330ea29767bcab8f9d1c7631d4449dbaa89c162",
}
EXPECTED_RGB_SCRIPT_SHA256 = (
    "7afccbcd93822ecaf77f3f51c2c244a7f28410367eda552f0fae1d64da795505"
)
EXPECTED_CFA4_SCRIPT_SHA256 = (
    "b581ae0c24b4fc8a9c02cd9a3c668114be4b2ebbe5d1f942402f9d467c7ee818"
)
RGB_SCRIPT = Path(__file__).with_name("stack_sony_s6.py")
CFA4_SCRIPT = Path(__file__).with_name("stack_sony_cfa4_s6.py")
SKILL_PATH = Path(
    "/Users/USUARI/.codex/skills/apilatge-imatges-eclipsi/SKILL.md"
)

SOLAR_CENTER_XY = (3894.0057024183907, 2768.6725752051257)
SOLAR_RADIUS_PX = 295.64720468902027
SOLAR_RADIUS_AUTHORITY = (
    "DE440 topocentric at 2026-08-12 totality, site 42.299407N "
    "5.02503W 798 m; IAU nominal solar radius 695700 km; "
    "946.6598 arcsec / 3.2019913768363018 arcsec px-1"
)
PLANE_ORDER = ("R", "G1", "B", "G2")
PLANE_OFFSETS_YX = ((0, 0), (0, 1), (1, 1), (1, 0))
EIGHT_SECOND_REASON = "QUARANTENA_COVARIANCIA_PENDENT"

ANNULAR_GATE = {
    "minimum_samples_each_plane": 1000,
    "maximum_abs_median_z": 0.20,
    "maximum_robust_sigma_z": 1.30,
    "maximum_sector_rms_z": 0.60,
    "maximum_abs_sector_median_z": 1.25,
    "maximum_abs_acf_32_64_full_px": 0.12,
    "sector_count": 24,
}


class ContractError(RuntimeError):
    """An input or requested operation violates the delivery contract."""


@dataclass(frozen=True)
class ProductSpec:
    segment: str
    tag: str
    exposure_s: float
    members: tuple[str, ...]
    product_class: str
    verdict: str
    reason_codes: tuple[str, ...]
    accepted_min_rsun: float | None = None
    acf_annulus_rsun: tuple[float, float] | None = None
    inner_quarantine_annulus_rsun: tuple[float, float] | None = None
    provisional_visual_min_rsun: float | None = None

    @property
    def product_id(self) -> str:
        return f"segment_{self.segment}_{self.tag}"


PRODUCTS = (
    ProductSpec("A", "1-30s", 1 / 30, ("DSC06983",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C")),
    ProductSpec("A", "1-8s", 1 / 8, ("DSC06986",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C")),
    ProductSpec("A", "1-4s", 1 / 4, ("DSC06982",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C")),
    ProductSpec("A", "1s", 1.0, ("DSC06985",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C")),
    ProductSpec("A", "2s", 2.0, ("DSC06984",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C")),
    ProductSpec("A", "8s", 8.0, ("DSC06987",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", "SEGMENT_A_NO_COMBINAT_AMB_C",
                 EIGHT_SECOND_REASON, "A8_CROSS_EXPOSURE_NULL_FAIL")),
    ProductSpec("C", "1-30s", 1 / 30, ("DSC06995", "DSC06998"),
                "STACK_SEGMENT_C_REPETIT", "ACCEPTAT",
                ("CFA4_SPLIT_ANNULAR_SECTOR_ACF_PASS",
                 "CORONA_ONLY_MODELLED_REGISTRATION_SCOPE"),
                accepted_min_rsun=1.2, acf_annulus_rsun=(1.5, 2.0)),
    ProductSpec("C", "1-8s", 1 / 8, ("DSC06992",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN",)),
    ProductSpec("C", "1-4s", 1 / 4, ("DSC06994", "DSC06997"),
                "STACK_SEGMENT_C_REPETIT", "ACCEPTAT",
                ("CFA4_SPLIT_ANNULAR_SECTOR_ACF_PASS",),
                accepted_min_rsun=1.5, acf_annulus_rsun=(2.0, 3.0),
                inner_quarantine_annulus_rsun=(1.2, 1.5)),
    ProductSpec("C", "2s", 2.0, ("DSC06996", "DSC06999"),
                "STACK_SEGMENT_C_REPETIT", "ACCEPTAT",
                ("CFA4_SPLIT_ANNULAR_SECTOR_ACF_PASS",),
                accepted_min_rsun=2.0, acf_annulus_rsun=(2.0, 3.0),
                inner_quarantine_annulus_rsun=(1.5, 2.0)),
    ProductSpec("C", "8s", 8.0, ("DSC06993",),
                "CONTRIBUCIO_INDEPENDENT_SINGLE", "QUARANTENA",
                ("SINGLE_FRAME_NO_REPEAT_GAIN", EIGHT_SECOND_REASON),
                provisional_visual_min_rsun=3.0),
)

CAPTURE_DECISIONS = {
    "DSC06988": {
        "pipeline_disposition": "REBUTJAT",
        "exposure_s": 1.0,
        "reason_codes": ["TRAIL_ESTELLAR_APROX_25PX_DURANT_SALT_MUNTURA"],
    },
    "DSC06989": {
        "pipeline_disposition": "QUARANTENA",
        "exposure_s": 1 / 8,
        "reason_codes": ["LIMB_RMS_4_30PX_ENTRE_SALTS_MUNTURA"],
    },
    "DSC06990": {
        "pipeline_disposition": "REBUTJAT",
        "exposure_s": 8.0,
        "reason_codes": ["MOVIMENT_DURANT_EXPOSICIO_8S"],
    },
    "DSC06991": {
        "pipeline_disposition": "QUARANTENA",
        "exposure_s": 1.0,
        "reason_codes": ["TRACA_ESTELLAR_APROX_11PX"],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=True)


def json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sha256(path)


def safe_manifest_rel(text: str) -> Path:
    rel = Path(text)
    if rel.is_absolute() or not rel.parts or any(part in ("", ".", "..")
                                                  for part in rel.parts):
        raise ContractError(f"unsafe manifest path: {text!r}")
    return rel


def parse_sha_manifest(path: Path) -> dict[Path, str]:
    entries: dict[Path, str] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            digest, name = raw_line.split("  ", 1)
        except ValueError as exc:
            raise ContractError(f"malformed manifest line {path}:{number}") from exc
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ContractError(f"invalid SHA-256 at {path}:{number}")
        rel = safe_manifest_rel(name)
        if rel in entries:
            raise ContractError(f"duplicate manifest path {rel} in {path}")
        entries[rel] = digest
    if not entries:
        raise ContractError(f"empty manifest: {path}")
    return entries


def direct_validate_manifest(
    manifest: Path, base: Path, *, exact_flat_directory: bool
) -> list[dict[str, Any]]:
    entries = parse_sha_manifest(manifest)
    records: list[dict[str, Any]] = []
    for rel, expected in sorted(entries.items(), key=lambda row: str(row[0])):
        source = canonical(base / rel)
        if not source.is_file():
            raise ContractError(f"manifest member is not a file: {source}")
        actual = sha256(source)
        if actual != expected:
            raise ContractError(
                f"manifest hash mismatch {source}: {actual} != {expected}"
            )
        records.append({
            "source": source,
            "source_rel": str(rel),
            "bytes": source.stat().st_size,
            "sha256": actual,
        })
    manifest_resolved = canonical(manifest)
    records.append({
        "source": manifest_resolved,
        "source_rel": manifest.name,
        "bytes": manifest_resolved.stat().st_size,
        "sha256": sha256(manifest_resolved),
    })
    if exact_flat_directory:
        if any(len(rel.parts) != 1 for rel in entries):
            raise ContractError(f"group manifest must be flat: {manifest}")
        actual_names = {path.name for path in base.iterdir() if path.is_file()}
        expected_names = {str(rel) for rel in entries} | {manifest.name}
        if actual_names != expected_names:
            raise ContractError(
                f"unexpected/missing files in {base}: "
                f"extra={sorted(actual_names - expected_names)}, "
                f"missing={sorted(expected_names - actual_names)}"
            )
    return records


def assert_close(actual: float, expected: float, label: str,
                 tolerance: float = 1e-9) -> None:
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        raise ContractError(f"{label}: {actual} != {expected}")


def static_contract() -> None:
    if len(PRODUCTS) != 11:
        raise ContractError("expected exactly 11 materialised products")
    product_ids = [spec.product_id for spec in PRODUCTS]
    if len(product_ids) != len(set(product_ids)):
        raise ContractError("duplicate product id")
    processed = [frame for spec in PRODUCTS for frame in spec.members]
    if len(processed) != 14 or len(set(processed)) != 14:
        raise ContractError("processed product membership must be 14 unique frames")
    capture = processed + list(CAPTURE_DECISIONS)
    expected = [f"DSC{number:05d}" for number in range(6982, 7000)]
    if sorted(capture) != expected:
        raise ContractError(f"candidate ledger is not exact DSC06982--DSC06999: {capture}")
    counts = {
        status: sum(1 for value in CAPTURE_DECISIONS.values()
                    if value["pipeline_disposition"] == status)
        for status in ("REBUTJAT", "QUARANTENA")
    }
    if counts != {"REBUTJAT": 2, "QUARANTENA": 2}:
        raise ContractError(f"capture decision counts changed: {counts}")
    accepted = [spec for spec in PRODUCTS if spec.verdict == "ACCEPTAT"]
    if len(accepted) != 3:
        raise ContractError("exactly three products must be ACCEPTAT")
    for spec in accepted:
        if spec.segment != "C" or len(spec.members) < 2 or spec.accepted_min_rsun is None:
            raise ContractError(f"illegal accepted product: {spec}")
    for spec in PRODUCTS:
        if spec.exposure_s == 8.0 and (
            spec.verdict != "QUARANTENA" or EIGHT_SECOND_REASON not in spec.reason_codes
        ):
            raise ContractError(f"8 s product lacks covariance quarantine: {spec}")


def roots_from_args(args: argparse.Namespace) -> dict[tuple[str, str], Path]:
    roots = {
        ("A", "RGB_DERIVATIVE"): args.a_rgb_root,
        ("C", "RGB_DERIVATIVE"): args.c_rgb_root,
        ("A", "CFA4_PRIMARY"): args.a_cfa4_root,
        ("C", "CFA4_PRIMARY"): args.c_cfa4_root,
    }
    return {key: canonical(value) for key, value in roots.items()}


def validate_runs(
    roots: dict[tuple[str, str], Path]
) -> tuple[dict[tuple[str, str], dict[str, Any]],
           dict[tuple[str, str], list[dict[str, Any]]]]:
    current_rgb_script = sha256(canonical(RGB_SCRIPT))
    current_cfa4_script = sha256(canonical(CFA4_SCRIPT))
    if current_rgb_script != EXPECTED_RGB_SCRIPT_SHA256:
        raise ContractError(
            f"current stack_sony_s6.py drifted: {current_rgb_script}"
        )
    if current_cfa4_script != EXPECTED_CFA4_SCRIPT_SHA256:
        raise ContractError(
            f"current stack_sony_cfa4_s6.py drifted: {current_cfa4_script}"
        )
    run_objects: dict[tuple[str, str], dict[str, Any]] = {}
    run_records: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for key, root in roots.items():
        segment, authority = key
        run_name = "RUN_RECEIPT.json" if authority == "RGB_DERIVATIVE" \
            else "RUN_CFA4_RECEIPT.json"
        run_path = canonical(root / run_name)
        actual = sha256(run_path)
        expected = EXPECTED_RUN_HASHES[key]
        if actual != expected:
            raise ContractError(f"upstream run receipt drifted {run_path}: {actual}")
        receipt = json_object(run_path)
        if receipt.get("mount_segment") != segment:
            raise ContractError(f"run segment mismatch: {run_path}")
        expected_script = (EXPECTED_RGB_SCRIPT_SHA256
                           if authority == "RGB_DERIVATIVE"
                           else EXPECTED_CFA4_SCRIPT_SHA256)
        if receipt.get("script_sha256") != expected_script:
            raise ContractError(f"run software hash mismatch: {run_path}")
        records = [{
            "source": run_path,
            "source_rel": run_name,
            "bytes": run_path.stat().st_size,
            "sha256": actual,
        }]
        if authority == "RGB_DERIVATIVE":
            manifest = canonical(root / "RUN_SHA256SUMS.txt")
            checked = direct_validate_manifest(
                manifest, root, exact_flat_directory=False
            )
            manifest_run = next(
                row for row in checked if row["source_rel"] == run_name
            )
            if manifest_run["sha256"] != actual:
                raise ContractError(f"RGB run manifest disagrees: {manifest}")
            records.append(next(row for row in checked
                                if row["source_rel"] == manifest.name))
        run_objects[key] = receipt
        run_records[key] = records
        print(f"validated run {segment} {authority}: {actual}", flush=True)
    return run_objects, run_records


def run_group_record(run: dict[str, Any], tag: str) -> dict[str, Any]:
    rows = [row for row in run.get("groups", []) if row.get("path") == tag]
    if len(rows) != 1:
        raise ContractError(f"run receipt has {len(rows)} entries for {tag}")
    return rows[0]


def validate_product_sources(
    spec: ProductSpec,
    roots: dict[tuple[str, str], Path],
    runs: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    all_records: dict[str, list[dict[str, Any]]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    for authority, receipt_name in (
        ("CFA4_PRIMARY", "STACK_CFA4_RECEIPT.json"),
        ("RGB_DERIVATIVE", "STACK_RECEIPT.json"),
    ):
        root = roots[(spec.segment, authority)]
        group = canonical(root / spec.tag)
        manifest = canonical(group / "SHA256SUMS.txt")
        records = direct_validate_manifest(
            manifest, group, exact_flat_directory=True
        )
        receipt_path = canonical(group / receipt_name)
        receipt_digest = next(
            row["sha256"] for row in records if row["source"] == receipt_path
        )
        run_row = run_group_record(runs[(spec.segment, authority)], spec.tag)
        if run_row.get("receipt_sha256") != receipt_digest:
            raise ContractError(
                f"run/group receipt mismatch {spec.product_id} {authority}"
            )
        receipt = json_object(receipt_path)
        if tuple(receipt.get("members", [])) != spec.members:
            raise ContractError(
                f"member mismatch {spec.product_id} {authority}: "
                f"{receipt.get('members')} != {spec.members}"
            )
        assert_close(float(receipt.get("exposure_s")), spec.exposure_s,
                     f"{spec.product_id} {authority} exposure")
        radius = receipt.get("solar_radius_model", {}).get("radius_px")
        assert_close(float(radius), SOLAR_RADIUS_PX,
                     f"{spec.product_id} {authority} solar radius", 1e-6)
        if authority == "RGB_DERIVATIVE":
            if receipt.get("mount_segment") != spec.segment:
                raise ContractError(
                    f"RGB segment mismatch: {spec.product_id}"
                )
        else:
            if receipt.get("plane_order") != list(PLANE_ORDER):
                raise ContractError(f"CFA4 plane order mismatch: {spec.product_id}")
            if receipt.get("plane_offsets_yx") != [list(row) for row in PLANE_OFFSETS_YX]:
                raise ContractError(f"CFA4 plane offsets mismatch: {spec.product_id}")
            if receipt.get("authority") != "PRIMARY_LINEAR_CFA4; RGB products are derivatives":
                raise ContractError(f"CFA4 authority mismatch: {spec.product_id}")
            if spec.exposure_s == 8.0 and "scalar 8 s inflation withdrawn" not in \
                    receipt.get("spatial_covariance", ""):
                raise ContractError(f"8 s covariance correction absent: {spec.product_id}")
        all_records[authority] = records
        receipts[authority] = receipt
        apparent = sum(row["bytes"] for row in records)
        print(
            f"validated {spec.product_id} {authority}: "
            f"{len(records)} files, {apparent / (1 << 30):.2f} GiB",
            flush=True,
        )
    return all_records, receipts


def annulus_geometry(shape: tuple[int, int], plane: int) -> tuple[np.ndarray, np.ndarray]:
    height, width = shape
    oy, ox = PLANE_OFFSETS_YX[plane]
    yy = np.arange(height, dtype=np.float64)[:, None] * 8.0 + oy
    xx = np.arange(width, dtype=np.float64)[None, :] * 8.0 + ox
    dx = xx - SOLAR_CENTER_XY[0]
    dy = yy - SOLAR_CENTER_XY[1]
    rho = np.hypot(dx, dy) / SOLAR_RADIUS_PX
    angle = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0
    return rho, angle


def annular_stats(z: np.ndarray, bounds: tuple[float, float]) -> dict[str, Any]:
    lower, upper = bounds
    result: dict[str, Any] = {
        "annulus_rsun": [lower, upper],
        "planes": {},
    }
    for plane, label in enumerate(PLANE_ORDER):
        rho, angle = annulus_geometry(z.shape[:2], plane)
        selected = ((rho >= lower) & (rho < upper)
                    & np.isfinite(z[..., plane]))
        values = z[..., plane][selected].astype(np.float64)
        if not len(values):
            raise ContractError(f"empty annulus {bounds} plane {label}")
        median = float(np.median(values))
        sigma = float(1.4826 * np.median(np.abs(values - median)))
        sector_medians: list[float] = []
        sector_width = 360.0 / ANNULAR_GATE["sector_count"]
        for sector in range(ANNULAR_GATE["sector_count"]):
            sector_selected = (
                selected
                & (angle >= sector * sector_width)
                & (angle < (sector + 1) * sector_width)
            )
            sector_values = z[..., plane][sector_selected]
            if len(sector_values) >= 50:
                sector_medians.append(float(np.median(sector_values)))
        if len(sector_medians) < 12:
            raise ContractError(
                f"insufficient sectors {bounds} plane {label}: {len(sector_medians)}"
            )
        result["planes"][label] = {
            "samples": int(len(values)),
            "median_z": median,
            "robust_sigma_z": sigma,
            "sector_medians_z": sector_medians,
            "sector_rms_z": float(np.sqrt(np.mean(np.square(sector_medians)))),
            "maximum_abs_sector_median_z": float(max(map(abs, sector_medians))),
        }
    return result


def acf_stats(z: np.ndarray, bounds: tuple[float, float]) -> dict[str, Any]:
    lower, upper = bounds
    output: dict[str, Any] = {
        "annulus_rsun": [lower, upper],
        "full_pixel_lags": [32, 64],
        "z_array_lags": [4, 8],
        "planes": {},
    }
    for plane, label in enumerate(PLANE_ORDER):
        rho, _ = annulus_geometry(z.shape[:2], plane)
        selected = ((rho >= lower) & (rho < upper)
                    & np.isfinite(z[..., plane]))
        values = z[..., plane].astype(np.float64)
        values -= np.median(values[selected])
        correlations: dict[str, float] = {}
        for lag in (4, 8):
            for axis, (dy, dx) in {
                "x": (0, lag), "y": (lag, 0)
            }.items():
                first_mask = selected[: selected.shape[0] - dy or None,
                                      : selected.shape[1] - dx or None]
                second_mask = selected[dy:, dx:]
                common = first_mask & second_mask
                first = values[: values.shape[0] - dy or None,
                               : values.shape[1] - dx or None][common]
                second = values[dy:, dx:][common]
                if len(first) < 100:
                    raise ContractError(
                        f"insufficient ACF pairs {bounds} {label} {axis}{lag}"
                    )
                correlation = float(np.corrcoef(first, second)[0, 1])
                if not math.isfinite(correlation):
                    raise ContractError(
                        f"non-finite ACF {bounds} {label} {axis}{lag}"
                    )
                correlations[f"{axis}_{lag * 8}_full_px"] = correlation
        output["planes"][label] = {
            "correlations": correlations,
            "maximum_abs_correlation": float(max(map(abs, correlations.values()))),
        }
    return output


def gate_annulus(first: dict[str, Any], acf: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for label, stats in first["planes"].items():
        if stats["samples"] < ANNULAR_GATE["minimum_samples_each_plane"]:
            failures.append(f"{label}:samples")
        if abs(stats["median_z"]) > ANNULAR_GATE["maximum_abs_median_z"]:
            failures.append(f"{label}:median")
        if stats["robust_sigma_z"] > ANNULAR_GATE["maximum_robust_sigma_z"]:
            failures.append(f"{label}:sigma")
        if stats["sector_rms_z"] > ANNULAR_GATE["maximum_sector_rms_z"]:
            failures.append(f"{label}:sector_rms")
        if stats["maximum_abs_sector_median_z"] > \
                ANNULAR_GATE["maximum_abs_sector_median_z"]:
            failures.append(f"{label}:sector_max")
    for label, stats in acf["planes"].items():
        if stats["maximum_abs_correlation"] > \
                ANNULAR_GATE["maximum_abs_acf_32_64_full_px"]:
            failures.append(f"{label}:acf")
    return not failures, failures


def build_qa_evidence(
    roots: dict[tuple[str, str], Path],
    receipts: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    accepted: dict[str, Any] = {}
    for spec in PRODUCTS:
        if spec.verdict != "ACCEPTAT":
            continue
        z_path = canonical(
            roots[(spec.segment, "CFA4_PRIMARY")]
            / spec.tag / "SPLIT_z_CFA4_ds4.npz"
        )
        with np.load(z_path) as payload:
            if payload.files != ["z"]:
                raise ContractError(f"unexpected split z payload: {z_path}")
            z = np.asarray(payload["z"], dtype=np.float32)
        first_upper = {
            1.2: 1.5,
            1.5: 2.0,
            2.0: 3.0,
        }[float(spec.accepted_min_rsun)]
        first = annular_stats(z, (float(spec.accepted_min_rsun), first_upper))
        acf = acf_stats(z, spec.acf_annulus_rsun)
        passed, failures = gate_annulus(first, acf)
        if not passed:
            raise ContractError(
                f"declared acceptance domain failed {spec.product_id}: {failures}"
            )
        inner = None
        if spec.inner_quarantine_annulus_rsun:
            inner_stats = annular_stats(z, spec.inner_quarantine_annulus_rsun)
            inner_acf = acf_stats(z, spec.inner_quarantine_annulus_rsun)
            inner_pass, inner_failures = gate_annulus(inner_stats, inner_acf)
            if inner_pass:
                raise ContractError(
                    f"declared inner quarantine unexpectedly passed: {spec.product_id}"
                )
            inner = {
                "status": "QUARANTENA",
                "statistics": inner_stats,
                "acf": inner_acf,
                "failed_gates": inner_failures,
            }
        cfa_receipt_path = canonical(
            roots[(spec.segment, "CFA4_PRIMARY")]
            / spec.tag / "STACK_CFA4_RECEIPT.json"
        )
        accepted[spec.product_id] = {
            "verdict": "ACCEPTAT",
            "scope": (
                f"corona with physical radius rho >= {spec.accepted_min_rsun:.1f} "
                "Rsun and per-pixel support in the hashed validity mask"
            ),
            "astrometry_scope": (
                "not promoted; acceptance validates the registered coronal stack "
                "only and cannot be transferred to stellar astrometry"
            ),
            "source_split_z": {
                "path": str(z_path),
                "sha256": sha256(z_path),
            },
            "source_cfa4_receipt": {
                "path": str(cfa_receipt_path),
                "sha256": sha256(cfa_receipt_path),
            },
            "first_accepted_annulus": first,
            "acf_structure_check": acf,
            "gate_failures": failures,
            "inner_domain": inner,
        }
    eight_second = {
        "verdict": "QUARANTENA",
        "reason_code": EIGHT_SECOND_REASON,
        "diagonal_variance_factor": 1.0,
        "covariance_product_status": "PENDENT",
        "skill_override": {
            "scope": "this immutable run only; global skill file was not edited",
            "withdrawn_claim": (
                "the previous +0.42 lag-1 / factor 1.408 estimate was derived "
                "from an unregistered A-C scene difference"
            ),
            "correction": (
                "retain diagonal variance factor 1.0; spatial covariance remains "
                "unmodelled and therefore both 8 s contributions stay quarantined"
            ),
            "dark_pair_lag1_observation": "approximately 0.07--0.11, like the 2 s darks",
        },
        "registered_tests": {
            "A8_DSC06987_vs_C8_DSC06993_no_gain": {
                "common_support_starts_rsun": 2.0606,
                "annuli": {
                    "2.0_2.2": {
                        "median_z_rgb": [1.825, 2.489, 1.853],
                        "robust_sigma_z_rgb": [1.511, 1.833, 1.442],
                        "maximum_abs_sector_median_z_rgb": [3.368, 4.869, 3.480],
                    },
                    "2.2_2.5": {
                        "median_z_rgb": [1.298, 1.650, 1.394],
                        "robust_sigma_z_rgb": [1.577, 1.927, 1.532],
                    },
                    "2.5_3.0": {
                        "robust_sigma_z_rgb": [2.070, 2.650, 1.926],
                        "maximum_abs_sector_median_z_rgb": [4.796, 6.600, 4.587],
                    },
                    "3.0_4.2": {"robust_sigma_z_rgb": [1.392, 1.861, 1.564]},
                    "4.2_6.0": {"robust_sigma_z_rgb": [1.153, 1.445, 1.320]},
                    "6.0_10.0": {"robust_sigma_z_rgb": [1.094, 1.270, 1.238]},
                },
                "broad_acf_2.2_6_rsun_lags_4_32_full_px": "approximately 0.33--0.54",
                "photometric_gain_verdict": "UNSTABLE_BY_ANNULUS_DO_NOT_APPLY",
            },
            "A8_DSC06987_vs_A2_DSC06984": {
                "diagnostic_gain_rgb_not_applied": [1.006841, 1.010131, 1.015373],
                "gain_fit_annulus_rsun": [2.5, 4.2],
                "after_gain_robust_sigma_z_rgb": {
                    "3.0_4.2": [1.460, 1.457, 1.507],
                    "4.2_6.0": [1.415, 1.389, 1.459],
                    "beyond_6_range": [1.39, 1.46],
                },
                "result": "FAIL_NO_ACCEPTED_DOMAIN",
            },
            "C8_DSC06993_vs_C2_DSC06996_DSC06999": {
                "diagnostic_gain_rgb_not_applied": [1.011455, 1.013515, 1.012165],
                "gain_fit_annulus_rsun": [2.5, 4.2],
                "after_gain": {
                    "2.5_3.0": {
                        "green_robust_sigma_z": 1.372,
                        "maximum_abs_sector_median_z": 1.345,
                        "result": "FAIL",
                    },
                    "3.0_4.2": {
                        "median_z_rgb": [0.074, -0.084, -0.031],
                        "robust_sigma_z_rgb": [1.048, 1.195, 1.160],
                        "maximum_abs_sector_median_z_rgb": [0.673, 0.817, 0.508],
                    },
                    "4.2_6.0": {
                        "robust_sigma_z_rgb": [1.004, 1.108, 1.118],
                        "maximum_abs_sector_median_z_rgb": [0.297, 0.572, 0.344],
                    },
                },
                "provisional_visual_domain": (
                    "rho >= 3.0 Rsun only; diagnostic, not scientific acceptance"
                ),
                "result": EIGHT_SECOND_REASON,
            },
        },
        "stellar_residual_checks": {
            "DSC06987": {
                "common_stars": 8,
                "median_dx_dy_px": [1.179, -0.340],
                "mad_dx_dy_px": [1.950, 1.231],
                "result": "FAIL",
            },
            "DSC06993": {
                "common_stars": 8,
                "median_dx_dy_px": [0.035, -0.087],
                "mad_dx_dy_px": [0.057, 0.137],
                "result": "PASS_GEOMETRY_ONLY",
            },
        },
        "source_receipts": {
            key: {
                "path": str(canonical(roots[(segment, authority)] / "8s" / filename)),
                "sha256": sha256(canonical(roots[(segment, authority)] / "8s" / filename)),
            }
            for key, segment, authority, filename in (
                ("A_CFA4", "A", "CFA4_PRIMARY", "STACK_CFA4_RECEIPT.json"),
                ("C_CFA4", "C", "CFA4_PRIMARY", "STACK_CFA4_RECEIPT.json"),
                ("A_RGB", "A", "RGB_DERIVATIVE", "STACK_RECEIPT.json"),
                ("C_RGB", "C", "RGB_DERIVATIVE", "STACK_RECEIPT.json"),
            )
        },
    }
    return {
        "schema": "SONY_S6_QA_AUDIT_RECEIPT_V1",
        "frame": "CORONA_SOLAR",
        "geometry": {
            "solar_center_xy_full_px": list(SOLAR_CENTER_XY),
            "solar_radius_px": SOLAR_RADIUS_PX,
            "authority": SOLAR_RADIUS_AUTHORITY,
            "split_z_sampling": (
                "CFA4 split z stride 4 CFA pixels = 8 full-sensor pixels; "
                "per-plane offsets are applied"
            ),
            "plane_order": list(PLANE_ORDER),
            "plane_offsets_yx": [list(row) for row in PLANE_OFFSETS_YX],
        },
        "acceptance_gate": ANNULAR_GATE,
        "accepted_products": accepted,
        "eight_second_covariance": eight_second,
        "cross_segment_policy": "A and C are never combined",
    }


def read_exif(raw_paths: list[Path]) -> tuple[dict[str, dict[str, Any]], str]:
    try:
        version = subprocess.run(
            ["exiftool", "-ver"], check=True, capture_output=True, text=True
        ).stdout.strip()
        command = [
            "exiftool", "-json", "-n", "-ExposureTime", "-ISO",
            "-CameraTemperature", "-Model", "-LensModel",
            *map(str, raw_paths),
        ]
        output = subprocess.run(
            command, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError(f"read-only exiftool audit failed: {exc}") from exc
    parsed = json.loads(output.stdout)
    if len(parsed) != len(raw_paths):
        raise ContractError("exiftool did not return every RAW")
    by_name: dict[str, dict[str, Any]] = {}
    for row in parsed:
        name = Path(row["SourceFile"]).stem
        if name in by_name:
            raise ContractError(f"duplicate EXIF row: {name}")
        by_name[name] = row
    return by_name, version


def build_raw_ledger(
    raw_root: Path,
    receipt_objects: dict[tuple[str, str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    raw_root = canonical(raw_root)
    expected_from_upstream: dict[str, dict[str, Any]] = {}
    product_by_frame: dict[str, ProductSpec] = {}
    for spec in PRODUCTS:
        rgb_receipt = receipt_objects[(spec.segment, spec.tag, "RGB_DERIVATIVE")]
        inputs = {row["name"]: row for row in rgb_receipt.get("inputs", [])}
        cfa_receipt = receipt_objects[(spec.segment, spec.tag, "CFA4_PRIMARY")]
        current_cfa = {row["name"]: row
                       for row in cfa_receipt.get("current_raw_hashes_revalidated", [])}
        for frame in spec.members:
            if frame in product_by_frame:
                raise ContractError(f"frame belongs to two products: {frame}")
            product_by_frame[frame] = spec
            if frame not in inputs or frame not in current_cfa:
                raise ContractError(f"upstream RAW evidence missing: {frame}")
            rgb = inputs[frame]
            cfa = current_cfa[frame]
            if (rgb.get("sha256"), rgb.get("bytes")) != \
                    (cfa.get("sha256"), cfa.get("bytes")):
                raise ContractError(f"RGB/CFA RAW evidence mismatch: {frame}")
            expected_from_upstream[frame] = rgb
    raw_paths = [canonical(raw_root / f"DSC{number:05d}.ARW")
                 for number in range(6982, 7000)]
    exif, exiftool_version = read_exif(raw_paths)
    ledger: list[dict[str, Any]] = []
    for raw in raw_paths:
        frame = raw.stem
        if raw != raw_root / f"{frame}.ARW":
            raise ContractError(f"RAW path is not canonical and exact: {raw}")
        digest = sha256(raw)
        size = raw.stat().st_size
        metadata = exif.get(frame)
        if metadata is None:
            raise ContractError(f"missing EXIF metadata: {frame}")
        if metadata.get("Model") != "ILCE-7RM3A" or metadata.get("ISO") != 100 \
                or metadata.get("CameraTemperature") != 40 \
                or metadata.get("LensModel") != "FE 300mm F2.8 GM OSS":
            raise ContractError(f"unexpected body/calibration metadata: {frame} {metadata}")
        if frame in product_by_frame:
            spec = product_by_frame[frame]
            upstream = expected_from_upstream[frame]
            if digest != upstream.get("sha256") or size != upstream.get("bytes"):
                raise ContractError(f"current RAW differs from upstream receipt: {frame}")
            assert_close(float(metadata["ExposureTime"]), spec.exposure_s,
                         f"{frame} EXIF exposure")
            disposition = "PROCESSAT"
            product_id = spec.product_id
            scientific_verdict = spec.verdict
            reasons = list(spec.reason_codes)
        else:
            decision = CAPTURE_DECISIONS[frame]
            assert_close(float(metadata["ExposureTime"]), decision["exposure_s"],
                         f"{frame} EXIF exposure")
            disposition = decision["pipeline_disposition"]
            product_id = None
            scientific_verdict = disposition
            reasons = decision["reason_codes"]
        ledger.append({
            "candidate": frame,
            "raw": {
                "path": str(raw),
                "bytes": size,
                "sha256": digest,
                "hash_basis": "direct current canonical RAW bytes",
            },
            "exif": {
                "exposure_s": float(metadata["ExposureTime"]),
                "iso": metadata["ISO"],
                "camera_temperature_c": metadata["CameraTemperature"],
                "model": metadata["Model"],
                "lens_model": metadata["LensModel"],
            },
            "pipeline_disposition": disposition,
            "product_id": product_id,
            "scientific_verdict": scientific_verdict,
            "reason_codes": reasons,
        })
        print(f"RAW {frame}: {disposition} {digest[:12]}", flush=True)
    counts = {status: sum(row["pipeline_disposition"] == status for row in ledger)
              for status in ("PROCESSAT", "REBUTJAT", "QUARANTENA")}
    if counts != {"PROCESSAT": 14, "REBUTJAT": 2, "QUARANTENA": 2}:
        raise ContractError(f"ledger counts are not 14+2+2: {counts}")
    if len({row["candidate"] for row in ledger}) != 18:
        raise ContractError("ledger contains duplicate candidates")
    return ledger, exiftool_version


def link_validated(
    source: Path, destination: Path, digest: str,
    digest_cache: dict[Path, str], stage: Path,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ContractError(f"refusing to overwrite package path: {destination}")
    if source.stat().st_dev != destination.parent.stat().st_dev:
        raise ContractError(f"cannot hardlink across filesystems: {source}")
    os.link(source, destination)
    source_stat = source.stat()
    destination_stat = destination.stat()
    if (source_stat.st_dev, source_stat.st_ino) != \
            (destination_stat.st_dev, destination_stat.st_ino):
        raise ContractError(f"hardlink inode check failed: {destination}")
    rel = destination.relative_to(stage)
    digest_cache[rel] = digest
    return {
        "source_path": str(source),
        "package_path": str(rel),
        "bytes": source_stat.st_size,
        "sha256": digest,
        "materialisation": "HARDLINK_SAME_DEVICE_INODE_VERIFIED",
    }


def copy_snapshot(
    source: Path, destination: Path, digest_cache: dict[Path, str], stage: Path
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ContractError(f"refusing to overwrite snapshot: {destination}")
    shutil.copy2(source, destination)
    digest = sha256(destination)
    if digest != sha256(source):
        raise ContractError(f"snapshot hash mismatch: {source}")
    rel = destination.relative_to(stage)
    digest_cache[rel] = digest
    return {
        "source_path": str(source),
        "package_path": str(rel),
        "bytes": destination.stat().st_size,
        "sha256": digest,
        "materialisation": "BYTE_IDENTICAL_SNAPSHOT",
    }


def make_cfa4_mask(source_group: Path, destination: Path,
                   minimum_rsun: float) -> dict[str, Any]:
    master = np.load(source_group / "MASTER_CFA4_linear_float32_ADU_s.npy",
                     mmap_mode="r")
    variance = np.load(source_group / "MASTER_VARIANCE_TOTAL.npy", mmap_mode="r")
    coverage = np.load(source_group / "MASTER_COVERAGE_N.npy", mmap_mode="r")
    if master.shape != variance.shape or master.shape != coverage.shape \
            or master.ndim != 3 or master.shape[2] != 4:
        raise ContractError(f"CFA4 mask source shape mismatch: {source_group}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = np.lib.format.open_memmap(
        destination, mode="w+", dtype=np.bool_, shape=master.shape
    )
    x = np.arange(master.shape[1], dtype=np.float64)
    true_count = 0
    for y0 in range(0, master.shape[0], 64):
        y1 = min(master.shape[0], y0 + 64)
        y = np.arange(y0, y1, dtype=np.float64)[:, None]
        for plane, (oy, ox) in enumerate(PLANE_OFFSETS_YX):
            rho = np.hypot(
                (2.0 * x[None, :] + ox) - SOLAR_CENTER_XY[0],
                (2.0 * y + oy) - SOLAR_CENTER_XY[1],
            ) / SOLAR_RADIUS_PX
            valid = (
                (rho >= minimum_rsun)
                & (coverage[y0:y1, :, plane] > 0)
                & np.isfinite(variance[y0:y1, :, plane])
                & np.isfinite(master[y0:y1, :, plane])
            )
            output[y0:y1, :, plane] = valid
            true_count += int(np.count_nonzero(valid))
    output.flush()
    del output
    digest = sha256(destination)
    return {
        "path": destination.name,
        "sha256": digest,
        "bytes": destination.stat().st_size,
        "shape": list(master.shape),
        "dtype": "bool",
        "true_count": true_count,
        "true_fraction": true_count / int(np.prod(master.shape)),
        "definition": (
            f"rho >= {minimum_rsun:.1f} Rsun at each native CFA plane offset; "
            "MASTER_COVERAGE_N > 0; finite primary master and total variance"
        ),
    }


def make_rgb_mask(source_group: Path, destination: Path,
                  minimum_rsun: float) -> dict[str, Any]:
    variance = np.load(source_group / "VARIANCE_ADU2_s2.npy", mmap_mode="r")
    coverage = np.load(source_group / "COVERAGE_N.npy", mmap_mode="r")
    if variance.shape != coverage.shape or variance.ndim != 3 \
            or variance.shape[2] != 3:
        raise ContractError(f"RGB mask source shape mismatch: {source_group}")
    shape = variance.shape[:2]
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = np.lib.format.open_memmap(
        destination, mode="w+", dtype=np.bool_, shape=shape
    )
    x = np.arange(shape[1], dtype=np.float64)[None, :]
    true_count = 0
    for y0 in range(0, shape[0], 64):
        y1 = min(shape[0], y0 + 64)
        y = np.arange(y0, y1, dtype=np.float64)[:, None]
        rho = np.hypot(x - SOLAR_CENTER_XY[0],
                       y - SOLAR_CENTER_XY[1]) / SOLAR_RADIUS_PX
        valid = (
            (rho >= minimum_rsun)
            & np.all(coverage[y0:y1] > 0, axis=2)
            & np.all(np.isfinite(variance[y0:y1]), axis=2)
        )
        output[y0:y1] = valid
        true_count += int(np.count_nonzero(valid))
    output.flush()
    del output
    digest = sha256(destination)
    return {
        "path": destination.name,
        "sha256": digest,
        "bytes": destination.stat().st_size,
        "shape": list(shape),
        "dtype": "bool",
        "true_count": true_count,
        "true_fraction": true_count / int(np.prod(shape)),
        "definition": (
            f"rho >= {minimum_rsun:.1f} Rsun at full RGB sampling; all-channel "
            "COVERAGE_N > 0 and finite total variance. Upstream combine guarantees "
            "finite master wherever these conditions hold."
        ),
    }


def materialise_product(
    stage: Path,
    spec: ProductSpec,
    roots: dict[tuple[str, str], Path],
    records: dict[str, list[dict[str, Any]]],
    receipts: dict[str, dict[str, Any]],
    qa_receipt_sha256: str,
    digest_cache: dict[Path, str],
) -> dict[str, Any]:
    product_dir = stage / "products" / f"segment_{spec.segment}" / spec.tag
    linked: list[dict[str, Any]] = []
    for authority in ("CFA4_PRIMARY", "RGB_DERIVATIVE"):
        destination_root = product_dir / authority
        for row in records[authority]:
            linked.append(link_validated(
                row["source"], destination_root / Path(row["source_rel"]).name,
                row["sha256"], digest_cache, stage,
            ))
    masks: dict[str, Any] | None = None
    if spec.verdict == "ACCEPTAT":
        mask_dir = product_dir / "VALIDITY_MASKS"
        cfa = make_cfa4_mask(
            roots[(spec.segment, "CFA4_PRIMARY")] / spec.tag,
            mask_dir / "VALID_DOMAIN_CFA4.npy",
            float(spec.accepted_min_rsun),
        )
        rgb = make_rgb_mask(
            roots[(spec.segment, "RGB_DERIVATIVE")] / spec.tag,
            mask_dir / "VALID_DOMAIN_RGB_ALL_CHANNELS.npy",
            float(spec.accepted_min_rsun),
        )
        for row in (cfa, rgb):
            rel = (mask_dir / row["path"]).relative_to(stage)
            digest_cache[rel] = row["sha256"]
            row["path"] = str(rel)
        masks = {"CFA4_PRIMARY": cfa, "RGB_DERIVATIVE": rgb}
    receipt_kind = ("STACK_ACCEPTANCE_RECEIPT"
                    if spec.verdict == "ACCEPTAT"
                    else "CONTRIBUTION_QUARANTINE_RECEIPT")
    receipt_name = ("STACK_ACCEPTANCE_RECEIPT.json"
                    if spec.verdict == "ACCEPTAT"
                    else "CONTRIBUTION_QUARANTINE_RECEIPT.json")
    receipt = {
        "schema": "SONY_S6_PRODUCT_RECEIPT_V1",
        "receipt_kind": receipt_kind,
        "product_id": spec.product_id,
        "product_class": spec.product_class,
        "frame": "CORONA_SOLAR",
        "mount_segment": spec.segment,
        "exposure_s": spec.exposure_s,
        "members": list(spec.members),
        "skill_verdict": spec.verdict,
        "reason_codes": list(spec.reason_codes),
        "segment_contract": (
            "this product contains one mount segment only; A and C are never combined"
        ),
        "authority": {
            "primary": "CFA4 R/G1/B/G2 linear products",
            "derivative": "Gaussian-demosaic RGB; not exact CFA authority",
            "random_systematic_variance": (
                "separate random and donor-flat systematic arrays are retained"
            ),
        },
        "radial_domain": ({
            "status": "ACCEPTAT",
            "literal_domain": f"rho >= {spec.accepted_min_rsun:.1f} Rsun",
            "outer_bound": "per-pixel hashed support mask; no artificial radial upper cut",
            "mask_role": (
                "hard scientific validity metadata only; not a feather, blend or "
                "Photoshop compositing mask"
            ),
        } if spec.verdict == "ACCEPTAT" else ({
            "status": EIGHT_SECOND_REASON,
            "provisional_visual_domain": f"rho >= {spec.provisional_visual_min_rsun:.1f} Rsun",
            "authorises_scientific_stack": False,
        } if spec.provisional_visual_min_rsun is not None else None)),
        "eight_second_covariance": ({
            "diagonal_variance_factor": 1.0,
            "status": EIGHT_SECOND_REASON,
            "spatial_covariance_product": "PENDENT",
        } if spec.exposure_s == 8.0 else None),
        "qa_audit_receipt": {
            "path": "QA_AUDIT_RECEIPT.json",
            "sha256": qa_receipt_sha256,
        },
        "validity_masks": masks,
        "upstream_receipts": {
            "CFA4_PRIMARY": sha256(
                roots[(spec.segment, "CFA4_PRIMARY")] / spec.tag
                / "STACK_CFA4_RECEIPT.json"
            ),
            "RGB_DERIVATIVE": sha256(
                roots[(spec.segment, "RGB_DERIVATIVE")] / spec.tag
                / "STACK_RECEIPT.json"
            ),
        },
        "hardlinked_upstream_files": linked,
        "source_mutations": 0,
    }
    receipt_path = product_dir / receipt_name
    receipt_sha = write_json(receipt_path, receipt)
    digest_cache[receipt_path.relative_to(stage)] = receipt_sha
    print(
        f"materialised {spec.product_id}: {spec.verdict}, "
        f"{len(linked)} hardlinks",
        flush=True,
    )
    return {
        "product_id": spec.product_id,
        "path": str(product_dir.relative_to(stage)),
        "receipt": str(receipt_path.relative_to(stage)),
        "receipt_sha256": receipt_sha,
        "product_class": spec.product_class,
        "mount_segment": spec.segment,
        "exposure_s": spec.exposure_s,
        "members": list(spec.members),
        "verdict": spec.verdict,
        "accepted_min_rsun": spec.accepted_min_rsun,
        "provisional_visual_min_rsun": spec.provisional_visual_min_rsun,
        "hardlinked_file_count": len(linked),
        "masks": masks,
    }


def write_ledgers(stage: Path, ledger: list[dict[str, Any]],
                  digest_cache: dict[Path, str]) -> dict[str, Any]:
    ledger_path = stage / "FRAME_LEDGER.json"
    counts = {status: sum(row["pipeline_disposition"] == status for row in ledger)
              for status in ("PROCESSAT", "REBUTJAT", "QUARANTENA")}
    ledger_object = {
        "schema": "SONY_S6_FRAME_LEDGER_V1",
        "candidate_range": "DSC06982--DSC06999 inclusive",
        "candidate_count": len(ledger),
        "counts": counts,
        "duplicate_candidates": 0,
        "frames": ledger,
    }
    ledger_hash = write_json(ledger_path, ledger_object)
    digest_cache[ledger_path.relative_to(stage)] = ledger_hash

    csv_path = stage / "FRAME_LEDGER.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "candidate", "exposure_s", "pipeline_disposition", "product_id",
            "scientific_verdict", "reason_codes", "raw_path", "raw_bytes",
            "raw_sha256", "iso", "camera_temperature_c", "model", "lens_model",
        ])
        writer.writeheader()
        for row in ledger:
            writer.writerow({
                "candidate": row["candidate"],
                "exposure_s": row["exif"]["exposure_s"],
                "pipeline_disposition": row["pipeline_disposition"],
                "product_id": row["product_id"] or "",
                "scientific_verdict": row["scientific_verdict"],
                "reason_codes": "|".join(row["reason_codes"]),
                "raw_path": row["raw"]["path"],
                "raw_bytes": row["raw"]["bytes"],
                "raw_sha256": row["raw"]["sha256"],
                "iso": row["exif"]["iso"],
                "camera_temperature_c": row["exif"]["camera_temperature_c"],
                "model": row["exif"]["model"],
                "lens_model": row["exif"]["lens_model"],
            })
    csv_hash = sha256(csv_path)
    digest_cache[csv_path.relative_to(stage)] = csv_hash

    frame_receipts: list[dict[str, Any]] = []
    for row in ledger:
        path = stage / "frame_receipts" / f"{row['candidate']}.json"
        value = {
            "schema": "SONY_S6_FRAME_DECISION_RECEIPT_V1",
            **row,
            "source_mutations": 0,
        }
        digest = write_json(path, value)
        digest_cache[path.relative_to(stage)] = digest
        frame_receipts.append({
            "candidate": row["candidate"],
            "path": str(path.relative_to(stage)),
            "sha256": digest,
        })
    return {
        "json": {"path": str(ledger_path.relative_to(stage)), "sha256": ledger_hash},
        "csv": {"path": str(csv_path.relative_to(stage)), "sha256": csv_hash},
        "frame_receipts": frame_receipts,
        "counts": counts,
    }


def write_readme(stage: Path, digest_cache: dict[Path, str]) -> dict[str, Any]:
    path = stage / "README.md"
    text = """# Sony S6 — catàleg auditat

Aquest directori és un lliurament mixt, no una declaració que tot el seu
contingut sigui acceptable. L'autoritat científica primària és CFA4 lineal
(`R/G1/B/G2`); els TIFF RGB són derivats amb demosaic gaussià.

Només tres stacks repetits del segment C tenen veredicte literal `ACCEPTAT`:

- `1/30 s`: corona a `rho >= 1.2 R_sun`;
- `1/4 s`: corona a `rho >= 1.5 R_sun`;
- `2 s`: corona a `rho >= 2.0 R_sun`.

Cada domini també exigeix que la màscara de validesa hashada sigui certa.
Aquestes màscares són suport científic dur: no són màscares de feather ni de
composició visual.

Les contribucions A es conserven separades i mai es combinen amb C. El `1/8 s`
de C també és una contribució single. Tots els `8 s` mantenen factor de
variància diagonal `1.0` i queden en `QUARANTENA_COVARIANCIA_PENDENT`; el C8
només té un domini visual provisional `rho >= 3 R_sun`, que no l'autoritza com
a stack científic.

`FRAME_LEDGER.json` conté exactament els 18 candidats: 14 processats, 2
rebutjats i 2 en quarantena de captura, sense duplicats. `QA_AUDIT_RECEIPT.json`
conté els tests anulars/sectorials/ACF i la correcció explícita dels 8 s.
`SHA256SUMS.txt` cobreix tots els fitxers del paquet menys ell mateix.
"""
    path.write_text(text, encoding="utf-8")
    digest = sha256(path)
    digest_cache[path.relative_to(stage)] = digest
    return {"path": str(path.relative_to(stage)), "sha256": digest}


def write_package_manifest(stage: Path, digest_cache: dict[Path, str]) -> Path:
    manifest = stage / "SHA256SUMS.txt"
    actual_files = {
        path.relative_to(stage) for path in stage.rglob("*")
        if path.is_file() and path != manifest
    }
    missing = actual_files - set(digest_cache)
    stale = set(digest_cache) - actual_files
    if stale:
        raise ContractError(f"digest cache contains absent files: {sorted(map(str, stale))}")
    for rel in sorted(missing, key=str):
        digest_cache[rel] = sha256(stage / rel)
    with manifest.open("w", encoding="utf-8") as handle:
        for rel in sorted(actual_files, key=str):
            handle.write(f"{digest_cache[rel]}  {rel}\n")
    return manifest


def build(args: argparse.Namespace) -> Path:
    static_contract()
    roots = roots_from_args(args)
    raw_root = canonical(args.raw_root)
    target = args.target.expanduser().resolve(strict=False)
    if target.exists():
        raise ContractError(f"target already exists; no clobber: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    runs, run_records = validate_runs(roots)
    source_records: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    receipt_objects: dict[tuple[str, str, str], dict[str, Any]] = {}
    for spec in PRODUCTS:
        records, receipts = validate_product_sources(spec, roots, runs)
        source_records[(spec.segment, spec.tag)] = records
        for authority, receipt in receipts.items():
            receipt_objects[(spec.segment, spec.tag, authority)] = receipt
    qa = build_qa_evidence(roots, receipt_objects)
    ledger, exiftool_version = build_raw_ledger(raw_root, receipt_objects)

    stage = Path(tempfile.mkdtemp(
        prefix=f".{target.name}.building-", dir=str(target.parent)
    ))
    digest_cache: dict[Path, str] = {}
    created_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        provenance_runs: list[dict[str, Any]] = []
        for key in sorted(run_records):
            segment, authority = key
            for row in run_records[key]:
                label = ("RGB" if authority == "RGB_DERIVATIVE" else "CFA4")
                destination = (
                    stage / "provenance/upstream_runs"
                    / f"segment_{segment}" / f"{label}_{Path(row['source_rel']).name}"
                )
                provenance_runs.append(link_validated(
                    row["source"], destination, row["sha256"], digest_cache, stage
                ))
        software_snapshots = [
            copy_snapshot(canonical(RGB_SCRIPT),
                          stage / "provenance/software/stack_sony_s6.py",
                          digest_cache, stage),
            copy_snapshot(canonical(CFA4_SCRIPT),
                          stage / "provenance/software/stack_sony_cfa4_s6.py",
                          digest_cache, stage),
            copy_snapshot(canonical(Path(__file__)),
                          stage / "provenance/software/materialize_sony_s6_accepted.py",
                          digest_cache, stage),
        ]

        qa.update({
            "created_utc": created_utc,
            "software": {
                "materializer_path": str(canonical(Path(__file__))),
                "materializer_sha256": sha256(canonical(Path(__file__))),
                "rgb_builder_sha256": EXPECTED_RGB_SCRIPT_SHA256,
                "cfa4_builder_sha256": EXPECTED_CFA4_SCRIPT_SHA256,
            },
            "global_skill_evidence": ({
                "path": str(canonical(SKILL_PATH)),
                "sha256": sha256(canonical(SKILL_PATH)),
                "authority_note": (
                    "the global skill was read but not edited; the run-specific "
                    "8 s correction in this receipt overrides its stale scalar claim"
                ),
            } if SKILL_PATH.exists() else {
                "path": str(SKILL_PATH), "status": "NOT_PRESENT_AT_MATERIALISATION"
            }),
        })
        qa_path = stage / "QA_AUDIT_RECEIPT.json"
        qa_hash = write_json(qa_path, qa)
        digest_cache[qa_path.relative_to(stage)] = qa_hash

        product_catalogue: list[dict[str, Any]] = []
        for spec in PRODUCTS:
            product_catalogue.append(materialise_product(
                stage, spec, roots, source_records[(spec.segment, spec.tag)],
                {
                    authority: receipt_objects[(spec.segment, spec.tag, authority)]
                    for authority in ("CFA4_PRIMARY", "RGB_DERIVATIVE")
                },
                qa_hash, digest_cache,
            ))

        ledgers = write_ledgers(stage, ledger, digest_cache)
        readme = write_readme(stage, digest_cache)
        accepted_products = [row for row in product_catalogue
                             if row["verdict"] == "ACCEPTAT"]
        quarantined_products = [row for row in product_catalogue
                                if row["verdict"] == "QUARANTENA"]
        catalog = {
            "schema": "SONY_S6_ACCEPTED_CATALOGUE_V1",
            "created_utc": created_utc,
            "delivery_class": "MIXED_AUDITED_CATALOGUE",
            "overall_verdict": (
                "3 STACKS ACCEPTAT + 8 CONTRIBUCIONS INDEPENDENTS QUARANTENA"
            ),
            "warning": (
                "the directory name does not promote quarantined contributions; "
                "consume only literal product receipts"
            ),
            "frame": "CORONA_SOLAR",
            "camera_train": "SONY_A7RIIIA_FE300MM_F2.8_GM",
            "authority": {
                "primary": "CFA4 R/G1/B/G2 linear",
                "rgb": "derived Gaussian demosaic",
                "random_systematic_variance": "retained separately",
            },
            "geometry": {
                "solar_center_xy_full_px": list(SOLAR_CENTER_XY),
                "solar_radius_px": SOLAR_RADIUS_PX,
                "authority": SOLAR_RADIUS_AUTHORITY,
            },
            "segment_policy": {
                "combined_A_C_products": 0,
                "literal": "segments A and C are never combined",
            },
            "accepted_radial_domains": {
                row["product_id"]: {
                    "minimum_rsun": row["accepted_min_rsun"],
                    "requires_hashed_validity_mask": True,
                }
                for row in accepted_products
            },
            "eight_second_policy": {
                "diagonal_variance_factor": 1.0,
                "verdict": "QUARANTENA",
                "reason_code": EIGHT_SECOND_REASON,
                "C8_provisional_visual_min_rsun": 3.0,
                "C8_scientific_acceptance": False,
            },
            "product_counts": {
                "total": len(product_catalogue),
                "accepted_repeated_C_stacks": len(accepted_products),
                "quarantined_independent_contributions": len(quarantined_products),
            },
            "candidate_counts": ledgers["counts"],
            "candidate_total": 18,
            "products": product_catalogue,
            "ledgers": ledgers,
            "qa_audit": {"path": str(qa_path.relative_to(stage)), "sha256": qa_hash},
            "readme": readme,
            "upstream_run_hardlinks": provenance_runs,
            "software_snapshots": software_snapshots,
            "software": {
                "materializer_sha256": sha256(canonical(Path(__file__))),
                "rgb_builder_sha256": EXPECTED_RGB_SCRIPT_SHA256,
                "cfa4_builder_sha256": EXPECTED_CFA4_SCRIPT_SHA256,
                "exiftool_version": exiftool_version,
                "python": sys.version,
                "numpy": np.__version__,
                "argv": sys.argv,
            },
            "hash_contract": {
                "algorithm": "SHA-256",
                "upstream": "direct source-byte rehash followed by same-inode hardlink",
                "package_manifest": "SHA256SUMS.txt; every package file except itself",
            },
            "source_mutations": 0,
        }
        catalog_path = stage / "CATALOG_RECEIPT.json"
        catalog_hash = write_json(catalog_path, catalog)
        digest_cache[catalog_path.relative_to(stage)] = catalog_hash
        manifest = write_package_manifest(stage, digest_cache)
        manifest_hash = sha256(manifest)
        stage.rename(target)
        print(f"published atomically: {target}", flush=True)
        print(f"catalog_sha256={catalog_hash}", flush=True)
        print(f"manifest_sha256={manifest_hash}", flush=True)
        return target
    except Exception:
        if stage.exists() and stage.parent == target.parent \
                and stage.name.startswith(f".{target.name}.building-"):
            shutil.rmtree(stage)
        raise


def verify_package(target: Path, *, check_sources: bool) -> dict[str, Any]:
    target = canonical(target)
    manifest = canonical(target / "SHA256SUMS.txt")
    entries = parse_sha_manifest(manifest)
    actual_files = {
        path.relative_to(target) for path in target.rglob("*")
        if path.is_file() and path != manifest
    }
    if set(entries) != actual_files:
        raise ContractError(
            f"package manifest topology mismatch: "
            f"extra={sorted(map(str, actual_files - set(entries)))}, "
            f"missing={sorted(map(str, set(entries) - actual_files))}"
        )
    total_bytes = 0
    for index, (rel, expected) in enumerate(sorted(entries.items(), key=lambda row: str(row[0])), 1):
        path = canonical(target / rel)
        actual = sha256(path)
        if actual != expected:
            raise ContractError(f"package hash mismatch {rel}: {actual} != {expected}")
        total_bytes += path.stat().st_size
        if index % 25 == 0 or index == len(entries):
            print(f"verified package hashes {index}/{len(entries)}", flush=True)
    catalog = json_object(target / "CATALOG_RECEIPT.json")
    ledger = json_object(target / "FRAME_LEDGER.json")
    if ledger.get("candidate_count") != 18 or ledger.get("counts") != {
        "PROCESSAT": 14, "QUARANTENA": 2, "REBUTJAT": 2
    }:
        raise ContractError("verified ledger is not exact 18=14+2+2")
    candidates = [row["candidate"] for row in ledger.get("frames", [])]
    if len(candidates) != 18 or len(set(candidates)) != 18:
        raise ContractError("verified ledger duplicates/misses candidates")
    products = catalog.get("products", [])
    accepted = [row for row in products if row.get("verdict") == "ACCEPTAT"]
    if len(accepted) != 3:
        raise ContractError("verified catalogue does not have exactly 3 accepted products")
    for row in accepted:
        if row.get("mount_segment") != "C" or len(row.get("members", [])) < 2 \
                or not row.get("masks"):
            raise ContractError(f"illegal accepted product after verification: {row}")
    for row in products:
        if float(row["exposure_s"]) == 8.0 and row.get("verdict") != "QUARANTENA":
            raise ContractError("an 8 s product was promoted")
    if catalog.get("segment_policy", {}).get("combined_A_C_products") != 0:
        raise ContractError("catalogue claims a combined A-C product")
    hardlinks_checked = 0
    if check_sources:
        for row in products:
            receipt = json_object(target / row["receipt"])
            for linked in receipt.get("hardlinked_upstream_files", []):
                source = Path(linked["source_path"])
                package = target / linked["package_path"]
                if not source.exists():
                    raise ContractError(f"hardlink source no longer exists: {source}")
                if (source.stat().st_dev, source.stat().st_ino) != \
                        (package.stat().st_dev, package.stat().st_ino):
                    raise ContractError(f"source/package are not hardlinks: {package}")
                hardlinks_checked += 1
    return {
        "target": str(target),
        "file_count_excluding_manifest": len(entries),
        "apparent_bytes_excluding_manifest": total_bytes,
        "manifest_sha256": sha256(manifest),
        "catalog_sha256": sha256(target / "CATALOG_RECEIPT.json"),
        "qa_sha256": sha256(target / "QA_AUDIT_RECEIPT.json"),
        "ledger_sha256": sha256(target / "FRAME_LEDGER.json"),
        "hardlinks_checked_against_sources": hardlinks_checked,
        "verdict": "PASS",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    result.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    result.add_argument("--a-rgb-root", type=Path,
                        default=DEFAULT_ROOTS[("A", "RGB_DERIVATIVE")])
    result.add_argument("--c-rgb-root", type=Path,
                        default=DEFAULT_ROOTS[("C", "RGB_DERIVATIVE")])
    result.add_argument("--a-cfa4-root", type=Path,
                        default=DEFAULT_ROOTS[("A", "CFA4_PRIMARY")])
    result.add_argument("--c-cfa4-root", type=Path,
                        default=DEFAULT_ROOTS[("C", "CFA4_PRIMARY")])
    result.add_argument("--verify", type=Path,
                        help="read-only verification of an existing package")
    result.add_argument("--check-sources", action="store_true",
                        help="with --verify, also require same-inode upstream sources")
    result.add_argument("--self-test", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    static_contract()
    if args.self_test:
        print(json.dumps({
            "verdict": "PASS",
            "products": len(PRODUCTS),
            "processed_frames": len({frame for spec in PRODUCTS for frame in spec.members}),
            "accepted_products": sum(spec.verdict == "ACCEPTAT" for spec in PRODUCTS),
            "capture_decisions": CAPTURE_DECISIONS,
        }, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.verify:
        print(json.dumps(
            verify_package(args.verify, check_sources=args.check_sources),
            indent=2, ensure_ascii=False, sort_keys=True,
        ))
        return 0
    target = build(args)
    print(json.dumps({"target": str(target), "verdict": "BUILT"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
