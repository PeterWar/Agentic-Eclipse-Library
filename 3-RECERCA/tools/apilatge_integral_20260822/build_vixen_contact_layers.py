#!/usr/bin/env python3
"""Build auditable, low-contrast Vixen C2 and C3 contact layers.

This is a new, isolated derivative pipeline.  It never edits RAW files,
calibrators, historical products or the accepted S6 authority.  It accepts
only the literal C2 and C3 groups materialised below
``masters/vixen_s6_ACCEPTED`` and revalidates the authority receipts, exact
membership, RAW/calibrator hashes and the current calibration/drizzle source
hashes before reading pixels.

The accepted contact groups contain one exposure band only (1/3200 s).  The
linear result uses the existing HDR per-pixel weighting path and is expressed
in ADU/s, but it is *not* described as multi-exposure dynamic-range extension.
The receipt records this limitation explicitly.

For each contact the program writes:

* a linear, common-solar-geometry contact master plus variance, inverse
  variance, coverage and drizzle-footprint saturation maps;
* a deliberately mild Adobe RGB presentation layer made with one global
  monotonic toe/shoulder curve (no MGN, NRGF, local contrast or denoise);
* the signed ``R-rho*G`` H-alpha excess, a soft inspection rendition, a
  thresholded prominence layer and its mask.

All lunar gates use the measured physical radius 453.8 px.  There is no
outer-field or solar-radial blend mask.  C2 and C3 are always independent.
Output promotion is atomic and refuses to overwrite an existing directory.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gc
import hashlib
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import tifffile
from scipy.ndimage import gaussian_filter


HERE = Path(__file__).resolve().parent
RESEARCH_TOOLS = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(RESEARCH_TOOLS))

import hdr_corona_vixen as H  # noqa: E402

# This override must happen before importing apila_hdr4_vixen.  The historical
# helper keeps the old generic 959-arcsec proxy; this derivative process uses
# the physical DE440+IAU value without mutating that source file.
SOLAR_RADIUS_ARCSEC = 946.6598
SOLAR_RADIUS_PX = SOLAR_RADIUS_ARCSEC / 2.1495
H.R_SOL_PX = SOLAR_RADIUS_PX

import apila_hdr4_vixen as A  # noqa: E402

sys.path.insert(0, str(HERE))
import build_natural_composite as N  # noqa: E402


SCHEMA = "VIXEN_CONTACT_LAYERS_REQUEST_V1"
RECEIPT_SCHEMA = "VIXEN_CONTACT_LAYERS_RECEIPT_V1"
GROUP_SCHEMA = "VIXEN_CONTACT_LAYER_GROUP_RECEIPT_V1"
AUTHORITY_SCHEMA = "VIXEN_R6_S6_ACCEPTED_AUTHORITY_V1"
GROUP_AUTHORITY_SCHEMA = "VIXEN_R6_S6_GROUP_AUTHORITY_V1"
UPSTREAM_SCHEMA = "VIXEN_R6_STACK_RECEIPT_S6_V2"
TRAIN = "VIXEN_VSD90SS_CANON_R6_MARK_III"
FRAME = "CONTACT_SOLAR_COMMON_GEOMETRY_LUNAR_LIMB_PROTECTED"
EXPOSURE_S = 1.0 / 3200.0
LUNAR_RADIUS_PX = 453.8
LUNAR_MARGIN_PX = 2.0
LUNAR_TRANSITION_PX = 4.0
EXPECTED_SHAPE = (4640, 6960, 3)
DEFAULT_AUTHORITY_ROOT = (
    ROOT / "output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED"
)

CONTACTS: dict[str, dict[str, Any]] = {
    "C2": {
        "authority_id": "STACK_CONTACT_C2_1-3200S",
        "relative": Path("accepted_stacks/contact_C2/1-3200s"),
        "members": tuple(f"572A{number}.CR3" for number in range(2958, 2967)),
        "reference": "572A2962.CR3",
        "phenomenon_scope": "CONTACT_C2_SEPARATE_FROM_CORONA",
    },
    "C3": {
        "authority_id": "STACK_CONTACT_C3_1-3200S",
        "relative": Path("accepted_stacks/contact_C3/1-3200s"),
        "members": tuple(f"572A{number}.CR3" for number in range(3009, 3026)),
        "reference": "572A3017.CR3",
        "phenomenon_scope": "CONTACT_C3_SEPARATE_FROM_CORONA",
    },
}


class ContractError(RuntimeError):
    """The accepted-authority or requested-output contract is not satisfied."""


@dataclass(frozen=True)
class ContactAuthority:
    name: str
    directory: Path
    authority_receipt_path: Path
    authority_receipt_sha256: str
    authority_receipt: dict[str, Any]
    upstream_receipt_path: Path
    upstream_receipt_sha256: str
    upstream_receipt: dict[str, Any]
    members: tuple[str, ...]
    reference: str
    raw_records: tuple[dict[str, Any], ...]
    calibrator_records: tuple[dict[str, Any], ...]


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
        raise ContractError(f"no es pot llegir JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} no conté un objecte JSON")
    return value


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def parse_sha256sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ContractError(f"no es pot llegir {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ContractError(f"línia SHA-256 invàlida {path}:{line_number}")
        try:
            int(parts[0], 16)
        except ValueError as exc:
            raise ContractError(
                f"digest SHA-256 invàlid {path}:{line_number}"
            ) from exc
        relative = parts[1].strip()
        if relative.startswith("*"):
            relative = relative[1:]
        candidate = Path(relative)
        if (candidate.is_absolute() or ".." in candidate.parts or relative in entries
                or relative in {"", "."}):
            raise ContractError(f"ruta SHA-256 insegura o duplicada: {relative!r}")
        entries[relative] = parts[0].lower()
    return entries


def require_root_hash(
    authority_root: Path, root_hashes: dict[str, str], path: Path, label: str
) -> str:
    try:
        relative = path.resolve().relative_to(authority_root.resolve()).as_posix()
    except ValueError as exc:
        raise ContractError(f"{label} surt de l'autoritat acceptada: {path}") from exc
    expected = root_hashes.get(relative)
    if expected is None:
        raise ContractError(f"{label} no és al SHA256SUMS arrel: {relative}")
    actual = sha256(path)
    if actual != expected:
        raise ContractError(
            f"hash divergent per {label}: {relative}; {actual} != {expected}"
        )
    return actual


def validate_file_record(record: object, label: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(record, dict):
        raise ContractError(f"registre invàlid: {label}")
    raw_path = record.get("path")
    digest = record.get("sha256")
    size = record.get("bytes")
    if not isinstance(raw_path, str) or not raw_path:
        raise ContractError(f"ruta invàlida: {label}")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ContractError(f"digest invàlid: {label}")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ContractError(f"mida invàlida: {label}")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"falta {label}: {path}")
    if path.stat().st_size != size:
        raise ContractError(f"mida divergent {label}: {path}")
    actual = sha256(path)
    if actual != digest.lower():
        raise ContractError(f"hash divergent {label}: {path}")
    return path, record


def _require_close(actual: object, expected: float, label: str, atol: float) -> None:
    try:
        value = float(actual)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label} no és numèric") from exc
    if not math.isfinite(value) or abs(value - expected) > atol:
        raise ContractError(f"{label}={value!r}; esperat {expected}")


def validate_authority(authority_root: Path) -> tuple[dict[str, Any], list[ContactAuthority]]:
    authority_root = authority_root.resolve()
    if not authority_root.is_dir():
        raise ContractError(f"falta l'autoritat Vixen acceptada: {authority_root}")
    root_hash_path = authority_root / "SHA256SUMS.txt"
    root_hashes = parse_sha256sums(root_hash_path)
    root_receipt_path = authority_root / "AUTHORITY_RECEIPT.json"
    root_receipt_sha = require_root_hash(
        authority_root, root_hashes, root_receipt_path, "rebut d'autoritat arrel"
    )
    ledger_path = authority_root / "LEDGER_68.json"
    require_root_hash(authority_root, root_hashes, ledger_path, "ledger 68")
    root_receipt = read_json(root_receipt_path)
    if (root_receipt.get("schema") != AUTHORITY_SCHEMA
            or root_receipt.get("verdict") != "ACCEPTAT"
            or root_receipt.get("train") != TRAIN):
        raise ContractError("l'autoritat Vixen arrel no és literalment ACCEPTAT")
    solar = root_receipt.get("solar_radius_model", {})
    _require_close(solar.get("radius_arcsec"), SOLAR_RADIUS_ARCSEC,
                   "radius_arcsec arrel", 1e-9)
    _require_close(solar.get("plate_scale_arcsec_px"), 2.1495,
                   "plate_scale arrel", 1e-12)
    _require_close(solar.get("radius_px"), SOLAR_RADIUS_PX,
                   "radius_px arrel", 1e-9)

    ledger = read_json(ledger_path)
    if (ledger.get("verdict") != "ACCEPTAT" or ledger.get("unique") != 68
            or ledger.get("listed") != 68):
        raise ContractError("el ledger Vixen no certifica 68/68 únics")
    ledger_entries = ledger.get("entries")
    if not isinstance(ledger_entries, list):
        raise ContractError("ledger.entries absent")
    ledger_by_frame = {item.get("frame"): item for item in ledger_entries
                       if isinstance(item, dict)}

    accepted_groups = root_receipt.get("accepted_stacks")
    if not isinstance(accepted_groups, list):
        raise ContractError("accepted_stacks absent al rebut arrel")
    root_by_id = {item.get("authority_id"): item for item in accepted_groups
                  if isinstance(item, dict)}

    current_manifest = {frame.nom: frame for frame in H.llegeix_manifest() if frame.usat}
    contacts: list[ContactAuthority] = []
    all_raw_paths: dict[Path, str] = {}
    all_calibrators: dict[Path, str] = {}
    for name in ("C2", "C3"):
        contract = CONTACTS[name]
        authority_id = contract["authority_id"]
        root_group = root_by_id.get(authority_id)
        if not isinstance(root_group, dict):
            raise ContractError(f"falta {authority_id} al rebut arrel")
        directory = authority_root / contract["relative"]
        group_authority_path = directory / "AUTHORITY_RECEIPT.json"
        upstream_path = directory / "STACK_RECEIPT.json"
        transforms_path = directory / "TRANSFORMS.csv"
        group_authority_sha = require_root_hash(
            authority_root, root_hashes, group_authority_path,
            f"rebut acceptat {name}",
        )
        upstream_sha = require_root_hash(
            authority_root, root_hashes, upstream_path, f"rebut upstream {name}"
        )
        require_root_hash(
            authority_root, root_hashes, transforms_path, f"transformacions {name}"
        )
        group = read_json(group_authority_path)
        upstream = read_json(upstream_path)
        expected_members = contract["members"]
        if (group.get("schema") != GROUP_AUTHORITY_SCHEMA
                or group.get("verdict") != "ACCEPTAT"
                or group.get("authority_id") != authority_id
                or group.get("train") != TRAIN
                or group.get("frame") != "CORONA_SOLAR"
                or group.get("product_class") != "EXPOSURE_STACK"
                or group.get("temporal_segment") != name
                or group.get("phenomenon_scope") != contract["phenomenon_scope"]
                or tuple(group.get("members", ())) != expected_members):
            raise ContractError(f"contracte de grup acceptat divergent: {name}")
        if root_group != group:
            raise ContractError(f"el grup {name} del rebut arrel divergeix del rebut local")
        _require_close(group.get("exposure_s"), EXPOSURE_S,
                       f"exposició {name}", 1e-12)
        group_solar = group.get("solar_radius_model", {})
        _require_close(group_solar.get("radius_px"), SOLAR_RADIUS_PX,
                       f"radi solar {name}", 1e-9)

        if (upstream.get("schema") != UPSTREAM_SCHEMA
                or upstream.get("train") != TRAIN
                or upstream.get("frame") != "CORONA_SOLAR"
                or upstream.get("temporal_segment") != name
                or tuple(upstream.get("members", ())) != expected_members):
            raise ContractError(f"rebut upstream divergent: {name}")
        if sha256(upstream_path) != group.get("upstream_receipt_sha256"):
            raise ContractError(f"enllaç de rebut upstream divergent: {name}")
        _require_close(upstream.get("exposure_s"), EXPOSURE_S,
                       f"exposició upstream {name}", 1e-12)
        if upstream.get("stack_info", {}).get("reference") != contract["reference"]:
            raise ContractError(f"referència temporal inesperada: {name}")

        with transforms_path.open(newline="", encoding="utf-8") as handle:
            transforms = list(csv.DictReader(handle))
        if tuple(row.get("frame") for row in transforms) != expected_members:
            raise ContractError(f"membres de TRANSFORMS divergents: {name}")
        if any(float(row["theta_deg"]) != 0.0 for row in transforms):
            raise ContractError(f"{name} no és autoritat theta=0")

        raw_records = upstream.get("input_hashes")
        calibrator_records = upstream.get("calibrator_hashes")
        if not isinstance(raw_records, list) or not isinstance(calibrator_records, list):
            raise ContractError(f"hashes d'entrada/calibradors absents: {name}")
        if tuple(item.get("name") for item in raw_records
                 if isinstance(item, dict)) != expected_members:
            raise ContractError(f"ordre/membres RAW divergent: {name}")
        for index, record in enumerate(raw_records):
            path, item = validate_file_record(record, f"RAW {name}[{index}]")
            if path.name != expected_members[index]:
                raise ContractError(f"nom RAW divergent: {path}")
            old = all_raw_paths.setdefault(path, item["sha256"])
            if old != item["sha256"]:
                raise ContractError(f"autoritat RAW conflictiva: {path}")
            manifest_frame = current_manifest.get(path.name)
            if manifest_frame is None:
                raise ContractError(f"{path.name} falta al manifest canònic")
            transform = transforms[index]
            for field, manifest_value in (
                ("t_rel_c2_s", manifest_frame.t_rel_c2),
                ("solar_x_px", manifest_frame.sol_x),
                ("solar_y_px", manifest_frame.sol_y),
                ("lunar_x_px", manifest_frame.lluna_x),
                ("lunar_y_px", manifest_frame.lluna_y),
            ):
                _require_close(transform.get(field), manifest_value,
                               f"{name} {path.name} {field}", 1e-8)
        for index, record in enumerate(calibrator_records):
            path, item = validate_file_record(record, f"calibrador {name}[{index}]")
            old = all_calibrators.setdefault(path, item["sha256"])
            if old != item["sha256"]:
                raise ContractError(f"autoritat de calibrador conflictiva: {path}")

        software = upstream.get("software", {})
        for module, current in (
            ("apila_hdr4_vixen.py", Path(A.__file__).resolve()),
            ("hdr_corona_vixen.py", Path(H.__file__).resolve()),
        ):
            record = software.get(module, {})
            if Path(str(record.get("path", ""))).resolve() != current:
                raise ContractError(f"ruta de software divergent: {module}")
            if record.get("sha256") != sha256(current):
                raise ContractError(f"hash de software divergent: {module}")

        for frame_name in expected_members:
            ledger_item = ledger_by_frame.get(frame_name)
            if (not isinstance(ledger_item, dict)
                    or ledger_item.get("authority_id") != authority_id
                    or ledger_item.get("temporal_segment") != name
                    or ledger_item.get("assigned_exactly_once") is not True):
                raise ContractError(f"assignació de ledger divergent: {frame_name}")
        contacts.append(ContactAuthority(
            name=name,
            directory=directory,
            authority_receipt_path=group_authority_path,
            authority_receipt_sha256=group_authority_sha,
            authority_receipt=group,
            upstream_receipt_path=upstream_path,
            upstream_receipt_sha256=upstream_sha,
            upstream_receipt=upstream,
            members=expected_members,
            reference=contract["reference"],
            raw_records=tuple(raw_records),
            calibrator_records=tuple(calibrator_records),
        ))

    if set(CONTACTS["C2"]["members"]) & set(CONTACTS["C3"]["members"]):
        raise AssertionError("C2/C3 constants overlap")
    manifest_path = H.OUT / "manifest.csv"
    ephemeris_path = H.EFEMERIDE.resolve()
    if not manifest_path.is_file() or not ephemeris_path.is_file():
        raise ContractError("falta el manifest geomètric o l'efemèride DE440s")
    return {
        "path": str(authority_root),
        "root_receipt": str(root_receipt_path),
        "root_receipt_sha256": root_receipt_sha,
        "root_sha256sums_sha256": sha256(root_hash_path),
        "raw_files_verified": len(all_raw_paths),
        "calibrator_files_verified": len(all_calibrators),
        "software_hashes_verified": 2,
        "ledger": "68/68 ACCEPTAT; contact members assigned exactly once",
        "geometry_manifest": {
            "path": str(manifest_path), "sha256": sha256(manifest_path),
        },
        "ephemeris": {
            "path": str(ephemeris_path), "sha256": sha256(ephemeris_path),
            "note": "current immutable DE440s dependency; geometry values also cross-checked against accepted transforms",
        },
    }, contacts


def save_float_rgb(path: Path, image: np.ndarray, unit: str, intent: str) -> None:
    tifffile.imwrite(
        path, image.astype(np.float32, copy=False), photometric="rgb",
        compression="zlib", compressionargs={"level": 4}, bigtiff=True,
        metadata={"axes": "YXS", "unit": unit, "linear": True, "intent": intent},
        software=Path(__file__).name,
    )


def save_float_gray(path: Path, image: np.ndarray, unit: str, intent: str) -> None:
    tifffile.imwrite(
        path, image.astype(np.float32, copy=False), photometric="minisblack",
        compression="zlib", compressionargs={"level": 4}, bigtiff=True,
        metadata={"axes": "YX", "unit": unit, "linear": True, "intent": intent},
        software=Path(__file__).name,
    )


def save_uint16_rgb_adobe(path: Path, linear_adobe: np.ndarray) -> dict[str, Any]:
    encoded = np.power(np.clip(linear_adobe, 0.0, 1.0), 1.0 / N.ADOBE_GAMMA)
    quantized = np.floor(encoded * 65535.0 + 0.5).astype(np.uint16)
    profile = N.adobe_rgb_icc(N.ADOBE_GAMMA)
    tifffile.imwrite(
        path, quantized, photometric="rgb", compression="zlib", metadata=None,
        resolution=(300, 300),
        extratags=[(34675, 7, len(profile), profile, False)],
    )
    valid = np.all(np.isfinite(linear_adobe), axis=2)
    return {
        "high_clip_channels": int(np.count_nonzero(quantized == 65535)),
        "high_clip_fraction": float(np.count_nonzero(quantized == 65535)
                                    / max(quantized.size, 1)),
        "finite_pixel_fraction": float(np.mean(valid)),
    }


def save_uint16_mask(path: Path, mask: np.ndarray) -> None:
    tifffile.imwrite(
        path, np.floor(np.clip(mask, 0.0, 1.0) * 65535.0 + 0.5).astype(np.uint16),
        photometric="minisblack", compression="zlib", metadata=None,
    )


def smoothstep01(value: np.ndarray) -> np.ndarray:
    x = np.clip(value, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def lunar_center(reference: H.Fotograma, solar_xy: tuple[float, float]) -> tuple[float, float, str]:
    offset = A.offset_limbe_model()
    if math.isfinite(reference.lluna_mes_x):
        lunar_x, lunar_y = reference.lluna_mes_x, reference.lluna_mes_y
        source = "measured lunar limb"
    else:
        lunar_x, lunar_y = reference.lluna_x + offset[0], reference.lluna_y + offset[1]
        source = "DE440 lunar model plus mean measured-limb offset"
    return (
        float(lunar_x + solar_xy[0] - reference.sol_x),
        float(lunar_y + solar_xy[1] - reference.sol_y),
        source,
    )


def contact_background_target(
    frames: list[H.Fotograma], data: dict[str, tuple[np.ndarray, np.ndarray]]
) -> tuple[np.ndarray, dict[str, Any]]:
    """Use only accepted contact members; never load historical 572A2972."""
    manifest = H.llegeix_manifest()
    common = next(frame for frame in manifest if frame.nom == A.NOM_EPOCA_COMUNA)
    factors = {frame.nom: A.factor_extincio(frame.t_rel_c2, common.t_rel_c2)
               for frame in frames}
    values = {
        frame.nom: (A.fons_fotograma(frame, data[frame.nom][0], factors[frame.nom])
                    / frame.exp_s)
        for frame in frames
    }
    target = np.median(np.stack(list(values.values()), axis=0), axis=0)
    if target.shape != (4,) or not np.all(np.isfinite(target)):
        raise ContractError("pedestal de contacte no finit")
    return target.astype(np.float64), {
        "policy": "median per-second sky of this contact's accepted members only",
        "hidden_572A2972_dependency_used": False,
        "target_RG1G2B_ADU_s": target.tolist(),
        "members_RG1G2B_ADU_s": {name: value.tolist() for name, value in values.items()},
    }


def drizzle_saturation_count(
    frames: list[H.Fotograma], data: dict[str, tuple[np.ndarray, np.ndarray]],
    solar_xy: tuple[float, float], shape: tuple[int, int, int],
) -> np.ndarray:
    """Count saturated CFA samples touching each output pixel footprint."""
    out = np.zeros(shape, dtype=np.uint16)
    channel_index = {"R": 0, "G1": 1, "G2": 1, "B": 2}
    for frame in frames:
        saturation = data[frame.nom][1]
        dx, dy = solar_xy[0] - frame.sol_x, solar_xy[1] - frame.sol_y
        for plane_name, (_, oy, ox) in A.plans(data[frame.nom][0]).items():
            samples = saturation[oy::2, ox::2].astype(np.uint16)
            channel = channel_index[plane_name]
            ky0, wy = A.gota(oy + 0.5 + dy)
            kx0, wx = A.gota(ox + 0.5 + dx)
            for row_offset, row_weight in enumerate(wy):
                if row_weight <= 0:
                    continue
                y_slices = A.talls(samples.shape[0], ky0 + row_offset, shape[0])
                if y_slices is None:
                    continue
                for col_offset, col_weight in enumerate(wx):
                    if col_weight <= 0:
                        continue
                    x_slices = A.talls(samples.shape[1], kx0 + col_offset, shape[1])
                    if x_slices is None:
                        continue
                    (iy, sy), (ix, sx) = y_slices, x_slices
                    out[sy, sx, channel] += samples[iy, ix]
    return out


def build_linear_contact(
    authority: ContactAuthority,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray,
    dict[str, Any], list[H.Fotograma],
]:
    manifest = {frame.nom: frame for frame in H.llegeix_manifest() if frame.usat}
    frames = [manifest[name] for name in authority.members]
    reference = manifest[authority.reference]
    if any(abs(frame.exp_s - EXPOSURE_S) > 1e-12 for frame in frames):
        raise ContractError(f"{authority.name}: grup no és exclusivament 1/3200 s")
    data = {frame.nom: A.carrega(frame) for frame in frames}
    target, target_receipt = contact_background_target(frames, data)
    # Fail closed against apila_hdr4_vixen.fons_comu() silently reading 2972.
    previous_background = A._fons_comu
    A._fons_comu = target
    info: dict[str, Any] = {
        "contact": authority.name,
        "reference": reference.nom,
        "members": [frame.nom for frame in frames],
    }
    request = {
        "nom": f"contact_{authority.name}_accepted_1-3200s",
        "ref": reference,
        "exp_s": EXPOSURE_S,
        "membres": frames,
        "r_lluna": LUNAR_RADIUS_PX,
        "marge": LUNAR_MARGIN_PX,
        "transicio": LUNAR_TRANSITION_PX,
        "hdr": True,
    }
    try:
        image, invvar, coverage = A.apila(request, data, info, mode="comuna")
    finally:
        A._fons_comu = previous_background
    if image.shape != EXPECTED_SHAPE or invvar.shape != EXPECTED_SHAPE:
        raise ContractError(f"forma inesperada {authority.name}: {image.shape}")
    variance = np.full(invvar.shape, np.nan, np.float32)
    positive = np.isfinite(invvar) & (invvar > 0)
    variance[positive] = (1.0 / invvar[positive]).astype(np.float32)
    solar_xy = (float(info["geometria"]["sol_x"]), float(info["geometria"]["sol_y"]))
    saturation = drizzle_saturation_count(frames, data, solar_xy, image.shape)
    info["contact_background_override"] = target_receipt
    info["solar_radius_model"] = {
        "radius_arcsec": SOLAR_RADIUS_ARCSEC,
        "plate_scale_arcsec_px": 2.1495,
        "radius_px": SOLAR_RADIUS_PX,
        "expression": "946.6598/2.1495",
        "historical_959_arcsec_used": False,
    }
    info["lunar_mask"] = {
        "physical_radius_px": LUNAR_RADIUS_PX,
        "margin_px": LUNAR_MARGIN_PX,
        "transition_px": LUNAR_TRANSITION_PX,
        "outer_field_mask": False,
    }
    del data
    gc.collect()
    return image, variance, invvar.astype(np.float32), coverage, saturation, info, frames


def presentation_sky_offset(
    image: np.ndarray, valid: np.ndarray, solar_xy: tuple[float, float],
    lunar_xy: tuple[float, float],
) -> tuple[np.ndarray, int]:
    stride = 4
    sample = image[::stride, ::stride]
    sample_valid = valid[::stride, ::stride]
    yy, xx = np.indices(sample_valid.shape, dtype=np.float32)
    xx *= stride
    yy *= stride
    rs = np.hypot(xx - solar_xy[0], yy - solar_xy[1]) / SOLAR_RADIUS_PX
    rl = np.hypot(xx - lunar_xy[0], yy - lunar_xy[1])
    selection = sample_valid & (rs >= 1.35) & (rs <= 1.55) & (rl > LUNAR_RADIUS_PX + 50)
    count = int(np.count_nonzero(selection))
    if count < 10_000:
        raise ContractError(f"massa pocs píxels per al pedestal visual: {count}")
    offset = np.nanmedian(sample[selection], axis=0)
    if offset.shape != (3,) or not np.all(np.isfinite(offset)):
        raise ContractError("pedestal visual invàlid")
    return offset.astype(np.float64), count


def build_soft_natural(
    image: np.ndarray, valid: np.ndarray, solar_xy: tuple[float, float],
    lunar_xy: tuple[float, float],
) -> tuple[np.ndarray, dict[str, Any]]:
    sky, sky_count = presentation_sky_offset(image, valid, solar_xy, lunar_xy)
    camera = np.asarray(image, np.float64) - sky
    adobe = N.camera_to_linear_adobe(
        camera, N.DEFAULT_WHITE_BALANCE, N.DEFAULT_CAMERA_TO_LINEAR_SRGB
    )
    adobe = np.maximum(adobe, 0.0)
    luminance = adobe @ N.ADOBE_LUMA
    yy, xx = np.indices(valid.shape, dtype=np.float32)
    lunar_radius = np.hypot(xx - lunar_xy[0], yy - lunar_xy[1])
    reference_zone = (
        valid & np.isfinite(luminance) & (luminance > 0)
        & (lunar_radius >= LUNAR_RADIUS_PX - 1.0)
        & (lunar_radius <= LUNAR_RADIUS_PX + 80.0)
    )
    values = luminance[reference_zone]
    if values.size < 10_000:
        raise ContractError(f"massa pocs píxels de limbe per a la corba: {values.size}")
    percentile = 99.7
    target = 0.68
    power = 0.92
    reference = float(np.percentile(values, percentile))
    scale = N.tone_scale(reference, target, power)
    display_luminance = N.tone_curve(luminance, scale, power)
    gain = np.zeros(luminance.shape, np.float64)
    positive = valid & np.isfinite(luminance) & (luminance > 0)
    gain[positive] = display_luminance[positive] / luminance[positive]
    visual = N.hue_preserving_gamut_shoulder(adobe * gain[..., None], 0.90)
    # Preserve explicit highlight headroom for Pere's final Photoshop curve.
    # This is one global monotonic multiplier, not local contrast or a mask.
    output_headroom = 0.985
    visual *= output_headroom
    # The only geometry mask is the measured lunar interior.  There is no
    # outer radius, field-edge mask or radial exposure blend.
    inner_gate = smoothstep01(
        (lunar_radius - (LUNAR_RADIUS_PX - 2.0)) / 4.0
    )
    visual *= inner_gate[..., None]
    visual[~valid] = 0.0
    visual = np.nan_to_num(visual, nan=0.0, posinf=0.0, neginf=0.0)
    grid = np.concatenate(([0.0], np.logspace(-12, 12, 20_000)))
    monotonic = bool(np.all(np.diff(N.tone_curve(grid, scale, power)) >= -1e-14))
    return visual.astype(np.float32), {
        "intent": "very mild natural contact layer; final user adjustment expected",
        "sky_offset_camera_RGB_ADU_s": sky.tolist(),
        "sky_sample_pixels_ds4": sky_count,
        "white_balance": N.DEFAULT_WHITE_BALANCE.tolist(),
        "camera_to_linear_srgb": N.DEFAULT_CAMERA_TO_LINEAR_SRGB.tolist(),
        "output_space": "Adobe RGB (1998)",
        "reference_zone": "physical lunar radius -1 to +80 px",
        "reference_percentile": percentile,
        "reference_luminance": reference,
        "reference_target": target,
        "tone_power": power,
        "tone_scale": scale,
        "gamut_knee": 0.90,
        "global_output_headroom": output_headroom,
        "tone_curve_monotonic": monotonic,
        "operations_absent": [
            "local contrast", "MGN", "NRGF", "denoise", "sharpen",
            "outer-field mask", "solar-radial exposure mask",
        ],
    }


def extract_halpha(
    image: np.ndarray, valid: np.ndarray, solar_xy: tuple[float, float],
    lunar_xy: tuple[float, float], lunar_radius_px: float = LUNAR_RADIUS_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Adapt the accepted historical R-rhoG method, without a field mask."""
    red = image[..., 0]
    green = image[..., 1]
    yy, xx = np.indices(valid.shape, dtype=np.float32)
    rs = np.hypot(xx - solar_xy[0], yy - solar_xy[1]) / SOLAR_RADIUS_PX
    rl = np.hypot(xx - lunar_xy[0], yy - lunar_xy[1])
    good = valid & np.isfinite(red) & np.isfinite(green)
    colour_zone = (
        good & (rs > 1.05) & (rs < 1.4) & (rl > lunar_radius_px + 6.0)
        & (green > 1e-3)
    )
    if np.count_nonzero(colour_zone) < 10_000:
        raise ContractError("massa pocs píxels per estimar rho(R/G)")
    rho = float(np.median(red[colour_zone] / green[colour_zone]))
    excess = np.where(good, red - rho * green, 0.0).astype(np.float32)
    background_ok = (rl > lunar_radius_px + 4.0) & (excess < 6.0 * 858.0) & good
    background = (
        gaussian_filter(np.where(background_ok, excess, 0.0), 40.0)
        / np.maximum(gaussian_filter(background_ok.astype(np.float32), 40.0), 1e-3)
    )
    excess_hp = np.where(rl > lunar_radius_px - 2.0, excess - background, 0.0)
    excess_hp = excess_hp.astype(np.float32)
    smooth2 = gaussian_filter(excess_hp, 2.0)
    negative = smooth2[colour_zone & (smooth2 < 0)]
    sigma = float(np.sqrt(np.mean(negative * negative))) if negative.size else 1.0
    smooth4 = gaussian_filter(excess_hp, 4.0)
    negative4 = smooth4[colour_zone & (smooth4 < 0)]
    sigma4 = float(np.sqrt(np.mean(negative4 * negative4))) if negative4.size else sigma
    inner_gate = smoothstep01((rl - (lunar_radius_px - 2.0)) / 3.0)
    # A Gaussian physical-lunar proximity prior has no hard outer boundary.
    proximity = np.exp(-0.5 * np.square(np.maximum(rl - lunar_radius_px, 0.0) / 120.0))
    mask = (
        np.clip((smooth2 - 2.0 * sigma) / max(2.0 * sigma, 1e-9), 0.0, 1.0)
        * np.clip((smooth4 - 1.5 * sigma4) / max(sigma4, 1e-9), 0.0, 1.0)
        * inner_gate * proximity * valid
    )
    mask = gaussian_filter(mask.astype(np.float32), 1.5) * inner_gate
    positive = np.clip(excess_hp, 0.0, None) * inner_gate * proximity
    return excess_hp, positive.astype(np.float32), mask.astype(np.float32), {
        "method": "E=R-rho*G; masked sigma40 background; sigma2/sigma4 confirmation",
        "rho_R_over_G": rho,
        "sigma_E_ADU_s": sigma,
        "sigma4_E_ADU_s": sigma4,
        "lunar_physical_radius_px": lunar_radius_px,
        "lunar_inner_gate": [lunar_radius_px - 2.0, lunar_radius_px + 1.0],
        "lunar_proximity_sigma_px": 120.0,
        "hard_outer_mask": False,
        "field_edge_mask": False,
    }


