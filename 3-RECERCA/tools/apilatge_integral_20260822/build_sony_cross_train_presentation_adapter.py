#!/usr/bin/env python3
"""Render the accepted Sony cross-train layer with the Vixen-v5 global look.

This is a deliberately narrow presentation adapter.  It consumes only the
accepted ``sony_cross_train_c_v2`` matched RGB/alpha products and the accepted
``vixen_natural_stable_v5`` receipt.  The Sony image is passed through exactly
the colour matrix, global luminance curve, gamut shoulder and Adobe RGB TRC
recorded by the Vixen-v5 receipt.  The alpha is merely quantised to MASK16;
positive sub-LSB values are promoted to one solely to preserve support.

There is no Sony-specific tone curve, local contrast, radial operation, MGN,
NRGF, denoise or sharpening in this program.  The source float products and
both upstream directories remain untouched.  Publication is non-overwriting
and uses an atomic same-directory rename after all QA gates pass.
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
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import tifffile


RECEIPT_SCHEMA = "SONY_CROSS_TRAIN_PRESENTATION_ADAPTER_RECEIPT_V1"
CROSS_SCHEMA = "SONY_CROSS_TRAIN_LAYER_RECEIPT_V1"
CROSS_VERDICT = "ACCEPTADA_PER_FUSIO"
BASE_SCHEMA = "ECLIPSE_NATURAL_COMPOSITE_RECEIPT_V1"
BASE_VERDICT = "ACCEPTAT"
OUTPUT_VERDICT = "ACCEPTAT"
CROSS_DIRECTORY_NAME = "sony_cross_train_c_v2"
BASE_DIRECTORY_NAME = "vixen_natural_stable_v5"
IMAGE_NAME = "SONY_MATCHED_TO_VIXEN_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif"
MASK_NAME = "SONY_VISUAL_ALPHA_EFFECTIVE_FLOAT32_BIGTIFF.tif"
OUTPUT_IMAGE_NAME = "IMAGE_ADOBERGB16.tif"
OUTPUT_MASK_NAME = "MASK16.tif"
ICC_NAME = "AdobeRGB1998.icc"
SHAPE_RGB = (4640, 6960, 3)
SHAPE_MASK = SHAPE_RGB[:2]
ADOBE_LUMA = np.array([0.2973769, 0.6273491, 0.0752741], dtype=np.float64)
ADOBE_GAMMA = 563.0 / 256.0
CANONICAL_JSON_DESCRIPTION = (
    'json.dumps(value, sort_keys=True, separators=(",",":"), '
    "ensure_ascii=False), UTF-8, no trailing newline"
)


class ContractError(RuntimeError):
    """A provenance, format or QA condition did not validate."""


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"No es pot llegir JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} no conté un objecte JSON")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ContractError(f"Falta {label}: {resolved}")
    return resolved


def require_directory_name(path: Path, expected: str, label: str) -> None:
    if path.name != expected:
        raise ContractError(
            f"{label} ha de ser literalment {expected}, rebut {path.name}"
        )


def output_index(receipt: dict[str, Any], receipt_path: Path) -> dict[str, dict[str, Any]]:
    rows = receipt.get("outputs")
    if not isinstance(rows, list) or not rows:
        raise ContractError(f"{receipt_path}: falta outputs")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError(f"{receipt_path}: output invàlid")
        name = row.get("path", row.get("name"))
        digest = row.get("sha256")
        if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
            raise ContractError(f"{receipt_path}: output sense name/path o hash vàlid")
        if name in result:
            raise ContractError(f"{receipt_path}: output duplicat {name}")
        result[name] = row
    return result


def verify_output_file(
    root: Path,
    index: dict[str, dict[str, Any]],
    name: str,
    label: str,
) -> tuple[Path, str]:
    if name not in index:
        raise ContractError(f"Falta {label} {name} al rebut")
    path = require_file(root / name, label)
    actual = sha256(path)
    expected = index[name]["sha256"]
    if actual != expected:
        raise ContractError(
            f"Hash divergent per {label}: esperat {expected}, actual {actual}"
        )
    expected_bytes = index[name].get("bytes")
    if expected_bytes is not None and int(expected_bytes) != path.stat().st_size:
        raise ContractError(f"Mida divergent per {label}")
    return path, actual


def tiff_info(path: Path) -> dict[str, Any]:
    with tifffile.TiffFile(path) as tif:
        if len(tif.series) != 1:
            raise ContractError(f"{path}: TIFF ha de tenir una sola sèrie")
        series = tif.series[0]
        page = tif.pages[0]
        icc = bytes(page.tags[34675].value) if 34675 in page.tags else None
        return {
            "shape": tuple(int(v) for v in series.shape),
            "dtype": str(series.dtype),
            "photometric": page.photometric.name,
            "icc": icc,
            "icc_sha256": hashlib.sha256(icc).hexdigest() if icc else None,
            "description": page.description,
        }


def validate_source_tiffs(image_path: Path, mask_path: Path) -> None:
    image_info = tiff_info(image_path)
    mask_info = tiff_info(mask_path)
    if image_info["shape"] != SHAPE_RGB or image_info["dtype"] != "float32":
        raise ContractError(f"Format Sony image inesperat: {image_info}")
    if image_info["photometric"] != "RGB" or image_info["icc"] is not None:
        raise ContractError("La font Sony ha de ser RGB lineal float sense ICC de display")
    if mask_info["shape"] != SHAPE_MASK or mask_info["dtype"] != "float32":
        raise ContractError(f"Format alpha Sony inesperat: {mask_info}")
    if mask_info["photometric"] != "MINISBLACK" or mask_info["icc"] is not None:
        raise ContractError("L'alpha Sony ha de ser grayscale lineal sense ICC")


def validate_cross_receipt(receipt: dict[str, Any], path: Path) -> None:
    if receipt.get("schema") != CROSS_SCHEMA:
        raise ContractError(f"{path}: schema cross-train no acceptat")
    if receipt.get("verdict") != CROSS_VERDICT:
        raise ContractError(f"{path}: cross-train no acceptat per fusió")
    geometry = receipt.get("geometry")
    if not isinstance(geometry, dict):
        raise ContractError(f"{path}: falta geometria")
    if geometry.get("destination_shape_yxc") != list(SHAPE_RGB):
        raise ContractError(f"{path}: llenç cross-train inesperat")
    if geometry.get("frame") != "CORONA_SOLAR":
        raise ContractError(f"{path}: frame cross-train inesperat")
    scope = receipt.get("input_scope")
    if not isinstance(scope, dict):
        raise ContractError(f"{path}: falta input_scope")
    required_scope = {
        "segment_A_consumed": False,
        "eight_second_consumed": False,
        "single_frame_products_consumed": False,
        "lunar_transform_consumed_or_transferred": False,
        "sony_mount_segment": "C only",
    }
    for key, value in required_scope.items():
        if scope.get(key) != value:
            raise ContractError(f"{path}: input_scope prohibit o divergent: {key}")
    exposures = [float(v) for v in scope.get("sony_exposures_s", [])]
    if len(exposures) != 3 or not np.allclose(
        exposures, [1.0 / 30.0, 0.25, 2.0], rtol=0.0, atol=1e-15
    ):
        raise ContractError(f"{path}: exposicions Sony no autoritzades")


def three_vector(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise ContractError(f"{label} ha de ser vector finit de tres elements")
    return array


def matrix3(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3, 3) or not np.all(np.isfinite(array)):
        raise ContractError(f"{label} ha de ser matriu finita 3x3")
    return array


def validate_natural_config(config: dict[str, Any]) -> dict[str, np.ndarray | float]:
    white_balance = three_vector(config.get("white_balance"), "white_balance")
    camera_matrix = matrix3(
        config.get("camera_to_linear_srgb"), "camera_to_linear_srgb"
    )
    srgb_to_xyz = matrix3(
        config.get("linear_srgb_to_xyz_d65"), "linear_srgb_to_xyz_d65"
    )
    xyz_to_adobe = matrix3(
        config.get("xyz_d65_to_linear_adobe_rgb"),
        "xyz_d65_to_linear_adobe_rgb",
    )
    sky_subtraction = three_vector(
        config.get("sky_subtraction_camera_adu_s"),
        "sky_subtraction_camera_adu_s",
    )
    if not np.array_equal(sky_subtraction, np.zeros(3, dtype=np.float64)):
        raise ContractError("v5 inesperat: la sostracció de cel no és exactament zero")
    if float(config.get("sky_subtract_fraction", math.nan)) != 0.0:
        raise ContractError("v5 inesperat: sky_subtract_fraction no és zero")
    gamma = float(config.get("adobe_rgb_trc_gamma", math.nan))
    if gamma != ADOBE_GAMMA:
        raise ContractError(f"Gamma AdobeRGB v5 inesperada: {gamma}")
    scale = float(config.get("tone_scale", math.nan))
    power = float(config.get("power", math.nan))
    knee = float(config.get("gamut_knee", math.nan))
    if not math.isfinite(scale) or scale <= 0:
        raise ContractError("tone_scale v5 invàlid")
    if not math.isfinite(power) or power <= 0:
        raise ContractError("power v5 invàlid")
    if not math.isfinite(knee) or not 0 < knee < 1:
        raise ContractError("gamut_knee v5 invàlid")
    curve = config.get("global_curve")
    if not isinstance(curve, dict):
        raise ContractError("Falta global_curve al rebut v5")
    if curve.get("kind") != "monotonic piecewise linear luminance-only":
        raise ContractError("La corba v5 no és la corba global esperada")
    if curve.get("spatial_or_radial_dependency") is not False:
        raise ContractError("La corba v5 declara dependència espacial/radial")
    input_anchors = np.asarray(curve.get("input_anchors"), dtype=np.float64)
    output_anchors = np.asarray(curve.get("output_anchors"), dtype=np.float64)
    if (
        input_anchors.ndim != 1
        or input_anchors.size < 2
        or output_anchors.shape != input_anchors.shape
        or not np.all(np.isfinite(input_anchors))
        or not np.all(np.isfinite(output_anchors))
        or not np.all(np.diff(input_anchors) > 0)
        or not np.all(np.diff(output_anchors) >= 0)
    ):
        raise ContractError("Àncores globals v5 invàlides o no monòtones")
    absent = config.get("operations_absent")
    required_absent = {"radial_mask", "MGN", "NRGF", "local_contrast", "denoise"}
    if not isinstance(absent, list) or not required_absent.issubset(set(absent)):
        raise ContractError("El rebut v5 no exclou totes les operacions locals prohibides")
    return {
        "white_balance": white_balance,
        "camera_matrix": camera_matrix,
        "srgb_to_xyz": srgb_to_xyz,
        "xyz_to_adobe": xyz_to_adobe,
        "sky_subtraction": sky_subtraction,
        "gamma": gamma,
        "scale": scale,
        "power": power,
        "knee": knee,
        "input_anchors": input_anchors,
        "output_anchors": output_anchors,
    }


def render_global_adobergb16(
    camera_rgb: np.ndarray,
    valid_pixels: np.ndarray,
    transform: dict[str, np.ndarray | float],
) -> tuple[np.ndarray, np.ndarray, dict[str, int | float]]:
    """Replay build_natural_composite.py's v5 pixelwise global transform."""
    camera = np.asarray(camera_rgb, dtype=np.float64)
    valid = np.asarray(valid_pixels, dtype=bool)
    # Compressed cross-train TIFFs retain NaN/Inf sentinels outside their
    # effective support.  Those pixels are semantically absent and become
    # black under the mask; zero them before matrix arithmetic so a canonical
    # run is warning-free without changing a single supported pixel.
    if np.any(~valid):
        camera = camera.copy()
        camera[~valid] = 0.0
    white_balance = np.asarray(transform["white_balance"])
    camera_matrix = np.asarray(transform["camera_matrix"])
    srgb_to_xyz = np.asarray(transform["srgb_to_xyz"])
    xyz_to_adobe = np.asarray(transform["xyz_to_adobe"])
    sky_subtraction = np.asarray(transform["sky_subtraction"])
    # NumPy 2.5/Accelerate can report stale floating-status flags from batched
    # matmul even after the unsupported sentinels have been zeroed.  The
    # explicit finite-in-support gate above and the post-render exact replay are
    # authoritative; keep the deterministic pixel math free of spurious stderr.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        linear_srgb = ((camera - sky_subtraction) * white_balance) @ camera_matrix.T
        xyz_d65 = linear_srgb @ srgb_to_xyz.T
        adobe = xyz_d65 @ xyz_to_adobe.T
    negative_matrix_channels = int(np.count_nonzero(valid[..., None] & (adobe < 0)))
    adobe = np.maximum(adobe, 0.0)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        luminance = adobe @ ADOBE_LUMA
        x = np.maximum(luminance, 0.0) / float(transform["scale"])
        base_curve = np.power(x / (1.0 + x), float(transform["power"]))
    display_luminance = np.interp(
        base_curve,
        np.asarray(transform["input_anchors"]),
        np.asarray(transform["output_anchors"]),
    )
    gain = np.zeros_like(luminance)
    positive = valid & np.isfinite(luminance) & (luminance > 0)
    gain[positive] = display_luminance[positive] / luminance[positive]
    visual = adobe * gain[..., None]
    maximum = np.max(visual, axis=-1)
    mapped = maximum.copy()
    knee = float(transform["knee"])
    high = maximum > knee
    width = 1.0 - knee
    mapped[high] = knee + width * (1.0 - np.exp(-(maximum[high] - knee) / width))
    shoulder_gain = np.ones_like(maximum)
    max_positive = maximum > 0
    shoulder_gain[max_positive] = mapped[max_positive] / maximum[max_positive]
    visual *= shoulder_gain[..., None]
    visual[~valid] = 0.0
    visual = np.nan_to_num(visual, nan=0.0, posinf=0.0, neginf=0.0)
    encoded = np.power(
        np.clip(visual, 0.0, 1.0), 1.0 / float(transform["gamma"])
    )
    quantized = np.floor(encoded * 65535.0 + 0.5).astype(np.uint16)
    stats: dict[str, int | float] = {
        "valid_pixels": int(np.count_nonzero(valid)),
        "positive_channels": int(np.count_nonzero(valid[..., None] & (visual > 0))),
        "high_clip_channels": int(
            np.count_nonzero(valid[..., None] & (quantized == 65535))
        ),
        "positive_quantized_to_black_channels": int(
            np.count_nonzero(valid[..., None] & (visual > 0) & (quantized == 0))
        ),
        "negative_camera_matrix_channels_clipped_in_visual_derivative": (
            negative_matrix_channels
        ),
        "linear_min": float(np.min(visual[valid])) if np.any(valid) else math.nan,
        "linear_max": float(np.max(visual[valid])) if np.any(valid) else math.nan,
    }
    return quantized, visual, stats


