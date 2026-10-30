#!/usr/bin/env python3
"""JSON runner for the Adobe Photoshop AEL bridge.

MIT License
Copyright (c) 2026 Pere Guerra Serra

Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")
# What the four operations import besides AEL (rawpy only for RAW frames), and the psd-tools modules that
# ael.photoshop loads to write the layered PSB.
NEEDED = ("numpy", "scipy", "cv2", "tifffile", "PIL", "imageio", "psd_tools", "psd_tools.api.layers",
          "psd_tools.constants", "psd_tools.psd.image_resources", "psd_tools.psd.layer_and_mask",
          "psd_tools.psd.tagged_blocks")
# The connector is validated against this AEL: the edge-aware WOW and the per-family layer names (1.3.5), the
# soft-log and MGN corrections (1.3.6), which the structure image and the filter layers depend on, and the geometry
# measured on the image (1.4.0), which the dialogs use when no geometry is given.
# The PixInsight connector refuses an older AEL with the same floor.
MINIMUM_AEL = (1, 4, 0)


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


def runtime() -> dict:
    answer = {"python": sys.executable, "python_version": list(sys.version_info[:3])}
    try:
        import ael
        answer.update(ael_version=ael.__version__, ael_file=ael.__file__)
    except Exception:
        pass
    return answer


def inspect_tiff(path: Path, expected: dict) -> dict:
    import numpy as np
    import tifffile

    with tifffile.TiffFile(path) as tf:
        if len(tf.pages) != 1:
            raise ValueError("The temporary TIFF must contain exactly one image")
        page = tf.pages[0]
        array = page.asarray()
        planar_tag = page.tags.get(284)
        planar = int(planar_tag.value) if planar_tag is not None else 1
        icc_tag = page.tags.get(34675)
        icc_bytes = len(icc_tag.value) if icc_tag is not None else 0
        extra_tag = page.tags.get(338)
    if extra_tag is not None:
        # Photoshop writes an alpha sample only when the visible composite has transparent
        # pixels. There is no data there; never let it become white or black pixels for AEL.
        alpha = array[..., -1]
        full = np.iinfo(alpha.dtype).max if np.issubdtype(alpha.dtype, np.integer) else 1.0
        transparent = int(np.count_nonzero(alpha < full))
        raise ValueError(f"The visible document has {transparent} transparent pixels: there is no data "
                         "there, so AEL was not run. Make the composite opaque deliberately first.")
    channels = int(expected["channels"])
    shape = [int(expected["height"]), int(expected["width"])]
    if channels > 1:
        shape.append(channels)
    if list(array.shape) != shape:
        raise ValueError(f"Unexpected TIFF layout {array.shape}; expected {tuple(shape)}")
    if planar != 1:
        raise ValueError("Planar TIFF is not supported; samples must be interleaved")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return {"shape": list(array.shape), "dtype": str(array.dtype), "planar": planar,
            "icc_bytes": icc_bytes, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def direct_ael(cfg: dict) -> dict:
    operation = cfg["operation"]
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    command = [sys.executable, "-m", "ael", operation,
               "--input", str(Path(cfg["input"]).expanduser().resolve()),
               "--geometry", str(Path(cfg["geometry"]).expanduser().resolve()),
               "--out", str(out)]
    if operation == "structure":
        command += ["--name", "structure"]
        if cfg.get("valid"):
            command += ["--valid", str(Path(cfg["valid"]).expanduser().resolve())]
    else:
        command += ["--rmax", str(cfg.get("rmax", 4.0))]
    completed = subprocess.run(command, text=True, capture_output=True, check=False,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=1800)
    if completed.returncode != 0:
        raise RuntimeError(f"AEL failed ({completed.returncode}): {(completed.stderr or completed.stdout).strip()}")
    try:
        result = json.loads(completed.stdout[completed.stdout.find("{"):completed.stdout.rfind("}") + 1])
    except Exception as exc:
        raise RuntimeError(f"AEL returned no readable JSON: {exc}; {completed.stdout[-1000:]}") from exc
    images = [{"name": key, "path": value} for key, value in result.get("files", {}).items()
              if str(value).lower().endswith((".tif", ".tiff", ".png"))]
    return {"ok": True, "operation": operation, "out": str(out), "images": images,
            "ael_result": result, "command": command, "receipt": result.get("receipt"),
            "gates": result.get("gate")}


def workflow(cfg: dict) -> dict:
    from ael_workflow import run_filters, run_master

    # By default the filter layers come as one layered 16-bit PSB written and verified by AEL: the display base
    # and every filter with its blend mode, opacity, visibility and alpha. "documents" opens every TIFF instead.
    layered = cfg.get("open_mode", "layered") != "documents"
    cfg = dict(cfg, photoshop_layers=layered)
    if cfg["operation"] == "master":
        cfg["filter_options"] = dict(cfg.get("filter_options") or {}, photoshop_layers=layered)
    result = run_master(cfg) if cfg["operation"] == "master" else run_filters(cfg)
    result["operation"] = cfg["operation"]
    if layered:
        if not result.get("psb"):
            raise RuntimeError("AEL did not write the layered PSB")
        linear = [image for image in result["images"] if image.get("kind") == "linear"]
        result["open"] = linear + [{"name": "layers", "kind": "psb", "path": result["psb"]}]
        # The opacity byte exactly as ael.photoshop writes it (Python's round), for Photoshop's own reading.
        result["psb_expected"] = [dict(layer, opacity_byte=int(round(float(layer["opacity"]) * 255)))
                                  for layer in result.pop("psb_layers")]
    else:
        result["open"] = [display_16(image) if image.get("view") == "AEL_DISPLAY" else image
                          for image in result["images"]]
    return result


def display_16(image: dict) -> dict:
    """AEL_DISPLAY is the PixelMath start, a 32-bit float TIFF. Photoshop has no Overlay at 32 bits per channel,
    so the separate documents get a copy rounded once to 16 bits to stack the filter layers on."""
    import numpy as np
    import tifffile
    from ael import io, photoshop

    path = Path(image["path"])
    data = tifffile.imread(path)
    if data.dtype == np.uint16:
        return image
    target = path.with_name(path.stem + "_16bit.tif")
    io.save_tiff(target, photoshop.to_u16(data),
                 description="AEL display start rounded once to 16 bits, for Photoshop's 16-bit blend modes")
    return dict(image, path=str(target))


def execute(cfg: dict) -> dict:
    operation = cfg.get("operation", "probe")
    if operation == "probe":
        if sys.version_info < (3, 10):
            return {"ok": False, "kind": "too_old", "message": "Python 3.10 or later is required",
                    "runtime": runtime()}
        try:
            import ael
        except Exception as exc:
            return {"ok": False, "kind": "missing_ael", "message": f"Cannot import ael: {exc}",
                    "runtime": runtime()}
        found = getattr(ael, "__version__", "unknown")
        if version_tuple(found) < MINIMUM_AEL:
            minimum = ".".join(str(n) for n in MINIMUM_AEL)
            return {"ok": False, "kind": "old_ael", "runtime": runtime(),
                    "message": f"AEL {found} was found at {getattr(ael, '__file__', 'unknown')}, but this connector "
                               f"needs AEL {minimum} or later. Use the AEL folder that comes with the connector (its "
                               f"runtime folder) or a current source checkout."}
        # ael imports psd_tools only when it writes the PSB, so a Python without it, or with a broken one, would
        # pass and fail at the end of a run. Imported here, Photoshop moves on to the next Python instead.
        missing, failed = [], []
        for name in NEEDED:
            if any(name.startswith(parent + ".") for parent in failed):
                continue
            try:
                importlib.import_module(name)
            except Exception as exc:
                failed.append(name)
                missing.append(f"{name} ({type(exc).__name__}: {exc})")
        if not missing:
            try:
                import ael_workflow  # noqa: F401
            except Exception as exc:
                missing.append(f"ael_workflow ({type(exc).__name__}: {exc})")
        if missing:
            return {"ok": False, "kind": "missing_dependency",
                    "message": f"AEL {ael.__version__} found, but this Python lacks {', '.join(missing)}",
                    "runtime": runtime()}
        return {"ok": True, "kind": "ready", "runtime": runtime(), "credit": CREDIT}
    if operation not in ("structure", "polar", "master", "filters"):
        raise ValueError(f"Unsupported operation: {operation}")
    missing = []
    if operation == "master":
        missing += [label for key, label in (("frames", "the master frames"),
                                             ("camera", "the measured camera profile JSON"),
                                             ("geometry", "the reference EclipseGeometry JSON")) if not cfg.get(key)]
    if operation == "filters" and not cfg.get("input"):
        missing.append("an existing linear.npy")
    if missing:
        raise ValueError("Select " + ", ".join(missing))
    # The exported layout is checked before AEL runs, not after its products exist.
    inspection = inspect_tiff(Path(cfg["input"]).expanduser().resolve(), cfg["source"]) if cfg.get("source") else None
    result = direct_ael(cfg) if operation in ("structure", "polar") else workflow(cfg)
    root = Path(cfg["run_root"]).expanduser().resolve()
    receipt = {"product": "Adobe Photoshop AEL bridge", "operation": operation,
               "runtime": runtime(), "source_document": cfg.get("source_document"),
               "input_inspection": inspection, "result": result, "credit": CREDIT}
    receipt_path = root / "AEL_PHOTOSHOP_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False), encoding="utf-8")
    result["bridge_receipt"] = str(receipt_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
        answer = execute(cfg)
    except Exception as exc:
        answer = {"ok": False, "kind": type(exc).__name__, "message": str(exc),
                  "runtime": runtime(), "traceback": traceback.format_exc()}
    args.result.write_text(json.dumps(answer, indent=1, ensure_ascii=False), encoding="utf-8")
    if not answer.get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
