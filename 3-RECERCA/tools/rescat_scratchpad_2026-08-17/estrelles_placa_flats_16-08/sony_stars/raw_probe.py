import rawpy, numpy as np
p="/Users/USUARI/Desktop/Eclipse 2026/300mm/DSC06987.ARW"
with rawpy.imread(p) as r:
    print("raw_image", r.raw_image.shape, r.raw_image.dtype)
    v=r.raw_image_visible
    print("visible", v.shape)
    c=r.raw_colors_visible
    print("colors", c.shape, np.unique(c, return_counts=True))
    print("pattern", r.raw_pattern, r.color_desc)
    print("black_level_per_channel", r.black_level_per_channel)
    print("white_level", r.white_level)
    print("camera_white_balance", r.camera_whitebalance)
    print("top-left 4x4 colors\n", c[:4,:4])
    print("min/max/median visible", v.min(), v.max(), np.median(v))
    # pedestal check on a dark corner region
    print("corner stats", v[:200,:200].mean(), v[:200,:200].std())
