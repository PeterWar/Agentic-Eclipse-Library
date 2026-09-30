#!/usr/bin/env python3
"""Build the primary registered CFA4 Sony masters for the S6 delivery.

The companion ``stack_sony_s6.py`` produces a Gaussian RGB derivative for
visual QA.  This script keeps R/G1/B/G2 separate on their native 2x2 sampling
grid, reads the already-audited per-frame transforms, fits all nuisance planes
again in CFA4 space, and propagates random and donor-flat systematic
uncertainty independently.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rawpy
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stack_sony_s6 as S  # noqa: E402


SCHEMA = "SONY_A7RIIIA_FE300_CFA4_STACK_RECEIPT_S6_V1"
PLANE_SPEC = ((0, "R", 0), (1, "G1", 1), (2, "B", 2), (3, "G2", 1))
_EVIDENCE_CACHE: dict[Path, tuple[int, int, dict]] = {}


def load_rows(group_dir: Path) -> tuple[list[dict], dict]:
    with (group_dir / "TRANSFORMS.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    receipt = json.loads((group_dir / "STACK_RECEIPT.json").read_text(encoding="utf-8"))
    return rows, receipt


def file_evidence(path: Path) -> dict:
    """Hash one immutable input and detect a concurrent replacement."""
    resolved = path.resolve(strict=True)
    before = resolved.stat()
    cached = _EVIDENCE_CACHE.get(resolved)
    if cached and cached[:2] == (before.st_size, before.st_mtime_ns):
        return dict(cached[2])
    digest = S.sha256(resolved)
    after = resolved.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"input changed while hashing: {resolved}")
    evidence = {"path": str(resolved), "bytes": after.st_size, "sha256": digest}
    _EVIDENCE_CACHE[resolved] = (after.st_size, after.st_mtime_ns, evidence)
    return dict(evidence)


def _matching_upstream_record(actual: dict, upstream: list[dict], label: str) -> dict:
    """Require byte identity with the correspondingly named upstream input."""
    actual_name = Path(actual["path"]).name
    matches = [row for row in upstream
               if Path(row["path"]).name == actual_name
               and int(row["bytes"]) == actual["bytes"]
               and row["sha256"] == actual["sha256"]]
    if len(matches) != 1:
        raise RuntimeError(
            f"{label}: current {actual_name} has no unique byte-identical upstream "
            f"record (matches={len(matches)})")
    return matches[0]


def validate_raw_inputs(names: list[str], receipt: dict) -> list[dict]:
    """Require the exact canonical RAW path and re-hash its current bytes."""
    expected = {row["name"]: row for row in receipt.get("inputs", [])}
    validated = []
    for name in names:
        if name not in expected:
            raise RuntimeError(f"{name}: missing upstream RAW receipt")
        row = expected[name]
        path = (S.DATA / f"{name}.ARW").resolve(strict=True)
        if Path(row["path"]).resolve(strict=True) != path:
            raise RuntimeError(
                f"{name}: upstream RAW path is not the canonical input: "
                f"{row['path']} != {path}")
        current = {"name": name, **file_evidence(path)}
        if current["bytes"] != row["bytes"] or current["sha256"] != row["sha256"]:
            raise RuntimeError(f"{name}: current RAW differs from upstream receipt")
        validated.append(current)
    return validated


def validate_calibrators(exposure: float, dark_root: Path, flat_root: Path,
                         receipt: dict) -> list[dict]:
    """Re-hash every calibrator actually selected by the CFA4 CLI roots."""
    dark_dir = dark_root / f"{exposure:.10g}"
    paths = [
        ("dark_master", dark_dir / "MASTER_DARK_raw_ADU.npy"),
        ("dark_variance", dark_dir / "MASTER_DARK_VARIANCE_ADU2.npy"),
        ("hot_pixel_map", dark_dir / "HOT_PIXEL_MAP.npy"),
        ("dark_receipt", dark_dir / "DARK_RECEIPT.json"),
        ("dark_manifest", dark_dir / "SHA256SUMS.txt"),
        ("optical_flat", flat_root / "flat_a7r3a_optical_rgb.npy"),
        ("optical_flat_uncertainty",
         flat_root / "flat_a7r3a_optical_uncertainty_rgb.npy"),
        ("flat_receipt", flat_root / "FLAT_RECEIPT.json"),
        ("flat_manifest", flat_root / "SHA256SUMS.txt"),
    ]
    upstream = receipt.get("calibrator_hashes", [])
    if not upstream:
        raise RuntimeError("upstream RGB receipt has no calibrator hashes")
    validated = []
    for role, path in paths:
        actual = file_evidence(path)
        matched = _matching_upstream_record(actual, upstream, role)
        validated.append({"role": role, **actual,
                          "upstream_path": matched["path"]})
    return validated


def validate_imported_stack_module(receipt: dict) -> dict:
    """Bind the helper module actually executing to the upstream RGB run."""
    actual = file_evidence(Path(S.__file__))
    matched = _matching_upstream_record(
        actual, receipt.get("calibrator_hashes", []), "imported stack_sony_s6.py")
    return {**actual, "upstream_path": matched["path"]}


def validate_upstream_geometry(group_dir: Path) -> list[dict]:
    """Verify the two consumed geometry files against the upstream manifest."""
    manifest_path = group_dir / "SHA256SUMS.txt"
    manifest = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, filename = line.split(maxsplit=1)
        manifest[filename.strip()] = digest
    validated = []
    for name in ("TRANSFORMS.csv", "STACK_RECEIPT.json"):
        actual = file_evidence(group_dir / name)
        if manifest.get(name) != actual["sha256"]:
            raise RuntimeError(
                f"upstream manifest mismatch for {group_dir / name}: "
                f"{manifest.get(name)} != {actual['sha256']}")
        validated.append(actual)
    validated.append(file_evidence(manifest_path))
    return validated


def calibrate_cfa4(name: str, exposure: float, dark_root: Path, flat_root: Path
                   ) -> dict:
    dark_dir = dark_root / f"{exposure:.10g}"
    dark = np.load(dark_dir / "MASTER_DARK_raw_ADU.npy", mmap_mode="r")
    dark_var = np.load(dark_dir / "MASTER_DARK_VARIANCE_ADU2.npy", mmap_mode="r")
    hot = np.load(dark_dir / "HOT_PIXEL_MAP.npy", mmap_mode="r").astype(bool)
    flat = np.load(flat_root / "flat_a7r3a_optical_rgb.npy", mmap_mode="r")
    flat_unc = np.load(
        flat_root / "flat_a7r3a_optical_uncertainty_rgb.npy", mmap_mode="r")
    with rawpy.imread(str(S.DATA / f"{name}.ARW")) as raw_file:
        raw = raw_file.raw_image_visible.astype(np.float32)
        colors = raw_file.raw_colors_visible.copy()
    if (raw.shape != dark.shape or raw.shape != dark_var.shape
            or raw.shape != hot.shape or raw.shape != flat.shape[:2]
            or raw.shape != flat_unc.shape[:2]):
        raise RuntimeError(
            f"{name}: CFA4 calibration shape mismatch: raw={raw.shape}, "
            f"dark={dark.shape}, dark_var={dark_var.shape}, hot={hot.shape}, "
            f"flat={flat.shape}, flat_unc={flat_unc.shape}")
    if raw.shape[0] % 2 or raw.shape[1] % 2:
        raise RuntimeError(f"{name}: CFA4 requires even raw dimensions: {raw.shape}")
    saturated_full = ndi.binary_dilation(
        raw >= S.SATURATION_RAW, iterations=S.SATURATION_DILATION)
    valid_full = ~saturated_full & ~hot
    valid_full[:40] = valid_full[-40:] = False
    valid_full[:, :40] = valid_full[:, -40:] = False
    images, randoms, systematics, valids, saturations, offsets = [], [], [], [], [], []
    for raw_channel, label, flat_channel in PLANE_SPEC:
        position = np.argwhere(colors[:2, :2] == raw_channel)
        if len(position) != 1:
            raise RuntimeError(f"{name}: unexpected CFA channel {raw_channel}: {position}")
        oy, ox = map(int, position[0])
        plane = np.s_[oy::2, ox::2]
        f = flat[..., flat_channel][plane]
        u = flat_unc[..., flat_channel][plane]
        native = raw[plane] - dark[plane]
        corrected = native / f
        expected = ndi.gaussian_filter(np.maximum(native, 0.0), 2.0, mode="nearest")
        random = ((expected / S.GAIN_E_PER_ADU + S.READ_NOISE_ADU ** 2
                   + dark_var[plane]) / np.square(f))
        systematic = np.square(corrected * u / f)
        images.append((corrected / exposure).astype(np.float32))
        covariance_factor = (S.SPATIAL_COVARIANCE_VARIANCE_FACTOR_8S
                             if abs(exposure - 8.0) < 1e-9 else 1.0)
        randoms.append((random * covariance_factor / exposure ** 2).astype(np.float32))
        systematics.append((systematic / exposure ** 2).astype(np.float32))
        valids.append(valid_full[plane])
        saturations.append(saturated_full[plane])
        offsets.append((oy, ox))
    return {
        "image": np.stack(images, -1),
        "random_variance": np.stack(randoms, -1),
        "systematic_variance": np.stack(systematics, -1),
        "valid": np.stack(valids, -1),
        "saturated": np.stack(saturations, -1),
        "offsets_yx": offsets,
        "hot_pixels": int(hot.sum()),
        "spatial_covariance_variance_factor": covariance_factor,
        "spatial_covariance_basis": S.SPATIAL_COVARIANCE_BASIS,
    }


def warp_cfa4(calibrated: dict, affine_full: np.ndarray,
              moon_output_xy: np.ndarray, moon_exclusion_radius: float) -> dict:
    h, w, _ = calibrated["image"].shape
    image = np.zeros((h, w, 4), np.float32)
    random = np.full((h, w, 4), np.inf, np.float32)
    systematic = np.full((h, w, 4), np.inf, np.float32)
    valid = np.zeros((h, w, 4), bool)
    saturated = np.zeros((h, w, 4), bool)
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    for channel, (oy, ox) in enumerate(calibrated["offsets_yx"]):
        offset_xy = np.array([ox, oy], np.float64)
        linear = affine_full[:, :2]
        translation = (linear @ offset_xy + affine_full[:, 2] - offset_xy) / 2.0
        affine_plane = np.c_[linear, translation]
        warped = S.warp_frame(
            calibrated["image"][..., channel:channel + 1],
            calibrated["random_variance"][..., channel:channel + 1],
            calibrated["systematic_variance"][..., channel:channel + 1],
            calibrated["valid"][..., channel:channel + 1],
            calibrated["saturated"][..., channel], affine_plane)
        (image[..., channel:channel + 1], random[..., channel:channel + 1],
         systematic[..., channel:channel + 1], valid[..., channel:channel + 1],
         warped_sat, _) = warped
        saturated[..., channel] = warped_sat
        moon_plane = (moon_output_xy - offset_xy) / 2.0
        lunar_valid = np.hypot(xx - moon_plane[0], yy - moon_plane[1]) > (
            moon_exclusion_radius / 2.0)
        valid[..., channel] &= lunar_valid
    return {
        "image": image, "random_variance": random,
        "systematic_variance": systematic, "valid": valid,
        "saturated": saturated,
    }


def apply_plane_cfa4(image: np.ndarray, coefficients_cfa4: list,
                     offsets_yx: list[tuple[int, int]],
                     full_shape: tuple[int, int]) -> np.ndarray:
    """Subtract four CFA-native planes expressed in full-sensor coordinates."""
    if len(coefficients_cfa4) != 4:
        raise RuntimeError(
            f"expected four CFA nuisance planes, got {len(coefficients_cfa4)}")
    corrected = image.copy()
    h_full, w_full = full_shape
    h, w = image.shape[:2]
    for channel in range(4):
        oy, ox = offsets_yx[channel]
        y = (2.0 * np.arange(h, dtype=np.float32)[:, None] + oy) / h_full
        x = (2.0 * np.arange(w, dtype=np.float32)[None, :] + ox) / w_full
        c = coefficients_cfa4[channel]
        corrected[..., channel] -= c[0] + c[1] * x + c[2] * y
    return corrected


def fit_plane_difference_cfa4(
        image: np.ndarray, reference: np.ndarray, valid: np.ndarray,
        offsets_yx: list[tuple[int, int]], full_shape: tuple[int, int]
        ) -> tuple[np.ndarray, list[list[float]]]:
    """Fit one robust additive outer-field plane per native CFA plane."""
    if image.shape != reference.shape or image.shape != valid.shape:
        raise RuntimeError(
            f"CFA4 nuisance shape mismatch: {image.shape}, {reference.shape}, "
            f"{valid.shape}")
    if image.ndim != 3 or image.shape[2] != 4:
        raise RuntimeError(f"expected HxWx4 CFA data, got {image.shape}")
    h_full, w_full = full_shape
    h, w = image.shape[:2]
    stride = 8  # 16 full-sensor pixels, matching the RGB nuisance sampling.
    sample_y = np.arange(0, h, stride)
    sample_x = np.arange(0, w, stride)
    coefficients = []
    for channel, (oy, ox) in enumerate(offsets_yx):
        x_full, y_full = np.meshgrid(
            2.0 * sample_x + ox, 2.0 * sample_y + oy)
        radius = np.hypot(
            x_full - S.SOLAR_REFERENCE[0], y_full - S.SOLAR_REFERENCE[1])
        mask = valid[::stride, ::stride, channel].copy()
        mask &= radius > 4.2 * S.SOLAR_RADIUS_PX
        values = ((image[::stride, ::stride, channel]
                   - reference[::stride, ::stride, channel])[mask])
        design = np.c_[
            np.ones(int(mask.sum()), np.float64),
            x_full[mask] / w_full,
            y_full[mask] / h_full,
        ]
        keep = np.isfinite(values)
        if int(keep.sum()) < 1000:
            raise RuntimeError(
                f"insufficient common valid CFA pixels for sky plane {channel}: "
                f"{int(keep.sum())}")
        for _ in range(4):
            coefficient, *_ = np.linalg.lstsq(design[keep], values[keep], rcond=None)
            residual = values - design @ coefficient
            centre = float(np.median(residual[keep]))
            sigma = 1.4826 * float(np.median(np.abs(residual[keep] - centre)))
            keep = np.isfinite(residual) & (np.abs(residual - centre)
                                             < 3.0 * max(sigma, 1e-6))
            if int(keep.sum()) < 1000:
                raise RuntimeError(
                    f"robust CFA sky-plane clipping left too few samples in "
                    f"channel {channel}: {int(keep.sum())}")
        coefficient, *_ = np.linalg.lstsq(
            design[keep], values[keep], rcond=None)
        coefficients.append(coefficient.tolist())
    return apply_plane_cfa4(
        image, coefficients, offsets_yx, full_shape), coefficients


def prepare_subset_cfa4(
        contributions: list[dict], offsets_yx: list[tuple[int, int]],
        full_shape: tuple[int, int]) -> tuple[list[dict], dict[str, list]]:
    """Prepare one full/split/LOO subset without nuisance leakage."""
    if not contributions:
        raise RuntimeError("cannot prepare an empty CFA4 subset")
    reference = next(
        (item for item in contributions if item["mount_group"] == "C"),
        contributions[0])
    prepared = []
    coefficients = {}
    for item in contributions:
        common_valid = item["valid"] & reference["valid"]
        corrected, planes = fit_plane_difference_cfa4(
            item["image"], reference["image"], common_valid,
            offsets_yx, full_shape)
        prepared.append({**item, "image": corrected})
        coefficients[item["name"]] = planes
    return prepared, coefficients


def combine(items: list[dict]) -> tuple:
    shape = items[0]["image"].shape
    numerator = np.zeros(shape, np.float64)
    denominator = np.zeros(shape, np.float64)
    systematic_sigma_numerator = np.zeros(shape, np.float64)
    coverage = np.zeros(shape, np.uint16)
    saturation = np.zeros(shape, np.uint16)
    for item in items:
        weight = np.where(
            item["valid"], 1.0 / np.maximum(item["random_variance"], 1e-20), 0.0)
        numerator += weight * item["image"]
        denominator += weight
        systematic_sigma_numerator += weight * np.sqrt(
            np.where(item["valid"], item["systematic_variance"], 0.0))
        coverage += item["valid"].astype(np.uint16)
        saturation += item["saturated"].astype(np.uint16)
    image = np.where(
        denominator > 0, numerator / np.maximum(denominator, 1e-30), np.nan).astype(np.float32)
    random = np.where(
        denominator > 0, 1.0 / np.maximum(denominator, 1e-30), np.nan).astype(np.float32)
    systematic = np.where(
        denominator > 0,
        np.square(systematic_sigma_numerator / np.maximum(denominator, 1e-30)),
        np.nan).astype(np.float32)
    return image, random + systematic, random, systematic, coverage, saturation


def save_products(outdir: Path, prefix: str, result: tuple) -> None:
    image, total, random, systematic, coverage, saturation = result
    np.save(outdir / f"{prefix}_CFA4_linear_float32_ADU_s.npy", image)
    np.save(outdir / f"{prefix}_VARIANCE_TOTAL.npy", total)
    np.save(outdir / f"{prefix}_VARIANCE_RANDOM.npy", random)
    np.save(outdir / f"{prefix}_VARIANCE_SYSTEMATIC_FLAT.npy", systematic)
    np.save(outdir / f"{prefix}_COVERAGE_N.npy", coverage)
    np.save(outdir / f"{prefix}_SATURATION_COUNT.npy", saturation)


def metrics(a: tuple, c: tuple, z_path: Path) -> dict:
    stride = 4
    # The donor-flat term is explicitly common-mode/fully correlated.  It
    # must not be added twice as though independent in a split-half null.
    z = ((a[0][::stride, ::stride] - c[0][::stride, ::stride])
         / np.sqrt(a[2][::stride, ::stride] + c[2][::stride, ::stride]))
    np.savez_compressed(z_path, z=z.astype(np.float32))
    valid = np.all(np.isfinite(z), axis=2)
    values = z[valid]
    if len(values) < 1000:
        return {"status": "INCONCLUSIVE", "common_pixels": int(len(values))}
    centre = np.median(values, axis=0)
    sigma = 1.4826 * np.median(np.abs(values - centre), axis=0)
    return {"status": "MEASURED", "stride_cfa_pixels": stride,
            "uncertainty_basis": ("independent random variance only; donor-flat "
                                  "systematic is shared and cancels in this null"),
            "common_pixels": int(len(values)), "z_median_cfa4": centre.tolist(),
            "z_sigma_robust_cfa4": sigma.tolist()}


def process_group(exposure: float, names: list[str], rgb_group: Path,
                  outdir: Path, dark_root: Path, flat_root: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=False)
    rows, rgb_receipt = load_rows(rgb_group)
    validated_geometry = validate_upstream_geometry(rgb_group)
    validated_raws = validate_raw_inputs(names, rgb_receipt)
    validated_calibrators = validate_calibrators(
        exposure, dark_root, flat_root, rgb_receipt)
    validated_stack_module = validate_imported_stack_module(rgb_receipt)
    by_name = {row["frame"]: row for row in rows}
    if set(by_name) != set(names):
        raise RuntimeError(f"RGB transform membership mismatch: {set(by_name)} != {set(names)}")
    contributions = []
    offsets = None
    full_shape = None
    for name in names:
        row = by_name[name]
        calibrated = calibrate_cfa4(name, exposure, dark_root, flat_root)
        frame_offsets = calibrated["offsets_yx"]
        if offsets is None:
            offsets = frame_offsets
        elif offsets != frame_offsets:
            raise RuntimeError(
                f"{name}: CFA layout differs within group: {frame_offsets} != {offsets}")
        if full_shape is None:
            full_shape = (calibrated["image"].shape[0] * 2,
                          calibrated["image"].shape[1] * 2)
        elif calibrated["image"].shape[:2] != (full_shape[0] // 2,
                                                full_shape[1] // 2):
            raise RuntimeError(
                f"{name}: CFA shape differs within group: "
                f"{calibrated['image'].shape[:2]}")
        factor = float(row["extinction_factor_to_DSC06993"])
        calibrated["image"] *= factor
        calibrated["random_variance"] *= factor ** 2
        calibrated["systematic_variance"] *= factor ** 2
        affine = np.array([
            [float(row["affine_00"]), float(row["affine_01"]), float(row["affine_02"])],
            [float(row["affine_10"]), float(row["affine_11"]), float(row["affine_12"])],
        ])
        item = warp_cfa4(
            calibrated, affine,
            np.array([float(row["moon_output_x_px"]), float(row["moon_output_y_px"])]),
            float(row["moon_exclusion_radius_px"]))
        item.update({"name": name, "mount_group": row["mount_group"]})
        contributions.append(item)
        print(f"{name}: CFA4 calibrated and registered", flush=True)

    main_items, main_planes = prepare_subset_cfa4(
        contributions, offsets, full_shape)
    full = combine(main_items)
    del main_items
    save_products(outdir, "MASTER", full)

    split_receipt = rgb_receipt.get("split_independent")
    split_metrics = None
    if split_receipt and split_receipt.get("left") and split_receipt.get("right"):
        halves = {}
        half_planes = {}
        for half in ("left", "right"):
            subset = [item for item in contributions
                      if item["name"] in split_receipt[half]]
            if not subset:
                raise RuntimeError(f"empty CFA4 split half: {half}")
            prepared, half_planes[half] = prepare_subset_cfa4(
                subset, offsets, full_shape)
            halves[half] = list(combine(prepared))
            del prepared
        split_common = ((halves["left"][4] > 0) & (halves["right"][4] > 0)
                        & np.isfinite(halves["left"][0])
                        & np.isfinite(halves["right"][0]))
        halves["left"][0], cross_plane = fit_plane_difference_cfa4(
            halves["left"][0], halves["right"][0], split_common,
            offsets, full_shape)
        halves = {key: tuple(value) for key, value in halves.items()}
        save_products(outdir, "SPLIT_LEFT", halves["left"])
        save_products(outdir, "SPLIT_RIGHT", halves["right"])
        split_metrics = metrics(
            halves["left"], halves["right"], outdir / "SPLIT_z_CFA4_ds4.npz")
        split_metrics.update({"partition_method": split_receipt["partition_method"],
                              "left": split_receipt["left"],
                              "right": split_receipt["right"],
                              "left_internal_planes_cfa4": half_planes["left"],
                              "right_internal_planes_cfa4": half_planes["right"],
                              "left_to_right_null_plane_cfa4": cross_plane,
                              "nuisance_planes_authority": (
                                  "CFA4-native; each half fitted from itself; only "
                                  "the explicit cross-half null plane sees both halves")})
        del halves

    loo = []
    for excluded in contributions:
        subset = [item for item in contributions if item is not excluded]
        if not subset:
            loo.append({"frame": excluded["name"], "status": "INCONCLUSIVE"})
            continue
        prepared, loo_planes = prepare_subset_cfa4(
            subset, offsets, full_shape)
        candidate = combine(prepared)[0][::8, ::8]
        delta = candidate - full[0][::8, ::8]
        values = delta[np.all(np.isfinite(delta), axis=2)]
        if len(values) < 1000:
            loo.append({"frame": excluded["name"], "status": "INCONCLUSIVE",
                        "planes_recomputed_from_subset_cfa4": loo_planes,
                        "common_pixels": int(len(values))})
            continue
        centre = np.median(values, axis=0)
        loo.append({"frame": excluded["name"], "status": "MEASURED",
                    "planes_recomputed_from_subset_cfa4": loo_planes,
                    "common_pixels": int(len(values)),
                    "delta_median_cfa4": centre.tolist(),
                    "delta_mad_cfa4": (1.4826 * np.median(
                        np.abs(values - centre), axis=0)).tolist()})

    receipt = {
        "schema": SCHEMA, "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "train": "SONY_A7RIIIA_FE300MM_F2.8_GM", "frame": "CORONA_SOLAR",
        "exposure_s": exposure, "members": names,
        "plane_order": [label for _, label, _ in PLANE_SPEC],
        "plane_offsets_yx": offsets,
        "authority": "PRIMARY_LINEAR_CFA4; RGB products are derivatives",
        "calibration": "dark/hot and donor optical flat before any interpolation; G1/G2 separate",
        "registration": "per-plane affine induced from audited full-sensor transform; exact bilinear random variance",
        "solar_radius_model": rgb_receipt.get("solar_radius_model"),
        "nuisance_planes": {
            "authority": "CFA4-native; RGB nuisance coefficients are not reused",
            "fit_domain": "outer common field beyond 4.2 physical solar radii",
            "main_planes_cfa4": main_planes,
            "independence": ("full, each split half and every LOO subset fitted "
                             "independently; only cross-half null plane is shared"),
        },
        "weighting": "inverse random variance; donor-flat systematic kept fully correlated",
        "spatial_covariance": S.SPATIAL_COVARIANCE_BASIS,
        "split_independent": split_metrics, "leave_one_out": loo,
        "upstream_inputs": rgb_receipt.get("inputs", []),
        "current_raw_hashes_revalidated": validated_raws,
        "current_calibrators_revalidated": validated_calibrators,
        "upstream_calibrator_hashes": rgb_receipt.get("calibrator_hashes", []),
        "upstream_geometry_files": validated_geometry,
        "rgb_authority": {"path": str(rgb_group / "STACK_RECEIPT.json"),
                          "sha256": S.sha256(rgb_group / "STACK_RECEIPT.json")},
        "software": {"path": str(Path(__file__).resolve()),
                     "sha256": S.sha256(Path(__file__).resolve()), "argv": sys.argv,
                     "imported_stack_sony_s6": validated_stack_module},
        "verdict": "CANDIDATE_PENDING_CFA4_SPLIT_LOO_STRUCTURED_QA",
        "source_mutations": 0,
    }
    receipt_path = outdir / "STACK_CFA4_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    with (outdir / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for path in sorted(outdir.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                fh.write(f"{S.sha256(path)}  {path.name}\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rgb-root", type=Path, required=True)
    parser.add_argument("--dark-root", type=Path, required=True)
    parser.add_argument("--flat-root", type=Path, required=True)
    select = parser.add_mutually_exclusive_group(required=True)
    select.add_argument("--exposure", type=float)
    select.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    available = []
    for receipt_path in sorted(args.rgb_root.glob("*/STACK_RECEIPT.json")):
        upstream = json.loads(receipt_path.read_text(encoding="utf-8"))
        available.append((float(upstream["exposure_s"]), receipt_path.parent,
                          list(upstream["members"]), upstream))
    if not available:
        raise SystemExit(f"no RGB group receipts under {args.rgb_root}")
    if args.exposure is not None:
        chosen = min(available, key=lambda row: abs(row[0] - args.exposure))
        exposure = chosen[0]
        if abs(exposure - args.exposure) > 1e-8:
            raise SystemExit(f"exposure not found: {args.exposure}")
        available = [chosen]
    groups = []
    for exposure, rgb_group, names, upstream in available:
        tag = rgb_group.name
        receipt = process_group(exposure, names, rgb_group,
                                args.out / tag, args.dark_root, args.flat_root)
        groups.append({"exposure_s": exposure, "path": tag,
                       "receipt_sha256": S.sha256(args.out / tag / "STACK_CFA4_RECEIPT.json"),
                       "verdict": receipt["verdict"]})
    run = args.out / "RUN_CFA4_RECEIPT.json"
    run.write_text(json.dumps({
        "schema": "SONY_A7RIIIA_FE300_CFA4_RUN_S6_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mount_segment": available[0][3].get("mount_segment")
        if len({row[3].get("mount_segment") for row in available}) == 1 else "mixed",
        "groups": groups, "script_sha256": S.sha256(Path(__file__).resolve()),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
