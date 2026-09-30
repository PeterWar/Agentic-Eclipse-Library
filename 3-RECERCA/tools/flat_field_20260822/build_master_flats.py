#!/usr/bin/env python3
"""Construeix màsters flat CFA lineals i auditables dels flats del 22-08-2026.

El programa no toca cap RAW ni cap màster vigent. Escriu en un directori de
staging nou i només el promociona al final. Els productes se separen perquè
tenen autoritats diferents:

* FULL: flat de sessió complet; és diagnòstic fins que es provi la transferència.
* OPTICAL_RADIAL: component radial, invariant a una rotació del cos.
* OPTICAL_EVEN180: camp suau parell a 180 graus; elimina el gradient lineal.
* OPTICAL_SMOOTH2D: camp 2-D suau, però pot conservar gradient de cel.
* FINE_SENSOR: PRNU de gra fi, sense la baixa freqüència ni defectes grossos.

Tot es calcula abans del debayer, sense WB, denoise ni clipping fotomètric.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rawpy
from astropy.io import fits
from PIL import Image, ImageDraw
from scipy import ndimage as ndi


PLANE_NAMES = ("R", "G1", "G2", "B")
PLANE_OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))
CLIP_SIGMA = 5.5
COARSE_FACTOR = 8
OPTICAL_SIGMA_PLANE_PX = 25.0
FINE_SIGMA_PLANE_PX = 2.0
EXIFTOOL = Path("/opt/homebrew/bin/exiftool")


@dataclass(frozen=True)
class Train:
    key: str
    source: Path
    suffix: str
    prefix: str
    first: int
    last: int
    model: str
    internal_serial: str
    lens: str | None
    black: tuple[float, float, float, float]
    saturation_raw: float
    raw_shape: tuple[int, int]
    crop: tuple[int, int, int, int] | None
    expected_exposures: tuple[float, ...]


TRAINS = {
    "vixen": Train(
        key="vixen_r6iii",
        source=Path("/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Flats R6III"),
        suffix="CR3",
        prefix="572A",
        first=7121,
        last=7245,
        model="Canon EOS R6 Mark III",
        internal_serial="[SÈRIE]",
        lens=None,
        # LibRaw publica [0, 32, 96, 64] per aquests CR3, però és fals. La
        # reixa S6 i els darks mesuren un pedestal físic de 511,5 ADU.
        black=(511.5, 511.5, 511.5, 511.5),
        saturation_raw=13995.0,
        raw_shape=(4640, 6960),
        # Mateixa reixa que apila_hdr4_vixen.py i els S6: y=108, x=172.
        crop=(108, 172, 4640, 6960),
        expected_exposures=(1 / 320, 1 / 100, 1 / 40, 1 / 25),
    ),
    "sony": Train(
        key="sony_a7r3a_300mm",
        source=Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA/Flats Sony A7RIIIA 300mm"),
        suffix="ARW",
        prefix="DSC",
        first=67,
        last=119,
        model="ILCE-7RM3A",
        internal_serial="[SÈRIE]",
        lens="FE 300mm F2.8 GM OSS",
        black=(512.0, 512.0, 512.0, 512.0),
        saturation_raw=0.90 * 16383.0,
        raw_shape=(5320, 7968),
        crop=None,
        expected_exposures=(1 / 200,),
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def expected_paths(train: Train) -> list[Path]:
    width = 4 if train.prefix == "572A" else 5
    expected = [train.source / f"{train.prefix}{n:0{width}d}.{train.suffix}"
                for n in range(train.first, train.last + 1)]
    actual = sorted(train.source.glob(f"*.{train.suffix}"))
    if actual != expected:
        missing = [str(p) for p in expected if not p.exists()]
        extra = [str(p) for p in actual if p not in set(expected)]
        raise RuntimeError(f"inventari inesperat; missing={missing}, extra={extra}")
    return expected


def exif_records(paths: list[Path]) -> list[dict[str, Any]]:
    cmd = [
        str(EXIFTOOL), "-json", "-G1", "-s",
        "-Model", "-SerialNumber", "-InternalSerialNumber", "-ISO",
        "-ExposureTime", "-LensModel", "-FocalLength", "-FNumber",
        "-DateTimeOriginal", "-OffsetTimeOriginal", "-CameraTemperature",
        "-ImageWidth", "-ImageHeight", "-Compression",
        *map(str, paths),
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    records = json.loads(proc.stdout)
    if len(records) != len(paths):
        raise RuntimeError(f"ExifTool ha retornat {len(records)} registres per {len(paths)} fitxers")
    return records


def parse_fraction(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().split()[0]
    if "/" in text:
        a, b = text.split("/", 1)
        return float(a) / float(b)
    return float(text)


def validate_exif(train: Train, paths: list[Path], records: list[dict[str, Any]]) -> None:
    for path, rec in zip(paths, records, strict=True):
        if Path(rec["SourceFile"]) != path:
            raise RuntimeError(f"ordre EXIF divergent: {rec['SourceFile']} != {path}")
        if rec.get("IFD0:Model") != train.model:
            raise RuntimeError(f"model divergent a {path}: {rec.get('IFD0:Model')}")
        serial = rec.get("Canon:InternalSerialNumber") or rec.get("Sony:InternalSerialNumber")
        if str(serial) != train.internal_serial:
            raise RuntimeError(f"sèrie interna divergent a {path}: {serial}")
        if int(rec.get("ExifIFD:ISO", -1)) != 100:
            raise RuntimeError(f"ISO divergent a {path}: {rec.get('ExifIFD:ISO')}")
        exp = parse_fraction(rec.get("ExifIFD:ExposureTime"))
        if not any(math.isclose(exp, x, rel_tol=0.015) for x in train.expected_exposures):
            raise RuntimeError(f"exposició divergent a {path}: {exp}")
        if train.lens is not None and rec.get("ExifIFD:LensModel") != train.lens:
            raise RuntimeError(f"objectiu divergent a {path}: {rec.get('ExifIFD:LensModel')}")


def central_annulus(shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    yy, xx = np.ogrid[:h, :w]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    r2 = (yy - cy) ** 2 + (xx - cx) ** 2
    scale = min(h, w)
    return (r2 >= (0.05 * scale) ** 2) & (r2 <= (0.18 * scale) ** 2)


def load_planes(path: Path, train: Train) -> tuple[np.ndarray, tuple[float, ...]]:
    with rawpy.imread(str(path)) as raw:
        if not np.array_equal(raw.raw_pattern, np.array([[0, 1], [3, 2]], dtype=np.uint8)):
            raise RuntimeError(f"CFA no RGGB a {path}: {raw.raw_pattern}")
        if train.crop is None:
            mosaic = raw.raw_image_visible
        else:
            y0, x0, h, w = train.crop
            mosaic = raw.raw_image[y0:y0 + h, x0:x0 + w]
        if tuple(mosaic.shape) != train.raw_shape:
            raise RuntimeError(f"reixa divergent a {path}: {mosaic.shape} != {train.raw_shape}")
        planes = np.empty((4, mosaic.shape[0] // 2, mosaic.shape[1] // 2), np.float32)
        sat = []
        for c, ((oy, ox), black) in enumerate(zip(PLANE_OFFSETS, train.black, strict=True)):
            raw_plane = mosaic[oy::2, ox::2]
            sat.append(float(np.count_nonzero(raw_plane >= train.saturation_raw) / raw_plane.size))
            np.subtract(raw_plane, black, out=planes[c], dtype=np.float32)
    return planes, tuple(sat)


def downsample_mean(array: np.ndarray, factor: int = COARSE_FACTOR) -> np.ndarray:
    h = (array.shape[-2] // factor) * factor
    w = (array.shape[-1] // factor) * factor
    return array[..., :h, :w].reshape(
        *array.shape[:-2], h // factor, factor, w // factor, factor
    ).mean(axis=(-3, -1), dtype=np.float32)


def normalize_factor(planes: np.ndarray, annulus: np.ndarray) -> tuple[np.ndarray, list[float]]:
    out = planes.astype(np.float32, copy=True)
    scales = []
    for c in range(4):
        scale = float(np.median(out[c][annulus]))
        if not np.isfinite(scale) or scale <= 0:
            raise RuntimeError(f"normalització invàlida al pla {PLANE_NAMES[c]}: {scale}")
        out[c] /= scale
        scales.append(scale)
    return out, scales


def radialize_log(log_even: np.ndarray) -> np.ndarray:
    _, h, w = log_even.shape
    yy, xx = np.ogrid[:h, :w]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    rbin = np.rint(np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)).astype(np.uint16)
    nbin = int(rbin.max()) + 1
    count = np.bincount(rbin.ravel(), minlength=nbin).astype(np.float64)
    result = np.empty_like(log_even)
    for c in range(4):
        total = np.bincount(rbin.ravel(), weights=log_even[c].ravel(), minlength=nbin)
        profile = total / np.maximum(count, 1.0)
        profile = ndi.gaussian_filter1d(profile, sigma=8.0, mode="nearest")
        result[c] = profile[rbin]
    return result


def split_correlation(a: np.ndarray, b: np.ndarray, border: int = 24) -> tuple[float, int]:
    aa = a[border:-border, border:-border].ravel()
    bb = b[border:-border, border:-border].ravel()
    good = np.isfinite(aa) & np.isfinite(bb) & (np.abs(aa) < 0.08) & (np.abs(bb) < 0.08)
    if good.sum() < 1000:
        return 0.0, int(good.sum())
    # Mostreig determinista per evitar una còpia gegant i perquè n>>1e6 no
    # canvia materialment la correlació.
    idx = np.flatnonzero(good)[::max(1, int(good.sum()) // 1_500_000)]
    return float(np.corrcoef(aa[idx], bb[idx])[0, 1]), int(good.sum())


def sample_stats(array: np.ndarray, stride: int = 8) -> dict[str, Any]:
    sample = array[:, ::stride, ::stride]
    return {
        "min": sample.reshape(4, -1).min(1).astype(float).tolist(),
        "median": np.median(sample.reshape(4, -1), axis=1).astype(float).tolist(),
        "max": sample.reshape(4, -1).max(1).astype(float).tolist(),
        "p01": np.percentile(sample.reshape(4, -1), 1, axis=1).astype(float).tolist(),
        "p99": np.percentile(sample.reshape(4, -1), 99, axis=1).astype(float).tolist(),
    }


def metric_abs_percent(array: np.ndarray, stride: int = 8) -> dict[str, float]:
    a = np.abs(array[:, ::stride, ::stride].ravel()) * 100.0
    return {
        "median_percent": float(np.median(a)),
        "p95_percent": float(np.percentile(a, 95)),
        "p99_percent": float(np.percentile(a, 99)),
        "max_percent": float(np.max(a)),
        "rms_percent": float(np.sqrt(np.mean(a * a))),
    }


def to_mosaic(cfa4: np.ndarray) -> np.ndarray:
    _, h, w = cfa4.shape
    mosaic = np.empty((2 * h, 2 * w), np.float32)
    for c, (oy, ox) in enumerate(PLANE_OFFSETS):
        mosaic[oy::2, ox::2] = cfa4[c]
    return mosaic


def write_fits(path: Path, cfa4: np.ndarray, train: Train, caltype: str, nframes: int) -> None:
    mosaic = to_mosaic(cfa4)
    header = fits.Header()
    header["BUNIT"] = "DIMENSIONLESS"
    header["CALTYPE"] = caltype
    header["BAYERPAT"] = "RGGB"
    header["PLANES"] = "R,G1,G2,B"
    header["TRAIN"] = train.key
    header["NFRAMES"] = nframes
    header["POSTECL"] = True
    header["BLACK"] = float(train.black[0])
    header.add_history("Linear CFA master; no debayer, WB, denoise or photometric clipping.")
    header.add_history("Built from posterior twilight flats captured 2026-08-22.")
    fits.PrimaryHDU(data=mosaic, header=header).writeto(path, overwrite=False, checksum=True)


def make_preview(path: Path, full: np.ndarray, radial: np.ndarray,
                 smooth2d: np.ndarray, fine_log: np.ndarray) -> None:
    green_full = 0.5 * (full[1] + full[2])
    green_radial = 0.5 * (radial[1] + radial[2])
    green_smooth = 0.5 * (smooth2d[1] + smooth2d[2])
    asym = 0.5 * np.log(np.clip(green_full, 1e-6, None) /
                        np.clip(green_full[::-1, ::-1], 1e-6, None))
    green_fine = 0.5 * (fine_log[1] + fine_log[2])

    def panel(data: np.ndarray, lo: float, hi: float, label: str) -> Image.Image:
        scaled = np.clip((data - lo) / (hi - lo), 0, 1)
        im = Image.fromarray((scaled * 255).astype(np.uint8), mode="L")
        im.thumbnail((900, 600), Image.Resampling.LANCZOS)
        rgb = Image.merge("RGB", (im, im, im))
        ImageDraw.Draw(rgb).rectangle((0, 0, 420, 34), fill=(0, 0, 0))
        ImageDraw.Draw(rgb).text((10, 9), label, fill=(255, 255, 255))
        return rgb

    panels = [
        panel(green_full, 0.28, 1.08, "FULL sessio (verd)"),
        panel(green_radial, 0.28, 1.08, "OPTICAL radial"),
        panel(green_smooth, 0.28, 1.08, "OPTICAL 2-D suau"),
        panel(asym, -0.05, 0.05, "Asimetria log +/-5%"),
        panel(green_fine, -0.03, 0.03, "PRNU fi log +/-3%"),
    ]
    w = max(p.width for p in panels)
    h = max(p.height for p in panels)
    canvas = Image.new("RGB", (w * 3, h * 2), (20, 20, 20))
    for i, p in enumerate(panels):
        canvas.paste(p, ((i % 3) * w, (i // 3) * h))
    canvas.save(path)


def build(train: Train, destination: Path, workers: int) -> dict[str, Any]:
    if destination.exists():
        raise RuntimeError(f"la destinació ja existeix: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.staging-{os.getpid()}"
    if staging.exists():
        raise RuntimeError(f"staging preexistent: {staging}")
    staging.mkdir()

    paths = expected_paths(train)
    records = exif_records(paths)
    validate_exif(train, paths, records)
    print(f"{train.key}: EXIF i inventari validats, {len(paths)} RAW", flush=True)

    first, first_sat = load_planes(paths[0], train)
    shape = first.shape
    annulus = central_annulus(shape[-2:])
    sum_x = np.zeros(shape, np.float32)
    sum_x2 = np.zeros(shape, np.float32)
    sum_w = np.zeros(4, np.float64)
    frame_ledger: list[dict[str, Any]] = []

    # Passada 1: normalitzacions fotomètriques i estimador preliminar.
    for index, path in enumerate(paths):
        planes, sat = (first, first_sat) if index == 0 else load_planes(path, train)
        norms = [float(np.median(planes[c][annulus])) for c in range(4)]
        accepted = (max(sat) <= 0.001 and min(norms) > 50.0 and all(np.isfinite(norms)))
        frame_ledger.append({
            "path": str(path),
            "accepted": bool(accepted),
            "central_signal_adu_R_G1_G2_B": norms,
            "saturated_fraction_R_G1_G2_B": list(map(float, sat)),
            "exif": records[index],
        })
        if not accepted:
            print(f"  REBUTJAT {path.name}: norm={norms}, sat={sat}", flush=True)
            continue
        for c in range(4):
            x = planes[c] / norms[c]
            w = norms[c]
            sum_x[c] += w * x
            sum_x2[c] += w * x * x
            sum_w[c] += w
        if (index + 1) % 10 == 0 or index + 1 == len(paths):
            print(f"  passada 1: {index + 1}/{len(paths)}", flush=True)
        del planes

    accepted_ledger = [row for row in frame_ledger if row["accepted"]]
    if len(accepted_ledger) < 10:
        raise RuntimeError(f"només {len(accepted_ledger)} flats acceptats")
    sw_scalar = sum_w[:, None, None]
    prelim_mean = sum_x / sw_scalar
    prelim_var = np.maximum(sum_x2 / sw_scalar - prelim_mean * prelim_mean, 1e-10)
    prelim_std = np.sqrt(prelim_var, dtype=np.float32)
    del sum_x, sum_x2, prelim_var, first

    # Passada 2: rebuig per píxel i splits independents odd/even.
    sw_a = np.zeros(shape, np.float32)
    sx_a = np.zeros(shape, np.float32)
    sw_b = np.zeros(shape, np.float32)
    sx_b = np.zeros(shape, np.float32)
    sw2 = np.zeros(shape, np.float32)
    sx2 = np.zeros(shape, np.float32)
    coverage = np.zeros(shape, np.uint16)
    coarse_shape = (4, shape[-2] // COARSE_FACTOR, shape[-1] // COARSE_FACTOR)
    coarse_sx = np.zeros((4, *coarse_shape), np.float32)
    coarse_sw = np.zeros((4, 4), np.float64)

    for j, row in enumerate(accepted_ledger):
        path = Path(row["path"])
        norms = row["central_signal_adu_R_G1_G2_B"]
        planes, _ = load_planes(path, train)
        group = min(3, (4 * j) // len(accepted_ledger))
        for c in range(4):
            signal = planes[c]
            x = signal / norms[c]
            shot = np.sqrt(np.maximum(signal, 1.0) + 16.0, dtype=np.float32) / norms[c]
            threshold = CLIP_SIGMA * np.maximum(prelim_std[c], shot) + 0.001
            valid = ((signal > 0) & (signal + train.black[c] < train.saturation_raw) &
                     np.isfinite(x) & (np.abs(x - prelim_mean[c]) <= threshold))
            vf = valid.astype(np.float32)
            weighted = norms[c] * vf
            if j % 2 == 0:
                sw_a[c] += weighted
                sx_a[c] += weighted * x
            else:
                sw_b[c] += weighted
                sx_b[c] += weighted * x
            sw2[c] += norms[c] * norms[c] * vf
            sx2[c] += weighted * x * x
            coverage[c] += valid
            coarse_sx[group, c] += norms[c] * downsample_mean(x)
            coarse_sw[group, c] += norms[c]
        if (j + 1) % 10 == 0 or j + 1 == len(accepted_ledger):
            print(f"  passada 2: {j + 1}/{len(accepted_ledger)}", flush=True)
        del planes

    sw = sw_a + sw_b
    sx = sx_a + sx_b
    master = np.divide(sx, sw, out=np.ones_like(sx), where=sw > 0)
    split_a = np.divide(sx_a, sw_a, out=np.ones_like(sx_a), where=sw_a > 0)
    split_b = np.divide(sx_b, sw_b, out=np.ones_like(sx_b), where=sw_b > 0)
    population_var = np.maximum(np.divide(sx2, sw, out=np.zeros_like(sx2), where=sw > 0)
                                - master * master, 0.0)
    neff = np.divide(sw * sw, sw2, out=np.zeros_like(sw), where=sw2 > 0)
    variance_random = np.divide(population_var, np.maximum(neff - 1.0, 1.0))
    variance_systematic = 0.25 * (split_a - split_b) ** 2
    del sx, sw, sx2, sw2, population_var, sx_a, sx_b, sw_a, sw_b

    master, scales = normalize_factor(master, annulus)
    for c, scale in enumerate(scales):
        split_a[c] /= scale
        split_b[c] /= scale
        variance_random[c] /= scale * scale
        variance_systematic[c] /= scale * scale

    blocks = np.empty_like(coarse_sx)
    for g in range(4):
        for c in range(4):
            blocks[g, c] = coarse_sx[g, c] / coarse_sw[g, c]
    del coarse_sx

    # Separació multiplicativa en log: el geometric-even anul·la un gradient
    # lineal estable sense deixar el terme de segon ordre de la mitjana aritmètica.
    log_full = np.log(np.clip(master, 1e-6, None), dtype=np.float32)
    log_even = 0.5 * (log_full + log_full[:, ::-1, ::-1])
    log_even_smooth = ndi.gaussian_filter(
        log_even, sigma=(0, OPTICAL_SIGMA_PLANE_PX, OPTICAL_SIGMA_PLANE_PX), mode="nearest"
    ).astype(np.float32)
    log_smooth2d = ndi.gaussian_filter(
        log_full, sigma=(0, OPTICAL_SIGMA_PLANE_PX, OPTICAL_SIGMA_PLANE_PX), mode="nearest"
    ).astype(np.float32)
    log_radial = radialize_log(log_even_smooth)
    optical_even, _ = normalize_factor(np.exp(log_even_smooth), annulus)
    optical_smooth2d, _ = normalize_factor(np.exp(log_smooth2d), annulus)
    optical_radial, _ = normalize_factor(np.exp(log_radial), annulus)

    # PRNU fi: residu logarítmic respecte d'una base de pocs píxels. Els
    # defectes grossos no es promocionen com a guany multiplicatiu.
    fine_log_raw = log_full - ndi.gaussian_filter(
        log_full, sigma=(0, FINE_SIGMA_PLANE_PX, FINE_SIGMA_PLANE_PX), mode="reflect"
    )
    log_a = np.log(np.clip(split_a, 1e-6, None), dtype=np.float32)
    log_b = np.log(np.clip(split_b, 1e-6, None), dtype=np.float32)
    fine_a = log_a - ndi.gaussian_filter(
        log_a, sigma=(0, FINE_SIGMA_PLANE_PX, FINE_SIGMA_PLANE_PX), mode="reflect"
    )
    fine_b = log_b - ndi.gaussian_filter(
        log_b, sigma=(0, FINE_SIGMA_PLANE_PX, FINE_SIGMA_PLANE_PX), mode="reflect"
    )
    defect = (~np.isfinite(fine_log_raw)) | (np.abs(fine_log_raw) >= 0.08)
    shrink = []
    split_r = []
    fine_log = np.zeros_like(fine_log_raw)
    for c in range(4):
        r, n_corr = split_correlation(fine_a[c], fine_b[c])
        factor = min(1.0, 2.0 * r / (1.0 + r)) if r > 0 else 0.0
        shrink.append(float(factor))
        split_r.append({"r": float(r), "n": n_corr})
        fine_log[c] = np.where(defect[c], 0.0,
                               np.clip(fine_log_raw[c] * factor, -0.08, 0.08))
    fine_factor = np.exp(fine_log).astype(np.float32)

    # Persistència científica en plans CFA4 i FITS mosaic interoperable.
    products = {
        "MASTER_FULL_CFA4.npy": master,
        "MASTER_OPTICAL_RADIAL_CFA4.npy": optical_radial,
        "MASTER_OPTICAL_EVEN180_CFA4.npy": optical_even,
        "MASTER_OPTICAL_SMOOTH2D_CFA4.npy": optical_smooth2d,
        "MASTER_FINE_SENSOR_FACTOR_CFA4.npy": fine_factor,
        "MASTER_VARIANCE_RANDOM_CFA4.npy": variance_random.astype(np.float32),
        "MASTER_VARIANCE_SYSTEMATIC_SPLIT_CFA4.npy": variance_systematic.astype(np.float32),
        "MASTER_COVERAGE_CFA4.npy": coverage,
        "SPLIT_ODD_CFA4.npy": split_a,
        "SPLIT_EVEN_CFA4.npy": split_b,
        "TEMPORAL_BLOCKS_CFA4_DOWNSAMPLED8.npy": blocks,
        "DEFECT_MASK_CFA4.npy": defect,
    }
    for filename, array in products.items():
        np.save(staging / filename, array, allow_pickle=False)
        print(f"  escrit {filename}", flush=True)

    fits_products = {
        "MASTER_FULL_CFA.fits": (master, "FULL_SESSION"),
        "MASTER_OPTICAL_RADIAL_CFA.fits": (optical_radial, "OPTICAL_RADIAL"),
        "MASTER_OPTICAL_EVEN180_CFA.fits": (optical_even, "OPTICAL_EVEN180"),
        "MASTER_OPTICAL_SMOOTH2D_CFA.fits": (optical_smooth2d, "OPTICAL_SMOOTH2D"),
        "MASTER_FINE_SENSOR_FACTOR_CFA.fits": (fine_factor, "FINE_SENSOR"),
    }
    for filename, (array, caltype) in fits_products.items():
        write_fits(staging / filename, array, train, caltype, len(accepted_ledger))
        print(f"  escrit {filename}", flush=True)

    make_preview(staging / "MASTER_DIAGNOSTIC.png", master, optical_radial,
                 optical_smooth2d, fine_log)

    source_stats = {
        str(path): {
            "size": path.stat().st_size,
            "inode": path.stat().st_ino,
            "mtime_ns": path.stat().st_mtime_ns,
        }
        for path in paths
    }
    source_hashes: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(sha256, path): path for path in paths}
        for future in concurrent.futures.as_completed(futures):
            source_hashes[str(futures[future])] = future.result()

    temporal_metrics = []
    for g in range(3):
        ratio = blocks[g + 1] / np.clip(blocks[g], 1e-6, None) - 1.0
        temporal_metrics.append({"from_block": g + 1, "to_block": g + 2,
                                 **metric_abs_percent(ratio, stride=1)})
    log_asym = 0.5 * (log_full - log_full[:, ::-1, ::-1])
    receipt = {
        "schema": "POSTERIOR_ECLIPSE_MASTER_FLAT_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "train": train.key,
        "source_folder": str(train.source),
        "source_epoch": "2026-08-22 posterior to the 2026-08-12 eclipse",
        "source_mutations": 0,
        "grid": {
            "mosaic_shape": list(train.raw_shape),
            "cfa4_shape": list(shape),
            "pattern": "RGGB",
            "plane_order": list(PLANE_NAMES),
            "crop_raw_y_x_h_w": list(train.crop) if train.crop else None,
        },
        "calibration": {
            "linear_cfa": True,
            "debayer": False,
            "white_balance": False,
            "denoise": False,
            "black_adu_R_G1_G2_B": list(train.black),
            "saturation_raw": train.saturation_raw,
            "normalization": "per frame and CFA plane, robust median of central annulus r=0.05..0.18 min-dimension",
            "weight": "central signal ADU, proportional to photon information within each plane",
            "combine": f"two-pass weighted mean; per-pixel {CLIP_SIGMA}-sigma rejection",
            "splits": "odd/even full resolution plus four contiguous temporal blocks downsampled 8x",
            "optical_even": "geometric 180-degree even component in log space",
            "optical_smoothing_sigma_plane_px": OPTICAL_SIGMA_PLANE_PX,
            "fine_highpass_sigma_plane_px": FINE_SIGMA_PLANE_PX,
        },
        "counts": {
            "total": len(paths),
            "accepted": len(accepted_ledger),
            "rejected": len(paths) - len(accepted_ledger),
        },
        "normalization_scale_after_combine_R_G1_G2_B": scales,
        "coverage": {
            "minimum": coverage.reshape(4, -1).min(1).astype(int).tolist(),
            "median": np.median(coverage.reshape(4, -1), axis=1).astype(float).tolist(),
            "maximum": coverage.reshape(4, -1).max(1).astype(int).tolist(),
        },
        "effective_n": sample_stats(neff),
        "full_stats": sample_stats(master),
        "optical_radial_stats": sample_stats(optical_radial),
        "random_sigma_master": sample_stats(np.sqrt(variance_random, dtype=np.float32)),
        "split_systematic_sigma": sample_stats(np.sqrt(variance_systematic, dtype=np.float32)),
        "odd_even_difference": metric_abs_percent(split_a / np.clip(split_b, 1e-6, None) - 1.0),
        "temporal_block_differences": temporal_metrics,
        "log_180_asymmetry": metric_abs_percent(log_asym),
        "fine_sensor": {
            "split_correlation_R_G1_G2_B": split_r,
            "wiener_shrink_R_G1_G2_B": shrink,
            "applied_log_residual": metric_abs_percent(fine_log),
            "defect_fraction_R_G1_G2_B": defect.reshape(4, -1).mean(1).astype(float).tolist(),
        },
        "product_policy": {
            "MASTER_FULL": "QUARANTINE_TRANSFER; diagnostic session flat",
            "MASTER_OPTICAL_RADIAL": "CANDIDATE; invariant under camera rotation",
            "MASTER_OPTICAL_EVEN180": "CANDIDATE; test against eclipse before promotion",
            "MASTER_OPTICAL_SMOOTH2D": "QUARANTINE_GRADIENT until eclipse null tests",
            "MASTER_FINE_SENSOR": "CANDIDATE; requires cross-epoch sensor-coordinate validation",
        },
        "frame_ledger": frame_ledger,
        "source_stat": source_stats,
        "source_sha256": dict(sorted(source_hashes.items())),
    }
    (staging / "MASTER_FLAT_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    output_hashes = {}
    for path in sorted(staging.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            output_hashes[path.name] = sha256(path)
    with (staging / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for filename, digest in output_hashes.items():
            fh.write(f"{digest}  {filename}\n")

    os.replace(staging, destination)
    print(f"PROMOGUT atomicament: {destination}", flush=True)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", choices=sorted(TRAINS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    receipt = build(TRAINS[args.train], args.out.resolve(), args.workers)
    print(json.dumps({
        "train": receipt["train"],
        "counts": receipt["counts"],
        "odd_even_difference": receipt["odd_even_difference"],
        "log_180_asymmetry": receipt["log_180_asymmetry"],
        "fine_sensor": receipt["fine_sensor"],
    }, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