def halpha_renditions(
    image: np.ndarray, positive: np.ndarray, mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    camera = np.maximum(np.asarray(image, np.float64), 0.0)
    adobe = N.camera_to_linear_adobe(
        camera, N.DEFAULT_WHITE_BALANCE, N.DEFAULT_CAMERA_TO_LINEAR_SRGB
    )
    adobe = np.maximum(adobe, 0.0)
    selected = mask > 0.5
    colour = np.nanmedian(adobe[selected], axis=0) if np.any(selected) else np.array([1.0, 0.3, 0.3])
    if not np.all(np.isfinite(colour)) or np.max(colour) <= 0:
        colour = np.array([1.0, 0.3, 0.3])
    colour = np.maximum(colour, 0.0) / max(float(np.max(colour)), 1e-9)
    strong_values = positive[selected]
    normalizer = float(np.percentile(strong_values, 99.9)) if strong_values.size else float(np.max(positive))
    normalizer = max(normalizer, 1e-9)
    normalized = positive / normalizer
    # A gentle asinh view for manual inspection; the signed float authority is
    # separate and remains untouched.
    asinh_scale = 0.02
    mapped = np.arcsinh(normalized / asinh_scale) / math.asinh(1.0 / asinh_scale)
    inspection = np.clip(mapped[..., None] * colour, 0.0, 1.0)
    prominence = inspection * mask[..., None]
    return inspection.astype(np.float32), prominence.astype(np.float32), {
        "colour_adobe_rgb": colour.tolist(),
        "normalizer_E_ADU_s_p99_9_mask": normalizer,
        "asinh_scale": asinh_scale,
        "inspection_threshold_mask_applied": False,
        "prominence_threshold_mask_applied": True,
    }


def write_transforms(path: Path, frames: list[H.Fotograma], info: dict[str, Any]) -> None:
    solar = info["geometria"]
    rows = []
    for frame in frames:
        rows.append({
            "frame": frame.nom,
            "t_rel_c2_s": f"{frame.t_rel_c2:.12g}",
            "dx_output_px": f"{solar['sol_x'] - frame.sol_x:.12g}",
            "dy_output_px": f"{solar['sol_y'] - frame.sol_y:.12g}",
            "theta_deg": "0",
            "extinction_factor": f"{info['factor_extincio'][frame.nom]:.15g}",
        })
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def preview_jpeg(path: Path, natural: np.ndarray, width: int = 1800) -> None:
    encoded = np.power(np.clip(natural, 0.0, 1.0), 1.0 / N.ADOBE_GAMMA)
    scale = min(1.0, width / encoded.shape[1])
    small = cv2.resize(encoded, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(path), np.floor(np.clip(small[..., ::-1], 0, 1) * 255 + 0.5).astype(np.uint8),
                [cv2.IMWRITE_JPEG_QUALITY, 94])


def output_records(directory: Path, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    excluded = exclude or set()
    return [
        {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(directory.iterdir())
        if path.is_file() and path.name not in excluded
    ]


def build_contact(authority: ContactAuthority, destination: Path) -> dict[str, Any]:
    destination.mkdir()
    image, variance, invvar, coverage, saturation, info, frames = build_linear_contact(authority)
    valid_channels = (
        np.isfinite(image) & np.isfinite(variance) & (variance > 0)
        & np.isfinite(invvar) & (invvar > 0) & (coverage > 0)
    )
    valid = np.all(valid_channels, axis=2)
    solar_xy = (float(info["geometria"]["sol_x"]), float(info["geometria"]["sol_y"]))
    reference = next(frame for frame in frames if frame.nom == authority.reference)
    lunar_x, lunar_y, lunar_source = lunar_center(reference, solar_xy)
    lunar_xy = (lunar_x, lunar_y)

    paths = {
        "linear": destination / f"CONTACT_{authority.name}_LINEAR_FLOAT32_ADU_S.tif",
        "variance": destination / "VARIANCE_ADU2_S2.npy",
        "invvar": destination / "INVVAR_WEIGHT.npy",
        "coverage": destination / "COVERAGE_SAMPLES.npy",
        "saturation": destination / "SATURATION_DRIZZLE_FOOTPRINT_COUNT.npy",
        "valid": destination / "VALID_CHANNELS.npy",
        "natural": destination / f"CONTACT_{authority.name}_NATURAL_SOFT_ADOBERGB16.tif",
        "halpha_signed": destination / "HALPHA_EXCESS_SIGNED_FLOAT32_ADU_S.tif",
        "halpha_inspection": destination / "HALPHA_INSPECTION_SOFT_ADOBERGB16.tif",
        "prominence": destination / "PROMINENCE_LAYER_SOFT_ADOBERGB16.tif",
        "prominence_mask": destination / "PROMINENCE_MASK16.tif",
        "transforms": destination / "TRANSFORMS.csv",
        "preview": destination / "PREVIEW_NATURAL_SOFT.jpg",
    }
    save_float_rgb(paths["linear"], image, "ADU/s", "contact master; one exposure band")
    np.save(paths["variance"], variance)
    np.save(paths["invvar"], invvar)
    np.save(paths["coverage"], coverage.astype(np.uint16, copy=False))
    np.save(paths["saturation"], saturation)
    np.save(paths["valid"], valid_channels.astype(np.uint8))

    natural, natural_receipt = build_soft_natural(image, valid, solar_xy, lunar_xy)
    natural_write_qa = save_uint16_rgb_adobe(paths["natural"], natural)
    preview_jpeg(paths["preview"], natural)

    excess, positive, mask, halpha_receipt = extract_halpha(
        image, valid, solar_xy, lunar_xy
    )
    inspection, prominence, rendition_receipt = halpha_renditions(image, positive, mask)
    save_float_gray(paths["halpha_signed"], excess, "ADU/s", "signed R-rho*G excess")
    inspection_write_qa = save_uint16_rgb_adobe(paths["halpha_inspection"], inspection)
    prominence_write_qa = save_uint16_rgb_adobe(paths["prominence"], prominence)
    save_uint16_mask(paths["prominence_mask"], mask)
    write_transforms(paths["transforms"], frames, info)

    yy, xx = np.indices(valid.shape, dtype=np.float32)
    lunar_r = np.hypot(xx - lunar_x, yy - lunar_y)
    strict_interior = lunar_r < LUNAR_RADIUS_PX - 3.0
    mask_interior_max = float(np.max(mask[strict_interior]))
    qa = {
        "shape_yxc": list(image.shape),
        "finite_valid_pixel_fraction": float(np.mean(valid)),
        "coverage_median_rgb": [float(np.median(coverage[..., c])) for c in range(3)],
        "variance_median_finite_rgb": [float(np.nanmedian(variance[..., c])) for c in range(3)],
        "saturated_footprint_pixels_rgb": [int(np.count_nonzero(saturation[..., c])) for c in range(3)],
        "tone_curve_monotonic": natural_receipt["tone_curve_monotonic"],
        "natural_write": natural_write_qa,
        "halpha_inspection_write": inspection_write_qa,
        "prominence_write": prominence_write_qa,
        "prominence_mask_strict_lunar_interior_max": mask_interior_max,
        "no_outer_field_mask": True,
        "no_solar_radial_blend_mask": True,
    }
    passed = (
        image.shape == EXPECTED_SHAPE
        and qa["finite_valid_pixel_fraction"] > 0.80
        and qa["tone_curve_monotonic"]
        and natural_write_qa["high_clip_fraction"] < 1e-5
        and mask_interior_max < 1e-3
    )
    products = output_records(destination)
    receipt = {
        "schema": GROUP_SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "verdict": "ACCEPTAT" if passed else "REPROCESSAR",
        "contact": authority.name,
        "train": TRAIN,
        "frame": FRAME,
        "input_authority": {
            "authority_receipt": str(authority.authority_receipt_path),
            "authority_receipt_sha256": authority.authority_receipt_sha256,
            "upstream_receipt": str(authority.upstream_receipt_path),
            "upstream_receipt_sha256": authority.upstream_receipt_sha256,
            "verdict": authority.authority_receipt["verdict"],
            "authority_id": authority.authority_receipt["authority_id"],
            "members": list(authority.members),
            "raw_hashes_reverified": list(authority.raw_records),
            "calibrator_hashes_reverified": list(authority.calibrator_records),
        },
        "exposure_contract": {
            "bands": 1,
            "exposure_s": EXPOSURE_S,
            "weighted_hdr_mode": True,
            "output_unit": "ADU/s",
            "multi_exposure_dynamic_range_extension": False,
            "reason": "accepted C2/C3 authorities contain only 1/3200 s",
        },
        "calibration": {
            "chain": "accepted linear CFA dark+PRNU; one-pass drizzle via apila_hdr4_vixen",
            "background": info["contact_background_override"],
            "clipping_before_stack": False,
            "debayer_before_stack": False,
        },
        "registration": {
            "geometry": info["geometria"],
            "theta_deg": 0.0,
            "solar_radius": info["solar_radius_model"],
            "lunar_center_output_xy_px": [lunar_x, lunar_y],
            "lunar_center_source": lunar_source,
            "lunar_physical_radius_px": LUNAR_RADIUS_PX,
            "transforms": "TRANSFORMS.csv",
        },
        "natural": natural_receipt,
        "halpha": {**halpha_receipt, **rendition_receipt},
        "mask_policy": {
            "lunar_physical_radius_px": LUNAR_RADIUS_PX,
            "lunar_interior_gate_only_for_natural": True,
            "prominence_lunar_proximity_is_gaussian_without_hard_outer_edge": True,
            "outer_field_masks": 0,
            "solar_radial_blend_masks": 0,
        },
        "qa": qa,
        "products": products,
        "source_mutations": 0,
    }
    write_json(destination / "RECEIPT.json", receipt)
    with (destination / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for path in sorted(destination.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                handle.write(f"{sha256(path)}  {path.name}\n")
    del image, variance, invvar, coverage, saturation, valid_channels, valid
    del natural, excess, positive, mask, inspection, prominence, yy, xx, lunar_r
    gc.collect()
    return receipt


def write_root_manifest(staging: Path) -> None:
    entries = []
    for path in staging.rglob("*"):
        if path.is_file() and path != staging / "SHA256SUMS.txt":
            entries.append((path.relative_to(staging).as_posix(), sha256(path)))
    with (staging / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for relative, digest in sorted(entries):
            handle.write(f"{digest}  {relative}\n")


def run_self_test() -> dict[str, Any]:
    tests: list[str] = []
    if set(CONTACTS["C2"]["members"]) & set(CONTACTS["C3"]["members"]):
        raise AssertionError("synthetic membership separation failed")
    if len(CONTACTS["C2"]["members"]) != 9 or len(CONTACTS["C3"]["members"]) != 17:
        raise AssertionError("synthetic expected counts failed")
    tests.append("C2_C3_membership_disjoint_9_17")

    grid = np.concatenate(([0.0], np.logspace(-12, 12, 20_000)))
    scale = N.tone_scale(1000.0, 0.68, 0.92)
    if not np.all(np.diff(N.tone_curve(grid, scale, 0.92)) >= -1e-14):
        raise AssertionError("tone monotonicity failed")
    tests.append("natural_tone_monotonic")

    height = width = 512
    yy, xx = np.indices((height, width), dtype=np.float32)
    centre = (256.0, 256.0)
    radius = 80.0
    rr = np.hypot(xx - centre[0], yy - centre[1])
    image = np.zeros((height, width, 3), np.float32)
    image[..., 1] = 100.0
    image[..., 0] = 80.0
    image[..., 2] = 60.0
    injected = (rr > radius + 2) & (rr < radius + 8) & (xx > centre[0])
    image[..., 0][injected] += 200.0
    valid = np.ones((height, width), bool)
    # Use a synthetic solar radius so the colour annulus is populated.
    original_radius = globals()["SOLAR_RADIUS_PX"]
    globals()["SOLAR_RADIUS_PX"] = 120.0
    try:
        _, positive, mask, _ = extract_halpha(
            image, valid, centre, centre, lunar_radius_px=radius
        )
    finally:
        globals()["SOLAR_RADIUS_PX"] = original_radius
    background = (rr > radius + 20) & (rr < radius + 35)
    if not (float(np.median(positive[injected])) > float(np.median(positive[background]))
            and float(np.max(mask[rr < radius - 3])) < 1e-3):
        raise AssertionError("synthetic H-alpha/lunar gate failed")
    tests.append("halpha_red_excess_and_physical_lunar_gate")

    with tempfile.TemporaryDirectory(prefix="contact-layer-selftest-") as temp:
        path = Path(temp) / "SHA256SUMS.txt"
        path.write_text("0" * 64 + "  safe/file.bin\n", encoding="utf-8")
        if parse_sha256sums(path) != {"safe/file.bin": "0" * 64}:
            raise AssertionError("safe hash manifest parse failed")
        path.write_text("0" * 64 + "  ../escape\n", encoding="utf-8")
        try:
            parse_sha256sums(path)
        except ContractError:
            pass
        else:
            raise AssertionError("unsafe hash path was accepted")
    tests.append("sha256_manifest_path_guard")
    return {"status": "SELF_TEST_PASS", "tests": tests}


def build(authority_root: Path, output: Path, validate_only: bool) -> int:
    if output.exists():
        raise ContractError(f"la sortida ja existeix; no se sobreescriu: {output}")
    authority_summary, contacts = validate_authority(authority_root)
    if validate_only:
        print(json.dumps({
            "status": "VALIDATED_NO_WRITES",
            "authority": authority_summary,
            "contacts": [
                {
                    "contact": contact.name,
                    "authority_id": contact.authority_receipt["authority_id"],
                    "members": list(contact.members),
                    "reference": contact.reference,
                    "exposure_s": EXPOSURE_S,
                }
                for contact in contacts
            ],
            "C2_C3_overlap": [],
            "solar_radius_px": SOLAR_RADIUS_PX,
            "lunar_radius_px": LUNAR_RADIUS_PX,
        }, indent=2, ensure_ascii=False))
        return 0

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.partial-{uuid.uuid4().hex[:10]}"
    staging.mkdir(exist_ok=False)
    try:
        group_receipts = [build_contact(contact, staging / contact.name)
                          for contact in contacts]
        overall = all(receipt["verdict"] == "ACCEPTAT" for receipt in group_receipts)
        root_receipt = {
            "schema": RECEIPT_SCHEMA,
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "verdict": "ACCEPTAT" if overall else "REPROCESSAR",
            "authority": authority_summary,
            "contacts": [
                {
                    "name": receipt["contact"],
                    "directory": receipt["contact"],
                    "verdict": receipt["verdict"],
                    "members": receipt["input_authority"]["members"],
                }
                for receipt in group_receipts
            ],
            "separation": {
                "C2_C3_fused": False,
                "C2_C3_overlap": [],
                "independent_directories_and_receipts": True,
            },
            "scientific_scope": {
                "linear_contact_masters": True,
                "exposure_bands_per_contact": 1,
                "multi_exposure_HDR_claimed": False,
                "presentation_derivatives_are_photometric_authority": False,
            },
            "geometry": {
                "solar_radius_arcsec": SOLAR_RADIUS_ARCSEC,
                "solar_radius_px": SOLAR_RADIUS_PX,
                "lunar_physical_radius_px": LUNAR_RADIUS_PX,
                "outer_field_masks": 0,
            },
            "software": {
                "build_vixen_contact_layers.py": {
                    "path": str(Path(__file__).resolve()),
                    "sha256": sha256(Path(__file__).resolve()),
                },
                "apila_hdr4_vixen.py": {
                    "path": str(Path(A.__file__).resolve()),
                    "sha256": sha256(Path(A.__file__).resolve()),
                },
                "hdr_corona_vixen.py": {
                    "path": str(Path(H.__file__).resolve()),
                    "sha256": sha256(Path(H.__file__).resolve()),
                },
                "build_natural_composite.py": {
                    "path": str(Path(N.__file__).resolve()),
                    "sha256": sha256(Path(N.__file__).resolve()),
                },
                "python": sys.version,
                "numpy": np.__version__,
                "tifffile": tifffile.__version__,
                "argv": sys.argv,
            },
            "source_mutations": 0,
            "atomic_non_overwrite_promotion": True,
        }
        write_json(staging / "RECEIPT.json", root_receipt)
        write_root_manifest(staging)
        staging.rename(output)
    except BaseException:
        # Delete only this invocation's uniquely named staging tree.  No
        # accepted or historical path is ever a deletion target.
        if staging.exists() and staging.parent == output.parent and staging.name.startswith(
            f".{output.name}.partial-"
        ):
            shutil.rmtree(staging)
        raise
    print(json.dumps({
        "status": root_receipt["verdict"],
        "output": str(output),
        "contacts": [receipt["verdict"] for receipt in group_receipts],
    }, indent=2, ensure_ascii=False))
    return 0 if overall else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority-root", type=Path, default=DEFAULT_AUTHORITY_ROOT)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, ensure_ascii=False))
        return 0
    if args.out is None:
        parser.error("--out és obligatori excepte amb --self-test")
    return build(args.authority_root, args.out, args.validate_only)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"CONTRACT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
