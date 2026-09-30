#!/usr/bin/env python3
"""Build a fail-closed Sony-C HDR and a measured Sony->Vixen visual layer.

The only Sony inputs admitted by this program are the three repeated, accepted
segment-C stacks at 1/30, 1/4 and 2 seconds in ``sony_s6_ACCEPTED``.  Their
CFA4 products remain the scientific authority; the RGB products consumed here
are explicitly a Gaussian-demosaic visual derivative.  Segment A, all singles
and every 8-second product are rejected by construction.

The program performs four auditable operations:

1. match the three accepted RGB exposure groups with a robust per-channel
   gain plus additive plane, then combine them with random inverse-variance
   weights while retaining donor-flat systematics as correlated variance;
2. resample the Sony product directly to the immutable Vixen solar frame with
   the plate solution supplied for this dataset (bilinear values, squared
   bilinear weights for random variance);
3. match Sony to Vixen with one further robust per-channel gain plus additive
   plane and propagate the fitted gain and coefficient covariance;
4. derive a conservative visual alpha from inverse variance and valid support,
   never from image brightness or desired coronal structure.  Candidate support
   tapers are selected by annular and sector seam tests.  No free circular mask
   or transferred lunar transform exists in this code.

If the fusion gates do not pass, the registered/matched Sony layer is still
delivered separately and the receipt verdict is ``NO_ACCEPTADA_PER_FUSIO``.
The program never overwrites an output directory and publishes through an
atomic same-directory rename.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from numpy.lib.format import open_memmap
from scipy import ndimage as ndi
import tifffile


SCHEMA = "SONY_CROSS_TRAIN_LAYER_V1"
RECEIPT_SCHEMA = "SONY_CROSS_TRAIN_LAYER_RECEIPT_V1"
ACCEPTED = "ACCEPTAT"
SONY_SHAPE = (5320, 7968, 3)
VIXEN_SHAPE = (4640, 6960, 3)
SONY_CENTER_XY = (3894.0057024183907, 2768.6725752051257)
VIXEN_CENTER_XY = (3563.8912793889317, 2274.660453669)
SONY_PLATE_SCALE = 3.2019913768363018
VIXEN_PLATE_SCALE = 2.1495
SOURCE_TO_DEST_SCALE = SONY_PLATE_SCALE / VIXEN_PLATE_SCALE
SOURCE_TO_DEST_ROTATION_DEG = 33.08059690231728
SONY_RADIUS_PX = 946.6598 / SONY_PLATE_SCALE
VIXEN_RADIUS_PX = 946.6598 / VIXEN_PLATE_SCALE
RESEARCH80_STAR_SCALE = 1.48860
RESEARCH80_STAR_ROTATION_DEG = 33.088
RESEARCH80_STAR_RMS_PX = 0.52
GROUPS = (
    ("1-30s", 1.0 / 30.0, 1.2),
    ("1-4s", 0.25, 1.5),
    ("2s", 2.0, 2.0),
)
ANCHOR_GROUP = "1-4s"
CHANNELS = ("R", "G", "B")
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float64)


class ContractError(RuntimeError):
    """A required provenance, geometry or data contract did not validate."""


@dataclass
class GroupInput:
    name: str
    exposure_s: float
    min_rsun: float
    directory: Path
    acceptance_receipt: Path
    acceptance: dict[str, Any]
    members: tuple[str, ...]
    paths: dict[str, Path]
    expected_hashes: dict[str, str]
    image: np.ndarray | None = None
    random_variance: np.ndarray | None = None
    systematic_variance: np.ndarray | None = None
    coverage: np.ndarray | None = None
    saturation: np.ndarray | None = None
    mask: np.ndarray | None = None


@dataclass(frozen=True)
class RobustFit:
    beta_scaled: np.ndarray
    covariance_scaled: np.ndarray
    source_median: float
    source_scale: float
    gain: float
    intercept: float
    coefficients_original: np.ndarray
    covariance_original: np.ndarray
    sample_count: int
    inlier_count: int
    robust_sigma: float
    median_residual: float
    p95_abs_residual: float
    iterations: int

    def apply(self, source: np.ndarray, xnorm: np.ndarray, ynorm: np.ndarray) -> np.ndarray:
        z = (source - self.source_median) / self.source_scale
        b = self.beta_scaled
        return b[0] * z + b[1] + b[2] * xnorm + b[3] * ynorm

    def model_variance(
        self, source: np.ndarray, xnorm: np.ndarray, ynorm: np.ndarray
    ) -> np.ndarray:
        z = (source - self.source_median) / self.source_scale
        design = np.stack((z, np.ones_like(z), xnorm, ynorm), axis=-1)
        return np.maximum(
            np.einsum("...i,ij,...j->...", design, self.covariance_scaled, design),
            0.0,
        )

    def receipt(self) -> dict[str, Any]:
        return {
            "model": "target = gain * source + intercept + bx*xnorm + by*ynorm",
            "gain": self.gain,
            "intercept": self.intercept,
            "bx": float(self.coefficients_original[2]),
            "by": float(self.coefficients_original[3]),
            "covariance_original": self.covariance_original.tolist(),
            "source_normalisation": {
                "median": self.source_median,
                "robust_scale": self.source_scale,
            },
            "sample_count": self.sample_count,
            "inlier_count": self.inlier_count,
            "robust_sigma_adu_s": self.robust_sigma,
            "median_residual_adu_s": self.median_residual,
            "p95_abs_residual_adu_s": self.p95_abs_residual,
            "iterations": self.iterations,
        }


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"No es pot llegir JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} no conté un objecte JSON")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def require_file(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"Falta {label}: {path}")
    return path


def output_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def expected_hardlink_index(receipt: dict[str, Any], receipt_path: Path) -> dict[str, str]:
    rows = receipt.get("hardlinked_upstream_files")
    if not isinstance(rows, list) or not rows:
        raise ContractError(f"{receipt_path}: falta hardlinked_upstream_files")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError(f"{receipt_path}: fila hardlink invàlida")
        package = row.get("package_path")
        digest = row.get("sha256")
        materialisation = row.get("materialisation")
        if (
            not isinstance(package, str)
            or not isinstance(digest, str)
            or len(digest) != 64
            or materialisation != "HARDLINK_SAME_DEVICE_INODE_VERIFIED"
        ):
            raise ContractError(f"{receipt_path}: contracte hardlink invàlid")
        if package in result:
            raise ContractError(f"{receipt_path}: package_path duplicat {package}")
        result[package] = digest
    return result


def validate_group(sony_root: Path, name: str, exposure: float, min_rsun: float) -> GroupInput:
    directory = sony_root / "products" / "segment_C" / name
    acceptance_path = require_file(directory / "STACK_ACCEPTANCE_RECEIPT.json", f"rebut {name}")
    receipt = json_object(acceptance_path)
    if (
        receipt.get("schema") != "SONY_S6_PRODUCT_RECEIPT_V1"
        or receipt.get("receipt_kind") != "STACK_ACCEPTANCE_RECEIPT"
        or receipt.get("skill_verdict") != ACCEPTED
        or receipt.get("mount_segment") != "C"
        or receipt.get("product_class") != "STACK_SEGMENT_C_REPETIT"
        or receipt.get("frame") != "CORONA_SOLAR"
        or receipt.get("source_mutations") != 0
    ):
        raise ContractError(f"{acceptance_path}: no és un stack C S6 ACCEPTAT immutable")
    got_exposure = receipt.get("exposure_s")
    if not isinstance(got_exposure, (int, float)) or not math.isclose(
        float(got_exposure), exposure, rel_tol=0.0, abs_tol=1e-12
    ):
        raise ContractError(f"{acceptance_path}: exposició inesperada {got_exposure!r}")
    members = receipt.get("members")
    if not isinstance(members, list) or len(members) != 2 or len(set(members)) != 2:
        raise ContractError(f"{acceptance_path}: calen dues captures independents")
    if any(not isinstance(item, str) or not item.startswith("DSC069") for item in members):
        raise ContractError(f"{acceptance_path}: membres invàlids")
    radial = receipt.get("radial_domain")
    expected_literal = f"rho >= {min_rsun:.1f} Rsun"
    if not isinstance(radial, dict) or radial.get("literal_domain") != expected_literal:
        raise ContractError(f"{acceptance_path}: domini radial no és {expected_literal}")
    authority = receipt.get("authority")
    if not isinstance(authority, dict) or "CFA4" not in str(authority.get("primary")):
        raise ContractError(f"{acceptance_path}: CFA4 no consta com autoritat")
    if "Gaussian-demosaic RGB" not in str(authority.get("derivative")):
        raise ContractError(f"{acceptance_path}: RGB no està declarat derivat gaussià")

    cfa_receipt = require_file(directory / "CFA4_PRIMARY" / "STACK_CFA4_RECEIPT.json", "rebut CFA4")
    cfa = json_object(cfa_receipt)
    if cfa.get("authority") != "PRIMARY_LINEAR_CFA4; RGB products are derivatives":
        raise ContractError(f"{cfa_receipt}: autoritat CFA4 divergent")
    split = cfa.get("split_independent")
    if not isinstance(split, dict) or split.get("status") != "MEASURED":
        raise ContractError(f"{cfa_receipt}: split CFA4 no mesurat")
    if split.get("left") == split.get("right"):
        raise ContractError(f"{cfa_receipt}: meitats CFA4 no independents")

    rgb = directory / "RGB_DERIVATIVE"
    paths = {
        "master": require_file(rgb / "MASTER_linear_float32_ADU_s.tif", "màster RGB"),
        "variance_random": require_file(rgb / "VARIANCE_RANDOM_ADU2_s2.npy", "variància aleatòria"),
        "variance_systematic": require_file(
            rgb / "VARIANCE_SYSTEMATIC_FLAT_ADU2_s2.npy", "variància sistemàtica"
        ),
        "coverage": require_file(rgb / "COVERAGE_N.npy", "cobertura"),
        "saturation": require_file(rgb / "SATURATION_COUNT.npy", "saturació"),
        "valid_mask": require_file(
            directory / "VALIDITY_MASKS" / "VALID_DOMAIN_RGB_ALL_CHANNELS.npy",
            "màscara de domini acceptat",
        ),
        "rgb_receipt": require_file(rgb / "STACK_RECEIPT.json", "rebut RGB derivat"),
        "cfa_receipt": cfa_receipt,
    }
    validity = receipt.get("validity_masks", {}).get("RGB_DERIVATIVE")
    if not isinstance(validity, dict):
        raise ContractError(f"{acceptance_path}: falta registre de la màscara RGB")
    expected_mask_hash = validity.get("sha256")
    expected_mask_shape = validity.get("shape")
    if expected_mask_shape != [SONY_SHAPE[0], SONY_SHAPE[1]]:
        raise ContractError(f"{acceptance_path}: shape de màscara inesperat")

    package_index = expected_hardlink_index(receipt, acceptance_path)
    expected: dict[str, str] = {}
    for role, path in paths.items():
        if role == "valid_mask":
            if not isinstance(expected_mask_hash, str):
                raise ContractError(f"{acceptance_path}: hash de màscara invàlid")
            expected[role] = expected_mask_hash
            continue
        relative = path.relative_to(sony_root).as_posix()
        digest = package_index.get(relative)
        if digest is None:
            raise ContractError(f"{acceptance_path}: {relative} no està ancorat")
        expected[role] = digest
    return GroupInput(
        name=name,
        exposure_s=exposure,
        min_rsun=min_rsun,
        directory=directory,
        acceptance_receipt=acceptance_path,
        acceptance=receipt,
        members=tuple(members),
        paths=paths,
        expected_hashes=expected,
    )


def validate_inputs(
    sony_root: Path, vixen_hdr: Path, research80: Path, script_path: Path
) -> tuple[list[GroupInput], dict[str, Any]]:
    sony_root = sony_root.expanduser().resolve()
    if not sony_root.is_dir() or sony_root.name != "sony_s6_ACCEPTED":
        raise ContractError("--sony-root ha d'apuntar literalment a sony_s6_ACCEPTED")
    catalogue_path = require_file(sony_root / "CATALOG_RECEIPT.json", "catàleg Sony ACCEPTED")
    catalogue = json_object(catalogue_path)
    if (
        catalogue.get("delivery_class") != "MIXED_AUDITED_CATALOGUE"
        or catalogue.get("camera_train") != "SONY_A7RIIIA_FE300MM_F2.8_GM"
        or catalogue.get("frame") != "CORONA_SOLAR"
        or catalogue.get("product_counts", {}).get("accepted_repeated_C_stacks") != 3
    ):
        raise ContractError(f"{catalogue_path}: catàleg Sony ACCEPTED invàlid")
    if catalogue.get("eight_second_policy", {}).get("verdict") != "QUARANTENA":
        raise ContractError("el catàleg no conserva literalment els 8 s en QUARANTENA")
    products = catalogue.get("products")
    accepted_ids = {
        row.get("product_id")
        for row in products
        if isinstance(row, dict) and row.get("verdict") == ACCEPTED
    } if isinstance(products, list) else set()
    if accepted_ids != {"segment_C_1-30s", "segment_C_1-4s", "segment_C_2s"}:
        raise ContractError(f"conjunt de stacks Sony acceptats inesperat: {accepted_ids}")
    groups = [validate_group(sony_root, *spec) for spec in GROUPS]

    vixen_hdr = require_file(vixen_hdr, "HDR Vixen acceptat")
    composite_receipt_path = require_file(vixen_hdr.parent / "COMPOSITE_RECEIPT.json", "rebut HDR Vixen")
    composite = json_object(composite_receipt_path)
    if composite.get("schema") != "ECLIPSE_NATURAL_COMPOSITE_RECEIPT_V1" or composite.get("verdict") != ACCEPTED:
        raise ContractError(f"{composite_receipt_path}: HDR Vixen no ACCEPTAT")
    geometry = composite.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("shape_yxc") != list(VIXEN_SHAPE):
        raise ContractError("geometria Vixen inesperada")
    center = geometry.get("solar_center_xy_px")
    radius = geometry.get("solar_radius_px")
    if (
        not isinstance(center, list)
        or len(center) != 2
        or max(abs(float(center[i]) - VIXEN_CENTER_XY[i]) for i in range(2)) > 1e-6
        or not isinstance(radius, (int, float))
        or abs(float(radius) - VIXEN_RADIUS_PX) > 1e-6
        or geometry.get("historical_959_arcsec_radius_used") is not False
    ):
        raise ContractError("centre/radi Vixen no coincideix amb DE440+IAU corregit")
    vixen_output = None
    for row in composite.get("outputs", []):
        if isinstance(row, dict) and row.get("name") == vixen_hdr.name:
            vixen_output = row
            break
    if not isinstance(vixen_output, dict):
        raise ContractError("el TIFF HDR Vixen no està ancorat al rebut")

    research80 = require_file(research80, "research/80")
    text = research80.read_text(encoding="utf-8")
    # ``7 estrelles`` and ``comunes`` are split by a Markdown newline in the
    # authority document; the numeric literals remain exact.
    literals = ("1,48860", "33,088°", "rms 0,52 px", "7 estrelles", "comunes**")
    if not all(literal in text for literal in literals):
        raise ContractError("research/80 no conserva els literals de la similitud de 7 estrelles")
    rotation_delta = abs(SOURCE_TO_DEST_ROTATION_DEG - RESEARCH80_STAR_ROTATION_DEG)
    scale_rel_delta = abs(SOURCE_TO_DEST_SCALE / RESEARCH80_STAR_SCALE - 1.0)
    if rotation_delta > 0.02 or scale_rel_delta > 0.002:
        raise ContractError("la solució de placa divergeix de l'ajust independent de 7 estrelles")

    log("Preflight SHA-256: es rehashen només les entrades consumides...")
    hash_rows: list[dict[str, Any]] = []
    for group in groups:
        for role, path in group.paths.items():
            actual = sha256(path)
            expected = group.expected_hashes[role]
            if actual != expected:
                raise ContractError(f"SHA-256 divergent {group.name}/{role}: {path}")
            hash_rows.append(
                {"group": group.name, "role": role, "path": str(path), "bytes": path.stat().st_size, "sha256": actual}
            )
    vixen_hash = sha256(vixen_hdr)
    if vixen_hash != vixen_output.get("sha256") or vixen_hdr.stat().st_size != vixen_output.get("bytes"):
        raise ContractError("bytes/hash del Vixen HDR divergeixen del rebut")
    catalogue_hash = sha256(catalogue_path)
    composite_receipt_hash = sha256(composite_receipt_path)
    evidence = {
        "sony_catalogue": {
            "path": str(catalogue_path),
            "bytes": catalogue_path.stat().st_size,
            "sha256": catalogue_hash,
        },
        "consumed_sony_files": hash_rows,
        "vixen_hdr": {"path": str(vixen_hdr), "bytes": vixen_hdr.stat().st_size, "sha256": vixen_hash},
        "vixen_composite_receipt": {
            "path": str(composite_receipt_path),
            "bytes": composite_receipt_path.stat().st_size,
            "sha256": composite_receipt_hash,
        },
        "research80": {"path": str(research80), "bytes": research80.stat().st_size, "sha256": sha256(research80)},
        "software": {"path": str(script_path), "bytes": script_path.stat().st_size, "sha256": sha256(script_path)},
        "seven_star_sign_validation": {
            "research80_source_to_destination_rotation_deg": RESEARCH80_STAR_ROTATION_DEG,
            "requested_source_to_destination_rotation_deg": SOURCE_TO_DEST_ROTATION_DEG,
            "absolute_rotation_difference_deg": rotation_delta,
            "research80_scale": RESEARCH80_STAR_SCALE,
            "plate_scale_ratio": SOURCE_TO_DEST_SCALE,
            "relative_scale_difference": scale_rel_delta,
            "research80_rms_px": RESEARCH80_STAR_RMS_PX,
            "sign": "POSITIVE_SOURCE_TO_DESTINATION_IN_Y_DOWN_COORDINATES",
            "status": "PASS",
        },
    }
    return groups, evidence


def robust_fit(
    source: np.ndarray,
    target: np.ndarray,
    xnorm: np.ndarray,
    ynorm: np.ndarray,
    variance: np.ndarray,
    label: str,
    max_samples: int = 500_000,
) -> RobustFit:
    source = np.asarray(source, np.float64).ravel()
    target = np.asarray(target, np.float64).ravel()
    xnorm = np.asarray(xnorm, np.float64).ravel()
    ynorm = np.asarray(ynorm, np.float64).ravel()
    variance = np.asarray(variance, np.float64).ravel()
    finite = (
        np.isfinite(source)
        & np.isfinite(target)
        & np.isfinite(xnorm)
        & np.isfinite(ynorm)
        & np.isfinite(variance)
        & (variance > 0)
    )
    source, target, xnorm, ynorm, variance = (
        value[finite] for value in (source, target, xnorm, ynorm, variance)
    )
    if source.size < 10_000:
        raise ContractError(f"{label}: mostres insuficients ({source.size})")
    if source.size > max_samples:
        take = np.linspace(0, source.size - 1, max_samples, dtype=np.int64)
        source, target, xnorm, ynorm, variance = (
            value[take] for value in (source, target, xnorm, ynorm, variance)
        )
    smed = float(np.median(source))
    sscale = float(1.4826 * np.median(np.abs(source - smed)))
    if not math.isfinite(sscale) or sscale <= max(abs(smed), 1.0) * 1e-6:
        sscale = float(np.std(source))
    if not math.isfinite(sscale) or sscale <= 0:
        raise ContractError(f"{label}: escala de font degenerada")
    z = (source - smed) / sscale
    design = np.column_stack((z, np.ones_like(z), xnorm, ynorm))
    invvar = 1.0 / variance
    lo, hi = np.percentile(invvar, (2.0, 98.0))
    base_weight = np.clip(invvar, max(lo, np.finfo(float).tiny), max(hi, lo * 1.001))
    base_weight /= np.median(base_weight)
    robust_weight = np.ones_like(base_weight)
    beta = np.zeros(4, np.float64)
    scale = float("nan")
    residual = np.zeros_like(target)
    keep = np.ones_like(target, bool)
    iterations = 0
    for iteration in range(12):
        iterations = iteration + 1
        weight = base_weight * robust_weight
        rootw = np.sqrt(weight)
        aw = design * rootw[:, None]
        yw = target * rootw
        beta_new, *_ = np.linalg.lstsq(aw, yw, rcond=None)
        residual = target - design @ beta_new
        med = float(np.median(residual))
        scale = float(1.4826 * np.median(np.abs(residual - med)))
        if not math.isfinite(scale) or scale <= 1e-12:
            raise ContractError(f"{label}: residu robust degenerat")
        u = np.abs(residual - med) / (1.345 * scale)
        robust_new = np.ones_like(u)
        far = u > 1.0
        robust_new[far] = 1.0 / u[far]
        keep = np.abs(residual - med) <= 4.5 * scale
        robust_new[~keep] = 0.0
        if np.allclose(beta, beta_new, rtol=2e-7, atol=2e-7) and np.max(
            np.abs(robust_new - robust_weight)
        ) < 1e-3:
            beta = beta_new
            robust_weight = robust_new
            break
        beta = beta_new
        robust_weight = robust_new
    weight = base_weight * robust_weight
    normal = design.T @ (weight[:, None] * design)
    if np.linalg.cond(normal) > 1e12:
        raise ContractError(f"{label}: model mal condicionat")
    dof = max(int(np.count_nonzero(weight)) - 4, 1)
    sigma2 = float(np.sum(weight * residual**2) / dof)
    covariance_scaled = np.linalg.inv(normal) * sigma2
    gain = float(beta[0] / sscale)
    intercept = float(beta[1] - gain * smed)
    coefficients = np.array((gain, intercept, beta[2], beta[3]), np.float64)
    transform = np.array(
        [
            [1.0 / sscale, 0.0, 0.0, 0.0],
            [-smed / sscale, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        np.float64,
    )
    covariance_original = transform @ covariance_scaled @ transform.T
    if not math.isfinite(gain) or gain <= 0 or not (0.1 <= gain <= 10.0):
        raise ContractError(f"{label}: guany físicament implausible {gain}")
    return RobustFit(
        beta_scaled=beta,
        covariance_scaled=covariance_scaled,
        source_median=smed,
        source_scale=sscale,
        gain=gain,
        intercept=intercept,
        coefficients_original=coefficients,
        covariance_original=covariance_original,
        sample_count=int(source.size),
        inlier_count=int(np.count_nonzero(keep)),
        robust_sigma=scale,
        median_residual=float(np.median(residual)),
        p95_abs_residual=float(np.percentile(np.abs(residual), 95)),
        iterations=iterations,
    )


def identity_fit() -> RobustFit:
    return RobustFit(
        beta_scaled=np.array((1.0, 0.0, 0.0, 0.0)),
        covariance_scaled=np.zeros((4, 4)),
        source_median=0.0,
        source_scale=1.0,
        gain=1.0,
        intercept=0.0,
        coefficients_original=np.array((1.0, 0.0, 0.0, 0.0)),
        covariance_original=np.zeros((4, 4)),
        sample_count=0,
        inlier_count=0,
        robust_sigma=0.0,
        median_residual=0.0,
        p95_abs_residual=0.0,
        iterations=0,
    )


def load_group_arrays(groups: list[GroupInput]) -> None:
    for group in groups:
        log(f"Carregant {group.name} ({group.members[0]} + {group.members[1]})...")
        group.image = tifffile.imread(group.paths["master"])
        if group.image.shape != SONY_SHAPE or group.image.dtype != np.float32:
            raise ContractError(f"{group.paths['master']}: shape/dtype inesperat")
        group.random_variance = np.load(group.paths["variance_random"], mmap_mode="r")
        group.systematic_variance = np.load(group.paths["variance_systematic"], mmap_mode="r")
        group.coverage = np.load(group.paths["coverage"], mmap_mode="r")
        group.saturation = np.load(group.paths["saturation"], mmap_mode="r")
        group.mask = np.load(group.paths["valid_mask"], mmap_mode="r")
        if (
            group.random_variance.shape != SONY_SHAPE
            or group.systematic_variance.shape != SONY_SHAPE
            or group.coverage.shape != SONY_SHAPE
            or group.saturation.shape != SONY_SHAPE[:2]
            or group.mask.shape != SONY_SHAPE[:2]
        ):
            raise ContractError(f"{group.name}: productes amb shapes incompatibles")


def group_valid(group: GroupInput, rows: slice, channel: int) -> np.ndarray:
    assert group.image is not None
    assert group.random_variance is not None
    assert group.systematic_variance is not None
    assert group.coverage is not None
    assert group.saturation is not None
    assert group.mask is not None
    return (
        np.asarray(group.mask[rows], bool)
        & (np.asarray(group.coverage[rows, :, channel]) > 0)
        & (np.asarray(group.saturation[rows]) < len(group.members))
        & np.isfinite(group.image[rows, :, channel])
        & np.isfinite(group.random_variance[rows, :, channel])
        & (np.asarray(group.random_variance[rows, :, channel]) > 0)
        & np.isfinite(group.systematic_variance[rows, :, channel])
        & (np.asarray(group.systematic_variance[rows, :, channel]) >= 0)
    )


def fit_internal_groups(groups: list[GroupInput], stride: int = 12) -> dict[str, list[RobustFit]]:
    by_name = {group.name: group for group in groups}
    anchor = by_name[ANCHOR_GROUP]
    assert anchor.image is not None
    yy, xx = np.mgrid[0:SONY_SHAPE[0]:stride, 0:SONY_SHAPE[1]:stride]
    rho = np.hypot(xx - SONY_CENTER_XY[0], yy - SONY_CENTER_XY[1]) / SONY_RADIUS_PX
    xnorm = (xx - SONY_CENTER_XY[0]) / (SONY_SHAPE[1] / 2.0)
    ynorm = (yy - SONY_CENTER_XY[1]) / (SONY_SHAPE[0] / 2.0)
    radial = (rho >= 2.2) & (rho <= 5.0)
    fits: dict[str, list[RobustFit]] = {}
    for group in groups:
        if group.name == ANCHOR_GROUP:
            fits[group.name] = [identity_fit(), identity_fit(), identity_fit()]
            continue
        channel_fits: list[RobustFit] = []
        for channel in range(3):
            gv = group_valid(group, slice(0, SONY_SHAPE[0], stride), channel)
            av = group_valid(anchor, slice(0, SONY_SHAPE[0], stride), channel)
            valid = radial & gv[:, ::stride] & av[:, ::stride]
            assert group.image is not None and group.random_variance is not None
            assert anchor.random_variance is not None
            source = group.image[::stride, ::stride, channel][valid]
            target = anchor.image[::stride, ::stride, channel][valid]
            variance = (
                group.random_variance[::stride, ::stride, channel][valid]
                + anchor.random_variance[::stride, ::stride, channel][valid]
            )
            fit = robust_fit(
                source,
                target,
                xnorm[valid],
                ynorm[valid],
                variance,
                f"normalització interna {group.name}/{CHANNELS[channel]}",
            )
            log(
                f"  {group.name}/{CHANNELS[channel]} -> {ANCHOR_GROUP}: "
                f"g={fit.gain:.6f}, sigma={fit.robust_sigma:.3f} ADU/s"
            )
            channel_fits.append(fit)
        fits[group.name] = channel_fits
    return fits


def create_native_hdr(
    groups: list[GroupInput], fits: dict[str, list[RobustFit]], staging: Path, chunk_rows: int
) -> dict[str, Path]:
    paths = {
        "image": staging / "SONY_C_HDR_RGB_DERIVATIVE_LINEAR_ADU_S.npy",
        "variance_random": staging / "SONY_C_HDR_VARIANCE_RANDOM_ADU2_S2.npy",
        "variance_systematic": staging / "SONY_C_HDR_VARIANCE_SYSTEMATIC_ADU2_S2.npy",
        "variance_total": staging / "SONY_C_HDR_VARIANCE_TOTAL_ADU2_S2.npy",
        "support": staging / "SONY_C_HDR_SUPPORT_ALL_CHANNELS_UINT8.npy",
        "contributors": staging / "SONY_C_HDR_CONTRIBUTORS_UINT8.npy",
    }
    image_out = open_memmap(paths["image"], mode="w+", dtype=np.float32, shape=SONY_SHAPE)
    vr_out = open_memmap(paths["variance_random"], mode="w+", dtype=np.float32, shape=SONY_SHAPE)
    vs_out = open_memmap(paths["variance_systematic"], mode="w+", dtype=np.float32, shape=SONY_SHAPE)
    vt_out = open_memmap(paths["variance_total"], mode="w+", dtype=np.float32, shape=SONY_SHAPE)
    support_out = open_memmap(paths["support"], mode="w+", dtype=np.uint8, shape=SONY_SHAPE[:2])
    contributors_out = open_memmap(paths["contributors"], mode="w+", dtype=np.uint8, shape=SONY_SHAPE)

    xfull = (np.arange(SONY_SHAPE[1], dtype=np.float32) - SONY_CENTER_XY[0]) / (SONY_SHAPE[1] / 2.0)
    for y0 in range(0, SONY_SHAPE[0], chunk_rows):
        y1 = min(y0 + chunk_rows, SONY_SHAPE[0])
        rows = slice(y0, y1)
        ynorm = (
            np.arange(y0, y1, dtype=np.float32)[:, None] - SONY_CENTER_XY[1]
        ) / (SONY_SHAPE[0] / 2.0)
        xnorm = np.broadcast_to(xfull[None, :], (y1 - y0, SONY_SHAPE[1]))
        ynorm2 = np.broadcast_to(ynorm, (y1 - y0, SONY_SHAPE[1]))
        common = np.ones((y1 - y0, SONY_SHAPE[1]), bool)
        for channel in range(3):
            numerator = np.zeros((y1 - y0, SONY_SHAPE[1]), np.float64)
            denominator = np.zeros_like(numerator)
            systematic_amplitude_numerator = np.zeros_like(numerator)
            contributor_count = np.zeros(numerator.shape, np.uint8)
            for group in groups:
                assert group.image is not None
                assert group.random_variance is not None
                assert group.systematic_variance is not None
                fit = fits[group.name][channel]
                source = np.asarray(group.image[rows, :, channel], np.float64)
                matched = fit.apply(source, xnorm, ynorm2)
                model_variance = fit.model_variance(source, xnorm, ynorm2)
                random_variance = fit.gain**2 * np.asarray(
                    group.random_variance[rows, :, channel], np.float64
                )
                systematic_variance = fit.gain**2 * np.asarray(
                    group.systematic_variance[rows, :, channel], np.float64
                ) + model_variance
                valid = group_valid(group, rows, channel)
                weight = np.zeros_like(random_variance)
                weight[valid] = 1.0 / random_variance[valid]
                numerator += weight * np.where(valid, matched, 0.0)
                denominator += weight
                systematic_amplitude_numerator += weight * np.where(
                    valid, np.sqrt(np.maximum(systematic_variance, 0.0)), 0.0
                )
                contributor_count += valid.astype(np.uint8)
            valid_out = denominator > 0
            hdr = np.full(denominator.shape, np.nan, np.float32)
            vr = np.full(denominator.shape, np.inf, np.float32)
            vs = np.full(denominator.shape, np.inf, np.float32)
            hdr[valid_out] = (numerator[valid_out] / denominator[valid_out]).astype(np.float32)
            vr[valid_out] = (1.0 / denominator[valid_out]).astype(np.float32)
            # The donor-flat term is shared.  A weighted sum of standard
            # deviations is a conservative full-positive-correlation model.
            vs[valid_out] = (
                systematic_amplitude_numerator[valid_out] / denominator[valid_out]
            ).astype(np.float32) ** 2
            image_out[rows, :, channel] = hdr
            vr_out[rows, :, channel] = vr
            vs_out[rows, :, channel] = vs
            vt_out[rows, :, channel] = vr + vs
            contributors_out[rows, :, channel] = contributor_count
            common &= valid_out
        support_out[rows] = common.astype(np.uint8)
        if y0 % (chunk_rows * 8) == 0:
            log(f"  HDR Sony natiu: files {y0}:{y1}")
    for array in (image_out, vr_out, vs_out, vt_out, support_out, contributors_out):
        array.flush()
    del image_out, vr_out, vs_out, vt_out, support_out, contributors_out
    tifffile.imwrite(
        staging / "SONY_C_HDR_RGB_DERIVATIVE_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        np.load(paths["image"], mmap_mode="r"),
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="rgb",
        metadata=None,
        description="Linear Sony segment-C HDR visual RGB derivative; units ADU/s; CFA4 remains authority",
    )
    tifffile.imwrite(
        staging / "SONY_C_HDR_VARIANCE_TOTAL_ADU2_S2_FLOAT32_BIGTIFF.tif",
        np.load(paths["variance_total"], mmap_mode="r"),
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="rgb",
        metadata=None,
        description="Total variance of Sony RGB derivative; units ADU^2/s^2",
    )
    return paths


def mapping_coordinates(
    y0: int, y1: int, rotation_deg: float = SOURCE_TO_DEST_ROTATION_DEG
) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[y0:y1, 0:VIXEN_SHAPE[1]].astype(np.float64)
    ux = (xx - VIXEN_CENTER_XY[0]) / SOURCE_TO_DEST_SCALE
    uy = (yy - VIXEN_CENTER_XY[1]) / SOURCE_TO_DEST_SCALE
    theta = math.radians(rotation_deg)
    c, s = math.cos(theta), math.sin(theta)
    # research/80 convention, y increasing downward.  The inverse map of the
    # positive source->destination rotation is R(-theta) in this convention.
    source_x = SONY_CENTER_XY[0] + ux * c - uy * s
    source_y = SONY_CENTER_XY[1] + ux * s + uy * c
    return source_y, source_x


def bilinear_geometry(
    source_y: np.ndarray, source_x: np.ndarray, support: np.ndarray
) -> tuple[np.ndarray, ...]:
    y0 = np.floor(source_y).astype(np.int32)
    x0 = np.floor(source_x).astype(np.int32)
    valid_bounds = (
        (x0 >= 0)
        & (y0 >= 0)
        & (x0 + 1 < SONY_SHAPE[1])
        & (y0 + 1 < SONY_SHAPE[0])
    )
    yc = np.clip(y0, 0, SONY_SHAPE[0] - 2)
    xc = np.clip(x0, 0, SONY_SHAPE[1] - 2)
    fx = source_x - x0
    fy = source_y - y0
    w00 = (1.0 - fx) * (1.0 - fy)
    w01 = fx * (1.0 - fy)
    w10 = (1.0 - fx) * fy
    w11 = fx * fy
    valid = (
        valid_bounds
        & (support[yc, xc] > 0)
        & (support[yc, xc + 1] > 0)
        & (support[yc + 1, xc] > 0)
        & (support[yc + 1, xc + 1] > 0)
    )
    return yc, xc, w00, w01, w10, w11, valid


def bilinear_value(
    array: np.ndarray,
    channel: int,
    yc: np.ndarray,
    xc: np.ndarray,
    weights: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    w00, w01, w10, w11 = weights
    return (
        w00 * array[yc, xc, channel]
        + w01 * array[yc, xc + 1, channel]
        + w10 * array[yc + 1, xc, channel]
        + w11 * array[yc + 1, xc + 1, channel]
    )


def bilinear_random_variance(
    array: np.ndarray,
    channel: int,
    yc: np.ndarray,
    xc: np.ndarray,
    weights: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    w00, w01, w10, w11 = weights
    return (
        w00**2 * array[yc, xc, channel]
        + w01**2 * array[yc, xc + 1, channel]
        + w10**2 * array[yc + 1, xc, channel]
        + w11**2 * array[yc + 1, xc + 1, channel]
    )


def bilinear_correlated_variance(
    array: np.ndarray,
    channel: int,
    yc: np.ndarray,
    xc: np.ndarray,
    weights: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    w00, w01, w10, w11 = weights
    amplitude = (
        w00 * np.sqrt(np.maximum(array[yc, xc, channel], 0.0))
        + w01 * np.sqrt(np.maximum(array[yc, xc + 1, channel], 0.0))
        + w10 * np.sqrt(np.maximum(array[yc + 1, xc, channel], 0.0))
        + w11 * np.sqrt(np.maximum(array[yc + 1, xc + 1, channel], 0.0))
    )
    return amplitude**2


def validate_rotation_with_data(
    sony_image: np.ndarray,
    sony_support: np.ndarray,
    vixen: np.ndarray,
    stride: int = 4,
) -> dict[str, Any]:
    correlations: dict[str, float] = {}
    v = vixen[::stride, ::stride, 1].astype(np.float64)
    yy, xx = np.mgrid[0:VIXEN_SHAPE[0]:stride, 0:VIXEN_SHAPE[1]:stride]
    rho = np.hypot(xx - VIXEN_CENTER_XY[0], yy - VIXEN_CENTER_XY[1]) / VIXEN_RADIUS_PX
    def masked_log_highpass(value: np.ndarray, mask: np.ndarray) -> np.ndarray:
        log_value = np.zeros(value.shape, np.float64)
        log_value[mask] = np.log(np.clip(value[mask], 1e-3, None))
        numerator = ndi.gaussian_filter(log_value * mask, 6.0, mode="constant", cval=0.0)
        denominator = ndi.gaussian_filter(mask.astype(np.float64), 6.0, mode="constant", cval=0.0)
        smooth = np.zeros_like(log_value)
        np.divide(numerator, denominator, out=smooth, where=denominator > 0.2)
        highpass = log_value - smooth
        highpass[~mask] = 0.0
        return highpass

    vmask = np.isfinite(v) & (v > 0)
    vh = masked_log_highpass(v, vmask)
    for label, angle in (("positive", SOURCE_TO_DEST_ROTATION_DEG), ("negative", -SOURCE_TO_DEST_ROTATION_DEG)):
        sy, sx = mapping_coordinates(0, VIXEN_SHAPE[0], angle)
        sy = sy[::stride, ::stride]
        sx = sx[::stride, ::stride]
        sw = ndi.map_coordinates(
            sony_image[..., 1], [sy, sx], order=1, mode="constant", cval=np.nan, prefilter=False
        )
        sm = ndi.map_coordinates(
            sony_support.astype(np.float32), [sy, sx], order=0, mode="constant", cval=0.0, prefilter=False
        ) > 0.5
        sm &= np.isfinite(sw) & (sw > 0)
        sh = masked_log_highpass(sw, sm)
        valid = (
            (rho >= 1.8)
            & (rho <= 3.4)
            & sm
            & vmask
        )
        if np.count_nonzero(valid) < 20_000:
            raise ContractError("mostres insuficients per validar el signe amb la corona")
        correlation = float(np.corrcoef(vh[valid], sh[valid])[0, 1])
        if not math.isfinite(correlation):
            raise ContractError(f"correlació no finita per validar el signe {label}")
        correlations[label] = correlation
    preferred = correlations["positive"] > correlations["negative"] + 0.05
    return {
        "method": "log high-pass coronal cross-correlation, 1.8-3.4 Rsun, stride 4",
        "positive_rotation_correlation": correlations["positive"],
        "negative_rotation_correlation": correlations["negative"],
        "positive_minus_negative": correlations["positive"] - correlations["negative"],
        "data_prefers_positive_sign": bool(preferred),
        "status": "PASS" if preferred else "AMBIGUOUS_DATA_STAR_SOLUTION_REMAINS_AUTHORITY",
    }


def warp_to_vixen(native: dict[str, Path], staging: Path, chunk_rows: int) -> dict[str, Path]:
    source_image = np.load(native["image"], mmap_mode="r")
    source_vr = np.load(native["variance_random"], mmap_mode="r")
    source_vs = np.load(native["variance_systematic"], mmap_mode="r")
    source_support = np.load(native["support"], mmap_mode="r")
    paths = {
        "image": staging / "SONY_C_HDR_WARPED_TO_VIXEN_LINEAR_ADU_S.npy",
        "variance_random": staging / "SONY_C_HDR_WARPED_VARIANCE_RANDOM_ADU2_S2.npy",
        "variance_systematic": staging / "SONY_C_HDR_WARPED_VARIANCE_SYSTEMATIC_ADU2_S2.npy",
        "variance_total": staging / "SONY_C_HDR_WARPED_VARIANCE_TOTAL_ADU2_S2.npy",
        "support": staging / "SONY_C_HDR_WARPED_SUPPORT_UINT8.npy",
    }
    image_out = open_memmap(paths["image"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vr_out = open_memmap(paths["variance_random"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vs_out = open_memmap(paths["variance_systematic"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vt_out = open_memmap(paths["variance_total"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    support_out = open_memmap(paths["support"], mode="w+", dtype=np.uint8, shape=VIXEN_SHAPE[:2])
    for y0 in range(0, VIXEN_SHAPE[0], chunk_rows):
        y1 = min(y0 + chunk_rows, VIXEN_SHAPE[0])
        sy, sx = mapping_coordinates(y0, y1)
        yc, xc, w00, w01, w10, w11, valid = bilinear_geometry(sy, sx, source_support)
        weights = (w00, w01, w10, w11)
        support_out[y0:y1] = valid.astype(np.uint8)
        for channel in range(3):
            image = bilinear_value(source_image, channel, yc, xc, weights)
            vr = bilinear_random_variance(source_vr, channel, yc, xc, weights)
            vs = bilinear_correlated_variance(source_vs, channel, yc, xc, weights)
            image_out[y0:y1, :, channel] = np.where(valid, image, np.nan).astype(np.float32)
            vr_out[y0:y1, :, channel] = np.where(valid, vr, np.inf).astype(np.float32)
            vs_out[y0:y1, :, channel] = np.where(valid, vs, np.inf).astype(np.float32)
            vt_out[y0:y1, :, channel] = np.where(valid, vr + vs, np.inf).astype(np.float32)
        if y0 % (chunk_rows * 8) == 0:
            log(f"  Warp Sony->Vixen: files {y0}:{y1}")
    for array in (image_out, vr_out, vs_out, vt_out, support_out):
        array.flush()
    del image_out, vr_out, vs_out, vt_out, support_out
    tifffile.imwrite(
        staging / "SONY_C_HDR_WARPED_TO_VIXEN_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        np.load(paths["image"], mmap_mode="r"),
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="rgb",
        metadata=None,
        description="Sony segment-C HDR RGB derivative resampled to the Vixen solar frame; units ADU/s",
    )
    return paths


def fit_cross_train(
    warped: dict[str, Path], vixen: np.ndarray, stride: int = 8
) -> list[RobustFit]:
    sony = np.load(warped["image"], mmap_mode="r")
    variance = np.load(warped["variance_total"], mmap_mode="r")
    support = np.load(warped["support"], mmap_mode="r")
    yy, xx = np.mgrid[0:VIXEN_SHAPE[0]:stride, 0:VIXEN_SHAPE[1]:stride]
    rho = np.hypot(xx - VIXEN_CENTER_XY[0], yy - VIXEN_CENTER_XY[1]) / VIXEN_RADIUS_PX
    xnorm = (xx - VIXEN_CENTER_XY[0]) / (VIXEN_SHAPE[1] / 2.0)
    ynorm = (yy - VIXEN_CENTER_XY[1]) / (VIXEN_SHAPE[0] / 2.0)
    domain = (rho >= 2.2) & (rho <= 5.0) & (support[::stride, ::stride] > 0)
    fits: list[RobustFit] = []
    for channel in range(3):
        s = sony[::stride, ::stride, channel]
        t = vixen[::stride, ::stride, channel]
        var = variance[::stride, ::stride, channel]
        valid = domain & np.isfinite(s) & np.isfinite(t) & np.isfinite(var) & (var > 0)
        fit = robust_fit(
            s[valid],
            t[valid],
            xnorm[valid],
            ynorm[valid],
            var[valid],
            f"aparellament Sony->Vixen/{CHANNELS[channel]}",
        )
        log(
            f"  Sony->Vixen/{CHANNELS[channel]}: g={fit.gain:.6f}, "
            f"sigma={fit.robust_sigma:.3f} ADU/s"
        )
        fits.append(fit)
    return fits


def materialize_matched_layer(
    warped: dict[str, Path], fits: list[RobustFit], staging: Path, chunk_rows: int
) -> dict[str, Path]:
    source = np.load(warped["image"], mmap_mode="r")
    source_vr = np.load(warped["variance_random"], mmap_mode="r")
    source_vs = np.load(warped["variance_systematic"], mmap_mode="r")
    support = np.load(warped["support"], mmap_mode="r")
    paths = {
        "image": staging / "SONY_MATCHED_TO_VIXEN_LINEAR_ADU_S.npy",
        "variance_random": staging / "SONY_MATCHED_VARIANCE_RANDOM_ADU2_S2.npy",
        "variance_systematic": staging / "SONY_MATCHED_VARIANCE_SYSTEMATIC_ADU2_S2.npy",
        "variance_total": staging / "SONY_MATCHED_VARIANCE_TOTAL_ADU2_S2.npy",
    }
    image_out = open_memmap(paths["image"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vr_out = open_memmap(paths["variance_random"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vs_out = open_memmap(paths["variance_systematic"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    vt_out = open_memmap(paths["variance_total"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    xfull = (np.arange(VIXEN_SHAPE[1], dtype=np.float32) - VIXEN_CENTER_XY[0]) / (VIXEN_SHAPE[1] / 2.0)
    for y0 in range(0, VIXEN_SHAPE[0], chunk_rows):
        y1 = min(y0 + chunk_rows, VIXEN_SHAPE[0])
        yn = (
            np.arange(y0, y1, dtype=np.float32)[:, None] - VIXEN_CENTER_XY[1]
        ) / (VIXEN_SHAPE[0] / 2.0)
        xn = np.broadcast_to(xfull[None, :], (y1 - y0, VIXEN_SHAPE[1]))
        yn = np.broadcast_to(yn, xn.shape)
        valid = support[y0:y1] > 0
        for channel, fit in enumerate(fits):
            s = np.asarray(source[y0:y1, :, channel], np.float64)
            image = fit.apply(s, xn, yn)
            vr = fit.gain**2 * np.asarray(source_vr[y0:y1, :, channel], np.float64)
            vs = fit.gain**2 * np.asarray(
                source_vs[y0:y1, :, channel], np.float64
            ) + fit.model_variance(s, xn, yn)
            image_out[y0:y1, :, channel] = np.where(valid, image, np.nan).astype(np.float32)
            vr_out[y0:y1, :, channel] = np.where(valid, vr, np.inf).astype(np.float32)
            vs_out[y0:y1, :, channel] = np.where(valid, vs, np.inf).astype(np.float32)
            vt_out[y0:y1, :, channel] = np.where(valid, vr + vs, np.inf).astype(np.float32)
    for array in (image_out, vr_out, vs_out, vt_out):
        array.flush()
    del image_out, vr_out, vs_out, vt_out
    tifffile.imwrite(
        staging / "SONY_MATCHED_TO_VIXEN_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        np.load(paths["image"], mmap_mode="r"),
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="rgb",
        metadata=None,
        description="Sony visual RGB derivative robustly matched to the accepted Vixen HDR; units ADU/s",
    )
    return paths


def smoothstep01(value: np.ndarray) -> np.ndarray:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def sector_ring_qa(
    alpha: np.ndarray,
    sony: np.ndarray,
    vixen: np.ndarray,
    stride: int = 4,
) -> dict[str, Any]:
    a = alpha[::stride, ::stride].astype(np.float64)
    s = sony[::stride, ::stride].astype(np.float64)
    v = vixen[::stride, ::stride].astype(np.float64)
    yy, xx = np.mgrid[0:VIXEN_SHAPE[0]:stride, 0:VIXEN_SHAPE[1]:stride]
    dx = xx - VIXEN_CENTER_XY[0]
    dy = yy - VIXEN_CENTER_XY[1]
    rho = np.hypot(dx, dy) / VIXEN_RADIUS_PX
    theta = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0
    lv = np.einsum("...c,c->...", v, LUMA)
    ls = np.einsum("...c,c->...", s, LUMA)
    # A zero alpha means the candidate is exactly Vixen even where the Sony
    # source has no support (notably 1.15--1.2 Rsun).  Treat that as a measured
    # zero contribution rather than dropping those QA cells.
    sony_or_zero = np.isfinite(ls) | (a == 0.0)
    valid_domain = (
        (rho >= 1.15)
        & (rho <= 5.0)
        & np.isfinite(lv)
        & sony_or_zero
        & np.isfinite(a)
    )
    floor = float(np.percentile(np.abs(lv[valid_domain]), 5))
    floor = max(floor, 1e-3)
    ls_safe = np.where(np.isfinite(ls), ls, lv)
    relative_delta = a * (ls_safe - lv) / np.maximum(np.abs(lv), floor)
    radial_edges = np.arange(1.15, 5.0001, 0.025)
    sector_edges = np.arange(0.0, 360.0001, 15.0)
    nsector = len(sector_edges) - 1
    nradial = len(radial_edges) - 1
    profiles = np.full((nsector, nradial), np.nan)
    counts = np.zeros(profiles.shape, np.int32)
    si = np.floor(theta[valid_domain] / 15.0).astype(np.int16)
    ri = np.floor((rho[valid_domain] - 1.15) / 0.025).astype(np.int16)
    values = relative_delta[valid_domain]
    in_grid = (si >= 0) & (si < nsector) & (ri >= 0) & (ri < nradial)
    group_id = (si[in_grid].astype(np.int32) * nradial + ri[in_grid]).astype(np.int32)
    values = values[in_grid]
    order = np.argsort(group_id, kind="stable")
    group_id = group_id[order]
    values = values[order]
    boundaries = np.r_[0, np.flatnonzero(np.diff(group_id)) + 1, len(group_id)]
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        group = int(group_id[start])
        sector_index, radial_index = divmod(group, nradial)
        count = int(end - start)
        counts[sector_index, radial_index] = count
        if count >= 20:
            profiles[sector_index, radial_index] = float(np.median(values[start:end]))
    annular = np.nanmedian(profiles, axis=0)
    annular_diff = np.abs(np.diff(annular))
    annular_curvature = np.abs(np.diff(annular, n=2))
    sector_steps = np.abs(np.diff(profiles, axis=1))
    finite_steps = sector_steps[np.isfinite(sector_steps)]
    # Compare each sector with its eight neighbours as in the project's
    # sector gate, but on the *new contribution* rather than real corona.
    neighbour_deviation: list[float] = []
    for si in range(profiles.shape[0]):
        neighbours = [(si + d) % profiles.shape[0] for d in (-4, -3, -2, -1, 1, 2, 3, 4)]
        reference = np.nanmedian(profiles[neighbours], axis=0)
        diff = np.abs(profiles[si] - reference)
        neighbour_deviation.extend(diff[np.isfinite(diff)].tolist())
    neighbour_array = np.asarray(neighbour_deviation, np.float64)
    metrics = {
        "radial_bin_rsun": 0.025,
        "sector_width_deg": 15.0,
        "valid_cell_fraction": float(np.isfinite(profiles).mean()),
        "minimum_cell_samples": int(counts[counts > 0].min()) if np.any(counts > 0) else 0,
        "annular_max_adjacent_relative_step": float(np.nanmax(annular_diff)),
        "annular_max_relative_curvature": float(np.nanmax(annular_curvature)),
        "sector_p95_adjacent_relative_step": float(np.percentile(finite_steps, 95)),
        "sector_max_adjacent_relative_step": float(np.max(finite_steps)),
        "sector_neighbour_p99_relative_deviation": float(np.percentile(neighbour_array, 99)),
        "sector_neighbour_max_relative_deviation": float(np.max(neighbour_array)),
    }
    thresholds = {
        "annular_max_adjacent_relative_step": 0.005,
        "annular_max_relative_curvature": 0.005,
        "sector_p95_adjacent_relative_step": 0.015,
        "sector_max_adjacent_relative_step": 0.04,
        "sector_neighbour_p99_relative_deviation": 0.035,
        "sector_neighbour_max_relative_deviation": 0.10,
        "minimum_valid_cell_fraction": 0.98,
    }
    passed = (
        metrics["annular_max_adjacent_relative_step"] <= thresholds["annular_max_adjacent_relative_step"]
        and metrics["annular_max_relative_curvature"] <= thresholds["annular_max_relative_curvature"]
        and metrics["sector_p95_adjacent_relative_step"] <= thresholds["sector_p95_adjacent_relative_step"]
        and metrics["sector_max_adjacent_relative_step"] <= thresholds["sector_max_adjacent_relative_step"]
        and metrics["sector_neighbour_p99_relative_deviation"] <= thresholds["sector_neighbour_p99_relative_deviation"]
        and metrics["sector_neighbour_max_relative_deviation"] <= thresholds["sector_neighbour_max_relative_deviation"]
        and metrics["valid_cell_fraction"] >= thresholds["minimum_valid_cell_fraction"]
    )
    return {
        "domain_rsun": [1.15, 5.0],
        "definition": "sector medians of (fused-vixen)/max(abs(vixen),p05), evaluated before tone mapping",
        "metrics": metrics,
        "thresholds": thresholds,
        "status": "PASS" if passed else "FAIL",
    }


def build_confidence_and_fusion(
    matched: dict[str, Path], warped: dict[str, Path], vixen: np.ndarray, staging: Path
) -> tuple[dict[str, Path], dict[str, Any], str]:
    sony = np.load(matched["image"], mmap_mode="r")
    variance = np.load(matched["variance_total"], mmap_mode="r")
    support = np.load(warped["support"], mmap_mode="r") > 0
    vixen_valid = np.all(np.isfinite(vixen), axis=2)
    valid = support & vixen_valid & np.all(np.isfinite(variance), axis=2)
    invvar = np.zeros(VIXEN_SHAPE[:2], np.float32)
    max_variance = np.max(np.asarray(variance), axis=2)
    invvar[valid] = 1.0 / np.maximum(max_variance[valid], np.finfo(np.float32).tiny)
    yy, xx = np.mgrid[0:VIXEN_SHAPE[0], 0:VIXEN_SHAPE[1]]
    rho = np.hypot(xx - VIXEN_CENTER_XY[0], yy - VIXEN_CENTER_XY[1]) / VIXEN_RADIUS_PX
    normalisation_domain = valid & (rho >= 2.2) & (rho <= 5.0)
    if np.count_nonzero(normalisation_domain) < 1_000_000:
        raise ContractError("domini insuficient per normalitzar la confiança Sony")
    iv_reference = float(np.median(invvar[normalisation_domain]))
    raw_confidence = invvar / (invvar + iv_reference)
    # Smooth only a measurement (inverse variance), by normalized convolution.
    # Image values never participate in this mask.
    sigma = 12.0
    num = ndi.gaussian_filter(raw_confidence * valid, sigma=sigma, mode="constant", cval=0.0)
    den = ndi.gaussian_filter(valid.astype(np.float32), sigma=sigma, mode="constant", cval=0.0)
    smoothed = np.zeros_like(raw_confidence)
    np.divide(num, den, out=smoothed, where=den > 0.2)
    smoothed[~valid] = 0.0
    distance = cv2.distanceTransform(valid.astype(np.uint8), cv2.DIST_L2, 5)
    max_alpha = 0.25
    candidates: list[dict[str, Any]] = []
    chosen_alpha: np.ndarray | None = None
    chosen_width: float | None = None
    for width in (32.0, 48.0, 64.0, 96.0, 128.0, 160.0, 192.0, 256.0):
        support_taper = smoothstep01(distance / width)
        alpha = (max_alpha * smoothed * support_taper).astype(np.float32)
        alpha[~valid] = 0.0
        qa = sector_ring_qa(alpha, sony, vixen)
        candidates.append({"support_taper_width_px": width, "qa": qa})
        log(
            f"  QA ploma {width:.0f}px: {qa['status']} "
            f"ring-step={qa['metrics']['annular_max_adjacent_relative_step']:.5f} "
            f"sector-p95={qa['metrics']['sector_p95_adjacent_relative_step']:.5f}"
        )
        if qa["status"] == "PASS" and chosen_alpha is None:
            chosen_alpha = alpha
            chosen_width = width
            break
    verdict = "ACCEPTADA_PER_FUSIO" if chosen_alpha is not None else "NO_ACCEPTADA_PER_FUSIO"
    if chosen_alpha is None:
        # A separate matched layer remains useful; publish a zero effective
        # fusion mask so no downstream compositor can mistake a failed pilot
        # for an accepted blend.
        chosen_alpha = np.zeros(VIXEN_SHAPE[:2], np.float32)
    paths = {
        "confidence": staging / "SONY_VISUAL_CONFIDENCE_FROM_INVVAR_SUPPORT.npy",
        "alpha": staging / "SONY_VISUAL_ALPHA_EFFECTIVE.npy",
        "fused": staging / "VIXEN_PLUS_SONY_VISUAL_CANDIDATE_LINEAR_ADU_S.npy",
    }
    np.save(paths["confidence"], smoothed.astype(np.float32))
    np.save(paths["alpha"], chosen_alpha)
    fused = open_memmap(paths["fused"], mode="w+", dtype=np.float32, shape=VIXEN_SHAPE)
    for y0 in range(0, VIXEN_SHAPE[0], 128):
        y1 = min(y0 + 128, VIXEN_SHAPE[0])
        a = chosen_alpha[y0:y1, :, None]
        v = vixen[y0:y1]
        s = np.asarray(sony[y0:y1])
        s_safe = np.where(np.isfinite(s), s, v)
        fused[y0:y1] = v + a * (s_safe - v)
    fused.flush()
    del fused
    tifffile.imwrite(
        staging / "SONY_VISUAL_ALPHA_EFFECTIVE_FLOAT32_BIGTIFF.tif",
        chosen_alpha,
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="minisblack",
        metadata=None,
        description="Visual alpha derived only from Sony inverse variance and valid-support distance; max 0.25",
    )
    tifffile.imwrite(
        staging / "VIXEN_PLUS_SONY_VISUAL_CANDIDATE_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        np.load(paths["fused"], mmap_mode="r"),
        bigtiff=True,
        compression="deflate",
        predictor=False,
        photometric="rgb",
        metadata=None,
        description=f"Linear visual cross-train candidate; verdict {verdict}; no tone or local contrast",
    )
    qa = {
        "alpha_basis": [
            "minimum RGB inverse total variance",
            "normalized convolution of inverse variance, sigma 12 px",
            "distance to accepted support boundary",
        ],
        "image_structure_used_in_alpha": False,
        "free_radial_or_circular_mask": False,
        "maximum_alpha": max_alpha,
        "inverse_variance_reference": iv_reference,
        "candidate_support_tapers": candidates,
        "chosen_support_taper_width_px": chosen_width,
        "effective_alpha_statistics": {
            "nonzero_fraction": float(np.mean(chosen_alpha > 0)),
            "median_nonzero": float(np.median(chosen_alpha[chosen_alpha > 0])) if np.any(chosen_alpha > 0) else 0.0,
            "p95": float(np.percentile(chosen_alpha, 95)),
            "maximum": float(np.max(chosen_alpha)),
        },
    }
    return paths, qa, verdict


def write_sha256sums(root: Path) -> None:
    paths = sorted(path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    lines = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        lines.append(f"{sha256(path)}  {relative}")
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> Path:
    script_path = Path(__file__).resolve()
    sony_root = Path(args.sony_root)
    vixen_hdr = Path(args.vixen_hdr)
    research80 = Path(args.research80)
    output = Path(args.output).expanduser().resolve()
    groups, evidence = validate_inputs(sony_root, vixen_hdr, research80, script_path)
    log("VALIDACIÓ D'ENTRADES: PASS")
    if args.validate_only:
        return output
    if output.exists():
        raise ContractError(f"el directori de sortida ja existeix: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    if staging.exists():
        raise ContractError(f"staging inesperadament existent: {staging}")
    staging.mkdir()
    try:
        load_group_arrays(groups)
        fits_internal = fit_internal_groups(groups)
        native = create_native_hdr(groups, fits_internal, staging, args.chunk_rows)
        vixen = tifffile.imread(vixen_hdr)
        if vixen.shape != VIXEN_SHAPE or vixen.dtype != np.float32:
            raise ContractError("HDR Vixen amb shape/dtype inesperat")
        sign_data = validate_rotation_with_data(
            np.load(native["image"], mmap_mode="r"),
            np.load(native["support"], mmap_mode="r"),
            vixen,
        )
        log(
            "Signe +33.0806°: "
            f"cc+={sign_data['positive_rotation_correlation']:.3f}, "
            f"cc-={sign_data['negative_rotation_correlation']:.3f}"
        )
        warped = warp_to_vixen(native, staging, args.chunk_rows)
        fits_cross = fit_cross_train(warped, vixen)
        matched = materialize_matched_layer(warped, fits_cross, staging, args.chunk_rows)
        visual, seam_qa, fusion_verdict = build_confidence_and_fusion(matched, warped, vixen, staging)

        # Machine-readable radial/sector profiles for an independent audit.
        write_json(staging / "SEAM_AND_SECTOR_QA.json", seam_qa)
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "verdict": fusion_verdict,
            "scientific_authority": "CFA4 R/G1/B/G2 accepted upstream; RGB here is a visual Gaussian-demosaic derivative",
            "input_scope": {
                "sony_mount_segment": "C only",
                "sony_exposures_s": [1.0 / 30.0, 0.25, 2.0],
                "segment_A_consumed": False,
                "eight_second_consumed": False,
                "single_frame_products_consumed": False,
                "lunar_transform_consumed_or_transferred": False,
            },
            "input_evidence": evidence,
            "geometry": {
                "frame": "CORONA_SOLAR",
                "source_shape_yxc": list(SONY_SHAPE),
                "destination_shape_yxc": list(VIXEN_SHAPE),
                "source_center_xy_px": list(SONY_CENTER_XY),
                "destination_center_xy_px": list(VIXEN_CENTER_XY),
                "source_plate_scale_arcsec_px": SONY_PLATE_SCALE,
                "destination_plate_scale_arcsec_px": VIXEN_PLATE_SCALE,
                "source_to_destination_scale": SOURCE_TO_DEST_SCALE,
                "source_to_destination_rotation_deg": SOURCE_TO_DEST_ROTATION_DEG,
                "coordinate_convention": "x right, y down; positive source->destination uses [[cos,sin],[-sin,cos]]",
                "resampling": "bilinear image; squared bilinear weights for random variance; correlated-amplitude interpolation for systematics; all four neighbours require support",
                "solar_radius_sony_px": SONY_RADIUS_PX,
                "solar_radius_vixen_px": VIXEN_RADIUS_PX,
                "sign_validation_data": sign_data,
            },
            "internal_hdr": {
                "anchor_exposure": ANCHOR_GROUP,
                "normalisation_domain_rsun": [2.2, 5.0],
                "normalisation": {
                    name: [fit.receipt() for fit in fits_internal[name]] for name in fits_internal
                },
                "random_weighting": "inverse random variance",
                "shared_flat_systematic": "not averaged down; weighted standard deviations added with full positive correlation",
                "accepted_scientific_domains_rsun": {
                    "1-30s": [1.2, None], "1-4s": [1.5, None], "2s": [2.0, None]
                },
            },
            "cross_train_photometry": {
                "model": "global robust per-channel gain plus additive plane",
                "fit_domain_rsun": [2.2, 5.0],
                "channels": {CHANNELS[i]: fit.receipt() for i, fit in enumerate(fits_cross)},
                "gain_and_model_covariance_propagated": True,
            },
            "visual_fusion": seam_qa,
            "anti_ring_domain_rsun": [1.15, 5.0],
            "tone_mapping": None,
            "local_contrast_or_detail_filter": None,
            "denoise": None,
            "source_mutations": 0,
            "outputs": [],
        }
        write_json(staging / "CROSS_TRAIN_RECEIPT.json", receipt)
        all_outputs = sorted(
            path for path in staging.rglob("*")
            if path.is_file() and path.name not in {"CROSS_TRAIN_RECEIPT.json", "SHA256SUMS.txt"}
        )
        receipt["outputs"] = [output_record(path, staging) for path in all_outputs]
        write_json(staging / "CROSS_TRAIN_RECEIPT.json", receipt)
        write_sha256sums(staging)
        os.replace(staging, output)
        return output
    except BaseException:
        # A failed staging tree can be many GiB and has no authority.  It is
        # safe to remove because the path was generated by this process and
        # has never been published.  Upstream files are never touched.
        if staging.exists():
            shutil.rmtree(staging)
        raise


def parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[3]
    derived = root / "output" / "postprocessat_final_20260822"
    v2 = derived / "composites" / "vixen_natural_stable_v2" / "VIXEN_HDR_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif"
    v1 = derived / "composites" / "vixen_natural_stable_v1" / "VIXEN_HDR_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif"
    default_vixen = v2 if v2.is_file() else v1
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--sony-root", default=str(derived / "masters" / "sony_s6_ACCEPTED"))
    result.add_argument("--vixen-hdr", default=str(default_vixen))
    result.add_argument(
        "--research80", default=str(root / "research" / "80_ENCAIX_CAPA_SONY_AL_COMPOST_I_ESTRELLES_2026-08-18.md")
    )
    result.add_argument("--output", default=str(derived / "composites" / "sony_cross_train_c_v1"))
    result.add_argument("--chunk-rows", type=int, default=96)
    result.add_argument("--validate-only", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.chunk_rows < 16 or args.chunk_rows > 512:
        raise ContractError("--chunk-rows ha d'estar entre 16 i 512")
    output = build(args)
    if args.validate_only:
        log(f"VALIDATE-ONLY PASS; no s'ha creat {output}")
    else:
        log(f"PUBLICAT ATÒMICAMENT: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"CONTRACT ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
