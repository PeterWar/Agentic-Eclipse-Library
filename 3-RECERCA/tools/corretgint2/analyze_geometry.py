"""Mesura read-only del limbe lunar de les capes de Corretgint.psb.

No escriu cap producte. S'executa amb l'intèrpret validat del projecte.
"""

import sys

import numpy as np
from psd_tools import PSDImage
from scipy import ndimage as ndi


SUN = (4020.89, 2737.66)
R_SUN = 446.15


def fit_limb(layer, left=None, top=None):
    rgb = layer.numpy("color")
    left = layer.left if left is None else left
    top = layer.top if top is None else top
    rr = np.arange(0.90, 1.10, 0.0005)
    theta = np.deg2rad(np.arange(0.0, 360.0, 1.0))
    radius, angle = np.meshgrid(rr, theta, indexing="ij")
    x = SUN[0] + radius * R_SUN * np.cos(angle)
    y = SUN[1] - radius * R_SUN * np.sin(angle)
    green = np.asarray(rgb[..., 1], np.float32)
    sample = ndi.map_coordinates(green, [y - top, x - left], order=1, mode="nearest")
    grad = np.gradient(ndi.gaussian_filter1d(np.log(np.maximum(sample, 1e-4)), 4, axis=0), axis=0)
    j0 = int((0.93 - 0.90) / 0.0005)
    j1 = int((1.06 - 0.90) / 0.0005)
    peak = j0 + np.argmax(grad[j0:j1], axis=0)
    limb_r = rr[peak]
    px = SUN[0] + limb_r * R_SUN * np.cos(theta)
    py = SUN[1] - limb_r * R_SUN * np.sin(theta)
    design = np.c_[2.0 * px, 2.0 * py, np.ones_like(px)]
    rhs = px * px + py * py
    cx, cy, c0 = np.linalg.lstsq(design, rhs, rcond=None)[0]
    radius_px = np.sqrt(c0 + cx * cx + cy * cy)
    residual = np.hypot(px - cx, py - cy) - radius_px
    keep = np.abs(residual - np.median(residual)) < 2.5 * np.std(residual)
    cx, cy, c0 = np.linalg.lstsq(design[keep], rhs[keep], rcond=None)[0]
    radius_px = np.sqrt(c0 + cx * cx + cy * cy)
    residual = np.hypot(px[keep] - cx, py[keep] - cy) - radius_px
    return float(cx), float(cy), float(radius_px), float(np.std(residual)), int(keep.sum())


def main(path):
    psd = PSDImage.open(path)
    for index, layer in enumerate(psd):
        cx, cy, radius, rms, count = fit_limb(layer)
        print(
            index,
            layer.layer_id,
            repr(layer.name),
            (layer.left, layer.top, layer.right, layer.bottom),
            f"moon=({cx:.3f},{cy:.3f}) r={radius:.3f} rms={rms:.3f} n={count}",
            flush=True,
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("ús: analyze_geometry.py FITXER.psb")
    main(sys.argv[1])
