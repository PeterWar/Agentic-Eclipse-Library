"""Pilot 1:1 de la ploma H40, sense construir ni modificar cap PSB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from psd_tools import PSDImage

import build_corretgint2 as b


def display8(rgb: np.ndarray) -> np.ndarray:
    value = np.power(np.clip(rgb, 0.0, 1.0), 1.0 / 2.2)
    return np.clip(np.floor(value * 255.0 + 0.5), 0, 255).astype(np.uint8)


def luminance8(rgb: np.ndarray) -> np.ndarray:
    shown = np.power(np.clip(rgb, 0.0, 1.0), 1.0 / 2.2) * 255.0
    return (
        shown[..., 0] * 0.2126
        + shown[..., 1] * 0.7152
        + shown[..., 2] * 0.0722
    ).astype(np.float32)


def gradient(value: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(value)
    return np.hypot(gx, gy).astype(np.float32)


def crop_frame(value: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    left, top, right, bottom = box
    return np.asarray(
        value[
            top - b.FRAME[1] : bottom - b.FRAME[1],
            left - b.FRAME[0] : right - b.FRAME[0],
        ]
    )


def panel(items: list[tuple[str, np.ndarray]], output: Path) -> None:
    images = [Image.fromarray(display8(value), mode="RGB") for _label, value in items]
    canvas = Image.new(
        "RGB", (sum(image.width for image in images), max(image.height for image in images) + 40), "black"
    )
    draw = ImageDraw.Draw(canvas)
    x = 0
    for (label, _value), image in zip(items, images):
        canvas.paste(image, (x, 40))
        draw.text((x + 8, 12), label, fill="white")
        x += image.width
    canvas.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("work10", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if b.sha256_file(args.source) != b.SOURCE_SHA256:
        raise AssertionError("font PSB inesperada")
    psd = PSDImage.open(args.source)
    layers, _hashes = b.validate_source(psd, args.source)
    header = psd._record.header
    lower, upper = b.compose_p3_upper_reference(
        layers,
        header,
        args.work10 / "frozen_L4_ID3_to_ID4_rgb16.npy",
        args.work10 / "mask_5_125_after_protection3_u16.npy",
        args.work10 / "mask_7_60_after_protection3_u16.npy",
    )
    allowed = np.load(args.work10 / "protected_allowed_layer_4.npy")
    strong = np.load(args.work10 / "protected_strong_layer_4.npy")
    radial = np.load(args.work10 / "protected_radial_gate_layer_4.npy").astype(np.float32)
    core = np.load(args.work10 / "protected_core_layer_4.npy")

    photo, gate, gate_u16, domain, support = b.harmonic_compatibility_gate(
        lower, upper, allowed, strong, radial, core
    )
    final = lower + (upper - lower) * (1.0 - gate[..., None])
    l_lower = luminance8(lower)
    l_upper = luminance8(upper)
    l_final = luminance8(final)
    g_lower = gradient(l_lower)
    g_upper = gradient(l_upper)
    g_final = gradient(l_final)
    g_gate = gradient(gate)
    radial_u16 = b.quantize_half_up_u16(radial)
    partial = (gate_u16 > 0) & (gate_u16 < 65535) & (radial_u16 == 0)
    parent_gradient = np.maximum(g_lower, g_upper)
    excess = g_final - parent_gradient
    correlation = float(np.corrcoef(g_final[partial], g_gate[partial])[0, 1])
    mask_term = np.abs(l_lower - l_upper) * g_gate
    physical_term = gate * g_lower + (1.0 - gate) * g_upper
    metrics = {
        "partial_pixels_outside_radial": int(np.count_nonzero(partial)),
        "final_gradient_median": float(np.median(g_final[partial])),
        "parent_gradient_median": float(np.median(parent_gradient[partial])),
        "gradient_excess_gt_2_pixels": int(np.count_nonzero(excess[partial] > 2.0)),
        "gradient_gate_correlation": correlation,
        "mask_term_dominant_pixels": int(
            np.count_nonzero(mask_term[partial] > physical_term[partial])
        ),
        "photo_nonzero_outside_declared_domain": int(
            np.count_nonzero((photo > 0.0) & ~domain)
        ),
        "core_gate_not_full": int(np.count_nonzero(gate_u16[core] != 65535)),
    }
    if (
        metrics["photo_nonzero_outside_declared_domain"]
        or metrics["core_gate_not_full"]
        or metrics["final_gradient_median"] > metrics["parent_gradient_median"]
        or metrics["gradient_excess_gt_2_pixels"] > 100
        or metrics["gradient_gate_correlation"] > 0.40
    ):
        raise AssertionError(f"pilot H40 no passa: {metrics}")

    np.save(args.output / "protected_photo_h40_u16.npy", b.quantize_half_up_u16(photo))
    np.save(args.output / "protected_gate_h40_u16.npy", gate_u16)
    np.save(args.output / "protected_domain_h40.npy", domain)
    contact = (3450, 2380, 3770, 2900)
    panel(
        [
            ("L4 congelat", crop_frame(lower, contact)),
            ("Superior original", crop_frame(upper, contact)),
            ("H40", crop_frame(final, contact)),
        ],
        args.output / "pilot_contact_100pct.png",
    )
    centre = (3437, 2139, 4637, 3339)
    upper_crop = display8(crop_frame(upper, centre))
    final_crop = display8(crop_frame(final, centre))
    diff4 = np.clip(
        np.abs(final_crop.astype(np.int16) - upper_crop.astype(np.int16)) * 4,
        0,
        255,
    ).astype(np.uint8)
    diff16 = np.clip(
        np.abs(final_crop.astype(np.int16) - upper_crop.astype(np.int16)) * 16,
        0,
        255,
    ).astype(np.uint8)
    centre_panel = Image.new("RGB", (1200 * 4, 1240), "black")
    draw = ImageDraw.Draw(centre_panel)
    for index, (label, value) in enumerate(
        (("Superior original", upper_crop), ("H40", final_crop), ("abs diff x4", diff4), ("abs diff x16", diff16))
    ):
        centre_panel.paste(Image.fromarray(value, mode="RGB"), (index * 1200, 40))
        draw.text((index * 1200 + 8, 12), label, fill="white")
    centre_panel.save(args.output / "pilot_centre_i_diferencies_100pct.png")

    receipt = {
        "status": "PASS",
        "source_sha256": b.SOURCE_SHA256,
        "input_work": str(args.work10),
        "support": support,
        "metrics": metrics,
        "files": {
            path.name: b.sha256_file(path)
            for path in sorted(args.output.iterdir())
            if path.is_file()
        },
    }
    (args.output / "pilot_h40.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
