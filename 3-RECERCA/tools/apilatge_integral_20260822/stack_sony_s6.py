#!/usr/bin/env python3
"""Build exposure-separated S6 corona masters for Sony A7RIIIA + FE 300/2.8.

Calibration is linear CFA (exact-temperature dark, then the smooth optical
flat) before interpolation.  Registration is per frame in the solar frame:
lunar limb plus DE440 supplies translation, while the independently measured
A-to-C mount similarity supplies rotation and scale.  Exposure groups remain
separate; HDR and visual treatment are downstream operations.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import pickle
import subprocess
from pathlib import Path

import cv2
import numpy as np
import rawpy
import tifffile
from scipy import ndimage as ndi


DATA = Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA")
WORK = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/"
    "Work_2026-08-17/sony"
)
EPHEMERIS = Path("/Users/USUARI/.cache/skyfield/de440s.bsp")
C2_LOCAL = dt.datetime(2026, 8, 12, 20, 28, 45)
UTC_OFFSET_H = 2
LOCATION = (42.299407, -5.02503, 798.0)
PLATE_SCALE = 3.2019913768363018
PA_NORTH = 90.27059690231728
PA_EAST = 358.64613998047975
SOLAR_REFERENCE = np.array([3894.0057024183907, 2768.6725752051257])
# DE440 topocentric Sun distance at the acquisition site/time together with
# IAU nominal R_sun=695700 km gives 946.6598 arcsec.  The old generic 959"
# value was 1.303% too large and moved the >4.2 R sky-fit gate by ~16 px.
SOLAR_RADIUS_PX = 946.6598 / PLATE_SCALE
SOLAR_RADIUS_AUTHORITY = (
    "DE440 topocentric at 2026-08-12 totality, site 42.299407N 5.02503W "
    "798 m; IAU nominal solar radius 695700 km; 946.6598 arcsec"
)
GAIN_E_PER_ADU = 3.41
READ_NOISE_ADU = 1.22
SATURATION_RAW = 16100
SATURATION_DILATION = 3
SIGMA_INTERP = (1.0, 0.7, 1.0)
K_EXTINCTION_MAG_AIRMASS = 0.402
# Gate fixed in physical/model geometry, never from the apparent deep-frame
# hole.  The 8 s glow biases the measured edge inward by about 10 px; using
# that apparent radius created an exposure-dependent mask step and therefore
# a direct HDR-ring risk.  The 325 px value is the project G4 registration
# gate (physical lunar radius plus PSF/limb safety margin).
LUNAR_EXCLUSION_RADIUS_NATIVE_PX = 325.0
# Keep the diagonal per-pixel variance unchanged.  The earlier +0.42 lag-1
# estimate came from an unregistered A--C difference and therefore contained
# broad solar structure; registered dark-pair checks are only about 0.07--0.11
# and do not justify a scalar 8 s inflation.  A spatial covariance product is
# still pending and must be propagated separately if later demonstrated.
SPATIAL_COVARIANCE_VARIANCE_FACTOR_8S = 1.0
SPATIAL_COVARIANCE_BASIS = (
    "diagonal pixel variance only; scalar 8 s inflation withdrawn because "
    "the prior +0.42 estimate mixed unregistered solar/mount structure; "
    "full spatial covariance product pending"
)
XMATCH_SOLUTION = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/"
    "Work_2026-08-17/xmatch/final_solution.json")

GROUPS = {
    1 / 30: ["DSC06983", "DSC06995", "DSC06998"],
    1 / 8: ["DSC06986", "DSC06992"],
    1 / 4: ["DSC06982", "DSC06994", "DSC06997"],
    1.0: ["DSC06985"],
    2.0: ["DSC06984", "DSC06996", "DSC06999"],
    8.0: ["DSC06987", "DSC06993"],
}
REJECTED = {"DSC06988": "~25 px star trail during mount jump",
            "DSC06990": "8 s exposure moved during mount jump"}
QUARANTINE = {"DSC06989": "limb rms 4.30 px between mount jumps; inclusion test required",
              "DSC06991": "~11 px stellar trace; inclusion test required"}
MOON_DEEP = {key: value for key, value in pickle.load(open(WORK / "moon.pkl", "rb")).items()}
OFFSETS6 = pickle.load(open(WORK / "offsets6.pkl", "rb"))["off"]
REGISTER_V3_PATH = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Sony/Apilats/"
    "300mm_apilat_v3/registre_v3.json"
)
REGISTER_V3 = json.loads(REGISTER_V3_PATH.read_text(encoding="utf-8"))["registre"]
STELLAR_OFFSETS = {
    **{key: tuple(map(float, value)) for key, value in OFFSETS6.items()},
    **{key: (float(value["dx"]), float(value["dy"]))
       for key, value in REGISTER_V3.items()},
    # Re-measured 22-08-2026 with the v3 linear-G catalogue algorithm against
    # the nearest non-trailed frame of the same mount group.
    "DSC06986": (-233.778694028, 713.491498815),
    "DSC06992": (-0.751816324, -0.326901067),
}
STELLAR_OFFSET_SOURCE = {
    "DSC06986": "3 common stars vs DSC06985; MAD=(0.156,0.564) px",
    "DSC06992": "4 common stars vs DSC06993; MAD=(0.121,0.482) px",
}
CATALOGUE_RESIDUAL_ANCHOR = {"DSC06986": "DSC06985", "DSC06992": "DSC06993"}
STELLAR_CATALOG = {}
with (WORK / "catalog_sony.txt").open(encoding="utf-8") as _catalog_fh:
    for _line in _catalog_fh:
        if _line.startswith("#") or not _line.strip():
            continue
        _parts = _line.split()
        STELLAR_CATALOG[_parts[0]] = np.array(
            [float(_parts[1]), float(_parts[2])], np.float64)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exp_tag(exposure: float) -> str:
    return f"{exposure:g}s" if exposure >= 1 else f"1-{round(1 / exposure):d}s"


def parse_exif(names: list[str]) -> dict[str, dict]:
    paths = [DATA / f"{name}.ARW" for name in names]
    cmd = ["exiftool", "-q", "-n", "-j", "-FileName", "-DateTimeOriginal",
           "-SubSecTimeOriginal", "-ExposureTime", "-ISO", "-CameraTemperature",
           "-Model", "-LensModel", *map(str, paths)]
    rows = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)
    out = {}
    for row in rows:
        name = Path(row["FileName"]).stem
        stamp = dt.datetime.strptime(row["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
        subseconds = str(row.get("SubSecTimeOriginal", "") or "")
        if subseconds and subseconds.isdigit():
            stamp += dt.timedelta(seconds=float("0." + subseconds))
        exposure = float(row["ExposureTime"])
        midpoint = stamp - dt.timedelta(seconds=exposure / 2)  # Sony EXIF=end
        row["midpoint"] = midpoint
        row["t_rel_c2_s"] = (midpoint - C2_LOCAL).total_seconds()
        out[name] = row
    return out


def seed_for(name: str) -> tuple[float, float]:
    number = int(name[-5:])
    if number <= 6987:
        return 3670.0, 3483.0
    if number <= 6990:
        return 3890.0, 3483.0
    return 3894.0, 2768.0


def fit_circle(px: np.ndarray, py: np.ndarray) -> tuple[float, float, float]:
    design = np.c_[2 * px, 2 * py, np.ones(len(px))]
    solution, *_ = np.linalg.lstsq(design, px * px + py * py, rcond=None)
    cx, cy = solution[0], solution[1]
    radius = math.sqrt(max(solution[2] + cx * cx + cy * cy, 0))
    return float(cx), float(cy), float(radius)


def measure_limb(name: str) -> dict:
    if name in MOON_DEEP and name in {"DSC06987", "DSC06993"}:
        x, y, radius, *_ = MOON_DEEP[name]
        return {"moon_x": float(x), "moon_y": float(y), "moon_radius_px": float(radius),
                "limb_rms_px": None, "limb_n": None,
                "method": "validated saturated-hole moon.pkl"}
    with rawpy.imread(str(DATA / f"{name}.ARW")) as raw:
        green = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16,
                                gamma=(1, 1), half_size=False)[..., 1].astype(np.float32)
    cx, cy = seed_for(name)
    angles = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    ca, sa = np.cos(angles), np.sin(angles)
    radii = np.arange(255.0, 390.0, 0.5)
    result = None
    for _ in range(5):
        xs = cx + radii[None, :] * ca[:, None]
        ys = cy + radii[None, :] * sa[:, None]
        profiles = ndi.map_coordinates(green, [ys.ravel(), xs.ravel()], order=1,
                                       mode="constant", cval=np.nan).reshape(len(angles), -1)
        gradient = np.nan_to_num(np.gradient(profiles, axis=1))
        peak = gradient.argmax(axis=1)
        strength = gradient[np.arange(len(angles)), peak]
        ok = strength > max(float(np.percentile(strength, 55)) * 0.3, 1.0)
        ok &= (peak > 3) & (peak < len(radii) - 4)
        rp = radii[peak]
        px, py = cx + rp * ca, cy + rp * sa
        for _ in range(4):
            if ok.sum() < 30:
                break
            fx, fy, fr = fit_circle(px[ok], py[ok])
            residual = np.abs(np.hypot(px - fx, py - fy) - fr)
            scale = max(2.5 * float(np.median(residual[ok])), 0.8)
            ok &= residual < scale
        if ok.sum() < 30:
            break
        cx, cy = fx, fy
        rms = float(np.sqrt(np.mean((np.hypot(px[ok] - cx, py[ok] - cy) - fr) ** 2)))
        result = {"moon_x": cx, "moon_y": cy, "moon_radius_px": fr,
                  "limb_rms_px": rms, "limb_n": int(ok.sum()),
                  "method": "linear geometry demosaic; robust radial-gradient circle"}
    if result is None:
        raise RuntimeError(f"lunar limb failed: {name}")
    return result


def basis_vector(pa_deg: float) -> np.ndarray:
    angle = math.radians(pa_deg)
    return np.array([math.sin(angle), -math.cos(angle)])


def lunar_minus_solar(meta: dict[str, dict]) -> dict[str, np.ndarray]:
    from skyfield.api import load, wgs84
    eph = load(str(EPHEMERIS))
    timescale = load.timescale()
    site = eph["earth"] + wgs84.latlon(LOCATION[0], LOCATION[1], elevation_m=LOCATION[2])
    north, east = basis_vector(PA_NORTH), basis_vector(PA_EAST)
    out = {}
    for name, row in meta.items():
        local = row["midpoint"]
        utc = local - dt.timedelta(hours=UTC_OFFSET_H)
        t = timescale.utc(utc.year, utc.month, utc.day, utc.hour, utc.minute,
                          utc.second + utc.microsecond * 1e-6)
        observer = site.at(t)
        moon_ra, moon_dec, _ = observer.observe(eph["moon"]).apparent().radec()
        sun_ra, sun_dec, _ = observer.observe(eph["sun"]).apparent().radec()
        d_east = (moon_ra.radians - sun_ra.radians) * math.cos(sun_dec.radians)
        d_north = moon_dec.radians - sun_dec.radians
        out[name] = ((d_east * 206264.806) * east
                     + (d_north * 206264.806) * north) / PLATE_SCALE
    return out


def airmass_and_altitude(meta: dict[str, dict]) -> dict[str, tuple[float, float]]:
    """Kasten-Young airmass at each frame midpoint, with apparent altitude."""
    from skyfield.api import load, wgs84
    eph = load(str(EPHEMERIS))
    timescale = load.timescale()
    site = eph["earth"] + wgs84.latlon(LOCATION[0], LOCATION[1], elevation_m=LOCATION[2])
    out = {}
    for name, row in meta.items():
        local = row["midpoint"]
        utc = local - dt.timedelta(hours=UTC_OFFSET_H)
        t = timescale.utc(utc.year, utc.month, utc.day, utc.hour, utc.minute,
                          utc.second + utc.microsecond * 1e-6)
        altitude = float(site.at(t).observe(eph["sun"]).apparent().altaz()[0].degrees)
        airmass = 1.0 / (math.sin(math.radians(altitude))
                         + 0.50572 * (altitude + 6.07995) ** -1.6364)
        out[name] = (float(airmass), altitude)
    return out


def group_name(name: str) -> str:
    number = int(name[-5:])
    return "A" if number <= 6987 else "B" if number <= 6990 else "C"


def linear_mount_transform(name: str, meta: dict[str, dict]) -> tuple[np.ndarray, dict]:
    measured = np.load(WORK / "warpM.npy").astype(np.float64)
    scale_a = math.sqrt(abs(np.linalg.det(measured)))
    theta_a = math.atan2(measured[1, 0], measured[0, 0])
    group = group_name(name)
    if group == "A":
        fraction = 0.0
    elif group == "C":
        fraction = 1.0
    else:
        ta = max(row["midpoint"] for n, row in meta.items() if group_name(n) == "A")
        tc = min(row["midpoint"] for n, row in meta.items() if group_name(n) == "C")
        fraction = np.clip((meta[name]["midpoint"] - ta).total_seconds()
                           / max((tc - ta).total_seconds(), 1e-6), 0, 1)
    scale = 1.0 + (1.0 - fraction) * (scale_a - 1.0)
    theta = (1.0 - fraction) * theta_a
    c, s = math.cos(theta), math.sin(theta)
    matrix = scale * np.array([[c, -s], [s, c]], np.float64)
    return matrix, {"mount_group": group, "A_to_C_fraction": float(fraction),
                    "scale": scale, "rotation_deg": math.degrees(theta),
                    "status": "MEASURED_A_OR_C" if group != "B" else "MODELLED_B_QUARANTINE"}


def registration_affine(name: str, meta: dict[str, dict], solar_xy: np.ndarray
                        ) -> tuple[np.ndarray, dict]:
    """Return a source-to-output affine in the solar frame.

    Stellar data determine only rotation/scale.  Translation is closed for
    every frame by the independently measured lunar limb plus DE440 solar
    offset.  Applying the historical stellar OFF as the final translation
    left 0.3--2.1 px of frame-dependent solar-centre error in the v5 pilot,
    which is enough to leave coherent inner corona in the A-C null.
    """
    group = group_name(name)
    if name in STELLAR_OFFSETS and group in {"A", "C"}:
        offset = np.asarray(STELLAR_OFFSETS[name], np.float64)
        if group == "A":
            measured = np.load(WORK / "warpM.npy").astype(np.float64)
            translation = np.load(WORK / "warpT.npy").astype(np.float64)
            centre = np.load(WORK / "warpC.npy").astype(np.float64)
            inverse = np.linalg.inv(measured)
            # apila_sony_v3 expresses the mapping as output->source for
            # scipy.ndimage. Convert it exactly to OpenCV source->output.
            inverse_offset = -inverse @ (centre + translation) + centre + offset
            affine_translation = -measured @ inverse_offset
            linear = measured
        else:
            linear = np.eye(2, dtype=np.float64)
            affine_translation = -offset
        stellar_affine = np.c_[linear, affine_translation]
        residual_median = np.zeros(2, np.float64)
        residual_mad = np.full(2, np.nan, np.float64)
        residual_n = 0
        # The historical OFF is a robust translation against a nearby frame.
        # Close the remaining sub-pixel catalogue residual when the validated
        # per-frame centroids are available; this does not fit a new rotation
        # or scale and therefore cannot absorb coronal structure.
        details = REGISTER_V3.get(name, {}).get("estrelles", {}).get("detall", {})
        common = REGISTER_V3.get(name, {}).get("estrelles", {}).get(
            "comunes", list(details))
        residuals = []
        for star_id in common:
            if star_id not in details or star_id not in STELLAR_CATALOG:
                continue
            native = np.array([details[star_id]["x"], details[star_id]["y"]], np.float64)
            residuals.append(stellar_affine[:, :2] @ native + stellar_affine[:, 2]
                             - STELLAR_CATALOG[star_id])
        if len(residuals) >= 3:
            residuals = np.asarray(residuals)
            residual_median = np.median(residuals, axis=0)
            radial = np.hypot(*(residuals - residual_median).T)
            keep = radial < max(3.0, 2.5 * float(np.median(radial)))
            if int(keep.sum()) >= 3:
                residuals = residuals[keep]
                residual_median = np.median(residuals, axis=0)
            residual_mad = 1.4826 * np.median(
                np.abs(residuals - residual_median), axis=0)
            residual_n = len(residuals)
        elif name in CATALOGUE_RESIDUAL_ANCHOR:
            anchor = CATALOGUE_RESIDUAL_ANCHOR[name]
            _, anchor_info = registration_affine(anchor, meta, solar_xy)
            residual_median = np.array([
                anchor_info["catalogue_residual_dx_removed"],
                anchor_info["catalogue_residual_dy_removed"],
            ], np.float64)
            residual_mad = np.array([
                anchor_info["catalogue_residual_mad_x"],
                anchor_info["catalogue_residual_mad_y"],
            ], np.float64)
            residual_n = int(anchor_info["catalogue_residual_n"])
        # The output frame is heliocentric.  A stellar OFF is an independent
        # geometry check, not the translation authority for the moving Sun.
        affine = np.c_[linear, SOLAR_REFERENCE - linear @ solar_xy]
        return affine, {
            "mount_group": group,
            "A_to_C_fraction": 0.0 if group == "A" else 1.0,
            "scale": float(math.sqrt(abs(np.linalg.det(linear)))),
            "rotation_deg": float(math.degrees(math.atan2(linear[1, 0], linear[0, 0]))),
            "status": "MEASURED_STELLAR_OFFSET_AND_CATALOGUE_RESIDUAL",
            "stellar_offset_dx": float(offset[0]),
            "stellar_offset_dy": float(offset[1]),
            "stellar_offset_source": STELLAR_OFFSET_SOURCE.get(
                name, "historical validated OFF/register_v3"),
            "catalogue_residual_anchor": CATALOGUE_RESIDUAL_ANCHOR.get(name),
            "catalogue_residual_dx_removed": float(residual_median[0]),
            "catalogue_residual_dy_removed": float(residual_median[1]),
            "catalogue_residual_mad_x": float(residual_mad[0]),
            "catalogue_residual_mad_y": float(residual_mad[1]),
            "catalogue_residual_n": residual_n,
            "translation_authority": "measured lunar limb + DE440; exact solar-centre closure",
        }
    linear, info = linear_mount_transform(name, meta)
    affine = np.c_[linear, SOLAR_REFERENCE - linear @ solar_xy]
    info.update({
        "status": "MODELLED_LIMB_EPHEMERIS_QUARANTINE",
        "stellar_offset_dx": None,
        "stellar_offset_dy": None,
        "catalogue_residual_dx_removed": None,
        "catalogue_residual_dy_removed": None,
        "catalogue_residual_mad_x": None,
        "catalogue_residual_mad_y": None,
        "catalogue_residual_n": 0,
        "translation_authority": "measured lunar limb + DE440; exact solar-centre closure",
    })
    return affine, info


def gaussian_sumsq(sigma: float) -> float:
    size = int(math.ceil(8 * sigma)) | 1
    impulse = np.zeros((size, size), np.float64)
    impulse[size // 2, size // 2] = 1
    kernel = ndi.gaussian_filter(impulse, sigma, mode="constant")
    return float(np.square(kernel).sum())


def interpolate_cfa(signal: np.ndarray, variance: np.ndarray, colors: np.ndarray,
                    valid: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    images, variances, valids = [], [], []
    for output_channel, raw_channels in enumerate(((0,), (1, 3), (2,))):
        sigma = SIGMA_INTERP[output_channel]
        cfa_samples = np.isin(colors, raw_channels)
        mask = (valid & cfa_samples).astype(np.float32)
        denominator = ndi.gaussian_filter(mask, sigma, mode="constant")
        nominal_denominator = ndi.gaussian_filter(
            cfa_samples.astype(np.float32), sigma, mode="constant")
        numerator = ndi.gaussian_filter(signal * mask, sigma, mode="constant")
        image = np.where(denominator > 0.08, numerator / np.maximum(denominator, 1e-8), 0)
        q = gaussian_sumsq(sigma)
        var_num = q * ndi.gaussian_filter(variance * mask, sigma / math.sqrt(2), mode="constant")
        var_image = np.where(denominator > 0.08,
                             var_num / np.maximum(denominator * denominator, 1e-12), np.inf)
        # A Bayer plane occupies 1/4 (R/B) or 1/2 (G) of the sensor, so an
        # absolute threshold near one would reject every pixel.  Compare the
        # surviving samples with the locally expected CFA density instead.
        ok = ((nominal_denominator > 0.08)
              & (denominator >= 0.97 * nominal_denominator))
        images.append(image.astype(np.float32))
        variances.append(var_image.astype(np.float32))
        valids.append(ok)
    return np.stack(images, -1), np.stack(variances, -1), np.stack(valids, -1)


def interpolate_cfa_systematic(systematic_variance: np.ndarray, colors: np.ndarray,
                               valid: np.ndarray) -> np.ndarray:
    """Conservative local propagation for the shared smooth optical flat.

    Flat uncertainty is systematic, not independent pixel noise.  Standard
    deviations therefore combine linearly through the normalized kernel and
    are kept separate from the random variance used for stacking weights.
    """
    output = []
    sigma_native = np.sqrt(np.maximum(systematic_variance, 0.0))
    for output_channel, raw_channels in enumerate(((0,), (1, 3), (2,))):
        sigma = SIGMA_INTERP[output_channel]
        samples = np.isin(colors, raw_channels)
        mask = (valid & samples).astype(np.float32)
        denominator = ndi.gaussian_filter(mask, sigma, mode="constant")
        sigma_num = ndi.gaussian_filter(sigma_native * mask, sigma, mode="constant")
        sigma_image = np.where(
            denominator > 0.08, sigma_num / np.maximum(denominator, 1e-8), np.inf)
        output.append(np.square(sigma_image).astype(np.float32))
    return np.stack(output, -1)


def calibrate(name: str, exposure: float, dark_root: Path, flat_root: Path
              ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                         np.ndarray, dict]:
    dark_dir = dark_root / f"{exposure:.10g}"
    dark = np.load(dark_dir / "MASTER_DARK_raw_ADU.npy", mmap_mode="r")
    dark_var = np.load(dark_dir / "MASTER_DARK_VARIANCE_ADU2.npy", mmap_mode="r")
    hot = np.load(dark_dir / "HOT_PIXEL_MAP.npy", mmap_mode="r").astype(bool)
    flat = np.load(flat_root / "flat_a7r3a_optical_rgb.npy", mmap_mode="r")
    flat_unc = np.load(flat_root / "flat_a7r3a_optical_uncertainty_rgb.npy", mmap_mode="r")
    with rawpy.imread(str(DATA / f"{name}.ARW")) as raw_file:
        raw = raw_file.raw_image_visible.astype(np.float32)
        colors = raw_file.raw_colors_visible.copy()
    if raw.shape != dark.shape or raw.shape != flat.shape[:2]:
        raise RuntimeError(f"shape mismatch {name}: raw {raw.shape}, dark {dark.shape}, flat {flat.shape}")
    saturated = ndi.binary_dilation(raw >= SATURATION_RAW, iterations=SATURATION_DILATION)
    valid = ~saturated & ~hot
    valid[:40] = valid[-40:] = False
    valid[:, :40] = valid[:, -40:] = False
    signal = np.empty_like(raw, np.float32)
    random_variance = np.empty_like(raw, np.float32)
    systematic_variance = np.empty_like(raw, np.float32)
    for raw_channel, flat_channel in ((0, 0), (1, 1), (3, 1), (2, 2)):
        positions = np.argwhere(colors[:2, :2] == raw_channel)
        if len(positions) != 1:
            raise RuntimeError(f"unexpected CFA pattern for channel {raw_channel}: {positions}")
        oy, ox = map(int, positions[0])
        plane = np.s_[oy::2, ox::2]
        f = flat[..., flat_channel][plane]
        u = flat_unc[..., flat_channel][plane]
        native = raw[plane] - dark[plane]
        corrected = native / f
        # Estimate shot noise from a local expectation, not from the noisy
        # sample that is subsequently inverse-variance weighted.
        expected_native = ndi.gaussian_filter(np.maximum(native, 0.0), 2.0, mode="nearest")
        signal[plane] = corrected
        random_variance[plane] = ((expected_native / GAIN_E_PER_ADU
                                   + READ_NOISE_ADU ** 2 + dark_var[plane])
                                  / np.square(f))
        systematic_variance[plane] = np.square(corrected * u / f)
    image, random_var_image, valid_image = interpolate_cfa(
        signal, random_variance, colors, valid)
    systematic_var_image = interpolate_cfa_systematic(
        systematic_variance, colors, valid)
    image /= exposure
    random_var_image /= exposure * exposure
    systematic_var_image /= exposure * exposure
    covariance_factor = (SPATIAL_COVARIANCE_VARIANCE_FACTOR_8S
                         if abs(exposure - 8.0) < 1e-9 else 1.0)
    random_var_image *= covariance_factor
    return image, random_var_image, systematic_var_image, valid_image, saturated, {
        "raw_saturated_pixels": int(saturated.sum()),
        "hot_pixels_excluded": int(hot.sum()),
        "finite_signal_fraction": float(np.isfinite(signal).mean()),
        "dark_receipt": str(dark_dir / "DARK_RECEIPT.json"),
        "spatial_covariance_variance_factor": covariance_factor,
        "spatial_covariance_basis": SPATIAL_COVARIANCE_BASIS,
    }


def warp_frame(image: np.ndarray, random_variance: np.ndarray,
               systematic_variance: np.ndarray, valid: np.ndarray,
               saturated: np.ndarray, affine: np.ndarray
               ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                          np.ndarray, np.ndarray]:
    """Affine resampling with exact bilinear variance and full support.

    OpenCV's linear warp is correct for signal but not for variance: variance
    propagates with squared interpolation coefficients.  The implementation is
    row-chunked to avoid another pair of full-frame coordinate grids.  A
    destination channel is valid only when every non-zero bilinear contributor
    is valid, preventing zero/infinite border leakage.
    """
    height, width = image.shape[:2]
    inverse = cv2.invertAffineTransform(affine).astype(np.float32)
    warped_image = np.zeros_like(image, dtype=np.float32)
    warped_random_variance = np.full_like(random_variance, np.inf, dtype=np.float32)
    warped_systematic_variance = np.full_like(
        systematic_variance, np.inf, dtype=np.float32)
    warped_valid = np.zeros_like(valid, dtype=bool)
    warped_sat = np.zeros((height, width), dtype=bool)
    destination_x = np.arange(width, dtype=np.float32)[None, :]
    chunk_rows = 192
    for row0 in range(0, height, chunk_rows):
        row1 = min(row0 + chunk_rows, height)
        destination_y = np.arange(row0, row1, dtype=np.float32)[:, None]
        source_x = (inverse[0, 0] * destination_x
                    + inverse[0, 1] * destination_y + inverse[0, 2])
        source_y = (inverse[1, 0] * destination_x
                    + inverse[1, 1] * destination_y + inverse[1, 2])
        x0 = np.floor(source_x).astype(np.int32)
        y0 = np.floor(source_y).astype(np.int32)
        inside = (x0 >= 0) & (x0 < width - 1) & (y0 >= 0) & (y0 < height - 1)
        xc = np.clip(x0, 0, width - 2)
        yc = np.clip(y0, 0, height - 2)
        fx = source_x - x0
        fy = source_y - y0
        w00 = (1.0 - fx) * (1.0 - fy)
        w10 = fx * (1.0 - fy)
        w01 = (1.0 - fx) * fy
        w11 = fx * fy
        active00, active10 = w00 > 1e-7, w10 > 1e-7
        active01, active11 = w01 > 1e-7, w11 > 1e-7
        warped_sat[row0:row1] = (
            inside
            & ((active00 & saturated[yc, xc])
               | (active10 & saturated[yc, xc + 1])
               | (active01 & saturated[yc + 1, xc])
               | (active11 & saturated[yc + 1, xc + 1])))
        for channel in range(image.shape[2]):
            support = (inside
                       & (~active00 | valid[yc, xc, channel])
                       & (~active10 | valid[yc, xc + 1, channel])
                       & (~active01 | valid[yc + 1, xc, channel])
                       & (~active11 | valid[yc + 1, xc + 1, channel]))
            signal = (w00 * image[yc, xc, channel]
                      + w10 * image[yc, xc + 1, channel]
                      + w01 * image[yc + 1, xc, channel]
                      + w11 * image[yc + 1, xc + 1, channel])
            propagated_random = (
                np.square(w00) * np.where(
                    active00, random_variance[yc, xc, channel], 0.0)
                + np.square(w10) * np.where(
                    active10, random_variance[yc, xc + 1, channel], 0.0)
                + np.square(w01) * np.where(
                    active01, random_variance[yc + 1, xc, channel], 0.0)
                + np.square(w11) * np.where(
                    active11, random_variance[yc + 1, xc + 1, channel], 0.0))
            propagated_systematic_sigma = (
                w00 * np.sqrt(np.where(
                    active00, systematic_variance[yc, xc, channel], 0.0))
                + w10 * np.sqrt(np.where(
                    active10, systematic_variance[yc, xc + 1, channel], 0.0))
                + w01 * np.sqrt(np.where(
                    active01, systematic_variance[yc + 1, xc, channel], 0.0))
                + w11 * np.sqrt(np.where(
                    active11, systematic_variance[yc + 1, xc + 1, channel], 0.0)))
            warped_image[row0:row1, :, channel] = np.where(support, signal, 0.0)
            warped_random_variance[row0:row1, :, channel] = np.where(
                support, propagated_random, np.inf)
            warped_systematic_variance[row0:row1, :, channel] = np.where(
                support, np.square(propagated_systematic_sigma), np.inf)
            warped_valid[row0:row1, :, channel] = support
    return (warped_image, warped_random_variance, warped_systematic_variance,
            warped_valid, warped_sat, affine)


def fit_plane_difference(image: np.ndarray, reference: np.ndarray,
                         valid: np.ndarray) -> tuple[np.ndarray, list[list[float]]]:
    height, width = image.shape[:2]
    yy, xx = np.mgrid[0:height:16, 0:width:16]
    radius = np.hypot(xx - SOLAR_REFERENCE[0], yy - SOLAR_REFERENCE[1])
    base = valid[::16, ::16] & (radius > 4.2 * SOLAR_RADIUS_PX)[..., None]
    corrected = image.copy()
    coefficients = []
    full_y = np.arange(height, dtype=np.float32)[:, None] / height
    full_x = np.arange(width, dtype=np.float32)[None, :] / width
    for channel in range(3):
        mask = base[..., channel]
        if int(mask.sum()) < 1000:
            raise RuntimeError(
                f"insufficient common valid pixels for sky plane channel {channel}: "
                f"{int(mask.sum())}")
        values = (image[::16, ::16, channel] - reference[::16, ::16, channel])[mask]
        design = np.c_[np.ones(mask.sum()), xx[mask] / width, yy[mask] / height]
        keep = np.isfinite(values)
        for _ in range(4):
            coef, *_ = np.linalg.lstsq(design[keep], values[keep], rcond=None)
            residual = values - design @ coef
            sigma = 1.4826 * np.median(np.abs(residual[keep] - np.median(residual[keep])))
            keep = np.abs(residual - np.median(residual[keep])) < 3 * max(sigma, 1e-6)
        plane = coef[0] + coef[1] * full_x + coef[2] * full_y
        corrected[..., channel] -= plane
        coefficients.append(coef.tolist())
    return corrected, coefficients


def prepare_subset(contributions: list[dict]) -> tuple[list[dict], dict[str, list]]:
    """Fit nuisance sky planes using only the supplied subset.

    This is called independently for the full stack, each split and every LOO
    subset so an excluded or opposite-half frame cannot leak through a plane
    previously estimated from it.
    """
    reference = next(
        (item for item in contributions if item["mount_group"] == "C"),
        contributions[0])
    prepared = []
    coefficients = {}
    for item in contributions:
        common_valid = item["valid"] & reference["valid"]
        corrected, plane = fit_plane_difference(
            item["image"], reference["image"], common_valid)
        prepared.append({**item, "image": corrected})
        coefficients[item["name"]] = plane
    return prepared, coefficients


def combine(contributions: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                                np.ndarray, np.ndarray, np.ndarray]:
    shape = contributions[0]["image"].shape
    numerator = np.zeros(shape, np.float64)
    denominator = np.zeros(shape, np.float64)
    systematic_sigma_numerator = np.zeros(shape, np.float64)
    coverage = np.zeros(shape, np.uint16)
    saturation = np.zeros(shape[:2], np.uint16)
    for item in contributions:
        weight = np.where(
            item["valid"], 1.0 / np.maximum(item["random_variance"], 1e-20), 0.0)
        numerator += weight * item["image"]
        denominator += weight
        systematic_sigma_numerator += weight * np.sqrt(
            np.where(item["valid"], item["systematic_variance"], 0.0))
        coverage += item["valid"].astype(np.uint16)
        saturation += item["saturated"].astype(np.uint16)
        item["weight"] = weight.astype(np.float32)
    image = np.where(denominator > 0, numerator / np.maximum(denominator, 1e-30), np.nan).astype(np.float32)
    random_variance = np.where(
        denominator > 0, 1.0 / np.maximum(denominator, 1e-30), np.nan).astype(np.float32)
    systematic_variance = np.where(
        denominator > 0,
        np.square(systematic_sigma_numerator / np.maximum(denominator, 1e-30)),
        np.nan).astype(np.float32)
    total_variance = random_variance + systematic_variance
    return (image, total_variance, random_variance, systematic_variance,
            coverage, saturation)


def split_metrics(a: tuple, c: tuple) -> dict:
    ia, va, _, _, ca, _ = a
    ic, vc, _, _, cc, _ = c
    stride = 8
    variance = va[::stride, ::stride] + vc[::stride, ::stride]
    z = (ia[::stride, ::stride] - ic[::stride, ::stride]) / np.sqrt(variance)
    valid = np.all(np.isfinite(z), axis=2)
    valid &= np.all(ca[::stride, ::stride] > 0, axis=2)
    valid &= np.all(cc[::stride, ::stride] > 0, axis=2)
    values = z[valid]
    if len(values) < 1000:
        return {"status": "INCONCLUSIVE", "common_pixels": int(len(values)),
                "reason": "fewer than 1000 common RGB pixels"}
    centre = np.median(values, axis=0)
    sigma = 1.4826 * np.median(np.abs(values - centre), axis=0)
    return {"common_pixels": int(valid.sum()), "z_median_rgb": centre.tolist(),
            "z_sigma_robust_rgb": sigma.tolist(), "variance_scale_rgb": np.square(sigma).tolist()}


def save_tiff(path: Path, image: np.ndarray) -> None:
    tifffile.imwrite(path, image.astype(np.float32, copy=False), photometric="rgb",
                     compression="zlib", compressionargs={"level": 4}, bigtiff=True,
                     metadata={"axes": "YXS", "unit": "ADU/s", "linear": True},
                     software="stack_sony_s6.py")


def preview(path: Path, image: np.ndarray) -> None:
    finite = np.all(np.isfinite(image), axis=2)
    if not finite.any():
        raise RuntimeError("preview has no finite RGB pixels")
    with np.errstate(invalid="ignore"):
        luminance = np.nanmean(image, axis=2)
    values = luminance[finite]
    lo = max(float(np.percentile(values, 2)), 1e-4)
    hi = max(float(np.percentile(values, 99.9)), lo * 10)
    shown = np.log1p(np.maximum(image, 0) / lo) / np.log1p(hi / lo)
    shown = np.nan_to_num(np.clip(shown, 0, 1))
    scale = min(1.0, 1800 / image.shape[1])
    shown = cv2.resize(shown, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    if not cv2.imwrite(str(path), (shown[..., ::-1] * 255).astype(np.uint8)):
        raise RuntimeError(f"failed to write preview: {path}")


def process_group(exposure: float, names: list[str], outdir: Path,
                  dark_root: Path, flat_root: Path, segment: str) -> dict:
    outdir.mkdir(parents=True, exist_ok=False)
    meta = parse_exif(names + (["DSC06993"] if "DSC06993" not in names else []))
    for name in names:
        row = meta[name]
        assertions = {
            "ExposureTime": abs(float(row["ExposureTime"]) - exposure) <= 1e-8,
            "ISO": int(row["ISO"]) == 100,
            "CameraTemperature": int(row["CameraTemperature"]) == 40,
            "Model": row["Model"] == "ILCE-7RM3A",
            "LensModel": row["LensModel"] == "FE 300mm F2.8 GM OSS",
        }
        failed = [key for key, ok in assertions.items() if not ok]
        if failed:
            raise RuntimeError(f"{name}: EXIF identity/calibration mismatch: {failed}; {row}")
    limb = {name: measure_limb(name) for name in meta}
    relative = lunar_minus_solar(meta)
    atmosphere = airmass_and_altitude(meta)
    reference_airmass = atmosphere["DSC06993"][0]
    extinction = {name: 10 ** (0.4 * K_EXTINCTION_MAG_AIRMASS
                               * (atmosphere[name][0] - reference_airmass))
                  for name in meta}
    raw_ref_sun = np.array([limb["DSC06993"]["moon_x"], limb["DSC06993"]["moon_y"]]) - relative["DSC06993"]
    anchor = SOLAR_REFERENCE - raw_ref_sun
    solar = {name: np.array([limb[name]["moon_x"], limb[name]["moon_y"]])
                    - relative[name] + anchor for name in names}

    contributions = []
    transform_rows = []
    for name in names:
        image, random_variance, systematic_variance, valid, saturated, cal_info = calibrate(
            name, exposure, dark_root, flat_root)
        image *= extinction[name]
        random_variance *= extinction[name] ** 2
        systematic_variance *= extinction[name] ** 2
        affine, mount_info = registration_affine(name, meta, solar[name])
        (image, random_variance, systematic_variance, valid, saturated,
         affine) = warp_frame(image, random_variance, systematic_variance,
                              valid, saturated, affine)
        moon_native = np.array([limb[name]["moon_x"], limb[name]["moon_y"]])
        moon_output = affine[:, :2] @ moon_native + affine[:, 2]
        moon_radius = (LUNAR_EXCLUSION_RADIUS_NATIVE_PX
                       * math.sqrt(abs(np.linalg.det(affine[:, :2]))))
        yy = np.arange(image.shape[0], dtype=np.float32)[:, None]
        xx = np.arange(image.shape[1], dtype=np.float32)[None, :]
        lunar_valid = np.hypot(xx - moon_output[0], yy - moon_output[1]) > moon_radius
        valid &= lunar_valid[..., None]
        contributions.append({"name": name, "image": image,
                              "random_variance": random_variance,
                              "systematic_variance": systematic_variance,
                              "valid": valid, "saturated": saturated,
                              "lunar_valid": lunar_valid,
                              "mount_group": mount_info["mount_group"]})
        transform_rows.append({
            "frame": name, "t_rel_c2_s": meta[name]["t_rel_c2_s"],
            "exposure_s_exif": meta[name]["ExposureTime"],
            "iso_exif": meta[name]["ISO"],
            "camera_temperature_c_exif": meta[name]["CameraTemperature"],
            "model_exif": meta[name]["Model"], "lens_model_exif": meta[name]["LensModel"],
            "moon_x_px": limb[name]["moon_x"], "moon_y_px": limb[name]["moon_y"],
            "limb_rms_px": limb[name]["limb_rms_px"],
            "solar_x_px": solar[name][0], "solar_y_px": solar[name][1],
            "moon_output_x_px": moon_output[0], "moon_output_y_px": moon_output[1],
            "moon_exclusion_radius_px": moon_radius,
            "moon_exclusion_radius_native_model_px": LUNAR_EXCLUSION_RADIUS_NATIVE_PX,
            "airmass": atmosphere[name][0], "solar_altitude_deg": atmosphere[name][1],
            "extinction_factor_to_DSC06993": extinction[name],
            "affine_00": affine[0, 0], "affine_01": affine[0, 1], "affine_02": affine[0, 2],
            "affine_10": affine[1, 0], "affine_11": affine[1, 1], "affine_12": affine[1, 2],
            **mount_info, **cal_info,
        })
        print(f"{name}: limb rms={limb[name]['limb_rms_px']} group={mount_info['mount_group']} "
              f"rotation={mount_info['rotation_deg']:+.5f} deg", flush=True)

    # Only an additive global plane is removed.  Every null subset recomputes
    # this nuisance fit independently; no annular/radial correction is used.
    prepared, main_planes = prepare_subset(contributions)
    for row in transform_rows:
        row["sky_plane_rgb"] = json.dumps(
            main_planes[row["frame"]], separators=(",", ":"))

    full = combine(prepared)
    a_items = [x for x in contributions if x["mount_group"] == "A"]
    c_items = [x for x in contributions if x["mount_group"] == "C"]
    split = None
    if len(contributions) >= 2:
        if a_items and c_items:
            left_items, right_items = a_items, c_items
            split_method = "independent mount segments A versus C"
            left_label, right_label = "A", "C"
        else:
            # A segment-local null is more meaningful than forcing together
            # the pre/post mount-jump populations after the combined null has
            # failed.  Alternate chronologically within the same segment.
            left_items, right_items = contributions[::2], contributions[1::2]
            split_method = f"chronological interleave within segment {segment}"
            left_label, right_label = "EVEN", "ODD"
        prepared_a, planes_a = prepare_subset(left_items)
        prepared_c, planes_c = prepare_subset(right_items)
        split_a = list(combine(prepared_a))
        split_c = list(combine(prepared_c))
        split_common = ((split_a[4] > 0) & (split_c[4] > 0)
                        & np.isfinite(split_a[0]) & np.isfinite(split_c[0]))
        split_a[0], split_cross_plane = fit_plane_difference(
            split_a[0], split_c[0], split_common)
        split_a = tuple(split_a)
        split_c = tuple(split_c)
        split = split_metrics(split_a, split_c)
        split.update({
            "partition_method": split_method,
            "left_label": left_label, "right_label": right_label,
            "left": [x["name"] for x in left_items],
            "right": [x["name"] for x in right_items],
            "left_internal_planes": planes_a,
            "right_internal_planes": planes_c,
            "left_to_right_null_plane_rgb": split_cross_plane,
            "independence": "each half internally prepared from itself; only the explicit A-to-C nuisance plane uses both assembled halves",
        })
        save_tiff(outdir / "SPLIT_A_linear_float32_ADU_s.tif", split_a[0])
        save_tiff(outdir / "SPLIT_C_linear_float32_ADU_s.tif", split_c[0])
        np.save(outdir / "SPLIT_A_VARIANCE_TOTAL.npy", split_a[1])
        np.save(outdir / "SPLIT_C_VARIANCE_TOTAL.npy", split_c[1])
        np.save(outdir / "SPLIT_A_COVERAGE_N.npy", split_a[4])
        np.save(outdir / "SPLIT_C_COVERAGE_N.npy", split_c[4])
        np.save(outdir / "SPLIT_A_SATURATION_COUNT.npy", split_a[5])
        np.save(outdir / "SPLIT_C_SATURATION_COUNT.npy", split_c[5])
        z = ((split_a[0][::4, ::4] - split_c[0][::4, ::4])
             / np.sqrt(split_a[1][::4, ::4] + split_c[1][::4, ::4]))
        np.savez_compressed(outdir / "SPLIT_A_minus_C_z_ds4.npz", z=z.astype(np.float32))

    image, variance, random_variance, systematic_variance, coverage, saturation = full
    empirical_scale = np.ones(3, np.float32)
    if split is not None and "variance_scale_rgb" in split:
        empirical_scale = np.maximum(1.0, np.asarray(split["variance_scale_rgb"], np.float32))
        random_variance *= empirical_scale
        variance = random_variance + systematic_variance
    save_tiff(outdir / "MASTER_linear_float32_ADU_s.tif", image)
    np.save(outdir / "VARIANCE_ADU2_s2.npy", variance)
    np.save(outdir / "VARIANCE_RANDOM_ADU2_s2.npy", random_variance)
    np.save(outdir / "VARIANCE_SYSTEMATIC_FLAT_ADU2_s2.npy", systematic_variance)
    np.save(outdir / "COVERAGE_N.npy", coverage)
    np.save(outdir / "COVERAGE_EFFECTIVE_S.npy", coverage.astype(np.float32) * exposure)
    np.save(outdir / "SATURATION_COUNT.npy", saturation)
    np.save(outdir / "LUNAR_EXCLUSION_COUNT.npy", sum(
        (~item["lunar_valid"]).astype(np.uint16) for item in contributions))
    preview(outdir / "MASTER_preview_neutral.jpg", image)
    with (outdir / "TRANSFORMS.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(transform_rows[0]))
        writer.writeheader(); writer.writerows(transform_rows)

    # Sparse leave-one-out from stored per-frame numerator/weight.
    stride = 16
    full_small = image[::stride, ::stride]
    loo = []
    for excluded in contributions:
        subset = [x for x in contributions if x is not excluded]
        if not subset:
            loo.append({"frame": excluded["name"], "status": "ONLY_FRAME"})
            continue
        prepared_loo, loo_planes = prepare_subset(subset)
        loo_image = combine([{**x, "image": x["image"][::stride, ::stride],
                              "random_variance": x["random_variance"][::stride, ::stride],
                              "systematic_variance": x["systematic_variance"][::stride, ::stride],
                              "valid": x["valid"][::stride, ::stride],
                              "saturated": x["saturated"][::stride, ::stride]}
                             for x in prepared_loo])[0]
        delta = loo_image - full_small
        values = delta[np.all(np.isfinite(delta), axis=2)]
        if len(values) < 1000:
            loo.append({"frame": excluded["name"], "status": "INCONCLUSIVE",
                        "planes_recomputed_from_subset": loo_planes,
                        "common_pixels": int(len(values))})
            continue
        centre = np.median(values, axis=0)
        loo.append({"frame": excluded["name"], "status": "MEASURED",
                    "planes_recomputed_from_subset": loo_planes,
                    "delta_median_adu_s_rgb": centre.tolist(),
                    "delta_mad_adu_s_rgb": (1.4826 * np.median(np.abs(values - centre), axis=0)).tolist()})

    transform_by_name = {row["frame"]: row for row in transform_rows}
    inputs = []
    for name in names:
        path = DATA / f"{name}.ARW"
        registration_status = transform_by_name[name]["status"]
        decision = ("MODELLED_REGISTRATION_QUARANTINE"
                    if "QUARANTINE" in registration_status else "CANDIDATE_PENDING_QA")
        inputs.append({"name": name, "path": str(path), "bytes": path.stat().st_size,
                       "sha256": sha256(path),
                       "decision": decision,
                       "registration_status": registration_status})
    if "DSC06993" not in names:
        auxiliary = DATA / "DSC06993.ARW"
        inputs.append({"name": "DSC06993", "path": str(auxiliary),
                       "bytes": auxiliary.stat().st_size, "sha256": sha256(auxiliary),
                       "decision": "AUXILIARY_GEOMETRY_AIRMASS_REFERENCE_ONLY"})
    dark_dir = dark_root / f"{exposure:.10g}"
    inventory_root = Path("output/postprocessat_final_20260822/inventory_v2")
    calibrators = [
        dark_dir / "MASTER_DARK_raw_ADU.npy",
        dark_dir / "MASTER_DARK_VARIANCE_ADU2.npy",
        dark_dir / "HOT_PIXEL_MAP.npy", dark_dir / "DARK_RECEIPT.json",
        dark_dir / "SHA256SUMS.txt",
        flat_root / "flat_a7r3a_optical_rgb.npy",
        flat_root / "flat_a7r3a_optical_uncertainty_rgb.npy",
        flat_root / "FLAT_RECEIPT.json", flat_root / "SHA256SUMS.txt",
        WORK / "warpM.npy", WORK / "warpT.npy", WORK / "warpC.npy",
        WORK / "moon.pkl", WORK / "offsets6.pkl", WORK / "catalog_sony.txt",
        REGISTER_V3_PATH, XMATCH_SOLUTION, EPHEMERIS, Path(__file__).resolve(),
        inventory_root / "summary.json", inventory_root / "inventory.jsonl",
    ]
    has_modelled_registration = any(
        "QUARANTINE" in transform_by_name[name]["status"] for name in names)
    if segment == "combined":
        verdict = "COMBINED_SEGMENTS_CANDIDATE_PENDING_SPLIT_LOO_AND_VISUAL_NULL_REVIEW"
    elif len(names) == 1:
        verdict = "CALIBRATED_REGISTERED_SINGLE_FRAME_NO_STACK_GAIN_PENDING_QA"
    elif has_modelled_registration:
        verdict = "SEGMENT_STACK_MODELLED_REGISTRATION_PENDING_SPLIT_LOO_VISUAL_QA"
    else:
        verdict = "SEGMENT_STACK_PENDING_SPLIT_LOO_VISUAL_ACCEPTANCE"
    receipt = {
        "schema": "SONY_A7RIIIA_FE300_STACK_RECEIPT_S6_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "train": "SONY_A7RIIIA_FE300MM_F2.8_GM",
        "frame": "CORONA_SOLAR", "mount_segment": segment,
        "exposure_s": exposure,
        "members": names, "inputs": inputs, "rejected_global": REJECTED,
        "quarantine_global": QUARANTINE,
        "quarantine_in_group": {
            n: (QUARANTINE.get(n)
                or "registration is modelled from limb+ephemeris without a conclusive stellar OFF")
            for n in names
            if n in QUARANTINE or "QUARANTINE" in transform_by_name[n]["status"]
        },
        "calibration": "RGB derivative from linear CFA: exact ISO100/40C trimmed-mean dark, hot-pixel exclusion, random and systematic variance separated, smooth donor-body optical flat; no A7RIIIA PRNU claim",
        "registration": "per-frame heliocentric translation from measured lunar limb + DE440; stellar A-to-C similarity supplies rotation/scale; modelled linear geometry remains quarantined",
        "registration_authority": "solar-centre translation closes exactly by limb+DE440; validated stellar geometry is an independent rotation/scale check",
        "solar_radius_model": {"radius_px": SOLAR_RADIUS_PX,
                               "plate_scale_arcsec_px": PLATE_SCALE,
                               "authority": SOLAR_RADIUS_AUTHORITY},
        "lunar_gate": (f"fixed {LUNAR_EXCLUSION_RADIUS_NATIVE_PX:.1f} px native registration gate "
                       "for every exposure; the modelled physical lunar radius is about 302.9 px, "
                       "HDR validity is a separate downstream decision, and the apparent "
                       "deep-frame hole is diagnostic only"),
        "photometry": ("ADU/s normalized to DSC06993 airmass with Kasten-Young and "
                       f"k={K_EXTINCTION_MAG_AIRMASS:.3f} mag/airmass"),
        "sky": "global robust additive plane per channel on outer common field; applied globally; no radial boundary",
        "weighting": "inverse random variance only; shot term from locally smoothed expectation; donor-flat uncertainty propagated separately as fully correlated systematic",
        "split_independent": split, "leave_one_out": loo,
        "empirical_variance_scale_rgb": empirical_scale.tolist(),
        "qa": {"finite_fraction_rgb": [float(np.isfinite(image[..., c]).mean()) for c in range(3)],
               "coverage_median_rgb": [float(np.median(coverage[..., c])) for c in range(3)],
               "limb": limb},
        "calibrator_hashes": [{"path": str(p), "bytes": p.stat().st_size,
                               "sha256": sha256(p)} for p in calibrators],
        "verdict": verdict,
        "source_mutations": 0,
    }
    (outdir / "STACK_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    with (outdir / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for path in sorted(outdir.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                fh.write(f"{sha256(path)}  {path.name}\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dark-root", type=Path, required=True)
    parser.add_argument("--flat-root", type=Path, required=True)
    parser.add_argument("--segment", choices=("combined", "A", "C"),
                        default="combined",
                        help="do not combine mount segments after a failed A-C null")
    select = parser.add_mutually_exclusive_group(required=True)
    select.add_argument("--exposure", type=float)
    select.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    exposures = sorted(GROUPS)
    if args.exposure is not None:
        exposure = min(exposures, key=lambda x: abs(x - args.exposure))
        if abs(exposure - args.exposure) > 1e-8:
            raise SystemExit(f"exposure not found: {args.exposure}")
        exposures = [exposure]
    run = []
    for exposure in exposures:
        names = [name for name in GROUPS[exposure]
                 if args.segment == "combined" or group_name(name) == args.segment]
        if not names:
            continue
        receipt = process_group(exposure, names, args.out / exp_tag(exposure),
                                args.dark_root, args.flat_root, args.segment)
        group_receipt = args.out / exp_tag(exposure) / "STACK_RECEIPT.json"
        group_sums = args.out / exp_tag(exposure) / "SHA256SUMS.txt"
        run.append({"exposure_s": exposure, "n": len(names),
                    "path": exp_tag(exposure), "verdict": receipt["verdict"],
                    "receipt_sha256": sha256(group_receipt),
                    "group_sha256s_sha256": sha256(group_sums)})
    run_receipt = args.out / "RUN_RECEIPT.json"
    run_receipt.write_text(json.dumps({
        "schema": "SONY_A7RIIIA_FE300_S6_RUN_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).resolve()),
        "mount_segment": args.segment, "groups": run,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    with (args.out / "RUN_SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        fh.write(f"{sha256(run_receipt)}  RUN_RECEIPT.json\n")
        for row in run:
            for filename in ("STACK_RECEIPT.json", "SHA256SUMS.txt"):
                path = args.out / row["path"] / filename
                fh.write(f"{sha256(path)}  {row['path']}/{filename}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
