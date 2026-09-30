import numpy as np, rawpy
D = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"

def raw(name):
    with rawpy.imread(D+name) as r:
        return r.raw_image_visible.astype(np.float64) - 512.0

for name in ["572A2999.CR3", "572A3009.CR3", "572A2988.CR3"]:
    img = raw(name)
    h, w = img.shape
    sub = img[:h//2*2, :w//2*2].reshape(h//2,2,w//2,2).mean(axis=(1,3))
    # binned x4 more
    b = sub[:sub.shape[0]//4*4, :sub.shape[1]//4*4].reshape(sub.shape[0]//4,4,sub.shape[1]//4,4).mean(axis=(1,3))
    thr = np.percentile(b, 99.5)
    ys, xs = np.where(b > max(thr, 20))
    cy, cx = ys.mean()*4, xs.mean()*4   # in sub coords
    print(name, "approx centre (sub px)", round(cy,1), round(cx,1), "thr", round(thr,1))
    # radial profile about that centre
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    r = np.hypot(yy-cy, xx-cx)
    for rad in range(0, 700, 25):
        m = (r>=rad)&(r<rad+25)
        print("   r=%4d  med=%9.1f  n=%d" % (rad, np.median(sub[m]), m.sum()))
    print()
