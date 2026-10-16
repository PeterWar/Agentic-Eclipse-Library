"""End-to-end pipelines: the three products, from your own data, with their gates and receipts.

* :func:`structure_from_linear` – a linear HDR composite (RGB or mono) → Druckmüller-style structure
  images (mono, cool-toned and measured-colour versions) with a receipt.
* :func:`polar_views` – any image → unrolled views around the Sun and around the Moon, labelled.
* :func:`motion_from_config` – calibrated RAW frames with times and Sun centres → epochs in the Sun
  frame, displacement vectors with every gate, a visual-check sheet and GIF/MP4 animations.
* :func:`motion_gif` – epochs (one or two instruments) → the motion GIF in the reference look (band-pass grey,
  common noise filter, real epochs only), built so that it has **no waves**: the same recipe at every radius
  and the same grain in every frame, checked by two gates (see :mod:`ael.animation`).

All three refuse to write a product whose gate fails, unless ``force=True`` (and then say so in the
receipt).  Everything here was first done by hand on the 2026 data (see ``3-RECERCA/tools/ael_2026``).
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from . import animation, annotate, calibrate, gates, motion, polar, render
from . import io as aio
from .geometry import EclipseGeometry

__all__ = ["structure_from_linear", "polar_views", "motion_from_config", "motion_gif", "demo_motion_synthetic"]


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
    Optional ``gif`` {``feather_px`` (60), ``out_size`` [1320, 1044], ``rsun_out_px`` (242), ``rotation_deg`` (0),
    ``labels``, ``force``}: also writes the motion GIF without waves (:func:`motion_gif`), with every epoch given the
    grain of the noisiest one through the same epoch without its longest exposure.
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

    gcfg = cfg.get("gif")
    E, Ef, Es = {}, {}, {}
    for nm, paths in cfg["epochs"].items():
        fl = [load(fr_by[p]) for p in paths]
        E[nm] = motion.merge_epoch(fl, ref, (H, W), geo_t, name=nm)
        if gcfg:
            fp = float(gcfg.get("feather_px", 60))
            Ef[nm] = motion.merge_epoch(fl, ref, (H, W), geo_t, name=nm, feather_px=fp)
            longest = max(fl, key=lambda f: f.exposure)
            sub = [f for f in fl if f is not longest]
            Es[nm] = motion.merge_epoch(sub, ref, (H, W), geo_t, name=nm, feather_px=fp) if sub else Ef[nm]
        del fl
    names = list(cfg["epochs"])
    phot = motion.match_epochs([E[n] for n in names], ref=0, ring_rsun=tuple(cfg.get("match_ring_rsun", (1.1, 2.0))))
    gif_res = None
    if gcfg:
        phf = motion.match_epochs([Ef[n] for n in names], ref=0, ring_rsun=tuple(cfg.get("match_ring_rsun", (1.1, 2.0))))
        for n, ab in zip(names, phf):
            if Es[n] is not Ef[n]:
                Es[n].data = ((Es[n].data - ab["b"]) / ab["a"]).astype(np.float32)
        gif_res = motion_gif([Ef[n] for n in names], out / "gif", noisier=[Es[n].data for n in names],
                             labels=gcfg.get("labels"), rotation_deg=float(gcfg.get("rotation_deg", 0.0)),
                             out_size=tuple(gcfg.get("out_size", (1320, 1044))), rsun_out_px=float(gcfg.get("rsun_out_px", 242.0)),
                             force=bool(gcfg.get("force", False)), name="motion_gif")
        del Ef, Es

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
               motion_gif=None if gif_res is None else dict(files=gif_res["files"], gates=gif_res["gates"]),
               dt_independent_s=dtB, global_affine=afA, null_noise_px=noise, detection_limit_px=lim,
               detection_limit_km_s=lim * kmpx / dtA, classes=cls, confirmation=conf, candidates=cand,
               note="Candidates must be checked by eye on candidates_visual_check.png before any claim.")
    aio.write_receipt(out / "MOTION_RECEIPT.json", product="coronal motion analysis", parameters=res,
                      outputs=dict(gif=str(out / "motion_epochs.gif"), sheet=str(out / "candidates_visual_check.png")),
                      hash_inputs=False)
    return res


# ------------------------------------------------------------------------------------------------
# Motion GIF without waves
# ------------------------------------------------------------------------------------------------
def motion_gif(epochs: list, out_dir: str | Path, *, noisier: list | None = None, extras: list | None = None,
               extras_window_rsun: tuple | None = None, noise_pairs: list | None = None, zones: list | None = None,
               zones_space: str = "output", K: float = 2.2, out_size=(1320, 1044), rsun_out_px: float = 242.0,
               rotation_deg: float = 0.0, labels: list | None = None, footer: str | None = None,
               hold_ms: int = 700, step_ms: int = 220, name: str = "motion", force: bool = False,
               scale: float | None = None) -> dict:
    """The coronal-motion GIF in the reference look, without waves (see :mod:`ael.animation`).

    ``epochs``: :class:`ael.motion.Epoch` on one canvas (Sun at the same point), photometrically matched
    (:func:`ael.motion.match_epochs`), ideally merged with ``feather_px`` (≈30 px of the canvas).
    ``noisier``: optional, one array per epoch — the same epoch made from a subset of its frames (e.g. without its
    longest exposure): every epoch then gets the grain of the noisiest one.
    ``extras``: optional, one list per epoch of ``(image, usable_mask)`` from a second instrument, already on the
    canvas and matched; they add fine detail only, beyond ``extras_window_rsun`` (default: from the radius where
    all of them are free of saturation, 0.5 R☉ wide).
    ``noise_pairs``: epoch index pairs a few seconds apart (default: neighbours closer than 10 s).
    ``zones``: places of confirmed change (e.g. from :func:`ael.animation.two_site_change`), drawn as radial arrows.
    ``scale``: multiplies every scale in pixels (detail bands, grain windows, feathers).  The defaults were
    validated at 4.3″/px (2026, superpixels); by default ``scale = 4.3 / geometry.arcsec_per_px`` (≥ 1), so the
    same arcsecond scales are used at any pixel size.
    Refuses to write if a gate fails, unless ``force``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    geo = epochs[0].geometry
    if scale is None:
        scale = max(1.0, 4.3 / geo.arcsec_per_px) if geo.arcsec_per_px else 1.0
    k = float(scale)
    det = lambda img, g: animation.display_detail(img, g, fine=(0.7 * k, 4.0 * k), coarse=(1.3 * k, 6.0 * k))
    eqkw = dict(detail=det, fine_px=1.4 * k, window_px=15.0 * k, hp_px=10.0 * k, smooth_px=3.0 * k)
    data = [np.asarray(e.data, np.float32) for e in epochs]
    report = {"scale": k}
    if noisier is not None:
        data, report["grain_epochs"] = animation.equalize_fine_grain(data, [np.asarray(x, np.float32) for x in noisier], geo, **eqkw)
    if extras is not None:
        usable = [u for ex in extras for (_, u) in ex]
        if extras_window_rsun is None:
            r0 = max(r for r in animation.saturation_free_radius(usable, geo) if np.isfinite(r)) + 0.03
            extras_window_rsun = (r0, r0 + 0.5)
        comb = []
        for base, ex in zip(data, extras):
            wb = animation.feather(np.isfinite(base), 0) / animation.ring_noise(base, geo, fine_px=1.5 * k) ** 2
            ws = [(img, animation.feather(u, 12 * k) / animation.ring_noise(np.where(u, img, np.nan), geo, fine_px=1.5 * k) ** 2)
                  for img, u in ex]
            comb.append(animation.add_fine_detail(base, wb, ws, geo, window_rsun=extras_window_rsun, fine_px=15.0 * k)[0])
        data, report["grain_combined"] = animation.equalize_fine_grain(comb, data, geo, **eqkw)
        report["extras_window_rsun"] = list(extras_window_rsun)
    details = [det(x, geo) for x in data]
    moons = [tuple(np.mean(e.moon_xy, axis=0)) if len(e.moon_xy) else geo.moon_xy for e in epochs]
    if geo.moon_radius_px and all(m is not None for m in moons):
        details = animation.uniform_moon_edge(details, moons, geo.moon_radius_px, geo)
    if noise_pairs is None:
        noise_pairs = [(i, i + 1) for i in range(len(epochs) - 1) if abs(epochs[i + 1].t - epochs[i].t) < 10.0] or \
                      [(i, i + 1) for i in range(len(epochs) - 1)]
    flt = animation.common_noise_filter(details, geo, noise_pairs)
    frames = animation.render_frames(details, geo, flt, K=K, moon_xy=moons, moon_radius_px=geo.moon_radius_px,
                                     out_size=out_size, rsun_out_px=rsun_out_px, rotation_deg=rotation_deg)
    W, H = out_size
    geo_out = EclipseGeometry(shape=(H, W), sun_xy=(W / 2, H / 2), sun_radius_px=rsun_out_px)
    valid = np.all([f > 0.02 for f in frames], axis=0)
    g1 = gates.grain_uniformity(frames, geo_out, valid=valid)
    g2 = gates.no_concentric_bands(frames, geo_out, valid=valid)
    passed = g1["passed"] and g2["passed"]
    if not passed and not force:
        raise RuntimeError(f"motion GIF gates failed (waves): grain {g1['worst_ratio']:.2f} (tol {g1['tol']}), "
                           f"bands {g2['worst_sigma']:.2f}σ at {g2['worst_r']} R☉ (tol {g2['tol_sigma']})")
    if zones and zones_space == "canvas":
        M = animation.output_matrix(geo, out_size, rsun_out_px, rotation_deg)
        zones = [dict(z, x=float(M[0] @ [z["x"], z["y"], 1.0]), y=float(M[1] @ [z["x"], z["y"], 1.0])) for z in zones]
    from . import CREDIT
    imgs, files = [], {}
    for i, (f, e) in enumerate(zip(frames, epochs)):
        img = annotate.to_rgb8(f)
        if zones:
            animation.draw_zone_arrows(img, zones, (W / 2, H / 2))
        annotate.draw_text(img, labels[i] if labels else f"t = {e.t:.0f} s", (22, 16), size=30)
        annotate.draw_text(img, footer if footer is not None else CREDIT, (W - 14, H - 12), size=15, anchor="rd",
                           color=(225, 225, 225))
        imgs.append(img)
        files[f"frame_{i + 1}"] = str(aio.save_png(out / f"{name}_frame_{i + 1}.png", img))
    seq = imgs + imgs[-2:0:-1]
    n = len(imgs)
    dur = [hold_ms] + [step_ms] * (n - 2) + [hold_ms] + [step_ms] * (n - 2)
    files["gif"] = str(aio.save_gif(out / f"{name}.gif", seq, dur[:len(seq)]))
    mp4 = aio.save_mp4(out / f"{name}.mp4", seq * 3, (dur[:len(seq)]) * 3)
    if mp4:
        files["mp4"] = str(mp4)
    rec = aio.write_receipt(out / f"{name}_RECEIPT.json", product="coronal motion GIF (same recipe, same grain)",
                            outputs=files, parameters=dict(K=K, out_size=list(out_size), rsun_out_px=rsun_out_px,
                                                           rotation_deg=rotation_deg, noise_pairs=noise_pairs,
                                                           noise_filter={k: v for k, v in flt.items() if k != "G0"},
                                                           G0=flt["G0"], epochs=[dict(name=e.name, t=e.t) for e in epochs],
                                                           zones=zones or [], report=report),
                            gates=dict(grain_uniformity=g1, no_concentric_bands=g2, forced=bool(force and not passed)),
                            notes="Arrows mark places where two independent series see the same change; they do not "
                                  "show a direction and cannot tell motion from a change of brightness.",
                            hash_inputs=False)
    return dict(files=files, receipt=str(rec), gates=dict(grain_uniformity=g1, no_concentric_bands=g2),
                noise_filter=flt, report=report, frames=frames)


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
