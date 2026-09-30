#!/usr/bin/env python3
"""Build a conservative, manifest-driven Vixen HDR and NATURAL rendition.

This program is deliberately independent from the historical radial-mask,
MGN and NRGF compositors.  It consumes only exposure-separated upstream
masters whose receipt has the *literal* verdict ``ACCEPTAT``.  Every consumed
file must be listed and hashed by that receipt.

The HDR is a per-pixel inverse-variance mean in the already common Vixen
geometry.  A source contributes only where its linear range, unsaturated
support and coverage are valid.  No radius, annulus or hand-painted mask is
used to blend exposures.  The intersection of upstream physical support is
kept as a hard no-data guard; this prevents a neighbouring exposure from
painting across another master's lunar/no-data boundary.

An optional, manifest-declared photometric harmonisation measures one global
RGB multiplier per exposure from robust radial-sector medians in common
linear overlap.  The annuli are used only to estimate those three constants;
they never become spatial blend masks.  Image values and variances are then
transformed coherently (``L'=gL``, ``Var'=g^2 Var``).  This removes a genuine
exposure-scale discontinuity without manufacturing radial detail.

The NATURAL branch is intentionally mild and editable: one global monotonic
toe/shoulder curve, the measured R6 daylight white balance and camera matrix,
and a real conversion to Adobe RGB (1998).  It has no local contrast, detail
filter, denoise, MGN or NRGF.  The scientific linear HDR remains a separate
float BigTIFF.

Minimal input manifest (paths are relative to the manifest):

{
  "schema": "ECLIPSE_NATURAL_COMPOSITE_V1",
  "vixen": {
    "temporal_segment": "STABLE",
    "masters": [
      {
        "receipt": "masters/1-125s/STACK_RECEIPT.json",
        "valid_range": {"mode": "upstream_weighted_support"}
      }
    ],
    "support_policy": "intersection_of_upstream_physical_support"
  },
  "geometry": {
    "solar_center_xy_px": [3563.8913, 2274.6605],
    "solar_radius_px": 440.399
  },
  "extensions": {"sony": null, "earthshine": null}
}

``valid_range`` may additionally declare ``min_adu_s`` and ``max_adu_s``
(scalar or three values, ``null`` meaning unbounded) and/or ``valid_map``
(a receipt-hashed HxW or HxWx3 NPY map).  The upstream-weighted mode trusts an
accepted stack to have excluded raw non-linearity per pixel, then independently
rechecks finite values, positive variance/inverse variance, coverage and the
all-members-saturated condition.  Use mode ``explicit`` to require an explicit
map or numeric bound.

Sony and earthshine are named extension points but intentionally unimplemented:
supplying either one fails closed until a measured cross-train transform and a
separate lunar registration/photometric contract exist.

The coronal temporal segment is also fail-closed.  ``STABLE`` is reserved for
groups whose early/late split and sector gates explicitly passed before the
acceptance receipt was issued.  Otherwise the manifest must select exactly
one of ``EARLY``, ``LATE``, ``LATE1`` or ``LATE2``.  Raw ``all`` is rejected;
``C2`` and ``C3`` are always excluded from this coronal HDR and remain
protected contact-phenomenon branches.

The program never overwrites an output directory.  Validation and all upstream
hash checks happen before it creates a staging directory.  A failed build leaves
its own ``.partial-*`` directory for audit; it never mutates an upstream file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import struct
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import tifffile
from scipy import ndimage


SCHEMA = "ECLIPSE_NATURAL_COMPOSITE_V1"
RECEIPT_SCHEMA = "ECLIPSE_NATURAL_COMPOSITE_RECEIPT_V1"
UPSTREAM_ACCEPTED = "ACCEPTAT"
FRAME = "CORONA_SOLAR"
ALLOWED_CORONAL_SEGMENTS = frozenset({"STABLE", "EARLY", "LATE", "LATE1", "LATE2"})
# Corrected DE440+IAU radii for this dataset.  The historical Vixen 959-arcsec
# constant is explicitly forbidden.  These radii are QA geometry only: they
# never generate an HDR blend mask.
VIXEN_SOLAR_RADIUS_PX = 946.6598 / 2.1495
SONY_SOLAR_RADIUS_PX = 295.647
SOLAR_RADIUS_TOLERANCE_PX = 0.05

DEFAULT_PRODUCTS = {
    "master": "MASTER_linear_float32_ADU_s.tif",
    "variance": "VARIANCE_ADU2_s2.npy",
    "invvar": "INVVAR_WEIGHT.npy",
    "coverage": "COVERAGE_SAMPLES.npy",
    "coverage_effective": "COVERAGE_EFFECTIVE_S.npy",
    "saturation": "SATURATION_OUTPUT_COUNT.npy",
}

# Canon R6 Mark III daylight colour path already measured and used by the
# project's Vixen pipeline (hdr_corona_vixen.py).  The manifest can override
# both values, and the exact values used are always written to the receipt.
DEFAULT_WHITE_BALANCE = np.array([2.1678, 1.0, 1.3555], np.float64)
DEFAULT_CAMERA_TO_LINEAR_SRGB = np.array(
    [[1.5595, -0.5902, 0.0306],
     [-0.1770, 1.6854, -0.5083],
     [-0.0250, -0.4964, 1.5214]],
    np.float64,
)

LINEAR_SRGB_TO_XYZ_D65 = np.array(
    [[0.4124564, 0.3575761, 0.1804375],
     [0.2126729, 0.7151522, 0.0721750],
     [0.0193339, 0.1191920, 0.9503041]],
    np.float64,
)
XYZ_D65_TO_LINEAR_ADOBE_RGB = np.array(
    [[2.0413690, -0.5649464, -0.3446944],
     [-0.9692660, 1.8760108, 0.0415560],
     [0.0134474, -0.1183897, 1.0154096]],
    np.float64,
)
ADOBE_RGB_TO_XYZ_D65 = np.array(
    [[0.5767309, 0.1855540, 0.1881852],
     [0.2973769, 0.6273491, 0.0752741],
     [0.0270343, 0.0706872, 0.9911085]],
    np.float64,
)
ADOBE_LUMA = ADOBE_RGB_TO_XYZ_D65[1]
ADOBE_GAMMA = 563.0 / 256.0


class ContractError(RuntimeError):
    """An input or requested operation violates the fail-closed contract."""


@dataclass(frozen=True)
class RangeContract:
    mode: str
    minimum: tuple[float | None, float | None, float | None]
    maximum: tuple[float | None, float | None, float | None]
    valid_map: Path | None
    valid_map_name: str | None


@dataclass(frozen=True)
class MasterSpec:
    receipt_path: Path
    receipt_sha256: str
    receipt: dict[str, Any]
    temporal_segment: str
    exposure_s: float
    member_count: int
    empirical_variance_scale: tuple[float, float, float]
    geometry_xy: tuple[float, float]
    paths: dict[str, Path]
    product_records: dict[str, dict[str, Any]]
    valid_range: RangeContract
    shape: tuple[int, int, int]


@dataclass(frozen=True)
class AcceptedRoot:
    """Hash-anchored Vixen S6 authority root declared by the manifest."""

    root: Path
    receipt_path: Path
    receipt_sha256: str
    sums_path: Path
    sums_sha256: str
    checksums: dict[str, dict[str, Any]]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"No es pot llegir JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} no conté un objecte JSON")
    return value


def read_sha256sums(path: Path) -> dict[str, dict[str, Any]]:
    """Parse a strict sha256sum file without accepting absolute/escaping paths."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ContractError(f"No es pot llegir {path}: {exc}") from exc
    records: dict[str, dict[str, Any]] = {}
    for ordinal, line in enumerate(lines, start=1):
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ContractError(f"{path}:{ordinal}: línia SHA-256 invàlida")
        digest, name = parts
        if any(ch not in "0123456789abcdef" for ch in digest):
            raise ContractError(f"{path}:{ordinal}: digest SHA-256 invàlid")
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != name:
            raise ContractError(f"{path}:{ordinal}: ruta no relativa/canònica: {name!r}")
        if name in records:
            raise ContractError(f"{path}:{ordinal}: ruta duplicada: {name}")
        records[name] = {"name": relative.name, "sha256": digest}
    if not records:
        raise ContractError(f"{path}: manifest SHA-256 buit")
    return records


def accepted_root_contract(
    manifest: dict[str, Any], manifest_path: Path
) -> AcceptedRoot | None:
    """Validate the immutable root that promoted pending S6 products.

    Older, directly accepted S6 receipts remain readable for reproducibility,
    but the post-eclipse authority layout uses a separate group
    ``AUTHORITY_RECEIPT.json``.  In that layout the root receipt and its full
    checksum manifest must be pinned literally by the NATURAL manifest before
    any large product is opened.
    """
    vixen = manifest.get("vixen")
    if not isinstance(vixen, dict):
        return None
    raw = vixen.get("accepted_root")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ContractError("vixen.accepted_root ha de ser un objecte")
    base = manifest_path.parent
    receipt_path = resolve_manifest_path(
        base, raw.get("receipt"), "vixen.accepted_root.receipt"
    )
    sums_path = resolve_manifest_path(
        base, raw.get("sha256sums"), "vixen.accepted_root.sha256sums"
    )
    expected_receipt = raw.get("receipt_sha256")
    expected_sums = raw.get("sha256sums_sha256")
    if not isinstance(expected_receipt, str) or len(expected_receipt) != 64:
        raise ContractError("vixen.accepted_root.receipt_sha256 invàlid")
    if not isinstance(expected_sums, str) or len(expected_sums) != 64:
        raise ContractError("vixen.accepted_root.sha256sums_sha256 invàlid")
    if sha256(receipt_path) != expected_receipt:
        raise ContractError("SHA-256 divergent del rebut arrel Vixen ACCEPTED")
    if sha256(sums_path) != expected_sums:
        raise ContractError("SHA-256 divergent de SHA256SUMS arrel Vixen ACCEPTED")
    receipt = read_json_object(receipt_path)
    if (receipt.get("schema") != "VIXEN_R6_S6_ACCEPTED_AUTHORITY_V1"
            or receipt.get("verdict") != UPSTREAM_ACCEPTED
            or receipt.get("train") != "VIXEN_VSD90SS_CANON_R6_MARK_III"
            or receipt.get("frame") != FRAME):
        raise ContractError("rebut arrel Vixen ACCEPTED invàlid")
    root = receipt_path.parent.resolve()
    if sums_path.parent.resolve() != root:
        raise ContractError("receipt i sha256sums Vixen han de compartir root")
    checksums = read_sha256sums(sums_path)
    root_receipt_record = checksums.get(receipt_path.name)
    if not root_receipt_record or root_receipt_record["sha256"] != expected_receipt:
        raise ContractError("SHA256SUMS arrel no ancora AUTHORITY_RECEIPT.json")
    return AcceptedRoot(
        root=root,
        receipt_path=receipt_path,
        receipt_sha256=expected_receipt,
        sums_path=sums_path,
        sums_sha256=expected_sums,
        checksums=checksums,
    )


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def resolve_manifest_path(base: Path, raw: object, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ContractError(f"{label} ha de ser una ruta no buida")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def require_finite_positive(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} ha de ser numèric")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ContractError(f"{label} ha de ser finit i > 0")
    return result


def optional_channel_bounds(value: object, label: str) -> tuple[float | None, ...]:
    if value is None:
        return (None, None, None)
    items = [value, value, value] if not isinstance(value, list) else value
    if len(items) != 3:
        raise ContractError(f"{label} ha de tenir un valor o tres canals")
    result: list[float | None] = []
    for index, item in enumerate(items):
        if item is None:
            result.append(None)
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ContractError(f"{label}[{index}] ha de ser numèric o null")
        number = float(item)
        if not math.isfinite(number):
            raise ContractError(f"{label}[{index}] ha de ser finit")
        result.append(number)
    return tuple(result)


def three_vector(value: object, default: np.ndarray, label: str) -> np.ndarray:
    if value is None:
        return default.copy()
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise ContractError(f"{label} ha de ser un vector finit de tres valors")
    if np.any(array <= 0):
        raise ContractError(f"{label} ha de ser estrictament positiu")
    return array


def matrix3(value: object, default: np.ndarray, label: str) -> np.ndarray:
    if value is None:
        return default.copy()
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3, 3) or not np.all(np.isfinite(array)):
        raise ContractError(f"{label} ha de ser una matriu finita 3x3")
    if abs(float(np.linalg.det(array))) < 1e-10:
        raise ContractError(f"{label} és singular")
    return array


