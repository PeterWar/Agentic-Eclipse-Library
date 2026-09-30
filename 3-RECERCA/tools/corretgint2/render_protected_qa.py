"""Renderitza a 100 % els gates protegits del candidat Corretgint2.

Els PNG són només QA visual. No modifiquen el PSB ni intervenen en cap gate
numèric del builder.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


FRAME = (457, 463, 7417, 5103)
CANVAS = (5353, 7648)


def display_rgb(rgb16: np.ndarray) -> np.ndarray:
    value = np.clip(np.asarray(rgb16, dtype=np.float32) / 65535.0, 0.0, 1.0)
    value = np.power(value, 1.0 / 2.2)
    return np.clip(np.rint(value * 255.0), 0, 255).astype(np.uint8)


def crop_document(array: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    left, top, right, bottom = box
    if array.shape[:2] == CANVAS:
        return np.asarray(array[top:bottom, left:right])
    return np.asarray(
        array[top - FRAME[1] : bottom - FRAME[1], left - FRAME[0] : right - FRAME[0]]
    )


def labelled_panel(items: list[tuple[str, np.ndarray]], output: Path) -> None:
    rendered = [Image.fromarray(display_rgb(item), mode="RGB") for _label, item in items]
    width = sum(image.width for image in rendered)
    height = max(image.height for image in rendered) + 42
    panel = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(panel)
    x = 0
    for (label, _item), image in zip(items, rendered):
        panel.paste(image, (x, 42))
        draw.text((x + 8, 12), label, fill="white")
        x += image.width
    panel.save(output)


def labelled_panel_display8(items: list[tuple[str, np.ndarray]], output: Path) -> None:
    rendered = [Image.fromarray(np.asarray(item, dtype=np.uint8), mode="RGB") for _label, item in items]
    width = sum(image.width for image in rendered)
    height = max(image.height for image in rendered) + 42
    panel = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(panel)
    x = 0
    for (label, _item), image in zip(items, rendered):
        panel.paste(image, (x, 42))
        draw.text((x + 8, 12), label, fill="white")
        x += image.width
    panel.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    work = args.work

    final = np.load(work / "merged_rgb16.npy", mmap_mode="r")
    lower4 = np.load(work / "frozen_L4_ID3_to_ID4_rgb16.npy", mmap_mode="r")
    upper4 = np.load(work / "upper_O_after_P3_rgb16.npy", mmap_mode="r")
    gate4 = np.load(work / "protected_gate_layer_4.npy", mmap_mode="r")
    core4 = np.load(work / "protected_core_layer_4.npy", mmap_mode="r")

    centre_box = (3437, 2139, 4637, 3339)
    contact_box = (3450, 2380, 3770, 2900)
    Image.fromarray(display_rgb(crop_document(final, centre_box)), mode="RGB").save(
        work / "preview_final_centre_100pct.png"
    )
    labelled_panel(
        [
            ("L4 congelat", crop_document(lower4, contact_box)),
            ("Superior original", crop_document(upper4, contact_box)),
            ("Final H40", crop_document(final, contact_box)),
        ],
        work / "preview_contact_L4_final_100pct.png",
    )

    upper_crop = display_rgb(crop_document(upper4, centre_box))
    final_crop = display_rgb(crop_document(final, centre_box))
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
    labelled_panel_display8(
        [
            ("Superior original", upper_crop),
            ("Final H40", final_crop),
            ("abs diff x4", diff4),
            ("abs diff x16", diff16),
        ],
        work / "preview_centre_i_diferencies_100pct.png",
    )

    gate_crop = crop_document(gate4, centre_box)
    core_crop = crop_document(core4, centre_box)
    gate_rgb = np.zeros((*gate_crop.shape, 3), dtype=np.uint8)
    gate_rgb[..., 0] = np.clip(np.rint(gate_crop * 255.0), 0, 255).astype(np.uint8)
    gate_rgb[..., 1] = core_crop.astype(np.uint8) * 255
    Image.fromarray(gate_rgb, mode="RGB").save(work / "preview_gate_P4_100pct.png")


if __name__ == "__main__":
    main()
