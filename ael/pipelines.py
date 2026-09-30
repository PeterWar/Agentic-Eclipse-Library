"""End-to-end pipelines: the three products, from your own data, with their gates and receipts.

* :func:`structure_from_linear` – a linear HDR composite (RGB or mono) → Druckmüller-style structure
  images (mono, cool-toned and measured-colour versions) with a receipt.
* :func:`polar_views` – any image → unrolled views around the Sun and around the Moon, labelled.
* :func:`motion_from_config` – calibrated RAW frames with times and Sun centres → epochs in the Sun
  frame, displacement vectors with every gate, a visual-check sheet and GIF/MP4 animations.

All three refuse to write a product whose gate fails, unless ``force=True`` (and then say so in the
receipt).  Everything here was first done by hand on the 2026 data (see ``3-RECERCA/tools/ael_2026``).
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from . import annotate, calibrate, gates, motion, polar, render
from . import io as aio
from .geometry import EclipseGeometry

__all__ = ["structure_from_linear", "polar_views", "motion_from_config", "demo_motion_synthetic"]


# ------------------------------------------------------------------------------------------------
# Structure images
# ------------------------------------------------------------------------------------------------
def structure_from_linear(data: np.ndarray, geometry: EclipseGeometry, out_dir: str | Path, *,
                          valid: np.ndarray | None = None, name: str = "structure", sky_r_min_rsun: float = 7.0,
                          sky_order: int = 2, params: dict | None = None, crop_height_rsun: float | None = 3.2,
                          styles=("mono", "cool", "measured"), tint=(0.62, 0.74, 1.0), force: bool = False) -> dict:
    """Linear composite → structure images.  ``data``: (H, W) or (H, W, 3) linear, sky included.

    Styles: 'mono' (grey), 'cool' (neutral corona, a declared cool tint growing outwards, prominences in
    their measured colour), 'measured' (the data's own colour, measured locally: e.g. a golden corona
    under a low Sun).  Returns a dict of written files and the gate results.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    a = np.asarray(data, np.float32)
    rgb = a if a.ndim == 3 else None
    lum = render.luminance(a) if a.ndim == 3 else a
    ok = np.isfinite(lum) if valid is None else (valid.astype(bool) & np.isfinite(lum))
    sky, sinfo = render.sky_background(lum, ok, geometry, r_min_rsun=sky_r_min_rsun, order=sky_order)
    p = dict(b_limb=0.68, b_slope=0.24, angular_gain=0.12, detail_amount=0.40, detail_gamma=0.6, wow_scales=9,
             noise_floor=3.0, noise_region_rsun=6.0)
    p.update(params or {})
    mono, parts = render.structure_image(lum, ok, geometry, sky=sky, return_parts=True, **p)
    g = gates.nothing_outside_data(mono, ok)
    if not g["passed"] and not force:
        raise RuntimeError(f"gate failed: {g}")
    files = {}
    rs = geometry.rsun_map()
    imgs = {"mono": np.repeat(mono[..., None], 3, axis=2)}
    if rgb is not None and ("cool" in styles or "measured" in styles):
        skyc = np.stack([render.sky_background(rgb[..., c], ok, geometry, r_min_rsun=sky_r_min_rsun, order=sky_order)[0]
                         for c in range(3)], -1)
        net = rgb - skyc
        ring = ok & (rs > 1.15) & (rs < 2.5)
        col = np.array([np.median(net[..., c][ring]) for c in range(3)])
        bal = net / (col / render.luminance(col[None, None, :].astype(np.float32))[0, 0]).astype(np.float32)
        wchr = render.chromosphere_weight(bal, ok, geometry, band_rsun=(0.95, 1.25), ratio_lo=1.25, ratio_hi=1.8)
        blur = lambda x: np.stack([cv2.GaussianBlur(np.nan_to_num(x[..., c]), (0, 0), 1.5) for c in range(3)], -1)
        if "cool" in styles:
            tw = np.clip((rs - 1.25) / 2.75, 0, 1).astype(np.float32) * 0.85
            imgs["cool"] = render.compose_color(mono, chroma_rgb=blur(bal), chroma_weight=wchr, tint=tint, tint_weight=tw)
        if "measured" in styles:
            loc = render.local_chromaticity(rgb, ok, 24.0)
            imgs["measured"] = render.compose_color(mono, chroma_rgb=blur(rgb), chroma_weight=wchr, corona_rgb=loc,
                                                    corona_color_strength=1.0)
    cx, cy = geometry.sun_xy
    geo_out = geometry
    if crop_height_rsun:
        H0, W0 = mono.shape
        h = min(int(round(2 * crop_height_rsun * geometry.sun_radius_px)), H0); w = min(int(round(h * 16 / 9)), W0)
        y0, x0 = max(0, int(round(cy - h / 2))), max(0, int(round(cx - w / 2)))
        y0, x0 = min(y0, H0 - h), min(x0, W0 - w)
        # the products are crops: write the geometry of the crop, so that polar views (and anyone) use the right centre
        geo_out = geometry.shifted(-x0, -y0, shape=(h, w))
    geo_file = out / f"{name}_geometry.json"
    geo_out.to_json(geo_file)
    files["geometry"] = str(geo_file)
    for st, im in imgs.items():
        if st not in styles:
            continue
        if crop_height_rsun:
            im = im[y0:y0 + h, x0:x0 + w]
        f = aio.save_tiff(out / f"{name}_{st}.tif", render.to_uint(im, 16),
                          description=f"Structure image ({st}); radial gradient compressed; detail from data only.")
        files[st] = str(f)
    rec = aio.write_receipt(out / f"{name}_RECEIPT.json", product="structure images", outputs=files,
                            parameters=dict(structure=p, sky=sinfo, styles=list(styles), tint=tint,
                                            floor=parts.get("floor"), noise_factors=parts.get("noise_factors")),
                            gates=dict(nothing_outside_data=g, forced=bool(force and not g["passed"])))
    return dict(files=files, receipt=str(rec), gate=g, mono=mono)


