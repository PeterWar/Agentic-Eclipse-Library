#!/usr/bin/env python3
"""Rebuild the large-scale FE 300/2.8 optical flat for the Sony A7RIIIA.

The 108 twilight flats were made with an A7III, so this product deliberately
retains only the smooth, 180-degree-even optical illumination field.  Sensor
PRNU and dust from the donor body are rejected by plane separation, strong
smoothing and physical-pitch resampling.  It is an optical-flat calibration,
not an A7RIIIA sensor-flat claim.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image
from scipy import ndimage as ndi


BASE = Path("/Users/USUARI/Desktop/Sony Calibration/Calibració A7III 04-2025")
SETS = {
    "3200": BASE / "Flats NETS 300mm 3200",
    "6400": BASE / "Flats NETS 300mm 6400",
}
PITCH_A7III_UM = 5.94
PITCH_A7R3A_UM = 4.51
TARGET_H, TARGET_W = 5320, 7968
SMOOTH_SIGMA_HALFRES_PX = 25.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_set(paths: list[Path]) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    acc = None
    colors = None
    accepted = []
    for path in paths:
        with rawpy.imread(str(path)) as raw:
            image = raw.raw_image_visible.astype(np.float32)
            colors = raw.raw_colors_visible.copy()
            black = np.asarray(raw.black_level_per_channel, np.float32)
            white = float(raw.white_level)
        bmap = black[colors]
        signal = image - bmap
        saturated = image > (bmap + 0.90 * (white - bmap))
        sat_fraction = float(saturated.mean())
        median = float(np.median(signal[~saturated]))
        if sat_fraction > 0.001 or not np.isfinite(median) or median <= 0:
            accepted.append({"path": str(path), "accepted": False,
                             "saturated_fraction": sat_fraction, "median_adu": median})
            continue
        normalized = signal / median
        if acc is None:
            acc = np.zeros_like(normalized, dtype=np.float64)
        acc += normalized
        accepted.append({"path": str(path), "accepted": True,
                         "saturated_fraction": sat_fraction, "median_adu": median})
    n = sum(x["accepted"] for x in accepted)
    if acc is None or colors is None or n < 2:
        raise RuntimeError("not enough accepted flats")
    return (acc / n).astype(np.float32), colors, accepted


def planes_half(image: np.ndarray, colors: np.ndarray) -> np.ndarray:
    h, w = image.shape
    h -= h % 2
    w -= w % 2
    out = []
    for channels in ((0,), (1, 3), (2,)):
        mask = np.isin(colors, channels).astype(np.float32)
        numerator = (image * mask)[:h, :w].reshape(h // 2, 2, w // 2, 2).sum((1, 3))
        denominator = mask[:h, :w].reshape(h // 2, 2, w // 2, 2).sum((1, 3))
        out.append(numerator / np.maximum(denominator, 1))
    return np.stack(out, axis=-1).astype(np.float32)


def even_smooth(planes: np.ndarray) -> np.ndarray:
    even = 0.5 * (planes + planes[::-1, ::-1])
    smooth = np.stack([
        ndi.gaussian_filter(even[..., c], SMOOTH_SIGMA_HALFRES_PX, mode="nearest")
        for c in range(3)
    ], axis=-1).astype(np.float32)
    h, w = smooth.shape[:2]
    cy, cx = h // 2, w // 2
    centre = smooth[cy - 50:cy + 50, cx - 50:cx + 50].mean((0, 1))
    return smooth / centre


def resample_to_a7r3a(field: np.ndarray) -> np.ndarray:
    h, w = field.shape[:2]
    cy, cx = h / 2 - 0.5, w / 2 - 0.5
    yr, xr = np.mgrid[0:TARGET_H, 0:TARGET_W].astype(np.float32)
    uy = (yr - (TARGET_H / 2 - 0.5)) * PITCH_A7R3A_UM / (2 * PITCH_A7III_UM) + cy
    ux = (xr - (TARGET_W / 2 - 0.5)) * PITCH_A7R3A_UM / (2 * PITCH_A7III_UM) + cx
    out = np.empty((TARGET_H, TARGET_W, 3), np.float32)
    for channel in range(3):
        out[..., channel] = ndi.map_coordinates(
            field[..., channel], [uy, ux], order=1, mode="nearest")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    paths_by_set = {tag: sorted(folder.glob("*.ARW")) for tag, folder in SETS.items()}
    if {tag: len(paths) for tag, paths in paths_by_set.items()} != {"3200": 49, "6400": 59}:
        raise SystemExit(f"unexpected flat counts: { {k: len(v) for k, v in paths_by_set.items()} }")

    products = {}
    ledgers = {}
    for tag, paths in paths_by_set.items():
        image, colors, ledger = load_set(paths)
        products[tag] = even_smooth(planes_half(image, colors))
        ledgers[tag] = ledger
        print(f"{tag}: {sum(x['accepted'] for x in ledger)}/{len(ledger)} accepted", flush=True)

    combined = 0.5 * (products["3200"] + products["6400"])
    # Half the independent-set difference is a conservative 1-sigma systematic
    # proxy for sky-gradient and illumination repeatability at large scale.
    uncertainty_half = 0.5 * np.abs(products["3200"] - products["6400"])
    flat = resample_to_a7r3a(combined)
    uncertainty = resample_to_a7r3a(uncertainty_half)
    np.save(args.out / "flat_a7r3a_optical_rgb.npy", flat)
    np.save(args.out / "flat_a7r3a_optical_uncertainty_rgb.npy", uncertainty)
    np.save(args.out / "flat_a7iii_even_smooth_rgb_halfres.npy", combined)

    diagnostic = np.concatenate([
        np.clip((combined[..., 1] - 0.30) / 0.75, 0, 1),
        np.clip(uncertainty_half[..., 1] / 0.03, 0, 1),
        np.clip((products["3200"][..., 1] / products["6400"][..., 1] - 0.94) / 0.12, 0, 1),
    ], axis=1)
    Image.fromarray((diagnostic[::2, ::2] * 255).astype(np.uint8)).save(
        args.out / "flat_diagnostic.png")

    all_paths = [p for paths in paths_by_set.values() for p in paths]
    hashes = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(sha256, p): p for p in all_paths}
        for future in concurrent.futures.as_completed(futures):
            hashes[str(futures[future])] = future.result()

    receipt = {
        "schema": "SONY_FE300_OPTICAL_FLAT_RECEIPT_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_body": "Sony A7 III",
        "target_body": "Sony A7R IIIA",
        "lens": "Sony FE 300mm F2.8 GM OSS at f/2.8",
        "purpose": "large-scale optical illumination only",
        "forbidden_claims": ["A7RIIIA sensor PRNU", "A7RIIIA sensor dust map"],
        "method": {
            "black_subtraction": "per CFA colour from RAW metadata",
            "normalization": "per-frame unsaturated median",
            "set_combination": "equal mean of the 3200 and 6400 twilight sets",
            "sky_gradient_rejection": "180-degree even component",
            "sensor_pattern_rejection": f"Gaussian sigma {SMOOTH_SIGMA_HALFRES_PX} px at half resolution",
            "resampling": "physical pixel pitch, optical axes centred",
            "pitch_um": {"A7III": PITCH_A7III_UM, "A7RIIIA": PITCH_A7R3A_UM},
        },
        "counts": {tag: {"total": len(ledger), "accepted": sum(x["accepted"] for x in ledger)}
                   for tag, ledger in ledgers.items()},
        "flat_stats_rgb": {
            "minimum": flat.reshape(-1, 3).min(0).tolist(),
            "median": np.median(flat.reshape(-1, 3), axis=0).tolist(),
            "maximum": flat.reshape(-1, 3).max(0).tolist(),
            "corner_tl": flat[0, 0].tolist(),
            "corner_br": flat[-1, -1].tolist(),
        },
        "uncertainty_stats_rgb": {
            "median": np.median(uncertainty.reshape(-1, 3), axis=0).tolist(),
            "p99": np.percentile(uncertainty.reshape(-1, 3), 99, axis=0).tolist(),
        },
        "source_sha256": hashes,
        "ledger": ledgers,
        "source_mutations": 0,
    }
    (args.out / "FLAT_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    with (args.out / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for path in sorted(args.out.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                fh.write(f"{sha256(path)}  {path.name}\n")
    print(json.dumps(receipt["flat_stats_rgb"], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
