import rawpy, numpy as np, os
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
frames={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
        'DSC06990':8.0,'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
for f,e in sorted(frames.items()):
    with rawpy.imread(D+f+".ARW") as r:
        v=r.raw_image_visible.astype(np.float32)
    x=v-512.0
    # 8x8 block mean for a coarse map
    h,w=x.shape
    b=x[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    sat=(v>=16380)
    ys,xs=np.nonzero(sat)
    print(f"{f} exp={e}s sat_px={sat.sum()}", end=" ")
    if sat.sum()>100:
        print(f"sat_centroid=({xs.mean():.0f},{ys.mean():.0f}) bbox x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]", end=" ")
    print(f"p50={np.percentile(x,50):.0f} p1={np.percentile(x,1):.0f} max={x.max():.0f}")
    np.save(f"coarse_{f}.npy", b.astype(np.float32))
