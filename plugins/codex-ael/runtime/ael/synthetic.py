"""Synthetic coronae with known truth, for tests, injections and demonstrations.

Nothing here ever enters a product made from real data.  The model is simple but has what the gates
need: a Baumbach radial profile, streamers, fine rays at fixed position angles, optional blobs that
move outwards, a dark Moon, a sky gradient, a Gaussian PSF and shot noise.
"""
from __future__ import annotations

import numpy as np

from .geometry import EclipseGeometry
from .filters import gaussian

__all__ = ["baumbach", "SyntheticScene", "render_scene"]


def baumbach(r_rsun):
    """Baumbach (1937) K+F corona brightness in units of the mean solar disc (valid ~1–4 R☉)."""
    r = np.maximum(np.asarray(r_rsun, np.float64), 1.0)
    return 1e-6 * (0.0532 * r ** -2.5 + 1.425 * r ** -7 + 2.565 * r ** -17)


class SyntheticScene:
    """A corona fixed on the Sun, with optional moving blobs.  Units: counts/s at the detector."""

    def __init__(self, sun_radius_px: float = 120.0, *, seed: int = 0, n_rays: int = 400,
                 streamers=((40.0, 18.0, 2.5), (130.0, 25.0, 1.8), (230.0, 15.0, 2.2), (300.0, 20.0, 1.5)),
                 blobs=(), limb_level: float = 2.0e5, sky_level: float = 300.0, sky_gradient=(0.15, -0.1),
                 moon_radius_px: float | None = None, north_deg: float = 0.0, psf_sigma_px: float = 1.1,
                 arcsec_per_px: float = 8.0):
        rng = np.random.default_rng(seed)
        self.R = float(sun_radius_px)
        self.moon_R = float(moon_radius_px if moon_radius_px is not None else 1.03 * sun_radius_px)
        self.streamers = [tuple(s) for s in streamers]
        self.ray_pa = rng.uniform(0, 360, n_rays)
        self.ray_w = rng.uniform(0.15, 0.9, n_rays)
        self.ray_a = rng.lognormal(-1.2, 0.6, n_rays)
        self.ray_r0 = rng.uniform(1.0, 1.6, n_rays)
        self.blobs = [dict(b) for b in blobs]      # dict(pa, r0_rsun, v_rsun_s, size_px, amp)
        self.limb_level = limb_level
        self.sky_level = sky_level
        self.sky_gradient = sky_gradient
        self.north_deg = north_deg
        self.psf = psf_sigma_px
        self.arcsec_per_px = arcsec_per_px

    def radiance(self, shape, sun_xy, moon_xy=None, t: float = 0.0, with_moon: bool = True):
        """Noise-free radiance image (counts/s) with the Sun at ``sun_xy`` at time ``t``."""
        h, w = shape
        geo = EclipseGeometry(shape=shape, sun_xy=sun_xy, sun_radius_px=self.R, moon_xy=moon_xy,
                              moon_radius_px=self.moon_R, north_deg=self.north_deg)
        r = geo.rsun_map().astype(np.float64)
        pa = geo.pa_map().astype(np.float64)
        prof = baumbach(r) / baumbach(1.0) * self.limb_level
        mod = np.ones_like(r)
        for pa0, width, amp in self.streamers:
            d = (pa - pa0 + 180) % 360 - 180
            mod += amp * np.exp(-0.5 * (d / width) ** 2) * np.clip((r - 1.0) / 0.5, 0, 1)
        rays = np.zeros_like(r)
        for pa0, wd, a, r0 in zip(self.ray_pa, self.ray_w, self.ray_a, self.ray_r0):
            d = (pa - pa0 + 180) % 360 - 180
            rays += a * np.exp(-0.5 * (d / wd) ** 2) * np.clip((r - r0 + 0.3) / 0.3, 0, 1)
        img = prof * mod * (1.0 + 0.6 * rays)
        yy, xx = np.mgrid[0:h, 0:w]
        for b in self.blobs:
            rb = (b["r0_rsun"] + b["v_rsun_s"] * t) * self.R
            a = np.radians(self.north_deg - b["pa"])   # image angle of the PA (not mirrored)
            bx, by = sun_xy[0] + rb * np.sin(a), sun_xy[1] - rb * np.cos(a)
            img += b["amp"] * baumbach(rb / self.R) / baumbach(1.0) * self.limb_level * np.exp(
                -0.5 * ((xx - bx) ** 2 + (yy - by) ** 2) / b["size_px"] ** 2)
        img[r < 1.0] = 0.0
        gx, gy = self.sky_gradient
        img += self.sky_level * (1 + gx * (xx - w / 2) / w + gy * (yy - h / 2) / h)
        if with_moon and moon_xy is not None:
            img[np.hypot(xx - moon_xy[0], yy - moon_xy[1]) <= self.moon_R] = self.sky_level * 0.02
        if self.psf > 0:
            img = gaussian(img.astype(np.float32), self.psf)
        return img.astype(np.float32)


def render_scene(scene: SyntheticScene, shape, sun_xy, moon_xy, t: float, exposure: float, *,
                 full_well: float = 15000.0, read_noise: float = 3.0, seed: int = 0,
                 sensor_dust: list | None = None):
    """Simulated calibrated frame (counts) and its saturation mask.

    ``sensor_dust``: list of (x, y, radius, depth) fixed on the sensor — they must come out as
    'sensor' motion, never as coronal.
    """
    rng = np.random.default_rng(seed)
    rad = scene.radiance(shape, sun_xy, moon_xy, t)
    sig = rad * exposure
    if sensor_dust:
        yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
        for x0, y0, rr, depth in sensor_dust:
            sig *= 1.0 - depth * np.exp(-0.5 * ((xx - x0) ** 2 + (yy - y0) ** 2) / rr ** 2)
    noisy = rng.poisson(np.clip(sig, 0, 1e9)).astype(np.float32) + rng.normal(0, read_noise, sig.shape).astype(np.float32)
    sat = sig >= full_well
    noisy[sat] = full_well
    return noisy, sat