def product_index(receipt: dict[str, Any], receipt_path: Path) -> dict[str, dict[str, Any]]:
    products = receipt.get("products")
    if not isinstance(products, list) or not products:
        raise ContractError(f"{receipt_path}: falta una llista products no buida")
    index: dict[str, dict[str, Any]] = {}
    for item in products:
        if not isinstance(item, dict):
            raise ContractError(f"{receipt_path}: producte no és objecte")
        name = item.get("name")
        digest = item.get("sha256")
        size = item.get("bytes")
        if (not isinstance(name, str) or not name or Path(name).name != name
                or name in index):
            raise ContractError(f"{receipt_path}: nom de producte invàlid o duplicat {name!r}")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ContractError(f"{receipt_path}: SHA-256 invàlid per {name}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ContractError(f"{receipt_path}: mida invàlida per {name}")
        index[name] = item
    return index


def parse_range_contract(
    raw: object,
    receipt_dir: Path,
    products: dict[str, dict[str, Any]],
    receipt_path: Path,
) -> RangeContract:
    if not isinstance(raw, dict):
        raise ContractError(f"{receipt_path}: valid_range és obligatori i ha de ser objecte")
    mode = raw.get("mode")
    if mode not in {"upstream_weighted_support", "explicit"}:
        raise ContractError(
            f"{receipt_path}: valid_range.mode ha de ser "
            "upstream_weighted_support o explicit"
        )
    minimum = optional_channel_bounds(raw.get("min_adu_s"), "valid_range.min_adu_s")
    maximum = optional_channel_bounds(raw.get("max_adu_s"), "valid_range.max_adu_s")
    for channel, (lo, hi) in enumerate(zip(minimum, maximum)):
        if lo is not None and hi is not None and lo >= hi:
            raise ContractError(f"{receipt_path}: rang invàlid al canal {channel}")
    valid_map_name = raw.get("valid_map")
    valid_map: Path | None = None
    if valid_map_name is not None:
        if (not isinstance(valid_map_name, str)
                or Path(valid_map_name).name != valid_map_name
                or valid_map_name not in products):
            raise ContractError(
                f"{receipt_path}: valid_map ha de ser un producte hashed del rebut"
            )
        valid_map = receipt_dir / valid_map_name
    has_bounds = any(x is not None for x in minimum + maximum)
    if mode == "explicit" and valid_map is None and not has_bounds:
        raise ContractError(
            f"{receipt_path}: mode explicit requereix valid_map o límits ADU/s"
        )
    return RangeContract(mode, minimum, maximum, valid_map, valid_map_name)


def basic_master_specs(manifest: dict[str, Any], manifest_path: Path) -> list[MasterSpec]:
    if manifest.get("schema") != SCHEMA:
        raise ContractError(f"schema ha de ser literalment {SCHEMA}")
    extensions = manifest.get("extensions", {})
    if not isinstance(extensions, dict):
        raise ContractError("extensions ha de ser un objecte")
    for name in ("sony", "earthshine"):
        request = extensions.get(name)
        disabled = request is None or request is False or request == {"enabled": False}
        if not disabled:
            raise ContractError(
                f"Extensió {name} NO IMPLEMENTADA: falta un transform mesurat, "
                "rebut propi i porta QA; no s'inventarà cap transformació"
            )

    vixen = manifest.get("vixen")
    if not isinstance(vixen, dict):
        raise ContractError("falta l'objecte vixen")
    selected_segment = vixen.get("temporal_segment")
    if selected_segment in {"C2", "C3"}:
        raise ContractError(
            f"vixen.temporal_segment={selected_segment} és un fenomen de contacte "
            "protegit i no pot entrar a l'HDR coronal"
        )
    if selected_segment == "all":
        raise ContractError(
            "vixen.temporal_segment='all' barreja estats temporals a cegues; "
            "tria EARLY, LATE, LATE1 o LATE2"
        )
    if selected_segment not in ALLOWED_CORONAL_SEGMENTS:
        raise ContractError(
            "vixen.temporal_segment ha de ser literalment STABLE, EARLY, "
            "LATE, LATE1 o LATE2"
        )
    if vixen.get("support_policy") != "intersection_of_upstream_physical_support":
        raise ContractError(
            "vixen.support_policy ha de ser literalment "
            "intersection_of_upstream_physical_support"
        )
    entries = vixen.get("masters")
    if not isinstance(entries, list) or not entries:
        raise ContractError("vixen.masters ha de ser una llista no buida")
    accepted_root = accepted_root_contract(manifest, manifest_path)

    base = manifest_path.parent
    provisional: list[MasterSpec] = []
    seen_receipts: set[Path] = set()
    for ordinal, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ContractError(f"vixen.masters[{ordinal}] ha de ser un objecte")
        receipt_path = resolve_manifest_path(
            base, entry.get("receipt"), f"vixen.masters[{ordinal}].receipt"
        )
        if receipt_path in seen_receipts:
            raise ContractError(f"rebut duplicat: {receipt_path}")
        seen_receipts.add(receipt_path)
        receipt = read_json_object(receipt_path)
        # This gate is intentionally first: today's pending candidates fail
        # without hashing or opening any large product.
        if receipt.get("verdict") != UPSTREAM_ACCEPTED:
            raise ContractError(
                f"{receipt_path}: veredicte upstream {receipt.get('verdict')!r}; "
                f"cal el literal {UPSTREAM_ACCEPTED!r}"
            )
        upstream_schema = receipt.get("schema")
        group_authority = upstream_schema == "VIXEN_R6_S6_GROUP_AUTHORITY_V1"
        if group_authority:
            if accepted_root is None:
                raise ContractError(
                    f"{receipt_path}: una autoritat de grup exigeix vixen.accepted_root"
                )
            try:
                relative_authority = receipt_path.relative_to(accepted_root.root).as_posix()
            except ValueError as exc:
                raise ContractError(
                    f"{receipt_path}: rebut de grup fora del root ACCEPTED"
                ) from exc
            root_record = accepted_root.checksums.get(relative_authority)
            if (root_record is None
                    or root_record["sha256"] != sha256(receipt_path)):
                raise ContractError(
                    f"{receipt_path}: el manifest arrel no ancora el rebut de grup"
                )
            if (receipt.get("product_class") != "EXPOSURE_STACK"
                    or receipt.get("phenomenon_scope") != FRAME):
                raise ContractError(
                    f"{receipt_path}: només s'admet un EXPOSURE_STACK de CORONA_SOLAR"
                )
            upstream_path = receipt_path.parent / "STACK_RECEIPT.json"
            expected_upstream = receipt.get("upstream_receipt_sha256")
            if (not isinstance(expected_upstream, str)
                    or sha256(upstream_path) != expected_upstream):
                raise ContractError(
                    f"{receipt_path}: STACK_RECEIPT upstream no coincideix amb l'autoritat"
                )
            upstream_sums = receipt_path.parent / "SHA256SUMS.txt"
            expected_sums = receipt.get("upstream_sha256sums_sha256")
            if (not isinstance(expected_sums, str)
                    or sha256(upstream_sums) != expected_sums):
                raise ContractError(
                    f"{receipt_path}: SHA256SUMS upstream no coincideix amb l'autoritat"
                )
            upstream = read_json_object(upstream_path)
            if (not isinstance(upstream.get("schema"), str)
                    or not upstream["schema"].startswith("VIXEN_R6_STACK_RECEIPT_S6_")):
                raise ContractError(f"{upstream_path}: schema upstream Vixen S6 invàlid")
            # The acceptance receipt governs verdict, segment, geometry and
            # empirical inflation.  The hash-anchored upstream receipt keeps
            # product metadata, calibration and pixel contracts.  Merge only
            # in memory; neither authority file is rewritten.
            authority = receipt
            receipt = dict(upstream)
            receipt.update(authority)
            receipt["products"] = upstream.get("products")
            receipt["stack_info"] = upstream.get("stack_info")
            receipt["weighting"] = upstream.get("weighting")
            receipt["photometry"] = upstream.get("photometry")
            receipt["source_mutations"] = authority.get("source_content_mutations", 0)
            receipt["authority_receipt_path"] = str(receipt_path)
            receipt["authority_receipt_sha256"] = root_record["sha256"]
        elif (not isinstance(upstream_schema, str)
                or not upstream_schema.startswith("VIXEN_R6_STACK_RECEIPT_S6_")):
            raise ContractError(f"{receipt_path}: schema upstream Vixen S6 invàlid")
        if receipt.get("train") != "VIXEN_VSD90SS_CANON_R6_MARK_III":
            raise ContractError(f"{receipt_path}: tren no és Vixen/R6 III")
        if receipt.get("frame") != FRAME:
            raise ContractError(f"{receipt_path}: frame ha de ser {FRAME}")
        receipt_segment = receipt.get("temporal_segment")
        if receipt_segment in {"C2", "C3"}:
            raise ContractError(
                f"{receipt_path}: segment {receipt_segment} exclòs; "
                "C2/C3 no són fonts de corona natural"
            )
        if receipt_segment != selected_segment:
            raise ContractError(
                f"{receipt_path}: temporal_segment={receipt_segment!r}, però el "
                f"manifest selecciona {selected_segment!r}; no es barregen segments"
            )
        radius_model = receipt.get("solar_radius_model")
        if not isinstance(radius_model, dict):
            raise ContractError(
                f"{receipt_path}: falta solar_radius_model corregit DE440+IAU; "
                "no s'accepta el radi històric de 959 arcsec"
            )
        radius_px = radius_model.get("radius_px")
        if (not isinstance(radius_px, (int, float))
                or not math.isfinite(float(radius_px))
                or abs(float(radius_px) - VIXEN_SOLAR_RADIUS_PX)
                > SOLAR_RADIUS_TOLERANCE_PX):
            raise ContractError(
                f"{receipt_path}: R_sun={radius_px!r} px; cal el model Vixen "
                f"DE440+IAU {VIXEN_SOLAR_RADIUS_PX:.3f} px"
            )
        if radius_model.get("historical_959_arcsec_overridden_in_process") is not True:
            raise ContractError(
                f"{receipt_path}: el rebut no prova que 959 arcsec hagi estat substituït"
            )
        if receipt.get("source_mutations") not in (None, 0):
            raise ContractError(f"{receipt_path}: source_mutations no és zero")
        exposure = require_finite_positive(receipt.get("exposure_s"), "exposure_s")
        members = receipt.get("members")
        if not isinstance(members, list) or not members or not all(
            isinstance(name, str) and name for name in members
        ):
            raise ContractError(f"{receipt_path}: members invàlid")
        empirical = three_vector(
            receipt.get("empirical_variance_scale_rgb"),
            np.ones(3, dtype=np.float64),
            "empirical_variance_scale_rgb",
        )
        if np.any(empirical < 1.0):
            raise ContractError(
                f"{receipt_path}: empirical_variance_scale_rgb no pot deflactar"
            )
        weighting = str(receipt.get("weighting", "")).lower()
        if "inverse variance" not in weighting or "saturation" not in weighting:
            raise ContractError(
                f"{receipt_path}: el contracte weighting no declara invvar+saturació"
            )
        photometry = str(receipt.get("photometry", "")).lower().replace(" ", "")
        if "adu/s" not in photometry:
            raise ContractError(f"{receipt_path}: fotometria no declara ADU/s")

        stack_info = receipt.get("stack_info")
        geometry = (
            receipt.get("reference_geometry") if group_authority
            else stack_info.get("geometria") if isinstance(stack_info, dict) else None
        )
        if not isinstance(geometry, dict):
            raise ContractError(f"{receipt_path}: falta la geometria d'autoritat")
        gx = geometry.get("sol_x")
        gy = geometry.get("sol_y")
        if not isinstance(gx, (int, float)) or not isinstance(gy, (int, float)):
            raise ContractError(f"{receipt_path}: centre solar invàlid")
        geometry_xy = (float(gx), float(gy))
        if not all(math.isfinite(x) for x in geometry_xy):
            raise ContractError(f"{receipt_path}: centre solar no finit")

        products = product_index(receipt, receipt_path)
        overrides = entry.get("products", {})
        if not isinstance(overrides, dict):
            raise ContractError(f"{receipt_path}: products override ha de ser objecte")
        names = dict(DEFAULT_PRODUCTS)
        for key, name in overrides.items():
            if key not in names or not isinstance(name, str) or Path(name).name != name:
                raise ContractError(f"{receipt_path}: override de producte invàlid {key!r}")
            names[key] = name
        empirical_product = receipt.get("empirical_variance_scale_product")
        if empirical_product is not None:
            if (not isinstance(empirical_product, str)
                    or Path(empirical_product).name != empirical_product):
                raise ContractError(
                    f"{receipt_path}: empirical_variance_scale_product invàlid"
                )
            if empirical_product not in products:
                if not group_authority or accepted_root is None:
                    raise ContractError(
                        f"{receipt_path}: empirical_variance_scale_product no hashed"
                    )
                empirical_path = receipt_path.parent / empirical_product
                relative_empirical = empirical_path.relative_to(
                    accepted_root.root
                ).as_posix()
                root_empirical = accepted_root.checksums.get(relative_empirical)
                if root_empirical is None:
                    raise ContractError(
                        f"{receipt_path}: el root no ancora {empirical_product}"
                    )
                if not empirical_path.is_file():
                    raise ContractError(f"falta {empirical_path}")
                products[empirical_product] = {
                    "name": empirical_product,
                    "bytes": empirical_path.stat().st_size,
                    "sha256": root_empirical["sha256"],
                }
            names["empirical_scale"] = empirical_product
        missing = [name for name in names.values() if name not in products]
        if missing:
            raise ContractError(f"{receipt_path}: productes obligatoris absents: {missing}")
        paths = {key: receipt_path.parent / name for key, name in names.items()}
        range_contract = parse_range_contract(
            entry.get("valid_range"), receipt_path.parent, products, receipt_path
        )
        if range_contract.valid_map_name:
            names["valid_range"] = range_contract.valid_map_name
            paths["valid_range"] = range_contract.valid_map  # type: ignore[assignment]

        # Shape is filled after the file/hash gate.  The dummy value keeps the
        # immutable dataclass simple during this first, cheap validation pass.
        provisional.append(MasterSpec(
            receipt_path=receipt_path,
            receipt_sha256="",
            receipt=receipt,
            temporal_segment=selected_segment,
            exposure_s=exposure,
            member_count=len(members),
            empirical_variance_scale=tuple(float(x) for x in empirical),
            geometry_xy=geometry_xy,
            paths=paths,
            product_records={key: products[name] for key, name in names.items()},
            valid_range=range_contract,
            shape=(0, 0, 0),
        ))
    return provisional


def inspect_tiff_shape(path: Path) -> tuple[tuple[int, int, int], np.dtype[Any]]:
    try:
        with tifffile.TiffFile(path) as tif:
            series = tif.series[0]
            shape = tuple(int(x) for x in series.shape)
            dtype = np.dtype(series.dtype)
    except (OSError, tifffile.TiffFileError, IndexError) as exc:
        raise ContractError(f"TIFF invàlid {path}: {exc}") from exc
    if len(shape) != 3 or shape[2] != 3:
        raise ContractError(f"{path}: s'esperava HxWx3, rebut {shape}")
    if dtype.kind != "f":
        raise ContractError(f"{path}: el màster ha de ser float, rebut {dtype}")
    return shape, dtype


def npy_shape(path: Path) -> tuple[tuple[int, ...], np.dtype[Any]]:
    try:
        array = np.load(path, mmap_mode="r", allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise ContractError(f"NPY invàlid {path}: {exc}") from exc
    return tuple(int(x) for x in array.shape), array.dtype


def verify_product(path: Path, record: dict[str, Any], receipt_path: Path) -> None:
    if not path.is_file():
        raise ContractError(f"{receipt_path}: falta producte {path}")
    actual_size = path.stat().st_size
    if actual_size != int(record["bytes"]):
        raise ContractError(
            f"{receipt_path}: mida divergent {path.name}: {actual_size} != {record['bytes']}"
        )
    actual_hash = sha256(path)
    if actual_hash != record["sha256"]:
        raise ContractError(
            f"{receipt_path}: SHA-256 divergent {path.name}: {actual_hash}"
        )


def verified_master_specs(provisional: list[MasterSpec]) -> list[MasterSpec]:
    verified: list[MasterSpec] = []
    common_shape: tuple[int, int, int] | None = None
    common_geometry: tuple[float, float] | None = None
    for source in provisional:
        for key, path in source.paths.items():
            verify_product(path, source.product_records[key], source.receipt_path)
        shape, _ = inspect_tiff_shape(source.paths["master"])
        if common_shape is None:
            common_shape = shape
        elif shape != common_shape:
            raise ContractError(
                f"geometries amb shape divergent: {shape} != {common_shape}"
            )
        if common_geometry is None:
            common_geometry = source.geometry_xy
        elif math.hypot(
            source.geometry_xy[0] - common_geometry[0],
            source.geometry_xy[1] - common_geometry[1],
        ) > 0.05:
            raise ContractError(
                f"{source.receipt_path}: centre comú divergent >0,05 px; "
                "aquest compositor no inventa cap transform"
            )

        expected_rgb = shape
        for key in ("variance", "invvar", "coverage", "coverage_effective"):
            map_shape, _ = npy_shape(source.paths[key])
            if map_shape != expected_rgb:
                raise ContractError(
                    f"{source.paths[key]}: shape {map_shape}, esperat {expected_rgb}"
                )
        sat_shape, _ = npy_shape(source.paths["saturation"])
        if sat_shape not in {shape[:2], shape}:
            raise ContractError(
                f"{source.paths['saturation']}: shape {sat_shape}, esperat HxW o HxWx3"
            )
        if source.valid_range.valid_map is not None:
            range_shape, _ = npy_shape(source.valid_range.valid_map)
            if range_shape not in {shape[:2], shape}:
                raise ContractError(
                    f"{source.valid_range.valid_map}: shape {range_shape}, esperat HxW o HxWx3"
                )
        if "empirical_scale" in source.paths:
            scale_array = np.load(
                source.paths["empirical_scale"], mmap_mode="r", allow_pickle=False
            )
            if scale_array.shape != (3,) or not np.allclose(
                np.asarray(scale_array, dtype=np.float64),
                np.asarray(source.empirical_variance_scale, dtype=np.float64),
                rtol=0.0, atol=1e-7,
            ):
                raise ContractError(
                    f"{source.paths['empirical_scale']}: escala no coincideix amb el rebut"
                )

        verified.append(MasterSpec(
            receipt_path=source.receipt_path,
            receipt_sha256=sha256(source.receipt_path),
            receipt=source.receipt,
            temporal_segment=source.temporal_segment,
            exposure_s=source.exposure_s,
            member_count=source.member_count,
            empirical_variance_scale=source.empirical_variance_scale,
            geometry_xy=source.geometry_xy,
            paths=source.paths,
            product_records=source.product_records,
            valid_range=source.valid_range,
            shape=shape,
        ))
    return sorted(verified, key=lambda item: (item.exposure_s, str(item.receipt_path)))


def load_manifest_and_sources(path: Path) -> tuple[dict[str, Any], list[MasterSpec]]:
    manifest = read_json_object(path)
    provisional = basic_master_specs(manifest, path)
    return manifest, verified_master_specs(provisional)


def expand_channels(array: np.ndarray, shape: tuple[int, int, int]) -> np.ndarray:
    if array.ndim == 2:
        return np.broadcast_to(array[..., None], shape)
    return array


def range_mask(values: np.ndarray, contract: RangeContract) -> np.ndarray:
    valid = np.isfinite(values)
    for channel, lower in enumerate(contract.minimum):
        if lower is not None:
            valid[..., channel] &= values[..., channel] >= lower
    for channel, upper in enumerate(contract.maximum):
        if upper is not None:
            valid[..., channel] &= values[..., channel] <= upper
    return valid


def source_valid_sample(
    source: MasterSpec,
    image: np.ndarray,
    stride: int,
    variance_product_rtol: float,
) -> np.ndarray:
    """Return the same per-channel validity gate used by the HDR, sampled.

    This deliberately repeats the upstream range/saturation/coverage contract
    before a photometric factor can be measured.  It does not create or return
    a spatial blend mask for the final composite.
    """
    shape = image.shape
    variance = np.load(source.paths["variance"], mmap_mode="r", allow_pickle=False)
    invvar = np.load(source.paths["invvar"], mmap_mode="r", allow_pickle=False)
    coverage = np.load(source.paths["coverage"], mmap_mode="r", allow_pickle=False)
    effective = np.load(
        source.paths["coverage_effective"], mmap_mode="r", allow_pickle=False
    )
    saturation = np.load(
        source.paths["saturation"], mmap_mode="r", allow_pickle=False
    )
    var = np.asarray(variance[::stride, ::stride], dtype=np.float64)
    weight = np.asarray(invvar[::stride, ::stride], dtype=np.float64)
    cov = np.asarray(coverage[::stride, ::stride])
    eff = np.asarray(effective[::stride, ::stride], dtype=np.float64)
    sat = expand_channels(
        np.asarray(saturation[::stride, ::stride]), shape
    )
    valid = range_mask(image, source.valid_range)
    if source.valid_range.valid_map is not None:
        valid_map = np.load(
            source.valid_range.valid_map, mmap_mode="r", allow_pickle=False
        )
        explicit = expand_channels(
            np.asarray(valid_map[::stride, ::stride]), shape
        ) > 0
        valid &= explicit
    pair = np.isfinite(var) & (var > 0) & np.isfinite(weight) & (weight > 0)
    product = np.zeros(shape, dtype=np.float64)
    np.multiply(var, weight, out=product, where=pair)
    pair &= np.abs(product - 1.0) <= variance_product_rtol
    valid &= pair & (cov > 0) & np.isfinite(eff) & (eff > 0)
    valid &= sat < source.member_count
    del variance, invvar, coverage, effective, saturation
    return valid


def exposure_source(
    sources: list[MasterSpec], exposure_s: float, label: str
) -> MasterSpec:
    matches = [
        source for source in sources
        if abs(source.exposure_s - exposure_s)
        <= max(1e-10, abs(exposure_s) * 2e-5)
    ]
    if len(matches) != 1:
        raise ContractError(
            f"{label}={exposure_s!r} no identifica exactament un màster: "
            f"{len(matches)} coincidències"
        )
    return matches[0]


def radial_sector_ratio_statistics(
    parent: MasterSpec,
    child: MasterSpec,
    center_xy: tuple[float, float],
    solar_radius: float,
    annulus_rsun: tuple[float, float],
    stride: int,
    radial_bins: int,
    angular_sectors: int,
    minimum_pixels_per_cell: int,
    variance_product_rtol: float,
) -> dict[str, Any]:
    """Measure parent/child global ratios from equal-area-ish scene cells."""
    parent_full = np.asarray(
        tifffile.imread(parent.paths["master"]), dtype=np.float32
    )
    child_full = np.asarray(
        tifffile.imread(child.paths["master"]), dtype=np.float32
    )
    parent_image = parent_full[::stride, ::stride]
    child_image = child_full[::stride, ::stride]
    if parent_image.shape != child_image.shape:
        raise ContractError("shape divergent durant harmonització fotomètrica")
    parent_valid = source_valid_sample(
        parent, parent_image, stride, variance_product_rtol
    )
    child_valid = source_valid_sample(
        child, child_image, stride, variance_product_rtol
    )
    height, width = parent_image.shape[:2]
    yy, xx = np.indices((height, width), dtype=np.float64)
    dx = xx * stride - center_xy[0]
    dy = yy * stride - center_xy[1]
    radius_rsun = np.hypot(dx, dy) / solar_radius
    angle = np.mod(np.arctan2(dy, dx), 2.0 * np.pi)
    r0, r1 = annulus_rsun
    radial_index = np.floor((radius_rsun - r0) / (r1 - r0) * radial_bins).astype(np.int32)
    sector_index = np.floor(angle / (2.0 * np.pi) * angular_sectors).astype(np.int32)
    annulus = (
        (radius_rsun >= r0) & (radius_rsun < r1)
        & (radial_index >= 0) & (radial_index < radial_bins)
    )
    channels: list[dict[str, Any]] = []
    for channel in range(3):
        common = (
            annulus & parent_valid[..., channel] & child_valid[..., channel]
            & np.isfinite(parent_image[..., channel])
            & np.isfinite(child_image[..., channel])
            & (parent_image[..., channel] > 0)
            & (child_image[..., channel] > 0)
        )
        cell_medians: list[float] = []
        pixels = 0
        for radial_bin in range(radial_bins):
            radial_mask = common & (radial_index == radial_bin)
            for sector in range(angular_sectors):
                mask = radial_mask & (sector_index == sector)
                count = int(np.count_nonzero(mask))
                if count < minimum_pixels_per_cell:
                    continue
                ratios = (
                    parent_image[..., channel][mask].astype(np.float64)
                    / child_image[..., channel][mask].astype(np.float64)
                )
                ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
                if ratios.size < minimum_pixels_per_cell:
                    continue
                cell_medians.append(float(np.median(ratios)))
                pixels += int(ratios.size)
        if not cell_medians:
            raise ContractError(
                f"sense cel·les de solapament per canal {channel}: "
                f"{parent.exposure_s} <- {child.exposure_s}"
            )
        values = np.asarray(cell_medians, dtype=np.float64)
        factor = float(np.median(values))
        mad = float(1.4826 * np.median(np.abs(values - factor)))
        channels.append({
            "channel": "RGB"[channel],
            "local_factor_parent_over_child": factor,
            "cell_count": int(values.size),
            "sampled_pixel_count": pixels,
            "cell_factor_p16_p50_p84": [
                float(x) for x in np.percentile(values, [16.0, 50.0, 84.0])
            ],
            "cell_factor_robust_sigma": mad,
            "relative_robust_sigma": mad / factor,
            "standard_error_advisory": mad / math.sqrt(values.size),
        })
    del parent_full, child_full, parent_image, child_image
    del parent_valid, child_valid, yy, xx, radius_rsun, angle
    return {
        "parent_exposure_s": parent.exposure_s,
        "child_exposure_s": child.exposure_s,
        "annulus_r_sun": [r0, r1],
        "stride": stride,
        "radial_bins": radial_bins,
        "angular_sectors": angular_sectors,
        "minimum_pixels_per_cell": minimum_pixels_per_cell,
        "channels": channels,
    }


def photometric_harmonisation(
    sources: list[MasterSpec],
    manifest: dict[str, Any],
    center_xy: tuple[float, float],
    solar_radius: float,
    variance_product_rtol: float,
) -> dict[str, Any]:
    """Resolve a manifest-declared calibration tree to global RGB gains."""
    processing = manifest.get("processing", {})
    raw = processing.get("photometric_harmonization") if isinstance(processing, dict) else None
    identity = {
        str(source.receipt_path): np.ones(3, dtype=np.float64) for source in sources
    }
    if raw is None:
        return {
            "mode": "IDENTITY",
            "scales_by_receipt": {key: value.tolist() for key, value in identity.items()},
            "pairs": [],
            "spatial_masks": 0,
            "passes": True,
        }
    if not isinstance(raw, dict) or raw.get("mode") != "PAIRWISE_RADIAL_SECTOR_GLOBAL_RGB":
        raise ContractError("processing.photometric_harmonization.mode invàlid")
    anchor_exposure = require_finite_positive(
        raw.get("anchor_exposure_s"), "photometric_harmonization.anchor_exposure_s"
    )
    anchor = exposure_source(sources, anchor_exposure, "anchor_exposure_s")
    pairs_raw = raw.get("pairs")
    if not isinstance(pairs_raw, list) or len(pairs_raw) != len(sources) - 1:
        raise ContractError("photometric_harmonization.pairs ha de formar un arbre complet")
    stride = int(raw.get("stride", 4))
    radial_bins = int(raw.get("radial_bins", 8))
    angular_sectors = int(raw.get("angular_sectors", 16))
    minimum_pixels = int(raw.get("minimum_pixels_per_cell", 8))
    minimum_cells = int(raw.get("minimum_cells_per_channel", 24))
    max_relative_sigma = float(raw.get("max_cell_relative_robust_sigma", 0.20))
    gain_min = float(raw.get("minimum_local_gain", 0.75))
    gain_max = float(raw.get("maximum_local_gain", 1.25))
    if not (2 <= stride <= 32 and 2 <= radial_bins <= 64
            and 4 <= angular_sectors <= 144 and minimum_pixels >= 2
            and minimum_cells >= 8 and 0 < max_relative_sigma < 1
            and 0 < gain_min < 1 < gain_max):
        raise ContractError("paràmetres d’harmonització fotomètrica fora de rang")

    scales: dict[str, np.ndarray] = {
        str(anchor.receipt_path): np.ones(3, dtype=np.float64)
    }
    relative_uncertainty: dict[str, np.ndarray] = {
        str(anchor.receipt_path): np.zeros(3, dtype=np.float64)
    }
    pending = list(pairs_raw)
    pair_records: list[dict[str, Any]] = []
    while pending:
        progressed = False
        for entry in list(pending):
            if not isinstance(entry, dict):
                raise ContractError("entrada pair d’harmonització no és objecte")
            parent = exposure_source(
                sources,
                require_finite_positive(entry.get("parent_exposure_s"), "parent_exposure_s"),
                "parent_exposure_s",
            )
            child = exposure_source(
                sources,
                require_finite_positive(entry.get("child_exposure_s"), "child_exposure_s"),
                "child_exposure_s",
            )
            parent_key = str(parent.receipt_path)
            child_key = str(child.receipt_path)
            if parent_key not in scales:
                continue
            if child_key in scales:
                raise ContractError("arbre fotomètric amb fill duplicat o cicle")
            annulus = entry.get("annulus_r_sun")
            if (not isinstance(annulus, list) or len(annulus) != 2
                    or not all(isinstance(x, (int, float)) for x in annulus)):
                raise ContractError("annulus_r_sun invàlid")
            annulus_tuple = (float(annulus[0]), float(annulus[1]))
            if not (0.9 <= annulus_tuple[0] < annulus_tuple[1] <= 9.0):
                raise ContractError("annulus_r_sun fora de rang")
            record = radial_sector_ratio_statistics(
                parent, child, center_xy, solar_radius, annulus_tuple,
                stride, radial_bins, angular_sectors, minimum_pixels,
                variance_product_rtol,
            )
            local = np.asarray([
                channel["local_factor_parent_over_child"]
                for channel in record["channels"]
            ], dtype=np.float64)
            local_error = np.asarray([
                channel["standard_error_advisory"]
                / channel["local_factor_parent_over_child"]
                for channel in record["channels"]
            ], dtype=np.float64)
            pair_pass = all(
                channel["cell_count"] >= minimum_cells
                and channel["relative_robust_sigma"] <= max_relative_sigma
                and gain_min <= channel["local_factor_parent_over_child"] <= gain_max
                for channel in record["channels"]
            )
            record["passes"] = pair_pass
            if not pair_pass:
                raise ContractError(
                    f"harmonització fotomètrica no acceptada: "
                    f"{parent.exposure_s} <- {child.exposure_s}"
                )
            scales[child_key] = scales[parent_key] * local
            relative_uncertainty[child_key] = np.sqrt(
                relative_uncertainty[parent_key] ** 2 + local_error ** 2
            )
            record["parent_cumulative_scale_rgb"] = scales[parent_key].tolist()
            record["child_cumulative_scale_rgb"] = scales[child_key].tolist()
            record["child_cumulative_relative_uncertainty_advisory_rgb"] = (
                relative_uncertainty[child_key].tolist()
            )
            pair_records.append(record)
            pending.remove(entry)
            progressed = True
        if not progressed:
            raise ContractError("pairs fotomètrics no formen un arbre orientat des de l’àncora")
    if len(scales) != len(sources):
        raise ContractError("arbre fotomètric incomplet")
    scale_records = []
    for source in sources:
        key = str(source.receipt_path)
        scale_records.append({
            "receipt": key,
            "exposure_s": source.exposure_s,
            "scale_rgb": scales[key].tolist(),
            "relative_uncertainty_advisory_rgb": relative_uncertainty[key].tolist(),
        })
    return {
        "mode": "PAIRWISE_RADIAL_SECTOR_GLOBAL_RGB",
        "anchor_exposure_s": anchor.exposure_s,
        "method": (
            "median of per-radial-bin/per-sector pixel-ratio medians; "
            "one global RGB multiplier per exposure"
        ),
        "variance_transform": "L'=g*L; Var'=g^2*Var; InvVar'=InvVar/g^2",
        "annuli_used_only_for_global_parameter_estimation": True,
        "spatial_masks": 0,
        "pairs": pair_records,
        "scales": scale_records,
        "scales_by_receipt": {key: value.tolist() for key, value in scales.items()},
        "systematic_scale_uncertainty_not_folded_into_pixel_variance": True,
        "passes": True,
    }


def create_memmap_npy(path: Path, dtype: Any, shape: tuple[int, ...]) -> np.memmap:
    return np.lib.format.open_memmap(path, mode="w+", dtype=dtype, shape=shape)


def create_tiff_memmap(
    path: Path,
    shape: tuple[int, ...],
    dtype: Any,
    description: dict[str, Any],
    *,
    bigtiff: bool,
    icc_profile: bytes | None = None,
) -> np.memmap:
    extratags: list[tuple[Any, ...]] = []
    if icc_profile is not None:
        extratags.append((34675, 7, len(icc_profile), icc_profile, False))
    photometric = "rgb" if len(shape) == 3 and shape[-1] == 3 else "minisblack"
    return tifffile.memmap(
        path,
        shape=shape,
        dtype=dtype,
        photometric=photometric,
        bigtiff=bigtiff,
        metadata=None,
        description=json.dumps(description, ensure_ascii=False, separators=(",", ":")),
        software="build_natural_composite.py",
        resolution=(300, 300),
        extratags=extratags,
    )


def flush_all(arrays: Iterable[np.memmap]) -> None:
    for array in arrays:
        array.flush()


def build_linear_hdr(
    sources: list[MasterSpec],
    staging: Path,
    chunk_rows: int,
    variance_product_rtol: float,
    photometric: dict[str, Any],
    saturation_taper_width_px: float,
    saturation_taper_exponent: float,
) -> tuple[dict[str, Path], dict[str, Any]]:
    height, width, channels = sources[0].shape
    shape = (height, width, channels)
    scratch_paths = {
        "numerator": staging / ".work_numerator_float64.npy",
        "denominator": staging / ".work_denominator_float64.npy",
        "weight_squared": staging / ".work_weight_squared_float64.npy",
        "variance_numerator": staging / ".work_variance_numerator_float64.npy",
        "contributors": staging / ".work_contributors_uint16.npy",
        "dominant_weight": staging / ".work_dominant_weight_float32.npy",
        "dominant_index": staging / ".work_dominant_index_uint16.npy",
        "support": staging / ".work_support_intersection_uint8.npy",
    }
    numerator = create_memmap_npy(scratch_paths["numerator"], np.float64, shape)
    denominator = create_memmap_npy(scratch_paths["denominator"], np.float64, shape)
    weight_squared = create_memmap_npy(scratch_paths["weight_squared"], np.float64, shape)
    variance_numerator = create_memmap_npy(
        scratch_paths["variance_numerator"], np.float64, shape
    )
    contributors = create_memmap_npy(scratch_paths["contributors"], np.uint16, shape)
    dominant_weight = create_memmap_npy(scratch_paths["dominant_weight"], np.float32, shape)
    dominant_index = create_memmap_npy(scratch_paths["dominant_index"], np.uint16, shape)
    support_intersection = create_memmap_npy(scratch_paths["support"], np.uint8, shape)
    numerator.fill(0)
    denominator.fill(0)
    weight_squared.fill(0)
    variance_numerator.fill(0)
    contributors.fill(0)
    dominant_weight.fill(0)
    dominant_index.fill(0)
    support_intersection.fill(1)

    source_qa: list[dict[str, Any]] = []
    total_pair_values = 0
    total_pair_bad = 0
    for source_index, source in enumerate(sources, start=1):
        # Upstream TIFFs are compressed BigTIFFs, so tifffile must decode one
        # master at a time.  All large auxiliary maps remain read-only memmaps.
        image = np.asarray(tifffile.imread(source.paths["master"]), dtype=np.float32)
        variance = np.load(source.paths["variance"], mmap_mode="r", allow_pickle=False)
        invvar = np.load(source.paths["invvar"], mmap_mode="r", allow_pickle=False)
        coverage = np.load(source.paths["coverage"], mmap_mode="r", allow_pickle=False)
        effective = np.load(
            source.paths["coverage_effective"], mmap_mode="r", allow_pickle=False
        )
        saturation = np.load(
            source.paths["saturation"], mmap_mode="r", allow_pickle=False
        )
        saturation_taper: np.ndarray | None = None
        fully_saturated_2d = None
        if saturation_taper_width_px > 0:
            saturation_array = np.asarray(saturation)
            if saturation_array.ndim == 3:
                fully_saturated_2d = np.all(
                    saturation_array >= source.member_count, axis=2
                )
            else:
                fully_saturated_2d = saturation_array >= source.member_count
            if np.any(fully_saturated_2d):
                distance = ndimage.distance_transform_edt(~fully_saturated_2d)
                unit = np.clip(distance / saturation_taper_width_px, 0.0, 1.0)
                smooth = unit * unit * (3.0 - 2.0 * unit)
                saturation_taper = np.power(
                    smooth, saturation_taper_exponent
                ).astype(np.float32)
                del distance, unit, smooth
        valid_map = (
            np.load(source.valid_range.valid_map, mmap_mode="r", allow_pickle=False)
            if source.valid_range.valid_map is not None else None
        )
        stats = {
            "receipt": str(source.receipt_path),
            "exposure_s": source.exposure_s,
            "members": source.member_count,
            "empirical_variance_scale_rgb": list(source.empirical_variance_scale),
            "photometric_scale_rgb": photometric["scales_by_receipt"][
                str(source.receipt_path)
            ],
            "valid_channels": 0,
            "physical_support_channels": 0,
            "all_members_saturated_channels": 0,
            "variance_invvar_pairs": 0,
            "variance_invvar_bad": 0,
            "saturation_reliability_taper": {
                "enabled": saturation_taper is not None,
                "width_px": saturation_taper_width_px,
                "exponent": saturation_taper_exponent,
                "fully_saturated_pixels": (
                    int(np.count_nonzero(fully_saturated_2d))
                    if fully_saturated_2d is not None else 0
                ),
                "tapered_nonzero_pixels": (
                    int(np.count_nonzero(
                        (saturation_taper > 0) & (saturation_taper < 1)
                    )) if saturation_taper is not None else 0
                ),
            },
        }
        for y0 in range(0, height, chunk_rows):
            y1 = min(height, y0 + chunk_rows)
            block_shape = (y1 - y0, width, channels)
            values = image[y0:y1]
            var = np.asarray(variance[y0:y1], dtype=np.float64)
            weight = np.asarray(invvar[y0:y1], dtype=np.float64)
            cov = np.asarray(coverage[y0:y1])
            eff = np.asarray(effective[y0:y1], dtype=np.float64)
            sat = expand_channels(np.asarray(saturation[y0:y1]), block_shape)

            # A zero-coverage location with saturation evidence still has
            # physical sensor support; it is merely outside this exposure's
            # usable range.  Zero coverage and zero saturation is upstream
            # no-data (including the lunar exclusion or frame edge).
            physical_support = (cov > 0) | (sat > 0)
            support_intersection[y0:y1] &= physical_support.astype(np.uint8)

            pair_base = np.isfinite(var) & (var > 0) & np.isfinite(weight) & (weight > 0)
            pair_ok = np.zeros(block_shape, dtype=bool)
            product = np.zeros(block_shape, dtype=np.float64)
            np.multiply(var, weight, out=product, where=pair_base)
            pair_ok[pair_base] = np.abs(product[pair_base] - 1.0) <= variance_product_rtol
            pair_count = int(np.count_nonzero(pair_base))
            pair_bad = int(np.count_nonzero(pair_base & ~pair_ok))
            total_pair_values += pair_count
            total_pair_bad += pair_bad

            valid = range_mask(values, source.valid_range)
            if valid_map is not None:
                explicit = expand_channels(np.asarray(valid_map[y0:y1]), block_shape) > 0
                valid &= explicit
            all_saturated = sat >= source.member_count
            valid &= ~all_saturated
            valid &= pair_ok & (cov > 0) & np.isfinite(eff) & (eff > 0)

            empirical_scale = np.asarray(
                source.empirical_variance_scale, dtype=np.float64
            ).reshape(1, 1, 3)
            photometric_scale = np.asarray(
                photometric["scales_by_receipt"][str(source.receipt_path)],
                dtype=np.float64,
            ).reshape(1, 1, 3)
            # A global gain is a calibration transform, not a spatial blend.
            # Propagate it coherently to both signal and variance.
            harmonized_values = values * photometric_scale
            usable_weight = np.where(
                valid,
                weight / (empirical_scale * photometric_scale * photometric_scale),
                0.0,
            )
            if saturation_taper is not None:
                usable_weight *= saturation_taper[y0:y1, :, None]
            numerator[y0:y1] += np.where(
                valid, harmonized_values, 0.0
            ) * usable_weight
            denominator[y0:y1] += usable_weight
            weight_squared[y0:y1] += usable_weight * usable_weight
            harmonized_variance = (
                var * empirical_scale * photometric_scale * photometric_scale
            )
            harmonized_variance = np.where(
                valid & np.isfinite(harmonized_variance),
                harmonized_variance,
                0.0,
            )
            variance_numerator[y0:y1] += (
                usable_weight * usable_weight * harmonized_variance
            )
            contributors[y0:y1] += valid.astype(np.uint16)
            stronger = usable_weight > dominant_weight[y0:y1]
            dominant_weight[y0:y1][stronger] = usable_weight[stronger].astype(np.float32)
            dominant_index[y0:y1][stronger] = source_index

            stats["valid_channels"] += int(np.count_nonzero(valid))
            stats["physical_support_channels"] += int(np.count_nonzero(physical_support))
            stats["all_members_saturated_channels"] += int(np.count_nonzero(all_saturated))
            stats["variance_invvar_pairs"] += pair_count
            stats["variance_invvar_bad"] += pair_bad

        channel_total = height * width * channels
        stats["valid_fraction"] = stats["valid_channels"] / channel_total
        stats["physical_support_fraction"] = (
            stats["physical_support_channels"] / channel_total
        )
        stats["all_members_saturated_fraction"] = (
            stats["all_members_saturated_channels"] / channel_total
        )
        stats["variance_invvar_bad_fraction"] = (
            stats["variance_invvar_bad"] / max(stats["variance_invvar_pairs"], 1)
        )
        source_qa.append(stats)
        del image, variance, invvar, coverage, effective, saturation, valid_map
        del saturation_taper, fully_saturated_2d

    bad_fraction = total_pair_bad / max(total_pair_values, 1)
    if total_pair_values == 0 or bad_fraction > 1e-6:
        raise ContractError(
            "VARIANCE_ADU2_s2 i INVVAR_WEIGHT no són recíprocs dins la "
            f"tolerància: {total_pair_bad}/{total_pair_values} ({bad_fraction:.3g})"
        )

    output_paths = {
        "hdr": staging / "VIXEN_HDR_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        "weight_sum": staging / "HDR_INVVAR_WEIGHT_SUM_FLOAT32_BIGTIFF.tif",
        "variance": staging / "HDR_VARIANCE_ADU2_S2_FLOAT32_BIGTIFF.tif",
        "effective_contributors": staging / "HDR_EFFECTIVE_CONTRIBUTORS_FLOAT32_BIGTIFF.tif",
        "contributors": staging / "HDR_CONTRIBUTOR_COUNT_UINT16.tif",
        "dominant": staging / "HDR_DOMINANT_SOURCE_UINT16.tif",
        "valid_channels": staging / "HDR_VALID_CHANNELS_UINT8.tif",
        "valid_pixels": staging / "HDR_VALID_PIXELS_UINT8.tif",
    }
    hdr = create_tiff_memmap(
        output_paths["hdr"], shape, np.float32,
        {"linear": True, "unit": "ADU/s", "frame": FRAME,
         "blend": "per-pixel inverse variance; no radial masks"},
        bigtiff=True,
    )
    weight_sum = create_tiff_memmap(
        output_paths["weight_sum"], shape, np.float32,
        {"linear": True, "unit": "1/(ADU/s)^2", "map": "inverse variance sum"},
        bigtiff=True,
    )
    hdr_variance = create_tiff_memmap(
        output_paths["variance"], shape, np.float32,
        {"linear": True, "unit": "(ADU/s)^2", "map": "1 / inverse variance sum"},
        bigtiff=True,
    )
    effective_contributors = create_tiff_memmap(
        output_paths["effective_contributors"], shape, np.float32,
        {"map": "Kish effective number of exposure masters"},
        bigtiff=True,
    )
    contributors_out = create_tiff_memmap(
        output_paths["contributors"], shape, np.uint16,
        {"map": "number of valid exposure masters"},
        bigtiff=False,
    )
    dominant_out = create_tiff_memmap(
        output_paths["dominant"], shape, np.uint16,
        {"map": "1-based source index; see COMPOSITE_RECEIPT.json"},
        bigtiff=False,
    )
    valid_channels = create_tiff_memmap(
        output_paths["valid_channels"], shape, np.uint8,
        {"map": "per-channel HDR validity; 1 valid, 0 no-data"},
        bigtiff=False,
    )
    valid_pixels = create_tiff_memmap(
        output_paths["valid_pixels"], shape[:2], np.uint8,
        {"map": "RGB-complete HDR validity; 1 valid, 0 no-data"},
        bigtiff=False,
    )

    valid_channel_count = 0
    valid_pixel_count = 0
    for y0 in range(0, height, chunk_rows):
        y1 = min(height, y0 + chunk_rows)
        num = np.asarray(numerator[y0:y1], dtype=np.float64)
        den = np.asarray(denominator[y0:y1], dtype=np.float64)
        den2 = np.asarray(weight_squared[y0:y1], dtype=np.float64)
        var_num = np.asarray(variance_numerator[y0:y1], dtype=np.float64)
        supported = np.asarray(support_intersection[y0:y1], dtype=bool)
        good = supported & np.isfinite(den) & (den > 0)
        block = np.full(num.shape, np.nan, dtype=np.float32)
        block[good] = (num[good] / den[good]).astype(np.float32)
        hdr[y0:y1] = block
        weight_sum[y0:y1] = np.where(good, den, 0).astype(np.float32)
        variance_block = np.zeros(num.shape, dtype=np.float32)
        variance_good = good & np.isfinite(var_num) & (var_num >= 0)
        variance_block[variance_good] = (
            var_num[variance_good] / (den[variance_good] * den[variance_good])
        ).astype(np.float32)
        hdr_variance[y0:y1] = variance_block
        neff = np.zeros(num.shape, dtype=np.float32)
        neff_good = good & np.isfinite(den2) & (den2 > 0)
        neff[neff_good] = (
            den[neff_good] * den[neff_good] / den2[neff_good]
        ).astype(np.float32)
        effective_contributors[y0:y1] = neff
        count_block = np.where(good, contributors[y0:y1], 0).astype(np.uint16)
        contributors_out[y0:y1] = count_block
        dominant_out[y0:y1] = np.where(good, dominant_index[y0:y1], 0).astype(np.uint16)
        valid_channels[y0:y1] = good.astype(np.uint8)
        pixel_good = np.all(good, axis=2)
        valid_pixels[y0:y1] = pixel_good.astype(np.uint8)
        valid_channel_count += int(np.count_nonzero(good))
        valid_pixel_count += int(np.count_nonzero(pixel_good))

    output_arrays = [
        hdr, weight_sum, hdr_variance, effective_contributors,
        contributors_out, dominant_out, valid_channels, valid_pixels,
    ]
    flush_all(output_arrays)
    del output_arrays
    qa = {
        "sources": source_qa,
        "variance_invvar_rtol": variance_product_rtol,
        "variance_invvar_bad_fraction": bad_fraction,
        "valid_channel_fraction": valid_channel_count / (height * width * channels),
        "valid_pixel_fraction": valid_pixel_count / (height * width),
        "support_policy": "intersection_of_upstream_physical_support",
        "spatial_blend_masks": 0,
        "blend_basis": ["inverse_variance", "empirical_variance_scale",
                        "global_photometric_scale",
                        "valid_range", "saturation", "coverage"],
        "photometric_harmonization": {
            "mode": photometric["mode"],
            "spatial_masks": photometric["spatial_masks"],
            "passes": photometric["passes"],
        },
        "saturation_reliability_taper": {
            "enabled": saturation_taper_width_px > 0,
            "width_px": saturation_taper_width_px,
            "exponent": saturation_taper_exponent,
            "basis": "distance to upstream all-members-saturated support",
            "free_radial_or_circular_mask": False,
        },
    }
    del hdr, weight_sum, hdr_variance, effective_contributors
    del contributors_out, dominant_out, valid_channels, valid_pixels
    del numerator, denominator, weight_squared, variance_numerator, contributors
    del dominant_weight, dominant_index, support_intersection
    for path in scratch_paths.values():
        path.unlink()
    return output_paths, qa


def adobe_rgb_icc(gamma: float) -> bytes:
    """Return a compact matrix/TRC Adobe RGB (1998) ICC v2 profile.

    The D50-adapted colourants and 2.19921875 TRC are the Adobe RGB (1998)
    matrix profile values.  Passing gamma=1 creates the linear companion.
    """
    d50 = (0.9642, 1.0, 0.8249)
    primaries = (
        (0.6097412109375, 0.3111114501953125, 0.01947021484375),
        (0.2052764892578125, 0.62567138671875, 0.0608673095703125),
        (0.1491851806640625, 0.0632171630859375, 0.74456787109375),
    )

    def s15fixed16(value: float) -> int:
        return int(round(value * 65536.0))

    def xyz_tag(values: tuple[float, float, float]) -> bytes:
        return b"XYZ " + b"\0" * 4 + struct.pack(
            ">3i", *(s15fixed16(value) for value in values)
        )

    def desc_tag(text: str) -> bytes:
        encoded = text.encode("ascii") + b"\0"
        # ICC v2 textDescriptionType: ASCII followed by empty Unicode and
        # ScriptCode sections.
        return (
            b"desc" + b"\0" * 4 + struct.pack(">I", len(encoded)) + encoded
            + struct.pack(">I", 0) + struct.pack(">I", 0) + struct.pack(">H", 0)
            + bytes([0]) + b"\0" * 67
        )

    gamma_u8fixed8 = int(round(gamma * 256.0))
    trc = b"curv" + b"\0" * 4 + struct.pack(">I", 1) + struct.pack(">H", gamma_u8fixed8)
    name = "Adobe RGB (1998)" + (" Linear" if abs(gamma - 1.0) < 1e-12 else "")
    tags = [
        (b"desc", desc_tag(name)),
        (b"wtpt", xyz_tag(d50)),
        (b"rXYZ", xyz_tag(primaries[0])),
        (b"gXYZ", xyz_tag(primaries[1])),
        (b"bXYZ", xyz_tag(primaries[2])),
        (b"rTRC", trc),
        (b"gTRC", trc),
        (b"bTRC", trc),
        (b"cprt", b"text" + b"\0" * 4 + b"public domain\0"),
    ]
    data_start = 128 + 4 + len(tags) * 12
    table = bytearray()
    data = bytearray()
    offsets: dict[bytes, tuple[int, int]] = {}
    for signature, payload in tags:
        if payload not in offsets:
            offsets[payload] = (data_start + len(data), len(payload))
            data.extend(payload)
            data.extend(b"\0" * ((4 - len(payload) % 4) % 4))
        table.extend(signature)
        table.extend(struct.pack(">II", *offsets[payload]))
    body = struct.pack(">I", len(tags)) + bytes(table) + bytes(data)
    header = bytearray(128)
    struct.pack_into(">I", header, 0, 128 + len(body))
    header[4:8] = b"pyNC"
    header[8:12] = b"\x02\x40\x00\x00"
    header[12:16] = b"mntr"
    header[16:20] = b"RGB "
    header[20:24] = b"XYZ "
    header[36:40] = b"acsp"
    header[40:44] = b"APPL"
    struct.pack_into(">3i", header, 68, *(s15fixed16(value) for value in d50))
    profile = bytes(header) + body
    if len(profile) != struct.unpack_from(">I", profile, 0)[0] or profile[36:40] != b"acsp":
        raise AssertionError("ICC intern invàlid")
    return profile


def camera_to_linear_adobe(
    camera_rgb: np.ndarray,
    white_balance: np.ndarray,
    camera_to_srgb: np.ndarray,
) -> np.ndarray:
    linear_srgb = (camera_rgb * white_balance) @ camera_to_srgb.T
    xyz_d65 = linear_srgb @ LINEAR_SRGB_TO_XYZ_D65.T
    return xyz_d65 @ XYZ_D65_TO_LINEAR_ADOBE_RGB.T


def tone_curve(luminance: np.ndarray, scale: float, power: float) -> np.ndarray:
    x = np.maximum(luminance, 0.0) / scale
    shoulder = x / (1.0 + x)
    return np.power(shoulder, power)


def tone_scale(reference_luminance: float, target: float, power: float) -> float:
    shoulder_target = target ** (1.0 / power)
    ratio = shoulder_target / (1.0 - shoulder_target)
    return reference_luminance / ratio


def anchored_global_curve(
    luminance: np.ndarray,
    scale: float,
    power: float,
    input_anchors: np.ndarray,
    output_anchors: np.ndarray,
) -> np.ndarray:
    """Apply a global monotonic piecewise-linear display curve.

    The optional anchors are global tonal controls, analogous to a restrained
    Photoshop Curves layer.  They depend only on pixel luminance, never on
    position/radius, and therefore cannot create a field-edge circle by
    construction.
    """
    base = tone_curve(luminance, scale, power)
    return np.interp(base, input_anchors, output_anchors)


def hue_preserving_gamut_shoulder(rgb: np.ndarray, knee: float) -> np.ndarray:
    maximum = np.max(rgb, axis=2)
    mapped = maximum.copy()
    high = maximum > knee
    width = 1.0 - knee
    mapped[high] = knee + width * (
        1.0 - np.exp(-(maximum[high] - knee) / width)
    )
    factor = np.ones_like(maximum)
    positive = maximum > 0
    factor[positive] = mapped[positive] / maximum[positive]
    return rgb * factor[..., None]


def percentile_reference(
    hdr_path: Path,
    valid_path: Path,
    white_balance: np.ndarray,
    camera_matrix: np.ndarray,
    sky_subtraction: np.ndarray,
    percentile: float,
    stride: int,
) -> tuple[float, int]:
    hdr = tifffile.memmap(hdr_path, mode="r")
    valid = tifffile.memmap(valid_path, mode="r")
    sample = np.asarray(hdr[::stride, ::stride], dtype=np.float64)
    sample_valid = np.asarray(valid[::stride, ::stride], dtype=bool)
    adobe = camera_to_linear_adobe(
        sample - sky_subtraction[None, None, :], white_balance, camera_matrix
    )
    luminance = adobe @ ADOBE_LUMA
    selection = sample_valid & np.isfinite(luminance) & (luminance > 0)
    count = int(np.count_nonzero(selection))
    if count < 10_000:
        raise ContractError(f"massa pocs píxels vàlids per fixar la corba: {count}")
    reference = float(np.percentile(luminance[selection], percentile))
    if not math.isfinite(reference) or reference <= 0:
        raise ContractError("percentil de luminància invàlid")
    return reference, count


def build_natural(
    hdr_path: Path,
    valid_path: Path,
    staging: Path,
    shape: tuple[int, int, int],
    chunk_rows: int,
    color_config: dict[str, Any],
    tone_config: dict[str, Any],
) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    white_balance = three_vector(
        color_config.get("white_balance"), DEFAULT_WHITE_BALANCE,
        "color.white_balance",
    )
    camera_matrix = matrix3(
        color_config.get("camera_to_linear_srgb"), DEFAULT_CAMERA_TO_LINEAR_SRGB,
        "color.camera_to_linear_srgb",
    )
    sky_pedestal = three_vector(
        color_config.get("sky_pedestal_camera_adu_s"),
        np.ones(3, dtype=np.float64),
        "color.sky_pedestal_camera_adu_s",
    )
    sky_fraction = float(color_config.get("sky_subtract_fraction", 0.0))
    if not math.isfinite(sky_fraction) or not 0.0 <= sky_fraction <= 1.0:
        raise ContractError("color.sky_subtract_fraction ha d'estar entre 0 i 1")
    if "sky_pedestal_camera_adu_s" not in color_config and sky_fraction != 0.0:
        raise ContractError(
            "sky_subtract_fraction no zero exigeix sky_pedestal_camera_adu_s"
        )
    sky_subtraction = sky_pedestal * sky_fraction
    percentile = float(tone_config.get("reference_percentile", 99.8))
    target = float(tone_config.get("reference_target", 0.78))
    power = float(tone_config.get("power", 0.78))
    gamut_knee = float(tone_config.get("gamut_knee", 0.90))
    sample_stride = int(tone_config.get("sample_stride", 4))
    if not 90.0 <= percentile < 100.0:
        raise ContractError("tone.reference_percentile ha d'estar entre 90 i 100")
    if not 0.1 < target < 0.95:
        raise ContractError("tone.reference_target ha d'estar entre 0,1 i 0,95")
    if not 0.25 <= power <= 1.5:
        raise ContractError("tone.power ha d'estar entre 0,25 i 1,5")
    if not 0.5 <= gamut_knee < 1.0:
        raise ContractError("tone.gamut_knee ha d'estar entre 0,5 i 1")
    if sample_stride < 1:
        raise ContractError("tone.sample_stride ha de ser >= 1")

    reference, sample_count = percentile_reference(
        hdr_path, valid_path, white_balance, camera_matrix, sky_subtraction,
        percentile, sample_stride
    )
    scale = tone_scale(reference, target, power)
    sky_anchor_raw = tone_config.get("sky_anchor_camera_adu_s")
    if sky_anchor_raw is None:
        curve_input = np.array([0.0, 1.0], dtype=np.float64)
        curve_output = np.array([0.0, 1.0], dtype=np.float64)
        sky_anchor = None
        sky_anchor_luminance = None
        sky_anchor_base = None
    else:
        sky_anchor = three_vector(
            sky_anchor_raw, np.ones(3, dtype=np.float64),
            "tone.sky_anchor_camera_adu_s",
        )
        sky_adobe = camera_to_linear_adobe(
            (sky_anchor - sky_subtraction)[None, None, :],
            white_balance, camera_matrix,
        )[0, 0]
        sky_anchor_luminance = float(max(sky_adobe @ ADOBE_LUMA, 0.0))
        sky_anchor_base = float(tone_curve(
            np.asarray([sky_anchor_luminance]), scale, power
        )[0])
        sky_target = float(tone_config.get("sky_output_linear", 0.025))
        reference_output = float(
            tone_config.get("reference_output_linear", min(target, 0.90))
        )
        white_output = float(tone_config.get("white_output_linear", 0.97))
        if not (0.0 < sky_anchor_base < target < 1.0):
            raise ContractError(
                "l'àncora de cel ha de caure entre negre i el percentil de referència"
            )
        if not (0.0 <= sky_target < reference_output < white_output <= 1.0):
            raise ContractError(
                "sortides de la corba global han de créixer: cel < referència < blanc"
            )
        curve_input = np.array(
            [0.0, sky_anchor_base, target, 1.0], dtype=np.float64
        )
        curve_output = np.array(
            [0.0, sky_target, reference_output, white_output], dtype=np.float64
        )
    if not math.isfinite(scale) or scale <= 0:
        raise ContractError("escala tonal invàlida")

    encoded_icc = adobe_rgb_icc(ADOBE_GAMMA)
    linear_icc = adobe_rgb_icc(1.0)
    icc_path = staging / "AdobeRGB1998.icc"
    icc_path.write_bytes(encoded_icc)
    paths = {
        "natural_linear": staging / "NATURAL_LINEAR_ADOBERGB_FLOAT32_BIGTIFF.tif",
        "natural_16": staging / "NATURAL_ADOBERGB16.tif",
        "icc": icc_path,
    }
    natural_linear = create_tiff_memmap(
        paths["natural_linear"], shape, np.float32,
        {"linear": True, "space": "Adobe RGB (1998)",
         "intent": "NATURAL gentle global monotonic shoulder; editable"},
        bigtiff=True,
        icc_profile=linear_icc,
    )
    natural_16 = create_tiff_memmap(
        paths["natural_16"], shape, np.uint16,
        {"linear": False, "space": "Adobe RGB (1998)",
         "trc_gamma": ADOBE_GAMMA, "intent": "NATURAL"},
        bigtiff=False,
        icc_profile=encoded_icc,
    )
    hdr = tifffile.memmap(hdr_path, mode="r")
    valid = tifffile.memmap(valid_path, mode="r")
    valid_count = 0
    positive_count = 0
    high_clip = 0
    black_quantized = 0
    linear_min = math.inf
    linear_max = -math.inf
    for y0 in range(0, shape[0], chunk_rows):
        y1 = min(shape[0], y0 + chunk_rows)
        camera = np.asarray(hdr[y0:y1], dtype=np.float64)
        pixel_valid = np.asarray(valid[y0:y1], dtype=bool)
        adobe = camera_to_linear_adobe(
            camera - sky_subtraction[None, None, :], white_balance, camera_matrix
        )
        # Negative camera-matrix excursions cannot be encoded as Adobe RGB.
        # They are clipped only in this explicitly visual derivative; the
        # separate ADU/s BigTIFF remains untouched.
        adobe = np.maximum(adobe, 0.0)
        luminance = adobe @ ADOBE_LUMA
        display_luminance = anchored_global_curve(
            luminance, scale, power, curve_input, curve_output
        )
        gain = np.zeros_like(luminance)
        positive = pixel_valid & np.isfinite(luminance) & (luminance > 0)
        gain[positive] = display_luminance[positive] / luminance[positive]
        visual = adobe * gain[..., None]
        visual = hue_preserving_gamut_shoulder(visual, gamut_knee)
        visual[~pixel_valid] = 0.0
        visual = np.nan_to_num(visual, nan=0.0, posinf=0.0, neginf=0.0)
        natural_linear[y0:y1] = visual.astype(np.float32)
        encoded = np.power(np.clip(visual, 0.0, 1.0), 1.0 / ADOBE_GAMMA)
        quantized = np.floor(encoded * 65535.0 + 0.5).astype(np.uint16)
        natural_16[y0:y1] = quantized

        selected = np.broadcast_to(pixel_valid[..., None], visual.shape)
        positive_channels = selected & (visual > 0)
        valid_count += int(np.count_nonzero(selected))
        positive_count += int(np.count_nonzero(positive_channels))
        high_clip += int(np.count_nonzero(selected & (quantized == 65535)))
        black_quantized += int(np.count_nonzero(positive_channels & (quantized == 0)))
        if np.any(selected):
            linear_min = min(linear_min, float(np.min(visual[selected])))
            linear_max = max(linear_max, float(np.max(visual[selected])))
    flush_all([natural_linear, natural_16])

    grid = np.concatenate(([0.0], np.logspace(-12, 12, 20_000)))
    mapped_grid = anchored_global_curve(
        grid, scale, power, curve_input, curve_output
    )
    monotonic = bool(np.all(np.diff(mapped_grid) >= -1e-14))
    qa = {
        "valid_channels": valid_count,
        "positive_channels": positive_count,
        "high_clip_channels": high_clip,
        "high_clip_fraction": high_clip / max(valid_count, 1),
        "positive_quantized_to_black_channels": black_quantized,
        "positive_quantized_to_black_fraction": black_quantized / max(positive_count, 1),
        "natural_linear_min": linear_min,
        "natural_linear_max": linear_max,
        "tone_curve_monotonic": monotonic,
    }
    used_config = {
        "white_balance": white_balance.tolist(),
        "camera_to_linear_srgb": camera_matrix.tolist(),
        "sky_pedestal_camera_adu_s": sky_pedestal.tolist(),
        "sky_subtract_fraction": sky_fraction,
        "sky_subtraction_camera_adu_s": sky_subtraction.tolist(),
        "sky_operation_scope": "visual derivative only; scientific HDR unchanged",
        "linear_srgb_to_xyz_d65": LINEAR_SRGB_TO_XYZ_D65.tolist(),
        "xyz_d65_to_linear_adobe_rgb": XYZ_D65_TO_LINEAR_ADOBE_RGB.tolist(),
        "adobe_rgb_trc_gamma": ADOBE_GAMMA,
        "reference_percentile": percentile,
        "reference_target": target,
        "power": power,
        "gamut_knee": gamut_knee,
        "sample_stride": sample_stride,
        "reference_luminance": reference,
        "reference_sample_count": sample_count,
        "tone_scale": scale,
        "global_curve": {
            "kind": "monotonic piecewise linear luminance-only",
            "input_anchors": curve_input.tolist(),
            "output_anchors": curve_output.tolist(),
            "sky_anchor_camera_adu_s": (
                sky_anchor.tolist() if sky_anchor is not None else None
            ),
            "sky_anchor_luminance": sky_anchor_luminance,
            "sky_anchor_base_curve": sky_anchor_base,
            "spatial_or_radial_dependency": False,
        },
        "operations_absent": ["radial_mask", "MGN", "NRGF", "local_contrast", "denoise"],
    }
    del natural_linear, natural_16, hdr, valid
    return paths, qa, used_config


def moving_average_nan(profile: np.ndarray, width: int) -> np.ndarray:
    kernel = np.ones(width, dtype=np.float64)
    finite = np.isfinite(profile)
    numerator = np.convolve(np.where(finite, profile, 0.0), kernel, mode="same")
    denominator = np.convolve(finite.astype(np.float64), kernel, mode="same")
    result = np.full(profile.shape, np.nan, dtype=np.float64)
    okay = denominator >= max(3, width // 2)
    result[okay] = numerator[okay] / denominator[okay]
    return result


def annular_ring_scan(
    luminance: np.ndarray,
    valid: np.ndarray,
    center_xy: tuple[float, float],
    solar_radius: float,
    sample_stride: int,
    bin_px: float,
    sector_deg: float,
    r_min_rsun: float,
    r_max_rsun: float,
    smooth_width_rsun: float,
    relative_threshold: float,
    minimum_sectors: int,
) -> dict[str, Any]:
    height, width = valid.shape
    yy = np.arange(0, height * sample_stride, sample_stride, dtype=np.float32)[:height]
    xx = np.arange(0, width * sample_stride, sample_stride, dtype=np.float32)[:width]
    dx = xx[None, :] - center_xy[0]
    dy = yy[:, None] - center_xy[1]
    radius = np.sqrt(dx * dx + dy * dy)
    angle = np.mod(np.degrees(np.arctan2(dy, dx)), 360.0)
    radial_bin = np.floor(radius / bin_px).astype(np.int32)
    sector_bin = np.floor(angle / sector_deg).astype(np.int16)
    sector_count = int(math.ceil(360.0 / sector_deg))
    radial_count = int(math.ceil(math.hypot(
        max(center_xy[0], width * sample_stride - center_xy[0]),
        max(center_xy[1], height * sample_stride - center_xy[1]),
    ) / bin_px)) + 1
    in_annulus = (
        valid & np.isfinite(luminance) & (luminance > 0)
        & (radius >= r_min_rsun * solar_radius)
        & (radius <= r_max_rsun * solar_radius)
    )
    keys = (sector_bin.astype(np.int64) * radial_count + radial_bin).ravel()
    selection = in_annulus.ravel()
    values = np.log(luminance.ravel()[selection])
    selected_keys = keys[selection]
    size = sector_count * radial_count
    sums = np.bincount(selected_keys, weights=values, minlength=size)
    counts = np.bincount(selected_keys, minlength=size)
    profiles = np.full(size, np.nan, dtype=np.float64)
    enough = counts >= 8
    profiles[enough] = sums[enough] / counts[enough]
    profiles = profiles.reshape(sector_count, radial_count)
    counts = counts.reshape(sector_count, radial_count)

    smooth_bins = max(5, int(round(smooth_width_rsun * solar_radius / bin_px)))
    if smooth_bins % 2 == 0:
        smooth_bins += 1
    threshold_log = math.log1p(relative_threshold)
    hits = np.zeros_like(profiles, dtype=bool)
    amplitudes = np.zeros_like(profiles)
    for sector in range(sector_count):
        smooth = moving_average_nan(profiles[sector], smooth_bins)
        residual = profiles[sector] - smooth
        amplitude = np.abs(residual)
        amplitudes[sector] = np.expm1(np.minimum(amplitude, 20.0))
        local_peak = np.zeros(radial_count, dtype=bool)
        local_peak[1:-1] = (
            (amplitude[1:-1] >= amplitude[:-2])
            & (amplitude[1:-1] >= amplitude[2:])
        )
        hits[sector] = (
            local_peak & np.isfinite(residual) & (amplitude > threshold_log)
            & (counts[sector] >= 8)
        )
    # A circular feature may fall one radial bin apart between sectors.
    dilated = hits | np.roll(hits, 1, axis=1) | np.roll(hits, -1, axis=1)
    coincident = np.sum(dilated, axis=0)
    radial_lo = int(math.ceil(r_min_rsun * solar_radius / bin_px))
    radial_hi = min(radial_count, int(math.floor(r_max_rsun * solar_radius / bin_px)) + 1)
    edge_guard = smooth_bins // 2 + 2
    candidates: list[dict[str, Any]] = []
    for radial in range(radial_lo + edge_guard, radial_hi - edge_guard):
        if coincident[radial] < minimum_sectors:
            continue
        nearby = amplitudes[:, max(0, radial - 1):radial + 2]
        candidates.append({
            "radius_px": (radial + 0.5) * bin_px,
            "radius_rsun": (radial + 0.5) * bin_px / solar_radius,
            "sector_hits": int(coincident[radial]),
            "max_relative_amplitude": float(np.nanmax(nearby)),
        })
    candidates.sort(key=lambda item: item["max_relative_amplitude"], reverse=True)
    return {
        "method": "sector log-luminance minus 0.08-Rsun moving baseline; local extrema",
        "bin_px": bin_px,
        "sector_deg": sector_deg,
        "sample_stride": sample_stride,
        "r_min_rsun": r_min_rsun,
        "r_max_rsun": r_max_rsun,
        "smooth_width_rsun": smooth_width_rsun,
        "relative_threshold": relative_threshold,
        "minimum_coincident_sectors": minimum_sectors,
        "sampled_valid_pixels": int(np.count_nonzero(selection)),
        "candidate_count": len(candidates),
        "candidates": candidates[:32],
    }


def anti_ring_qa(
    hdr_path: Path,
    natural_linear_path: Path,
    valid_path: Path,
    shape: tuple[int, int, int],
    center_xy: tuple[float, float],
    solar_radius: float,
    white_balance: np.ndarray,
    camera_matrix: np.ndarray,
    config: dict[str, Any],
) -> dict[str, Any]:
    stride = int(config.get("ring_sample_stride", 2))
    bin_px = float(config.get("ring_bin_px", 4.0))
    sector_deg = float(config.get("ring_sector_deg", 5.0))
    r_min = float(config.get("ring_r_min_rsun", 1.15))
    r_max = float(config.get("ring_r_max_rsun", 5.0))
    smooth_width = float(config.get("ring_smooth_width_rsun", 0.08))
    threshold = float(config.get("ring_relative_threshold", 0.01))
    minimum_sectors = int(config.get("ring_minimum_sectors", 3))
    if stride < 1 or bin_px <= 0 or sector_deg <= 0 or sector_deg > 45:
        raise ContractError("paràmetres anti-anell invàlids")
    if not 1.0 < r_min < r_max or smooth_width <= 0:
        raise ContractError("domini anti-anell invàlid")
    if not 0 < threshold < 0.25 or minimum_sectors < 2:
        raise ContractError("llindar anti-anell invàlid")

    hdr = tifffile.memmap(hdr_path, mode="r")
    natural = tifffile.memmap(natural_linear_path, mode="r")
    valid = tifffile.memmap(valid_path, mode="r")
    sampled_valid = np.asarray(valid[::stride, ::stride], dtype=bool)
    sampled_hdr = np.asarray(hdr[::stride, ::stride], dtype=np.float64)
    sampled_natural = np.asarray(natural[::stride, ::stride], dtype=np.float64)
    scene_adobe = camera_to_linear_adobe(sampled_hdr, white_balance, camera_matrix)
    scene_luminance = np.maximum(scene_adobe, 0.0) @ ADOBE_LUMA
    natural_luminance = sampled_natural @ ADOBE_LUMA
    scan_args = (
        sampled_valid, center_xy, solar_radius, stride, bin_px, sector_deg,
        r_min, r_max, smooth_width, threshold, minimum_sectors,
    )
    hdr_scan = annular_ring_scan(scene_luminance, *scan_args)
    natural_scan = annular_ring_scan(natural_luminance, *scan_args)
    hdr_radii = [item["radius_px"] for item in hdr_scan["candidates"]]
    new_natural = [
        item for item in natural_scan["candidates"]
        if not any(abs(item["radius_px"] - radius) <= bin_px for radius in hdr_radii)
    ]
    result = {
        "hdr_blend": hdr_scan,
        "natural": natural_scan,
        "natural_new_candidate_count": len(new_natural),
        "natural_new_candidates": new_natural[:32],
        "pass": hdr_scan["candidate_count"] == 0 and len(new_natural) == 0,
        "structural_guard": (
            "zero free radial/circular blend masks; only receipt-hashed "
            "per-pixel range, saturation, coverage, inverse variance and an "
            "optional distance taper derived from all-members saturation"
        ),
    }
    del hdr, natural, valid, sampled_hdr, sampled_natural
    return result


def output_hash_records(paths: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    for role, path in sorted(paths.items()):
        records.append({
            "role": role,
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return records


def input_records(
    sources: list[MasterSpec], photometric: dict[str, Any]
) -> list[dict[str, Any]]:
    records = []
    for index, source in enumerate(sources, start=1):
        records.append({
            "source_index": index,
            "receipt": str(source.receipt_path),
            "receipt_sha256": source.receipt_sha256,
            "upstream_verdict": source.receipt["verdict"],
            "temporal_segment": source.temporal_segment,
            "exposure_s": source.exposure_s,
            "solar_radius_model": source.receipt["solar_radius_model"],
            "members": source.receipt["members"],
            "empirical_variance_scale_rgb": list(source.empirical_variance_scale),
            "photometric_scale_rgb": photometric["scales_by_receipt"][
                str(source.receipt_path)
            ],
            "geometry_xy": list(source.geometry_xy),
            "valid_range": {
                "mode": source.valid_range.mode,
                "min_adu_s": list(source.valid_range.minimum),
                "max_adu_s": list(source.valid_range.maximum),
                "valid_map": source.valid_range.valid_map_name,
            },
            "consumed_products": [
                {
                    "role": role,
                    "name": path.name,
                    "bytes": source.product_records[role]["bytes"],
                    "sha256": source.product_records[role]["sha256"],
                }
                for role, path in sorted(source.paths.items())
            ],
        })
    return records


def geometry_config(manifest: dict[str, Any], sources: list[MasterSpec]) -> tuple[tuple[float, float], float]:
    raw = manifest.get("geometry")
    if not isinstance(raw, dict):
        raise ContractError("falta geometry")
    center = raw.get("solar_center_xy_px")
    if not isinstance(center, list) or len(center) != 2:
        raise ContractError("geometry.solar_center_xy_px ha de tenir [x,y]")
    try:
        center_xy = (float(center[0]), float(center[1]))
    except (TypeError, ValueError) as exc:
        raise ContractError("centre solar invàlid") from exc
    if not all(math.isfinite(value) for value in center_xy):
        raise ContractError("centre solar no finit")
    receipt_center = sources[0].geometry_xy
    if math.hypot(center_xy[0] - receipt_center[0], center_xy[1] - receipt_center[1]) > 0.25:
        raise ContractError(
            "geometry.solar_center_xy_px divergeix >0,25 px dels rebuts acceptats"
        )
    requested_radius = require_finite_positive(
        raw.get("solar_radius_px"), "solar_radius_px"
    )
    if abs(requested_radius - VIXEN_SOLAR_RADIUS_PX) > SOLAR_RADIUS_TOLERANCE_PX:
        raise ContractError(
            f"geometry.solar_radius_px={requested_radius:.6f}; aquest Vixen usa "
            f"R_sun DE440+IAU={VIXEN_SOLAR_RADIUS_PX:.3f} px, no el radi històric"
        )
    # Use the declared canonical value itself, not a nearby rounded manifest
    # value, so every radial QA bin has identical geometry.
    radius = VIXEN_SOLAR_RADIUS_PX
    height, width, _ = sources[0].shape
    if not (0 <= center_xy[0] < width and 0 <= center_xy[1] < height):
        raise ContractError("centre solar fora del llenç")
    if radius < 10 or radius > min(height, width):
        raise ContractError("radi solar implausible")
    return center_xy, radius


def extension_sony(*_: Any, **__: Any) -> None:
    raise NotImplementedError(
        "Sony: cal transform FOV/placa/rotació mesurat i rebut ACCEPTAT abans de fusionar"
    )


def extension_earthshine(*_: Any, **__: Any) -> None:
    raise NotImplementedError(
        "Earthshine: cal registre lunar independent, radi lunar físic i "
        "transferència fotomètrica acceptada; no s'usa R_sun"
    )


def build(manifest_path: Path, output_dir: Path, validate_only: bool) -> int:
    manifest_path = manifest_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ContractError(f"sortida ja existeix; no se sobreescriu: {output_dir}")
    manifest, sources = load_manifest_and_sources(manifest_path)
    center_xy, solar_radius = geometry_config(manifest, sources)
    if validate_only:
        print(json.dumps({
            "status": "VALIDATED_NO_WRITES",
            "manifest": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "accepted_vixen_masters": len(sources),
            "temporal_segment": sources[0].temporal_segment,
            "shape": list(sources[0].shape),
            "exposures_s": [source.exposure_s for source in sources],
        }, indent=2, ensure_ascii=False))
        return 0

    processing = manifest.get("processing", {})
    if not isinstance(processing, dict):
        raise ContractError("processing ha de ser objecte")
    chunk_rows = int(processing.get("chunk_rows", 128))
    variance_rtol = float(processing.get("variance_invvar_product_rtol", 5e-4))
    saturation_taper_width = float(
        processing.get("saturation_reliability_taper_width_px", 0.0)
    )
    saturation_taper_exponent = float(
        processing.get("saturation_reliability_taper_exponent", 1.0)
    )
    if chunk_rows < 8 or chunk_rows > sources[0].shape[0]:
        raise ContractError("processing.chunk_rows fora de rang")
    if not 0 < variance_rtol <= 0.01:
        raise ContractError("variance_invvar_product_rtol fora de rang")
    if (not math.isfinite(saturation_taper_width)
            or not 0.0 <= saturation_taper_width <= 512.0):
        raise ContractError("saturation_reliability_taper_width_px fora de rang")
    if (not math.isfinite(saturation_taper_exponent)
            or not 0.25 <= saturation_taper_exponent <= 32.0):
        raise ContractError("saturation_reliability_taper_exponent fora de rang")
    photometric = photometric_harmonisation(
        sources, manifest, center_xy, solar_radius, variance_rtol
    )
    color = manifest.get("color", {})
    tone = manifest.get("tone", {})
    qa_config = manifest.get("qa", {})
    if not isinstance(color, dict) or not isinstance(tone, dict) or not isinstance(qa_config, dict):
        raise ContractError("color, tone i qa han de ser objectes")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = output_dir.parent / (
        f".{output_dir.name}.partial-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    staging.mkdir(exist_ok=False)
    print(f"staging auditable: {staging}", flush=True)

    hdr_paths, hdr_qa = build_linear_hdr(
        sources, staging, chunk_rows, variance_rtol, photometric,
        saturation_taper_width, saturation_taper_exponent,
    )
    natural_paths, natural_qa, natural_config = build_natural(
        hdr_paths["hdr"], hdr_paths["valid_pixels"], staging, sources[0].shape,
        chunk_rows, color, tone,
    )
    white_balance = np.asarray(natural_config["white_balance"], dtype=np.float64)
    camera_matrix = np.asarray(natural_config["camera_to_linear_srgb"], dtype=np.float64)
    ring_qa = anti_ring_qa(
        hdr_paths["hdr"], natural_paths["natural_linear"],
        hdr_paths["valid_pixels"], sources[0].shape, center_xy, solar_radius,
        white_balance, camera_matrix, qa_config,
    )

    max_high_clip = float(qa_config.get("max_high_clip_fraction", 1e-6))
    max_black = float(qa_config.get("max_positive_to_black_fraction", 1e-4))
    clipping_pass = (
        natural_qa["high_clip_fraction"] <= max_high_clip
        and natural_qa["positive_quantized_to_black_fraction"] <= max_black
    )
    monotonic_pass = bool(natural_qa["tone_curve_monotonic"])
    overall_pass = clipping_pass and monotonic_pass and bool(ring_qa["pass"])
    verdict = "ACCEPTAT" if overall_pass else "REPROCESSAR"

    all_outputs = dict(hdr_paths)
    all_outputs.update(natural_paths)
    output_records = output_hash_records(all_outputs)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stage": "VIXEN_HDR_AND_NATURAL_PRESENTATION",
        "verdict": verdict,
        "manifest": {
            "path": str(manifest_path),
            "sha256": sha256(manifest_path),
            "schema": manifest["schema"],
        },
        "software": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256(Path(__file__).resolve()),
            "python": sys.version,
            "numpy": np.__version__,
            "tifffile": tifffile.__version__,
            "argv": sys.argv,
        },
        "inputs": input_records(sources, photometric),
        "geometry": {
            "shape_yxc": list(sources[0].shape),
            "solar_center_xy_px": list(center_xy),
            "solar_radius_px": solar_radius,
            "solar_radius_authority": "Vixen DE440 topocentric + IAU nominal solar radius",
            "historical_959_arcsec_radius_used": False,
            "cross_source_transform": "none; common accepted Vixen geometry required",
        },
        "temporal_selection": {
            "selected_segment": sources[0].temporal_segment,
            "allowed_coronal_segments": sorted(ALLOWED_CORONAL_SEGMENTS),
            "contact_segments_excluded": ["C2", "C3"],
            "mixed_all_excluded": True,
        },
        "hdr": {
            "estimator": (
                "sum((g_i*L_i) * invvar_i / "
                "(empirical_scale_i*g_i^2)) / sum(invvar_i / "
                "(empirical_scale_i*g_i^2))"
            ),
            "gates": ["valid_range", "not_all_members_saturated", "coverage",
                      "effective_coverage", "variance_invvar_reciprocity",
                      "intersection_of_upstream_physical_support"],
            "circular_or_radial_masks": 0,
            "data_derived_saturation_reliability_taper": {
                "enabled": saturation_taper_width > 0,
                "width_px": saturation_taper_width,
                "exponent": saturation_taper_exponent,
                "basis": "upstream all-members-saturated support only",
                "free_radial_or_circular_mask": False,
            },
            "qa": hdr_qa,
        },
        "photometric_harmonization": photometric,
        "natural": {
            "branch": "NATURAL",
            "config": natural_config,
            "qa": natural_qa,
            "photometric_authority": False,
            "scientific_authority": "VIXEN_HDR_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif",
        },
        "qa": {
            "clipping": {
                "max_high_clip_fraction": max_high_clip,
                "max_positive_to_black_fraction": max_black,
                "pass": clipping_pass,
            },
            "monotonic_tone": {"pass": monotonic_pass},
            "anti_ring": ring_qa,
            "pass": overall_pass,
        },
        "extensions": {
            "sony": {
                "status": "NOT_IMPLEMENTED_NO_ACCEPTED_CROSS_TRAIN_TRANSFORM",
                "dataset_solar_radius_px_reserved": SONY_SOLAR_RADIUS_PX,
            },
            "earthshine": {
                "status": "NOT_IMPLEMENTED_NO_ACCEPTED_LUNAR_TRANSFORM",
                "radius_policy": "physical lunar radius; never solar radius",
            },
        },
        "outputs": output_records,
        "source_mutations": 0,
    }
    receipt_path = staging / "COMPOSITE_RECEIPT.json"
    atomic_json(receipt_path, receipt)
    sums_path = staging / "SHA256SUMS.txt"
    with sums_path.open("w", encoding="utf-8") as handle:
        for path in sorted(staging.iterdir(), key=lambda item: item.name):
            if path.is_file() and path.name != sums_path.name:
                handle.write(f"{sha256(path)}  {path.name}\n")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    os.rename(staging, output_dir)
    print(f"{verdict}: {output_dir}", flush=True)
    return 0 if overall_pass else 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compositor Vixen HDR + NATURAL; només rebuts upstream amb "
            "veredicte literal ACCEPTAT"
        )
    )
    parser.add_argument("--manifest", type=Path, required=True,
                        help="manifest JSON ECLIPSE_NATURAL_COMPOSITE_V1")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="directori nou; mai no se sobreescriu")
    parser.add_argument("--validate-only", action="store_true",
                        help="valida contractes i hashes sense escriure cap sortida")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return build(args.manifest, args.output_dir, args.validate_only)
    except ContractError as exc:
        print(f"ERROR DE CONTRACTE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
