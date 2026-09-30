"""QA capa a capa de les transicions de ``CapesTotalsV2`` sense cap PSB.

L'eina parteix del merged de ``Corretgint2`` (C2), aplica en espai codificat
les fonts CT1 8, 9, 10, 11, 12, 13 i 16 amb les màscares de
``final_masks/`` i produeix únicament derivats NPY/PNG/JSON de QA.

Propietats deliberades:

* no crida mai ``PSDImage.save`` ni modifica cap PSB;
* no desenfoca ni resampleja cap raster font;
* reutilitza la fórmula Normal del builder canònic i no requantitza entre
  capes;
* manté l'acumulador gran en un únic memmap float32 i treballa per files;
* genera pilots 1:1 ``ABANS | DESPRES | DIFERENCIA | MASCARA`` per ID9/ID11;
* mesura perfils globals i en 24 sectors entre 452 px i 3 Rsol, i marca
  mínims nous o gradients de la diferència centrats en una transició de
  màscara. Els flags són diagnòstics, no un veredicte automàtic de capa.

El merged C2 preferit és RGBA u16 de llenç complet. Un RGB u16 només s'admet
amb un alfa u16 explícit o amb ``--assume-opaque-c2``; mai s'inventa l'alfa
silenciosament.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, ImageDraw
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, ChannelID
from scipy import ndimage as ndi
from scipy.signal import find_peaks


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_capes_totals_v2 as build  # noqa: E402


SOURCE_IDS = (8, 9, 10, 11, 12, 13, 16)
PILOT_IDS = (9, 11)
BASE_STAGE_ID = 7
FRAME = (457, 463, 7417, 5103)

SUN = (4020.89, 2737.66)
R_SUN = 446.15
PROFILE_R_MIN_PX = 452.0
PROFILE_R_MAX_RSUN = 3.0
SECTOR_COUNT = 24

# Coeficients Y de Display P3. S'apliquen als valors codificats només com a
# escalar diagnòstic de continuïtat, no com a radiància física lineal.
DISPLAY_P3_Y = np.asarray(
    (0.22897456, 0.69173852, 0.07928691),
    dtype=np.float32,
)


@dataclass(frozen=True)
class Thresholds:
    profile_smoothing_sigma_px: float
    minimum_prominence_fraction: float
    minimum_prominence_dn: float
    minimum_match_radius_px: int
    mask_gradient_floor_per_px: float
    gradient_center_halfwidth_px: int
    gradient_shoulder_inner_px: int
    gradient_shoulder_outer_px: int
    gradient_center_ratio: float
    gradient_minimum_dn_per_px: float


@dataclass(frozen=True)
class RadialIndex:
    path: Path
    bbox: tuple[int, int, int, int]
    radii_px: np.ndarray
    counts_by_sector: np.ndarray

    @property
    def bin_count(self) -> int:
        return int(self.radii_px.size)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_new_output_dir(path: Path) -> Path:
    path = path.resolve()
    if path.exists():
        raise FileExistsError(f"no se sobreescriu cap directori de QA: {path}")
    path.mkdir(parents=True, exist_ok=False)
    return path


def _is_native_u16(array: np.ndarray) -> bool:
    return array.dtype == np.dtype(np.uint16)


def validate_c2_merged(
    merged_path: Path,
    alpha_path: Path | None,
    assume_opaque: bool,
) -> tuple[np.ndarray, np.ndarray | None, dict[str, object]]:
    merged_path = merged_path.resolve()
    if not merged_path.is_file() or merged_path.is_symlink():
        raise FileNotFoundError(f"merged C2 absent o no canònic: {merged_path}")
    merged = np.load(merged_path, mmap_mode="r", allow_pickle=False)
    if not _is_native_u16(merged) or merged.ndim != 3:
        raise TypeError(
            f"merged C2 ha de ser uint16 HxWx3/4, rebut {merged.dtype} {merged.shape}"
        )
    if merged.shape[:2] != (build.HEIGHT, build.WIDTH) or merged.shape[2] not in (3, 4):
        raise ValueError(
            "merged C2 ha de cobrir el llenç complet "
            f"{(build.HEIGHT, build.WIDTH)} amb 3 o 4 canals; rebut {merged.shape}"
        )

    alpha: np.ndarray | None = None
    alpha_receipt: dict[str, object]
    if merged.shape[2] == 4:
        if alpha_path is not None or assume_opaque:
            raise ValueError(
                "un merged RGBA ja conté alfa; no hi afegeixis --c2-alpha ni "
                "--assume-opaque-c2"
            )
        alpha_receipt = {"authority": "merged_channel_3"}
    elif alpha_path is not None:
        alpha_path = alpha_path.resolve()
        if not alpha_path.is_file() or alpha_path.is_symlink():
            raise FileNotFoundError(f"alfa C2 absent o no canònic: {alpha_path}")
        alpha = np.load(alpha_path, mmap_mode="r", allow_pickle=False)
        if not _is_native_u16(alpha) or alpha.shape != (build.HEIGHT, build.WIDTH):
            raise TypeError(
                "--c2-alpha ha de ser uint16 de llenç complet; "
                f"rebut {alpha.dtype} {alpha.shape}"
            )
        alpha_receipt = {
            "authority": "separate_u16_npy",
            "path": str(alpha_path),
            "sha256": sha256_file(alpha_path),
        }
    elif assume_opaque:
        alpha_receipt = {
            "authority": "explicit_cli_assumption",
            "value": 65535,
            "warning": "RGB no permet demostrar l'alfa C2; assumpció explícita de l'operador",
        }
    else:
        raise ValueError(
            "merged C2 RGB no conté alfa: aporta --c2-alpha o autoritza "
            "explícitament --assume-opaque-c2"
        )

    receipt = {
        "path": str(merged_path),
        "sha256": sha256_file(merged_path),
        "dtype": str(merged.dtype),
        "shape": list(merged.shape),
        "alpha": alpha_receipt,
    }
    return merged, alpha, receipt


def validate_ct1_source(path: Path) -> tuple[PSDImage, dict[int, object], dict[str, object]]:
    path = path.resolve()
    build._validate_file_pin(
        path,
        build.CAPES_TOTALS_V1_SIZE,
        build.CAPES_TOTALS_V1_SHA256,
    )
    psd = PSDImage.open(path)
    build._validate_header(psd, expected_channels=4, label="CapesTotalsV1")
    actual_ids = tuple(layer.layer_id for layer in psd)
    if actual_ids != build.CAPES_TOTALS_ALL_IDS:
        raise AssertionError(f"ordre CT1 inesperat: {actual_ids}")
    by_id = build._validate_selected_layers(psd, SOURCE_IDS, "CapesTotalsV1")
    for layer_id in SOURCE_IDS:
        layer = by_id[layer_id]
        if tuple(layer.bbox) != FRAME:
            raise AssertionError(
                f"layer_id={layer_id}: bbox {tuple(layer.bbox)} != {FRAME}"
            )
        if layer.blend_mode != BlendMode.NORMAL:
            raise AssertionError(f"layer_id={layer_id}: no és Normal")
        if layer.opacity != 255 or layer.fill_opacity != 255:
            raise AssertionError(
                f"layer_id={layer_id}: opacity/fill no són 100 %"
            )
    return psd, by_id, {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": build.CAPES_TOTALS_V1_SHA256,
        "layer_ids": list(actual_ids),
        "selected_ids": list(SOURCE_IDS),
    }


def _outside_frame_nonzero(mask: np.ndarray, chunk_rows: int) -> int:
    left, top, right, bottom = FRAME
    count = 0
    for row0 in range(0, build.HEIGHT, chunk_rows):
        row1 = min(build.HEIGHT, row0 + chunk_rows)
        block = np.asarray(mask[row0:row1])
        if row1 <= top or row0 >= bottom:
            count += int(np.count_nonzero(block))
            continue
        local_top = max(top, row0) - row0
        local_bottom = min(bottom, row1) - row0
        count += int(np.count_nonzero(block[:local_top]))
        count += int(np.count_nonzero(block[local_bottom:]))
        count += int(np.count_nonzero(block[local_top:local_bottom, :left]))
        count += int(np.count_nonzero(block[local_top:local_bottom, right:]))
    return count


def validate_final_masks(
    mask_dir: Path,
    chunk_rows: int,
) -> tuple[dict[int, np.ndarray], dict[str, object]]:
    mask_dir = mask_dir.resolve()
    if not mask_dir.is_dir() or mask_dir.is_symlink():
        raise FileNotFoundError(f"final_masks absent o no canònic: {mask_dir}")
    expected_names = {f"mask_{layer_id}.npy" for layer_id in SOURCE_IDS}
    actual_names = {entry.name for entry in mask_dir.iterdir()}
    if actual_names != expected_names:
        raise AssertionError(
            "final_masks ha de contenir exactament les set màscares: "
            f"actual={sorted(actual_names)}, esperat={sorted(expected_names)}"
        )

    masks: dict[int, np.ndarray] = {}
    receipt: dict[str, object] = {}
    for layer_id in SOURCE_IDS:
        path = mask_dir / f"mask_{layer_id}.npy"
        if path.is_symlink():
            raise ValueError(f"no s'admet symlink a final_masks: {path}")
        mask = np.load(path, mmap_mode="r", allow_pickle=False)
        if not _is_native_u16(mask) or mask.shape != (build.HEIGHT, build.WIDTH):
            raise TypeError(
                f"mask_{layer_id}.npy ha de ser uint16 de llenç complet; "
                f"rebut {mask.dtype} {mask.shape}"
            )
        outside = _outside_frame_nonzero(mask, chunk_rows)
        if outside:
            raise AssertionError(
                f"mask_{layer_id}.npy té {outside} píxels no-zero fora del raster"
            )
        masks[layer_id] = mask
        receipt[str(layer_id)] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "shape": list(mask.shape),
            "dtype": str(mask.dtype),
            "min": int(mask.min()),
            "max": int(mask.max(initial=0)),
            "nonzero_pixels": int(np.count_nonzero(mask)),
            "outside_raster_nonzero_pixels": outside,
        }
    return masks, {"directory": str(mask_dir), "masks": receipt}


def initialize_accumulator(
    path: Path,
    merged: np.ndarray,
    separate_alpha: np.ndarray | None,
    assume_opaque: bool,
    chunk_rows: int,
) -> np.memmap:
    accumulator = np.lib.format.open_memmap(
        path,
        mode="w+",
        dtype=np.float32,
        shape=(build.HEIGHT, build.WIDTH, 4),
    )
    scale = np.float32(1.0 / 65535.0)
    for row0 in range(0, build.HEIGHT, chunk_rows):
        row1 = min(build.HEIGHT, row0 + chunk_rows)
        accumulator[row0:row1, :, :3] = (
            np.asarray(merged[row0:row1, :, :3], dtype=np.float32) * scale
        )
        if merged.shape[2] == 4:
            accumulator[row0:row1, :, 3] = (
                np.asarray(merged[row0:row1, :, 3], dtype=np.float32) * scale
            )
        elif separate_alpha is not None:
            accumulator[row0:row1, :, 3] = (
                np.asarray(separate_alpha[row0:row1], dtype=np.float32) * scale
            )
        elif assume_opaque:
            accumulator[row0:row1, :, 3] = 1.0
        else:  # cobert per validate_c2_merged; defensa local fail-closed.
            raise AssertionError("alfa C2 no resolta")
    accumulator.flush()
    return accumulator


def compose_normal_layer_in_place(
    accumulator: np.memmap,
    layer,
    mask: np.ndarray,
    header,
    chunk_rows: int,
) -> dict[str, object]:
    """Aplica una font Normal al memmap, sense requantitzar ni tocar el raster."""

    if layer.blend_mode != BlendMode.NORMAL or layer.fill_opacity != 255:
        raise AssertionError(f"layer_id={layer.layer_id}: estat no compatible amb FONT_HDR")
    x0 = max(0, int(layer.left))
    y0 = max(0, int(layer.top))
    x1 = min(build.WIDTH, int(layer.right))
    y1 = min(build.HEIGHT, int(layer.bottom))
    if x0 >= x1 or y0 >= y1:
        raise AssertionError(f"layer_id={layer.layer_id}: cobertura buida")

    transparency = build._decoded_channel_u16(
        layer,
        ChannelID.TRANSPARENCY_MASK,
        header,
    )
    inv_u16 = np.float32(1.0 / 65535.0)
    opacity = np.float32(layer.opacity / 255.0)

    def alpha_rows(row0: int, row1: int) -> np.ndarray:
        alpha = np.asarray(
            transparency[
                row0 - layer.top : row1 - layer.top,
                x0 - layer.left : x1 - layer.left,
            ],
            dtype=np.float32,
        )
        alpha *= inv_u16
        alpha *= np.asarray(mask[row0:row1, x0:x1], dtype=np.float32) * inv_u16
        alpha *= opacity
        return alpha

    for channel_index, channel_id in enumerate(
        (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
    ):
        source = build._decoded_channel_u16(layer, channel_id, header)
        for row0 in range(y0, y1, chunk_rows):
            row1 = min(y1, row0 + chunk_rows)
            alpha = alpha_rows(row0, row1)
            source_rows = np.asarray(
                source[
                    row0 - layer.top : row1 - layer.top,
                    x0 - layer.left : x1 - layer.left,
                ],
                dtype=np.float32,
            )
            source_rows *= inv_u16
            previous = np.asarray(
                accumulator[row0:row1, x0:x1, channel_index],
                dtype=np.float32,
            )
            accumulator[row0:row1, x0:x1, channel_index] = (
                previous * (1.0 - alpha) + source_rows * alpha
            )
        del source

    effective_pixels = 0
    full_weight_pixels = 0
    alpha_sum = 0.0
    alpha_max = 0.0
    for row0 in range(y0, y1, chunk_rows):
        row1 = min(y1, row0 + chunk_rows)
        alpha = alpha_rows(row0, row1)
        previous_alpha = np.asarray(
            accumulator[row0:row1, x0:x1, 3],
            dtype=np.float32,
        )
        accumulator[row0:row1, x0:x1, 3] = (
            alpha + previous_alpha * (1.0 - alpha)
        )
        effective_pixels += int(np.count_nonzero(alpha))
        full_weight_pixels += int(np.count_nonzero(alpha >= (1.0 - 0.5 / 65535.0)))
        alpha_sum += float(alpha.sum(dtype=np.float64))
        alpha_max = max(alpha_max, float(alpha.max(initial=0.0)))
    accumulator.flush()
    del transparency
    return {
        "layer_id": int(layer.layer_id),
        "source_name": layer.name,
        "bbox": [x0, y0, x1, y1],
        "effective_alpha_nonzero_pixels": effective_pixels,
        "effective_alpha_full_weight_pixels": full_weight_pixels,
        "effective_alpha_sum": alpha_sum,
        "effective_alpha_max": alpha_max,
        "blend": "Normal in encoded document space",
        "interstage_quantization": False,
        "raster_resampled_or_filtered": False,
    }


def quantize_accumulator(
    accumulator: np.ndarray,
    output_path: Path,
    chunk_rows: int,
) -> np.memmap:
    output = np.lib.format.open_memmap(
        output_path,
        mode="w+",
        dtype=np.uint16,
        shape=(build.HEIGHT, build.WIDTH, 4),
    )
    for row0 in range(0, build.HEIGHT, chunk_rows):
        row1 = min(build.HEIGHT, row0 + chunk_rows)
        values = np.asarray(accumulator[row0:row1], dtype=np.float64)
        output[row0:row1] = np.clip(
            np.floor(values * 65535.0 + 0.5),
            0,
            65535,
        ).astype(np.uint16)
    output.flush()
    return output


def make_radial_index(path: Path, chunk_rows: int) -> RadialIndex:
    r_max = PROFILE_R_MAX_RSUN * R_SUN
    left = max(0, int(math.floor(SUN[0] - r_max)))
    top = max(0, int(math.floor(SUN[1] - r_max)))
    right = min(build.WIDTH, int(math.ceil(SUN[0] + r_max)) + 1)
    bottom = min(build.HEIGHT, int(math.ceil(SUN[1] + r_max)) + 1)
    height = bottom - top
    width = right - left
    bin_count = int(math.ceil(r_max - PROFILE_R_MIN_PX))
    radii_px = PROFILE_R_MIN_PX + np.arange(bin_count, dtype=np.float64) + 0.5
    combined_count = SECTOR_COUNT * bin_count

    index = np.lib.format.open_memmap(
        path,
        mode="w+",
        dtype=np.int32,
        shape=(height, width),
    )
    counts = np.zeros(combined_count, dtype=np.int64)
    dx = np.arange(left, right, dtype=np.float64) - SUN[0]
    sector_width = 2.0 * math.pi / SECTOR_COUNT
    for local0 in range(0, height, chunk_rows):
        local1 = min(height, local0 + chunk_rows)
        y = np.arange(top + local0, top + local1, dtype=np.float64)
        dy = y[:, None] - SUN[1]
        radius = np.hypot(dx[None, :], dy)
        valid = (radius >= PROFILE_R_MIN_PX) & (radius < r_max)
        radial_bin = np.floor(radius - PROFILE_R_MIN_PX).astype(np.int32)
        angle = np.mod(np.arctan2(-dy, dx[None, :]), 2.0 * math.pi)
        sector = np.floor(angle / sector_width).astype(np.int32)
        combined = sector * bin_count + radial_bin
        block = np.full((local1 - local0, width), -1, dtype=np.int32)
        block[valid] = combined[valid]
        index[local0:local1] = block
        counts += np.bincount(
            block[block >= 0],
            minlength=combined_count,
        ).astype(np.int64)
    index.flush()
    return RadialIndex(
        path=path,
        bbox=(left, top, right, bottom),
        radii_px=radii_px,
        counts_by_sector=counts.reshape(SECTOR_COUNT, bin_count),
    )


def _profiles_from_sector_sums(
    sums_by_sector: np.ndarray,
    counts_by_sector: np.ndarray,
) -> np.ndarray:
    sector = np.divide(
        sums_by_sector,
        counts_by_sector,
        out=np.full(sums_by_sector.shape, np.nan, dtype=np.float64),
        where=counts_by_sector > 0,
    )
    global_sum = sums_by_sector.sum(axis=0)
    global_count = counts_by_sector.sum(axis=0)
    global_profile = np.divide(
        global_sum,
        global_count,
        out=np.full(global_sum.shape, np.nan, dtype=np.float64),
        where=global_count > 0,
    )
    return np.concatenate((global_profile[None, :], sector), axis=0)


def radial_profiles_rgb(
    image: np.ndarray,
    radial: RadialIndex,
    chunk_rows: int,
) -> np.ndarray:
    left, top, right, bottom = radial.bbox
    index = np.load(radial.path, mmap_mode="r", allow_pickle=False)
    combined_count = SECTOR_COUNT * radial.bin_count
    sums = np.zeros(combined_count, dtype=np.float64)
    for local0 in range(0, bottom - top, chunk_rows):
        local1 = min(bottom - top, local0 + chunk_rows)
        ids = np.asarray(index[local0:local1])
        rgb = np.asarray(
            image[top + local0 : top + local1, left:right, :3],
            dtype=np.float32,
        )
        scalar = np.einsum("...c,c->...", rgb, DISPLAY_P3_Y, optimize=True)
        valid = ids >= 0
        sums += np.bincount(
            ids[valid],
            weights=scalar[valid].astype(np.float64),
            minlength=combined_count,
        )
    return _profiles_from_sector_sums(
        sums.reshape(SECTOR_COUNT, radial.bin_count),
        radial.counts_by_sector,
    )


def radial_profiles_mask(
    mask: np.ndarray,
    radial: RadialIndex,
    chunk_rows: int,
) -> np.ndarray:
    left, top, right, bottom = radial.bbox
    index = np.load(radial.path, mmap_mode="r", allow_pickle=False)
    combined_count = SECTOR_COUNT * radial.bin_count
    sums = np.zeros(combined_count, dtype=np.float64)
    for local0 in range(0, bottom - top, chunk_rows):
        local1 = min(bottom - top, local0 + chunk_rows)
        ids = np.asarray(index[local0:local1])
        values = (
            np.asarray(mask[top + local0 : top + local1, left:right], dtype=np.float32)
            * np.float32(1.0 / 65535.0)
        )
        valid = ids >= 0
        sums += np.bincount(
            ids[valid],
            weights=values[valid].astype(np.float64),
            minlength=combined_count,
        )
    return _profiles_from_sector_sums(
        sums.reshape(SECTOR_COUNT, radial.bin_count),
        radial.counts_by_sector,
    )


def _finite_smooth(profile: np.ndarray, sigma_px: float) -> np.ndarray:
    values = np.asarray(profile, dtype=np.float64)
    finite = np.isfinite(values)
    if not np.any(finite):
        return np.full(values.shape, np.nan, dtype=np.float64)
    if not np.all(finite):
        coordinates = np.arange(values.size, dtype=np.float64)
        values = np.interp(coordinates, coordinates[finite], values[finite])
    if sigma_px <= 0:
        return values.copy()
    return ndi.gaussian_filter1d(values, sigma_px, mode="nearest")


def _profile_name(index: int) -> str:
    if index == 0:
        return "global"
    sector = index - 1
    start = sector * 360.0 / SECTOR_COUNT
    end = (sector + 1) * 360.0 / SECTOR_COUNT
    return f"sector_{sector:02d}_{start:05.1f}_{end:05.1f}_deg"


def _minima(
    profile: np.ndarray,
    thresholds: Thresholds,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    smooth = _finite_smooth(profile, thresholds.profile_smoothing_sigma_px)
    finite = smooth[np.isfinite(smooth)]
    if finite.size == 0:
        return np.empty(0, dtype=int), np.empty(0), smooth
    scale = max(float(np.nanmedian(np.abs(finite))), 1.0 / 65535.0)
    prominence = max(
        thresholds.minimum_prominence_dn / 65535.0,
        thresholds.minimum_prominence_fraction * scale,
    )
    indices, properties = find_peaks(
        -smooth,
        prominence=prominence,
        distance=max(1, thresholds.minimum_match_radius_px),
    )
    return indices, properties.get("prominences", np.empty(0)), smooth


def _new_minima_for_profile(
    before: np.ndarray,
    after: np.ndarray,
    radii_px: np.ndarray,
    thresholds: Thresholds,
) -> list[dict[str, float]]:
    before_indices, _before_prom, _before_smooth = _minima(before, thresholds)
    after_indices, after_prom, after_smooth = _minima(after, thresholds)
    result: list[dict[str, float]] = []
    for index, prominence in zip(after_indices, after_prom):
        if before_indices.size and int(np.min(np.abs(before_indices - index))) <= (
            thresholds.minimum_match_radius_px
        ):
            continue
        result.append(
            {
                "radius_px": float(radii_px[index]),
                "radius_rsun": float(radii_px[index] / R_SUN),
                "value_dn": float(after_smooth[index] * 65535.0),
                "prominence_dn": float(prominence * 65535.0),
            }
        )
    return result


def _centered_gradient_for_profile(
    before: np.ndarray,
    after: np.ndarray,
    mask_profile: np.ndarray,
    radii_px: np.ndarray,
    thresholds: Thresholds,
) -> list[dict[str, object]]:
    mask_smooth = _finite_smooth(
        mask_profile,
        thresholds.profile_smoothing_sigma_px,
    )
    delta_smooth = _finite_smooth(
        np.asarray(after) - np.asarray(before),
        thresholds.profile_smoothing_sigma_px,
    )
    if not np.any(np.isfinite(mask_smooth)) or not np.any(np.isfinite(delta_smooth)):
        return []
    mask_gradient = np.abs(np.gradient(mask_smooth))
    delta_gradient = np.abs(np.gradient(delta_smooth))
    centers, properties = find_peaks(
        mask_gradient,
        prominence=thresholds.mask_gradient_floor_per_px,
        distance=max(3, thresholds.gradient_shoulder_inner_px),
    )
    if centers.size == 0:
        return []
    prominences = properties.get("prominences", np.zeros(centers.size))
    order = np.argsort(prominences)[::-1][:4]
    result: list[dict[str, object]] = []
    for position in order:
        center = int(centers[position])
        c0 = max(0, center - thresholds.gradient_center_halfwidth_px)
        c1 = min(delta_gradient.size, center + thresholds.gradient_center_halfwidth_px + 1)
        left0 = max(0, center - thresholds.gradient_shoulder_outer_px)
        left1 = max(0, center - thresholds.gradient_shoulder_inner_px)
        right0 = min(delta_gradient.size, center + thresholds.gradient_shoulder_inner_px + 1)
        right1 = min(delta_gradient.size, center + thresholds.gradient_shoulder_outer_px + 1)
        shoulders = np.concatenate((delta_gradient[left0:left1], delta_gradient[right0:right1]))
        shoulders = shoulders[np.isfinite(shoulders)]
        center_peak = float(np.nanmax(delta_gradient[c0:c1], initial=0.0))
        shoulder_p95 = float(np.quantile(shoulders, 0.95)) if shoulders.size else 0.0
        ratio = center_peak / max(shoulder_p95, 0.5 / 65535.0)
        flagged = (
            center_peak * 65535.0 >= thresholds.gradient_minimum_dn_per_px
            and ratio >= thresholds.gradient_center_ratio
        )
        result.append(
            {
                "radius_px": float(radii_px[center]),
                "radius_rsun": float(radii_px[center] / R_SUN),
                "mask_gradient_per_px": float(mask_gradient[center]),
                "delta_gradient_center_dn_per_px": center_peak * 65535.0,
                "delta_gradient_shoulder_p95_dn_per_px": shoulder_p95 * 65535.0,
                "center_to_shoulder_ratio": ratio,
                "flag": bool(flagged),
            }
        )
    return result


def analyze_stage_transition(
    before: np.ndarray,
    after: np.ndarray,
    mask_profiles: np.ndarray,
    radii_px: np.ndarray,
    thresholds: Thresholds,
) -> dict[str, object]:
    new_minima: dict[str, object] = {}
    centered: dict[str, object] = {}
    for profile_index in range(1 + SECTOR_COUNT):
        name = _profile_name(profile_index)
        minima = _new_minima_for_profile(
            before[profile_index],
            after[profile_index],
            radii_px,
            thresholds,
        )
        gradients = _centered_gradient_for_profile(
            before[profile_index],
            after[profile_index],
            mask_profiles[profile_index],
            radii_px,
            thresholds,
        )
        if minima:
            new_minima[name] = minima
        flagged_gradients = [item for item in gradients if item["flag"]]
        if flagged_gradients:
            centered[name] = flagged_gradients
    return {
        "new_minima_flag": bool(new_minima),
        "new_minima": new_minima,
        "centered_gradient_flag": bool(centered),
        "centered_gradients": centered,
        "status": "FLAG" if new_minima or centered else "PASS_NUMERIC",
    }


def select_transition_boxes(
    mask_profiles: np.ndarray,
    radii_px: np.ndarray,
    crop_size: int,
    crop_count: int,
    thresholds: Thresholds,
) -> list[dict[str, object]]:
    candidates: list[tuple[float, int, int]] = []
    for sector in range(SECTOR_COUNT):
        smooth = _finite_smooth(
            mask_profiles[1 + sector],
            thresholds.profile_smoothing_sigma_px,
        )
        gradient = np.abs(np.gradient(smooth))
        radius_index = int(np.nanargmax(gradient))
        candidates.append((float(gradient[radius_index]), sector, radius_index))
    candidates.sort(reverse=True)

    selected: list[tuple[float, int, int]] = []
    minimum_sector_distance = max(1, SECTOR_COUNT // (crop_count * 2))
    for candidate in candidates:
        _score, sector, _radius_index = candidate
        if all(
            min(abs(sector - old[1]), SECTOR_COUNT - abs(sector - old[1]))
            >= minimum_sector_distance
            for old in selected
        ):
            selected.append(candidate)
        if len(selected) == crop_count:
            break
    if len(selected) < crop_count:
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) == crop_count:
                break

    half = crop_size // 2
    result: list[dict[str, object]] = []
    for score, sector, radius_index in selected:
        angle = (sector + 0.5) * 2.0 * math.pi / SECTOR_COUNT
        radius = float(radii_px[radius_index])
        center_x = SUN[0] + radius * math.cos(angle)
        center_y = SUN[1] - radius * math.sin(angle)
        left = int(round(center_x)) - half
        top = int(round(center_y)) - half
        left = min(max(0, left), build.WIDTH - crop_size)
        top = min(max(0, top), build.HEIGHT - crop_size)
        result.append(
            {
                "sector": sector,
                "sector_center_deg": (sector + 0.5) * 360.0 / SECTOR_COUNT,
                "transition_radius_px": radius,
                "transition_radius_rsun": radius / R_SUN,
                "mask_gradient_score_per_px": score,
                "bbox": [left, top, left + crop_size, top + crop_size],
            }
        )
    return result


def _display_rgb(encoded_rgb: np.ndarray, gamma: float) -> np.ndarray:
    values = np.clip(np.asarray(encoded_rgb, dtype=np.float32), 0.0, 1.0)
    values = np.power(values, gamma)
    return np.clip(np.floor(values * 255.0 + 0.5), 0, 255).astype(np.uint8)


def _signed_difference_rgb(
    before: np.ndarray,
    after: np.ndarray,
    scale_dn: float,
) -> np.ndarray:
    delta_dn = (np.asarray(after, dtype=np.float32) - np.asarray(before, dtype=np.float32)) * 65535.0
    display = 0.5 + delta_dn / (2.0 * scale_dn)
    return np.clip(np.floor(display * 255.0 + 0.5), 0, 255).astype(np.uint8)


def _mask_rgb(mask: np.ndarray) -> np.ndarray:
    gray = np.clip(
        np.floor(np.asarray(mask, dtype=np.float32) * (255.0 / 65535.0) + 0.5),
        0,
        255,
    ).astype(np.uint8)
    return np.repeat(gray[..., None], 3, axis=2)


def _labelled_horizontal_panel(
    items: Sequence[tuple[str, np.ndarray]],
    output: Path,
) -> None:
    images = [Image.fromarray(np.asarray(array, dtype=np.uint8), mode="RGB") for _label, array in items]
    if len({image.size for image in images}) != 1:
        raise AssertionError("el pilot 1:1 exigeix quatre retalls de la mateixa mida")
    label_height = 40
    panel = Image.new(
        "RGB",
        (sum(image.width for image in images), images[0].height + label_height),
        "black",
    )
    draw = ImageDraw.Draw(panel)
    x = 0
    for (label, _array), image in zip(items, images):
        panel.paste(image, (x, label_height))
        draw.text((x + 8, 12), label, fill="white")
        x += image.width
    panel.save(output, format="PNG", optimize=False)


def render_pilot_panels(
    layer_id: int,
    before_crops: Sequence[np.ndarray],
    after_image: np.ndarray,
    mask: np.ndarray,
    boxes: Sequence[dict[str, object]],
    panel_dir: Path,
    gamma: float,
    difference_scale_dn: float,
) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for index, (before, box_info) in enumerate(zip(before_crops, boxes), start=1):
        left, top, right, bottom = box_info["bbox"]
        after = np.asarray(after_image[top:bottom, left:right, :3], dtype=np.float32).copy()
        mask_crop = np.asarray(mask[top:bottom, left:right])
        output = panel_dir / f"id{layer_id:02d}_transition_{index:02d}_1to1.png"
        _labelled_horizontal_panel(
            (
                ("ABANS", _display_rgb(before, gamma)),
                ("DESPRES", _display_rgb(after, gamma)),
                (
                    f"DIFERENCIA SIGNADA +/-{difference_scale_dn:g} DN",
                    _signed_difference_rgb(before, after, difference_scale_dn),
                ),
                ("MASCARA", _mask_rgb(mask_crop)),
            ),
            output,
        )
        delta_dn = (after - before) * 65535.0
        receipts.append(
            {
                **box_info,
                "path": str(output),
                "sha256": sha256_file(output),
                "pixel_scale": "1 image pixel per PNG pixel",
                "difference_scale_dn": difference_scale_dn,
                "difference_abs_p99_dn": float(np.quantile(np.abs(delta_dn), 0.99)),
                "difference_abs_max_dn": float(np.max(np.abs(delta_dn), initial=0.0)),
            }
        )
    return receipts


def stage_preview(
    image: np.ndarray,
    radial: RadialIndex,
    tile_max_px: int,
    gamma: float,
) -> tuple[Image.Image, int]:
    left, top, right, bottom = radial.bbox
    stride = max(1, int(math.ceil(max(right - left, bottom - top) / tile_max_px)))
    sample = np.asarray(image[top:bottom:stride, left:right:stride, :3], dtype=np.float32)
    return Image.fromarray(_display_rgb(sample, gamma), mode="RGB"), stride


def render_stage_contact_sheet(
    stages: Sequence[tuple[str, Image.Image]],
    output: Path,
    columns: int = 4,
) -> None:
    if not stages:
        raise ValueError("contact sheet sense stages")
    tile_width = max(image.width for _label, image in stages)
    tile_height = max(image.height for _label, image in stages)
    label_height = 34
    rows = int(math.ceil(len(stages) / columns))
    sheet = Image.new(
        "RGB",
        (columns * tile_width, rows * (tile_height + label_height)),
        "black",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(stages):
        column = index % columns
        row = index // columns
        x = column * tile_width
        y = row * (tile_height + label_height)
        draw.text((x + 8, y + 9), label, fill="white")
        sheet.paste(image, (x, y + label_height))
    sheet.save(output, format="PNG", optimize=False)


def _thresholds_to_json(value: Thresholds) -> dict[str, object]:
    return {
        "profile_smoothing_sigma_px": value.profile_smoothing_sigma_px,
        "minimum_prominence_fraction": value.minimum_prominence_fraction,
        "minimum_prominence_dn": value.minimum_prominence_dn,
        "minimum_match_radius_px": value.minimum_match_radius_px,
        "mask_gradient_floor_per_px": value.mask_gradient_floor_per_px,
        "gradient_center_halfwidth_px": value.gradient_center_halfwidth_px,
        "gradient_shoulder_inner_px": value.gradient_shoulder_inner_px,
        "gradient_shoulder_outer_px": value.gradient_shoulder_outer_px,
        "gradient_center_ratio": value.gradient_center_ratio,
        "gradient_minimum_dn_per_px": value.gradient_minimum_dn_per_px,
    }


def render_transition_qa(
    *,
    c2_merged_path: Path,
    c2_alpha_path: Path | None,
    assume_opaque_c2: bool,
    final_mask_dir: Path,
    ct1_path: Path,
    output_dir: Path,
    chunk_rows: int,
    crop_size: int,
    crop_count: int,
    contact_tile_px: int,
    preview_gamma: float,
    difference_scale_dn: float,
    thresholds: Thresholds,
) -> dict[str, object]:
    if chunk_rows <= 0:
        raise ValueError("chunk_rows ha de ser positiu")
    if crop_size <= 0 or crop_size % 2:
        raise ValueError("crop_size ha de ser positiu i parell")
    if crop_count <= 0 or crop_count > SECTOR_COUNT:
        raise ValueError("crop_count ha d'estar entre 1 i 24")
    if contact_tile_px <= 0 or preview_gamma <= 0 or difference_scale_dn <= 0:
        raise ValueError("mides, gamma i escala de diferència han de ser positives")
    if not (
        0 <= thresholds.gradient_center_halfwidth_px
        < thresholds.gradient_shoulder_inner_px
        < thresholds.gradient_shoulder_outer_px
    ):
        raise ValueError("finestres de gradient incoherents")

    # Totes les fonts es validen abans de crear ni un directori de sortida.
    merged, separate_alpha, c2_receipt = validate_c2_merged(
        c2_merged_path,
        c2_alpha_path,
        assume_opaque_c2,
    )
    ct1, by_id, ct1_receipt = validate_ct1_source(ct1_path)
    masks, masks_receipt = validate_final_masks(final_mask_dir, chunk_rows)

    output_dir = _require_new_output_dir(output_dir)
    work_dir = output_dir / "work"
    panel_dir = output_dir / "panels"
    work_dir.mkdir()
    panel_dir.mkdir()

    radial = make_radial_index(work_dir / "radial_sector_index.npy", chunk_rows)
    mask_profile_map = {
        layer_id: radial_profiles_mask(masks[layer_id], radial, chunk_rows)
        for layer_id in SOURCE_IDS
    }
    pilot_boxes = {
        layer_id: select_transition_boxes(
            mask_profile_map[layer_id],
            radial.radii_px,
            crop_size,
            crop_count,
            thresholds,
        )
        for layer_id in PILOT_IDS
    }

    accumulator_path = work_dir / "composite_float32.npy"
    accumulator = initialize_accumulator(
        accumulator_path,
        merged,
        separate_alpha,
        assume_opaque_c2,
        chunk_rows,
    )

    stage_ids = [BASE_STAGE_ID]
    stage_labels = ["C2 BASE (fins ID7)"]
    stage_profiles = [radial_profiles_rgb(accumulator, radial, chunk_rows)]
    preview, preview_stride = stage_preview(
        accumulator,
        radial,
        contact_tile_px,
        preview_gamma,
    )
    stage_previews: list[tuple[str, Image.Image]] = [(stage_labels[0], preview)]
    stage_receipts: dict[str, object] = {}
    pilot_receipts: dict[str, object] = {}

    for layer_id in SOURCE_IDS:
        boxes = pilot_boxes.get(layer_id, [])
        before_crops = []
        for box_info in boxes:
            left, top, right, bottom = box_info["bbox"]
            before_crops.append(
                np.asarray(
                    accumulator[top:bottom, left:right, :3],
                    dtype=np.float32,
                ).copy()
            )

        composition = compose_normal_layer_in_place(
            accumulator,
            by_id[layer_id],
            masks[layer_id],
            ct1._record.header,
            chunk_rows,
        )
        after_profile = radial_profiles_rgb(accumulator, radial, chunk_rows)
        flags = analyze_stage_transition(
            stage_profiles[-1],
            after_profile,
            mask_profile_map[layer_id],
            radial.radii_px,
            thresholds,
        )
        stage_profiles.append(after_profile)
        stage_ids.append(layer_id)
        label = f"+ ID{layer_id}"
        stage_labels.append(label)
        preview, current_stride = stage_preview(
            accumulator,
            radial,
            contact_tile_px,
            preview_gamma,
        )
        if current_stride != preview_stride:
            raise AssertionError("stride inconsistent al contact sheet")
        stage_previews.append((label, preview))
        stage_receipts[str(layer_id)] = {
            "composition": composition,
            "profile_flags": flags,
        }

        if layer_id in PILOT_IDS:
            pilot_receipts[str(layer_id)] = render_pilot_panels(
                layer_id,
                before_crops,
                accumulator,
                masks[layer_id],
                boxes,
                panel_dir,
                preview_gamma,
                difference_scale_dn,
            )

    final_path = output_dir / "composite_after_id16_rgba16.npy"
    final_u16 = quantize_accumulator(accumulator, final_path, chunk_rows)

    contact_path = output_dir / "stages_contact_sheet.png"
    render_stage_contact_sheet(stage_previews, contact_path)

    profiles_path = output_dir / "radial_profiles_452px_to_3Rsun.npz"
    np.savez_compressed(
        profiles_path,
        radii_px=radial.radii_px,
        radii_rsun=radial.radii_px / R_SUN,
        stage_ids=np.asarray(stage_ids, dtype=np.int16),
        stage_profiles_encoded_p3_y=np.stack(stage_profiles),
        mask_ids=np.asarray(SOURCE_IDS, dtype=np.int16),
        mask_profiles=np.stack([mask_profile_map[layer_id] for layer_id in SOURCE_IDS]),
        counts_global_and_24_sectors=np.concatenate(
            (
                radial.counts_by_sector.sum(axis=0, keepdims=True),
                radial.counts_by_sector,
            ),
            axis=0,
        ),
    )

    panel_files = sorted(panel_dir.glob("*.png"))
    any_minima = any(
        stage_receipts[str(layer_id)]["profile_flags"]["new_minima_flag"]
        for layer_id in SOURCE_IDS
    )
    any_centered = any(
        stage_receipts[str(layer_id)]["profile_flags"]["centered_gradient_flag"]
        for layer_id in SOURCE_IDS
    )
    manifest = {
        "status": "QA_RENDERED_NO_PSB_WRITTEN",
        "sources": {
            "c2_merged": c2_receipt,
            "capes_totals_v1": ct1_receipt,
            "final_masks": masks_receipt,
        },
        "composition": {
            "stage_ids_bottom_to_top": stage_ids,
            "stage_labels": stage_labels,
            "space": "Display P3 encoded document values",
            "blend": "Normal source-over, identical RGB/alpha formula to build_capes_totals_v2",
            "interstage_quantization": False,
            "raster_blur": False,
            "raster_resampling": False,
            "chunk_rows": chunk_rows,
            "accumulator": {
                "path": str(accumulator_path),
                "dtype": "float32",
                "shape": [build.HEIGHT, build.WIDTH, 4],
            },
            "stages": stage_receipts,
        },
        "profiles": {
            "path": str(profiles_path),
            "sha256": sha256_file(profiles_path),
            "radius_px": [PROFILE_R_MIN_PX, PROFILE_R_MAX_RSUN * R_SUN],
            "radius_rsun": [PROFILE_R_MIN_PX / R_SUN, PROFILE_R_MAX_RSUN],
            "profile_order": ["global"] + [_profile_name(i) for i in range(1, 25)],
            "scalar": "Display P3 Y coefficients over encoded RGB; diagnostic, not linear radiance",
            "thresholds": _thresholds_to_json(thresholds),
            "any_new_minimum_flag": any_minima,
            "any_centered_gradient_flag": any_centered,
        },
        "pilots_1to1": {
            "ids": list(PILOT_IDS),
            "layout": "ABANS | DESPRES | DIFERENCIA SIGNADA | MASCARA",
            "preview_gamma": preview_gamma,
            "receipts": pilot_receipts,
        },
        "stage_contact_sheet": {
            "path": str(contact_path),
            "sha256": sha256_file(contact_path),
            "source_bbox": list(radial.bbox),
            "sampling_stride_px": preview_stride,
            "preview_gamma": preview_gamma,
        },
        "outputs": {
            "final_composite_rgba16": {
                "path": str(final_path),
                "sha256": sha256_file(final_path),
                "dtype": str(final_u16.dtype),
                "shape": list(final_u16.shape),
            },
            "panels": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in panel_files
            ],
        },
        "psb_opened_read_only": [str(ct1_path.resolve())],
        "psb_saved": False,
        "scientific_verdict_automatic": False,
    }
    manifest_path = output_dir / "qa_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest["manifest"] = {
        "path": str(manifest_path),
        "sha256": sha256_file(manifest_path),
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compon C2 + fonts CT1 amb final_masks i genera QA de transicions; "
            "no desa cap PSB."
        )
    )
    parser.add_argument("--c2-merged", type=Path, required=True)
    parser.add_argument("--c2-alpha", type=Path)
    parser.add_argument("--assume-opaque-c2", action="store_true")
    parser.add_argument("--final-masks", type=Path, required=True)
    parser.add_argument(
        "--capes-totals-v1",
        type=Path,
        default=build.DEFAULT_CAPES_TOTALS_V1,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunk-rows", type=int, default=96)
    parser.add_argument("--crop-size", type=int, default=512)
    parser.add_argument("--crop-count", type=int, default=3)
    parser.add_argument("--contact-tile-px", type=int, default=720)
    parser.add_argument("--preview-gamma", type=float, default=1.0 / 2.2)
    parser.add_argument("--difference-scale-dn", type=float, default=2048.0)

    # Llindars de QA, tots explícits i registrats al manifest. No governen el
    # sigma de cap màscara ni es presenten com constants universals.
    parser.add_argument("--profile-smoothing-sigma-px", type=float, default=3.0)
    parser.add_argument("--minimum-prominence-fraction", type=float, default=0.003)
    parser.add_argument("--minimum-prominence-dn", type=float, default=8.0)
    parser.add_argument("--minimum-match-radius-px", type=int, default=3)
    parser.add_argument("--mask-gradient-floor-per-px", type=float, default=1.0e-4)
    parser.add_argument("--gradient-center-halfwidth-px", type=int, default=6)
    parser.add_argument("--gradient-shoulder-inner-px", type=int, default=12)
    parser.add_argument("--gradient-shoulder-outer-px", type=int, default=36)
    parser.add_argument("--gradient-center-ratio", type=float, default=2.0)
    parser.add_argument("--gradient-minimum-dn-per-px", type=float, default=8.0)
    args = parser.parse_args()

    thresholds = Thresholds(
        profile_smoothing_sigma_px=args.profile_smoothing_sigma_px,
        minimum_prominence_fraction=args.minimum_prominence_fraction,
        minimum_prominence_dn=args.minimum_prominence_dn,
        minimum_match_radius_px=args.minimum_match_radius_px,
        mask_gradient_floor_per_px=args.mask_gradient_floor_per_px,
        gradient_center_halfwidth_px=args.gradient_center_halfwidth_px,
        gradient_shoulder_inner_px=args.gradient_shoulder_inner_px,
        gradient_shoulder_outer_px=args.gradient_shoulder_outer_px,
        gradient_center_ratio=args.gradient_center_ratio,
        gradient_minimum_dn_per_px=args.gradient_minimum_dn_per_px,
    )
    manifest = render_transition_qa(
        c2_merged_path=args.c2_merged,
        c2_alpha_path=args.c2_alpha,
        assume_opaque_c2=args.assume_opaque_c2,
        final_mask_dir=args.final_masks,
        ct1_path=args.capes_totals_v1,
        output_dir=args.output_dir,
        chunk_rows=args.chunk_rows,
        crop_size=args.crop_size,
        crop_count=args.crop_count,
        contact_tile_px=args.contact_tile_px,
        preview_gamma=args.preview_gamma,
        difference_scale_dn=args.difference_scale_dn,
        thresholds=thresholds,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
