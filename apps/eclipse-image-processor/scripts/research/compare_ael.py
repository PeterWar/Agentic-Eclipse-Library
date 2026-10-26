"""Read-only filter experiments against a separately downloaded AEL checkout.

AEL is not installed or bundled into the application. Research artifacts (which
may show a private source image) belong under ignored build/research, not Git.
The reference scenes/helpers are from AEL 1.3.2, MIT, Pere Guerra Serra (2026).
See docs/ael-filter-review.md for the pinned revision and interpretation limits.
"""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import time
import warnings

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import tifffile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def correlation(change, signal, selected):
    valid = selected & np.isfinite(change)
    return {
        "correlation": float(np.corrcoef(change[valid], signal[valid])[0, 1]),
        "gain": float(np.sum(change[valid] * signal[valid]) / np.sum(signal[valid] ** 2)),
        "coverage": float(valid.sum() / selected.sum()),
    }


def contact_sheet(images, destination):
    """Display layers only: not a matched-strength final-image comparison."""
    tile, columns = 280, 4
    sheet = Image.new("RGB", (columns * tile, ((len(images) + columns - 1) // columns) * (tile + 30)))
    draw = ImageDraw.Draw(sheet)
    for index, (name, layer) in enumerate(images.items()):
        x, y = index % columns * tile, index // columns * (tile + 30)
        pixels = np.clip(np.nan_to_num(layer, nan=0), 0, 1)
        picture = Image.fromarray((pixels * 255).astype(np.uint8))
        sheet.paste(picture.resize((tile, tile), Image.Resampling.LANCZOS), (x, y + 30))
        draw.text((x + 5, y + 8), name, fill="white")
    sheet.save(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ael-root", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "build/research/ael-review")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=[512, 1500])
    parser.add_argument("--upstream-tests", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.ael_root.resolve()))
    filters = importlib.import_module("ael.filters")
    bank = importlib.import_module("ael.filterbank")
    geometry = importlib.import_module("ael.geometry")
    review = importlib.import_module("ael._tests.test_review")
    lessons = importlib.import_module("ael._tests.test_lessons")
    from core.filters import rhef_normalize
    from watroo import utils

    args.out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(
        ["git", "-C", str(args.ael_root), "rev-parse", "HEAD"], text=True).strip()
    results = {"ael_commit": commit, "rings": {}, "noise": [], "sign": [], "real": []}
    if args.upstream_tests:
        with (args.out / "upstream-tests.log").open("w") as log:
            completed = subprocess.run(
                [sys.executable, str(args.ael_root / "tests/run_tests.py")], stdout=log, stderr=subprocess.STDOUT)
        results["upstream_test_exit_code"] = completed.returncode

    g, radius, valid, image = review._steep_scene(R=120, N=660)
    for scene, data in (("steep", image), ("flat", (image * radius ** 3).astype(np.float32))):
        rank = rhef_normalize(data, radius, np.arange(0, radius.max() + 4, 2),
                              application_radius=126, upsilon=None, valid=valid)
        continuous = bank.make_filter("rhef", data, valid, g)[0]
        for name, layer in (("app_rank", rank), ("ael_continuous", continuous)):
            results["rings"][f"{scene}/{name}"] = review._ripple(layer, radius, valid, 120)

    for smoothing in (0, .8, 1.5):
        noise = np.random.default_rng(91).normal(size=(512, 512)).astype(np.float32)
        if smoothing:
            noise = gaussian_filter(noise, smoothing)
        noise /= noise.std()
        valid = np.ones(noise.shape, bool)
        region = np.zeros(noise.shape, bool)
        region[100:412, 100:412] = True
        factors = filters.noise_factors(noise, valid, region, n_scales=6, trusted_scales=4, margin=16)
        results["noise"].append({"smoothing": smoothing, "factors": factors.tolist(),
                                 "ratio_to_white": (factors[:4] / filters.STARLET_NOISE[:4]).tolist()})

    for offset in (0, 6):
        g = geometry.EclipseGeometry((360, 360), (179.7, 180.3), 40,
                                     (179.7 + offset, 180.3), 41)
        radius, theta = g.radius_map(), np.radians(g.pa_map())
        valid = (g.radius_map("moon") > 43) & (radius < 170)
        scene = ((np.maximum(radius, 1) / 40) ** -3 *
                 (1 + .3 * np.cos(3 * theta) + .1 * np.sin(7 * theta))).astype(np.float32)
        for sigma in (0, .003, .01):
            noise = (1 + sigma * np.random.default_rng(1).standard_normal(scene.shape)).astype(np.float32)
            for frequency in (17, 37):
                signal = .005 * np.sin(frequency * theta + 1.33) * np.exp(-((radius - 106) / 43) ** 4)
                clean = (scene * noise).astype(np.float32)
                injected = (scene * np.exp(signal) * noise).astype(np.float32)
                clean[~valid] = .01
                injected[~valid] = .01
                selected = valid & (radius > 60) & (radius < 165)
                operators = {
                    "ael_wow": lambda a: bank.make_filter("wow", a, valid, g)[0],
                    "ael_bilateral": lambda a: bank.make_filter("wow_bilateral", a, valid, g)[0],
                    "watroo_standard": lambda a: utils.wow(a.astype(float), n_scales=6,
                                                         denoise_coefficients=[], bilateral=None)[0],
                    "watroo_bilateral": lambda a: utils.wow(a.astype(float), n_scales=6,
                                                          denoise_coefficients=[], bilateral=1)[0],
                }
                for name, run in operators.items():
                    change = run(injected.copy()) - run(clean.copy())
                    results["sign"].append(dict(operator=name, offset=offset, noise=sigma,
                                                frequency=frequency, **correlation(change, signal, selected)))
        print(f"Synthetic sign sweep complete: lunar offset {offset}", flush=True)

    # This reproduces the upstream reference case, which is not a realistic input
    # to an unmasked filter: the hidden lunar interior contains a bright r^-3 law.
    g, radius, _, theta, valid, image = lessons._ring_free_scene()
    signal = .005 * np.sin(37 * theta + np.random.default_rng(20261005).uniform(-np.pi, np.pi))
    signal *= np.exp(-((radius - 160) / 65) ** 4)
    noise = (1 + .003 * np.random.default_rng(1).standard_normal(image.shape)).astype(np.float32)
    selected = valid & (radius > 90) & (radius < 260)
    for name in bank.NAMES:
        change = (bank.make_filter(name, (image * np.exp(signal) * noise).astype(np.float32), valid, g)[0] -
                  bank.make_filter(name, (image * noise).astype(np.float32), valid, g)[0])
        results["sign"].append(dict(operator=f"ael_reference/{name}", **correlation(change, signal, selected)))

    if args.image:
        from gui.app import EclipseProcessorApp
        image = tifffile.imread(args.image).astype(np.float32)
        if image.ndim == 3:
            image = .299 * image[:, :, 0] + .587 * image[:, :, 1] + .114 * image[:, :, 2]
        cx, cy, radius = EclipseProcessorApp.detect_lunar_limb(image)
        full_geometry = geometry.EclipseGeometry(image.shape, (cx, cy), radius, (cx, cy), radius)
        results["source"] = {"sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(),
                             "shape": list(image.shape), "solar_equals_lunar_assumed": True}
        for size in args.sizes:
            factor = size / max(image.shape)
            g = full_geometry.scaled(factor)
            data = cv2.resize(image, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_AREA)
            valid = g.radius_map("moon") > g.moon_radius_px * 1.03
            images = {}
            for name in bank.NAMES:
                started = time.monotonic()
                with warnings.catch_warnings(record=True) as recorded:
                    warnings.simplefilter("always")
                    layer = bank.make_filter(name, data, valid, g)[0]
                good = valid & np.isfinite(layer)
                results["real"].append({"operator": name, "size": size,
                                        "seconds": time.monotonic() - started,
                                        "coverage": float(good.sum() / valid.sum()),
                                        "warnings": sorted({str(w.message) for w in recorded})})
                images[name] = np.where(good, layer, np.nan)
                print(f"Real image: {size}px {name}", flush=True)
            contact_sheet(images, args.out / f"ael-layers-{size}.png")
    destination = args.out / "reproduced.json"
    destination.write_text(json.dumps(results, indent=2))
    print(f"Research results: {destination}")


if __name__ == "__main__":
    main()
