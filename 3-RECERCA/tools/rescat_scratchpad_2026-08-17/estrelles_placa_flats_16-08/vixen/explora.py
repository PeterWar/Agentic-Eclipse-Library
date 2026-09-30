import numpy as np, rawpy, sys

D = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"

def load(name):
    with rawpy.imread(D+name) as raw:
        img = raw.raw_image_visible.astype(np.float64)
        col = raw.raw_colors_visible.copy()
    return img, col

for name in ["572A2940.CR3", "572A3030.CR3", "572A2967.CR3"]:
    img, col = load(name)
    print(name, img.shape, "colors uniq", np.unique(col))
    print("  min/max/med", img.min(), img.max(), np.median(img))
    # per-plane
    for c, lab in [(0,'R'),(1,'G1'),(3,'B')]:
        m = col==c
        v = img[m]
        print(f"   {lab}: med={np.median(v):.1f} p99={np.percentile(v,99):.1f} max={v.max():.0f}")
    # corner stats (should be sky/dark)
    print("  corner 100x100 med", np.median(img[:100,:100]))
