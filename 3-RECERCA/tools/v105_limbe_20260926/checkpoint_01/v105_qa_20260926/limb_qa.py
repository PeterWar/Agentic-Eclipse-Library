#!/usr/bin/env python3
"""Read-only array QA; output is one JSON, never an image or PSB.

Coordinates: box=(x0,y0,x1,y1), cx/cy global, angle 0=right, 90=up.
Photographic alpha/finite pixels are NOT a physical-corona validity mask.
No image is registered, tone-matched, filled, sharpened or otherwise edited.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_erosion, map_coordinates

DEFAULT_SECTORS = [("top", 75, 105), ("upper_left", 110, 140),
                   ("prominence", 150, 180), ("lower_left", 210, 240),
                   ("lower_left_exception", 240, 270), ("right", 300, 60)]
DEFAULT_BANDS = [-4, -2, 0, 1, 2, 3, 5, 8, 15, 30, 60, 100, 150, 160]


def load_array(path, rgb=False, scale=None):
    obj = np.load(path, allow_pickle=False)
    if isinstance(obj, np.lib.npyio.NpzFile):
        if rgb and all(f"c{i}" in obj for i in range(3)):
            arr = np.stack([obj[f"c{i}"] for i in range(3)], -1)
        else:
            keys = [k for k in ("rgb", "array", "valid", "mask", "delta", "arr_0") if k in obj]
            if not keys:
                if len(obj.files) != 1:
                    raise ValueError(f"Ambiguous NPZ keys in {path}: {obj.files}")
                keys = obj.files
            arr = obj[keys[0]]
        obj.close()
    else:
        arr = obj
    divisor = (float(scale) if scale is not None else
               float(np.iinfo(arr.dtype).max) if np.issubdtype(arr.dtype, np.integer) else 1.0)
    if divisor <= 0:
        raise ValueError("Scale must be positive")
    arr = np.asarray(arr, np.float64) / divisor
    if rgb and (arr.ndim != 3 or arr.shape[-1] != 3):
        raise ValueError(f"Expected HxWx3 RGB, received {arr.shape}")
    return arr


def luminance(rgb):
    """Fixed diagnostic R+2G+B, not a claim of calibrated luminance."""
    return (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4


def geometry(shape, box, cxcyR):
    x0, y0, x1, y1 = box
    if tuple(shape) != (y1-y0, x1-x0):
        raise ValueError(f"Array shape {shape} does not match box {box}")
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx-cxcyR[0], yy-cxcyR[1]
    rr = np.hypot(dx, dy)
    cs, sn = dx/np.maximum(rr, 1e-30), -dy/np.maximum(rr, 1e-30)
    return rr-cxcyR[2], np.degrees(np.arctan2(-dy, dx)) % 360, cs, sn


def sector_mask(theta, lo, hi):
    return ((theta >= lo) & (theta < hi)) if lo < hi else ((theta >= lo) | (theta < hi))


def stats(values):
    a = np.asarray(values)
    a = a[np.isfinite(a)]
    if not a.size:
        return {"n": 0}
    p = np.percentile(a, [5, 50, 95])
    return {"n": int(a.size), "p05": float(p[0]), "median": float(p[1]),
            "p95": float(p[2]), "mean": float(a.mean()), "rms": float(np.sqrt(np.mean(a*a)))}


def correlation(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if len(a) < 32 or np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def gradients(lum, valid, cs, sn):
    """Never report derivatives across invalid support or a cropped-array edge."""
    ok = binary_erosion(valid & np.isfinite(lum), iterations=1, border_value=0)
    gy, gx = np.gradient(lum)
    radial, tangential = gx*cs-gy*sn, -gx*sn-gy*cs
    return radial, tangential, ok


def band_report(images, validity, dist, theta, cs, sn, sectors=DEFAULT_SECTORS, bands=DEFAULT_BANDS):
    lum = {k: luminance(a) for k, a in images.items()}
    grads = {k: gradients(v, validity[k], cs, sn) for k, v in lum.items()}
    out = {}
    for name, lo, hi in sectors:
        sec, rows = sector_mask(theta, lo, hi), []
        for a, b in zip(bands[:-1], bands[1:]):
            zone = sec & (dist >= a) & (dist < b)
            n = int(zone.sum())
            row = {"distance_px": [a, b], "pixels_in_bin": n, "images": {}}
            for key, val in lum.items():
                good = zone & validity[key] & np.isfinite(val)
                gr, gt, gv = grads[key]
                row["images"][key] = {"coverage": float(good.sum()/n) if n else None,
                    "level": stats(val[good]), "radial_gradient": stats(gr[zone & gv]),
                    "tangential_gradient": stats(gt[zone & gv])}
            for lhs, rhs in (("candidate", "base"), ("candidate", "ref"), ("base", "ref")):
                if lhs not in images or rhs not in images:
                    continue
                common = zone & validity[lhs] & validity[rhs]
                grad_common = zone & grads[lhs][2] & grads[rhs][2]
                positive = common & (lum[lhs] > 0) & (lum[rhs] > 0)
                row[f"{lhs}_minus_{rhs}"] = {"common_pixels": int(common.sum()),
                    "level_delta": stats((lum[lhs]-lum[rhs])[common]),
                    "ln_ratio": stats(np.log(lum[lhs][positive]/lum[rhs][positive])),
                    "tangential_gradient_correlation": correlation(grads[lhs][1][grad_common], grads[rhs][1][grad_common])}
            rows.append(row)
        out[name] = rows
    return out


def radial_cuts(lum, valid, box, cxcyR, sectors=DEFAULT_SECTORS, distances=None):
    """Nine independent radial cuts per sector, then median; unsupported samples excluded.

    The sampling mask requires every bilinear input pixel to be valid; no
    interpolation of log(0), no replacement of holes by zero-valued radiance.
    """
    distances = np.arange(-4, 161, 1.0) if distances is None else np.asarray(distances)
    out = {}
    for name, lo, hi in sectors:
        end = hi if hi > lo else hi+360
        angles = np.linspace(lo+(end-lo)/20, end-(end-lo)/20, 9)
        th = np.deg2rad(angles)[None, :]
        rr = (cxcyR[2]+distances)[:, None]
        coords = np.array([cxcyR[1]-rr*np.sin(th)-box[1], cxcyR[0]+rr*np.cos(th)-box[0]])
        vals = map_coordinates(lum, coords, order=1, mode="constant", cval=np.nan, prefilter=False)
        support = map_coordinates(valid.astype(float), coords, order=1, mode="constant", cval=0., prefilter=False) >= 1-1e-12
        vals[~support] = np.nan
        med = [float(np.median(v[np.isfinite(v)])) if np.isfinite(v).any() else None for v in vals]
        out[name] = {"angle_deg": angles.tolist(), "distance_px": distances.tolist(),
                     "median": med, "valid_cuts": support.sum(axis=1).tolist()}
    return out


def shifted(array, dy, dx):
    """Integer null displacement without wraparound being admitted as support."""
    result = np.roll(array, (dy, dx), (0, 1)).copy()
    if dy > 0: result[:dy] = 0
    if dy < 0: result[dy:] = 0
    if dx > 0: result[:, :dx] = 0
    if dx < 0: result[:, dx:] = 0
    return result


def null_shift_report(candidate, reference, candidate_valid, reference_valid, dist, theta, cs, sn, shifts):
    _, cg, cv = gradients(candidate, candidate_valid, cs, sn)
    out = {}
    for name, lo, hi in DEFAULT_SECTORS:
        zone = sector_mask(theta, lo, hi) & (dist >= 3) & (dist < 30)
        scores = []
        for dy, dx in [(0, 0)] + shifts:
            rg = shifted(reference, dy, dx)
            rv = shifted(reference_valid, dy, dx).astype(bool)
            _, tg, tv = gradients(rg, rv, cs, sn)
            ok = zone & cv & tv
            scores.append({"shift_dy_dx": [dy, dx], "n": int(ok.sum()),
                           "tangential_gradient_correlation": correlation(cg[ok], tg[ok])})
        out[name] = scores
    return out


def phase_transfer(delta_in, delta_out, valid, dist, theta, sectors=DEFAULT_SECTORS, bands=DEFAULT_BANDS):
    """Signed transfer projected onto the ORIGINAL injected phase, not RMS gain.

    delta_in/out must be matched injected-minus-uninjected arrays. A nuisance
    constant is fitted and returned. An inverted injection has transfer -1;
    unrelated high-contrast noise does not falsely count as retained detail.
    """
    if delta_in.ndim == 3: delta_in = luminance(delta_in)
    if delta_out.ndim == 3: delta_out = luminance(delta_out)
    ok = valid & np.isfinite(delta_in) & np.isfinite(delta_out)
    def fit(mask):
        x, y = delta_in[mask], delta_out[mask]
        if x.size < 32 or np.var(x) < 1e-20:
            return {"n": int(x.size), "gain": None}
        xc, yc = x-x.mean(), y-y.mean()
        gain = float(np.dot(xc, yc)/np.dot(xc, xc))
        offset = float(y.mean()-gain*x.mean())
        return {"n": int(x.size), "gain": gain, "offset": offset,
                "orthogonal_residual_rms": float(np.sqrt(np.mean((y-gain*x-offset)**2))),
                "original_phase_correlation": correlation(x, y)}
    out = {}
    for name, lo, hi in sectors:
        sec = sector_mask(theta, lo, hi)
        interior = fit(ok & sec & (dist >= 15) & (dist < 30))
        rows = []
        for a, b in zip(bands[:-1], bands[1:]):
            item = fit(ok & sec & (dist >= a) & (dist < b))
            ig, g = interior.get("gain"), item.get("gain")
            ratio = g/ig if g is not None and ig is not None and abs(ig) > 1e-12 else None
            item.update({"distance_px": [a, b], "relative_to_15_30_px": ratio,
                         "relative_gate_0p90_1p10": bool(.90 <= ratio <= 1.10 and g > 0 and ig > 0) if ratio is not None else None})
            rows.append(item)
        out[name] = {"interior_reference": interior, "bands": rows}
    return out


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "candidate", "ref"):
        p.add_argument(f"--{name}", required=name != "ref")
        p.add_argument(f"--{name}-valid", help="Physical validity mask; 0 invalid, nonzero valid")
    p.add_argument("--box", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    p.add_argument("--cxcyR", type=float, nargs=3, required=True)
    p.add_argument("--scale", type=float, help="Common divisor, default dtype max for integers, 1 for floats")
    p.add_argument("--output", required=True)
    p.add_argument("--reference-registered", action="store_true", help="Only set after independent solar registration")
    p.add_argument("--null-shift", type=int, nargs=2, action="append", default=[], metavar=("DY", "DX"))
    p.add_argument("--transfer-input", help="Injected-minus-original INPUT (same grid, original injected phase)")
    p.add_argument("--transfer-output", help="Injected-minus-original OUTPUT including actual compositing")
    p.add_argument("--transfer-valid", help="Common physical support for injection INPUT and OUTPUT")
    args = p.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(Path("/private/tmp/v105_qa_20260926")):
        p.error("Output is restricted to /private/tmp/v105_qa_20260926")
    images, valid, provenance, physical = {}, {}, {}, {}
    for name in ("base", "candidate", "ref"):
        path = getattr(args, name)
        if not path: continue
        images[name] = load_array(path, rgb=True, scale=args.scale)
        mpath = getattr(args, f"{name}_valid")
        mask = load_array(mpath) != 0 if mpath else np.ones(images[name].shape[:2], bool)
        if mask.shape != images[name].shape[:2]: raise ValueError(f"Mask shape mismatch: {name}")
        valid[name] = mask & np.isfinite(images[name]).all(-1)
        physical[name] = bool(mpath)
        provenance[name] = {"path": str(Path(path).resolve()), "sha256": sha(path),
                            "validity_path": mpath, "validity_sha256": sha(mpath) if mpath else None}
    if len({a.shape for a in images.values()}) != 1: raise ValueError("RGB array shapes differ")
    dist, theta, cs, sn = geometry(images["base"].shape[:2], args.box, args.cxcyR)
    outside = (dist >= 150) & np.isfinite(images["base"]).all(-1) & np.isfinite(images["candidate"]).all(-1)
    outside_lost_support = int(((dist >= 150) & valid["base"] & ~valid["candidate"]).sum())
    dd = np.abs(images["candidate"]-images["base"])
    report = {"geometry": {"box_xyxy": args.box, "cxcyR_global": args.cxcyR,
                "distance_is_to": "declared presentation circle; not actual per-frame limb or operator domain"},
        "input": provenance, "physical_validity_masks_supplied": physical,
        "reference_solar_registration_confirmed": args.reference_registered,
        "limitations": ["Comparison does not itself register images, validate solar signal, or estimate PSF.",
            "Absent physical masks, coverage only means finite arrays, not observed unocculted corona.",
            "RGB diagnostic levels are display quantities unless caller supplied calibrated linear data.",
            "Unregistered reference comparison is descriptive and must not gate detail recovery."],
        "fixed_gates": {"outside_150_px_max_abs_normalized": 2/65535,
            "original_phase_transfer_relative_to_interior": [.9, 1.1],
            "reference_detail_gate_enabled": "ref" in images and args.reference_registered and all(physical.values())},
        "outside_150_px": {"finite_pixels": int(outside.sum()), "lost_support_pixels": outside_lost_support,
            "absolute_delta": stats(dd[outside]),
            "max_absolute_delta": float(dd[outside].max()) if outside.any() else None,
            "pass_2_uint16_lsb": bool(outside_lost_support == 0 and np.all(dd[outside] <= 2/65535+1e-15)) if outside.any() else None},
        "bands": band_report(images, valid, dist, theta, cs, sn),
        "radial_cuts": {k: radial_cuts(luminance(a), valid[k], args.box, args.cxcyR) for k, a in images.items()}}
    if args.null_shift:
        if "ref" not in images: p.error("--null-shift requires --ref")
        report["null_shifts"] = null_shift_report(luminance(images["candidate"]), luminance(images["ref"]),
            valid["candidate"], valid["ref"], dist, theta, cs, sn, args.null_shift)
    if bool(args.transfer_input) != bool(args.transfer_output): p.error("Supply both transfer arrays")
    if args.transfer_input:
        di = load_array(args.transfer_input, scale=args.scale)
        do = load_array(args.transfer_output, scale=args.scale)
        if di.shape[:2] != dist.shape or do.shape[:2] != dist.shape: raise ValueError("Transfer shape mismatch")
        iv = load_array(args.transfer_valid) != 0 if args.transfer_valid else valid["candidate"] & valid["base"]
        report["transfer"] = phase_transfer(di, do, iv, dist, theta)
        report["transfer_provenance"] = {k: {"path": v, "sha256": sha(v)} for k, v in
            (("input", args.transfer_input), ("output", args.transfer_output))}
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(output), "outside_150_px": report["outside_150_px"],
                      "reference_detail_gate_enabled": report["fixed_gates"]["reference_detail_gate_enabled"]}))


if __name__ == "__main__":
    main()
