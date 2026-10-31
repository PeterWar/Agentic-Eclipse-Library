#!/usr/bin/env python3
"""RAW files in, a layered image out: the automatic workflow shared by the PixInsight and Photoshop connectors.

MIT License
Copyright (c) 2026 Pere Guerra Serra

Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The user chooses the RAW files of the totality and, if there are any, calibration frames. Everything else is
measured on the files and written in the receipt: which files are totality frames, darks or flats; the camera's
black and saturation levels; the lunar disc of every frame; the registration on the Sun; the lunar motion; and the
solar geometry. Nothing is guessed silently: what is assumed is said in the receipt.

Both connectors carry this same file (tools/check_connectors.py keeps the two copies identical): the same photos give
the same linear master and the same filter layers in either program. Only the last step differs: Photoshop receives
one layered 16-bit PSB, PixInsight the layers as images and the PixelMath expressions that compose them.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import shutil
import tempfile
import time

import cv2
import numpy as np

import ael
from ael import calibrate, stack
from ael.geometry import EclipseGeometry, find_disc, fit_limb

from ael_workflow import CREDIT, RAW_EXTENSIONS, runtime

# The top of each RAW range is left out of the stack: some sensors stop being linear well before they clip (the
# Canon R6 Mark III at 85 % of its range). Shorter exposures of the same totality cover what is left out.
LINEARITY_FRACTION = 0.85
# At most this many darks per exposure and flats per camera are combined: the master's noise then sits far below
# that of one light frame, and a whole session of calibration frames stays quick to read.
MAX_DARKS = 32
MAX_FLATS = 48
# Registration on the Sun: the corona between these radii of the reference frame, where it is bright, structured and
# free of the Moon's own scattered light.
RING_RSUN = (1.36, 3.0)
# Apparent diameter of the Moon over that of the Sun at greatest eclipse (eclipse magnitude, Espenak's catalogue):
# the solar radius of a frame is its measured lunar radius over this ratio. Locally the ratio is up to ~1 % smaller,
# the Moon being farther away when it is lower in the sky.
TOTAL_ECLIPSES = {
    "2008-08-01": 1.0394, "2009-07-22": 1.0799, "2010-07-11": 1.0580, "2012-11-13": 1.0500,
    "2015-03-20": 1.0445, "2016-03-09": 1.0450, "2017-08-21": 1.0306, "2019-07-02": 1.0459,
    "2020-12-14": 1.0254, "2021-12-04": 1.0367, "2023-04-20": 1.0132, "2024-04-08": 1.0566,
    "2026-08-12": 1.0386, "2027-08-02": 1.0790, "2028-07-22": 1.0560, "2030-11-25": 1.0468,
    "2031-11-14": 1.0106, "2033-03-30": 1.0462, "2034-03-20": 1.0458, "2035-09-02": 1.0320,
}


class Cancelled(RuntimeError):
    pass


class Progress:
    """Progress for the connector's window: one small JSON file, rewritten in place. A ``cancel`` file beside it,
    written by the window's Stop button, stops the run at the next step."""

    def __init__(self, path: Path | None, cancel: Path | None = None, program: str = "Photoshop"):
        self.path, self.cancel, self.program = path, cancel, program
        self.start = time.time()

    def __call__(self, stage: str, done: int = 0, total: int = 0, message: str = "") -> None:
        if self.cancel and self.cancel.exists():
            raise Cancelled(f"Stopped from {self.program}")
        if not self.path:
            return
        payload = {"stage": stage, "done": done, "total": total, "message": message,
                   "elapsed_s": round(time.time() - self.start, 1)}
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)


# --- what the files are ---------------------------------------------------------------------------------------
def _exif_tags(path: Path) -> dict:
    """Camera, serial number and sub-second time from the file's EXIF, with exifread when it is installed (pure
    Python). A CR3 file keeps its EXIF in boxes (CMT1, CMT2) that hold small TIFF streams: those are read one by one."""
    try:
        import exifread
    except ImportError:
        return {}
    import io as _io

    tags = {}
    with path.open("rb") as handle:
        head = handle.read(1 << 20)
    blobs = []
    if head[4:8] == b"ftyp":
        for name in (b"CMT1", b"CMT2"):
            k = head.find(name)
            if k >= 4:
                size = int.from_bytes(head[k - 4:k], "big")
                blobs.append(head[k + 4:k - 4 + size])
    else:
        blobs.append(head)
    for blob in blobs:
        try:
            found = exifread.process_file(_io.BytesIO(blob), details=False)
        except Exception:
            continue
        tags.update({str(key).split(" ", 1)[-1]: str(value) for key, value in found.items()})
    return tags


def read_metadata(path: Path, raw) -> dict:
    """Exposure, ISO and capture time from LibRaw (``raw``, the file already open in rawpy), which reads every RAW
    format it opens; camera, serial number and sub-second time from the EXIF when exifread can read it. No external
    program is needed."""
    other = raw.other
    signature = f"{raw.sizes.width}x{raw.sizes.height} {raw.color_desc.decode()}"
    tags = {}
    try:
        tags = _exif_tags(path)
    except Exception:
        pass
    return _metadata(tags, float(other.shutter_speed), float(other.iso_speed), other.timestamp, signature)