# ------------------------------------------------------------------------------------------------
# Polar views
# ------------------------------------------------------------------------------------------------
def polar_views(image01: np.ndarray, geometry: EclipseGeometry, out_dir: str | Path, *, valid: np.ndarray | None = None,
                name: str = "polar", r_max_rsun: float = 4.0, n_pa: int = 7200, centers=("sun", "moon"),
                panels_deg: float | None = 120.0) -> dict:
    """Unrolled views of a display image (values in [0, 1], mono or RGB).  Also writes panels of
    ``panels_deg`` degrees (a 120° panel of a 360° × 3 R☉ unroll is close to 16:9)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    a = np.asarray(image01, np.float32)
    files = {}
    R = geometry.sun_radius_px
    for c in centers:
        if c == "moon" and geometry.moon_xy is None:
            continue
        r0 = 0.95 * R if c == "sun" else 0.985 * geometry.moon_radius_px
        P = polar.to_polar(a, geometry, center=c, r_range=(r0, r_max_rsun * R), n_pa=n_pa, valid=valid)
        disp = np.nan_to_num(P.display(), nan=0.0)
        img8 = annotate.to_rgb8(disp)
        mb, ml = 40, 110
        canvas = np.zeros((img8.shape[0] + mb, img8.shape[1] + ml, 3), np.uint8)
        canvas[:img8.shape[0], ml:] = img8
        ticks = tuple(t for t in (1.0, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6) if t <= r_max_rsun)
        annotate.polar_axes(canvas, P, pa_ticks=range(0, 360, 30), rsun_ticks=ticks, size=26, margin_bottom=mb,
                            margin_left=ml)
        f = aio.save_png(out / f"{name}_{c}.png", canvas,
                         description=f"Unrolled corona around the {c}: x = position angle, y = distance from the centre.")
        files[c] = str(f)
        if panels_deg:
            n = int(round(360 / panels_deg))
            w = img8.shape[1] // n
            for k in range(n):
                pan = img8[:, k * w:(k + 1) * w]
                files[f"{c}_panel{k + 1}"] = str(aio.save_png(out / f"{name}_{c}_panel{k + 1}.png", pan))
    return dict(files=files)


# ------------------------------------------------------------------------------------------------
# Motion
# ------------------------------------------------------------------------------------------------
def _band(e, s1, s2):
    from .filters import normalized_gaussian
    m = e.valid & np.isfinite(e.data) & (e.data > 0)
    lg = np.where(m, np.log(np.where(m, e.data, 1.0)), np.nan).astype(np.float32)
    a = normalized_gaussian(lg, m, s1, 0.5) if s1 > 0 else lg
    return (a - normalized_gaussian(lg, m, s2, 0.5)).astype(np.float32)


def motion_from_config(config: str | Path | dict, out_dir: str | Path) -> dict:
    """Coronal-motion analysis and animation from a JSON config (see ``examples/motion_config.json``).

    Config keys: ``frames`` (list of {path, t, exposure, sun_xy, moon_xy?}), ``epochs`` (dict name →
    list of frame paths, in time order), ``dark`` (dict exposure → master path) or ``pedestal``,
    ``flat`` (path, optional), ``prnu`` (path, optional, same geometry as the RAW), ``white``,
    ``pedestal``, ``sun_radius_px``, ``moon_radius_px``, ``arcsec_per_px``, ``north_deg``,
    ``canvas`` [h, w], ``pairs`` (A and B: [start epoch(s), end epoch(s)] with no frame in common),
    ``nulls`` (two [epoch, epoch] pairs a few seconds apart), ``band_px`` [2, 12], ``r_range_rsun``.
    """
    cfg = json.loads(Path(config).read_text()) if not isinstance(config, dict) else config
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    H, W = cfg.get("canvas", [3000, 3000])
    ref = (W / 2, H / 2)
    geo_t = EclipseGeometry(shape=(H, W), sun_xy=ref, sun_radius_px=cfg["sun_radius_px"],
                            moon_radius_px=cfg.get("moon_radius_px"), north_deg=cfg.get("north_deg", 0.0),
                            arcsec_per_px=cfg.get("arcsec_per_px"))
    flat = calibrate.load_calibration_frame(cfg["flat"]) if cfg.get("flat") else None
    if cfg.get("prnu"):
        pr = calibrate.load_calibration_frame(cfg["prnu"])
        flat = pr if flat is None else flat * pr
    darks = {float(k): v for k, v in (cfg.get("dark") or {}).items()}
    fr_by = {f["path"]: f for f in cfg["frames"]}

    def load(fr):
        info = calibrate.read_raw(fr["path"], full=cfg.get("full_raw", True))
        sat = calibrate.saturation_mask(info["bayer"], cfg.get("white", 16383), cfg.get("pedestal", 0.0), cfg.get("linear_frac", 0.85))
        if darks:
            k = min(darks, key=lambda e: abs(np.log(e / fr["exposure"])))
            dk = calibrate.load_calibration_frame(darks[k])
        else:
            dk = cfg.get("pedestal", 0.0)
        c = calibrate.calibrate(info["bayer"], dk, flat)
        g, bad = calibrate.green_plane(c, info["pattern"], sat)
        return motion.Frame(name=Path(fr["path"]).name, t=fr["t"], exposure=fr["exposure"], sun_xy=tuple(fr["sun_xy"]),
                            moon_xy=tuple(fr["moon_xy"]) if fr.get("moon_xy") else None,
                            data=np.where(bad, np.nan, g).astype(np.float32), saturated=bad)

    E = {}
    for nm, paths in cfg["epochs"].items():
        E[nm] = motion.merge_epoch([load(fr_by[p]) for p in paths], ref, (H, W), geo_t, name=nm)
    names = list(cfg["epochs"])
    phot = motion.match_epochs([E[n] for n in names], ref=0, ring_rsun=tuple(cfg.get("match_ring_rsun", (1.1, 2.0))))

    def combo(lst):
        eps = [E[n] for n in (lst if isinstance(lst, list) else [lst])]
        if len(eps) == 1:
            return eps[0]
        num = np.zeros((H, W)); den = np.zeros((H, W))
        for e in eps:
            num[e.valid] += e.data[e.valid]; den[e.valid] += 1
        v = den > 0
        return motion.Epoch(name="+".join(x.name for x in eps), t=float(np.mean([x.t for x in eps])),
                            t_min=min(x.t_min for x in eps), t_max=max(x.t_max for x in eps),
                            data=np.where(v, num / np.maximum(den, 1), np.nan).astype(np.float32), valid=v,
                            geometry=eps[0].geometry, moon_xy=sum([list(x.moon_xy) for x in eps], []),
                            members=sum([x.members for x in eps], []))

    s1, s2 = cfg.get("band_px", [2.0, 12.0])
    yy, xx = np.mgrid[0:H, 0:W]
    ex = np.zeros((H, W), bool)
    for e in E.values():
        for (mx, my) in e.moon_xy:
            ex |= np.hypot(xx - mx, yy - my) <= (cfg.get("moon_radius_px") or 0) + cfg.get("moon_margin_px", 15)
    kw = dict(window=cfg.get("window", 61), step=cfg.get("step", 20), search=cfg.get("search", 26),
              r_range_rsun=tuple(cfg.get("r_range_rsun", (1.1, 2.2))), exclude=ex, min_peak=cfg.get("min_peak", 0.6))
    hp = {}
    def band(e):
        if e.name not in hp:
            hp[e.name] = _band(e, s1, s2)
        return hp[e.name]
    mv = lambda a, b: motion.measure_displacements(band(a), band(b), np.isfinite(band(a)), np.isfinite(band(b)), geo_t, **kw)
    A = [combo(x) for x in cfg["pairs"]["A"]]; B = [combo(x) for x in cfg["pairs"]["B"]]
    shared = set(A[0].members + A[1].members) & set(B[0].members + B[1].members)
    if shared:
        raise ValueError(f"pairs A and B share frames {sorted(shared)}: the second testimony would not be independent")
    n0, n1 = [mv(combo(a), combo(b)) for a, b in cfg["nulls"]]
    vA, vB = mv(*A), mv(*B)
    dtA, dtB = A[1].t - A[0].t, B[1].t - B[0].t
    afA = motion.fit_global_affine(vA, ref, classes=("",)); motion.fit_global_affine(vB, ref, classes=("",))
    noise = max(motion.null_noise(n0)["sigma"], motion.null_noise(n1)["sigma"])
    sv, mvv = tuple(cfg["sensor_velocity_px_s"]), tuple(cfg["moon_velocity_px_s"]) if cfg.get("moon_velocity_px_s") else None
    cls = motion.classify(vA, dtA, sensor_velocity=sv, moon_velocity=mvv, noise_px=noise, min_iso=cfg.get("min_iso", 0.3))
    motion.classify(vB, dtB, sensor_velocity=sv, moon_velocity=mvv, noise_px=noise, min_iso=cfg.get("min_iso", 0.3))
    lim = max(1.5, 3 * noise)
    motion.confirm(vA, dtA, null_vecs=n0, null_max_px=lim)
    conf = motion.confirm(vA, dtA, null_vecs=n1, null_max_px=lim, mid_vecs=vB, dt_mid=dtB, tol_px=1.0, tol_frac=0.25)
    sheet = motion.candidate_sheet(vA, {"A0": band(A[0]), "A1": band(A[1]), "B0": band(B[0]), "B1": band(B[1])})
    aio.save_png(out / "candidates_visual_check.png", sheet)
    # animation of the real epochs (band-pass display, same gain for all)
    rs = geo_t.rsun_map()
    b0 = _band(E[names[0]], 1.0, 8.0)
    gain = 0.5 / float(np.nanpercentile(np.abs(b0[(rs > 1.05) & (rs < 1.6)]), 99.5))
    frames = []
    for n in names:
        d = motion.to_display(_band(E[n], 1.0, 8.0), gain)
        img = annotate.to_rgb8(d)
        annotate.draw_text(img, f"t = {E[n].t:.0f} s", (20, img.shape[0] - 50), size=34)
        frames.append(img)
    dur = [900] + [450] * (len(frames) - 1)
    aio.save_gif(out / "motion_epochs.gif", frames, dur)
    aio.save_mp4(out / "motion_epochs.mp4", frames, dur)
    kmpx = motion.km_per_px(cfg.get("arcsec_per_px", 1.0), cfg.get("sun_distance_au", 1.0))
    cand = [dict(x=v.x, y=v.y, r_rsun=v.r_rsun, residual_px=[v.rdx, v.rdy], km_s=float(np.hypot(v.rdx, v.rdy) * kmpx / dtA),
                 peak=v.peak, iso=v.iso) for v in vA if v.cls == "coronal"]
    res = dict(epochs={n: dict(t=E[n].t, members=E[n].members) for n in names}, photometry=phot, dt_s=dtA,
               dt_independent_s=dtB, global_affine=afA, null_noise_px=noise, detection_limit_px=lim,
               detection_limit_km_s=lim * kmpx / dtA, classes=cls, confirmation=conf, candidates=cand,
               note="Candidates must be checked by eye on candidates_visual_check.png before any claim.")
    aio.write_receipt(out / "MOTION_RECEIPT.json", product="coronal motion analysis", parameters=res,
                      outputs=dict(gif=str(out / "motion_epochs.gif"), sheet=str(out / "candidates_visual_check.png")),
                      hash_inputs=False)
    return res


# ------------------------------------------------------------------------------------------------
# Synthetic demonstration (known truth)
# ------------------------------------------------------------------------------------------------
def demo_motion_synthetic(out_dir: str | Path, seed: int = 5) -> dict:
    """What the motion products look like when there *is* motion: a synthetic eclipse (Sun radius 60 px)
    with a blob moving outwards by 7.7 px in 80 s, dust fixed on the sensor and a Moon crossing.  The
    animation marks the confirmed vectors; the dust and the Moon's limb must never be marked."""
    from .synthetic import SyntheticScene, render_scene
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    shape = (360, 440); R = 60.0
    v_sun = np.array([0.10, -0.08]); v_moon = np.array([-0.15, -0.05])
    sc = SyntheticScene(R, seed=seed, moon_radius_px=61.5, psf_sigma_px=1.2, n_rays=500,
                        blobs=[dict(pa=60.0, r0_rsun=1.45, v_rsun_s=0.0016, size_px=2.2, amp=4.0)])
    s0, m0 = np.array([220.0, 180.0]), np.array([226.0, 182.0])
    dust = [(170.0, 120.0, 3.0, 0.25), (265.0, 245.0, 2.5, 0.3)]
    frames = []
    k = 0
    for t0 in (0.0, 5.0, 40.0, 80.0):
        for i, e in enumerate((0.002, 0.008, 0.032, 0.128)):
            t = t0 + 0.9 * i
            d, sat = render_scene(sc, shape, tuple(s0 + v_sun * t), tuple(m0 + (v_sun + v_moon) * t), t, e, seed=100 + k,
                                  sensor_dust=dust)
            frames.append(motion.Frame(f"f{k}", t, e, tuple(s0 + v_sun * t), tuple(m0 + (v_sun + v_moon) * t), d, sat))
            k += 1
    geo = EclipseGeometry(shape=shape, sun_xy=tuple(s0), sun_radius_px=R, moon_radius_px=61.5)
    groups = motion.group_epochs(frames, max_gap=1.5)
    E = [motion.merge_epoch(g, tuple(s0), shape, geo, name=f"E{i}") for i, g in enumerate(groups)]
    motion.match_epochs(E, ref=0, ring_rsun=(1.1, 1.8))
    hp = [motion.highpass(e.data, e.valid, sigma=4.0) for e in E]
    kw = dict(window=21, step=6, search=12, r_range_rsun=(1.12, 1.9))
    null = motion.measure_displacements(hp[0], hp[1], E[0].valid, E[1].valid, geo, **kw)
    vec = motion.measure_displacements(hp[0], hp[3], E[0].valid, E[3].valid, geo, **kw)
    mid = motion.measure_displacements(hp[0], hp[2], E[0].valid, E[2].valid, geo, **kw)
    dt = E[3].t - E[0].t
    motion.classify(vec, dt, sensor_velocity=tuple(-v_sun), moon_velocity=tuple(v_moon), noise_px=motion.null_noise(null)["sigma"])
    motion.confirm(vec, dt, null_vecs=null, mid_vecs=mid, dt_mid=E[2].t - E[0].t)
    cor = [v for v in vec if v.cls == "coronal"]
    gain = 0.5 / float(np.nanpercentile(np.abs(hp[0][np.isfinite(hp[0])]), 99.5))
    imgs = []
    for e, h in zip(E, hp):
        img = annotate.to_rgb8(cv2.resize(motion.to_display(h, gain), (shape[1] * 3, shape[0] * 3), interpolation=cv2.INTER_CUBIC))
        for v in cor:
            u = np.array([v.dx, v.dy]) / max(np.hypot(v.dx, v.dy), 1e-9)
            tip = np.array([v.x, v.y]) * 3 - u * 12
            annotate.draw_arrow(img, tip - u * 40, tip, color=(255, 255, 255), width=3)
        annotate.draw_text(img, "SYNTHETIC TEST DATA", (12, 10), size=24, color=(255, 210, 90))
        annotate.draw_text(img, f"t = {e.t:.0f} s", (12, img.shape[0] - 44), size=28)
        imgs.append(img)
    aio.save_gif(out / "demo_motion_synthetic.gif", imgs, [700, 450, 450, 450])
    return dict(n_coronal=len(cor), vectors=[(v.x, v.y, v.dx, v.dy) for v in cor], gif=str(out / "demo_motion_synthetic.gif"))
