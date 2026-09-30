"""Minimal RAW calibration for eclipse frames: dark, flat, saturation and Bayer handling.

This is deliberately small: what the motion and structure products need, done correctly.  The full
calibration used for the 2026 image (pedestal per channel, linearity ceiling, PRNU, LDIC stacking) is
described in the skill ``apilatge-imatges-eclipsi``.

Rules kept here:

* Work in the **raw Bayer domain** until the end (dark and flat are raw frames too).
* **Saturation is decided on the raw value**, before any subtraction, with a ceiling below the white
  level where the sensor is still linear (``frac`` of the range above the pedestal).
* No white balance, no demosaicing artefacts: :func:`green_plane` interpolates only the green quincunx
  (for luminance work), :func:`superpixel_rgb` bins each 2×2 cell (half resolution, exact colours).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

__all__ = ["read_raw", "load_calibration_frame", "calibrate", "saturation_mask", "green_plane", "superpixel_rgb"]


def read_raw(path: str | Path, full: bool = True) -> dict:
    """Read a RAW file with rawpy.  Returns the Bayer array (full sensor or visible area), the 2×2
    colour pattern as channel letters, the margins of the visible area, and black/white levels."""
    import rawpy

    with rawpy.imread(str(path)) as r:
        bayer = (r.raw_image if full else r.raw_image_visible).copy()
        desc = r.color_desc.decode()
        pat = np.array([[desc[r.raw_pattern[i, j]] for j in range(2)] for i in range(2)])
        s = r.sizes
        info = dict(bayer=bayer, pattern=pat, top=int(s.top_margin), left=int(s.left_margin),
                    visible_shape=(int(s.height), int(s.width)), black=list(map(float, r.black_level_per_channel)),
                    white=float(r.white_level), full=full)
    if full:
        # colour pattern of the full array: shift the visible-area pattern by the margins' parity
        t, l = info["top"] % 2, info["left"] % 2
        info["pattern"] = np.roll(np.roll(info["pattern"], t, axis=0), l, axis=1)
    return info


def load_calibration_frame(path: str | Path) -> np.ndarray:
    """Load a master dark/flat stored as FITS, NPY or TIFF (float32, raw Bayer geometry)."""
    p = Path(path)
    if p.suffix.lower() in (".fits", ".fit", ".fts"):
        from astropy.io import fits
        return np.asarray(fits.getdata(p), dtype=np.float32)
    if p.suffix.lower() == ".npy":
        return np.load(p).astype(np.float32)
    import tifffile
    return tifffile.imread(p).astype(np.float32)


def saturation_mask(bayer: np.ndarray, white: float, pedestal: float, frac: float = 0.85) -> np.ndarray:
    """True where the raw value is above the linear ceiling ``pedestal + frac·(white − pedestal)``."""
    return np.asarray(bayer) >= (pedestal + frac * (white - pedestal))


def calibrate(bayer: np.ndarray, dark: np.ndarray | float | None = None, flat: np.ndarray | None = None) -> np.ndarray:
    """``(raw − dark) / flat`` in float32.  ``dark`` may be a master frame or a constant pedestal; the
    flat must be normalised (≈1 in the centre).  Nothing is clipped."""
    x = np.asarray(bayer, np.float32)
    if dark is not None:
        x = x - np.asarray(dark, np.float32)
    if flat is not None:
        f = np.asarray(flat, np.float32)
        x = np.where(f > 0, x / np.where(f > 0, f, 1.0), np.nan).astype(np.float32)
    return x


def _green_sites(shape, pattern) -> np.ndarray:
    g = np.zeros(shape, bool)
    for i in range(2):
        for j in range(2):
            if pattern[i, j] == "G":
                g[i::2, j::2] = True
    return g


def green_plane(cal: np.ndarray, pattern, bad: np.ndarray | None = None):
    """Full-resolution green: measured at green sites, mean of the 4 green neighbours elsewhere.

    ``bad`` (e.g. saturation) propagates: an interpolated pixel is bad if any neighbour is.  Returns
    ``(green, bad_out)`` with NaN at bad pixels.
    """
    x = np.asarray(cal, np.float32)
    gs = _green_sites(x.shape, np.asarray(pattern))
    bd = np.zeros(x.shape, bool) if bad is None else np.asarray(bad, bool).copy()
    g = np.where(gs & ~bd, x, 0.0).astype(np.float32)
    ok = (gs & ~bd).astype(np.float32)
    p = np.pad(g, 1)
    q = np.pad(ok, 1)
    s = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    n = q[:-2, 1:-1] + q[2:, 1:-1] + q[1:-1, :-2] + q[1:-1, 2:]
    interp = np.where(n == 4, s / 4.0, np.nan)
    out = np.where(gs, np.where(bd, np.nan, x), interp).astype(np.float32)
    bad_out = ~np.isfinite(out)
    return out, bad_out


def superpixel_rgb(cal: np.ndarray, pattern, bad: np.ndarray | None = None):
    """Half-resolution RGB: each 2×2 Bayer cell gives R, mean(G1, G2), B.  A cell with any bad pixel
    is NaN.  Pixel (i, j) of the result is centred at full-resolution coordinate (2j + 0.5, 2i + 0.5)."""
    x = np.asarray(cal, np.float32)
    h, w = (x.shape[0] // 2) * 2, (x.shape[1] // 2) * 2
    x = x[:h, :w]
    pat = np.asarray(pattern)
    bd = None if bad is None else np.asarray(bad, bool)[:h, :w]
    planes = {"R": [], "G": [], "B": []}
    for i in range(2):
        for j in range(2):
            planes[pat[i, j]].append(x[i::2, j::2])
    rgb = np.stack([planes["R"][0], (planes["G"][0] + planes["G"][1]) / 2, planes["B"][0]], axis=-1)
    if bd is not None:
        cell_bad = bd[0::2, 0::2] | bd[0::2, 1::2] | bd[1::2, 0::2] | bd[1::2, 1::2]
        rgb[cell_bad] = np.nan
    return rgb.astype(np.float32)


# ------------------------------------------------------------------------------------------------
# Flats: master per CFA plane and the fine (pixel-scale) sensor factor
# ------------------------------------------------------------------------------------------------
def split_cfa(mosaic: np.ndarray, pattern) -> tuple[np.ndarray, list[str]]:
    """Mosaic (H, W) → planes (4, H/2, W/2) in the order of ``pattern`` read row by row."""
    x = np.asarray(mosaic)
    h, w = (x.shape[0] // 2) * 2, (x.shape[1] // 2) * 2
    pat = np.asarray(pattern)
    planes, names = [], []
    for i in range(2):
        for j in range(2):
            planes.append(x[i:h:2, j:w:2])
            names.append(str(pat[i, j]))
    return np.stack(planes), names


def merge_cfa(planes: np.ndarray) -> np.ndarray:
    """Inverse of :func:`split_cfa` (same plane order)."""
    p = np.asarray(planes)
    h2, w2 = p.shape[1:]
    out = np.empty((2 * h2, 2 * w2), p.dtype)
    k = 0
    for i in range(2):
        for j in range(2):
            out[i::2, j::2] = p[k]
            k += 1
    return out


def master_flat(paths, *, black: float = 511.5, saturation: float = 13995.0, visible: bool = True,
                ring=(0.05, 0.18), reject_sigma: float = 5.5, progress: bool = False) -> tuple[np.ndarray, dict]:
    """Master flat per CFA plane from RAW flat frames (two passes, weighted mean with rejection).

    Each frame and plane is normalised by the median of a central annulus (radii ``ring`` × the
    smaller dimension); weights are the plane's central signal (photon information).  Second pass:
    per-pixel rejection beyond ``reject_sigma`` of the first-pass scatter.  Saturated pixels are
    excluded.  Returns ``(planes (4, h, w) normalised to ~1, info)``.
    """
    import rawpy

    def load(p):
        with rawpy.imread(str(p)) as r:
            b = (r.raw_image_visible if visible else r.raw_image).astype(np.float32)
            desc = r.color_desc.decode()
            pat = np.array([[desc[r.raw_pattern[i, j]] for j in range(2)] for i in range(2)])
        return b, pat

    paths = list(paths)
    b0, pat = load(paths[0])
    planes0, names = split_cfa(b0, pat)
    _, h, w = planes0.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - (w - 1) / 2, yy - (h - 1) / 2) / min(h, w)
    ann = (rr >= ring[0]) & (rr <= ring[1])

    def norm_planes(b):
        sat = b >= saturation
        pl, _ = split_cfa(b - black, pat)
        sp, _ = split_cfa(sat, pat)
        out, wts = [], []
        for k in range(4):
            med = float(np.median(pl[k][ann & ~sp[k]]))
            v = np.where(sp[k], np.nan, pl[k] / med).astype(np.float32)
            out.append(v)
            wts.append(med)
        return np.stack(out), np.array(wts)

    s1 = np.zeros((4, h, w)); s2 = np.zeros((4, h, w)); sw = np.zeros((4, h, w))
    for n, p in enumerate(paths):
        v, wt = norm_planes(load(p)[0])
        ok = np.isfinite(v)
        wv = wt[:, None, None] * ok
        s1 += np.where(ok, v, 0) * wv; s2 += np.where(ok, v * v, 0) * wv; sw += wv
        if progress and n % 20 == 0:
            print(f"  pass 1: {n + 1}/{len(paths)}")
    mean1 = s1 / np.maximum(sw, 1e-12)
    sd1 = np.sqrt(np.maximum(s2 / np.maximum(sw, 1e-12) - mean1 ** 2, 0))
    s1[:] = 0; sw[:] = 0
    nrej = 0
    for n, p in enumerate(paths):
        v, wt = norm_planes(load(p)[0])
        ok = np.isfinite(v) & (np.abs(v - mean1) <= reject_sigma * np.maximum(sd1, 1e-6))
        nrej += int((np.isfinite(v) & ~ok).sum())
        wv = wt[:, None, None] * ok
        s1 += np.where(ok, v, 0) * wv; sw += wv
        if progress and n % 20 == 0:
            print(f"  pass 2: {n + 1}/{len(paths)}")
    master = (s1 / np.maximum(sw, 1e-12)).astype(np.float32)
    info = dict(n_frames=len(paths), planes=names, pattern=pat.tolist(), black=black, saturation=saturation,
                visible=visible, ring=ring, reject_sigma=reject_sigma, rejected_samples=nrej,
                median_per_plane=[float(np.median(m)) for m in master])
    return master, info


def fine_sensor_factor(master_planes: np.ndarray, sigma_plane_px: float = 2.0, clip: float = 0.05) -> np.ndarray:
    """Pixel-scale sensitivity (PRNU) per plane: ``master / G_σ(master)``, limited to ±``clip``.

    It lives in sensor coordinates, so it transfers between the flat session and the eclipse even if
    the optics were rotated or the dust moved (dust shadows are much larger than σ and cancel in the
    ratio).  Divide calibrated frames by it (re-mosaicked with :func:`merge_cfa`)."""
    import cv2
    out = []
    for m in master_planes:
        k = int(2 * np.ceil(4 * sigma_plane_px) + 1)
        sm = cv2.GaussianBlur(m.astype(np.float32), (k, k), sigma_plane_px, borderType=cv2.BORDER_REFLECT)
        out.append(np.clip(m / np.maximum(sm, 1e-6), 1 - clip, 1 + clip))
    return np.stack(out).astype(np.float32)