def _metadata(tags: dict, exposure: float, iso: float, moment, signature: str) -> dict:
    """Exposure, ISO, time and camera: the EXIF's when it has them, otherwise LibRaw's."""
    text = tags.get("ExposureTime", "")
    if "/" in text:
        a, b = text.split("/", 1)
        try:
            exposure = float(a) / float(b)
        except ValueError:
            pass
    elif text:
        try:
            exposure = float(text)
        except ValueError:
            pass
    else:
        exposure = float(f"{exposure:.6g}")
    if tags.get("ISOSpeedRatings", "").strip().isdigit():
        iso = float(tags["ISOSpeedRatings"])
    if moment is None and tags.get("DateTimeOriginal"):
        try:
            moment = datetime.strptime(tags["DateTimeOriginal"].strip()[:19], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            moment = None
    sub = tags.get("SubSecTimeOriginal", "").strip()
    if moment and sub.isdigit():
        moment = moment + timedelta(seconds=float("0." + sub))
    make, model = tags.get("Make", "").strip(), tags.get("Model", "").strip()
    serial = (tags.get("BodySerialNumber") or tags.get("SerialNumber") or "").strip()
    # "Canon" + "Canon EOS R6 Mark III" is one name, not two.
    name = model if model.lower().startswith(make.lower()) else " ".join(v for v in (make, model) if v)
    camera = " ".join(v for v in (name, serial) if v) or f"camera with {signature} sensor"
    return dict(ExposureTime=exposure, ISO=iso, time=moment, camera=camera, model=name or f"{signature} sensor",
                subseconds=bool(sub.isdigit()), exif_read=bool(tags))


def capture_time(row: dict) -> datetime | None:
    return row.get("time")


def camera_key(row: dict) -> str:
    return row.get("camera", "")


def _pattern(raw) -> np.ndarray:
    desc = raw.color_desc.decode()
    return np.array([[desc[raw.raw_pattern[i, j]] for j in range(2)] for i in range(2)])


def raw_survey(path: Path) -> dict:
    """What one RAW file says about itself: shape, Bayer pattern, LibRaw's levels, the masked (optically black)
    border of the sensor, the plateau at its highest value, and a sample of its pixels for the classification."""
    import rawpy

    with rawpy.imread(str(path)) as raw:
        meta = read_metadata(path, raw)
        full, visible, sizes = raw.raw_image, raw.raw_image_visible, raw.sizes
        top, left = int(sizes.top_margin), int(sizes.left_margin)
        h, w = visible.shape
        masked = []
        if left >= 16:
            masked.append(full[top:top + h, 4:left - 4].ravel())
        if top >= 16:
            masked.append(full[4:top - 4, left + 4:left + w - 4].ravel())
        highest = int(visible.max())
        black = None
        if masked:
            # The mean of the masked pixels, not their median: the values are whole numbers and a median rounds the
            # black by up to half a level, which the faint sky shows once each channel is balanced. Light leaking into
            # the border and hot pixels are left out first (beyond 4 sigma of the median, sigma from the MAD).
            values = np.concatenate(masked).astype(np.float64)
            centre = float(np.median(values))
            sigma = 1.4826 * float(np.median(np.abs(values - centre))) or 1.0
            black = float(values[np.abs(values - centre) <= 4 * sigma].mean())
        answer = dict(shape=[h, w], pattern=_pattern(raw).tolist(),
                      libraw_black=float(np.median(raw.black_level_per_channel)), libraw_white=float(raw.white_level),
                      masked_black=black,
                      highest=highest, at_highest=int(np.count_nonzero(visible == highest)),
                      sample=np.asarray(visible[::4, ::4], np.float32), meta=meta)
    return answer


def classify(sample: np.ndarray, black: float, white: float) -> tuple[str, dict]:
    """Dark, flat or light, from the pixels alone.

    A dark is uniform and near black: its brightest pixels are isolated hot pixels, which a blur removes. A flat is
    bright, with nothing much brighter than its median (vignetting darkens it, a corona would rise far above it).
    Everything else is a light frame.
    """
    x = (sample - black) / max(white - black, 1.0)
    median = float(np.median(x))
    blurred = cv2.GaussianBlur(x, (0, 0), 3)
    spread = float(np.percentile(blurred, 99.99) - median)
    h, w = x.shape
    cells = cv2.resize(x, (8, 8), interpolation=cv2.INTER_AREA)
    contrast = float(cells.min() / max(cells.max(), 1e-9))
    stats = dict(median=round(median, 5), blurred_top=round(spread, 5), cell_contrast=round(contrast, 4),
                 saturated=round(float(np.mean(x >= 0.98)), 6))
    if median < 0.01 and spread < 0.01:
        return "dark", stats
    if 0.05 <= median <= 0.95 and spread < 0.6 * median and stats["saturated"] < 0.001:
        return "flat", stats
    return "light", stats


def _fast_look(path: Path):
    """The small JPEG preview and the EXIF straight from the file, without LibRaw (a CR3 keeps both in boxes near
    its start, a TIFF-based RAW in its first IFDs): a few milliseconds a file. None when that is not possible."""
    import io as _io
    try:
        import exifread
    except ImportError:
        return None
    from PIL import Image

    with path.open("rb") as handle:
        head = handle.read(1 << 20)
    if head[4:8] == b"ftyp":
        k = head.find(b"THMB")
        start = head.find(b"\xff\xd8\xff", k) if k >= 0 else -1
        if start < 0:
            return None
        image = Image.open(_io.BytesIO(head[start:]))
        tags = _exif_tags(path)
    else:
        with path.open("rb") as handle:
            found = exifread.process_file(handle, details=True)
        thumb = found.get("JPEGThumbnail")
        if not thumb:
            return None
        image = Image.open(_io.BytesIO(thumb))
        # The maker notes are left out, as for the light frames: the camera must be named the same way for both.
        tags = {str(key).split(" ", 1)[-1]: str(value) for key, value in found.items()
                if key != "JPEGThumbnail" and not str(key).startswith("MakerNote")}
    if not tags.get("ExposureTime") or not tags.get("DateTimeOriginal"):
        return None
    sample = np.asarray(image.convert("L"), np.float32)
    meta = _metadata(tags, 0.0, 0.0, None, "unknown sensor")
    if not meta["camera"] or meta["camera"].startswith("camera with") or not meta["ExposureTime"]:
        return None
    return sample, meta


def thumbnail_kind(path: Path) -> tuple[str, dict]:
    """Dark, flat or light from the JPEG preview inside the RAW file: a calibration session can hold hundreds of
    frames, and a preview tells them apart in milliseconds. The preview's black is 0 and its white 255; a file
    without a preview is read whole."""
    import io as _io
    import rawpy
    from PIL import Image

    try:
        look = _fast_look(path)
    except Exception:
        look = None
    if look is not None:
        kind, stats = classify(look[0], 0.0, 255.0)
        return kind, dict(stats, source="preview"), look[1]
    try:
        raw = rawpy.RawPy()
        raw.open_file(str(path))
        try:
            meta = read_metadata(path, raw)
            thumb = raw.extract_thumb()
        finally:
            raw.close()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            image = Image.open(_io.BytesIO(thumb.data))
            image.draft("L", (image.size[0] // 8, image.size[1] // 8))
            sample = np.asarray(image.convert("L"), np.float32)
        else:
            sample = np.asarray(thumb.data, np.float32).mean(axis=-1)
        kind, stats = classify(sample, 0.0, 255.0)
        return kind, dict(stats, source="preview"), meta
    except Exception:
        survey = raw_survey(path)
        kind, stats = classify(survey["sample"], survey["masked_black"] or survey["libraw_black"],
                               survey["libraw_white"])
        return kind, dict(stats, source="raw"), survey["meta"]


def camera_levels(surveys: list[dict]) -> dict:
    """Black and saturation of one camera, from all its files.

    Black: the mean level of the masked border of the sensor where there is one (LibRaw does not know every camera:
    for the Canon R6 Mark III it declares 0-97 where the sensor reads 512), otherwise LibRaw's black.
    Saturation: where many pixels of a frame share its highest value, that plateau is where the sensor clips; the
    lowest such plateau over the files, otherwise LibRaw's white.
    """
    libraw_black = float(np.median([s["libraw_black"] for s in surveys]))
    masked = [s["masked_black"] for s in surveys if s["masked_black"] is not None]
    if masked:
        black = float(np.median(masked))
        black_source = (f"mean level of the masked border of the sensor (median of {len(masked)} files); LibRaw declares "
                        f"{libraw_black:g}")
    else:
        black, black_source = libraw_black, "LibRaw's black level (the sensor has no masked border in the file)"
    libraw_white = float(np.median([s["libraw_white"] for s in surveys]))
    plateaus = [s["highest"] for s in surveys if s["at_highest"] >= 25 and s["highest"] > black + 0.5 * (libraw_white - black)]
    if plateaus:
        white = float(min(plateaus))
        white_source = f"lowest plateau of the highest value over {len(plateaus)} files; LibRaw declares {libraw_white:g}"
    else:
        white, white_source = libraw_white, "LibRaw's white level (no file clips)"
    if not white > black:
        raise ValueError(f"Invalid levels: black {black}, white {white}")
    return dict(black=black, white=white, black_source=black_source, white_source=white_source,
                linearity_fraction=LINEARITY_FRACTION,
                ceiling=black + LINEARITY_FRACTION * (white - black))


# --- calibration ---------------------------------------------------------------------------------------------
def _spread(items: list, limit: int) -> list:
    if len(items) <= limit:
        return list(items)
    picks = np.linspace(0, len(items) - 1, limit).round().astype(int)
    return [items[i] for i in picks]


def master_dark(paths: list[Path], out: Path, shape, levels: dict) -> dict | None:
    """Median of the dark frames of one exposure, in raw DN with the pedestal: AEL subtracts it from the raw values.
    Each dark is checked on its own raw data first: one with any structure (a prominence, a corona) is no dark."""
    import rawpy

    used = _spread(sorted(paths), MAX_DARKS)
    frames, skipped, not_dark = [], [], []
    for path in used:
        with rawpy.imread(str(path)) as raw:
            frame = raw.raw_image_visible.copy()
        if tuple(frame.shape) != tuple(shape):
            skipped.append(path.name)
            continue
        kind, _ = classify(np.asarray(frame[::4, ::4], np.float32), levels["black"], levels["white"])
        if kind != "dark":
            not_dark.append(path.name)
            continue
        frames.append(frame)
    if not frames:
        return None
    used = [p for p in used if p.name not in skipped and p.name not in not_dark]
    cube = np.stack(frames)
    master = np.empty(cube.shape[1:], np.float32)
    for y0 in range(0, cube.shape[1], 256):          # bounded memory: the median one band of rows at a time
        master[y0:y0 + 256] = np.median(cube[:, y0:y0 + 256], axis=0)
    np.save(out, master)
    return dict(path=str(out), frames=[str(p) for p in used], available=len(paths), used=len(used),
                other_size=skipped, not_dark=not_dark, median_dn=float(np.median(master)))


def master_flat_frame(paths: list[Path], levels: dict, out: Path, shape) -> dict:
    """AEL's master flat (each CFA plane normalised by its central median), put back into the Bayer mosaic. A sensor
    with an odd number of rows or columns keeps its last one uncorrected (the CFA planes hold whole 2x2 cells)."""
    used = _spread(sorted(paths), MAX_FLATS)
    planes, info = calibrate.master_flat(used, black=levels["black"], saturation=levels["ceiling"])
    merged = calibrate.merge_cfa(planes).astype(np.float32)
    mosaic = np.full(tuple(shape), np.nan, np.float32)
    mosaic[:merged.shape[0], :merged.shape[1]] = merged
    bad = ~np.isfinite(mosaic) | (mosaic <= 0.05)
    # Where every flat clipped there is no flat measurement: those pixels are left uncorrected, and counted.
    mosaic[bad] = 1.0
    np.save(out, mosaic)
    return dict(path=str(out), frames=[str(p) for p in used], available=len(paths), used=len(used),
                uncorrected_pixels=int(bad.sum()), range=[float(np.percentile(mosaic, 0.1)),
                                                          float(np.percentile(mosaic, 99.9))],
                median_per_plane=info["median_per_plane"])


# --- one light frame -----------------------------------------------------------------------------------------
def green_half(path: Path, levels: dict, dark: str | None, flat: np.ndarray | None):
    """Calibrated green at half resolution (the mean of the two greens of each 2x2 cell, centred at 2i+0.5) and
    where any of them is above the linear ceiling."""
    import rawpy

    with rawpy.imread(str(path)) as raw:
        mosaic = raw.raw_image_visible.astype(np.float32)
        pattern = _pattern(raw)
    saturated = mosaic >= levels["ceiling"]
    mosaic -= np.load(dark) if dark else levels["black"]
    if flat is not None:
        mosaic /= flat
    planes, names = calibrate.split_cfa(mosaic, pattern)
    sat_planes, _ = calibrate.split_cfa(saturated, pattern)
    greens = [k for k, name in enumerate(names) if name.upper().startswith("G")]
    if len(greens) != 2:
        raise ValueError(f"Expected two green sites in the Bayer pattern {pattern.tolist()}")
    green = 0.5 * (planes[greens[0]] + planes[greens[1]])
    return green.astype(np.float32), sat_planes[greens[0]] | sat_planes[greens[1]], pattern


def find_moon(green: np.ndarray, guess: dict | None = None) -> dict:
    """The lunar limb of one frame (half resolution): found with no input, or, failing that, searched from the Moon
    of the reference frame."""
    try:
        disc = find_disc(green)
        if disc["method"] == "lunar limb":
            return dict(xy=list(disc["xy"]), r=disc["r"], rms=disc["rms"], n_used=disc["n_used"],
                        n_rays=disc["n_rays"], method="found on the frame")
    except RuntimeError as exc:
        if guess is None:
            raise
        reason = str(exc)
    else:
        reason = "no limb"
    if guess is None:
        raise RuntimeError(reason)
    floor = float(np.percentile(green, 0.1))
    work = np.maximum(green - floor, 0).astype(np.float32) + 1e-6
    wide = fit_limb(work, guess["xy"], guess["r"], n_rays=720, search_frac=0.3, smooth_px=1.1, n_iter=4)
    fine = fit_limb(work, wide["xy"], wide["r"], n_rays=720, search_frac=0.08, smooth_px=1.1, n_iter=4)
    if fine["n_used"] < 0.5 * fine["n_rays"] or fine["rms"] > max(1.5, 0.01 * fine["r"]) or \
            abs(fine["r"] - guess["r"]) > 0.05 * guess["r"]:
        raise RuntimeError(f"{reason}; searched from the reference Moon: rms {fine['rms']:.2f} px, "
                           f"{fine['n_used']} of {fine['n_rays']} rays, radius {fine['r']:.1f} px")
    return dict(xy=list(fine["xy"]), r=fine["r"], rms=fine["rms"], n_used=fine["n_used"], n_rays=fine["n_rays"],
                method="searched from the reference Moon")


def band_image(green: np.ndarray, saturated: np.ndarray, moon: dict, sigma: tuple[float, float]):
    """Band-pass of the log corona with normalised convolution: no saturated, empty or lunar pixel counts.

    The small scale stays above the sensor's own pattern (interpolated greens, hot pixels), the large one removes the
    smooth light that the Moon uncovers as it moves. Nothing here is centred anywhere: the band only needs the data.
    """
    valid = np.isfinite(green) & (green > 0) & ~saturated
    yy, xx = np.mgrid[:green.shape[0], :green.shape[1]]
    valid &= np.hypot(xx - moon["xy"][0], yy - moon["xy"][1]) > moon["r"] + max(5.0, 0.02 * moon["r"])
    lg = np.where(valid, np.log(np.where(valid, green, 1)), 0).astype(np.float32)
    v = valid.astype(np.float32)
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    small, large = blur(v, sigma[0]), blur(v, sigma[1])
    band = blur(lg * v, sigma[0]) / np.maximum(small, 1e-6) - blur(lg * v, sigma[1]) / np.maximum(large, 1e-6)
    keep = valid & (large > 0.9)
    return np.where(keep, band, 0).astype(np.float32), keep


# --- registration on the Sun ---------------------------------------------------------------------------------
def _box(center, half: int, shape):
    cx, cy = int(round(center[0])), int(round(center[1]))
    return cy - half, cy + half, cx - half, cx + half


def _crop(a: np.ndarray, box, fill=0):
    y0, y1, x0, x1 = box
    out = np.full((y1 - y0, x1 - x0), fill, a.dtype)
    ys, ye, xs, xe = max(y0, 0), min(y1, a.shape[0]), max(x0, 0), min(x1, a.shape[1])
    if ye > ys and xe > xs:
        out[ys - y0:ye - y0, xs - x0:xe - x0] = a[ys:ye, xs:xe]
    return out


def coarse_shift(ref_band, ref_use, mov_band, mov_keep, center, half, offset):
    """Cross-correlation (not whitened: a band-pass leaves frequencies empty that whitening would inflate) of the
    reference ring against the moving frame, in boxes of the same size; the moving box is moved by ``offset``."""
    box = _box(center, half, ref_band.shape)
    moved = (box[0] + offset[1], box[1] + offset[1], box[2] + offset[0], box[3] + offset[0])
    window = np.outer(np.hanning(2 * half), np.hanning(2 * half)).astype(np.float32)
    a = _crop(np.where(ref_use, ref_band, 0).astype(np.float32), box) * window
    b = _crop(np.where(mov_keep, mov_band, 0).astype(np.float32), moved) * window
    spectrum = np.fft.rfft2(b) * np.conj(np.fft.rfft2(a))
    corr = np.fft.irfft2(spectrum, s=a.shape)
    peak = np.unravel_index(int(np.argmax(corr)), corr.shape)

    def refine(k, n, axis):
        values = [corr[(peak[0] + d) % n, peak[1]] if axis == 0 else corr[peak[0], (peak[1] + d) % n] for d in (-1, 0, 1)]
        den = values[0] - 2 * values[1] + values[2]
        frac = 0.5 * (values[0] - values[2]) / den if den < 0 else 0.0
        k = k + frac
        return k - n if k > n / 2 else k
    dy, dx = refine(peak[0], corr.shape[0], 0), refine(peak[1], corr.shape[1], 1)
    return np.array([offset[0] + dx, offset[1] + dy], np.float64)


def _axes(shape, centre):
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(np.float32)
    return xx - np.float32(centre[0]), yy - np.float32(centre[1])


def _rigid_sampler(shape, centre, theta, shift, axes=None):
    """Coordinates where reference box pixel q falls in the moving box: R(theta) (q - centre) + centre + shift."""
    u, v = axes if axes is not None else _axes(shape, centre)
    c, s = np.float32(math.cos(theta)), np.float32(math.sin(theta))
    mx = (centre[0] + c * u - s * v + shift[0]).astype(np.float32)
    my = (centre[1] + s * u + c * v + shift[1]).astype(np.float32)
    sample = lambda a: cv2.remap(np.ascontiguousarray(a, np.float32), mx, my, cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return sample, u, v


def solve_rigid(ref, ref_use, weight, mov, mov_use, centre, start, *, iterations=150):
    """Weighted Gauss-Newton for mov(R(theta)(x - centre) + centre + t) = a*ref(x) + b: the translation and the turn
    of the field about the Sun (a mount that does not track the sky turns the field during the totality)."""
    gy, gx = np.gradient(mov)
    grad_use = cv2.erode(mov_use.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    t = np.asarray(start, np.float64).copy()
    theta = 0.0
    reach = max(1.0, 0.5 * max(ref.shape))
    axes = _axes(ref.shape, centre)
    for _ in range(iterations):
        sample, u, v = _rigid_sampler(ref.shape, centre, theta, t, axes)
        m = ref_use & (sample(grad_use) > 0.999)
        n = int(m.sum())
        if n < 100:
            raise RuntimeError("Insufficient overlap for solar registration")
        c, s = math.cos(theta), math.sin(theta)
        sx, sy = sample(gx)[m].astype(np.float64), sample(gy)[m].astype(np.float64)
        jt = sx * (-s * u[m] - c * v[m]) + sy * (c * u[m] - s * v[m])
        root = np.sqrt(weight[m]).astype(np.float64)
        a = np.column_stack([sx, sy, jt, -ref[m], -np.ones(n)]) * root[:, None]
        step = np.linalg.lstsq(a, -sample(mov)[m] * root, rcond=None)[0][:3]
        move = float(np.hypot(step[0], step[1]))
        step[:2] *= min(1.0, 1.0 / max(move, 1e-12))
        step[2] = float(np.clip(step[2], -1.0 / reach, 1.0 / reach))
        t += step[:2]
        theta += step[2]
        if move < 1e-4 and abs(step[2]) * reach < 1e-4:
            return t, theta
    raise RuntimeError("Solar registration did not converge")


def fine_rigid(ref_band, ref_use, weight, mov_band, mov_keep, centre, half, start):
    """``solve_rigid`` on the band images in a box around the reference Sun; returns (translation, turn) that take
    reference pixels to the frame's pixels about ``centre`` (half resolution)."""
    whole = np.round(start).astype(int)
    box = _box(centre, half, ref_band.shape)
    moved = (box[0] + whole[1], box[1] + whole[1], box[2] + whole[0], box[3] + whole[0])
    r, ru, w = _crop(ref_band, box), _crop(ref_use, box, False), _crop(weight, box)
    m, mu = _crop(mov_band, moved), _crop(mov_keep, moved, False)
    local = (centre[0] - box[2], centre[1] - box[0])
    t, theta = solve_rigid(r, ru, w, m, mu, local, np.asarray(start, np.float64) - whole)
    return t + whole, theta


def rigid_structure(ref_band, ref_use, mov_band, mov_keep, centre, half, t, theta) -> dict:
    """The registration checked on coronal structure, against the same frame turned 90 and 270 degrees about the
    Sun: those keep the radial statistics and lose the structure. Score = share of what the turn leaves unexplained
    that the registration explains."""
    whole = np.round(t).astype(int)
    box = _box(centre, half, ref_band.shape)
    moved = (box[0] + whole[1], box[1] + whole[1], box[2] + whole[0], box[3] + whole[0])
    r, ru = _crop(ref_band, box), _crop(ref_use, box, False)
    m, mu = _crop(mov_band, moved), _crop(mov_keep, moved, False).astype(np.float32)
    local = (centre[0] - box[2], centre[1] - box[0])
    values = {}
    for turn in (0, 90, 270):
        sample, _, _ = _rigid_sampler(r.shape, local, theta + math.radians(turn), np.asarray(t) - whole)
        use = ru & (sample(mu) > 0.999)
        if use.sum() < 100:
            values[turn] = float("nan")
            continue
        x, y = r[use].astype(np.float64), sample(m)[use].astype(np.float64)
        x, y = x - x.mean(), y - y.mean()
        values[turn] = float((x * y).sum() / max(math.sqrt((x * x).sum() * (y * y).sum()), 1e-30))
    null = max(values[90], values[270])
    score = (values[0] - null) / (1.0 - null) if null < 1 else float("nan")
    return dict(correlation=values[0], turned=[values[90], values[270]], structure_score=score)


GRID_RHO = np.exp(np.linspace(np.log(1.15), np.log(5.0), 25))
GRID_THETA = 16


def photometry_grid(green, saturated, moon, exposure, matrix, centre, radius, levels) -> dict:
    """The corona of one frame on a coarse grid of the canvas (24 radii from 1.15 to 5 solar radii, log spaced, by 16
    position angles), through the frame's final placement ``matrix`` (canvas -> frame, full resolution): the median
    DN/s of its pixels that are neither saturated nor near the top of the range (non-linear), above the noise floor
    and outside the frame's own Moon (half-resolution ``moon``)."""
    h, w = green.shape
    yy, xx = np.mgrid[:h, :w].astype(np.float64)
    span = levels["white"] - levels["black"]
    good = np.isfinite(green) & ~saturated & (green > 0.002 * span) & (green < 0.8 * LINEARITY_FRACTION * span)
    good &= np.hypot(xx - moon["xy"][0], yy - moon["xy"][1]) > moon["r"] * 1.03 + 3
    m = np.asarray(matrix, np.float64)
    inverse = np.linalg.inv(np.vstack([m, [0.0, 0.0, 1.0]]))[:2]
    fx, fy = 2 * xx + 0.5, 2 * yy + 0.5
    cx = inverse[0, 0] * fx + inverse[0, 1] * fy + inverse[0, 2] - centre[0]
    cy = inverse[1, 0] * fx + inverse[1, 1] * fy + inverse[1, 2] - centre[1]
    rho = np.hypot(cx, cy) / radius
    theta = (np.arctan2(cy, cx) % (2 * np.pi)) / (2 * np.pi)
    ring = np.searchsorted(GRID_RHO, rho) - 1
    good &= (ring >= 0) & (ring < len(GRID_RHO) - 1)
    cell = ring[good] * GRID_THETA + np.minimum((theta[good] * GRID_THETA).astype(int), GRID_THETA - 1)
    values = green[good] / exposure
    order = np.argsort(cell, kind="stable")
    cell, values = cell[order], values[order]
    starts = np.flatnonzero(np.r_[True, cell[1:] != cell[:-1]])
    ends = np.r_[starts[1:], len(cell)]
    return {int(cell[a]): float(np.median(values[a:b])) for a, b in zip(starts, ends) if b - a >= 30}


def solve_gains(grids: list[dict], reference: int) -> dict:
    """One photometric gain per frame: log F[n, c] = log a[n] + log S[c], by alternating medians (robust to clouds
    over part of the field and to a few bad cells), with the reference frame's gain fixed at 1. What the gains leave
    unexplained, the residual, measures how far the frames are from one sky: thin clouds or haze changing during the
    totality show there."""
    cells = sorted({c for g in grids for c in g})
    if not cells:
        return dict(gains=[1.0] * len(grids), residual=None, frames_without_overlap=list(range(len(grids))))
    index = {c: k for k, c in enumerate(cells)}
    logf = np.full((len(grids), len(cells)), np.nan)
    for n, g in enumerate(grids):
        for c, value in g.items():
            if value > 0:
                logf[n, index[c]] = math.log(value)
    shared = np.isfinite(logf).sum(axis=0) >= 2
    logf[:, ~shared] = np.nan
    a = np.zeros(len(grids))
    with np.errstate(all="ignore"):
        for _ in range(50):
            sky = np.nanmedian(logf - a[:, None], axis=0)
            new = np.nanmedian(logf - sky[None, :], axis=1)
            new = np.where(np.isfinite(new), new, 0.0)
            new -= new[reference]
            moved = float(np.max(np.abs(new - a)))
            a = new
            if moved < 1e-5:
                break
        residual = logf - a[:, None] - sky[None, :]
    finite = np.isfinite(residual)
    lonely = [n for n in range(len(grids)) if not finite[n].any()]
    spread = float(1.4826 * np.median(np.abs(residual[finite]))) if finite.any() else None
    per_frame = [float(1.4826 * np.median(np.abs(residual[n][finite[n]]))) if finite[n].any() else None
                 for n in range(len(grids))]
    return dict(gains=[float(math.exp(v)) for v in a], residual=spread, residual_per_frame=per_frame,
                frames_without_overlap=lonely, cells=int(shared.sum()))


def fit_lunar_motion(times: np.ndarray, lunar: np.ndarray, use: np.ndarray) -> dict:
    """The Moon relative to the Sun, a straight line in time: over a few minutes the curvature of its path stays
    below 0.1 px for any eclipse photographed with a telescope. Robust: frames more than 3 sigma off are left out,
    sigma from the median absolute residual, never below 0.15 px."""
    keep = use.copy()
    for _ in range(5):
        if keep.sum() < 2:
            raise RuntimeError("Fewer than two frames registered on the corona: the lunar motion cannot be measured")
        design = np.column_stack([np.ones(keep.sum()), times[keep]])
        coef = np.linalg.lstsq(design, lunar[keep], rcond=None)[0]
        residual = lunar - np.column_stack([np.ones(len(times)), times]) @ coef
        norm = np.hypot(residual[:, 0], residual[:, 1])
        sigma = max(0.15, 1.4826 * float(np.median(norm[keep])))
        new = use & (norm <= 3 * sigma)
        if (new == keep).all():
            break
        keep = new
    return dict(intercept=coef[0].tolist(), velocity_px_per_s=coef[1].tolist(), residual=residual,
                residual_norm=norm, sigma=sigma, used=keep)


def eclipse_ratio(moment: datetime | None) -> tuple[float | None, str]:
    """The ratio of apparent radii of the total eclipse photographed, from the date of the frames (±1 day for the
    camera's time zone); None when the date matches no total eclipse of the table (a camera clock left unset)."""
    if moment is None:
        return None, "the frames carry no date"
    for day, ratio in TOTAL_ECLIPSES.items():
        if abs((moment - datetime.strptime(day, "%Y-%m-%d")).total_seconds()) <= 2 * 86400:
            return ratio, f"total solar eclipse of {day}: Moon/Sun apparent diameter {ratio} at greatest eclipse"
    return None, f"the camera's date ({moment:%Y-%m-%d}) matches no total solar eclipse of 2008-2035"


def unique_files(values) -> list[Path]:
    seen, answer = set(), []
    for value in values or []:
        path = Path(value).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in RAW_EXTENSIONS and str(path) not in seen:
            seen.add(str(path))
            answer.append(path)
    return answer


def analyse(raw_files, calibration_files, work: Path, progress=Progress(None)) -> dict:
    """Everything the stack needs, measured on the files: see the module's docstring."""
    t_start = time.time()
    lights_in, calibration_in = unique_files(raw_files), unique_files(calibration_files)
    calibration_in = [p for p in calibration_in if str(p) not in {str(q) for q in lights_in}]
    if not lights_in:
        raise ValueError("Choose the RAW files of the totality (CR2, CR3, NEF, ARW, DNG, RAF, ORF or RW2)")
    every = lights_in + calibration_in
    progress("Reading the files", 0, len(every))
    # The RAW files chosen as totality are read whole (levels, size, a sample); calibration files by their preview.
    surveys, kinds, exif = {}, {}, {}
    for n, path in enumerate(lights_in):
        surveys[str(path)] = raw_survey(path)
        exif[str(path)] = surveys[str(path)]["meta"]
        progress("Reading the files", n + 1, len(every), path.name)
    for n, path in enumerate(calibration_in):
        kind, stats, meta = thumbnail_kind(path)
        kinds[str(path)], exif[str(path)] = (kind, stats), meta
        progress("Reading the files", len(lights_in) + n + 1, len(every), path.name)
    cameras = {}
    for path in lights_in:
        cameras.setdefault(camera_key(exif.get(str(path), {})), []).append(path)
    levels = {key: camera_levels([surveys[str(p)] for p in paths]) for key, paths in cameras.items()}
    files, excluded = {}, []
    for path in every:
        row = exif.get(str(path), {})
        key = camera_key(row)
        if str(path) in surveys:
            # A file chosen as a totality photo stays one: a very short exposure can look as black as a dark, and
            # used as a dark it would erase the data of the other frames. Without a Moon it is simply left out.
            survey = surveys[str(path)]
            kind, stats = "light", {}
            shape = survey["shape"]
        else:
            kind, stats = kinds[str(path)]
            shape = None
        files[str(path)] = dict(path=str(path), name=path.name, camera=key, model=row.get("model"), kind=kind, stats=stats,
                                exposure_s=float(row.get("ExposureTime") or 0), iso=row.get("ISO"),
                                time=capture_time(row), chosen_as="light" if path in lights_in else "calibration",
                                shape=shape)
    for item in files.values():
        if item["chosen_as"] == "calibration" and item["kind"] == "light":
            excluded.append(dict(file=item["name"], reason="chosen as calibration, but it is a light frame"))
    lights = [f for f in files.values() if f["chosen_as"] == "light"]
    if not lights:
        raise ValueError("None of the chosen RAW files is a light frame of the eclipse: " +
                         "; ".join(f"{e['file']}: {e['reason']}" for e in excluded[:5]))
    camera = Counter(f["camera"] for f in lights).most_common(1)[0][0]
    for f in lights:
        if f["camera"] != camera:
            excluded.append(dict(file=f["name"], reason=f"another camera ({f['camera']}): one camera per run, "
                                                        "each optic needs its own distortion model before fusing"))
    lights = [f for f in lights if f["camera"] == camera]
    iso = Counter(f["iso"] for f in lights).most_common(1)[0][0]
    for f in lights:
        if f["iso"] != iso:
            excluded.append(dict(file=f["name"], reason=f"ISO {f['iso']}: the stack uses one ISO, {iso}"))
    lights = [f for f in lights if f["iso"] == iso]
    shape = Counter(tuple(f["shape"]) for f in lights).most_common(1)[0][0]
    for f in lights:
        if tuple(f["shape"]) != shape:
            excluded.append(dict(file=f["name"], reason=f"image size {f['shape']} differs from {list(shape)}"))
    lights = [f for f in lights if tuple(f["shape"]) == shape]
    lv = levels[camera]

    # Calibration of this camera: darks by exposure (only the exposures of the lights), one flat.
    work.mkdir(parents=True, exist_ok=True)
    calibration = {"darks": [], "flat": None, "notes": []}
    # A calibration file chosen as such was only looked at through its preview: its size is checked when it is read.
    fits = lambda f: f["camera"] == camera and (f["shape"] is None or tuple(f["shape"]) == shape)
    darks = [f for f in files.values() if f["kind"] == "dark" and fits(f)]
    flats = [f for f in files.values() if f["kind"] == "flat" and fits(f)]
    other = [f for f in files.values() if f["kind"] in ("dark", "flat") and not fits(f)]
    for f in other:
        excluded.append(dict(file=f["name"], reason=f"a {f['kind']} of another camera or size: not used"))
    dark_for = {}
    exposures = sorted({f["exposure_s"] for f in lights})
    for n, exposure in enumerate(exposures):
        match = [Path(d["path"]) for d in darks if d["iso"] == iso and math.isclose(d["exposure_s"], exposure, rel_tol=1e-3)]
        if not match:
            continue
        progress("Combining darks", n + 1, len(exposures), f"{exposure:g} s")
        info = master_dark(match, work / f"master_dark_{exposure:.6g}s.npy", shape, lv)
        if info is None:
            calibration["notes"].append(f"No usable dark of {exposure:g} s (another image size, or not dark)")
            continue
        info.update(exposure_s=exposure, iso=iso)
        calibration["darks"].append(info)
        dark_for[exposure] = info["path"]
    unmatched = [e for e in exposures if e not in dark_for]
    if darks and unmatched:
        calibration["notes"].append("No dark of the same exposure and ISO for " + ", ".join(f"{e:g} s" for e in unmatched) +
                                    ": those frames are calibrated with the black level only")
    flat = None
    if flats:
        progress("Combining flats", 0, 1, f"{len(flats)} flats")
        try:
            calibration["flat"] = master_flat_frame([Path(f["path"]) for f in flats], lv, work / "master_flat.npy", shape)
            flat = np.load(calibration["flat"]["path"])
            if tuple(flat.shape) != tuple(shape):
                raise ValueError(f"size {list(flat.shape)}")
        except Exception as exc:
            calibration["notes"].append(f"The flats could not be combined for these frames ({exc}): not used")
            calibration["flat"], flat = None, None

    # Pass 1: the Moon of every frame, found with no input, and how much of its corona each frame holds.
    lights.sort(key=lambda f: (f["time"] or datetime.min, f["name"]))
    for n, f in enumerate(lights):
        progress("Finding the Moon", n + 1, len(lights), f["name"])
        green, saturated, _ = green_half(Path(f["path"]), lv, dark_for.get(f["exposure_s"]), flat)
        try:
            f["moon"] = find_moon(green)
        except RuntimeError as exc:
            f["moon"], f["moon_error"] = None, str(exc)
            continue
        yy, xx = np.mgrid[:green.shape[0], :green.shape[1]]
        rho = np.hypot(xx - f["moon"]["xy"][0], yy - f["moon"]["xy"][1]) / f["moon"]["r"]
        ring = (rho >= RING_RSUN[0]) & (rho <= RING_RSUN[1])
        usable = ring & ~saturated & (green > 0)
        f["ring_usable"] = float(usable.sum() / max(ring.sum(), 1))
        f["ring_signal_dn"] = float(np.median(green[usable])) if usable.any() else 0.0
        # Saturation beside the limb, and how much of it falls within 90 degrees of position angle (the photosphere
        # shows as one arc; a saturated corona goes all the way round).
        limb = (rho >= 1.0) & (rho <= 1.3) & saturated
        angle = np.degrees(np.arctan2(yy[limb] - f["moon"]["xy"][1], xx[limb] - f["moon"]["xy"][0])) % 360
        sectors = np.bincount((angle // 10).astype(int) % 36, minlength=36)
        window = np.convolve(np.concatenate([sectors, sectors[:8]]), np.ones(9, int), "valid")[:36]
        f["limb_saturated"] = int(limb.sum())
        f["limb_saturated_top_share"] = float(window.max() / max(int(limb.sum()), 1))
        clear = (rho >= 1.0) & (rho <= 1.3) & ~saturated & (green > 0)
        f["limb_rate"] = float(np.percentile(green[clear], 99.9)) / f["exposure_s"] if clear.any() else 0.0
    # The photosphere (Baily's beads, the diamond ring) is thousands of times brighter than the corona and the
    # chromosphere. A frame that saturates beside the limb, in one direction, at an exposure so short that it takes
    # more than twice the brightest light any clean frame shows there unsaturated, sees the photosphere: its scattered
    # light would enter the stack, so it stays out. A prominence that saturates a longer exposure does not qualify.
    clean = [f for f in lights if f.get("moon") and f["limb_saturated"] == 0 and f["limb_rate"] > 0]
    if clean:
        brightest = max(f["limb_rate"] for f in clean)
        for g in lights:
            if not g.get("moon"):
                continue
            needed = (lv["ceiling"] - lv["black"]) / g["exposure_s"]
            if g["limb_saturated"] >= 15 and g["limb_saturated_top_share"] >= 0.5 and needed > 2 * brightest:
                g["photosphere"] = (f"the photosphere shows (Baily's beads or the diamond ring): {g['limb_saturated']} "
                                    f"saturated pixels beside the limb, {100 * g['limb_saturated_top_share']:.0f} % "
                                    f"within 90 degrees, at {g['exposure_s']:g} s, which takes {needed / brightest:.0f} "
                                    f"times the brightest light the clean frames show there")
    for f in [f for f in lights if f.get("photosphere")]:
        excluded.append(dict(file=f["name"], reason=f["photosphere"]))
        lights.remove(f)
    found = [f for f in lights if f.get("moon")]
    if not found:
        raise RuntimeError("No lunar disc was found on any chosen frame: are these totality frames? " +
                           "; ".join(f"{f['name']}: {f.get('moon_error')}" for f in lights[:3]))
    timed = [f for f in found if f["time"]]
    middle = (min(f["time"] for f in timed) + (max(f["time"] for f in timed) - min(f["time"] for f in timed)) / 2) if timed else None
    def reference_score(f):
        closeness = abs((f["time"] - middle).total_seconds()) if middle and f["time"] else 0.0
        return (-f["ring_usable"] * math.log10(1 + f["ring_signal_dn"]), closeness)
    reference = min(found, key=reference_score)
    ref_green, ref_sat, _ = green_half(Path(reference["path"]), lv, dark_for.get(reference["exposure_s"]), flat)
    ref_moon = reference["moon"]
    radius = ref_moon["r"]
    # The registration works where the Sun is about 240 px across its radius: a long focal length is reduced by a
    # whole factor (block means; a block is saturated if any of its pixels is), and the result scaled back exactly.
    step = max(1, int(round(radius / 240.0)))
    offset_step = (step - 1) / 2.0

    def shrink(green, saturated):
        if step == 1:
            return green, saturated
        h, w = (green.shape[0] // step) * step, (green.shape[1] // step) * step
        blocks = (h // step, step, w // step, step)
        return (green[:h, :w].reshape(blocks).mean(axis=(1, 3)).astype(np.float32),
                saturated[:h, :w].reshape(blocks).any(axis=(1, 3)))

    def shrink_moon(moon):
        return dict(xy=[(v - offset_step) / step for v in moon["xy"]], r=moon["r"] / step)

    small_green, small_sat = shrink(ref_green, ref_sat)
    small_moon = shrink_moon(ref_moon)
    small_radius = radius / step
    sigma = (float(np.clip(3.0 * small_radius / 227.0, 1.5, 6.0)), 0.0)
    sigma = (sigma[0], sigma[0] * 10.0 / 3.0)
    ref_band, ref_keep = band_image(small_green, small_sat, small_moon, sigma)
    yy, xx = np.mgrid[:small_green.shape[0], :small_green.shape[1]]
    rho = np.hypot(xx - small_moon["xy"][0], yy - small_moon["xy"][1]) / small_radius
    ring_use = ref_keep & (rho >= RING_RSUN[0]) & (rho <= RING_RSUN[1])
    weight = np.where(ring_use, cv2.GaussianBlur(np.maximum(small_green, 0), (0, 0), 3), 0).astype(np.float32)
    weight /= max(float(weight.max()), 1e-30)
    half = int(RING_RSUN[1] * small_radius + 2 * sigma[1] + 8)

    # Pass 2: every other frame on the reference, on the corona; its own Moon searched again if pass 1 missed it.
    # A frame whose Moon cannot be measured (in a long exposure scattered light can saturate the lunar disc) is still
    # registered on its corona, behind a lunar mask wide enough for any position of the Moon, starting from the shift
    # of the frames registered nearest in time.
    order = [f for f in lights if f.get("moon")] + [f for f in lights if not f.get("moon")]
    for n, f in enumerate(order):
        progress("Registering on the Sun", n + 1, len(lights), f["name"])
        if f is reference:
            f["corona"] = dict(t=[0.0, 0.0], gates="reference")
            continue
        green, saturated, _ = green_half(Path(f["path"]), lv, dark_for.get(f["exposure_s"]), flat)
        if not f.get("moon"):
            try:
                f["moon"] = find_moon(green, ref_moon)
            except RuntimeError as exc:
                f["moon_error"] = str(exc)
        if f.get("moon"):
            mask_moon = f["moon"]
            offset = np.round(np.asarray(f["moon"]["xy"]) - ref_moon["xy"]).astype(int)
        else:
            known = [(g["time"], g["corona"]["t"]) for g in lights if g.get("corona", {}).get("gates") in
                     ("passed", "reference") and g["time"] and f["time"]]
            if known:
                known.sort(key=lambda item: abs((item[0] - f["time"]).total_seconds()))
                guess = np.asarray(known[0][1])
            else:
                guess = np.zeros(2)
            offset = np.round(guess).astype(int)
            mask_moon = dict(xy=(np.asarray(ref_moon["xy"]) + guess).tolist(), r=radius * 1.16 + 4)
        small, small_saturated = shrink(green, saturated)
        band, keep = band_image(small, small_saturated, shrink_moon(mask_moon), sigma)
        small_offset = np.round(np.asarray(offset, float) / step).astype(int)
        record = {}
        try:
            centre = small_moon["xy"]
            coarse = coarse_shift(ref_band, ring_use, band, keep, centre, half, small_offset)
            fine, theta = fine_rigid(ref_band, ring_use, weight, band, keep, centre, half, coarse)
            starts = [fine_rigid(ref_band, ring_use, weight, band, keep, centre, half, coarse + d)
                      for d in ((1.5, -1.5),)]
            spread = max(max(float(np.hypot(*(st - fine))), abs(th - theta) * half) for st, th in starts) * step
            check = rigid_structure(ref_band, ring_use, band, keep, centre, half, fine, theta)
            record = dict(t=(fine * step).tolist(), theta=theta, coarse=(coarse * step).tolist(), start_spread=spread,
                          structure_score=check["structure_score"], correlation=check["correlation"])
            problems = []
            if spread > 0.05 * step:
                problems.append(f"the result depends on the starting point by {2 * spread:.2f} px")
            if not math.isfinite(check["structure_score"]) or check["structure_score"] < 0.25:
                problems.append(f"structure score {check['structure_score']:.2f} < 0.25")
            record["gates"] = "; ".join(problems) or "passed"
        except RuntimeError as exc:
            record = dict(gates=str(exc))
        f["corona"] = record
    # Everything in full-resolution pixels of each frame from here on: x = 2 x_half + 0.5, shifts x2.
    for f in lights:
        if f.get("moon"):
            f["moon_full"] = dict(xy=[2 * v + 0.5 for v in f["moon"]["xy"]], r=2 * f["moon"]["r"],
                                  rms=2 * f["moon"]["rms"])
        if f.get("corona", {}).get("t") is not None:
            f["corona_full"] = [2 * v for v in f["corona"]["t"]]
            f["corona_theta"] = float(f["corona"].get("theta", 0.0))
    return dict(files=files, lights=lights, reference=reference, levels=lv, camera=camera, iso=iso,
                calibration=calibration, excluded=excluded, sigma_half_px=sigma, shape=list(shape),
                dark_for=dark_for, flat=calibration["flat"]["path"] if calibration["flat"] else None,
                centre_full=[2 * v + 0.5 for v in ref_moon["xy"]], registration_scale=step,
                analysis_s=round(time.time() - t_start, 1))


def decide(analysis: dict) -> dict:
    """Where every frame goes on the reference canvas, and which frames stay out.

    The corona fixes the Sun but its registration is noisy in short or long exposures; the lunar limb is measured to
    a tenth of a pixel in every frame, but the Moon moves across the Sun. Over a totality that motion is a straight
    line in time, so it is fitted on the frames that the corona registered, and each frame is then placed by its own
    limb minus the line: the Sun of frame i is at moon_i - (a + b t_i). A frame the corona registered far from the
    line is left out; without times, or with fewer than three frames on the corona, the corona registration is used
    as it is.
    """
    lights, reference = analysis["lights"], analysis["reference"]
    placed = [f for f in lights if f.get("moon_full")]
    # A frame whose Moon cannot be measured but whose corona registered (a long exposure with a saturated lunar disc)
    # is placed by the corona alone; its Moon, for the stack's lunar mask, comes from the fitted lunar motion.
    by_corona = [f for f in lights if not f.get("moon_full") and f.get("corona", {}).get("gates") == "passed"]
    for f in lights:
        if not f.get("moon_full") and f not in by_corona:
            analysis["excluded"].append(dict(file=f["name"], reason="no lunar disc and no corona registration: not a "
                                                                    "totality frame, or neither holds (" +
                                                                    str(f.get("moon_error")) + "; " +
                                                                    str(f.get("corona", {}).get("gates")) + ")"))
    on_corona = [f for f in placed if f.get("corona", {}).get("gates") in ("passed", "reference")]
    timed = all(f["time"] for f in placed) and reference["time"] is not None
    report = dict(method=None, frames=[])
    # Frame i shows canvas point p at R(theta_i) (p - C) + C + t_i: C is the reference Sun (its Moon's centre), theta_i
    # the turn of the field (zero on a mount that tracks the sky), t_i the shift.
    centre = np.asarray(analysis["centre_full"], np.float64)

    def turn(theta, v):
        c, s_ = math.cos(theta), math.sin(theta)
        v = np.asarray(v, np.float64)
        return np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]])

    def row_matrix(theta, shift):
        c, s_ = math.cos(theta), math.sin(theta)
        offset = centre + np.asarray(shift) - turn(theta, centre)
        return [[c, -s_, float(offset[0])], [s_, c, float(offset[1])]]

    if timed and len(on_corona) >= 3:
        seconds = np.array([(f["time"] - reference["time"]).total_seconds() for f in placed])
        use = np.array([f in on_corona for f in placed])
        # The turn of the field is smooth over a totality: a straight line in time through the measured turns.
        measured = np.array([f.get("corona_theta", 0.0) if f in on_corona else np.nan for f in placed])
        design = np.column_stack([np.ones(use.sum()), seconds[use]])
        spin = np.linalg.lstsq(design, measured[use], rcond=None)[0]
        spin_residual = measured[use] - design @ spin
        theta_fit = np.column_stack([np.ones(len(seconds)), seconds]) @ spin
        corona = np.array([f.get("corona_full") or [np.nan, np.nan] for f in placed], np.float64)
        moon = np.array([f["moon_full"]["xy"] for f in placed], np.float64)
        # The Moon on the canvas (the sky), from the frames the corona registered: R(-theta_i)(moon_i - C - t_i) + C.
        lunar = np.array([turn(-measured[k], moon[k] - centre - corona[k]) + centre if use[k] else [np.nan, np.nan]
                          for k in range(len(placed))])
        lunar = np.where(use[:, None], lunar, 0)
        fit = fit_lunar_motion(seconds, lunar, use)
        coef = np.array([fit["intercept"], fit["velocity_px_per_s"]])
        line = np.column_stack([np.ones(len(seconds)), seconds]) @ coef
        limit = max(3 * fit["sigma"], 0.5)
        # When the Moon and the corona disagree beyond a pixel (sigma of the line), one of them is biased and the data
        # cannot tell which. The corona is what the image is made of: each frame registered on it keeps its own
        # registration, and a frame between two of them follows the lunar track measured on its neighbours in time.
        # A frame before the first or after the last frame on the corona cannot be placed and stays out.
        local = fit["sigma"] > 1.0
        if local:
            order_t = np.argsort(seconds[use])
            known_t = seconds[use][order_t]
            known_l = lunar[use][order_t]
            line = np.column_stack([np.interp(seconds, known_t, known_l[:, 0], left=np.nan, right=np.nan),
                                    np.interp(seconds, known_t, known_l[:, 1], left=np.nan, right=np.nan)])
            limit = float("inf")
        for k, f in enumerate(placed):
            theta = float(measured[k]) if (local and use[k]) else float(theta_fit[k])
            if local and use[k]:
                shift = corona[k]
                line[k] = lunar[k]
            else:
                shift = moon[k] - centre - turn(theta, line[k] - centre)
            row = dict(file=f["name"], seconds=float(seconds[k]), exposure_s=f["exposure_s"],
                       moon_xy=f["moon_full"]["xy"], moon_r=f["moon_full"]["r"], limb_rms=f["moon_full"]["rms"],
                       corona_gates=f.get("corona", {}).get("gates"), corona_shift=f.get("corona_full"),
                       corona_theta_deg=math.degrees(measured[k]) if use[k] else None,
                       theta_deg=math.degrees(theta), shift=shift.tolist(), canvas_moon=line[k].tolist(),
                       matrix=row_matrix(theta, shift))
            if use[k]:
                row["residual_px"] = float(fit["residual_norm"][k])
                if fit["residual_norm"][k] > limit:
                    row["excluded"] = (f"the corona places it {fit['residual_norm'][k]:.2f} px off the lunar motion "
                                       f"(limit {limit:.2f} px)")
            if not np.isfinite(row["shift"]).all():
                row["excluded"] = ("outside the time span of the frames registered on the corona, while the Moon and "
                                   "the corona disagree: it cannot be placed")
            report["frames"].append(row)
        for f in by_corona:
            seconds_f = (f["time"] - reference["time"]).total_seconds() if f["time"] else 0.0
            canvas_moon = np.array([1.0, seconds_f]) @ coef
            theta = float(f.get("corona_theta", 0.0))
            report["frames"].append(dict(file=f["name"], seconds=seconds_f, exposure_s=f["exposure_s"],
                                         moon_xy=(turn(theta, canvas_moon - centre) + centre +
                                                  np.asarray(f["corona_full"])).tolist(), moon_r=None,
                                         limb_rms=None, corona_gates="passed", corona_shift=f["corona_full"],
                                         theta_deg=math.degrees(theta), shift=f["corona_full"],
                                         canvas_moon=canvas_moon.tolist(), matrix=row_matrix(theta, f["corona_full"]),
                                         placed="by the corona: its Moon cannot be measured"))
        speed = float(np.hypot(*fit["velocity_px_per_s"]))
        report.update(method=("the corona registration of each frame, and for the others their lunar limb minus the "
                              "lunar track measured on their neighbours in time (the Moon and the corona disagree by "
                              f"{fit['sigma']:.1f} px on a straight lunar motion)") if local else
                      "lunar limb of each frame, minus the lunar motion fitted on the corona registration",
                      lunar_velocity_px_per_s=fit["velocity_px_per_s"], lunar_speed_px_per_s=speed,
                      residual_sigma_px=fit["sigma"], frames_on_corona=int(use.sum()),
                      frames_in_fit=int(fit["used"].sum()), limit_px=limit,
                      field_turn_deg_per_min=math.degrees(spin[1]) * 60,
                      field_turn_residual_deg=float(np.degrees(np.sqrt(np.mean(spin_residual ** 2)))))
        span = [float(seconds.min()), float(seconds.max())]
        middle = 0.5 * (span[0] + span[1])
        sun = (np.asarray(fit["intercept"]) + np.asarray(fit["velocity_px_per_s"]) * middle).tolist()
        report["sun"] = dict(xy=sun, how=f"the Moon's centre at the middle of the frames ({middle:+.1f} s from the "
                                          f"reference), on the fitted lunar motion: the Sun's centre when the frames "
                                          f"span the totality symmetrically and the site is on the central line")
    else:
        why = "the frames carry no capture time" if not timed else f"only {len(on_corona)} frames registered on the corona"
        for f in by_corona + [f for f in placed if f in on_corona]:
            theta = float(f.get("corona_theta", 0.0))
            shift = np.asarray(f["corona_full"])
            moon_xy = (f["moon_full"]["xy"] if f.get("moon_full") else
                       (turn(theta, np.asarray(reference["moon_full"]["xy"]) - centre) + centre + shift).tolist())
            report["frames"].append(dict(file=f["name"], exposure_s=f["exposure_s"], corona_gates="passed",
                                         moon_xy=moon_xy, moon_r=f["moon_full"]["r"] if f.get("moon_full") else None,
                                         corona_shift=f["corona_full"], theta_deg=math.degrees(theta),
                                         shift=shift.tolist(),
                                         canvas_moon=(turn(-theta, np.asarray(moon_xy) - centre - shift) + centre).tolist(),
                                         matrix=row_matrix(theta, shift),
                                         placed=None if f.get("moon_full") else "by the corona: its Moon cannot be measured"))
        for f in placed:
            if f not in on_corona:
                report["frames"].append(dict(file=f["name"], exposure_s=f["exposure_s"], moon_xy=f["moon_full"]["xy"],
                                             moon_r=f["moon_full"]["r"], corona_gates=f.get("corona", {}).get("gates"),
                                             excluded="not registered on the corona: " +
                                                      str(f.get("corona", {}).get("gates"))))
        report.update(method=f"registration on the corona only ({why})")
        report["sun"] = dict(xy=list(reference["moon_full"]["xy"]),
                             how="the Moon's centre of the reference frame (no lunar motion could be fitted)")
    # A mount re-pointed during the totality leaves photos that cover another part of the sky: where their edges
    # cross the image, the number of photos changes and so does the noise, and the filters draw that edge. Only the
    # pointing of the reference frame is stacked: a jump of more than 2 % of the sensor's diagonal between photos
    # taken one after the other starts another pointing (a drift during the totality does not).
    placed_rows = sorted([row for row in report["frames"] if not row.get("excluded")],
                         key=lambda row: row.get("seconds", 0.0))
    jump_limit = 0.02 * math.hypot(*analysis["shape"])
    pointing, group = {}, 0
    for k, row in enumerate(placed_rows):
        if k and float(np.hypot(*(np.asarray(row["shift"]) - np.asarray(placed_rows[k - 1]["shift"])))) > jump_limit:
            group += 1
        pointing[row["file"]] = group
    if group:
        mine = pointing[reference["name"]]
        for row in placed_rows:
            if pointing[row["file"]] != mine:
                moved = float(np.hypot(*(np.asarray(row["shift"]) - np.asarray(
                    next(r for r in placed_rows if r["file"] == reference["name"])["shift"]))))
                row["excluded"] = (f"another pointing of the mount ({moved:.0f} px from the reference's): one pointing "
                                   "is stacked, so that no edge of a photo crosses the image")
        report["pointings"] = group + 1
    for row in report["frames"]:
        if row.get("excluded"):
            analysis["excluded"].append(dict(file=row["file"], reason=row["excluded"]))
    report["used"] = [row for row in report["frames"] if not row.get("excluded")]
    if not report["used"]:
        raise RuntimeError("No frame could be placed on the Sun")
    radii = [row["moon_r"] for row in report["used"] if row.get("moon_r")]
    ratio, ratio_note = eclipse_ratio(reference["time"])
    moon_radius = float(np.median(radii))
    for row in report["used"]:
        if not row.get("moon_r"):
            row["moon_r"] = moon_radius
    report["moon_radius_px"] = moon_radius
    if ratio:
        report["sun"].update(radius_px=moon_radius / ratio, radius_how=f"lunar radius {moon_radius:.1f} px over "
                             f"{ratio} ({ratio_note})")
    else:
        report["sun"].update(radius_px=moon_radius, radius_how=f"the lunar radius ({ratio_note}): the Sun is up to "
                                                               "8 % smaller")
    return report


def measure_photometry(analysis: dict, decision: dict, progress=Progress(None)) -> dict:
    """One photometric gain per placed frame, measured where the frames share good data on the canvas, through each
    frame's final placement. A frame whose light does not follow the others at all (a gain beyond 2x, or more than
    20 % scatter left around the common corona) carries light that is not the corona's: sunlight scattered near a
    contact, or a cloud. It stays out, and the gains are fitted again without it."""
    lv = analysis["levels"]
    by_name = {f["name"]: f for f in analysis["lights"]}
    flat = np.load(analysis["flat"]) if analysis.get("flat") else None
    centre = np.asarray(decision["sun"]["xy"], np.float64)
    radius = float(decision["sun"]["radius_px"])
    rows = decision["used"]
    for n, row in enumerate(rows):
        progress("Measuring the light of each photo", n + 1, len(rows), row["file"])
        f = by_name[row["file"]]
        green, saturated, _ = green_half(Path(f["path"]), lv, analysis["dark_for"].get(f["exposure_s"]), flat)
        moon = dict(xy=[(v - 0.5) / 2 for v in row["moon_xy"]], r=row["moon_r"] / 2)
        row["grid"] = photometry_grid(green, saturated, moon, f["exposure_s"], row["matrix"], centre, radius, lv)
    reference = analysis["reference"]["name"]
    kept = list(rows)
    for _ in range(3):
        names = [row["file"] for row in kept]
        solved = solve_gains([row["grid"] for row in kept], names.index(reference) if reference in names else 0)
        odd = [(row, g, r) for row, g, r in zip(kept, solved["gains"], solved.get("residual_per_frame") or [])
               if row["file"] != reference and (not 0.5 <= g <= 2.0 or (r is not None and r > 0.2))]
        if not odd:
            break
        for row, g, r in odd:
            row["excluded"] = (f"its light does not follow the other frames (gain {g:.2f}, scatter "
                               f"{100 * (r or 0):.0f} %): sunlight scattered near a contact, or a cloud")
            analysis["excluded"].append(dict(file=row["file"], reason=row["excluded"]))
            kept.remove(row)
    # The gains go to the stack only when the sky changed during the totality (thin clouds or haze: frames more than
    # 3 % apart once their gains are fitted): there they remove the steps where each exposure saturates. Under a clear
    # sky the nominal exposure times are kept: the gain fit then carries more of its own bias (the blur of the inner
    # corona, the faint sky of the long exposures) than the shutter carries error.
    cloudy = solved.get("residual") is not None and solved["residual"] > 0.03
    for row, gain in zip(kept, solved["gains"]):
        row["gain_measured"] = gain
        row["gain"] = gain if cloudy else 1.0
    for row in rows:
        row.pop("grid", None)
    decision["used"] = kept
    photometry = {k: v for k, v in solved.items() if k not in ("gains", "residual_per_frame")}
    photometry["frames_without_overlap"] = [kept[n]["file"] for n in solved["frames_without_overlap"]]
    photometry["residual_per_frame"] = {kept[n]["file"]: v for n, v in enumerate(solved.get("residual_per_frame") or [])}
    photometry["gains"] = {row["file"]: row["gain_measured"] for row in kept}
    photometry["gains_applied"] = cloudy
    return photometry


# --- colour, stack, filters, PSB ------------------------------------------------------------------------------
# sRGB (D65) primaries in XYZ, as LibRaw and dcraw use them.
XYZ_FROM_SRGB = np.array([[0.412453, 0.357580, 0.180423],
                          [0.212671, 0.715160, 0.072169],
                          [0.019334, 0.119193, 0.950227]])


def daylight_colour(path: Path) -> dict | None:
    """The camera's daylight white balance and its camera-to-sRGB matrix, from the colour matrix LibRaw holds for the
    camera (Adobe's), as dcraw derives them: the corona keeps the colour a camera set to daylight records. A low Sun
    stays golden; nothing is neutralised."""
    import rawpy

    with rawpy.imread(str(path)) as raw:
        cam_xyz = np.asarray(raw.rgb_xyz_matrix, np.float64)[:3]
        desc = raw.color_desc.decode()
    if desc[:3] != "RGB" or not np.isfinite(cam_xyz).all() or not np.any(cam_xyz):
        return None
    cam_rgb = cam_xyz @ XYZ_FROM_SRGB
    rows = cam_rgb.sum(axis=1)
    if (rows <= 0).any():
        return None
    cam_rgb /= rows[:, None]
    balance = (1.0 / rows) / (1.0 / rows[1])
    matrix = np.linalg.inv(cam_rgb)
    return dict(white_balance=balance.tolist(), camera_to_linear_rgb=matrix.tolist(),
                how="daylight white balance and camera-to-sRGB matrix derived from LibRaw's colour matrix for the "
                    "camera (as dcraw does); profile sRGB")


def display_scale(linear: np.ndarray, valid: np.ndarray, coverage: np.ndarray, geometry: EclipseGeometry,
                  colour: dict | None) -> float:
    """The connector's display scale (median luminance of the corona between 1.1 and 2 solar radii), measured on the
    colours that will be displayed."""
    rgb = linear
    if colour:
        rgb = (linear * np.asarray(colour["white_balance"], np.float32)) @ np.asarray(colour["camera_to_linear_rgb"], np.float32).T
    lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4
    r = geometry.rsun_map()
    use = valid & (coverage >= 0.5) & np.isfinite(lum) & (lum > 0) & (r >= 1.1) & (r <= 2.0)
    if geometry.moon_xy is not None:
        use &= ~geometry.moon_mask(2)
    if not use.any():
        use = valid & np.isfinite(lum) & (lum > 0) & (r > 1.0)
    if not use.any():
        raise RuntimeError("No observed corona to set the display brightness")
    return float(np.median(lum[use]))


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROGRAMS = {"photoshop": "Photoshop", "pixinsight": "PixInsight"}


def run_auto(cfg: dict) -> dict:
    """The whole workflow: analyse, decide, stack, filter, and write into ``cfg['out']`` what ``cfg['program']``
    opens: a layered PSB for Photoshop (the default), the layer images and their PixelMath expressions for
    PixInsight. Everything before the filter layers is the same for both."""
    from ael import develop, io
    from ael.filterbank import DEFAULTS
    from PIL import ImageCms

    program = cfg.get("program", "photoshop")
    if program not in PROGRAMS:
        raise ValueError(f"Unknown program {program!r}: one of {sorted(PROGRAMS)}")
    name = PROGRAMS[program]
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"The output folder is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    progress = Progress(Path(cfg["progress"]) if cfg.get("progress") else None,
                        Path(cfg["cancel"]) if cfg.get("cancel") else None, name)
    clock = {"start": time.time()}
    work = Path(tempfile.mkdtemp(prefix=f"AEL_{name}_", dir=cfg.get("work_parent")))
    kept_work = False
    try:
        analysis = analyse(cfg.get("raw") or [], cfg.get("calibration") or [], work / "calibration", progress)
        clock["analysed"] = time.time()
        decision = decide(analysis)
        analysis["photometry"] = measure_photometry(analysis, decision, progress)
        lv, reference = analysis["levels"], analysis["reference"]
        by_name = {f["name"]: f for f in analysis["lights"]}
        dark_for = {d["exposure_s"]: d["path"] for d in analysis["calibration"]["darks"]}
        flat_path = analysis["calibration"]["flat"]["path"] if analysis["calibration"]["flat"] else None
        rows = sorted(decision["used"], key=lambda row: (row["file"] != reference["name"], row.get("seconds", 0)))
        if rows[0]["file"] != reference["name"]:
            raise RuntimeError("The reference frame was left out of the stack")
        frames = []
        for row in rows:
            f = by_name[row["file"]]
            frame = {"path": f["path"], "kind": "raw", "iso": f["iso"], "exposure_s": f["exposure_s"],
                     "black": lv["black"], "white": lv["white"], "linearity_fraction": lv["linearity_fraction"],
                     "reference_to_input": row["matrix"],
                     "moon_xy": row["moon_xy"], "moon_radius_px": row["moon_r"], "train": "one",
                     "flux_scale": float(row.get("gain", 1.0))}
            if dark_for.get(f["exposure_s"]):
                frame["dark"] = dark_for[f["exposure_s"]]
            if flat_path:
                frame["flat"] = flat_path
            frames.append(frame)
        # The Moon on the canvas: frame i's Moon sits at moon_i - shift_i. The filters leave out the band that the Moon
        # sweeps across the corona during the frames (it mixes frames there): a disc that covers every position.
        canvas_moons = np.array([row["canvas_moon"] for row in rows])
        moon_r = decision["moon_radius_px"]
        far = max((float(np.hypot(*(a - b))) for a in canvas_moons for b in canvas_moons), default=0.0)
        pair = max(((a, b) for a in canvas_moons for b in canvas_moons), key=lambda ab: float(np.hypot(*(ab[0] - ab[1]))))
        swept_xy = ((pair[0] + pair[1]) / 2).tolist()
        shape = tuple(analysis["shape"])
        date = reference["time"].strftime("%Y-%m-%d") if reference["time"] else "unknown date"
        note = (f"Measured on the RAW files by the AEL {name} connector. Sun: {decision['sun']['how']}; radius: "
                f"{decision['sun']['radius_how']}. North unknown (position angles from the top of the image), parity "
                f"not mirrored, plate scale unknown.")
        stack_geometry = EclipseGeometry(shape=shape, sun_xy=tuple(decision["sun"]["xy"]),
                                         sun_radius_px=float(decision["sun"]["radius_px"]),
                                         moon_xy=tuple(canvas_moons[0]), moon_radius_px=moon_r, note=note)
        # Two exposures never agree exactly where the longer one saturates (shutter times, the sky changing, the
        # blur of the inner corona), and an abrupt hand-over leaves a step that the filters draw as a ring. Each
        # photo's weight therefore fades over the top half of its range, not the top fifth: the hand-over spreads over
        # about 15 % of the radius, and the shorter exposure covers what the longer one gives up.
        photometry = analysis["photometry"]
        cloudy = photometry.get("residual") is not None and photometry["residual"] > 0.03
        taper = 0.5
        recipe = {"geometry": json.loads(stack_geometry.to_json()), "frames": frames,
                  "stack": {"canvas": "reference", "taper_start": taper, "moon_guard_px": 2, "limb_fade_px": 4,
                            "band_sigma_px": 0, "hot_pixels": {"enabled": False}},
                  "note": f"AEL {name} connector: every value measured on the files (see the connector's receipt)"}
        recipe_path = work / "stack_recipe.json"
        recipe_path.write_text(json.dumps(recipe, indent=1, ensure_ascii=False), encoding="utf-8")
        total = len(frames)

        def stack_progress(message):
            text = str(message)
            if text.startswith("stack ") and "/" in text:
                done = int(text.split()[1].split("/")[0])
                progress("Stacking", done, total, text.split(": ", 1)[-1])
        progress("Stacking", 0, total)
        stacked = stack.stack_from_config(recipe_path, work / "stack", progress=stack_progress)
        stack_receipt = json.loads(Path(stacked["receipt"]).read_text())
        if not all(stack_receipt["gates"].get(k) for k in ("observed_support", "nothing_outside_data")):
            raise RuntimeError(f"AEL stack gate failed: {stack_receipt['gates']}")
        clock["stacked"] = time.time()

        # Filters: AEL's default layers over the display base, in the colours of the camera set to daylight.
        progress("Filters", 0, len(DEFAULTS))
        filter_geometry = EclipseGeometry.from_json(stacked["files"]["geometry"])
        filter_geometry = EclipseGeometry(shape=filter_geometry.shape, sun_xy=filter_geometry.sun_xy,
                                          sun_radius_px=filter_geometry.sun_radius_px, moon_xy=tuple(swept_xy),
                                          moon_radius_px=moon_r + far / 2 + 1.0, north_deg=0.0, mirrored=False,
                                          note=note + f" Lunar disc for the filters: every position of the Moon during "
                                                      f"the frames ({far:.1f} px of motion), so that the band the Moon "
                                                      f"swept enters no filter.")
        filter_geometry_path = work / "geometry_filters.json"
        filter_geometry.to_json(filter_geometry_path)
        colour = daylight_colour(Path(reference["path"]))
        linear = np.load(stacked["files"]["linear"])
        scale = display_scale(linear, np.load(stacked["files"]["valid"]), np.load(stacked["files"]["coverage"]),
                              filter_geometry, colour)
        del linear
        model = reference.get("model") or analysis["camera"]
        stem = f"Eclipse {date} {model}".replace("/", "-").replace(":", "-").strip()
        linear_tif = out / f"{stem} linear master.tif"
        preview = out / f"{stem} preview.png"
        details = out / "details"
        layers_cfg = {"input": stacked["files"]["linear"], "geometry": str(filter_geometry_path),
                      "valid": stacked["files"]["valid"], "coverage": stacked["files"]["coverage"],
                      "min_coverage": 0.5, "alpha": stacked["files"]["alpha"],
                      "filters": list(DEFAULTS), "visible": list(DEFAULTS),
                      "display": {"scale": scale, "asinh": 20, "highlight_ceiling": 0.9},
                      "note": f"AEL {name} connector: AEL's default filter layers over the display base"}
        if colour:
            layers_cfg.update(white_balance=colour["white_balance"], camera_to_linear_rgb=colour["camera_to_linear_rgb"])
        if program == "photoshop":
            icc_path = work / "sRGB.icc"
            icc_path.write_bytes(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
            filters_recipe = dict(layers_cfg, photoshop=True, icc=str(icc_path))
            filters_recipe_path = work / "filters_recipe.json"
            filters_recipe_path.write_text(json.dumps(filters_recipe, indent=1, ensure_ascii=False), encoding="utf-8")

            def filter_progress(message):
                text = str(message)
                if text.startswith("filter ") and "/" in text:
                    done = int(text.split()[1].split("/")[0])
                    progress("Filters", done, len(DEFAULTS), text.split(": ", 1)[-1])
            product = develop.filters_from_config(filters_recipe_path, work / "filters", progress=filter_progress)
            filters_receipt_path = Path(product["receipt"])
            filters_receipt = json.loads(filters_receipt_path.read_text())
            gates = filters_receipt["gates"]
            if not gates.get("nothing_outside_data") or not gates.get("photoshop_roundtrip", {}).get("ok"):
                raise RuntimeError(f"AEL filter gate failed: {gates}")
            preview_source = product["files"]["preview"]
            pixelmath, images = None, None
        else:
            # The same layers as images, and the PixelMath expressions that compose them over the display base, as
            # the connector's filter operation makes them (ael_workflow.run_filters): PixInsight opens them as views.
            from ael_workflow import run_filters
            filters_dir = work / "filters"
            layered = run_filters(dict(layers_cfg, out=str(filters_dir)))
            filters_receipt_path = Path(json.loads(Path(layered["receipt"]).read_text())["ael_receipt"])
            filters_receipt = json.loads(filters_receipt_path.read_text())
            gates = filters_receipt["gates"]
            preview_source = filters_receipt_path.parent / "preview.png"
            pixelmath = layered["pixelmath"]
            shutil.move(str(filters_dir / "tiff"), str(out / "layers"))
            shutil.move(str(filters_dir / "PIXELMATH.md"), str(out / "PIXELMATH.md"))
            images = [{"name": "linear", "kind": "linear", "path": str(linear_tif), "view": "AEL_LINEAR_MASTER"}]
            images += [dict(image, path=str(out / "layers" / Path(image["path"]).name)) for image in layered["images"]]
        clock["filtered"] = time.time()

        # What the user keeps: the layered image, the linear master, a preview and the receipts. The rest was temporary.
        progress("Saving", 0, 1)
        shutil.move(stacked["files"]["tiff"], linear_tif)
        shutil.move(str(preview_source), preview)
        details.mkdir()
        for source, detail in ((recipe_path, "stack_recipe.json"), (Path(stacked["receipt"]), "stack_receipt.json"),
                               (filters_receipt_path, "filters_receipt.json"), (filter_geometry_path, "geometry.json")):
            shutil.copy2(source, details / detail)
        layers = [{"name": "Background", "mode": "normal", "opacity": 1.0, "visible": True},
                  {"name": "Linear reference / receipt scale", "mode": "normal", "opacity": 1.0, "visible": False},
                  {"name": "00 Display base", "mode": "normal", "opacity": 1.0, "visible": True}]
        layers += [{"name": entry["layer"], "mode": entry["mode"], "opacity": float(entry["opacity"]),
                    "visible": bool(entry["visible"])} for entry in filters_receipt["parameters"]["layers"]]
        outputs = {"linear_master": dict(path=str(linear_tif), sha256=_sha256(linear_tif)),
                   "preview": dict(path=str(preview), sha256=_sha256(preview))}
        if program == "photoshop":
            psb = out / f"{stem} AEL.psb"
            shutil.move(product["files"]["psb"], psb)
            outputs["psb"] = dict(path=str(psb), sha256=_sha256(psb))
        else:
            outputs["layers"] = [dict(path=image["path"], sha256=_sha256(Path(image["path"])))
                                 for image in images[1:]]
            outputs["pixelmath"] = dict(path=str(out / "PIXELMATH.md"), operations=pixelmath)
        used = decision["used"]
        summary = dict(camera=analysis["camera"], date=date, iso=analysis["iso"], frames_stacked=len(used),
                       sky_consistency=photometry.get("residual"), cloudy=cloudy,
                       frames_chosen=len([f for f in analysis["files"].values() if f["chosen_as"] == "light"]),
                       exposures=sorted({row["exposure_s"] for row in used}),
                       darks=len(analysis["calibration"]["darks"]),
                       flat=bool(analysis["calibration"]["flat"]), left_out=len(analysis["excluded"]))
        receipt = {"product": f"AEL {name} connector: RAW files to " +
                              ("a layered PSB" if program == "photoshop" else "filter layers and a PixelMath composite"),
                   "credit": CREDIT, "runtime": runtime(), "program": name, "summary": summary,
                   "files": [{k: (str(v) if k == "time" else v) for k, v in f.items()} for f in analysis["files"].values()],
                   "left_out": analysis["excluded"], "levels": lv, "calibration": analysis["calibration"],
                   "reference": reference["name"], "band_sigma_half_px": analysis["sigma_half_px"],
                   "registration": decision, "photometry": dict(photometry, taper_start=taper),
                   "colour": colour or "camera colour matrix unknown: sensor RGB",
                   "display_scale": scale, "stack_gates": stack_receipt["gates"], "filters_gates": gates,
                   "layers": layers, "outputs": outputs,
                   "assumed": [decision["sun"]["how"], decision["sun"]["radius_how"],
                               "north unknown: position angles from the top of the image; plate scale unknown",
                               f"the top {100 - round(100 * LINEARITY_FRACTION)} % of each RAW range is not used "
                               "(sensors stop being linear before they clip); shorter exposures cover it",
                               "temporary files (calibration masters, stack and filter arrays) deleted at the end"],
                   "timings_s": {k: round(v - clock["start"], 1) for k, v in clock.items() if k != "start"}}
        receipt_path = out / "AEL receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        progress("Done", 1, 1)
        answer = {"ok": True, "operation": "raw", "program": name, "out": str(out), "linear_master": str(linear_tif),
                  "preview": str(preview), "receipt": str(receipt_path), "summary": summary, "left_out": analysis["excluded"]}
        if program == "photoshop":
            answer.update(psb=outputs["psb"]["path"], psb_layers=layers)
        else:
            answer.update(images=images, pixelmath=pixelmath, gates=gates, geometry_source="measured on the RAW files",
                          geometry=json.loads(filter_geometry_path.read_text(encoding="utf-8")))
        return answer
    except Exception:
        kept_work = bool(cfg.get("keep_work_on_error"))
        raise
    finally:
        if not kept_work:
            shutil.rmtree(work, ignore_errors=True)
