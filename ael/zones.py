"""The inner limit of the corona filters: what is corona and what is not, decided by the data, pixel by pixel.

Detail filters (NRGF, RHEF, MGN, ACHF, WOW…) were made for the corona. On the lunar limb they draw rims and dotted
lines, and on a prominence or a Baily's bead they saturate and ring, whatever the operator. So every filter needs an
inner limit, and it must be the *same* for all of them: when each operator keeps its own rule, each layer starts at a
different place and the differences show.

:func:`inner_zones` makes that one map from the colour and the brightness of the data:

* **emission** (chromosphere and prominences): H-alpha makes it redder than the corona of the same sector;
* **Baily's beads**: single pixels several times brighter than the corona of their arc, or blue-white;
* **the lunar limb**: the pixel at the edge of the data and its **white rim** — where the Moon does not hide the base
  of the Sun, light of the limb scattered by the optics leaves a rim one to three pixels wide that is not red, so colour
  does not see it; it is found by its brightness against the trend of the corona of the same angle.

Two rules come from the author's 2026 image, where a person judged every version of this map by eye:

1. **No margin, no feather, no closed island.** The map is binary and to the pixel. The corona between two prominences,
   inside the arc of one, or next to the limb with little signal is corona, and the filters act there. A margin "to be
   safe" throws away exactly the fine inner detail one wants (a 9 px margin took a whole pocket of corona inside a
   prominence arch; the gate :func:`ael.gates.zones_against_truth` exists to catch that).
2. **A detection threshold is not a boundary.** Five sigma of colour finds the faint haze of emission around a
   prominence, where the pixel is still 95 % corona. That haze is removed from the *input* of the filters (red and blue
   clipped to the corona's colour, green corrected), and the filters act on what is left. Only where the light that is
   not corona weighs ``share`` (5 %) of the pixel or more is the pixel out (the **core**).

Nothing is painted and no value is invented: the map only says where filters act, and the cleaned input is a linear
combination of the three observed channels of the same pixel.

Measured and judged on one image (12 August 2026, 440 px per solar radius, Sun at 9° of altitude); on other images check
the map by eye (:func:`zones_preview`) before trusting it. See docs/INNER_LIMIT.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .geometry import EclipseGeometry

__all__ = ["InnerZones", "inner_zones", "zones_preview", "CLASS_NAMES"]

CLASS_NAMES = {0: "no data", 1: "corona", 2: "limb (edge pixel and white rim)", 3: "chromosphere", 4: "prominence",
               5: "bead", 6: "core inside the Moon's circle", 7: "corona, emission clipped at the filters' input"}
_REFERENCE_SUN_RADIUS_PX = 440.603          # the image the lengths below were set on


@dataclass
class InnerZones:
    """Result of :func:`inner_zones`.

    ``classes`` (uint8, see :data:`CLASS_NAMES`), ``core`` (bool: no filter acts or looks there), ``seen`` (bool:
    observed and outside the Moon's circle), ``clean`` (float32 H×W×3: the input for the filters, identical to the data
    outside the detected emission; ``None`` if not asked for), ``info`` (what each criterion measured)."""
    classes: np.ndarray
    core: np.ndarray
    seen: np.ndarray
    clean: np.ndarray | None
    info: dict = field(default_factory=dict)

    def support(self, valid: np.ndarray) -> np.ndarray:
        """The support for the filters: the observed pixels without the core."""
        return np.asarray(valid, bool) & ~self.core


def _mad(v) -> float:
    v = np.asarray(v, np.float64)
    return float(1.4826 * np.median(np.abs(v - np.median(v)))) if v.size else float("nan")


def _circular_fill(values: np.ndarray) -> np.ndarray:
    """NaN entries of a circular table filled by linear interpolation between their finite neighbours."""
    v = np.asarray(values, np.float64).copy()
    good = np.isfinite(v)
    if good.all():
        return v
    if good.sum() < 3:
        raise ValueError("not enough corona next to the Moon to measure its colour (fewer than three 10° sectors with data)")
    n = len(v); idx = np.arange(n)
    v[~good] = np.interp(idx[~good], idx[good], v[good], period=n)
    return v


def inner_zones(rgb: np.ndarray, valid: np.ndarray, geometry: EclipseGeometry, *, share: float = 0.05,
                rim_share: float = 0.10, detect_sigmas: float = 5.0, min_blob_px: int = 6,
                bead_factor: float = 3.0, return_clean: bool = True) -> InnerZones:
    """The single map of the inner limit, to the pixel, and the input of the filters without the hydrogen light.

    ``rgb``: linear H×W×3 (sky included or not; white-balanced or not: only ratios against the corona of the same
    sector are used). A mono image (H×W) is accepted: without colour, emission cannot be found, and the result says so.
    ``valid``: observed pixels. ``geometry`` must hold the Moon; "the contour" below is the edge of the observed data
    around the Moon, or the Moon's circle where the data reach inside it. Observed pixels inside the Moon's circle get
    no white-rim test: those found as emission or as the edge of the data go to the core (class "core inside the
    Moon's circle"), and the rest stay in :meth:`InnerZones.support` (corona that the circle of a presentation hides
    helps the operators next to the limb). If the disc holds anything else — earthshine, a dark Moon — take it out of
    ``valid`` first (``~geometry.moon_mask()``), as ``ael filters`` does. The result warns when there are such pixels.

    How each thing is found (lengths are those of the 2026 image, 440.6 px per solar radius, and scale with the Sun's
    radius in pixels unless they are a matter of sampling):

    1. **Colour of the corona** per 10° sector around the Moon: 25th percentile of ln(R/G) and median of ln(B/G) between
       16 and 60 px from the contour; its noise, the MAD of the departures between 60 and 140 px.
    2. **Detected emission**, where the input of the filters is cleaned: ln(R/G) above the corona's by more than
       ``detect_sigmas`` noises, in blobs of ``min_blob_px`` pixels or more, within 160 px of the contour. There R and B
       are clipped to the corona's colour (``R ← G × colour``) and G loses ``alpha`` times the red excess, ``alpha``
       measured on the image by regressing the fine detail of G on that of the red excess inside the strong emission
       (it is small and can have either sign: it depends on the colour matrix of the camera).
    3. **Core of emission**: (red excess + blue excess) / (R + 2G + B) ≥ ``share``, blobs of ``min_blob_px`` or more.
       Called *chromosphere* while it stays attached to the contour (up to 10 px), *prominence* above.
    4. **Beads**: within 40 px, pixels ``bead_factor`` times brighter than the median of their arc (±8°, rings of
       2 px), or bluer than the corona by more than ``detect_sigmas`` noises. A single pixel counts.
    5. **Limb**: the pixel at the edge of the data (1.5 px), and the white rim: per 2° angle (±2°), the parabola of
       ln L against distance fitted between 16 and 60 px and continued inwards; rim where the brightness exceeds that
       trend by ``rim_share`` or more, from the contour up to where it stops exceeding it (height per angle, median
       over 10° so that a narrow bright structure of the corona does not count), plus single pixels that meet the same
       criterion, touch the core and lie no more than 2 px above the rim of their angle. The trend only classifies.

    The **core** is limb + rim + emission core + beads: binary, no margin, no feather, pockets of corona inside it
    stay corona. ``share`` and ``rim_share`` are the two choices of this map (5 % and 10 %, set on the 2026 image,
    where a rim threshold of 5 % took 2 595 more pixels, up to 11 px from the limb, and part of a pocket of corona);
    do not change them to make a layer pass.
    """
    import cv2
    from scipy import ndimage as ndi

    a = np.asarray(rgb)
    mono = a.ndim == 2
    if mono:
        a = np.repeat(a[..., None], 3, axis=-1)
    elif a.ndim == 3 and a.shape[-1] == 3 and np.array_equal(a[..., 0], a[..., 1], equal_nan=True) \
            and np.array_equal(a[..., 1], a[..., 2], equal_nan=True):
        mono = True                                     # three equal channels are a mono image
    if a.ndim != 3 or a.shape[-1] != 3:
        raise ValueError("rgb must be HxWx3 (or HxW mono)")
    valid = np.asarray(valid, bool)
    if valid.shape != a.shape[:2] or valid.shape != tuple(geometry.shape):
        raise ValueError("rgb, valid and geometry must share one canvas")
    if geometry.moon_xy is None or geometry.moon_radius_px is None:
        raise ValueError("inner_zones needs the Moon in the geometry (run `ael geometry`, or set moon_xy and moon_radius_px)")
    if not (0 < share < 1 and 0 < rim_share < 1 and detect_sigmas > 0 and bead_factor > 1 and min_blob_px >= 1):
        raise ValueError("share and rim_share in (0, 1); detect_sigmas > 0; bead_factor > 1; min_blob_px >= 1")
    H, W = valid.shape
    s = float(geometry.sun_radius_px) / _REFERENCE_SUN_RADIUS_PX
    sr = max(s, 0.5)                                    # the rim is a matter of optics too: never below half
    ref_rho, ref_noise = (16.0 * s, 60.0 * s), (60.0 * s, 140.0 * s)
    emission_within, chrom_max, bead_within = 160.0 * s, 10.0 * s, max(40.0 * s, 12.0)
    fit0 = int(round(16 * sr)); fit1 = int(round(60 * sr)); rim_max = fit0
    limb_px, bead_arc = 1.5, 8
    mx, my, mr = float(geometry.moon_xy[0]), float(geometry.moon_xy[1]), float(geometry.moon_radius_px)
    half = int(np.ceil(mr + max(ref_noise[1], emission_within) + 150))
    x0, y0 = max(0, int(mx - half)), max(0, int(my - half)); x1, y1 = min(W, int(mx - half) + 2 * half), min(H, int(my - half) + 2 * half)
    if x1 - x0 < 16 or y1 - y0 < 16:
        raise ValueError("the Moon of the geometry lies outside the canvas")
    F = np.asarray(a[y0:y1, x0:x1], np.float64); S = valid[y0:y1, x0:x1]
    ok = S & np.isfinite(F).all(-1) & (F[..., 1] > 0)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dm = np.hypot(xx - mx, yy - my) - mr
    ang = np.degrees(np.arctan2(yy - my, xx - mx)) % 360
    del yy, xx
    # the hole of the Moon: the pixels without data that hang together with the Moon's disc (a masked star or a dead
    # column elsewhere is no lunar limb)
    lab, n = ndi.label(~ok | (dm < 0), structure=np.ones((3, 3)))
    touch = np.unique(lab[dm < 0]); touch = touch[touch > 0]
    hole = np.isin(lab, touch) & ~ok                    # no data, and joined to the Moon's disc
    other_holes = int((~ok & ~hole & (dm < max(ref_noise[1], emission_within))).sum())
    dist = cv2.distanceTransform((~hole).astype(np.uint8), cv2.DIST_L2, 5)
    rho = np.minimum(dist, np.maximum(dm, 0)); seen = ok & (dm >= 0)
    if seen.sum() < 1000:
        raise ValueError("fewer than 1000 observed pixels around the Moon")
    R, G, B = F[..., 0], F[..., 1], F[..., 2]
    with np.errstate(all="ignore"):
        rg = np.log(np.where(ok & (R > 0), R, np.nan) / G); bg = np.log(np.where(ok & (B > 0), B, np.nan) / G)
    L = F.mean(-1)

    # 1) the colour of the corona per 10° sector, and its noise
    sec = (ang // 10).astype(int); ref = np.full((36, 2), np.nan); fin = np.isfinite(rg) & np.isfinite(bg)
    zr = seen & (rho > ref_rho[0]) & (rho < ref_rho[1]) & fin; zs = seen & (rho > ref_noise[0]) & (rho < ref_noise[1]) & fin
    for k in range(36):
        m = zr & (sec == k)
        if m.sum() >= 50:
            ref[k] = np.percentile(rg[m], 25.0), np.median(bg[m])
    sectors_measured = int(np.isfinite(ref[:, 0]).sum())
    ref[:, 0] = _circular_fill(ref[:, 0]); ref[:, 1] = _circular_fill(ref[:, 1])
    cent = np.arange(36) * 10 + 5.0
    r_rg = np.interp(ang, cent, ref[:, 0], period=360); r_bg = np.interp(ang, cent, ref[:, 1], period=360)
    drg, dbg = rg - r_rg, bg - r_bg
    if zs.sum() < 200:
        zs = zr
    s_rg, s_bg = _mad(drg[zs]), _mad(dbg[zs])
    colour = bool(not mono and np.isfinite(s_rg))
    # a floor of 0.1 % on the colour noise: a stack so clean (or a synthetic one) that the ratio of two channels has no
    # scatter would otherwise make every pixel "five sigma" from itself, or none
    noise_floored = bool(colour and (s_rg < 1e-3 or not np.isfinite(s_bg) or s_bg < 1e-3))
    if colour:
        s_rg = max(s_rg, 1e-3); s_bg = max(s_bg, 1e-3) if np.isfinite(s_bg) else 1e-3

    # 2) detected emission (where the input of the filters is cleaned)
    near = ok & (rho < emission_within)
    em = near & (np.nan_to_num(drg, nan=9) > detect_sigmas * s_rg) if colour else np.zeros(ok.shape, bool)

    def blobs(mask):
        lab, n = ndi.label(mask, structure=np.ones((3, 3)))
        if n:
            area = ndi.sum(mask, lab, np.arange(1, n + 1)); mask = mask & np.r_[False, area >= min_blob_px][lab]
        return mask
    em = blobs(em)
    topR = G * np.exp(r_rg + detect_sigmas * s_rg) if colour else R; topB = G * np.exp(r_bg + detect_sigmas * s_bg) if colour else B
    ER = np.where(em, np.maximum(R - topR, 0), 0.0)     # red excess over the corona's colour
    EB = np.where(em, np.maximum(B - topB, 0), 0.0)     # blue excess (H-beta, calcium), inside the emission only
    quota = (ER + EB) / np.maximum(R + 2 * G + B, 1e-30)

    # 3) core of emission: the light that is not corona weighs `share` of the pixel or more
    emn = blobs(em & (quota >= share))

    # 4) what the emission leaves in the green: regression of the fine detail of G on that of the red excess
    def hp(z, m, sig):
        num = cv2.GaussianBlur(np.where(m, z, 0), (0, 0), sig); den = cv2.GaussianBlur(m.astype(np.float64), (0, 0), sig)
        return z - num / np.maximum(den, 1e-6)
    alpha = corr = None; alpha_unc = 0.0; per_blob = []
    zf = emn & seen & (rho > 3)
    if zf.sum() >= 30:
        with np.errstate(all="ignore"):
            hG = hp(G, ok, 1.5) / G; hE = hp(ER, ok, 1.5) / G
        zf &= np.isfinite(hG) & np.isfinite(hE)
        den = float((hE[zf] ** 2).sum())
        if zf.sum() >= 30 and den > 0:
            alpha = float((hG[zf] * hE[zf]).sum() / den); corr = float(np.corrcoef(hG[zf], hE[zf])[0, 1])
            lab, n = ndi.label(emn & seen, structure=np.ones((3, 3)))
            for i in range(1, n + 1):
                m = (lab == i) & zf
                if m.sum() < 30:
                    continue
                d2 = float((hE[m] ** 2).sum())
                if d2 > 0:
                    per_blob.append(dict(px=int(m.sum()), alpha=float((hG[m] * hE[m]).sum() / d2),
                                         correlation=float(np.corrcoef(hG[m], hE[m])[0, 1])))
            clear = [b["alpha"] for b in per_blob if abs(b["correlation"]) >= .5]
            alpha_unc = float(np.std(clear)) if len(clear) >= 2 else abs(alpha) / 2
    a_green = 0.0 if alpha is None else alpha

    # 5) the clean corona: R and B clipped to the corona's colour, G corrected. Outside the emission, identical.
    Gc = np.where(em, G - a_green * ER, G)
    Rc = np.where(em, np.minimum(R, Gc * np.exp(r_rg + detect_sigmas * s_rg)), R) if colour else R
    Bc = np.where(em, np.minimum(B, Gc * np.exp(r_bg + detect_sigmas * s_bg)), B) if colour else B
    changed = em & ((Rc != R) | (Bc != B) | (Gc != G))
    Lv, Lc = (R + 2 * G + B) / 4, (Rc + 2 * Gc + Bc) / 4
    with np.errstate(all="ignore"):
        dlum = Lc / Lv - 1
    haze = changed & ~emn & seen                        # corona with a haze of emission: filters act, on the clean input
    left = np.abs(alpha_unc) * ER / np.maximum(Gc, 1e-30)

    # 6) chromosphere (a name only): emission core attached to the contour while it is the majority, per 2° angle
    NA = 180; ia = np.floor(ang / 2).astype(int) % NA; ir1 = np.floor(rho).astype(int); NRH = max(4 * int(np.ceil(chrom_max)), 8)
    z = near & seen & (rho < NRH); k = ia[z] * NRH + ir1[z]
    tot = np.bincount(k, minlength=NA * NRH).reshape(NA, NRH).astype(float)
    ne = np.bincount(k, weights=emn[z].astype(float), minlength=NA * NRH).reshape(NA, NRH)
    ne = ndi.uniform_filter1d(ne, 3, axis=0, mode="wrap"); tot = ndi.uniform_filter1d(tot, 3, axis=0, mode="wrap")
    frac = ne / np.maximum(tot, 1e-9); alc = np.zeros(NA)
    for q in range(NA):
        amb = np.flatnonzero(tot[q] > 0)
        if not len(amb) or frac[q, amb[0]] < .5:
            continue
        low = [r for r in amb if frac[q, r] < .5]; alc[q] = min(float(low[0]) if low else float(NRH), chrom_max)
    chrom = emn & seen & (rho < alc[ia])
    limb = ok & (dm >= 0) & (dist < limb_px)

    # 7) beads
    zb = ok & ~em & (rho < bead_within)
    ir = np.floor(rho / 2).astype(int); it = np.floor(ang / 1.0).astype(int) % 360; nr = max(int(bead_within / 2), 1)
    med = np.full((nr, 360), np.nan)
    for i in range(nr):
        m = zb & (ir == i)
        if m.sum() < 100:
            continue
        v, q = L[m], it[m]; o = np.argsort(q, kind="stable"); v, q = v[o], q[o]; cuts = np.searchsorted(q, np.arange(361))
        for j in range(360):
            vals = np.concatenate([v[cuts[p]:cuts[p + 1]] for p in [(j + d) % 360 for d in range(-bead_arc, bead_arc + 1)]])
            if len(vals) >= 30:
                med[i, j] = np.median(vals)
    for i in range(nr - 2, -1, -1):
        med[i] = np.where(np.isfinite(med[i]), med[i], med[i + 1])
    mm = med[np.minimum(ir, nr - 1), it]
    exc = np.where(zb, L / np.where(np.isfinite(mm), mm, np.inf), 0)
    blue = zb & (np.nan_to_num(dbg, nan=0) > detect_sigmas * s_bg) if colour else np.zeros(ok.shape, bool)
    bead = zb & ((exc > bead_factor) | blue)

    # 7b) the white rim of the limb: per 2° angle (±2°), brightness against the trend of the corona of the same angle
    zz = seen & ~emn & ~bead & (Lc > 0) & (rho < fit1); fl = np.flatnonzero(zz.ravel())
    ia_f = ia.ravel()[fl]; rb_f = np.floor(rho.ravel()[fl]).astype(int); ll_f = np.log(Lc.ravel()[fl])
    o = np.argsort(ia_f, kind="stable"); ia_f, rb_f, ll_f = ia_f[o], rb_f[o], ll_f[o]; cuts = np.searchsorted(ia_f, np.arange(NA + 1))
    hv = np.zeros(NA); rim_excess = np.full((NA, rim_max), np.nan); no_fit = 0; pfs = np.full((NA, 3), np.nan)
    need = min(25, max(6, int(0.57 * (fit1 - fit0))))
    for q in range(NA):
        sel = np.concatenate([np.arange(cuts[p], cuts[p + 1]) for p in ((q - 1) % NA, q, (q + 1) % NA)])
        rb, ll = rb_f[sel], ll_f[sel]; medv = np.full(fit1, np.nan); cnt = np.bincount(rb, minlength=fit1)
        for r in range(fit1):
            if cnt[r] >= 6:
                medv[r] = np.median(ll[rb == r])
        rr = np.arange(fit0, fit1); val = np.isfinite(medv[rr])
        if val.sum() < need:
            no_fit += 1; continue
        pf = np.polyfit(rr[val] + .5, medv[rr][val], 2); pfs[q] = pf
        ex = np.exp(medv[:rim_max] - np.polyval(pf, np.arange(rim_max) + .5)) - 1; rim_excess[q] = ex
        amb = np.flatnonzero(np.isfinite(ex))
        if not len(amb) or ex[amb[0]] < rim_share:
            continue
        low = [r for r in amb if ex[r] < rim_share]; hv[q] = float(low[0]) if low else float(rim_max)
    hv_raw = hv.copy(); hv = ndi.median_filter(hv, size=5, mode="wrap")
    rim = seen & ~emn & ~bead & (rho < hv[ia])
    with np.errstate(all="ignore"):
        ex_px = Lc / np.exp(pfs[ia, 0] * rho * rho + pfs[ia, 1] * rho + pfs[ia, 2]) - 1
    cand = seen & ~emn & ~bead & (rho < np.minimum(hv[ia] + 2, rim_max)) & (np.nan_to_num(ex_px, nan=0) >= rim_share)
    seed = limb | rim | emn | bead | (ok & ~seen)
    loose = ndi.binary_propagation(seed, structure=np.ones((3, 3)), mask=seed | cand) & cand & ~rim & ~limb
    rim |= loose

    # 8) classes and core (binary: no margin, no feather, no island)
    cls = np.zeros(ok.shape, np.uint8); cls[seen] = 1; cls[haze] = 7
    cls[limb | rim] = 2; cls[chrom] = 3; cls[emn & ~chrom] = 4; cls[bead] = 5
    core = limb | rim | emn | bead
    haze &= ~core
    cls[~seen & core] = 6

    # receipt
    px = {CLASS_NAMES[i]: int((cls == i).sum()) for i in (2, 3, 4, 5, 6, 7)}
    lab, n = ndi.label(cls == 4, structure=np.ones((3, 3))); proms = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() < 20:
            continue
        cy, cx = ndi.center_of_mass(m)
        proms.append(dict(px=int(m.sum()), x=round(float(cx + x0), 1), y=round(float(cy + y0), 1),
                          height_px=round(float(rho[m].max()), 1), median_share=round(float(np.median(quota[m])), 3)))
    proms.sort(key=lambda t: -t["px"])
    lab, n = ndi.label(seen & ~core, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])); pockets = []
    if n > 1:
        area = ndi.sum(np.ones(lab.shape), lab, np.arange(1, n + 1)); big = int(np.argmax(area)) + 1
        for i in range(1, n + 1):
            if i == big:
                continue
            m = lab == i; cy, cx = ndi.center_of_mass(m)
            pockets.append(dict(px=int(m.sum()), x=round(float(cx + x0), 1), y=round(float(cy + y0), 1)))
    pockets.sort(key=lambda t: -t["px"])
    q = lambda v, p: float(np.percentile(v, p)) if v.size else None
    warnings = []
    if mono:
        warnings.append("mono input: emission (chromosphere, prominences) cannot be found without colour; only the limb, "
                        "its white rim and beads by brightness are in the core")
    elif not colour:
        warnings.append("the colour of the corona could not be measured: no emission was looked for")
    elif noise_floored:
        warnings.append("the colour of the corona has almost no scatter (below 0.1 %): a floor of 0.1 % was used as its noise")
    if sectors_measured < 36:
        warnings.append(f"the corona's colour was measured in {sectors_measured} of 36 sectors; the others are interpolated")
    if no_fit:
        warnings.append(f"no brightness trend could be fitted at {2 * no_fit}° of the limb: no white rim was looked for there")
    inside_moon = int((ok & (dm < 0)).sum())
    if inside_moon:
        warnings.append(f"{inside_moon} observed pixels lie inside the Moon's circle ({int((core & ~seen).sum())} of them in the "
                        "core); the rest stay in the filters' support; take them out of `valid` if they are not corona")
    if s < 0.34:
        warnings.append("fewer than 150 px per solar radius: the brightness trend that finds the white rim of the limb "
                        "is fitted on few pixels at this sampling, and no real image this small has been tried; check "
                        "the map by eye")
    info = dict(method="inner_zones: one binary map from colour and brightness; no margin, no feather, pockets stay corona",
                box=[x0, y0, x1, y1], scale_to_reference_image=s, share=share, rim_share=rim_share,
                pixels_without_data_away_from_the_moon=other_holes,
                detect_sigmas=detect_sigmas, min_blob_px=min_blob_px, bead_factor=bead_factor,
                corona_colour=dict(noise_ln_R_G=None if not colour else round(s_rg, 5),
                                   noise_ln_B_G=None if not np.isfinite(s_bg) else round(s_bg, 5),
                                   sectors_measured=sectors_measured),
                pixels=px, core_pixels_seen=int((core & seen).sum()),
                filter_input=dict(pixels_changed=int(changed.sum()), pixels_changed_outside_core=int(haze.sum()),
                                  alpha_green_per_red_excess=None if alpha is None else round(alpha, 5),
                                  alpha_uncertainty=round(alpha_unc, 5), correlation=None if corr is None else round(corr, 3),
                                  per_blob=per_blob[:12],
                                  luminance_change_outside_core=dict(median=q(dlum[haze], 50), p1=q(dlum[haze], 1)),
                                  emission_possibly_left_over_green=dict(median=q(left[haze], 50), p99=q(left[haze], 99))),
                chromosphere=dict(max_height_px=float(alc.max()), degrees_with_chromosphere=int((alc > 0).sum() * 2)),
                white_rim=dict(pixels=int((rim & ~limb).sum()), loose_pixels=int(loose.sum()), trend_fit_px=[fit0, fit1],
                               degrees_with_rim=int((hv > 0).sum() * 2), degrees_without_fit=int(no_fit * 2),
                               degrees_where_the_median_lowered_a_tower=int((hv_raw > hv + 2).sum() * 2),
                               max_height_px=float(hv.max())),
                prominences=proms[:20], corona_pockets_inside_the_core=pockets[:20], bead_pixels=int(bead.sum()),
                warnings=warnings)

    def full(z, fill, dtype):
        out = np.full((H, W), fill, dtype); out[y0:y1, x0:x1] = z; return out
    classes = np.zeros((H, W), np.uint8); far = valid & np.isfinite(a).all(-1) & (a[..., 1] > 0)
    classes[far] = 1; classes[y0:y1, x0:x1] = cls
    clean = None
    if return_clean:
        clean = np.array(a, np.float32, copy=True)
        blk = clean[y0:y1, x0:x1]
        for c, new in enumerate((Rc, Gc, Bc)):
            blk[..., c][changed] = new[changed].astype(np.float32)
    seen_all = far.copy(); seen_all[y0:y1, x0:x1] = seen
    return InnerZones(classes=classes, core=full(core, False, bool), seen=seen_all, clean=clean, info=info)


_COLOURS = np.array([[0, 0, 0], [70, 70, 70], [255, 255, 255], [255, 120, 200], [255, 0, 0], [0, 220, 255], [120, 0, 0],
                     [110, 90, 40]], np.uint8)


def zones_preview(zones: InnerZones, luminance: np.ndarray | None = None, *, margin_px: int = 120) -> np.ndarray:
    """An 8-bit RGB picture of the map around the Moon, to check it by eye: corona grey (modulated by the luminance if
    given), limb white, chromosphere pink, prominences red, beads cyan, corona with cleaned input brown. Enlarge it:
    the map is to the pixel."""
    x0, y0, x1, y1 = zones.info["box"]
    cls = zones.classes[y0:y1, x0:x1]
    ys, xs = np.nonzero(zones.core[y0:y1, x0:x1])
    if len(ys):
        a, b = max(0, ys.min() - margin_px), min(cls.shape[0], ys.max() + margin_px + 1)
        c, d = max(0, xs.min() - margin_px), min(cls.shape[1], xs.max() + margin_px + 1)
    else:
        a, b, c, d = 0, cls.shape[0], 0, cls.shape[1]
    img = _COLOURS[cls[a:b, c:d]].astype(np.float32)
    if luminance is not None:
        lum = np.asarray(luminance, np.float32)[y0:y1, x0:x1][a:b, c:d]
        cor = cls[a:b, c:d] == 1
        if cor.any():
            lo, hi = np.nanpercentile(np.log(np.maximum(lum[cor], 1e-30)), [1, 99])
            g = np.clip((np.log(np.maximum(lum, 1e-30)) - lo) / max(hi - lo, 1e-9), 0, 1) * 140 + 40
            img[cor] = g[cor, None]
    return np.clip(img, 0, 255).astype(np.uint8)
