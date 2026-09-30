#!/usr/bin/env python3
"""Build the gentle, editable eclipse presentation delivery.

This is an isolated *presentation* stage.  It consumes an accepted Vixen
natural composite, independently accepted C2/C3 contact products, the pinned
monochrome Sony earthshine product, and (optionally) an accepted cross-train
Sony exterior.  It never reads the visual mock-up, Kimi's PSB, RAW files or
historical masks.

The working canvas is always the native Vixen 6960 x 4640 grid.  The principal
Photoshop document and the flat final are cropped only at the last step to
6595 x 4281 at canvas offset (+182, +179).  The PSB is RGB/16-bit Adobe RGB
(1998), uses real 16-bit layer masks, and keeps these components separable:

* immutable gentle Vixen natural base (visible);
* optional accepted Sony exterior (visible only after an ACCEPTAT receipt);
* C2 natural, H-alpha and prominence options (hidden);
* C3 natural, H-alpha and local-prominence contact options (hidden);
* a neutral, structure-free lunar presentation-floor option (hidden);
* pinned monochrome Sony earthshine in the independently registered C3 lunar
  frame (hidden at low opacity, presentation-only, never absolute photometry).

No MGN, NRGF, local contrast, sharpening, denoise or radial field blend is
implemented here.  Promotion is atomic and refuses to overwrite an existing
directory.  Every consumed raster is checked against the hash list in its
receipt.  An unaccepted or incomplete cross-train receipt is recorded as
NO_CONSUMIT and contributes no pixels.

Manifest schema (paths may be absolute or relative to the manifest)::

  {
    "schema": "ECLIPSE_EDITABLE_DELIVERY_REQUEST_V1",
    "base": {
      "receipt": ".../COMPOSITE_RECEIPT.json",
      "image_role": "natural_16",
      "icc_role": "icc"
    },
    "contacts": {
      "root_receipt": ".../contact_layers/RECEIPT.json",
      "C2": {"receipt": ".../contact_layers/C2/RECEIPT.json"},
      "C3": {"receipt": ".../contact_layers/C3/RECEIPT.json"}
    },
    "gentle_detail": {
      "receipt": ".../gentle_detail/RECEIPT.json",
      "image_role": "image",
      "mask_role": "mask",
      "opacity_255": 48
    },
    "cross_train": {
      "receipt": ".../sony_cross_train_adapter/RECEIPT.json",
      "image_role": "image",
      "mask_role": "mask"
    },
    "earthshine": {
      "path": "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Earthshine/Earthshine_FINAL/earthshine_FINAL_Sony2x8s_LUM_fullres_ADU16_per_s.tif",
      "sha256": "17c3515226ee1aed184cbc34b8b5a1b50df5ead538190ace5dc1f266ab181978",
      "valid_radius_px": 267,
      "source_lunar_radius_px": 302,
      "source_center_xy_px": [800, 800],
      "plate_scale_arcsec_px": 3.234,
      "sony_to_vixen_rotation_deg": 33.0805969
    }
  }

An optional ``cross_train`` is either ``null`` or the exact three-field object
shown above.  The receipt must be a
``SONY_CROSS_TRAIN_PRESENTATION_ADAPTER_RECEIPT_V1``/``ACCEPTAT`` adapter with
``image``/``mask``/``icc`` products and ``qa.pass=true``.  The adapter must in
turn pin the live ``SONY_CROSS_TRAIN_LAYER_RECEIPT_V1`` with literal verdict
``ACCEPTADA_PER_FUSIO``, its two float32 hashes, and the exact selected natural
base/configuration.  Thus the float cross-train is never silently discarded
or improvised as display RGB inside this delivery stage.
``gentle_detail`` may be ``null`` or use the exact four-field object above.
Its receipt must be ACCEPTAT, both products must cover the
full native canvas, and ``opacity_255`` must be an integer from 1 through 96.
The blend mode is pinned to Normal; the low opacity remains editable in the
PSB and is not baked into the immutable base layer.
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
import struct
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
import tifffile
from PIL import Image, ImageCms
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, ChannelID, Compression, Resource, Tag
from psd_tools.psd.image_resources import ImageResource


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PSB_TOOLS = ROOT / "research/tools/encaix_sony"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PSB_TOOLS))

import build_natural_composite as N  # noqa: E402
from psb_utils import (  # noqa: E402
    add_mask16,
    add_pixel_layer,
    finalize_lr16,
    new_psb,
    set_merged,
)


REQUEST_SCHEMA = "ECLIPSE_EDITABLE_DELIVERY_REQUEST_V1"
RECEIPT_SCHEMA = "ECLIPSE_EDITABLE_DELIVERY_RECEIPT_V1"
BASE_SCHEMA = "ECLIPSE_NATURAL_COMPOSITE_RECEIPT_V1"
CONTACT_ROOT_SCHEMA = "VIXEN_CONTACT_LAYERS_RECEIPT_V1"
CONTACT_GROUP_SCHEMA = "VIXEN_CONTACT_LAYER_GROUP_RECEIPT_V1"
CROSS_ADAPTER_SCHEMA = "SONY_CROSS_TRAIN_PRESENTATION_ADAPTER_RECEIPT_V1"
CROSS_UPSTREAM_SCHEMA = "SONY_CROSS_TRAIN_LAYER_RECEIPT_V1"
CROSS_UPSTREAM_VERDICT = "ACCEPTADA_PER_FUSIO"
CROSS_UPSTREAM_IMAGE = "SONY_MATCHED_TO_VIXEN_LINEAR_ADU_S_FLOAT32_BIGTIFF.tif"
CROSS_UPSTREAM_MASK = "SONY_VISUAL_ALPHA_EFFECTIVE_FLOAT32_BIGTIFF.tif"

CANVAS_W = 6960
CANVAS_H = 4640
CROP_X = 182
CROP_Y = 179
CROP_W = 6595
CROP_H = 4281
EXPECTED_SHAPE = (CANVAS_H, CANVAS_W, 3)
ADOBE_GAMMA = 2.19921875
SOLAR_RADIUS_PX = 946.6598 / 2.1495

EARTHSHINE_PATH = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Earthshine/Earthshine_FINAL/"
    "earthshine_FINAL_Sony2x8s_LUM_fullres_ADU16_per_s.tif"
)
EARTHSHINE_SHA256 = (
    "17c3515226ee1aed184cbc34b8b5a1b50df5ead538190ace5dc1f266ab181978"
)
EARTHSHINE_VALID_RADIUS_PX = 267.0
EARTHSHINE_SOURCE_RADIUS_PX = 302.0
EARTHSHINE_SOURCE_CENTER_XY = (800.0, 800.0)
EARTHSHINE_PLATE_SCALE = 3.234
VIXEN_PLATE_SCALE = 2.1495
EARTHSHINE_SCALE = EARTHSHINE_PLATE_SCALE / VIXEN_PLATE_SCALE
SONY_TO_VIXEN_ROTATION_DEG = 33.0805969
EARTHSHINE_FEATHER_PX_SOURCE = 18.0
LUNAR_PHYSICAL_RADIUS_PX = 453.8
LUNAR_FLOOR_FEATHER_PX = 4.0
EARTHSHINE_LINEAR_LOW = 0.006
EARTHSHINE_LINEAR_HIGH = 0.040
EARTHSHINE_TINT = np.array([1.018, 1.0, 0.965], np.float64)
EARTHSHINE_PRESENTATION_OPACITY = 96

CONTACT_FILES = {
    "natural": "CONTACT_{contact}_NATURAL_SOFT_ADOBERGB16.tif",
    "halpha": "HALPHA_INSPECTION_SOFT_ADOBERGB16.tif",
    "prominence": "PROMINENCE_LAYER_SOFT_ADOBERGB16.tif",
    "mask": "PROMINENCE_MASK16.tif",
}
CONTACT_NATURAL_OPACITY = 92
CONTACT_HALPHA_OPACITY = 58
CONTACT_PROMINENCE_OPACITY = 32
GENTLE_DETAIL_MAX_OPACITY = 96
ANTI_RING_RELATIVE_THRESHOLD = 0.01

FORBIDDEN_SOURCE_TOKENS = (
    "maqueta de resultat esperat",
    "foto_v4b",
    "capestotalsv4b",
    "capes totals v4b",
    "/kimi/",
)


class ContractError(RuntimeError):
    """An input, geometry, provenance or output gate was not satisfied."""


@dataclass(frozen=True)
class Product:
    role: str | None
    name: str
    path: Path
    sha256: str
    bytes: int


@dataclass(frozen=True)
class ReceiptInput:
    path: Path
    sha256: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ContactInput:
    name: str
    receipt: ReceiptInput
    natural: Product
    halpha: Product
    prominence: Product
    mask: Product
    lunar_center_xy: tuple[float, float]


@dataclass(frozen=True)
class CrossTrainInput:
    status: str
    reason: str
    receipt: ReceiptInput | None
    image: Product | None
    mask: Product | None
    qa: dict[str, Any] | None


@dataclass(frozen=True)
class GentleDetailInput:
    status: str
    reason: str
    receipt: ReceiptInput | None
    image: Product | None
    mask: Product | None
    opacity: int | None


@dataclass
class LayerPatch:
    name: str
    rgb16: np.ndarray
    mask16: np.ndarray | None
    left: int
    top: int
    opacity: int
    visible: bool
    layer_class: str
    frame: str
    source: str
    source_sha256: str | None
    notes: str

    @property
    def width(self) -> int:
        return int(self.rgb16.shape[1])

    @property
    def height(self) -> int:
        return int(self.rgb16.shape[0])


@dataclass(frozen=True)
class ValidatedInputs:
    manifest_path: Path
    manifest_sha256: str
    manifest: dict[str, Any]
    base_receipt: ReceiptInput
    base_image: Product
    icc: Product
    contacts_root: ReceiptInput
    c2: ContactInput
    c3: ContactInput
    gentle_detail: GentleDetailInput
    cross_train: CrossTrainInput
    earthshine_path: Path
    earthshine_sha256: str
    solar_center_xy: tuple[float, float]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def array_digest(array: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(b"\0")
    digest.update(json.dumps(list(array.shape)).encode("ascii"))
    digest.update(b"\0")
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def resolve_manifest_path(manifest_path: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ContractError(f"falta ruta {label}")
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    return candidate.resolve()


def assert_not_forbidden(path: Path) -> None:
    lowered = path.as_posix().lower()
    if any(token in lowered for token in FORBIDDEN_SOURCE_TOKENS):
        raise ContractError(f"font visual prohibida (maqueta/Kimi): {path}")


def assert_workspace_path(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"{label} ha d'estar dins el worktree canònic: {path}") from exc
    assert_not_forbidden(path)


def receipt_input(path: Path, expected_schema: str | None = None) -> ReceiptInput:
    if not path.is_file():
        raise ContractError(f"falta rebut: {path}")
    assert_not_forbidden(path)
    data = read_json(path)
    if expected_schema is not None and data.get("schema") != expected_schema:
        raise ContractError(
            f"schema inesperat a {path}: {data.get('schema')!r}; cal {expected_schema}"
        )
    return ReceiptInput(path=path, sha256=sha256(path), data=data)


def product_records(receipt: ReceiptInput) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()
    for key in ("outputs", "products"):
        value = receipt.data.get(key)
        if isinstance(value, list):
            for record in value:
                if isinstance(record, dict):
                    product_name = record.get("name", record.get("path"))
                    identity = (record.get("role"), product_name, record.get("sha256"))
                    if identity not in seen:
                        seen.add(identity)
                        candidates.append(record)
    return candidates


def resolve_product(
    receipt: ReceiptInput,
    *,
    role: str | None = None,
    name: str | None = None,
    required: bool = True,
) -> Product | None:
    if (role is None) == (name is None):
        raise ContractError("cal declarar exactament un role o un name de producte")
    matches: list[dict[str, Any]] = []
    for record in product_records(receipt):
        if role is not None and record.get("role") == role:
            matches.append(record)
        if name is not None and record.get("name", record.get("path")) == name:
            matches.append(record)
    if len(matches) != 1:
        if not required and len(matches) == 0:
            return None
        selector = f"role={role!r}" if role is not None else f"name={name!r}"
        raise ContractError(
            f"{receipt.path}: el producte {selector} té {len(matches)} coincidències"
        )
    record = matches[0]
    product_name = record.get("name", record.get("path"))
    expected_hash = record.get("sha256")
    if not isinstance(product_name, str) or not product_name:
        raise ContractError(f"producte sense nom a {receipt.path}")
    relative = Path(product_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ContractError(f"nom de producte insegur: {product_name!r}")
    path = (receipt.path.parent / relative).resolve()
    if path.parent != receipt.path.parent.resolve() and receipt.path.parent.resolve() not in path.parents:
        raise ContractError(f"producte escapa del directori del rebut: {path}")
    assert_not_forbidden(path)
    if not path.is_file():
        raise ContractError(f"falta producte hashat: {path}")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ContractError(f"SHA-256 invàlid per {product_name}")
    actual_hash = sha256(path)
    if actual_hash != expected_hash.lower():
        raise ContractError(
            f"SHA-256 divergent {path}: {actual_hash} != {expected_hash}"
        )
    expected_bytes = record.get("bytes")
    actual_bytes = path.stat().st_size
    if expected_bytes is not None and int(expected_bytes) != actual_bytes:
        raise ContractError(f"mida divergent {path}: {actual_bytes} != {expected_bytes}")
    return Product(
        role=record.get("role") if isinstance(record.get("role"), str) else None,
        name=product_name,
        path=path,
        sha256=actual_hash,
        bytes=actual_bytes,
    )


def tiff_metadata(path: Path) -> tuple[tuple[int, ...], np.dtype[Any], bytes | None]:
    try:
        with tifffile.TiffFile(path) as document:
            page = document.pages[0]
            shape = tuple(int(value) for value in page.shape)
            dtype = np.dtype(page.dtype)
            tag = page.tags.get(34675)
            icc = bytes(tag.value) if tag is not None else None
    except Exception as exc:  # tifffile raises several format-specific errors.
        raise ContractError(f"TIFF invàlid {path}: {exc}") from exc
    return shape, dtype, icc


def verify_rgb16_tiff(path: Path, icc_expected: bytes | None = None) -> None:
    shape, dtype, icc = tiff_metadata(path)
    if shape != EXPECTED_SHAPE or dtype != np.dtype(np.uint16):
        raise ContractError(f"TIFF RGB16 inesperat {path}: shape={shape}, dtype={dtype}")
    if icc_expected is not None and icc != icc_expected:
        raise ContractError(f"ICC divergent a {path}")


def verify_mask16_tiff(path: Path) -> None:
    shape, dtype, _ = tiff_metadata(path)
    if shape != EXPECTED_SHAPE[:2] or dtype != np.dtype(np.uint16):
        raise ContractError(f"màscara 16-bit inesperada {path}: {shape}, {dtype}")


def verify_float_rgb_tiff(path: Path) -> None:
    shape, dtype, _ = tiff_metadata(path)
    if shape != EXPECTED_SHAPE or dtype != np.dtype(np.float32):
        raise ContractError(f"TIFF RGB float32 inesperat {path}: {shape}, {dtype}")


def verify_float_mask_tiff(path: Path) -> None:
    shape, dtype, _ = tiff_metadata(path)
    if shape != EXPECTED_SHAPE[:2] or dtype != np.dtype(np.float32):
        raise ContractError(f"màscara float32 inesperada {path}: {shape}, {dtype}")


def validate_base(manifest_path: Path, spec: Any) -> tuple[ReceiptInput, Product, Product, tuple[float, float]]:
    if not isinstance(spec, dict):
        raise ContractError("base ha de ser un objecte")
    path = resolve_manifest_path(manifest_path, spec.get("receipt"), "base.receipt")
    assert_workspace_path(path, "base.receipt")
    receipt = receipt_input(path, BASE_SCHEMA)
    data = receipt.data
    if data.get("verdict") != "ACCEPTAT" or data.get("stage") != "VIXEN_HDR_AND_NATURAL_PRESENTATION":
        raise ContractError("la base Vixen no és un compost natural ACCEPTAT")
    if data.get("qa", {}).get("pass") is not True:
        raise ContractError("la QA de la base Vixen no és PASS")
    if int(data.get("hdr", {}).get("circular_or_radial_masks", -1)) != 0:
        raise ContractError("la base declara màscares circulars/radials")
    absent = {
        str(value).strip().lower().replace("_", " ")
        for value in data.get("natural", {}).get("config", {}).get("operations_absent", [])
    }
    required_absent = {"mgn", "nrgf", "local contrast", "denoise"}
    if not required_absent.issubset(absent):
        raise ContractError(
            f"la base no demostra absència de {sorted(required_absent - absent)}"
        )
    image_role = spec.get("image_role", "natural_16")
    icc_role = spec.get("icc_role", "icc")
    if not isinstance(image_role, str) or not isinstance(icc_role, str):
        raise ContractError("base.image_role/base.icc_role invàlids")
    image = resolve_product(receipt, role=image_role)
    icc = resolve_product(receipt, role=icc_role)
    assert image is not None and icc is not None
    icc_bytes = icc.path.read_bytes()
    verify_rgb16_tiff(image.path, icc_bytes)
    geometry = data.get("geometry", {})
    if geometry.get("shape_yxc") != list(EXPECTED_SHAPE):
        raise ContractError(f"llenç base inesperat: {geometry.get('shape_yxc')}")
    center = geometry.get("solar_center_xy_px")
    if not isinstance(center, list) or len(center) != 2:
        raise ContractError("falta centre solar a la base")
    center_xy = (float(center[0]), float(center[1]))
    if not all(math.isfinite(value) for value in center_xy):
        raise ContractError("centre solar no finit")
    if abs(float(geometry.get("solar_radius_px", 0.0)) - SOLAR_RADIUS_PX) > 1e-6:
        raise ContractError("la base no usa el radi solar físic DE440+IAU")
    return receipt, image, icc, center_xy


def validate_contact_group(
    manifest_path: Path,
    name: str,
    spec: Any,
    root_receipt: ReceiptInput,
    icc_bytes: bytes,
) -> ContactInput:
    if not isinstance(spec, dict):
        raise ContractError(f"contacts.{name} ha de ser un objecte")
    path = resolve_manifest_path(manifest_path, spec.get("receipt"), f"contacts.{name}.receipt")
    assert_workspace_path(path, f"contacts.{name}.receipt")
    receipt = receipt_input(path, CONTACT_GROUP_SCHEMA)
    data = receipt.data
    if data.get("verdict") != "ACCEPTAT" or data.get("contact") != name:
        raise ContractError(f"contacte {name} no és ACCEPTAT o està mal identificat")
    if data.get("input_authority", {}).get("verdict") != "ACCEPTAT":
        raise ContractError(f"autoritat upstream del contacte {name} no acceptada")
    if data.get("qa", {}).get("tone_curve_monotonic") is not True:
        raise ContractError(f"contacte {name}: corba tonal no demostrada monòtona")
    policy = data.get("mask_policy", {})
    if int(policy.get("outer_field_masks", -1)) != 0:
        raise ContractError(f"contacte {name}: conté màscara de camp exterior")
    root_entries = root_receipt.data.get("contacts")
    if not isinstance(root_entries, list):
        raise ContractError("rebut arrel de contactes sense catàleg")
    matches = [entry for entry in root_entries if isinstance(entry, dict) and entry.get("name") == name]
    if len(matches) != 1 or matches[0].get("verdict") != "ACCEPTAT":
        raise ContractError(f"contacte {name} no acceptat inequívocament pel rebut arrel")
    if matches[0].get("members") != data.get("input_authority", {}).get("members"):
        raise ContractError(f"membres {name} divergeixen entre rebuts")
    names = {
        key: spec.get(f"{key}_name", template.format(contact=name))
        for key, template in CONTACT_FILES.items()
    }
    if not all(isinstance(value, str) and value for value in names.values()):
        raise ContractError(f"noms de producte invàlids per {name}")
    natural = resolve_product(receipt, name=names["natural"])
    halpha = resolve_product(receipt, name=names["halpha"])
    prominence = resolve_product(receipt, name=names["prominence"])
    mask = resolve_product(receipt, name=names["mask"])
    assert (
        natural is not None
        and halpha is not None
        and prominence is not None
        and mask is not None
    )
    verify_rgb16_tiff(natural.path, icc_bytes)
    verify_rgb16_tiff(halpha.path, icc_bytes)
    verify_rgb16_tiff(prominence.path, icc_bytes)
    verify_mask16_tiff(mask.path)
    registration = data.get("registration", {})
    center = registration.get("lunar_center_output_xy_px")
    if not isinstance(center, list) or len(center) != 2:
        raise ContractError(f"contacte {name}: falta centre lunar")
    lunar_center = (float(center[0]), float(center[1]))
    if not all(math.isfinite(value) for value in lunar_center):
        raise ContractError(f"contacte {name}: centre lunar no finit")
    if abs(float(registration.get("lunar_physical_radius_px", 0.0)) - 453.8) > 1e-6:
        raise ContractError(f"contacte {name}: radi lunar físic inesperat")
    return ContactInput(
        name, receipt, natural, halpha, prominence, mask, lunar_center
    )


def validate_contacts(
    manifest_path: Path, spec: Any, icc_bytes: bytes
) -> tuple[ReceiptInput, ContactInput, ContactInput]:
    if not isinstance(spec, dict):
        raise ContractError("contacts ha de ser un objecte")
    root_path = resolve_manifest_path(
        manifest_path, spec.get("root_receipt"), "contacts.root_receipt"
    )
    assert_workspace_path(root_path, "contacts.root_receipt")
    root_receipt = receipt_input(root_path, CONTACT_ROOT_SCHEMA)
    root = root_receipt.data
    if root.get("verdict") != "ACCEPTAT":
        raise ContractError("el paquet de contactes no és ACCEPTAT")
    separation = root.get("separation", {})
    if separation.get("C2_C3_fused") is not False or separation.get("C2_C3_overlap") != []:
        raise ContractError("C2 i C3 no estan demostrats com a productes separats")
    c2 = validate_contact_group(manifest_path, "C2", spec.get("C2"), root_receipt, icc_bytes)
    c3 = validate_contact_group(manifest_path, "C3", spec.get("C3"), root_receipt, icc_bytes)
    if set(c2.receipt.data["input_authority"]["members"]) & set(
        c3.receipt.data["input_authority"]["members"]
    ):
        raise ContractError("C2/C3 comparteixen fotogrames")
    return root_receipt, c2, c3


def validate_cross_train(
    manifest_path: Path,
    spec: Any,
    icc_bytes: bytes,
    base_receipt: ReceiptInput,
) -> CrossTrainInput:
    if spec is None:
        return CrossTrainInput(
            "NO_CONSUMIT", "extensió no declarada", None, None, None, None
        )
    if not isinstance(spec, dict):
        raise ContractError("cross_train ha de ser null o un objecte")
    if set(spec) != {"receipt", "image_role", "mask_role"}:
        raise ContractError(
            "cross_train ha de declarar exactament receipt, image_role i mask_role"
        )
    if spec.get("image_role") != "image" or spec.get("mask_role") != "mask":
        raise ContractError("cross_train exigeix image_role='image' i mask_role='mask'")
    path = resolve_manifest_path(manifest_path, spec.get("receipt"), "cross_train.receipt")
    assert_workspace_path(path, "cross_train.receipt")
    receipt = receipt_input(path, CROSS_ADAPTER_SCHEMA)
    if receipt.data.get("verdict") != "ACCEPTAT":
        raise ContractError(
            f"adaptador cross_train té veredicte {receipt.data.get('verdict')!r}, no ACCEPTAT"
        )
    if receipt.data.get("qa", {}).get("pass") is not True:
        raise ContractError("adaptador cross_train no demostra qa.pass=true")

    upstream = receipt.data.get("upstream_cross_train")
    if not isinstance(upstream, dict):
        raise ContractError("adaptador cross_train sense bloc upstream_cross_train")
    required_upstream = {
        "receipt",
        "receipt_sha256",
        "schema",
        "verdict",
        "image_name",
        "image_sha256",
        "mask_name",
        "mask_sha256",
    }
    if set(upstream) != required_upstream:
        raise ContractError(
            "upstream_cross_train ha de contenir exactament "
            f"{sorted(required_upstream)}"
        )
    if (
        upstream.get("schema") != CROSS_UPSTREAM_SCHEMA
        or upstream.get("verdict") != CROSS_UPSTREAM_VERDICT
        or upstream.get("image_name") != CROSS_UPSTREAM_IMAGE
        or upstream.get("mask_name") != CROSS_UPSTREAM_MASK
    ):
        raise ContractError("identitat/schema/veredicte upstream cross_train divergent")
    raw_upstream_path = upstream.get("receipt")
    if not isinstance(raw_upstream_path, str) or not raw_upstream_path:
        raise ContractError("upstream_cross_train.receipt invàlid")
    upstream_path = Path(raw_upstream_path).expanduser()
    if not upstream_path.is_absolute():
        upstream_path = receipt.path.parent / upstream_path
    upstream_path = upstream_path.resolve()
    assert_workspace_path(upstream_path, "upstream_cross_train.receipt")
    upstream_receipt = receipt_input(upstream_path, CROSS_UPSTREAM_SCHEMA)
    if upstream_receipt.sha256 != upstream.get("receipt_sha256"):
        raise ContractError("hash del rebut upstream cross_train divergent")
    if upstream_receipt.data.get("verdict") != CROSS_UPSTREAM_VERDICT:
        raise ContractError("veredicte viu upstream cross_train divergent")
    upstream_image = resolve_product(upstream_receipt, name=CROSS_UPSTREAM_IMAGE)
    upstream_mask = resolve_product(upstream_receipt, name=CROSS_UPSTREAM_MASK)
    assert upstream_image is not None and upstream_mask is not None
    if (
        upstream_image.sha256 != upstream.get("image_sha256")
        or upstream_mask.sha256 != upstream.get("mask_sha256")
    ):
        raise ContractError("hashos dels float upstream cross_train divergents")
    verify_float_rgb_tiff(upstream_image.path)
    verify_float_mask_tiff(upstream_mask.path)

    base_anchor = receipt.data.get("base_natural")
    if not isinstance(base_anchor, dict):
        raise ContractError("adaptador cross_train sense base_natural")
    required_base_anchor = {
        "receipt",
        "receipt_sha256",
        "schema",
        "verdict",
        "directory_name",
        "natural_config_sha256",
        "manifest_sha256",
    }
    if not required_base_anchor.issubset(base_anchor):
        raise ContractError(
            "base_natural ha de contenir com a mínim "
            f"{sorted(required_base_anchor)}"
        )
    natural_config_hash = canonical_json_digest(
        base_receipt.data.get("natural", {}).get("config")
    )
    if (
        base_anchor.get("receipt") != str(base_receipt.path)
        or base_anchor.get("receipt_sha256") != base_receipt.sha256
        or base_anchor.get("schema") != BASE_SCHEMA
        or base_anchor.get("verdict") != "ACCEPTAT"
        or base_anchor.get("directory_name") != base_receipt.path.parent.name
        or base_anchor.get("natural_config_sha256") != natural_config_hash
        or base_anchor.get("manifest_sha256")
        != base_receipt.data.get("manifest", {}).get("sha256")
    ):
        raise ContractError("adaptador cross_train no està revelat contra la base seleccionada")

    image = resolve_product(receipt, role="image")
    mask = resolve_product(receipt, role="mask")
    adapter_icc = resolve_product(receipt, role="icc")
    assert image is not None and mask is not None and adapter_icc is not None
    verify_rgb16_tiff(image.path, icc_bytes)
    verify_mask16_tiff(mask.path)
    if adapter_icc.path.read_bytes() != icc_bytes:
        raise ContractError("ICC del producte adaptador cross_train divergent")
    alpha = tifffile.imread(upstream_mask.path)
    quantized = tifffile.imread(mask.path)
    if (
        alpha.shape != EXPECTED_SHAPE[:2]
        or alpha.dtype != np.float32
        or quantized.shape != EXPECTED_SHAPE[:2]
        or quantized.dtype != np.uint16
        or not np.all(np.isfinite(alpha))
        or float(np.min(alpha)) < 0.0
        or float(np.max(alpha)) > 1.0
    ):
        raise ContractError("domini alpha cross_train invàlid")
    support_equal = bool(np.array_equal(quantized > 0, alpha > 0))
    maximum_error = float(
        np.max(np.abs(quantized.astype(np.float32) / 65535.0 - alpha))
    )
    sub_lsb_positive = int(np.count_nonzero((alpha > 0) & (alpha < 0.5 / 65535.0)))
    if not support_equal or maximum_error > 1.0 / 65535.0 + 2e-8:
        raise ContractError(
            "quantització MASK16 cross_train no preserva suport/error <=1/65535"
        )
    cross_qa = {
        "adapter_schema": CROSS_ADAPTER_SCHEMA,
        "upstream_schema": CROSS_UPSTREAM_SCHEMA,
        "upstream_verdict": CROSS_UPSTREAM_VERDICT,
        "base_natural_config_sha256": natural_config_hash,
        "mask_support_exact": support_equal,
        "mask_maximum_absolute_error": maximum_error,
        "mask_error_limit": 1.0 / 65535.0,
        "positive_alpha_below_half_lsb": sub_lsb_positive,
    }
    del alpha, quantized
    return CrossTrainInput(
        "CONSUMIT_ACCEPTAT",
        (
            "adaptador ACCEPTAT; upstream SONY_CROSS_TRAIN_LAYER_RECEIPT_V1 "
            "ACCEPTADA_PER_FUSIO i floats hashats verificats"
        ),
        receipt,
        image,
        mask,
        cross_qa,
    )


def gentle_detail_opacity(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError("gentle_detail.opacity_255 ha de ser un enter")
    if not 1 <= value <= GENTLE_DETAIL_MAX_OPACITY:
        raise ContractError(
            "gentle_detail.opacity_255 ha d'estar entre 1 i "
            f"{GENTLE_DETAIL_MAX_OPACITY} (opacitat baixa)"
        )
    return value


def validate_gentle_detail(
    manifest_path: Path,
    spec: Any,
    icc_bytes: bytes,
    base_receipt: ReceiptInput,
) -> GentleDetailInput:
    if spec is None:
        return GentleDetailInput(
            "NO_CONSUMIT", "extensió no declarada", None, None, None, None
        )
    if not isinstance(spec, dict):
        raise ContractError("gentle_detail ha de ser null o un objecte")
    allowed = {"receipt", "image_role", "mask_role", "opacity_255"}
    if set(spec) != allowed:
        raise ContractError(
            "gentle_detail ha de declarar exactament receipt, image_role, "
            "mask_role i opacity_255"
        )
    if spec.get("image_role") != "image" or spec.get("mask_role") != "mask":
        raise ContractError("gentle_detail exigeix image_role='image' i mask_role='mask'")
    opacity = gentle_detail_opacity(spec.get("opacity_255"))
    path = resolve_manifest_path(
        manifest_path, spec.get("receipt"), "gentle_detail.receipt"
    )
    assert_workspace_path(path, "gentle_detail.receipt")
    receipt = receipt_input(path)
    if not isinstance(receipt.data.get("schema"), str) or not receipt.data.get("schema"):
        raise ContractError("gentle_detail: rebut sense schema literal")
    if receipt.data.get("verdict") != "ACCEPTAT":
        return GentleDetailInput(
            "NO_CONSUMIT",
            f"veredicte {receipt.data.get('verdict')!r}, no ACCEPTAT",
            receipt,
            None,
            None,
            opacity,
        )
    if receipt.data.get("frame") != "CORONA_SOLAR_VIXEN_COMMON_GRID":
        raise ContractError(
            "gentle_detail ACCEPTAT no declara frame CORONA_SOLAR_VIXEN_COMMON_GRID"
        )
    base_anchor = receipt.data.get("base_natural")
    if not isinstance(base_anchor, dict) or set(base_anchor) != {
        "receipt",
        "receipt_sha256",
    }:
        raise ContractError(
            "gentle_detail ACCEPTAT ha de declarar base_natural.receipt/receipt_sha256"
        )
    if (
        base_anchor.get("receipt") != str(base_receipt.path)
        or base_anchor.get("receipt_sha256") != base_receipt.sha256
    ):
        raise ContractError("gentle_detail està ancorat a un altre fonament")
    image = resolve_product(receipt, role="image", required=False)
    mask = resolve_product(receipt, role="mask", required=False)
    if image is None or mask is None:
        return GentleDetailInput(
            "NO_CONSUMIT",
            "selectors sense productes hashats",
            receipt,
            None,
            None,
            opacity,
        )
    verify_rgb16_tiff(image.path, icc_bytes)
    verify_mask16_tiff(mask.path)
    if receipt.data.get("qa", {}).get("pass") is not True:
        return GentleDetailInput(
            "NO_CONSUMIT", "falta qa.pass=true", receipt, None, None, opacity
        )
    return GentleDetailInput(
        "CONSUMIT_ACCEPTAT",
        "rebut ACCEPTAT, RGB16/ICC, màscara16 i hashes verificats",
        receipt,
        image,
        mask,
        opacity,
    )


def require_close(actual: Any, expected: float, label: str, tolerance: float = 1e-9) -> None:
    try:
        value = float(actual)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label} invàlid") from exc
    if not math.isfinite(value) or abs(value - expected) > tolerance:
        raise ContractError(f"{label}={value!r}; cal {expected}")


def validate_earthshine(manifest_path: Path, spec: Any) -> tuple[Path, str]:
    if not isinstance(spec, dict):
        raise ContractError("earthshine ha de ser un objecte explícit")
    path = resolve_manifest_path(manifest_path, spec.get("path"), "earthshine.path")
    if path != EARTHSHINE_PATH.resolve():
        raise ContractError(f"earthshine no és el producte autoritzat: {path}")
    if spec.get("sha256") != EARTHSHINE_SHA256:
        raise ContractError("earthshine.sha256 no reafirma el hash autoritzat")
    require_close(spec.get("valid_radius_px"), EARTHSHINE_VALID_RADIUS_PX, "valid_radius_px")
    require_close(spec.get("source_lunar_radius_px"), EARTHSHINE_SOURCE_RADIUS_PX, "source_lunar_radius_px")
    require_close(spec.get("plate_scale_arcsec_px"), EARTHSHINE_PLATE_SCALE, "plate_scale_arcsec_px")
    require_close(
        spec.get("sony_to_vixen_rotation_deg"),
        SONY_TO_VIXEN_ROTATION_DEG,
        "sony_to_vixen_rotation_deg",
    )
    center = spec.get("source_center_xy_px")
    if not isinstance(center, list) or len(center) != 2:
        raise ContractError("earthshine.source_center_xy_px ha de ser [800,800]")
    require_close(center[0], EARTHSHINE_SOURCE_CENTER_XY[0], "source_center_x")
    require_close(center[1], EARTHSHINE_SOURCE_CENTER_XY[1], "source_center_y")
    if not path.is_file():
        raise ContractError(f"falta earthshine: {path}")
    actual_hash = sha256(path)
    if actual_hash != EARTHSHINE_SHA256:
        raise ContractError(f"hash earthshine divergent: {actual_hash}")
    shape, dtype, icc = tiff_metadata(path)
    if shape != (1600, 1600) or dtype != np.dtype(np.float32) or icc is not None:
        raise ContractError(f"autoritat earthshine inesperada: {shape}, {dtype}, ICC={icc is not None}")
    return path, actual_hash


def validate_inputs(manifest_path: Path) -> ValidatedInputs:
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise ContractError(f"falta manifest: {manifest_path}")
    assert_workspace_path(manifest_path, "manifest")
    manifest = read_json(manifest_path)
    if manifest.get("schema") != REQUEST_SCHEMA:
        raise ContractError(f"schema de manifest inesperat: {manifest.get('schema')!r}")
    allowed = {
        "schema",
        "base",
        "contacts",
        "gentle_detail",
        "cross_train",
        "earthshine",
    }
    extra = set(manifest) - allowed
    if extra:
        raise ContractError(f"camps de manifest desconeguts: {sorted(extra)}")
    base_receipt, base_image, icc, solar_center = validate_base(
        manifest_path, manifest.get("base")
    )
    icc_bytes = icc.path.read_bytes()
    if icc_bytes != N.adobe_rgb_icc(ADOBE_GAMMA):
        raise ContractError("ICC base no és l'Adobe RGB (1998) pinat pel pipeline")
    contacts_root, c2, c3 = validate_contacts(
        manifest_path, manifest.get("contacts"), icc_bytes
    )
    gentle = validate_gentle_detail(
        manifest_path, manifest.get("gentle_detail"), icc_bytes, base_receipt
    )
    cross = validate_cross_train(
        manifest_path, manifest.get("cross_train"), icc_bytes, base_receipt
    )
    earth_path, earth_hash = validate_earthshine(manifest_path, manifest.get("earthshine"))
    return ValidatedInputs(
        manifest_path=manifest_path,
        manifest_sha256=sha256(manifest_path),
        manifest=manifest,
        base_receipt=base_receipt,
        base_image=base_image,
        icc=icc,
        contacts_root=contacts_root,
        c2=c2,
        c3=c3,
        gentle_detail=gentle,
        cross_train=cross,
        earthshine_path=earth_path,
        earthshine_sha256=earth_hash,
        solar_center_xy=solar_center,
    )


def load_rgb16(path: Path) -> np.ndarray:
    array = tifffile.imread(path)
    if array.shape != EXPECTED_SHAPE or array.dtype != np.uint16:
        raise ContractError(f"RGB16 canviat després de validar: {path}")
    return array


def load_mask16(path: Path) -> np.ndarray:
    array = tifffile.imread(path)
    if array.shape != EXPECTED_SHAPE[:2] or array.dtype != np.uint16:
        raise ContractError(f"màscara canviada després de validar: {path}")
    return array


def nonzero_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    rows = np.flatnonzero(np.any(mask != 0, axis=1))
    columns = np.flatnonzero(np.any(mask != 0, axis=0))
    if rows.size == 0 or columns.size == 0:
        return None
    return int(columns[0]), int(rows[0]), int(columns[-1] + 1), int(rows[-1] + 1)


def product_patch(
    image: Product,
    mask: Product,
    *,
    name: str,
    opacity: int,
    visible: bool,
    layer_class: str,
    frame: str,
    notes: str,
) -> LayerPatch:
    mask_full = load_mask16(mask.path)
    bbox = nonzero_bbox(mask_full)
    if bbox is None:
        raise ContractError(f"màscara buida: {mask.path}")
    x0, y0, x1, y1 = bbox
    mask_patch = np.ascontiguousarray(mask_full[y0:y1, x0:x1])
    del mask_full
    image_full = load_rgb16(image.path)
    rgb_patch = np.ascontiguousarray(image_full[y0:y1, x0:x1])
    del image_full
    return LayerPatch(
        name=name,
        rgb16=rgb_patch,
        mask16=mask_patch,
        left=x0,
        top=y0,
        opacity=opacity,
        visible=visible,
        layer_class=layer_class,
        frame=frame,
        source=str(image.path),
        source_sha256=image.sha256,
        notes=notes,
    )


def full_size_product_layer(
    image: Product,
    mask: Product,
    *,
    name: str,
    opacity: int,
    visible: bool,
    layer_class: str,
    frame: str,
    notes: str,
) -> LayerPatch:
    return LayerPatch(
        name=name,
        rgb16=np.ascontiguousarray(load_rgb16(image.path)),
        mask16=np.ascontiguousarray(load_mask16(mask.path)),
        left=0,
        top=0,
        opacity=opacity,
        visible=visible,
        layer_class=layer_class,
        frame=frame,
        source=str(image.path),
        source_sha256=image.sha256,
        notes=notes,
    )


def contact_patches(
    contact: ContactInput, *, prominence_visible: bool
) -> tuple[LayerPatch, LayerPatch, LayerPatch]:
    hidden_note = "opció amagada; cap contribució al merged"
    natural = product_patch(
        contact.natural,
        contact.mask,
        name=f"{contact.name} · contacte natural suau (amagat)",
        opacity=CONTACT_NATURAL_OPACITY,
        visible=False,
        layer_class="FONT_PROTEGIDA_PRESENTACIO",
        frame=f"CONTACTE_{contact.name}_SOLAR_AMB_PORTA_LUNAR_PROPIA",
        notes=f"{hidden_note}; màscara de prominències hashada del mateix contacte",
    )
    halpha = product_patch(
        contact.halpha,
        contact.mask,
        name=f"{contact.name} · H-alpha suau (amagat)",
        opacity=CONTACT_HALPHA_OPACITY,
        visible=False,
        layer_class="COLOR_PRESENTACIO_H_ALPHA",
        frame=f"CONTACTE_{contact.name}_SOLAR_AMB_PORTA_LUNAR_PROPIA",
        notes=f"{hidden_note}; derivat R-rho*G, no torna al HDR científic",
    )
    prominence = product_patch(
        contact.prominence,
        contact.mask,
        name=(
            f"{contact.name} · prominència local suau"
            + ("" if prominence_visible else " (amagat)")
        ),
        opacity=CONTACT_PROMINENCE_OPACITY,
        visible=prominence_visible,
        layer_class="PROMINENCIA_LOCAL_PRESENTACIO",
        frame=f"CONTACTE_{contact.name}_SOLAR_AMB_PORTA_LUNAR_PROPIA",
        notes=(
            "visible molt suau; opacitat 32/255 passa el gate anti-anell"
            if prominence_visible
            else "opció amagada; cap contribució al merged"
        ) + "; producte presentacional local, no torna al HDR científic",
    )
    return natural, halpha, prominence


def smoothstep01(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def earthshine_visual(source: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    yy, xx = np.indices(source.shape, dtype=np.float32)
    radius = np.hypot(xx - EARTHSHINE_SOURCE_CENTER_XY[0], yy - EARTHSHINE_SOURCE_CENTER_XY[1])
    valid = radius < EARTHSHINE_VALID_RADIUS_PX
    values = source[valid].astype(np.float64)
    if values.size < 200_000 or not np.all(np.isfinite(values)):
        raise ContractError("suport vàlid earthshine insuficient o no finit")
    p01, p50, p99 = np.percentile(values, [1.0, 50.0, 99.0])
    if not p01 < p50 < p99 or p99 - p01 < 1e-6:
        raise ContractError("rang earthshine degenerat")
    normalized = np.clip((source.astype(np.float64) - p01) / (p99 - p01), 0.0, 1.0)
    # One global, monotonic and deliberately restrained presentation curve.
    curve_power = 1.08
    mapped = np.power(normalized, curve_power)
    linear_low = EARTHSHINE_LINEAR_LOW
    linear_high = EARTHSHINE_LINEAR_HIGH
    luminance = linear_low + (linear_high - linear_low) * mapped
    tint = EARTHSHINE_TINT.copy()
    tint /= float(tint @ N.ADOBE_LUMA)
    linear_rgb = np.clip(luminance[..., None] * tint, 0.0, 1.0)
    encoded = np.power(linear_rgb, 1.0 / ADOBE_GAMMA)
    rgb16 = np.floor(encoded * 65535.0 + 0.5).astype(np.uint16)
    # The authority is valid only inside r<267.  Feathering happens *inside*
    # that support; no invalid annulus is invented.
    mask = smoothstep01(
        (EARTHSHINE_VALID_RADIUS_PX - radius) / EARTHSHINE_FEATHER_PX_SOURCE
    )
    mask *= valid
    mask16 = np.floor(mask * 65535.0 + 0.5).astype(np.uint16)
    rgb16[~valid] = 0
    grid = np.linspace(float(p01), float(p99), 20_000)
    grid_norm = np.clip((grid - p01) / (p99 - p01), 0.0, 1.0)
    monotonic = bool(np.all(np.diff(np.power(grid_norm, curve_power)) >= 0))
    receipt = {
        "source_percentiles_ADU16_s": {"p01": float(p01), "p50": float(p50), "p99": float(p99)},
        "curve": "clip((x-p01)/(p99-p01),0,1)^1.08; one global monotonic curve",
        "curve_power": curve_power,
        "linear_luminance_range": [linear_low, linear_high],
        "neutral_warm_tint_adobe_rgb_luma_normalized": tint.tolist(),
        "monotonic": monotonic,
        "valid_radius_px_source": EARTHSHINE_VALID_RADIUS_PX,
        "feather_px_source_inside_valid_support": EARTHSHINE_FEATHER_PX_SOURCE,
        "photometric_authority": False,
        "visual_smoothing_or_denoise": False,
    }
    return rgb16, mask16, receipt


def affine_source_to_patch(
    source_center: tuple[float, float],
    destination_center: tuple[float, float],
    scale: float,
    angle_deg: float,
    patch_origin: tuple[int, int],
) -> np.ndarray:
    theta = math.radians(angle_deg)
    alpha = scale * math.cos(theta)
    beta = scale * math.sin(theta)
    sx, sy = source_center
    dx, dy = destination_center
    ox, oy = patch_origin
    return np.array(
        [
            [alpha, beta, dx - ox - alpha * sx - beta * sy],
            [-beta, alpha, dy - oy + beta * sx - alpha * sy],
        ],
        dtype=np.float64,
    )


def earthshine_patch(
    path: Path, source_hash: str, lunar_center: tuple[float, float]
) -> tuple[LayerPatch, dict[str, Any]]:
    source = tifffile.imread(path)
    if source.shape != (1600, 1600) or source.dtype != np.float32:
        raise ContractError("earthshine canviat després de validar")
    rgb16, mask16, tone_receipt = earthshine_visual(source)
    transformed_valid_radius = EARTHSHINE_VALID_RADIUS_PX * EARTHSHINE_SCALE
    margin = 4
    x0 = max(0, int(math.floor(lunar_center[0] - transformed_valid_radius)) - margin)
    y0 = max(0, int(math.floor(lunar_center[1] - transformed_valid_radius)) - margin)
    x1 = min(CANVAS_W, int(math.ceil(lunar_center[0] + transformed_valid_radius)) + margin + 1)
    y1 = min(CANVAS_H, int(math.ceil(lunar_center[1] + transformed_valid_radius)) + margin + 1)
    if x1 <= x0 or y1 <= y0:
        raise ContractError("earthshine queda fora del llenç Vixen")
    matrix = affine_source_to_patch(
        EARTHSHINE_SOURCE_CENTER_XY,
        lunar_center,
        EARTHSHINE_SCALE,
        SONY_TO_VIXEN_ROTATION_DEG,
        (x0, y0),
    )
    size = (x1 - x0, y1 - y0)
    warped_rgb = cv2.warpAffine(
        rgb16,
        matrix,
        size,
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    warped_mask = cv2.warpAffine(
        mask16,
        matrix,
        size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    warped_rgb = np.clip(warped_rgb, 0, 65535).astype(np.uint16, copy=False)
    warped_mask = np.clip(warped_mask, 0, 65535).astype(np.uint16, copy=False)
    if np.count_nonzero(warped_mask) < 100_000:
        raise ContractError("màscara earthshine transformada massa petita")
    # Verify the affine centre directly, independently of the resampled image.
    center_h = np.array([*EARTHSHINE_SOURCE_CENTER_XY, 1.0])
    center_patch = matrix @ center_h
    center_canvas = center_patch + np.array([x0, y0], np.float64)
    residual = float(np.hypot(*(center_canvas - np.asarray(lunar_center))))
    if residual > 1e-9:
        raise ContractError(f"residu de centre earthshine: {residual}")
    output_radius = EARTHSHINE_SOURCE_RADIUS_PX * EARTHSHINE_SCALE
    if abs(output_radius - 453.8) > 1.0:
        raise ContractError(f"escala lunar inconsistent: R={output_radius:.4f} px")
    receipt = {
        **tone_receipt,
        "frame": "LLUNA_C3",
        "source_center_xy_px": list(EARTHSHINE_SOURCE_CENTER_XY),
        "destination_lunar_center_xy_px": list(lunar_center),
        "source_lunar_radius_px": EARTHSHINE_SOURCE_RADIUS_PX,
        "scale_expression": "3.234/2.1495",
        "scale": EARTHSHINE_SCALE,
        "output_lunar_radius_px": output_radius,
        "sony_to_vixen_rotation_deg": SONY_TO_VIXEN_ROTATION_DEG,
        "affine_source_to_patch": matrix.tolist(),
        "patch_origin_xy": [x0, y0],
        "center_residual_px": residual,
        "interpolation_raster": "OpenCV cubic; presentation derivative only",
        "interpolation_mask": "OpenCV linear; hard zeros outside valid support reimposed by source mask",
        "independent_validation": "LROC WAC out-of-sample r=0.68 full scale; stellar orientation agreement is independent",
        "corona_8s_policy": "Sony 8 s corona remains quarantined; this lunar product has its own LROC validation",
    }
    layer = LayerPatch(
        name="LLUNA C3 · earthshine Sony monocrom suau (amagat)",
        rgb16=np.ascontiguousarray(warped_rgb),
        mask16=np.ascontiguousarray(warped_mask),
        left=x0,
        top=y0,
        opacity=EARTHSHINE_PRESENTATION_OPACITY,
        visible=False,
        layer_class="FONT_PROTEGIDA_PRESENTACIO_LLUNA",
        frame="LLUNA_C3",
        source=str(path),
        source_sha256=source_hash,
        notes=(
            "amagat per defecte perquè el suport validat acaba abans del limbe; "
            "opacitat 96/255; no fotometria absoluta; no entra al HDR coronal"
        ),
    )
    return layer, receipt


def lunar_floor_patch(
    lunar_center: tuple[float, float], source_path: Path, source_hash: str
) -> tuple[LayerPatch, dict[str, Any]]:
    """Create a dark, structure-free owner for the unvalidated lunar annulus.

    This is explicitly a presentation layer, not an extrapolation of lunar
    geography.  Its one constant level is the lower endpoint of the global
    earthshine display mapping.  The independently validated earthshine
    raster remains a separate layer above it.
    """
    radius = LUNAR_PHYSICAL_RADIUS_PX
    margin = 2
    x0 = max(0, int(math.floor(lunar_center[0] - radius)) - margin)
    y0 = max(0, int(math.floor(lunar_center[1] - radius)) - margin)
    x1 = min(CANVAS_W, int(math.ceil(lunar_center[0] + radius)) + margin + 1)
    y1 = min(CANVAS_H, int(math.ceil(lunar_center[1] + radius)) + margin + 1)
    if x1 <= x0 or y1 <= y0:
        raise ContractError("el nivell lunar neutre queda fora del llenç Vixen")

    yy, xx = np.indices((y1 - y0, x1 - x0), dtype=np.float32)
    distance = np.hypot(xx + x0 - lunar_center[0], yy + y0 - lunar_center[1])
    support = distance < radius
    mask = smoothstep01((radius - distance) / LUNAR_FLOOR_FEATHER_PX)
    mask *= support
    mask16 = np.floor(mask * 65535.0 + 0.5).astype(np.uint16)

    tint = EARTHSHINE_TINT.copy()
    tint /= float(tint @ N.ADOBE_LUMA)
    linear_rgb = np.clip(EARTHSHINE_LINEAR_LOW * tint, 0.0, 1.0)
    encoded_rgb = np.power(linear_rgb, 1.0 / ADOBE_GAMMA)
    value16 = np.floor(encoded_rgb * 65535.0 + 0.5).astype(np.uint16)
    rgb16 = np.broadcast_to(value16, (y1 - y0, x1 - x0, 3)).copy()
    rgb16[~support] = 0

    layer = LayerPatch(
        name="LLUNA C3 · nivell neutre sense relleu (amagat; no científic)",
        rgb16=np.ascontiguousarray(rgb16),
        mask16=np.ascontiguousarray(mask16),
        left=x0,
        top=y0,
        opacity=255,
        visible=False,
        layer_class="VISUALITZACIO_LLUNA_SENSE_ESTRUCTURA",
        frame="LLUNA_C3",
        source=str(source_path),
        source_sha256=source_hash,
        notes=(
            "nivell únic igual al mínim visual de l'earthshine; sense relleu, "
            "sense extrapolar geografia i sense autoritat fotomètrica"
        ),
    )
    receipt = {
        "purpose": "own the otherwise black annulus between valid earthshine and physical lunar limb",
        "classification": "VISUALITZACIO; structure-free; not scientific data",
        "frame": "LLUNA_C3",
        "destination_lunar_center_xy_px": list(lunar_center),
        "physical_lunar_radius_px": radius,
        "inner_valid_earthshine_radius_px": (
            EARTHSHINE_VALID_RADIUS_PX * EARTHSHINE_SCALE
        ),
        "feather_px_inside_physical_limb": LUNAR_FLOOR_FEATHER_PX,
        "constant_linear_luminance": EARTHSHINE_LINEAR_LOW,
        "neutral_warm_tint_adobe_rgb_luma_normalized": tint.tolist(),
        "lunar_structure_added": False,
        "absolute_photometry": False,
        "source_raster_pixels_reused_for_structure": False,
    }
    return layer, receipt


def placeholder_cross_train(reason: str) -> LayerPatch:
    return LayerPatch(
        name="SONY exterior · NO CONSUMIT (amagat)",
        rgb16=np.zeros((1, 1, 3), np.uint16),
        mask16=np.zeros((1, 1), np.uint16),
        left=0,
        top=0,
        opacity=255,
        visible=False,
        layer_class="PLACEHOLDER_NO_PIXELS",
        frame="CORONA_SOLAR",
        source="",
        source_sha256=None,
        notes=reason,
    )


def gentle_detail_patch(gentle: GentleDetailInput) -> LayerPatch | None:
    if gentle.status != "CONSUMIT_ACCEPTAT":
        return None
    assert (
        gentle.image is not None
        and gentle.mask is not None
        and gentle.opacity is not None
    )
    return full_size_product_layer(
        gentle.image,
        gentle.mask,
        name="DETALL SUAU · AdobeRGB16 ACCEPTAT",
        opacity=gentle.opacity,
        visible=True,
        layer_class="DETALL_PRESENTACIO_GENTLE",
        frame="CORONA_SOLAR_VIXEN_COMMON_GRID",
        notes=(
            "Normal a opacitat baixa; capa separada, reversible i no bakejada "
            "a la base Vixen"
        ),
    )


def cross_train_patch(cross: CrossTrainInput) -> LayerPatch:
    if cross.status != "CONSUMIT_ACCEPTAT":
        return placeholder_cross_train(cross.reason)
    assert cross.image is not None and cross.mask is not None
    return product_patch(
        cross.image,
        cross.mask,
        name="SONY exterior · cross-train ACCEPTAT",
        opacity=255,
        visible=True,
        layer_class="FONT_HDR_CROSS_TRAIN_ACCEPTADA",
        frame="CORONA_SOLAR_VIXEN_COMMON_GRID",
        notes="només domini acceptat pel rebut cross-train; 8 s coronal no és autoritzat aquí",
    )


def effective_mask(mask16: np.ndarray | None, opacity: int) -> np.ndarray | None:
    if mask16 is None:
        if opacity == 255:
            return None
        raise ContractError("opacitat parcial sense màscara només s'admet en capa amb màscara")
    if not 0 <= opacity <= 255:
        raise ContractError(f"opacitat invàlida: {opacity}")
    if opacity == 255:
        return mask16
    return ((mask16.astype(np.uint32) * opacity + 127) // 255).astype(np.uint16)


def composite_patch(destination: np.ndarray, patch: LayerPatch) -> None:
    if not patch.visible:
        return
    x0, y0 = patch.left, patch.top
    x1, y1 = x0 + patch.width, y0 + patch.height
    height, width = destination.shape[:2]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ContractError(f"capa fora de llenç: {patch.name} bbox={(x0,y0,x1,y1)}")
    mask = effective_mask(patch.mask16, patch.opacity)
    target = destination[y0:y1, x0:x1]
    if mask is None:
        target[...] = patch.rgb16
        return
    for row0 in range(0, patch.height, 128):
        row1 = min(row0 + 128, patch.height)
        alpha = mask[row0:row1].astype(np.uint64)[..., None]
        inverse = 65535 - alpha
        source = patch.rgb16[row0:row1].astype(np.uint64)
        current = target[row0:row1].astype(np.uint64)
        blended = (source * alpha + current * inverse + 32767) // 65535
        target[row0:row1] = blended.astype(np.uint16)


def patch_intersection_with_crop(patch: LayerPatch) -> LayerPatch:
    px0, py0 = patch.left, patch.top
    px1, py1 = px0 + patch.width, py0 + patch.height
    cx0, cy0, cx1, cy1 = CROP_X, CROP_Y, CROP_X + CROP_W, CROP_Y + CROP_H
    x0, y0 = max(px0, cx0), max(py0, cy0)
    x1, y1 = min(px1, cx1), min(py1, cy1)
    if x1 <= x0 or y1 <= y0:
        if patch.visible:
            raise ContractError(f"capa visible fora del retall final: {patch.name}")
        return LayerPatch(
            name=patch.name,
            rgb16=np.zeros((1, 1, 3), np.uint16),
            mask16=np.zeros((1, 1), np.uint16),
            left=0,
            top=0,
            opacity=patch.opacity,
            visible=False,
            layer_class=patch.layer_class,
            frame=patch.frame,
            source=patch.source,
            source_sha256=patch.source_sha256,
            notes=patch.notes + "; fora del retall final",
        )
    sy0, sx0 = y0 - py0, x0 - px0
    sy1, sx1 = y1 - py0, x1 - px0
    return LayerPatch(
        name=patch.name,
        rgb16=np.ascontiguousarray(patch.rgb16[sy0:sy1, sx0:sx1]),
        mask16=(
            np.ascontiguousarray(patch.mask16[sy0:sy1, sx0:sx1])
            if patch.mask16 is not None
            else None
        ),
        left=x0 - CROP_X,
        top=y0 - CROP_Y,
        opacity=patch.opacity,
        visible=patch.visible,
        layer_class=patch.layer_class,
        frame=patch.frame,
        source=patch.source,
        source_sha256=patch.source_sha256,
        notes=patch.notes,
    )


def encoded_adobe_luminance(rgb16: np.ndarray) -> np.ndarray:
    linear = np.power(rgb16.astype(np.float32) / 65535.0, ADOBE_GAMMA)
    return linear @ N.ADOBE_LUMA.astype(np.float32)


def anti_ring_qa(
    base: np.ndarray,
    final: np.ndarray,
    center_xy: tuple[float, float],
) -> dict[str, Any]:
    stride = 2
    base_sample = base[::stride, ::stride]
    final_sample = final[::stride, ::stride]
    base_luma = encoded_adobe_luminance(base_sample)
    final_luma = encoded_adobe_luminance(final_sample)
    valid = np.isfinite(base_luma) & np.isfinite(final_luma) & (base_luma > 0) & (final_luma > 0)
    args = (
        valid,
        center_xy,
        SOLAR_RADIUS_PX,
        stride,
        4.0,
        5.0,
        1.15,
        8.5,
        0.08,
        ANTI_RING_RELATIVE_THRESHOLD,
        12,
    )
    base_scan = N.annular_ring_scan(base_luma, *args)
    final_scan = N.annular_ring_scan(final_luma, *args)
    base_radii = [item["radius_px"] for item in base_scan["candidates"]]
    new = [
        item
        for item in final_scan["candidates"]
        if not any(abs(item["radius_px"] - radius) <= 4.0 for radius in base_radii)
    ]
    return {
        "domain_rsun": [1.15, 8.5],
        "base": base_scan,
        "final": final_scan,
        "new_candidate_count": len(new),
        "new_candidates": new[:32],
        "pass": len(new) == 0,
        "note": (
            "llindar relatiu 0,01: cap capa, inclòs gentle_detail, pot "
            "introduir candidats que la base no tenia; fenòmens locals C3 "
            "no compleixen 12 sectors coincidents"
        ),
    }


def lunar_mask_edge_qa(layer: LayerPatch, lunar_center: tuple[float, float]) -> dict[str, Any]:
    if layer.mask16 is None:
        raise ContractError("earthshine sense màscara")
    yy, xx = np.indices(layer.mask16.shape, dtype=np.float32)
    radius = np.hypot(xx + layer.left - lunar_center[0], yy + layer.top - lunar_center[1])
    maximum_radius = int(math.ceil(float(np.max(radius))))
    indices = np.floor(radius).astype(np.int32)
    sums = np.bincount(indices.ravel(), weights=(layer.mask16.astype(np.float64) / 65535.0).ravel(), minlength=maximum_radius + 1)
    counts = np.bincount(indices.ravel(), minlength=maximum_radius + 1)
    profile = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    transformed_valid = EARTHSHINE_VALID_RADIUS_PX * EARTHSHINE_SCALE
    lo = max(1, int(math.floor(transformed_valid - EARTHSHINE_FEATHER_PX_SOURCE * EARTHSHINE_SCALE - 5)))
    hi = min(len(profile) - 1, int(math.ceil(transformed_valid + 3)))
    gradient = np.abs(np.diff(profile[lo:hi + 1]))
    maximum_step = float(np.max(gradient)) if gradient.size else math.inf
    outer_nonzero = int(np.count_nonzero(layer.mask16[radius >= transformed_valid + 1.5]))
    passed = maximum_step < 0.075 and outer_nonzero == 0
    return {
        "transformed_valid_radius_px": transformed_valid,
        "radial_profile_range_px": [lo, hi],
        "maximum_adjacent_radial_mask_step": maximum_step,
        "outer_nonzero_pixels_beyond_valid_plus_1_5px": outer_nonzero,
        "pass": passed,
    }


def lunar_floor_edge_qa(
    layer: LayerPatch, lunar_center: tuple[float, float]
) -> dict[str, Any]:
    if layer.mask16 is None:
        raise ContractError("nivell lunar neutre sense màscara")
    yy, xx = np.indices(layer.mask16.shape, dtype=np.float32)
    radius = np.hypot(
        xx + layer.left - lunar_center[0],
        yy + layer.top - lunar_center[1],
    )
    outer_nonzero = int(
        np.count_nonzero(layer.mask16[radius >= LUNAR_PHYSICAL_RADIUS_PX + 1.0])
    )
    annulus = (
        (radius >= LUNAR_PHYSICAL_RADIUS_PX - LUNAR_FLOOR_FEATHER_PX - 2.0)
        & (radius <= LUNAR_PHYSICAL_RADIUS_PX + 2.0)
    )
    indices = np.floor(radius[annulus]).astype(np.int32)
    values = layer.mask16[annulus].astype(np.float64) / 65535.0
    sums = np.bincount(indices, weights=values)
    counts = np.bincount(indices)
    profile = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    occupied = np.flatnonzero(counts > 0)
    radial = profile[occupied]
    monotonic = bool(np.all(np.diff(radial) <= 2e-3)) if radial.size > 1 else False
    passed = outer_nonzero == 0 and monotonic
    return {
        "physical_lunar_radius_px": LUNAR_PHYSICAL_RADIUS_PX,
        "feather_px_inside_physical_limb": LUNAR_FLOOR_FEATHER_PX,
        "outer_nonzero_pixels_beyond_limb_plus_1px": outer_nonzero,
        "radial_mask_monotonic_nonincreasing": monotonic,
        "pass": passed,
    }


def clipping_qa(base: np.ndarray, final: np.ndarray, crop: np.ndarray) -> dict[str, Any]:
    def stats(array: np.ndarray) -> dict[str, Any]:
        return {
            "high_clip_channels": int(np.count_nonzero(array == 65535)),
            "high_clip_fraction": float(np.mean(array == 65535)),
            "black_channels": int(np.count_nonzero(array == 0)),
            "black_fraction": float(np.mean(array == 0)),
        }

    base_stats = stats(base)
    full_stats = stats(final)
    crop_stats = stats(crop)
    base_p99 = float(np.percentile(encoded_adobe_luminance(base[::4, ::4]), 99.0))
    final_p99 = float(np.percentile(encoded_adobe_luminance(final[::4, ::4]), 99.0))
    ratio = final_p99 / base_p99 if base_p99 > 0 else math.inf
    passed = (
        full_stats["high_clip_fraction"] <= max(1e-6, base_stats["high_clip_fraction"] + 1e-7)
        and crop_stats["high_clip_fraction"] <= max(1e-6, base_stats["high_clip_fraction"] + 1e-7)
        and 0.90 <= ratio <= 1.10
    )
    return {
        "base": base_stats,
        "full_canvas": full_stats,
        "final_crop": crop_stats,
        "p99_linear_luminance_base": base_p99,
        "p99_linear_luminance_final": final_p99,
        "p99_ratio_final_over_base": ratio,
        "soft_tone_gate": [0.90, 1.10],
        "pass": passed,
    }


def save_rgb16_tiff(path: Path, array: np.ndarray, icc: bytes, description: str) -> None:
    tifffile.imwrite(
        path,
        array,
        photometric="rgb",
        compression="adobe_deflate",
        predictor=True,
        resolution=(300, 300),
        resolutionunit="INCH",
        metadata=None,
        description=description,
        extratags=[(34675, 7, len(icc), icc, False)],
    )


def save_srgb_preview(path: Path, crop: np.ndarray, adobe_icc: bytes, width: int = 2000) -> dict[str, Any]:
    scale = min(1.0, width / crop.shape[1])
    encoded8 = ((crop.astype(np.uint32) + 128) // 257).astype(np.uint8)
    if scale < 1.0:
        encoded8 = cv2.resize(
            encoded8,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )
    image = Image.fromarray(encoded8, mode="RGB")
    adobe_profile = ImageCms.ImageCmsProfile(io.BytesIO(adobe_icc))
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    converted = ImageCms.profileToProfile(
        image,
        adobe_profile,
        srgb_profile,
        renderingIntent=0,
        outputMode="RGB",
    )
    srgb_bytes = srgb_profile.tobytes()
    converted.save(path, format="PNG", icc_profile=srgb_bytes, optimize=True)
    with Image.open(path) as reopened:
        reopened_icc = reopened.info.get("icc_profile")
        if reopened.mode != "RGB" or reopened.size != converted.size or reopened_icc != srgb_bytes:
            raise ContractError("round-trip PNG sRGB fallit")
    return {
        "size_xy": list(converted.size),
        "mode": "RGB8_sRGB_preview_only",
        "srgb_icc_sha256": hashlib.sha256(srgb_bytes).hexdigest(),
    }


def resolution_resource() -> ImageResource:
    return ImageResource(
        signature=b"8BIM",
        key=Resource.RESOLUTION_INFO,
        name="",
        data=struct.pack(">IHHIHH", 300 << 16, 1, 1, 300 << 16, 1, 1),
    )


def layer_record(layer: LayerPatch) -> dict[str, Any]:
    return {
        "name": layer.name,
        "visible": layer.visible,
        "opacity_255": layer.opacity,
        "class": layer.layer_class,
        "frame": layer.frame,
        "bbox_xywh_in_document": [layer.left, layer.top, layer.width, layer.height],
        "source": layer.source,
        "source_sha256": layer.source_sha256,
        "raster_array_sha256": array_digest(layer.rgb16),
        "mask16_array_sha256": array_digest(layer.mask16) if layer.mask16 is not None else None,
        "notes": layer.notes,
    }


def build_psb(
    path: Path,
    crop_base: np.ndarray,
    crop_final: np.ndarray,
    layers: list[LayerPatch],
    icc: bytes,
) -> list[dict[str, Any]]:
    document = new_psb(CROP_W, CROP_H, icc_bytes=icc)
    document._record.image_resources[Resource.RESOLUTION_INFO] = resolution_resource()
    base_name = "BASE · Vixen NATURAL suau (immutable)"
    add_pixel_layer(
        document,
        crop_base,
        base_name,
        top=0,
        left=0,
        visible=True,
        opacity=255,
        compression=Compression.ZIP_WITH_PREDICTION,
    )
    cropped_layers = [patch_intersection_with_crop(layer) for layer in layers]
    for layer in cropped_layers:
        psb_layer = add_pixel_layer(
            document,
            layer.rgb16,
            layer.name,
            top=layer.top,
            left=layer.left,
            visible=layer.visible,
            opacity=layer.opacity,
            compression=Compression.ZIP_WITH_PREDICTION,
        )
        if layer.mask16 is not None:
            add_mask16(
                psb_layer,
                layer.mask16,
                top=layer.top,
                left=layer.left,
                compression=Compression.ZIP_WITH_PREDICTION,
            )
    finalize_lr16(document)
    set_merged(document, crop_final, compression=Compression.RAW)
    document.save(path)
    expected = [
        {
            "name": base_name,
            "rgb16": crop_base,
            "mask16": None,
            "left": 0,
            "top": 0,
            "visible": True,
            "opacity": 255,
        }
    ] + [
        {
            "name": layer.name,
            "rgb16": layer.rgb16,
            "mask16": layer.mask16,
            "left": layer.left,
            "top": layer.top,
            "visible": layer.visible,
            "opacity": layer.opacity,
        }
        for layer in cropped_layers
    ]
    qa = verify_psb(path, expected, crop_final, icc)
    return qa


def channel_bytes(layer: Any, channel_id: ChannelID, depth: int, version: int) -> bytes:
    for info, data in zip(layer._record.channel_info, layer._channels):
        if info.id == channel_id:
            return data.get_data(layer.width, layer.height, depth, version)
    raise ContractError(f"canal {channel_id} absent a {layer.name}")


def verify_psb(
    path: Path,
    expected: list[dict[str, Any]],
    merged: np.ndarray,
    icc: bytes,
) -> list[dict[str, Any]]:
    document = PSDImage.open(path)
    header = document._record.header
    expected_height, expected_width = merged.shape[:2]
    if (document.width, document.height, document.depth, header.version) != (
        expected_width,
        expected_height,
        16,
        2,
    ):
        raise ContractError(
            f"capçalera PSB no és {expected_width}x{expected_height} RGB16 PSB v2"
        )
    if document.color_mode.name != "RGB":
        raise ContractError(f"mode PSB inesperat: {document.color_mode}")
    if document.image_resources.get_data(Resource.ICC_PROFILE) != icc:
        raise ContractError("ICC PSB no preservat")
    tagged = document._record.layer_and_mask_information.tagged_blocks
    if tagged is None or Tag.LAYER_16 not in tagged:
        raise ContractError("PSB no conté el bloc Lr16")
    layers = list(document)
    if [layer.name for layer in layers] != [item["name"] for item in expected]:
        raise ContractError("ordre/noms de capes PSB divergent")
    version = header.version
    records: list[dict[str, Any]] = []
    for layer, item in zip(layers, expected):
        if (
            layer.left != item["left"]
            or layer.top != item["top"]
            or layer.width != item["rgb16"].shape[1]
            or layer.height != item["rgb16"].shape[0]
            or bool(layer.visible) != item["visible"]
            or int(layer.opacity) != item["opacity"]
            or layer.blend_mode != BlendMode.NORMAL
        ):
            raise ContractError(f"metadades de capa divergents: {layer.name}")
        raster_ok = True
        for channel in range(3):
            raw = channel_bytes(layer, ChannelID(channel), 16, version)
            actual = np.frombuffer(raw, dtype=">u2").reshape(layer.height, layer.width)
            if not np.array_equal(actual, item["rgb16"][..., channel]):
                raster_ok = False
                break
        if not raster_ok:
            raise ContractError(f"round-trip ràster 16-bit fallit: {layer.name}")
        expected_mask = item["mask16"]
        if expected_mask is None:
            mask_ok = layer.mask is None
        else:
            raw = channel_bytes(layer, ChannelID.USER_LAYER_MASK, 16, version)
            actual_mask = np.frombuffer(raw, dtype=">u2").reshape(layer.height, layer.width)
            mask_ok = np.array_equal(actual_mask, expected_mask)
        if not mask_ok:
            raise ContractError(f"round-trip màscara 16-bit fallit: {layer.name}")
        records.append({
            "name": layer.name,
            "raster16_roundtrip": True,
            "mask16_roundtrip": expected_mask is not None,
            "visible": bool(layer.visible),
            "opacity_255": int(layer.opacity),
            "blend_mode": "normal",
            "bbox": [layer.left, layer.top, layer.width, layer.height],
        })
    merged_channels = document._record.image_data.get_data(header)
    if len(merged_channels) != 3:
        raise ContractError("merged PSB no té tres canals")
    for channel, raw in enumerate(merged_channels):
        actual = np.frombuffer(raw, dtype=">u2").reshape(expected_height, expected_width)
        if not np.array_equal(actual, merged[..., channel]):
            raise ContractError(f"merged PSB divergent al canal {channel}")
    return records


def output_records(directory: Path, paths: Iterable[tuple[str, Path]]) -> list[dict[str, Any]]:
    return [
        {
            "role": role,
            "name": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for role, path in paths
    ]


def input_summary(inputs: ValidatedInputs) -> dict[str, Any]:
    cross = inputs.cross_train
    gentle = inputs.gentle_detail
    return {
        "manifest": {"path": str(inputs.manifest_path), "sha256": inputs.manifest_sha256},
        "base": {
            "receipt": str(inputs.base_receipt.path),
            "receipt_sha256": inputs.base_receipt.sha256,
            "image": str(inputs.base_image.path),
            "image_sha256": inputs.base_image.sha256,
            "icc": str(inputs.icc.path),
            "icc_sha256": inputs.icc.sha256,
        },
        "contacts": {
            "root_receipt": str(inputs.contacts_root.path),
            "root_receipt_sha256": inputs.contacts_root.sha256,
            "C2": {
                "receipt": str(inputs.c2.receipt.path),
                "receipt_sha256": inputs.c2.receipt.sha256,
                "natural_sha256": inputs.c2.natural.sha256,
                "halpha_sha256": inputs.c2.halpha.sha256,
                "prominence_sha256": inputs.c2.prominence.sha256,
                "mask_sha256": inputs.c2.mask.sha256,
                "lunar_center_xy": list(inputs.c2.lunar_center_xy),
            },
            "C3": {
                "receipt": str(inputs.c3.receipt.path),
                "receipt_sha256": inputs.c3.receipt.sha256,
                "natural_sha256": inputs.c3.natural.sha256,
                "halpha_sha256": inputs.c3.halpha.sha256,
                "prominence_sha256": inputs.c3.prominence.sha256,
                "mask_sha256": inputs.c3.mask.sha256,
                "lunar_center_xy": list(inputs.c3.lunar_center_xy),
            },
        },
        "gentle_detail": {
            "status": gentle.status,
            "reason": gentle.reason,
            "receipt": str(gentle.receipt.path) if gentle.receipt else None,
            "receipt_sha256": gentle.receipt.sha256 if gentle.receipt else None,
            "receipt_schema": (
                gentle.receipt.data.get("schema") if gentle.receipt else None
            ),
            "image_sha256": gentle.image.sha256 if gentle.image else None,
            "mask_sha256": gentle.mask.sha256 if gentle.mask else None,
            "opacity_255": gentle.opacity,
            "blend_mode": "normal",
            "base_baked": False,
        },
        "cross_train": {
            "status": cross.status,
            "reason": cross.reason,
            "receipt": str(cross.receipt.path) if cross.receipt else None,
            "receipt_sha256": cross.receipt.sha256 if cross.receipt else None,
            "image_sha256": cross.image.sha256 if cross.image else None,
            "mask_sha256": cross.mask.sha256 if cross.mask else None,
            "qa": cross.qa,
        },
        "earthshine": {
            "path": str(inputs.earthshine_path),
            "sha256": inputs.earthshine_sha256,
            "authority": "monochrome Sony 2x8 s lunar product; valid r<267 px",
            "absolute_photometry": False,
            "independent_validation": "LROC WAC out-of-sample",
        },
        "forbidden_sources_consumed": [],
    }


def build(inputs: ValidatedInputs, output: Path, validate_only: bool) -> int:
    output = output.expanduser().resolve()
    assert_workspace_path(output, "output")
    if output.exists():
        raise ContractError(f"la sortida ja existeix; no se sobreescriu: {output}")
    validation = {
        "status": "VALIDATED_NO_WRITES" if validate_only else "VALIDATED",
        "canvas_xy": [CANVAS_W, CANVAS_H],
        "final_crop_xywh": [CROP_X, CROP_Y, CROP_W, CROP_H],
        "solar_center_xy": list(inputs.solar_center_xy),
        "solar_radius_px": SOLAR_RADIUS_PX,
        "cross_train": {
            "status": inputs.cross_train.status,
            "reason": inputs.cross_train.reason,
        },
        "gentle_detail": {
            "status": inputs.gentle_detail.status,
            "reason": inputs.gentle_detail.reason,
            "opacity_255": inputs.gentle_detail.opacity,
            "blend_mode": "normal",
        },
        "C2_visible": False,
        "C3_visible": {
            "natural": False,
            "halpha": False,
            "prominence": False,
            "prominence_opacity_255": CONTACT_PROMINENCE_OPACITY,
        },
        "lunar_floor_visible": False,
        "earthshine_visible": False,
        "earthshine_opacity_255": EARTHSHINE_PRESENTATION_OPACITY,
        "earthshine_frame": "LLUNA_C3",
    }
    if validate_only:
        print(json.dumps(validation, indent=2, ensure_ascii=False))
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.partial-{uuid.uuid4().hex[:10]}"
    staging.mkdir(exist_ok=False)
    try:
        icc_bytes = inputs.icc.path.read_bytes()
        base = load_rgb16(inputs.base_image.path)
        final_full = np.array(base, copy=True)

        detail_layer = gentle_detail_patch(inputs.gentle_detail)
        cross_layer = cross_train_patch(inputs.cross_train)
        c2_natural, c2_halpha, c2_prominence = contact_patches(
            inputs.c2, prominence_visible=False
        )
        c3_natural, c3_halpha, c3_prominence = contact_patches(
            inputs.c3, prominence_visible=False
        )
        lunar_floor_layer, lunar_floor_receipt = lunar_floor_patch(
            inputs.c3.lunar_center_xy,
            inputs.earthshine_path,
            inputs.earthshine_sha256,
        )
        earth_layer, earth_receipt = earthshine_patch(
            inputs.earthshine_path, inputs.earthshine_sha256, inputs.c3.lunar_center_xy
        )
        layers = [
            *([detail_layer] if detail_layer is not None else []),
            cross_layer,
            c2_natural,
            c2_halpha,
            c2_prominence,
            c3_natural,
            c3_halpha,
            lunar_floor_layer,
            earth_layer,
            c3_prominence,
        ]
        for layer in layers:
            composite_patch(final_full, layer)

        crop_base = np.ascontiguousarray(
            base[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
        )
        crop_final = np.ascontiguousarray(
            final_full[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
        )
        if crop_final.shape != (CROP_H, CROP_W, 3):
            raise ContractError(f"retall final incorrecte: {crop_final.shape}")

        ring = anti_ring_qa(base, final_full, inputs.solar_center_xy)
        lunar_edge = lunar_mask_edge_qa(earth_layer, inputs.c3.lunar_center_xy)
        lunar_floor_edge = lunar_floor_edge_qa(
            lunar_floor_layer, inputs.c3.lunar_center_xy
        )
        clipping = clipping_qa(base, final_full, crop_final)
        visible_union = np.zeros((CANVAS_H, CANVAS_W), bool)
        for layer in layers:
            if layer.visible and layer.mask16 is not None:
                y0, x0 = layer.top, layer.left
                visible_union[y0:y0 + layer.height, x0:x0 + layer.width] |= (
                    effective_mask(layer.mask16, layer.opacity) > 0
                )
        outside_identical = bool(np.array_equal(final_full[~visible_union], base[~visible_union]))
        if not (
            ring["pass"]
            and lunar_edge["pass"]
            and lunar_floor_edge["pass"]
            and clipping["pass"]
            and outside_identical
        ):
            raise ContractError(
                "QA final fallida: "
                f"anti_ring={ring['pass']} lunar_edge={lunar_edge['pass']} "
                f"lunar_floor_edge={lunar_floor_edge['pass']} "
                f"clipping={clipping['pass']} outside={outside_identical}"
            )

        paths = {
            "final_tiff": staging / "ECLIPSE_NATURAL_FINAL_6595x4281_ADOBERGB16.tif",
            "preview_png": staging / "ECLIPSE_NATURAL_FINAL_6595x4281_PREVIEW_sRGB.png",
            "editable_psb": staging / "ECLIPSE_NATURAL_EDITABLE_6595x4281_ADOBERGB16.psb",
            "icc": staging / "AdobeRGB1998.icc",
            "receipt": staging / "DELIVERY_RECEIPT.json",
            "sha256sums": staging / "SHA256SUMS.txt",
        }
        paths["icc"].write_bytes(icc_bytes)
        save_rgb16_tiff(
            paths["final_tiff"],
            crop_final,
            icc_bytes,
            "Natural restrained eclipse presentation; final crop +182,+179 from Vixen 6960x4640; Adobe RGB (1998); no local contrast/MGN/NRGF/denoise.",
        )
        shape, dtype, reopened_icc = tiff_metadata(paths["final_tiff"])
        reopened_tiff = tifffile.imread(paths["final_tiff"])
        tiff_roundtrip = (
            shape == crop_final.shape
            and dtype == np.dtype(np.uint16)
            and reopened_icc == icc_bytes
            and np.array_equal(reopened_tiff, crop_final)
        )
        if not tiff_roundtrip:
            raise ContractError("round-trip TIFF final fallit")
        del reopened_tiff
        preview_qa = save_srgb_preview(paths["preview_png"], crop_final, icc_bytes)
        psb_qa = build_psb(
            paths["editable_psb"], crop_base, crop_final, layers, icc_bytes
        )

        base_layer_record = {
            "name": "BASE · Vixen NATURAL suau (immutable)",
            "visible": True,
            "opacity_255": 255,
            "blend_mode": "normal",
            "class": "BASE_NATURAL_PRESENTACIO",
            "frame": "CORONA_SOLAR_VIXEN_COMMON_GRID",
            "bbox_xywh_in_document": [0, 0, CANVAS_W, CANVAS_H],
            "source": str(inputs.base_image.path),
            "source_sha256": inputs.base_image.sha256,
            "raster_array_sha256": array_digest(base),
            "mask16_array_sha256": None,
            "notes": "visible, separada i immutable; cap detall no s'hi bakeja",
        }
        layer_records = [base_layer_record] + [layer_record(layer) for layer in layers]
        output_list = output_records(
            staging,
            [
                ("final_tiff", paths["final_tiff"]),
                ("preview_png", paths["preview_png"]),
                ("editable_psb", paths["editable_psb"]),
                ("icc", paths["icc"]),
            ],
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "verdict": "ACCEPTAT",
            "stage": "EDITABLE_NATURAL_PRESENTATION",
            "inputs": input_summary(inputs),
            "geometry": {
                "scientific_canvas_xy": [CANVAS_W, CANVAS_H],
                "final_crop_xywh": [CROP_X, CROP_Y, CROP_W, CROP_H],
                "final_dimensions_xy": [CROP_W, CROP_H],
                "solar_center_xy_full_canvas": list(inputs.solar_center_xy),
                "solar_radius_px": SOLAR_RADIUS_PX,
                "earthshine_lunar_center_source": "C3 contact receipt; never transferred from solar registration",
            },
            "layer_order_bottom_to_top": layer_records,
            "earthshine_presentation": earth_receipt,
            "lunar_floor_presentation": lunar_floor_receipt,
            "tone_policy": {
                "intent": "deliberadament suau i natural; Pere farà els retocs finals",
                "base_pixels_tonally_modified": False,
                "earthshine_curve": "single global monotonic curve",
                "lunar_floor": {
                    "visible": False,
                    "structure_free": True,
                    "constant_linear_luminance": EARTHSHINE_LINEAR_LOW,
                    "scientific_authority": False,
                },
                "earthshine_default": {
                    "visible": False,
                    "opacity_255": EARTHSHINE_PRESENTATION_OPACITY,
                    "reason": (
                        "validated support ends before the physical limb; hidden "
                        "to avoid a visible inner lunar circle"
                    ),
                },
                "contact_opacity_255": {
                    "natural": CONTACT_NATURAL_OPACITY,
                    "halpha": CONTACT_HALPHA_OPACITY,
                    "prominence": CONTACT_PROMINENCE_OPACITY,
                    "default_visibility": {
                        "C2_natural": False,
                        "C2_halpha": False,
                        "C2_prominence": False,
                        "C3_natural": False,
                        "C3_halpha": False,
                        "C3_prominence": False,
                    },
                },
                "gentle_detail": {
                    "status": inputs.gentle_detail.status,
                    "blend_mode": "normal",
                    "opacity_255": inputs.gentle_detail.opacity,
                    "base_baked": False,
                    "merged_includes_layer_if_consumed": (
                        inputs.gentle_detail.status == "CONSUMIT_ACCEPTAT"
                    ),
                },
                "builder_operations_absent": [
                    "local contrast",
                    "MGN",
                    "NRGF",
                    "denoise",
                    "sharpen",
                    "radial field mask",
                    "mock-up pixels or masks",
                    "Kimi pixels or masks",
                ],
                "gentle_detail_upstream_method": (
                    inputs.gentle_detail.receipt.data.get("method")
                    if inputs.gentle_detail.receipt
                    else None
                ),
            },
            "qa": {
                "canvas_and_crop": True,
                "tiff_rgb16_icc_exact_roundtrip": tiff_roundtrip,
                "png_srgb": preview_qa,
                "psb": {
                    "dimensions_xy": [CROP_W, CROP_H],
                    "depth": 16,
                    "version": 2,
                    "icc_sha256": hashlib.sha256(icc_bytes).hexdigest(),
                    "layers": psb_qa,
                    "merged_exact_roundtrip": True,
                },
                "clipping_and_soft_tone": clipping,
                "anti_ring_to_8_5_Rsun": ring,
                "earthshine_support_edge": lunar_edge,
                "lunar_floor_physical_limb_edge": lunar_floor_edge,
                "outside_visible_support_byte_identical_to_base": outside_identical,
                "pass": True,
            },
            "software": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256(Path(__file__).resolve()),
                "build_natural_composite.py": {
                    "path": str(Path(N.__file__).resolve()),
                    "sha256": sha256(Path(N.__file__).resolve()),
                },
                "psb_utils.py": {
                    "path": str((PSB_TOOLS / "psb_utils.py").resolve()),
                    "sha256": sha256((PSB_TOOLS / "psb_utils.py").resolve()),
                },
                "python": sys.version,
                "numpy": np.__version__,
                "opencv": cv2.__version__,
                "tifffile": tifffile.__version__,
                "argv": sys.argv,
            },
            "outputs": output_list,
            "source_mutations": 0,
            "atomic_non_overwrite_promotion": True,
            "reversal": "disable/remove one candidate layer; immutable base and all layer masks remain separable in PSB",
        }
        write_json(paths["receipt"], receipt)
        with paths["sha256sums"].open("w", encoding="utf-8") as handle:
            for path in sorted(staging.iterdir()):
                if path.is_file() and path.name != "SHA256SUMS.txt":
                    handle.write(f"{sha256(path)}  {path.name}\n")
        staging.rename(output)
    except BaseException:
        if (
            staging.exists()
            and staging.parent == output.parent
            and staging.name.startswith(f".{output.name}.partial-")
        ):
            shutil.rmtree(staging)
        raise
    print(json.dumps({
        "status": "ACCEPTAT",
        "output": str(output),
        "final_tiff": str(output / paths["final_tiff"].name),
        "editable_psb": str(output / paths["editable_psb"].name),
        "preview": str(output / paths["preview_png"].name),
        "cross_train": inputs.cross_train.status,
        "gentle_detail": inputs.gentle_detail.status,
    }, indent=2, ensure_ascii=False))
    return 0


def run_self_test() -> dict[str, Any]:
    tests: list[str] = []
    if (CROP_X + CROP_W, CROP_Y + CROP_H) != (6777, 4460):
        raise AssertionError("crop geometry")
    canvas = np.arange(60 * 80 * 3, dtype=np.uint16).reshape(60, 80, 3)
    if canvas[7:47, 5:65].shape != (40, 60, 3):
        raise AssertionError("synthetic crop")
    tests.append("crop_exact_origin_and_dimensions")

    destination = np.full((12, 16, 3), 1000, np.uint16)
    patch = LayerPatch(
        "synthetic",
        np.full((2, 3, 3), 5000, np.uint16),
        np.full((2, 3), 32768, np.uint16),
        4,
        5,
        255,
        True,
        "TEST",
        "TEST",
        "",
        None,
        "",
    )
    composite_patch(destination, patch)
    expected = (5000 * 32768 + 1000 * (65535 - 32768) + 32767) // 65535
    if not np.all(destination[5:7, 4:7] == expected):
        raise AssertionError("alpha composite")
    tests.append("uint16_alpha_composite")
    del destination

    immutable_base = np.full((6, 8, 3), 4000, np.uint16)
    detail_merged = immutable_base.copy()
    detail = LayerPatch(
        "synthetic gentle detail",
        np.full((6, 8, 3), 12000, np.uint16),
        np.full((6, 8), 65535, np.uint16),
        0,
        0,
        48,
        True,
        "DETALL_PRESENTACIO_GENTLE",
        "CORONA_SOLAR_VIXEN_COMMON_GRID",
        "",
        None,
        "normal, low opacity",
    )
    composite_patch(detail_merged, detail)
    alpha = (65535 * 48 + 127) // 255
    expected_detail = (12000 * alpha + 4000 * (65535 - alpha) + 32767) // 65535
    if (
        not np.all(immutable_base == 4000)
        or not np.all(detail_merged == expected_detail)
        or gentle_detail_opacity(48) != 48
    ):
        raise AssertionError("gentle detail separation/opacity")
    for invalid in (True, 0, 97, 48.0):
        try:
            gentle_detail_opacity(invalid)
        except ContractError:
            pass
        else:
            raise AssertionError(f"gentle opacity accepted invalid {invalid!r}")
    tests.append("gentle_detail_normal_low_opacity_separate_base")

    ring_size = 512
    ring_center = (256.0, 256.0)
    ring_radius = 40.0
    ring_y, ring_x = np.indices((ring_size, ring_size), dtype=np.float32)
    ring_r = np.hypot(ring_x - ring_center[0], ring_y - ring_center[1])
    ring_valid = np.ones((ring_size, ring_size), bool)
    ring_base = 1.0 / (1.0 + ring_r / 80.0)
    ring_candidate = ring_base.copy()
    ring_candidate[(ring_r >= 116.0) & (ring_r < 124.0)] *= 1.03
    ring_args = (
        ring_valid,
        ring_center,
        ring_radius,
        1,
        4.0,
        5.0,
        1.15,
        6.0,
        0.08,
        ANTI_RING_RELATIVE_THRESHOLD,
        12,
    )
    base_ring_scan = N.annular_ring_scan(ring_base, *ring_args)
    candidate_ring_scan = N.annular_ring_scan(ring_candidate, *ring_args)
    if (
        base_ring_scan["candidate_count"] != 0
        or candidate_ring_scan["candidate_count"] == 0
    ):
        raise AssertionError("anti-ring 0.01 differential gate")
    tests.append("anti_ring_relative_0_01_rejects_new_detail_ring")

    matrix = affine_source_to_patch((10.0, 20.0), (123.25, 88.5), 1.5, 33.0, (100, 50))
    transformed = matrix @ np.array([10.0, 20.0, 1.0]) + np.array([100.0, 50.0])
    if not np.allclose(transformed, [123.25, 88.5], atol=1e-10):
        raise AssertionError("affine centre")
    tests.append("lunar_affine_center_exact")

    synthetic = np.add.outer(np.arange(1600, dtype=np.float32), np.arange(1600, dtype=np.float32))
    _, mask, tone = earthshine_visual(synthetic)
    yy, xx = np.indices(synthetic.shape, dtype=np.float32)
    radius = np.hypot(xx - 800.0, yy - 800.0)
    if np.any(mask[radius >= EARTHSHINE_VALID_RADIUS_PX] != 0) or not tone["monotonic"]:
        raise AssertionError("earthshine support/curve")
    tests.append("earthshine_fail_closed_support_and_monotonic_tone")

    floor_layer, floor_receipt = lunar_floor_patch(
        (1000.25, 1001.75), Path("synthetic-earthshine.tif"), "0" * 64
    )
    floor_qa = lunar_floor_edge_qa(floor_layer, (1000.25, 1001.75))
    if (
        not floor_qa["pass"]
        or floor_receipt["lunar_structure_added"] is not False
        or len(np.unique(floor_layer.rgb16.reshape(-1, 3), axis=0)) > 2
    ):
        raise AssertionError("structure-free lunar floor")
    tests.append("lunar_floor_structure_free_and_hard_zero_outside_limb")

    with tempfile.TemporaryDirectory(prefix="editable-delivery-selftest-") as temporary:
        temp = Path(temporary)
        icc = N.adobe_rgb_icc(ADOBE_GAMMA)
        psb_path = temp / "synthetic.psb"
        rgb = np.arange(12 * 16 * 3, dtype=np.uint16).reshape(12, 16, 3) * 100
        mask16 = np.arange(12 * 16, dtype=np.uint16).reshape(12, 16) * 341
        document = new_psb(16, 12, icc_bytes=icc)
        layer = add_pixel_layer(document, rgb, "synthetic", compression=Compression.ZIP)
        add_mask16(layer, mask16, 0, 0, compression=Compression.ZIP_WITH_PREDICTION)
        finalize_lr16(document)
        set_merged(document, rgb, compression=Compression.RAW)
        document.save(psb_path)
        qa = verify_psb(
            psb_path,
            [{
                "name": "synthetic",
                "rgb16": rgb,
                "mask16": mask16,
                "left": 0,
                "top": 0,
                "visible": True,
                "opacity": 255,
            }],
            rgb,
            icc,
        )
        if not qa[0]["raster16_roundtrip"] or not qa[0]["mask16_roundtrip"]:
            raise AssertionError("PSB round-trip")
        tiff_path = temp / "synthetic.tif"
        save_rgb16_tiff(tiff_path, rgb, icc, "synthetic self-test")
        shape, dtype, embedded = tiff_metadata(tiff_path)
        if shape != rgb.shape or dtype != rgb.dtype or embedded != icc or not np.array_equal(
            tifffile.imread(tiff_path), rgb
        ):
            raise AssertionError("TIFF RGB16 ICC round-trip")
        preview_path = temp / "synthetic.png"
        preview = save_srgb_preview(preview_path, rgb, icc, width=8)
        if preview["size_xy"] != [8, 6]:
            raise AssertionError("PNG sRGB preview")
    tests.append("psb_v2_rgb16_Lr16_mask16_and_merged_roundtrip")
    tests.append("tiff_rgb16_adobergb_and_png_srgb_roundtrip")

    return {
        "status": "SELF_TEST_PASS",
        "tests": tests,
        "canvas_xy": [CANVAS_W, CANVAS_H],
        "crop_xywh": [CROP_X, CROP_Y, CROP_W, CROP_H],
        "earthshine_scale": EARTHSHINE_SCALE,
        "source_mutations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, ensure_ascii=False))
        return 0
    if args.manifest is None or args.output_dir is None:
        parser.error("--manifest i --output-dir són obligatoris excepte amb --self-test")
    inputs = validate_inputs(args.manifest)
    return build(inputs, args.output_dir, args.validate_only)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"CONTRACT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
