#!/usr/bin/env python3
"""Small, JSON-only preflight helper for the PixInsight AEL bridge.

MIT License
Copyright (c) 2026 Pere Guerra Serra

Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")

# The connector is validated against this AEL: the edge-aware WOW and the per-family layer names (1.3.5), and the
# soft-log and MGN corrections (1.3.6), which the structure image and the filter layers depend on.
MINIMUM_AEL = (1, 3, 6)


def version_tuple(text) -> tuple:
    """'1.3.6' -> (1, 3, 6); anything unreadable -> () which compares below every release."""
    numbers = []
    for piece in str(text).split("."):
        digits = ""
        for char in piece:
            if not char.isdigit():
                break
            digits += char
        if not digits:
            break
        numbers.append(int(digits))
    return tuple(numbers)


def emit(**payload) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def probe() -> None:
    version = list(sys.version_info[:3])
    if sys.version_info < (3, 10):
        emit(ok=False, kind="too_old", python=sys.executable, version=version,
             message="Python 3.10 or later is required.")
        return
    try:
        import ael
    except Exception as exc:
        emit(ok=False, kind="missing_ael", python=sys.executable, version=version,
             message=f"Cannot import ael: {exc}")
        return
    found = getattr(ael, "__version__", "unknown")
    if version_tuple(found) < MINIMUM_AEL:
        minimum = ".".join(str(n) for n in MINIMUM_AEL)
        emit(ok=False, kind="old_ael", python=sys.executable, version=version, ael_version=str(found),
             ael_file=getattr(ael, "__file__", "unknown"),
             message=f"AEL {found} was found at {getattr(ael, '__file__', 'unknown')}, but this connector needs AEL "
                     f"{minimum} or later. Use the AEL folder that comes with the connector (its runtime folder) "
                     f"or a current source checkout.")
        return
    emit(ok=True, kind="ready", python=sys.executable, version=version,
         ael_version=found, ael_file=getattr(ael, "__file__", "unknown"),
         credit=CREDIT)


def source_range(path: Path) -> None:
    """Range of a floating-point TIFF file as stored. PixInsight maps a float file whose values leave 0-1 to exactly 0-1
    when it opens it, (x - min) / (max - min), so the view is not the data in the file."""
    import numpy as np
    import tifffile

    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        if page.dtype.kind != "f":
            emit(ok=True, kind="not_float", dtype=str(page.dtype), outside_unit_range=False)
            return
        array = page.asarray()
    finite = np.isfinite(array)
    if not finite.any():
        emit(ok=False, kind="no_finite_samples", message="The file holds no finite samples.")
        return
    low, high = float(array[finite].min()), float(array[finite].max())
    emit(ok=True, kind="range", dtype=str(array.dtype), minimum=low, maximum=high,
         outside_unit_range=bool(low < 0.0 or high > 1.0))


def inspect(path: Path, width: int, height: int, channels: int, require_icc: bool,
            icc_source: Path | None) -> None:
    import tifffile

    original_icc = icc_source.read_bytes() if icc_source is not None else b""
    with tifffile.TiffFile(path) as tf:
        if len(tf.pages) != 1:
            emit(ok=False, kind="invalid_tiff", message="The temporary TIFF must contain exactly one image.")
            return
        page = tf.pages[0]
        array = page.asarray()
        shape = list(array.shape)
        dtype = str(array.dtype)
        icc_tag = page.tags.get(34675)
        current_icc = bytes(icc_tag.value) if icc_tag is not None else b""
        planar_tag = page.tags.get(284)
        planar = int(planar_tag.value) if planar_tag is not None else 1

    expected = [height, width] if channels == 1 else [height, width, channels]
    if shape != expected:
        emit(ok=False, kind="invalid_layout", shape=shape, expected=expected, dtype=dtype,
             message="Unexpected TIFF layout. RGB samples must be interleaved as (height, width, 3), not planar.")
        return
    if dtype != "float32":
        emit(ok=False, kind="invalid_dtype", shape=shape, dtype=dtype,
             message="The temporary TIFF is not 32-bit floating point.")
        return
    if planar != 1:
        emit(ok=False, kind="invalid_layout", shape=shape, dtype=dtype, planar=planar,
             message="Planar TIFF output is not supported; interleaved samples are required.")
        return
    if require_icc and not original_icc and not current_icc:
        emit(ok=False, kind="icc_lost", shape=shape, dtype=dtype, icc_bytes=0,
             message="The source ICC profile was not preserved in the temporary TIFF.")
        return

    icc_repaired = bool(original_icc and current_icc != original_icc)
    if icc_repaired:
        repaired = path.with_name(path.stem + ".icc-repaired.tif")
        tifffile.imwrite(repaired, array, photometric="rgb" if channels == 3 else "minisblack",
                         metadata=None, extratags=[(34675, "B", len(original_icc), original_icc, True)])
        repaired.replace(path)
        with tifffile.TiffFile(path) as tf:
            verified = tf.pages[0].asarray()
            verified_icc = bytes(tf.pages[0].tags[34675].value)
        if verified.shape != array.shape or verified.dtype != array.dtype or verified.tobytes() != array.tobytes():
            emit(ok=False, kind="icc_repair_changed_pixels", message="ICC restoration changed the image samples.")
            return
        if verified_icc != original_icc:
            emit(ok=False, kind="icc_lost", message="The original ICC profile could not be restored exactly.")
            return
        current_icc = verified_icc

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    emit(ok=True, kind="ready", shape=shape, dtype=dtype, planar=planar,
         icc_bytes=len(current_icc), icc_repaired=icc_repaired,
         sha256=digest.hexdigest(), bytes=path.stat().st_size)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("probe")
    source = sub.add_parser("source-range")
    source.add_argument("path", type=Path)
    check = sub.add_parser("inspect")
    check.add_argument("path", type=Path)
    check.add_argument("--width", type=int, required=True)
    check.add_argument("--height", type=int, required=True)
    check.add_argument("--channels", type=int, required=True)
    check.add_argument("--require-icc", action="store_true")
    check.add_argument("--icc-source", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "probe":
            probe()
        elif args.command == "source-range":
            source_range(args.path)
        else:
            inspect(args.path, args.width, args.height, args.channels, args.require_icc, args.icc_source)
    except Exception as exc:
        emit(ok=False, kind="preflight_error", message=str(exc))


if __name__ == "__main__":
    main()
