import rawpy, numpy as np, sys
p="/Users/USUARI/Desktop/Eclipse 2026/300mm/DSC06983.ARW"
with rawpy.imread(p) as r:
    raw=r.raw_image_visible.astype(np.float64)
    col=r.raw_colors_visible
    print("shape",raw.shape,"pattern",r.raw_pattern, r.color_desc)
    print("black_level_per_channel",r.black_level_per_channel,"white",r.white_level)
    print("cam pattern top-left 2x2 colors:",col[:2,:2])
    print("min/max",raw.min(),raw.max())
    g=(col==1)
    print("green frac",g.mean())
