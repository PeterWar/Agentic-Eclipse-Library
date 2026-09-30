#!/usr/bin/env python3
"""Build a restrained, reversible Vixen presentation-detail layer.

This stage is deliberately **not scientific**.  It consumes only the accepted
``vixen_natural_stable_v5`` composite and makes a full-canvas RGB/16 Adobe RGB
candidate for a low-opacity Photoshop *Normal* layer.  The candidate equals
the immutable NATURAL base where the detail gain is one; a 50-percent-grey
image would not be neutral under Normal blending and is therefore forbidden.

The sole local operation is a luminance-only residual in log space::

    local = Gaussian(log(Y) * support) / Gaussian(support)
    gain  = clip(exp(strength * (log(Y) - local)), 0.9, 1.1)
    detail_rgb = base_rgb * gain

The Gaussian is normalized by valid support, so missing pixels cannot darken
the estimate at an edge.  Chroma is preserved by one scalar gain per pixel.
There is no MGN, NRGF, denoise, radial normalization, radial blend, free field
mask or spatially varying strength.  The only mask gates are receipt-hashed
physical support and the union of upstream lunar interiors at the physical
radius 453.8 px.

Request schema (paths are relative to the request manifest)::

  {
    "schema": "ECLIPSE_GENTLE_DETAIL_REQUEST_V1",
    "base": {
      "receipt": "../composites/vixen_natural_stable_v5/COMPOSITE_RECEIPT.json",
      "receipt_sha256": "<64 lowercase hex>"
    },
    "processing": {
      "gaussian_sigma_px": 24.0,
      "detail_strength": 0.16,
      "gain_bounds": [0.9, 1.1],
      "lunar_physical_radius_px": 453.8,
      "recommended_opacity_255": 48,
      "chunk_rows": 128
    }
  }

The program never overwrites its destination.  All input receipts and files
are hash-checked before staging is created; promotion is one atomic rename.
Use ``--self-test`` for synthetic tests or ``--validate-only`` for a real,
read-only contract/hash validation.  A normal invocation performs the build.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import tifffile
from PIL import Image, ImageCms
from scipy import ndimage


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import build_natural_composite as N  # noqa: E402


REQUEST_SCHEMA = "ECLIPSE_GENTLE_DETAIL_REQUEST_V1"
RECEIPT_SCHEMA = "ECLIPSE_GENTLE_DETAIL_RECEIPT_V1"
BASE_RECEIPT_SCHEMA = "ECLIPSE_NATURAL_COMPOSITE_RECEIPT_V1"
CLASSIFICATION = "DETALL_PRESENTACIONAL_NO_CIENTIFIC"
FRAME = "CORONA_SOLAR_VIXEN_COMMON_GRID"
EXPECTED_BASE_DIRECTORY = "vixen_natural_stable_v5"
EXPECTED_SHAPE = (4640, 6960, 3)
PHYSICAL_LUNAR_RADIUS_PX = 453.8
GAIN_MIN = 0.9
GAIN_MAX = 1.1
DEFAULT_SIGMA_PX = 24.0
DEFAULT_STRENGTH = 0.16
DEFAULT_OPACITY_255 = 48
MAX_DELIVERY_OPACITY_255 = 96
LINEAR_ICC = N.adobe_rgb_icc(1.0)
ENCODED_ICC = N.adobe_rgb_icc(N.ADOBE_GAMMA)

PRODUCT_NAMES = {
    "image": "GENTLE_DETAIL_NORMAL_ADOBERGB16.tif",
    "mask": "GENTLE_DETAIL_MASK16.tif",
    "icc": "AdobeRGB1998.icc",
    "preview": "PREVIEW_GENTLE_DETAIL_NORMAL_sRGB.png",
    "receipt": "RECEIPT.json",
    "sha256sums": "SHA256SUMS.txt",
}


class ContractError(RuntimeError):
    """A fail-closed input or processing contract was violated."""


@dataclass(frozen=True)
class Product:
    role: str
    name: str
    path: Path
    sha256: str
    bytes: int


@dataclass(frozen=True)
class LunarAuthority:
    authority_path: Path
    authority_sha256: str
    stack_path: Path
    stack_sha256: str
    members: tuple[str, ...]
    center_xy: tuple[float, float]


@dataclass(frozen=True)
class Config:
    sigma_px: float
    strength: float
    opacity_255: int
    chunk_rows: int


@dataclass(frozen=True)
class Inputs:
    manifest_path: Path
    manifest: dict[str, Any]
    receipt_path: Path
    receipt_sha256: str
    receipt: dict[str, Any]
    natural: Product
    support: Product
    icc: Product
    shape: tuple[int, int, int]
    solar_center_xy: tuple[float, float]
    solar_radius_px: float
    lunar_authorities: tuple[LunarAuthority, ...]
    config: Config


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"No es pot llegir JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} no conté un objecte JSON")
    return value


def write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def resolve_path(manifest_path: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ContractError(f"{label} ha de ser una ruta no buida")
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    return candidate.resolve()


def assert_workspace_path(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"{label} ha d'estar dins el worktree canònic: {path}") from exc


def strict_digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractError(f"{label} ha de ser un SHA-256 hexadecimal minúscul")
    return value


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} ha de ser numèric")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} ha de ser finit")
    return result


def product_index(receipt: dict[str, Any], receipt_path: Path) -> dict[str, dict[str, Any]]:
    records = receipt.get("outputs")
    if not isinstance(records, list) or not records:
        raise ContractError(f"{receipt_path}: falta outputs")
    result: dict[str, dict[str, Any]] = {}
    for ordinal, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContractError(f"{receipt_path}: outputs[{ordinal}] no és objecte")
        role = record.get("role")
        name = record.get("name")
        digest = record.get("sha256")
        size = record.get("bytes")
        if not isinstance(role, str) or not role or role in result:
            raise ContractError(f"{receipt_path}: role invàlid o duplicat {role!r}")
        if not isinstance(name, str) or not name or Path(name).name != name:
            raise ContractError(f"{receipt_path}: nom de producte insegur {name!r}")
        strict_digest(digest, f"{receipt_path}:{name}.sha256")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise ContractError(f"{receipt_path}: mida invàlida per {name}")
        result[role] = record
    return result


def resolve_product(
    receipt_path: Path, index: dict[str, dict[str, Any]], role: str
) -> Product:
    record = index.get(role)
    if record is None:
        raise ContractError(f"{receipt_path}: falta producte role={role!r}")
    path = (receipt_path.parent / record["name"]).resolve()
    if path.parent != receipt_path.parent.resolve() or not path.is_file():
        raise ContractError(f"producte absent o fora del directori del rebut: {path}")
    actual_size = path.stat().st_size
    actual_hash = sha256(path)
    if actual_size != record["bytes"] or actual_hash != record["sha256"]:
        raise ContractError(f"hash/mida divergent del producte {role}: {path}")
    return Product(role, record["name"], path, actual_hash, actual_size)


def tiff_metadata(path: Path) -> tuple[tuple[int, ...], np.dtype[Any], bytes | None]:
    try:
        with tifffile.TiffFile(path) as document:
            page = document.pages[0]
            shape = tuple(int(value) for value in page.shape)
            dtype = np.dtype(page.dtype)
            tag = page.tags.get(34675)
            icc = bytes(tag.value) if tag is not None else None
    except Exception as exc:
        raise ContractError(f"TIFF invàlid {path}: {exc}") from exc
    return shape, dtype, icc


def parse_config(manifest: dict[str, Any]) -> Config:
    raw = manifest.get("processing", {})
    if not isinstance(raw, dict):
        raise ContractError("processing ha de ser un objecte")
    allowed = {
        "gaussian_sigma_px",
        "detail_strength",
        "gain_bounds",
        "lunar_physical_radius_px",
        "recommended_opacity_255",
        "chunk_rows",
    }
    extra = set(raw) - allowed
    if extra:
        raise ContractError(f"processing conté camps no admesos: {sorted(extra)}")
    sigma = finite_number(raw.get("gaussian_sigma_px", DEFAULT_SIGMA_PX), "gaussian_sigma_px")
    strength = finite_number(raw.get("detail_strength", DEFAULT_STRENGTH), "detail_strength")
    radius = finite_number(
        raw.get("lunar_physical_radius_px", PHYSICAL_LUNAR_RADIUS_PX),
        "lunar_physical_radius_px",
    )
    gain_bounds = raw.get("gain_bounds", [GAIN_MIN, GAIN_MAX])
    if not isinstance(gain_bounds, list) or len(gain_bounds) != 2:
        raise ContractError("gain_bounds ha de ser [0.9, 1.1]")
    gain_lo = finite_number(gain_bounds[0], "gain_bounds[0]")
    gain_hi = finite_number(gain_bounds[1], "gain_bounds[1]")
    opacity = raw.get("recommended_opacity_255", DEFAULT_OPACITY_255)
    chunk_rows = raw.get("chunk_rows", 128)
    if not 12.0 <= sigma <= 64.0:
        raise ContractError("gaussian_sigma_px ha d'estar entre 12 i 64 px")
    if not 0.0 < strength <= 0.20:
        raise ContractError("detail_strength ha de ser >0 i <=0.20")
    if abs(gain_lo - GAIN_MIN) > 1e-12 or abs(gain_hi - GAIN_MAX) > 1e-12:
        raise ContractError("gain_bounds queda fixat a [0.9, 1.1]")
    if abs(radius - PHYSICAL_LUNAR_RADIUS_PX) > 1e-9:
        raise ContractError("el radi lunar físic queda fixat a 453.8 px")
    if isinstance(opacity, bool) or not isinstance(opacity, int) or not 1 <= opacity <= 64:
        raise ContractError("recommended_opacity_255 ha de ser un enter entre 1 i 64")
    if isinstance(chunk_rows, bool) or not isinstance(chunk_rows, int) or not 16 <= chunk_rows <= 512:
        raise ContractError("chunk_rows ha de ser un enter entre 16 i 512")
    return Config(sigma, strength, opacity, chunk_rows)


def validate_lunar_authorities(receipt: dict[str, Any]) -> tuple[LunarAuthority, ...]:
    records = receipt.get("inputs")
    if not isinstance(records, list) or len(records) != 8:
        raise ContractError("vixen_natural_stable_v5 ha de declarar els 8 màsters STABLE")
    accepted_root = (
        ROOT
        / "output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED"
        / "accepted_stacks/corona/STABLE"
    ).resolve()
    result: list[LunarAuthority] = []
    all_members: list[str] = []
    for ordinal, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContractError(f"inputs[{ordinal}] no és objecte")
        raw_path = record.get("receipt")
        if not isinstance(raw_path, str):
            raise ContractError(f"inputs[{ordinal}].receipt invàlid")
        authority_path = Path(raw_path).expanduser().resolve()
        assert_workspace_path(authority_path, f"inputs[{ordinal}].receipt")
        try:
            authority_path.relative_to(accepted_root)
        except ValueError as exc:
            raise ContractError(f"autoritat Vixen fora de STABLE ACCEPTED: {authority_path}") from exc
        if authority_path.name != "AUTHORITY_RECEIPT.json" or not authority_path.is_file():
            raise ContractError(f"autoritat Vixen absent/invàlida: {authority_path}")
        expected_authority = strict_digest(
            record.get("receipt_sha256"), f"inputs[{ordinal}].receipt_sha256"
        )
        actual_authority = sha256(authority_path)
        if actual_authority != expected_authority:
            raise ContractError(f"SHA-256 divergent de l'autoritat: {authority_path}")
        authority = read_json(authority_path)
        if (
            authority.get("schema") != "VIXEN_R6_S6_GROUP_AUTHORITY_V1"
            or authority.get("verdict") != "ACCEPTAT"
            or authority.get("temporal_segment") != "STABLE"
            or authority.get("phenomenon_scope") != "CORONA_SOLAR"
        ):
            raise ContractError(f"autoritat STABLE no acceptada: {authority_path}")
        members_raw = record.get("members")
        if not isinstance(members_raw, list) or not all(
            isinstance(member, str) and member for member in members_raw
        ):
            raise ContractError(f"membres invàlids a inputs[{ordinal}]")
        members = tuple(members_raw)
        if authority.get("members") != list(members):
            raise ContractError(f"membres divergents a {authority_path}")
        all_members.extend(members)

        stack_path = authority_path.parent / "STACK_RECEIPT.json"
        expected_stack = strict_digest(
            authority.get("upstream_receipt_sha256"),
            f"{authority_path}.upstream_receipt_sha256",
        )
        if not stack_path.is_file() or sha256(stack_path) != expected_stack:
            raise ContractError(f"STACK_RECEIPT no coincideix amb l'autoritat: {stack_path}")
        stack = read_json(stack_path)
        # The immutable pixel receipt predates promotion and therefore keeps
        # its historical ``temporal_segment=all`` label.  Only the hash-anchored
        # authority above may promote that exact member set to STABLE.
        if stack.get("members") != list(members):
            raise ContractError(f"membres divergents a {stack_path}")
        lunar = stack.get("stack_info", {}).get("corona_lunar_no_data", {})
        center = lunar.get("centre_output_px")
        if not isinstance(center, list) or len(center) != 2:
            raise ContractError(f"falta centre lunar mesurat a {stack_path}")
        center_xy = (
            finite_number(center[0], f"{stack_path}.lunar_x"),
            finite_number(center[1], f"{stack_path}.lunar_y"),
        )
        exclusion = finite_number(
            lunar.get("exclusion_radius_px"), f"{stack_path}.exclusion_radius_px"
        )
        if exclusion < PHYSICAL_LUNAR_RADIUS_PX:
            raise ContractError(f"suport upstream no cobreix el radi lunar físic: {stack_path}")
        result.append(
            LunarAuthority(
                authority_path,
                actual_authority,
                stack_path,
                expected_stack,
                members,
                center_xy,
            )
        )
    if len(all_members) != len(set(all_members)):
        raise ContractError("els 8 màsters STABLE comparteixen membres inesperadament")
    return tuple(result)


def load_inputs(manifest_path: Path) -> Inputs:
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise ContractError(f"falta manifest: {manifest_path}")
    assert_workspace_path(manifest_path, "manifest")
    manifest = read_json(manifest_path)
    if manifest.get("schema") != REQUEST_SCHEMA:
        raise ContractError(f"schema invàlid; cal {REQUEST_SCHEMA}")
    allowed = {"schema", "base", "processing"}
    extra = set(manifest) - allowed
    if extra:
        raise ContractError(f"manifest conté camps no admesos: {sorted(extra)}")
    base = manifest.get("base")
    if not isinstance(base, dict) or set(base) != {"receipt", "receipt_sha256"}:
        raise ContractError("base ha de contenir exactament receipt i receipt_sha256")
    receipt_path = resolve_path(manifest_path, base["receipt"], "base.receipt")
    assert_workspace_path(receipt_path, "base.receipt")
    if receipt_path.parent.name != EXPECTED_BASE_DIRECTORY or receipt_path.name != "COMPOSITE_RECEIPT.json":
        raise ContractError("la font ha de ser literalment vixen_natural_stable_v5/COMPOSITE_RECEIPT.json")
    expected_receipt = strict_digest(base["receipt_sha256"], "base.receipt_sha256")
    if not receipt_path.is_file():
        raise ContractError(f"falta rebut base: {receipt_path}")
    receipt_hash = sha256(receipt_path)
    if receipt_hash != expected_receipt:
        raise ContractError("SHA-256 divergent del COMPOSITE_RECEIPT base")
    receipt = read_json(receipt_path)
    if (
        receipt.get("schema") != BASE_RECEIPT_SCHEMA
        or receipt.get("verdict") != "ACCEPTAT"
        or receipt.get("stage") != "VIXEN_HDR_AND_NATURAL_PRESENTATION"
        or receipt.get("qa", {}).get("pass") is not True
        or receipt.get("temporal_selection", {}).get("selected_segment") != "STABLE"
        or receipt.get("source_mutations") != 0
    ):
        raise ContractError("COMPOSITE_RECEIPT v5 no és una autoritat STABLE ACCEPTAT immutable")
    if receipt.get("natural", {}).get("photometric_authority") is not False:
        raise ContractError("la branca NATURAL s'ha de declarar no fotomètrica")
    if receipt.get("hdr", {}).get("circular_or_radial_masks") != 0:
        raise ContractError("la base v5 declara màscares circulars/radials")
    absent = set(receipt.get("natural", {}).get("config", {}).get("operations_absent", []))
    if not {"radial_mask", "MGN", "NRGF", "local_contrast", "denoise"}.issubset(absent):
        raise ContractError("la base v5 no demostra l'absència d'operacions locals prohibides")
    if receipt.get("natural", {}).get("config", {}).get("global_curve", {}).get(
        "spatial_or_radial_dependency"
    ) is not False:
        raise ContractError("la corba NATURAL base no és global")
    base_ring = receipt.get("qa", {}).get("anti_ring", {})
    if (
        base_ring.get("pass") is not True
        or float(base_ring.get("natural", {}).get("r_max_rsun", 0.0)) < 8.5
    ):
        raise ContractError("la base v5 no aporta una porta anti-anell PASS fins a 8.5 R_sun")

    geometry = receipt.get("geometry", {})
    shape_raw = geometry.get("shape_yxc")
    if shape_raw != list(EXPECTED_SHAPE):
        raise ContractError(f"geometria base inesperada: {shape_raw}")
    center = geometry.get("solar_center_xy_px")
    if not isinstance(center, list) or len(center) != 2:
        raise ContractError("falta centre solar base")
    center_xy = (
        finite_number(center[0], "solar_center_x"),
        finite_number(center[1], "solar_center_y"),
    )
    solar_radius = finite_number(geometry.get("solar_radius_px"), "solar_radius_px")
    if abs(solar_radius - N.VIXEN_SOLAR_RADIUS_PX) > 1e-9:
        raise ContractError("la base no usa R_sun=946.6598/2.1495")

    products = product_index(receipt, receipt_path)
    natural = resolve_product(receipt_path, products, "natural_linear")
    support = resolve_product(receipt_path, products, "valid_pixels")
    icc = resolve_product(receipt_path, products, "icc")
    natural_shape, natural_dtype, natural_icc = tiff_metadata(natural.path)
    support_shape, support_dtype, _ = tiff_metadata(support.path)
    if natural_shape != EXPECTED_SHAPE or natural_dtype != np.dtype(np.float32):
        raise ContractError("NATURAL_LINEAR ha de ser RGB float32 al llenç Vixen natiu")
    if natural_icc != LINEAR_ICC:
        raise ContractError("NATURAL_LINEAR no porta el perfil Adobe RGB lineal pinat")
    if support_shape != EXPECTED_SHAPE[:2] or support_dtype != np.dtype(np.uint8):
        raise ContractError("HDR_VALID_PIXELS ha de ser uint8 al llenç Vixen natiu")
    if icc.path.read_bytes() != ENCODED_ICC:
        raise ContractError("AdobeRGB1998.icc divergent del perfil codificat pinat")

    lunar = validate_lunar_authorities(receipt)
    config = parse_config(manifest)
    return Inputs(
        manifest_path,
        manifest,
        receipt_path,
        receipt_hash,
        receipt,
        natural,
        support,
        icc,
        EXPECTED_SHAPE,
        center_xy,
        solar_radius,
        lunar,
        config,
    )


def lunar_interior_chunk(
    y0: int,
    y1: int,
    width: int,
    centers: Iterable[tuple[float, float]],
    radius_px: float = PHYSICAL_LUNAR_RADIUS_PX,
) -> np.ndarray:
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(width, dtype=np.float32)[None, :]
    result = np.zeros((y1 - y0, width), dtype=bool)
    radius2 = radius_px * radius_px
    for center_x, center_y in centers:
        result |= (xx - center_x) ** 2 + (yy - center_y) ** 2 <= radius2
    return result


def normalized_gaussian(
    log_luminance: np.ndarray, support: np.ndarray, sigma_px: float
) -> tuple[np.ndarray, np.ndarray]:
    weights = np.asarray(support, dtype=np.float32)
    numerator = ndimage.gaussian_filter(
        np.asarray(log_luminance, dtype=np.float32) * weights,
        sigma=sigma_px,
        mode="constant",
        cval=0.0,
        truncate=4.0,
    )
    denominator = ndimage.gaussian_filter(
        weights, sigma=sigma_px, mode="constant", cval=0.0, truncate=4.0
    )
    local = np.zeros_like(numerator)
    np.divide(numerator, denominator, out=local, where=denominator > 1e-6)
    return local, denominator


def create_tiff_memmap(
    path: Path,
    shape: tuple[int, ...],
    dtype: Any,
    description: dict[str, Any],
    *,
    icc: bytes | None = None,
) -> np.memmap:
    extratags: list[tuple[Any, ...]] = []
    if icc is not None:
        extratags.append((34675, 7, len(icc), icc, False))
    return tifffile.memmap(
        path,
        shape=shape,
        dtype=dtype,
        photometric="rgb" if len(shape) == 3 else "minisblack",
        bigtiff=(np.prod(shape, dtype=np.int64) * np.dtype(dtype).itemsize) > (3 << 30),
        metadata=None,
        description=json.dumps(description, ensure_ascii=False, separators=(",", ":")),
        software="build_gentle_detail_layer.py",
        resolution=(300, 300),
        extratags=extratags,
    )


def make_support_and_log(
    inputs: Inputs, work: Path
) -> tuple[dict[str, Path], int, int]:
    height, width, _ = inputs.shape
    paths = {
        "log": work / "log_luminance_float32.npy",
        "weights": work / "support_float32.npy",
        "weighted": work / "weighted_log_float32.npy",
        "blur_num": work / "blurred_numerator_float32.npy",
        "blur_den": work / "blurred_denominator_float32.npy",
        "gain": work / "gain_float32.npy",
    }
    log_luma = np.lib.format.open_memmap(paths["log"], mode="w+", dtype=np.float32, shape=(height, width))
    weights = np.lib.format.open_memmap(paths["weights"], mode="w+", dtype=np.float32, shape=(height, width))
    weighted = np.lib.format.open_memmap(paths["weighted"], mode="w+", dtype=np.float32, shape=(height, width))
    natural = tifffile.memmap(inputs.natural.path, mode="r")
    support_source = tifffile.memmap(inputs.support.path, mode="r")
    centers = [entry.center_xy for entry in inputs.lunar_authorities]
    supported_count = 0
    lunar_source_nonzero = 0
    for y0 in range(0, height, inputs.config.chunk_rows):
        y1 = min(height, y0 + inputs.config.chunk_rows)
        rgb = np.asarray(natural[y0:y1], dtype=np.float32)
        luma = rgb @ N.ADOBE_LUMA.astype(np.float32)
        lunar = lunar_interior_chunk(y0, y1, width, centers)
        upstream = np.asarray(support_source[y0:y1], dtype=bool)
        valid = upstream & np.all(np.isfinite(rgb), axis=2) & np.all(rgb >= 0.0, axis=2)
        valid &= np.isfinite(luma) & (luma > 1e-8) & ~lunar
        lunar_source_nonzero += int(np.count_nonzero(upstream & lunar))
        chunk_log = np.zeros(luma.shape, dtype=np.float32)
        chunk_log[valid] = np.log(luma[valid])
        log_luma[y0:y1] = chunk_log
        weights[y0:y1] = valid.astype(np.float32)
        weighted[y0:y1] = chunk_log * valid
        supported_count += int(np.count_nonzero(valid))
    for array in (log_luma, weights, weighted):
        array.flush()
    if supported_count < height * width // 2:
        raise ContractError(f"suport útil insuficient: {supported_count} píxels")
    del natural, support_source, log_luma, weights, weighted

    weighted = np.load(paths["weighted"], mmap_mode="r")
    weights = np.load(paths["weights"], mmap_mode="r")
    blur_num = np.lib.format.open_memmap(paths["blur_num"], mode="w+", dtype=np.float32, shape=(height, width))
    blur_den = np.lib.format.open_memmap(paths["blur_den"], mode="w+", dtype=np.float32, shape=(height, width))
    ndimage.gaussian_filter(
        weighted,
        sigma=inputs.config.sigma_px,
        output=blur_num,
        mode="constant",
        cval=0.0,
        truncate=4.0,
    )
    ndimage.gaussian_filter(
        weights,
        sigma=inputs.config.sigma_px,
        output=blur_den,
        mode="constant",
        cval=0.0,
        truncate=4.0,
    )
    blur_num.flush()
    blur_den.flush()
    del weighted, weights, blur_num, blur_den
    return paths, supported_count, lunar_source_nonzero


def encode_adobe(linear: np.ndarray) -> np.ndarray:
    encoded = np.power(np.clip(linear, 0.0, 1.0), 1.0 / N.ADOBE_GAMMA)
    return np.floor(encoded * 65535.0 + 0.5).astype(np.uint16)


def build_products(inputs: Inputs, staging: Path, work: Path) -> tuple[dict[str, Path], dict[str, Any]]:
    height, width, _ = inputs.shape
    scratch, supported_count, lunar_source_nonzero = make_support_and_log(inputs, work)
    paths = {
        "image": staging / PRODUCT_NAMES["image"],
        "mask": staging / PRODUCT_NAMES["mask"],
        "icc": staging / PRODUCT_NAMES["icc"],
        "preview_srgb": staging / PRODUCT_NAMES["preview"],
    }
    paths["icc"].write_bytes(ENCODED_ICC)
    image = create_tiff_memmap(
        paths["image"],
        inputs.shape,
        np.uint16,
        {
            "class": CLASSIFICATION,
            "space": "Adobe RGB (1998)",
            "linear": False,
            "trc_gamma": N.ADOBE_GAMMA,
            "blend_mode": "Normal",
            "neutral_semantics": "candidate equals immutable base when gain=1",
        },
        icc=ENCODED_ICC,
    )
    mask = create_tiff_memmap(
        paths["mask"],
        (height, width),
        np.uint16,
        {
            "class": CLASSIFICATION,
            "mask": "receipt-hashed physical support minus physical lunar interiors",
            "free_radial_or_field_mask": False,
        },
    )
    gain_map = np.lib.format.open_memmap(
        scratch["gain"], mode="w+", dtype=np.float32, shape=(height, width)
    )
    natural = tifffile.memmap(inputs.natural.path, mode="r")
    log_luma = np.load(scratch["log"], mmap_mode="r")
    weights = np.load(scratch["weights"], mmap_mode="r")
    blur_num = np.load(scratch["blur_num"], mmap_mode="r")
    blur_den = np.load(scratch["blur_den"], mmap_mode="r")
    centers = [entry.center_xy for entry in inputs.lunar_authorities]

    gain_min_seen = math.inf
    gain_max_seen = -math.inf
    low_clamped = 0
    high_clamped = 0
    headroom_capped = 0
    outside_identity_mismatches = 0
    lunar_mask_nonzero = 0
    new_high_clip = 0
    sampled_gain: list[np.ndarray] = []
    # Keep the encoded layer below the 65535 clipping code where the base was
    # not clipped.  This is slightly more conservative than a mathematical 1.
    safe_linear_max = float(((65534.49 / 65535.0) ** N.ADOBE_GAMMA))

    for y0 in range(0, height, inputs.config.chunk_rows):
        y1 = min(height, y0 + inputs.config.chunk_rows)
        rgb = np.asarray(natural[y0:y1], dtype=np.float32)
        active = np.asarray(weights[y0:y1] > 0.5)
        local = np.zeros(active.shape, dtype=np.float32)
        denominator = np.asarray(blur_den[y0:y1], dtype=np.float32)
        np.divide(
            np.asarray(blur_num[y0:y1], dtype=np.float32),
            denominator,
            out=local,
            where=denominator > 1e-6,
        )
        residual = np.asarray(log_luma[y0:y1], dtype=np.float32) - local
        raw_gain = np.exp(inputs.config.strength * residual, dtype=np.float32)
        low_clamped += int(np.count_nonzero(active & (raw_gain < GAIN_MIN)))
        high_clamped += int(np.count_nonzero(active & (raw_gain > GAIN_MAX)))
        gain = np.clip(raw_gain, GAIN_MIN, GAIN_MAX)
        positive = rgb > 0.0
        per_channel_headroom = np.full(rgb.shape, np.inf, dtype=np.float32)
        np.divide(safe_linear_max, rgb, out=per_channel_headroom, where=positive)
        headroom = np.min(per_channel_headroom, axis=2)
        capped = active & (gain > headroom)
        headroom_capped += int(np.count_nonzero(capped))
        gain = np.minimum(gain, headroom)
        gain[~active] = 1.0
        candidate = rgb * gain[..., None]
        candidate[~active] = rgb[~active]
        encoded_base = encode_adobe(rgb)
        encoded_candidate = encode_adobe(candidate)
        chunk_mask = np.where(active, np.uint16(65535), np.uint16(0))
        lunar = lunar_interior_chunk(y0, y1, width, centers)
        lunar_mask_nonzero += int(np.count_nonzero(chunk_mask[lunar]))
        outside_identity_mismatches += int(
            np.count_nonzero(encoded_candidate[~active] != encoded_base[~active])
        )
        new_high_clip += int(
            np.count_nonzero((encoded_candidate == 65535) & (encoded_base < 65535))
        )
        image[y0:y1] = encoded_candidate
        mask[y0:y1] = chunk_mask
        gain_map[y0:y1] = gain
        selected_gain = gain[active]
        if selected_gain.size:
            gain_min_seen = min(gain_min_seen, float(np.min(selected_gain)))
            gain_max_seen = max(gain_max_seen, float(np.max(selected_gain)))
            sampled_gain.append(gain[::8, ::8][active[::8, ::8]].astype(np.float32))
    for array in (image, mask, gain_map):
        array.flush()
    del image, mask, gain_map, natural, log_luma, weights, blur_num, blur_den

    sample = np.concatenate(sampled_gain) if sampled_gain else np.asarray([], np.float32)
    if sample.size == 0:
        raise ContractError("cap mostra de guany vàlida")
    qa = {
        "support_pixels": supported_count,
        "upstream_support_zero_inside_physical_lunar_union": (
            lunar_source_nonzero == 0
        ),
        "upstream_support_nonzero_inside_physical_lunar_union": lunar_source_nonzero,
        "gain_min": gain_min_seen,
        "gain_max": gain_max_seen,
        "gain_percentiles_sampled_0_1_50_99_100": [
            float(value) for value in np.percentile(sample, [0, 1, 50, 99, 100])
        ],
        "raw_low_clamped_pixels": low_clamped,
        "raw_high_clamped_pixels": high_clamped,
        "headroom_capped_pixels": headroom_capped,
        "new_high_clip_channels": new_high_clip,
        "encoded_identity_mismatches_where_mask_zero": outside_identity_mismatches,
        "mask_nonzero_inside_physical_lunar_union": lunar_mask_nonzero,
        "scalar_rgb_gain_chroma_preserved_by_construction": True,
        "gain_bounds_pass": gain_min_seen >= GAIN_MIN - 2e-6 and gain_max_seen <= GAIN_MAX + 2e-6,
        "lunar_exclusion_pass": lunar_mask_nonzero == 0,
        "neutral_outside_mask_pass": outside_identity_mismatches == 0,
        "new_clipping_pass": new_high_clip == 0,
    }
    return paths, qa


def scan_blend(
    inputs: Inputs,
    image_path: Path,
    mask_path: Path,
    opacity_255: int,
) -> dict[str, Any]:
    stride = 2
    base = tifffile.memmap(inputs.natural.path, mode="r")
    candidate = tifffile.memmap(image_path, mode="r")
    mask = tifffile.memmap(mask_path, mode="r")
    base_linear = np.asarray(base[::stride, ::stride], dtype=np.float32)
    candidate_encoded = np.asarray(candidate[::stride, ::stride], dtype=np.float32) / 65535.0
    sampled_mask = np.asarray(mask[::stride, ::stride], dtype=np.float32) / 65535.0
    base_encoded = np.power(np.clip(base_linear, 0.0, 1.0), 1.0 / N.ADOBE_GAMMA)
    alpha = sampled_mask * (opacity_255 / 255.0)
    blended_encoded = (
        base_encoded * (1.0 - alpha[..., None])
        + candidate_encoded * alpha[..., None]
    )
    blended_linear = np.power(np.clip(blended_encoded, 0.0, 1.0), N.ADOBE_GAMMA)
    base_luma = base_linear @ N.ADOBE_LUMA.astype(np.float32)
    blended_luma = blended_linear @ N.ADOBE_LUMA.astype(np.float32)
    valid = sampled_mask > 0.0
    common_args = (
        valid,
        inputs.solar_center_xy,
        inputs.solar_radius_px,
        stride,
        4.0,
        5.0,
        1.15,
        8.5,
        0.08,
        0.01,
        12,
    )
    base_scan = N.annular_ring_scan(base_luma, *common_args)
    blend_scan = N.annular_ring_scan(blended_luma, *common_args)
    base_radii = [item["radius_px"] for item in base_scan["candidates"]]
    new_blend = [
        item
        for item in blend_scan["candidates"]
        if not any(abs(item["radius_px"] - radius) <= 4.0 for radius in base_radii)
    ]
    effect = np.ones_like(base_luma, dtype=np.float32)
    good = valid & np.isfinite(base_luma) & (base_luma > 1e-8)
    effect[good] = blended_luma[good] / base_luma[good]
    effect_scan = N.annular_ring_scan(
        effect,
        good,
        inputs.solar_center_xy,
        inputs.solar_radius_px,
        stride,
        4.0,
        5.0,
        1.15,
        8.5,
        0.08,
        0.005,
        12,
    )
    del base, candidate, mask
    return {
        "opacity_255": opacity_255,
        "blend_mode": "Normal in encoded Adobe RGB (Photoshop-compatible model)",
        "base": base_scan,
        "blended": blend_scan,
        "new_blended_candidate_count": len(new_blend),
        "new_blended_candidates": new_blend[:32],
        "effect_factor": effect_scan,
        "pass": len(new_blend) == 0 and effect_scan["candidate_count"] == 0,
    }


def save_preview(
    inputs: Inputs, image_path: Path, mask_path: Path, output_path: Path
) -> dict[str, Any]:
    max_dimension = 1800
    height, width, _ = inputs.shape
    stride = max(1, int(math.ceil(max(height, width) / max_dimension)))
    base = tifffile.memmap(inputs.natural.path, mode="r")
    candidate = tifffile.memmap(image_path, mode="r")
    mask = tifffile.memmap(mask_path, mode="r")
    base_linear = np.asarray(base[::stride, ::stride], dtype=np.float32)
    base_encoded = np.power(np.clip(base_linear, 0.0, 1.0), 1.0 / N.ADOBE_GAMMA)
    candidate_encoded = np.asarray(candidate[::stride, ::stride], dtype=np.float32) / 65535.0
    alpha = (
        np.asarray(mask[::stride, ::stride], dtype=np.float32)
        / 65535.0
        * (inputs.config.opacity_255 / 255.0)
    )
    preview_adobe = (
        base_encoded * (1.0 - alpha[..., None])
        + candidate_encoded * alpha[..., None]
    )
    adobe8 = np.floor(np.clip(preview_adobe, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    source = Image.fromarray(adobe8, mode="RGB")
    adobe_profile = ImageCms.ImageCmsProfile(io.BytesIO(ENCODED_ICC))
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    converted = ImageCms.profileToProfile(
        source, adobe_profile, srgb_profile, outputMode="RGB", renderingIntent=0
    )
    converted.save(output_path, icc_profile=srgb_profile.tobytes(), optimize=True)
    del base, candidate, mask
    return {
        "kind": "recommended low-opacity Normal blend; presentation preview only",
        "size_xy": list(converted.size),
        "source_stride": stride,
        "opacity_255": inputs.config.opacity_255,
        "color_space": "sRGB IEC61966-2.1",
    }


def output_records(paths: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "role": role,
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for role, path in sorted(paths.items())
    ]


def input_hash_anchors(inputs: Inputs) -> dict[Path, str]:
    result = {
        inputs.receipt_path: inputs.receipt_sha256,
        inputs.natural.path: inputs.natural.sha256,
        inputs.support.path: inputs.support.sha256,
        inputs.icc.path: inputs.icc.sha256,
    }
    for authority in inputs.lunar_authorities:
        result[authority.authority_path] = authority.authority_sha256
        result[authority.stack_path] = authority.stack_sha256
    return result


def verify_immutable(anchors: dict[Path, str]) -> None:
    changed = [str(path) for path, digest in anchors.items() if sha256(path) != digest]
    if changed:
        raise ContractError(f"fonts mutades durant el procés: {changed}")


def build(manifest_path: Path, output_dir: Path, validate_only: bool) -> int:
    output_dir = output_dir.expanduser().resolve()
    assert_workspace_path(output_dir, "output-dir")
    if output_dir.exists():
        raise ContractError(f"sortida ja existent; no se sobreescriu: {output_dir}")
    inputs = load_inputs(manifest_path)
    anchors = input_hash_anchors(inputs)
    if validate_only:
        print(
            json.dumps(
                {
                    "status": "VALIDATED_NO_WRITES",
                    "classification": CLASSIFICATION,
                    "manifest": str(inputs.manifest_path),
                    "manifest_sha256": sha256(inputs.manifest_path),
                    "base_receipt": str(inputs.receipt_path),
                    "base_receipt_sha256": inputs.receipt_sha256,
                    "natural_linear_sha256": inputs.natural.sha256,
                    "shape_yxc": list(inputs.shape),
                    "lunar_centers": [list(item.center_xy) for item in inputs.lunar_authorities],
                    "lunar_physical_radius_px": PHYSICAL_LUNAR_RADIUS_PX,
                    "would_write": str(output_dir),
                    "source_mutations": 0,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = output_dir.parent / (
        f".{output_dir.name}.partial-"
        f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    staging.mkdir(exist_ok=False)
    work = staging / ".work"
    work.mkdir()
    print(f"staging auditable: {staging}", flush=True)

    paths, pixel_qa = build_products(inputs, staging, work)
    ring_recommended = scan_blend(
        inputs,
        paths["image"],
        paths["mask"],
        inputs.config.opacity_255,
    )
    ring_max_delivery = scan_blend(
        inputs,
        paths["image"],
        paths["mask"],
        MAX_DELIVERY_OPACITY_255,
    )
    preview_qa = save_preview(
        inputs,
        paths["image"],
        paths["mask"],
        paths["preview_srgb"],
    )
    shutil.rmtree(work)
    verify_immutable(anchors)

    shape, dtype, embedded = tiff_metadata(paths["image"])
    mask_shape, mask_dtype, _ = tiff_metadata(paths["mask"])
    output_contract_pass = (
        shape == inputs.shape
        and dtype == np.dtype(np.uint16)
        and embedded == ENCODED_ICC
        and mask_shape == inputs.shape[:2]
        and mask_dtype == np.dtype(np.uint16)
    )
    overall_pass = (
        output_contract_pass
        and pixel_qa["gain_bounds_pass"]
        and pixel_qa["lunar_exclusion_pass"]
        and pixel_qa["neutral_outside_mask_pass"]
        and pixel_qa["new_clipping_pass"]
        and ring_recommended["pass"]
        and ring_max_delivery["pass"]
    )
    verdict = "ACCEPTAT" if overall_pass else "REPROCESSAR"
    products = output_records(paths)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stage": "GENTLE_PRESENTATION_DETAIL_LAYER",
        "verdict": verdict,
        "frame": FRAME,
        "method": "SINGLE_SIGMA_SUPPORT_NORMALIZED_LOG_LUMINANCE_GAUSSIAN",
        "classification": CLASSIFICATION,
        "photometric_authority": False,
        "scientific_authority": False,
        "scientific_feedback_forbidden": True,
        "manifest": {
            "path": str(inputs.manifest_path),
            "sha256": sha256(inputs.manifest_path),
            "schema": REQUEST_SCHEMA,
        },
        "software": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256(Path(__file__).resolve()),
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": getattr(sys.modules.get("scipy"), "__version__", None),
            "tifffile": tifffile.__version__,
            "argv": sys.argv,
            "reused_qa_module": {
                "path": str(Path(N.__file__).resolve()),
                "sha256": sha256(Path(N.__file__).resolve()),
                "function": "annular_ring_scan",
            },
        },
        "input_authority": {
            "base_receipt": str(inputs.receipt_path),
            "base_receipt_sha256": inputs.receipt_sha256,
            "base_verdict": inputs.receipt["verdict"],
            "base_directory_pinned": EXPECTED_BASE_DIRECTORY,
            "consumed_products": [
                {
                    "role": product.role,
                    "name": product.name,
                    "bytes": product.bytes,
                    "sha256": product.sha256,
                }
                for product in (inputs.natural, inputs.support, inputs.icc)
            ],
            "base_content_mutations": 0,
        },
        "base_natural": {
            "receipt": str(inputs.receipt_path),
            "receipt_sha256": inputs.receipt_sha256,
        },
        "geometry": {
            "shape_yxc": list(inputs.shape),
            "solar_center_xy_px": list(inputs.solar_center_xy),
            "solar_radius_px": inputs.solar_radius_px,
            "anti_ring_extent_rsun": 8.5,
            "frame": FRAME,
        },
        "lunar_exclusion": {
            "policy": "union of physical lunar interiors from all eight hash-anchored STABLE masters",
            "physical_radius_px": PHYSICAL_LUNAR_RADIUS_PX,
            "free_radial_or_field_mask": False,
            "authorities": [
                {
                    "authority_receipt": str(item.authority_path),
                    "authority_receipt_sha256": item.authority_sha256,
                    "stack_receipt": str(item.stack_path),
                    "stack_receipt_sha256": item.stack_sha256,
                    "members": list(item.members),
                    "lunar_center_xy_px": list(item.center_xy),
                }
                for item in inputs.lunar_authorities
            ],
        },
        "processing": {
            "algorithm": "support-normalized Gaussian residual of log Adobe-RGB luminance",
            "formula": "local=G(log(Y)*S)/G(S); gain=clip(exp(strength*(log(Y)-local)),0.9,1.1); RGB'=RGB*gain",
            "gaussian_sigma_px": inputs.config.sigma_px,
            "detail_strength": inputs.config.strength,
            "gain_bounds": [GAIN_MIN, GAIN_MAX],
            "luminance_weights": N.ADOBE_LUMA.tolist(),
            "normal_blend_candidate": True,
            "neutral_semantics": "full RGB candidate equals base when gain=1; grey is not neutral in Normal mode",
            "recommended_opacity_255": inputs.config.opacity_255,
            "maximum_validated_delivery_opacity_255": MAX_DELIVERY_OPACITY_255,
            "immutable_base_baked_or_modified": False,
            "operations_absent": [
                "MGN",
                "NRGF",
                "denoise",
                "radial_normalization",
                "radial_blend_mask",
                "free_field_mask",
                "spatially_varying_strength",
                "channel-wise_detail_gain",
            ],
        },
        "editable_delivery_contract": {
            "image_role": "image",
            "mask_role": "mask",
            "blend_mode": "Normal",
            "recommended_opacity_255": inputs.config.opacity_255,
            "insert_above": "immutable Vixen NATURAL base",
            "insert_below": "protected C2/C3 contact and earthshine layers",
        },
        "qa": {
            "pixels": pixel_qa,
            "output_contract_pass": output_contract_pass,
            "anti_ring_recommended_opacity": ring_recommended,
            "anti_ring_maximum_delivery_opacity": ring_max_delivery,
            "preview": preview_qa,
            "pass": overall_pass,
        },
        "products": products,
        "source_mutations": 0,
    }
    write_json_atomic(staging / PRODUCT_NAMES["receipt"], receipt)
    sums = staging / PRODUCT_NAMES["sha256sums"]
    with sums.open("w", encoding="utf-8") as handle:
        for path in sorted(staging.iterdir(), key=lambda item: item.name):
            if path.is_file() and path != sums:
                handle.write(f"{sha256(path)}  {path.name}\n")
    os.rename(staging, output_dir)
    print(
        json.dumps(
            {
                "status": verdict,
                "classification": CLASSIFICATION,
                "output": str(output_dir),
                "image_role": "image",
                "mask_role": "mask",
                "recommended_opacity_255": inputs.config.opacity_255,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_pass else 3


def run_self_test() -> dict[str, Any]:
    tests: list[str] = []
    shape = (128, 160)
    support = np.ones(shape, bool)
    support[36:92, 62:98] = False
    constant = np.full(shape, math.log(0.23), np.float32)
    local, denominator = normalized_gaussian(constant, support, 5.0)
    check = support & (denominator > 1e-4)
    if float(np.max(np.abs(local[check] - constant[check]))) > 2e-5:
        raise AssertionError("normalized Gaussian introduced a support-edge halo")
    tests.append("normalized_gaussian_constant_across_support_hole")

    lunar = lunar_interior_chunk(0, 128, 160, [(80.0, 64.0)], 22.5)
    mask = np.where(support & ~lunar, np.uint16(65535), np.uint16(0))
    yy, xx = np.indices(shape)
    physical = (xx - 80.0) ** 2 + (yy - 64.0) ** 2 <= 22.5 ** 2
    if np.any(mask[physical] != 0):
        raise AssertionError("physical lunar interior was not excluded")
    tests.append("physical_lunar_radius_excluded")

    base = np.empty((128, 160, 3), np.float32)
    base[..., 0] = 0.20
    base[..., 1] = 0.25
    base[..., 2] = 0.30
    texture = 0.16 * np.sin(xx / 4.0) * np.cos(yy / 7.0)
    raw_gain = np.exp(texture).astype(np.float32)
    gain = np.clip(raw_gain, GAIN_MIN, GAIN_MAX)
    gain[mask == 0] = 1.0
    candidate = base * gain[..., None]
    if (
        float(gain.min()) < GAIN_MIN - 1e-7
        or float(gain.max()) > GAIN_MAX + 1e-7
        or not np.array_equal(candidate[mask == 0], base[mask == 0])
    ):
        raise AssertionError("gain/neutral contract")
    ratios = candidate[mask != 0] / base[mask != 0]
    if float(np.max(np.ptp(ratios, axis=1))) > 1e-6:
        raise AssertionError("scalar gain changed chroma")
    tests.append("gain_clamped_scalar_rgb_and_normal_neutral_candidate")

    with tempfile.TemporaryDirectory(prefix="gentle-detail-selftest-") as temporary:
        temp = Path(temporary)
        image_path = temp / "detail.tif"
        mask_path = temp / "mask.tif"
        image = create_tiff_memmap(
            image_path,
            candidate.shape,
            np.uint16,
            {"class": CLASSIFICATION},
            icc=ENCODED_ICC,
        )
        mask_out = create_tiff_memmap(
            mask_path, mask.shape, np.uint16, {"physical_lunar_mask": True}
        )
        image[:] = encode_adobe(candidate)
        mask_out[:] = mask
        image.flush()
        mask_out.flush()
        del image, mask_out
        image_shape, image_dtype, embedded = tiff_metadata(image_path)
        mask_shape, mask_dtype, _ = tiff_metadata(mask_path)
        if (
            image_shape != candidate.shape
            or image_dtype != np.dtype(np.uint16)
            or embedded != ENCODED_ICC
            or mask_shape != mask.shape
            or mask_dtype != np.dtype(np.uint16)
        ):
            raise AssertionError("RGB16/ICC/mask16 round trip")
    tests.append("rgb16_adobergb_and_mask16_roundtrip")

    ring_shape = (512, 512)
    ring_center = (256.0, 256.0)
    radius_sun = 50.0
    valid = np.ones(ring_shape, bool)
    flat = np.ones(ring_shape, np.float32)
    flat_scan = N.annular_ring_scan(
        flat, valid, ring_center, radius_sun, 1, 2.0, 10.0, 1.15, 4.5, 0.12, 0.005, 12
    )
    if flat_scan["candidate_count"] != 0:
        raise AssertionError("flat effect generated a circular candidate")
    rr = np.hypot(*np.meshgrid(
        np.arange(512, dtype=np.float32) - ring_center[0],
        np.arange(512, dtype=np.float32) - ring_center[1],
    ))
    injected = 1.0 + 0.04 * np.exp(-0.5 * ((rr - 150.0) / 2.0) ** 2)
    injected_scan = N.annular_ring_scan(
        injected, valid, ring_center, radius_sun, 1, 2.0, 10.0, 1.15, 4.5, 0.12, 0.005, 12
    )
    if injected_scan["candidate_count"] == 0:
        raise AssertionError("anti-ring gate missed a synthetic circular artifact")
    tests.append("anti_ring_gate_rejects_synthetic_circle")

    return {
        "status": "SELF_TEST_PASS",
        "schema": REQUEST_SCHEMA,
        "receipt_schema": RECEIPT_SCHEMA,
        "classification": CLASSIFICATION,
        "tests": tests,
        "gain_bounds": [GAIN_MIN, GAIN_MAX],
        "lunar_physical_radius_px": PHYSICAL_LUNAR_RADIUS_PX,
        "anti_ring_extent_rsun": 8.5,
        "source_mutations": 0,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        if args.manifest is not None or args.output_dir is not None or args.validate_only:
            parser.error("--self-test no admet --manifest/--output-dir/--validate-only")
    elif args.manifest is None or args.output_dir is None:
        parser.error("calen --manifest i --output-dir")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            print(json.dumps(run_self_test(), ensure_ascii=False, indent=2))
            return 0
        assert args.manifest is not None and args.output_dir is not None
        return build(args.manifest, args.output_dir, args.validate_only)
    except ContractError as exc:
        print(f"ERROR DE CONTRACTE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
