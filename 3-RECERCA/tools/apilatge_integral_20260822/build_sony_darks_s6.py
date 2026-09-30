#!/usr/bin/env python3
"""Build exact-temperature linear-CFA dark masters for the Sony eclipse set.

The output remains in raw ADU (including the camera pedestal), uses all ISO100
40 C candidates at each requested shutter, rejects the per-pixel minimum and
maximum, and propagates both frame variance and variance of the master.  No
negative value is clipped and no debayering is performed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import rawpy


DARKS = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA/Darks A7RIIIA Eclipse"
)
EXPOSURES = [1 / 30, 1 / 8, 1 / 4, 1.0, 2.0, 8.0]


def tag(exposure: float) -> str:
    return f"{exposure:.10g}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inventory() -> dict[float, list[dict]]:
    paths = sorted(DARKS.glob("*.ARW"))
    cmd = ["exiftool", "-q", "-n", "-j", "-FileName", "-ExposureTime", "-ISO",
           "-CameraTemperature", "-Model", *map(str, paths)]
    rows = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)
    by_exp: dict[float, list[dict]] = {}
    for row in rows:
        exposure = float(row.get("ExposureTime", 0))
        iso = int(row.get("ISO", 0))
        temp = float(row.get("CameraTemperature", -999))
        if iso == 100 and abs(temp - 40.0) < 0.01:
            row["path"] = str(DARKS / row["FileName"])
            by_exp.setdefault(exposure, []).append(row)
    return by_exp


def select_exact(by_exp: dict[float, list[dict]], exposure: float) -> list[dict]:
    key = min(by_exp, key=lambda x: abs(x - exposure))
    if abs(key - exposure) > 1e-8:
        raise RuntimeError(f"no exact dark group for {exposure}")
    return sorted(by_exp[key], key=lambda row: row["FileName"])


def build(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    sample_path = Path(rows[0]["path"])
    with rawpy.imread(str(sample_path)) as raw:
        sample = raw.raw_image_visible
        shape = sample.shape
    stack = np.empty((len(rows), *shape), np.uint16)
    for index, row in enumerate(rows):
        with rawpy.imread(row["path"]) as raw:
            image = raw.raw_image_visible
            if image.shape != shape:
                raise RuntimeError(f"shape mismatch: {row['path']} {image.shape} != {shape}")
            stack[index] = image
        print(f"  dark {index + 1}/{len(rows)} {row['FileName']}", flush=True)

    master = np.empty(shape, np.float32)
    frame_variance = np.empty(shape, np.float32)
    rows_per_chunk = 64
    n_used = len(rows) - 2 if len(rows) >= 5 else len(rows)
    for y0 in range(0, shape[0], rows_per_chunk):
        y1 = min(y0 + rows_per_chunk, shape[0])
        block = stack[:, y0:y1].astype(np.float32)
        block.sort(axis=0)
        used = block[1:-1] if len(rows) >= 5 else block
        master[y0:y1] = used.mean(axis=0)
        frame_variance[y0:y1] = used.var(axis=0, ddof=1)
    del stack
    master_variance = frame_variance / n_used
    median = float(np.median(master))
    sigma = float(np.sqrt(np.median(frame_variance)))
    hot = (master > median + max(8.0 * sigma, 8.0)).astype(np.uint8)
    stats = {
        "shape": list(shape),
        "n_input": len(rows),
        "n_per_pixel_after_trim": n_used,
        "master_median_adu": median,
        "master_mean_adu": float(master.mean()),
        "frame_sigma_median_adu": sigma,
        "master_sigma_median_adu": float(np.sqrt(np.median(master_variance))),
        "hot_pixel_fraction": float(hot.mean()),
    }
    return master, master_variance.astype(np.float32), hot, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--exposure", type=float, action="append")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    requested = args.exposure or EXPOSURES
    groups = inventory()
    run_receipts = []
    for exposure in requested:
        rows = select_exact(groups, exposure)
        group_out = args.out / tag(exposure)
        group_out.mkdir()
        print(f"=== {exposure:g} s: {len(rows)} exact ISO100/40C darks", flush=True)
        master, master_variance, hot, stats = build(rows)
        np.save(group_out / "MASTER_DARK_raw_ADU.npy", master)
        np.save(group_out / "MASTER_DARK_VARIANCE_ADU2.npy", master_variance)
        np.save(group_out / "HOT_PIXEL_MAP.npy", hot)
        paths = [Path(row["path"]) for row in rows]
        hashes = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(sha256, path): path for path in paths}
            for future in concurrent.futures.as_completed(futures):
                hashes[str(futures[future])] = future.result()
        receipt = {
            "schema": "SONY_A7RIIIA_MASTER_DARK_S6_V1",
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "exposure_s": exposure,
            "iso": 100,
            "camera_temperature_C": 40.0,
            "method": "per-pixel trimmed mean, minimum and maximum rejected",
            "space": "linear CFA raw ADU including pedestal; no clipping; no debayer",
            "stats": stats,
            "inputs": [{"name": row["FileName"], "path": row["path"],
                        "sha256": hashes[row["path"]]} for row in rows],
            "source_mutations": 0,
        }
        (group_out / "DARK_RECEIPT.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        product_hashes = {}
        for path in sorted(group_out.iterdir()):
            if path.is_file():
                product_hashes[path.name] = sha256(path)
        with (group_out / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
            for name, digest in product_hashes.items():
                fh.write(f"{digest}  {name}\n")
        run_receipts.append({"exposure_s": exposure, "n": len(rows), "path": tag(exposure),
                             "stats": stats})
        del master, master_variance, hot

    (args.out / "RUN_RECEIPT.json").write_text(json.dumps({
        "schema": "SONY_A7RIIIA_DARK_RUN_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "groups": run_receipts,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
