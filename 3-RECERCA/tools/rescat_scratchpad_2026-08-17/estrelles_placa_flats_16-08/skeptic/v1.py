import rawpy, numpy as np, os
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
tgt=["572A3444","572A4030","572A3332","572A6843","572A3558","572A3462","572A3576","572A5219","572A4012"]
for n in tgt:
    with rawpy.imread(D+n+".CR3") as r:
        full=r.raw_image.astype(np.float64)
        vis=r.raw_image_visible.astype(np.float64)
    print(n, "shape_full",full.shape,"vis",vis.shape)
    print("   full.std=%.6f  [::4,::4].std=%.10f  [::2,::2].std=%.6f  [::3,::3].std=%.6f  [::8,::8].std=%.6f"%(
        full.std(), full[::4,::4].std(), full[::2,::2].std(), full[::3,::3].std(), full[::8,::8].std()))
    print("   vis.std=%.6f vis[::4,::4].std=%.6f  vis.mean=%.4f vis.median=%.1f"%(vis.std(), vis[::4,::4].std(), vis.mean(), np.median(vis)))
