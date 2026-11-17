"""Synthetic coronae with known truth, for tests, injections and demonstrations.

Nothing here ever enters a product made from real data.  The model is simple but has what the gates
need: a Baumbach radial profile, streamers, fine rays at fixed position angles, optional blobs that
move outwards, a dark Moon, a sky gradient, a Gaussian PSF and shot noise.
"""
from __future__ import annotations

import numpy as np

from .geometry import EclipseGeometry
from .filters import gaussian

__all__ = ["baumbach", "SyntheticScene", "render_scene", "inner_scene"]


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


def inner_scene(sun_radius_px: float = 220.0, *, shape=(1000, 1000), moon_offset_px=(7.0, 0.5), moon_ratio: float = 1.03,
                colour=(1.15, 1.0, 0.80), noise: float = 0.004, seed: int = 3, rim: float = 0.35, beads: int = 3):
    """A colour corona next to the Moon **with the truth known**, to judge a map of the inner limit
    (:func:`ael.zones.inner_zones`) without anybody's eye (since 1.5.0).

    What it holds, all of it declared and none of it ever part of a product:

    * a golden corona (Baumbach profile, streamers and fine rays; one colour everywhere, as under a low Sun);
    * a **prominence arch** with a **pocket of pure corona inside it**, a compact prominence and a thin chromosphere
      along part of the limb: red light (with a little blue and next to no green) added to the corona;
    * ``beads`` blue-white points on the limb;
    * a **white rim** (``rim`` of the brightness in the first pixel, falling over about two) along the half of the limb
      where the Moon does not hide the base of the Sun;
    * the Moon off the Sun's centre, a Gaussian PSF and noise of ``noise`` per channel.

    Returns ``(rgb, valid, geometry, truth)``; ``truth`` has boolean maps: ``emission_core`` (the red light is 8 % of
    the pixel or more, clearly inside the 5 % share that defines the core), ``corona`` (the light that is not corona
    is below 1 %, and the pixel is neither rim, bead nor edge: a map must leave these to the filters), ``pocket`` (the
    corona enclosed by the arch), ``rim``, ``beads``, and the noise-free ``share`` of non-coronal light."""
    rng = np.random.default_rng(seed)
    h, w = shape; R = float(sun_radius_px)
    sun = (w / 2.0, h / 2.0); moon = (sun[0] + moon_offset_px[0], sun[1] + moon_offset_px[1]); mr = moon_ratio * R
    geo = EclipseGeometry(shape=shape, sun_xy=sun, sun_radius_px=R, moon_xy=moon, moon_radius_px=mr)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dmoon = np.hypot(xx - moon[0], yy - moon[1]) - mr
    ang = np.degrees(np.arctan2(yy - moon[1], xx - moon[0])) % 360
    # the corona: every factor smooth in radius (a kink at one radius would be a real ring around the Sun)
    rs = np.maximum(np.hypot(xx - sun[0], yy - sun[1]) / R, 0.9); pa = np.degrees(np.arctan2(yy - sun[1], xx - sun[0])) % 360
    onset = 1 - np.exp(-np.maximum(rs - 1, 0) / 0.35)
    mod = np.ones(shape)
    for pa0, width, amp in ((40.0, 18.0, 2.5), (130.0, 25.0, 1.8), (230.0, 15.0, 2.2), (300.0, 20.0, 1.5)):
        mod += amp * np.exp(-.5 * (((pa - pa0 + 180) % 360 - 180) / width) ** 2) * onset
    rays = np.zeros(shape)
    # rays at least a few pixels wide everywhere: a ray thinner than a pixel is sampled differently by every annulus,
    # and any filter with statistics per annulus then draws real rings (the gramophone gate finds them)
    for pa0, wd, amp in zip(rng.uniform(0, 360, 160), rng.uniform(1.0, 3.5, 160), rng.lognormal(-1.2, 0.6, 160)):
        rays += amp * np.exp(-.5 * (((pa - pa0 + 180) % 360 - 180) / wd) ** 2)
    lum = 2.0e5 * baumbach(rs) / baumbach(1.0) * mod * (1.0 + 0.6 * rays * onset)
    # the reference level of the emission: the corona's brightness just above the limb
    lev = float(np.median(lum[(dmoon > 2) & (dmoon < 6)]))
    em = np.zeros(shape)

    def at(angle_deg, height):                              # a point at `height` px above the Moon's limb
        t = np.radians(angle_deg); return moon[0] + (mr + height) * np.cos(t), moon[1] + (mr + height) * np.sin(t)
    # an arch: an elliptical ring standing on the limb at 180° (left), 0.2 R☉ high, with a hollow of pure corona
    cx, cy = at(180.0, 0.0); a_out, b_out = 0.20 * R, 0.14 * R; t_ring = max(0.012 * R, 1.5)
    u = (xx - cx) / a_out; v = (yy - cy) / b_out; rr = np.hypot(u, v)
    ring = np.exp(-.5 * ((rr - 1) * min(a_out, b_out) / t_ring) ** 2)
    em += 6.0 * lev * ring
    pocket_geom = (rr < 0.62) & (dmoon > 0.04 * R)
    # a compact prominence at 250°, a small one at 40°
    for angle, hgt, size, amp in ((250.0, 0.035 * R, 0.022 * R, 5.0), (40.0, 0.02 * R, 0.014 * R, 2.5)):
        px, py = at(angle, hgt); em += amp * lev * np.exp(-.5 * ((xx - px) ** 2 + (yy - py) ** 2) / size ** 2)
    # chromosphere: a thin red layer on the limb between 120° and 300°
    arc = (np.clip((ang - 120) / 15, 0, 1) * np.clip((300 - ang) / 15, 0, 1))
    em += 3.0 * lev * arc * np.exp(-np.maximum(dmoon, 0) / (0.006 * R))
    col = np.asarray(colour, np.float64)
    rgb = lum[..., None] * col[None, None, :]
    rgb[..., 0] += em; rgb[..., 2] += 0.25 * em; rgb[..., 1] += 0.01 * em
    # the white rim (no colour of its own), where the Moon is not ahead of the Sun's limb: the left half here
    rim_arc = np.clip((ang - 100) / 20, 0, 1) * np.clip((330 - ang) / 20, 0, 1)
    rim_gain = rim * rim_arc * np.exp(-np.maximum(dmoon, 0) / 1.3)
    rgb *= (1 + rim_gain)[..., None]
    # beads: blue-white points right on the limb
    bead = np.zeros(shape)
    for angle in np.linspace(205.0, 235.0, max(int(beads), 0)):
        px, py = at(angle, 1.2); bead += np.exp(-.5 * ((xx - px) ** 2 + (yy - py) ** 2) / 0.9 ** 2)
    rgb += (25.0 * lev * bead)[..., None] * np.array([1.0, 1.0, 1.25])[None, None, :]
    clean_lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2])
    share = (1.24 * em * (1 + rim_gain)) / np.maximum(clean_lum, 1e-30)      # red + blue light that is not corona
    for c in range(3):
        rgb[..., c] = gaussian(rgb[..., c].astype(np.float32), 1.0)
    share = gaussian(share.astype(np.float32), 1.0).astype(np.float64)
    rgb = rgb * (1 + noise * rng.standard_normal(rgb.shape))
    valid = dmoon > 0
    rgb[~valid] = np.nan
    bead_t = (gaussian(bead.astype(np.float32), 1.0) * 25.0 * lev > 2.0 * gaussian(lum.astype(np.float32), 1.0)) & valid
    rim_t = (rim_gain >= 0.10) & valid
    edge = valid & (dmoon < 1.6)
    truth = dict(emission_core=(share >= 0.08) & valid, share=np.where(valid, share, np.nan).astype(np.float32),
                 rim=rim_t, beads=bead_t,
                 corona=valid & (share < 0.01) & ~rim_t & ~bead_t & ~edge & (rim_gain < 0.03)
                        & (gaussian(bead.astype(np.float32), 2.0) < 1e-3),
                 pocket=pocket_geom & valid & (share < 0.01))
    return rgb.astype(np.float32), valid, geo, truth
