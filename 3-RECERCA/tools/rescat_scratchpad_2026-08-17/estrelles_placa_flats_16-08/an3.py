"""Fons: dependencia azimutal contra radial, i soroll local real."""
import tifffile, numpy as np, sys, json, os
from scipy.ndimage import median_filter

def run(path, R, cx, cy, exp, ds=4):
    a = tifffile.imread(path)
    g = a[..., 1].astype(np.float32)[::ds, ::ds]
    H, W = g.shape
    yy, xx = np.mgrid[0:H, 0:W]
    dx = xx*ds - cx; dy = yy*ds - cy
    r = np.hypot(dx, dy)/R
    th = (np.degrees(np.arctan2(-dy, dx)) + 360) % 360   # y cap amunt a la imatge = -dy
    out = {"file": os.path.basename(path), "exp": exp, "R": R, "cx": cx, "cy": cy, "az": {}, "rad": []}
    for rr in [3,4,5,6,8,10,12,14]:
        sel0 = (r >= rr-0.25) & (r < rr+0.25)
        if sel0.sum() < 200: continue
        secs = []
        for a0 in range(0, 360, 30):
            s = sel0 & (th >= a0) & (th < a0+30)
            secs.append(round(float(np.median(g[s])),1) if s.sum()>40 else None)
        out["az"][rr] = secs
        out["rad"].append([rr, round(float(np.median(g[sel0])),1)])
    # soroll local real: passa-alt 5x5 en 4 finestres lluny
    noise = []
    for (y0,x0) in [(60,60),(60,W-260),(H-260,60),(H-260,W-260)]:
        p = g[y0:y0+200, x0:x0+200]
        hp = p - median_filter(p, 5)
        noise.append(round(float(np.std(hp)),1))
    out["noise_hp"] = noise
    out["corner_med"] = [round(float(np.median(g[60:260,60:260])),1), round(float(np.median(g[60:260,-260:-60])),1),
                         round(float(np.median(g[-260:-60,60:260])),1), round(float(np.median(g[-260:-60,-260:-60])),1)]
    return out

if __name__ == "__main__":
    cfg = json.loads(sys.argv[1])
    print(json.dumps([run(**c) for c in cfg]))