def create_tiff_memmap(
    path: Path,
    shape: tuple[int, ...],
    dtype: Any,
    description: dict[str, Any],
    *,
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
        bigtiff=False,
        metadata=None,
        description=json.dumps(description, ensure_ascii=False, separators=(",", ":")),
        software=Path(__file__).name,
        resolution=(300, 300),
        extratags=extratags,
    )


def product_record(path: Path, role: str) -> dict[str, Any]:
    info = tiff_info(path) if path.suffix.lower() in {".tif", ".tiff"} else None
    record: dict[str, Any] = {
        "role": role,
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if info is not None:
        record.update(
            {
                "shape": list(info["shape"]),
                "dtype": info["dtype"],
                "photometric": info["photometric"],
                "embedded_icc_sha256": info["icc_sha256"],
            }
        )
    return record


def merge_stats(total: dict[str, int | float], current: dict[str, int | float]) -> None:
    for key in (
        "valid_pixels",
        "positive_channels",
        "high_clip_channels",
        "positive_quantized_to_black_channels",
        "negative_camera_matrix_channels_clipped_in_visual_derivative",
    ):
        total[key] = int(total.get(key, 0)) + int(current[key])
    total["linear_min"] = min(float(total.get("linear_min", math.inf)), float(current["linear_min"]))
    total["linear_max"] = max(float(total.get("linear_max", -math.inf)), float(current["linear_max"]))


def verify_v5_replay(
    base_hdr_path: Path,
    base_valid_path: Path,
    base_natural_path: Path,
    transform: dict[str, np.ndarray | float],
) -> dict[str, Any]:
    hdr = tifffile.memmap(base_hdr_path, mode="r")
    valid = tifffile.memmap(base_valid_path, mode="r")
    natural = tifffile.memmap(base_natural_path, mode="r")
    ys = np.unique(np.concatenate((np.arange(0, SHAPE_MASK[0], 97), [SHAPE_MASK[0] - 1])))
    xs = np.unique(np.concatenate((np.arange(0, SHAPE_MASK[1], 101), [SHAPE_MASK[1] - 1])))
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    sample_camera = np.asarray(hdr[yy, xx], dtype=np.float64)
    sample_valid = np.asarray(valid[yy, xx], dtype=bool)
    expected, _, _ = render_global_adobergb16(sample_camera, sample_valid, transform)
    actual = np.asarray(natural[yy, xx], dtype=np.uint16)
    difference = np.abs(expected.astype(np.int32) - actual.astype(np.int32))
    result = {
        "method": (
            "deterministic 97x101-pixel grid replay against the receipt-hashed "
            "Vixen-v5 NATURAL_ADOBERGB16"
        ),
        "sampled_pixels": int(yy.size),
        "sampled_channels": int(difference.size),
        "maximum_uint16_difference": int(np.max(difference)),
        "different_channels": int(np.count_nonzero(difference)),
        "pass": bool(np.count_nonzero(difference) == 0),
    }
    del hdr, valid, natural
    return result


def build(args: argparse.Namespace) -> Path:
    cross_root = args.cross_root.expanduser().resolve()
    base_root = args.base_root.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    require_directory_name(cross_root, CROSS_DIRECTORY_NAME, "cross-root")
    require_directory_name(base_root, BASE_DIRECTORY_NAME, "base-root")
    if output_dir.exists():
        raise ContractError(f"No se sobreescriu una sortida existent: {output_dir}")
    if output_dir.parent.exists() and not output_dir.parent.is_dir():
        raise ContractError(f"El pare de sortida no és un directori: {output_dir.parent}")

    cross_receipt_path = require_file(
        cross_root / "CROSS_TRAIN_RECEIPT.json", "rebut cross-train"
    )
    cross_receipt = read_json(cross_receipt_path)
    validate_cross_receipt(cross_receipt, cross_receipt_path)
    cross_receipt_sha = sha256(cross_receipt_path)
    cross_index = output_index(cross_receipt, cross_receipt_path)
    source_image_path, source_image_sha = verify_output_file(
        cross_root, cross_index, IMAGE_NAME, "imatge Sony matched"
    )
    source_mask_path, source_mask_sha = verify_output_file(
        cross_root, cross_index, MASK_NAME, "alpha Sony effective"
    )
    validate_source_tiffs(source_image_path, source_mask_path)

    base_receipt_path = require_file(
        base_root / "COMPOSITE_RECEIPT.json", "rebut Vixen v5"
    )
    base_receipt = read_json(base_receipt_path)
    if base_receipt.get("schema") != BASE_SCHEMA or base_receipt.get("verdict") != BASE_VERDICT:
        raise ContractError("La base Vixen v5 no té schema/veredicte acceptats")
    base_receipt_sha = sha256(base_receipt_path)
    manifest_record = base_receipt.get("manifest")
    if not isinstance(manifest_record, dict):
        raise ContractError("El rebut v5 no declara manifest")
    manifest_path = require_file(Path(str(manifest_record.get("path"))), "manifest Vixen v5")
    manifest_sha = sha256(manifest_path)
    if manifest_sha != manifest_record.get("sha256"):
        raise ContractError("Hash del manifest Vixen v5 divergent")
    if manifest_path.name != "vixen_natural_stable_v5.json":
        raise ContractError("El manifest de base no és literalment vixen_natural_stable_v5")
    natural = base_receipt.get("natural")
    if not isinstance(natural, dict) or not isinstance(natural.get("config"), dict):
        raise ContractError("El rebut v5 no conté natural.config")
    natural_config: dict[str, Any] = natural["config"]
    natural_config_sha = canonical_json_sha256(natural_config)
    transform = validate_natural_config(natural_config)
    base_index = output_index(base_receipt, base_receipt_path)
    icc_path, icc_sha = verify_output_file(base_root, base_index, ICC_NAME, "ICC AdobeRGB v5")
    base_hdr_path, base_hdr_sha = verify_output_file(
        base_root, base_index, "VIXEN_HDR_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif", "HDR Vixen v5"
    )
    base_valid_path, base_valid_sha = verify_output_file(
        base_root, base_index, "HDR_VALID_PIXELS_UINT8.tif", "valid pixels Vixen v5"
    )
    base_natural_path, base_natural_sha = verify_output_file(
        base_root, base_index, "NATURAL_ADOBERGB16.tif", "NATURAL AdobeRGB16 Vixen v5"
    )
    base_software = base_receipt.get("software")
    if not isinstance(base_software, dict):
        raise ContractError("El rebut v5 no declara software")
    base_software_path = require_file(Path(str(base_software.get("path"))), "software Vixen v5")
    base_software_sha = sha256(base_software_path)
    if base_software_sha != base_software.get("sha256"):
        raise ContractError("L'implementació Vixen v5 ha canviat des del rebut")
    icc_bytes = icc_path.read_bytes()
    if len(icc_bytes) < 128 or icc_bytes[36:40] != b"acsp":
        raise ContractError("ICC AdobeRGB v5 invàlid")
    replay_qa = verify_v5_replay(
        base_hdr_path, base_valid_path, base_natural_path, transform
    )
    if not replay_qa["pass"]:
        raise ContractError(f"La reproducció tonal/color v5 no és exacta: {replay_qa}")

    log("Preflight i replay exacte de Vixen-v5: PASS")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = output_dir.parent / f".{output_dir.name}.partial-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o755)
    try:
        source_image = tifffile.imread(source_image_path)
        source_alpha = tifffile.imread(source_mask_path)
        if source_image.shape != SHAPE_RGB or source_image.dtype != np.float32:
            raise ContractError("La imatge Sony descodificada ha canviat de format")
        if source_alpha.shape != SHAPE_MASK or source_alpha.dtype != np.float32:
            raise ContractError("L'alpha Sony descodificat ha canviat de format")
        if not np.all(np.isfinite(source_alpha)):
            raise ContractError("L'alpha Sony conté NaN o infinit")
        if float(np.min(source_alpha)) < 0.0 or float(np.max(source_alpha)) > 1.0:
            raise ContractError("L'alpha Sony cau fora de [0,1]")
        source_support = source_alpha > 0
        if not np.any(source_support):
            raise ContractError("L'alpha Sony no té suport positiu")
        finite_rgb = np.all(np.isfinite(source_image), axis=2)
        if np.any(source_support & ~finite_rgb):
            raise ContractError("Hi ha RGB Sony no finit dins del suport efectiu")
        valid_pixels = source_support & finite_rgb

        image_out_path = staging / OUTPUT_IMAGE_NAME
        mask_out_path = staging / OUTPUT_MASK_NAME
        icc_out_path = staging / ICC_NAME
        shutil.copyfile(icc_path, icc_out_path)
        image_out = create_tiff_memmap(
            image_out_path,
            SHAPE_RGB,
            np.uint16,
            {
                "linear": False,
                "space": "Adobe RGB (1998)",
                "trc_gamma": ADOBE_GAMMA,
                "intent": "Sony cross-train C visual layer; exact Vixen-v5 global transform",
                "local_contrast": False,
                "separate_tone": False,
            },
            icc_profile=icc_bytes,
        )
        mask_out = create_tiff_memmap(
            mask_out_path,
            SHAPE_MASK,
            np.uint16,
            {
                "space": "linear grayscale mask",
                "mapping": "alpha in [0,1] -> uint16; nearest, positive minimum 1",
                "support_preserved": True,
            },
        )

        stats: dict[str, int | float] = {}
        chunk_rows = int(args.chunk_rows)
        if chunk_rows < 1:
            raise ContractError("chunk_rows ha de ser >= 1")
        for y0 in range(0, SHAPE_MASK[0], chunk_rows):
            y1 = min(SHAPE_MASK[0], y0 + chunk_rows)
            quantized, _, chunk_stats = render_global_adobergb16(
                source_image[y0:y1], valid_pixels[y0:y1], transform
            )
            image_out[y0:y1] = quantized
            alpha_chunk = np.asarray(source_alpha[y0:y1], dtype=np.float64)
            mask_chunk = np.floor(alpha_chunk * 65535.0 + 0.5).astype(np.uint16)
            positive = alpha_chunk > 0
            mask_chunk[positive & (mask_chunk == 0)] = np.uint16(1)
            mask_out[y0:y1] = mask_chunk
            merge_stats(stats, chunk_stats)
        image_out.flush()
        mask_out.flush()
        del image_out, mask_out

        rendered = tifffile.memmap(image_out_path, mode="r")
        quantized_mask = tifffile.memmap(mask_out_path, mode="r")
        mask_support_equal = bool(np.array_equal(quantized_mask > 0, source_support))
        mask_error = np.abs(
            np.asarray(quantized_mask, dtype=np.float64) / 65535.0
            - np.asarray(source_alpha, dtype=np.float64)
        )
        mask_max_error = float(np.max(mask_error))
        mask_sub_lsb_promoted = int(
            np.count_nonzero(
                source_support
                & (np.floor(np.asarray(source_alpha, dtype=np.float64) * 65535.0 + 0.5) == 0)
            )
        )
        mask_pass = (
            mask_support_equal
            and mask_max_error <= (1.0 / 65535.0 + 1e-12)
            and int(np.min(quantized_mask)) == 0
            and int(np.max(quantized_mask)) <= 65535
        )

        replay_mismatch = 0
        replay_max_difference = 0
        for y0 in range(0, SHAPE_MASK[0], chunk_rows):
            y1 = min(SHAPE_MASK[0], y0 + chunk_rows)
            expected, _, _ = render_global_adobergb16(
                source_image[y0:y1], valid_pixels[y0:y1], transform
            )
            difference = np.abs(
                expected.astype(np.int32) - np.asarray(rendered[y0:y1], dtype=np.int32)
            )
            replay_mismatch += int(np.count_nonzero(difference))
            replay_max_difference = max(replay_max_difference, int(np.max(difference)))
        del rendered, quantized_mask

        valid_channels = int(stats["valid_pixels"]) * 3
        positive_channels = int(stats["positive_channels"])
        high_clip_fraction = int(stats["high_clip_channels"]) / max(valid_channels, 1)
        black_fraction = int(stats["positive_quantized_to_black_channels"]) / max(
            positive_channels, 1
        )
        clipping_limits = base_receipt.get("qa", {}).get("clipping", {})
        max_high_clip = float(clipping_limits.get("max_high_clip_fraction", math.nan))
        max_black = float(clipping_limits.get("max_positive_to_black_fraction", math.nan))
        clipping_pass = (
            math.isfinite(max_high_clip)
            and math.isfinite(max_black)
            and high_clip_fraction <= max_high_clip
            and black_fraction <= max_black
        )

        image_info = tiff_info(image_out_path)
        mask_info = tiff_info(mask_out_path)
        icc_pass = (
            sha256(icc_out_path) == icc_sha
            and image_info["icc_sha256"] == icc_sha
            and mask_info["icc_sha256"] is None
        )
        format_pass = (
            image_info["shape"] == SHAPE_RGB
            and image_info["dtype"] == "uint16"
            and image_info["photometric"] == "RGB"
            and mask_info["shape"] == SHAPE_MASK
            and mask_info["dtype"] == "uint16"
            and mask_info["photometric"] == "MINISBLACK"
        )
        transform_pass = replay_mismatch == 0 and replay_max_difference == 0
        overall_pass = bool(
            clipping_pass
            and icc_pass
            and format_pass
            and mask_pass
            and transform_pass
            and replay_qa["pass"]
        )
        qa = {
            "pass": overall_pass,
            "clipping": {
                "valid_channels": valid_channels,
                "positive_channels": positive_channels,
                "high_clip_channels": int(stats["high_clip_channels"]),
                "high_clip_fraction": high_clip_fraction,
                "max_high_clip_fraction_from_v5": max_high_clip,
                "positive_quantized_to_black_channels": int(
                    stats["positive_quantized_to_black_channels"]
                ),
                "positive_quantized_to_black_fraction": black_fraction,
                "max_positive_to_black_fraction_from_v5": max_black,
                "linear_min": float(stats["linear_min"]),
                "linear_max": float(stats["linear_max"]),
                "negative_camera_matrix_channels_clipped_in_visual_derivative": int(
                    stats["negative_camera_matrix_channels_clipped_in_visual_derivative"]
                ),
                "pass": clipping_pass,
            },
            "icc": {
                "profile_file_sha256": sha256(icc_out_path),
                "embedded_image_profile_sha256": image_info["icc_sha256"],
                "mask_has_no_icc": mask_info["icc_sha256"] is None,
                "matches_vixen_v5_profile": image_info["icc_sha256"] == icc_sha,
                "pass": icc_pass,
            },
            "mask": {
                "source_min": float(np.min(source_alpha)),
                "source_max": float(np.max(source_alpha)),
                "source_positive_pixels": int(np.count_nonzero(source_support)),
                "output_positive_pixels": int(np.count_nonzero(source_support)),
                "support_exact": mask_support_equal,
                "quantization": (
                    "round(alpha*65535), with positive values promoted to at least 1 "
                    "to preserve support"
                ),
                "positive_sub_half_lsb_promoted": mask_sub_lsb_promoted,
                "maximum_absolute_error_in_unit_interval": mask_max_error,
                "maximum_allowed_error": 1.0 / 65535.0,
                "pass": mask_pass,
            },
            "format": {
                "image_shape": list(image_info["shape"]),
                "image_dtype": image_info["dtype"],
                "image_photometric": image_info["photometric"],
                "mask_shape": list(mask_info["shape"]),
                "mask_dtype": mask_info["dtype"],
                "mask_photometric": mask_info["photometric"],
                "pass": format_pass,
            },
            "vixen_v5_transform_replay": replay_qa,
            "sony_full_transform_replay": {
                "compared_channels": int(np.prod(SHAPE_RGB)),
                "different_channels": replay_mismatch,
                "maximum_uint16_difference": replay_max_difference,
                "pass": transform_pass,
            },
            "no_local_or_separate_tone": {
                "base_natural_config_consumed_without_overrides": True,
                "adapter_tone_overrides": [],
                "spatial_or_radial_parameters": [],
                "local_filters": [],
                "operations_absent": natural_config["operations_absent"],
                "pixel_function_position_inputs": [],
                "pass": True,
            },
            "hashes": {
                "upstream_receipts_and_consumed_products_verified": True,
                "base_manifest_verified": True,
                "base_implementation_verified": True,
                "products_hashed_after_QA": True,
                "pass": True,
            },
        }
        if not overall_pass:
            failed = {
                "schema": RECEIPT_SCHEMA,
                "verdict": "NO_ACCEPTAT",
                "qa": qa,
            }
            write_json(staging / "FAILED_RECEIPT.json", failed)
            raise ContractError(f"QA de l'adaptador no superat: {qa}")

        image_product = product_record(image_out_path, "image")
        mask_product = product_record(mask_out_path, "mask")
        icc_product = product_record(icc_out_path, "icc")
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "verdict": OUTPUT_VERDICT,
            "stage": "presentation_adapter",
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "upstream_cross_train": {
                "receipt": str(cross_receipt_path),
                "receipt_sha256": cross_receipt_sha,
                "schema": CROSS_SCHEMA,
                "verdict": CROSS_VERDICT,
                "image_name": IMAGE_NAME,
                "image_sha256": source_image_sha,
                "mask_name": MASK_NAME,
                "mask_sha256": source_mask_sha,
            },
            "base_natural": {
                "receipt": str(base_receipt_path),
                "receipt_sha256": base_receipt_sha,
                "schema": BASE_SCHEMA,
                "verdict": BASE_VERDICT,
                "directory_name": BASE_DIRECTORY_NAME,
                "natural_config_sha256": natural_config_sha,
                "natural_config_hash_canonicalization": CANONICAL_JSON_DESCRIPTION,
                "manifest": str(manifest_path),
                "manifest_sha256": manifest_sha,
                "implementation": str(base_software_path),
                "implementation_sha256": base_software_sha,
                "replay_inputs": {
                    "hdr_sha256": base_hdr_sha,
                    "valid_pixels_sha256": base_valid_sha,
                    "natural_adobergb16_sha256": base_natural_sha,
                    "icc_sha256": icc_sha,
                },
            },
            "geometry": {
                "frame": "CORONA_SOLAR",
                "shape_yx": list(SHAPE_MASK),
                "shape_yxc": list(SHAPE_RGB),
                "resampling": "none; already on the Vixen canvas",
            },
            "transform": {
                "origin": "base_natural receipt .natural.config, byte-content hash above",
                "config": natural_config,
                "adobe_luminance_coefficients": ADOBE_LUMA.tolist(),
                "operation_graph": [
                    "camera RGB times v5 white balance",
                    "v5 camera-to-linear-sRGB matrix",
                    "v5 linear-sRGB-to-XYZ-D65 matrix",
                    "v5 XYZ-D65-to-linear-AdobeRGB matrix",
                    "clip negative matrix excursions in visual derivative",
                    "v5 monotonic global luminance-only curve",
                    "v5 hue-preserving global gamut shoulder",
                    "v5 AdobeRGB TRC gamma",
                    "nearest uint16 quantization",
                ],
                "adapter_specific_color_parameters": [],
                "adapter_specific_tone_parameters": [],
                "local_or_spatial_operations": [],
            },
            "mask_conversion": {
                "source": MASK_NAME,
                "destination": OUTPUT_MASK_NAME,
                "policy": (
                    "round(alpha*65535); positive values that would quantize to zero "
                    "are set to 1; zero remains exactly zero"
                ),
                "support_changed": False,
                "tone_or_feather_added": False,
            },
            "products": [image_product, mask_product, icc_product],
            "qa": qa,
            "software": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256(Path(__file__).resolve()),
                "python": sys.version,
                "numpy": np.__version__,
                "tifffile": tifffile.__version__,
                "argv": sys.argv,
            },
            "source_mutations": [],
            "scientific_authority": (
                "unchanged upstream CFA4 Sony products and linear Vixen HDR; this is "
                "only a presentation derivative"
            ),
        }
        receipt_path = staging / "PRESENTATION_ADAPTER_RECEIPT.json"
        write_json(receipt_path, receipt)
        sum_paths = [image_out_path, mask_out_path, icc_out_path, receipt_path]
        sums = "".join(f"{sha256(path)}  {path.name}\n" for path in sum_paths)
        (staging / "SHA256SUMS.txt").write_text(sums, encoding="ascii")

        # Final hashes and receipt semantics are checked again before publication.
        for product in receipt["products"]:
            path = staging / product["name"]
            if sha256(path) != product["sha256"]:
                raise ContractError(f"Hash de producte canviat abans de publicar: {path}")
        check_receipt = read_json(receipt_path)
        if check_receipt.get("verdict") != OUTPUT_VERDICT or check_receipt.get("qa", {}).get("pass") is not True:
            raise ContractError("El rebut final no conserva verdict ACCEPTAT i qa.pass true")
        os.replace(staging, output_dir)
    except Exception:
        # Keep a uniquely named partial directory as audit evidence; never publish it.
        raise
    log(f"Adaptador Sony AdobeRGB16 publicat: {output_dir}")
    return output_dir


def parser() -> argparse.ArgumentParser:
    repo = Path(__file__).resolve().parents[3]
    output_root = repo / "output" / "postprocessat_final_20260822"
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--cross-root",
        type=Path,
        default=output_root / "composites" / CROSS_DIRECTORY_NAME,
    )
    result.add_argument(
        "--base-root",
        type=Path,
        default=output_root / "composites" / BASE_DIRECTORY_NAME,
    )
    result.add_argument(
        "--output-dir",
        type=Path,
        default=output_root / "presentation" / "sony_cross_train_c_v2_adobe",
    )
    result.add_argument("--chunk-rows", type=int, default=96)
    return result


def main() -> int:
    try:
        build(parser().parse_args())
    except ContractError as exc:
        print(f"ERROR DE CONTRACTE: {exc}", file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
