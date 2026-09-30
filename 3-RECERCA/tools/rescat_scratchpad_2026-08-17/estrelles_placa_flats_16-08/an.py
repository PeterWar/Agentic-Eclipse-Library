import tifffile, numpy as np, sys, os, json

def center_and_profile(path, moon_r_px, sat_thr=64000, bin_=4):
    a = tifffile.imread(path)
    H, W, _ = a.shape
    g = a[..., 1].astype(np.float32)
    # coarse centroid on the brightest pixels of a binned image
    gb = g[::bin_, ::bin_]
    thr = np.percentile(gb, 99.8)
    m = gb >= thr
    ys, xs = np.nonzero(m)
    cy, cx = ys.mean()*bin_, xs.mean()*bin_
    # radial stats on binned grid
    yy, xx = np.mgrid[0:gb.shape[0], 0:gb.shape[1]]
    r = np.hypot(yy*bin_ - cy, xx*bin_ - cx)
    sat = (a[::bin_, ::bin_] >= sat_thr).any(-1)
    satfrac_full = float((a >= sat_thr).any(-1).mean())
    # radius beyond which no saturation (99.9 percentile of saturated radii)
    rsat = float(np.percentile(r[sat], 99.5)) if sat.any() else 0.0
    # corner sky: 4 corners 400x400 (binned 100x100)
    k = 400//bin_
    corners = np.concatenate([gb[:k,:k].ravel(), gb[:k,-k:].ravel(), gb[-k:,:k].ravel(), gb[-k:,-k:].ravel()])
    sky = float(np.median(corners)); skysd = float(np.std(corners))
    # radial profile of median G in annuli (in units of moon radii)
    prof = []
    for rr in np.arange(1.0, 12.01, 0.25):
        lo, hi = (rr-0.125)*moon_r_px, (rr+0.125)*moon_r_px
        sel = (r >= lo) & (r < hi)
        if sel.sum() < 50: break
        v = gb[sel]
        prof.append((round(float(rr),3), float(np.median(v)), float(np.percentile(v,84)-np.percentile(v,16))/2.0, int(sel.sum()),
                     float(sat[sel].mean())))
    return dict(file=os.path.basename(path), shape=[H,W], cy=round(cy,1), cx=round(cx,1),
                sat_frac=satfrac_full, r_sat_px=round(rsat,1), r_sat_moon=round(rsat/moon_r_px,2),
                sky_med=sky, sky_sd=skysd, prof=prof)

if __name__ == "__main__":
    moon_r = float(sys.argv[1]); out=[]
    for p in sys.argv[2:]:
        try:
            out.append(center_and_profile(p, moon_r))
        except Exception as e:
            out.append({"file": os.path.basename(p), "error": repr(e)})
    print(json.dumps(out))
