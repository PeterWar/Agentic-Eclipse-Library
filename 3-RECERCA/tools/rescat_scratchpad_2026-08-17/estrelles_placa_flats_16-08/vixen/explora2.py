import numpy as np, rawpy

D = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
name = "572A3030.CR3"
with rawpy.imread(D+name) as raw:
    img = raw.raw_image_visible.astype(np.float64)
    col = raw.raw_colors_visible.copy()
    print("color_desc", raw.color_desc, "pattern\n", raw.raw_pattern)
    print("black_level_per_channel", raw.black_level_per_channel, "white", raw.white_level)

# green plane: take pattern-aware. Build 2x2 downsample of full frame as luminance proxy
h, w = img.shape
sub = img[:h//2*2, :w//2*2].reshape(h//2,2,w//2,2).mean(axis=(1,3)) - 512.0
print("sub shape", sub.shape, "max", sub.max())

# coarse: bin by 8
s2 = sub[:sub.shape[0]//8*8, :sub.shape[1]//8*8].reshape(sub.shape[0]//8,8,sub.shape[1]//8,8).mean(axis=(1,3))
np.save("sub_3030.npy", sub)
ys, xs = np.where(s2 > 50)
print("bright bbox in sub-coords:", ys.min()*8, ys.max()*8, xs.min()*8, xs.max()*8)
print("centroid approx", ys.mean()*8, xs.mean()*8)
# print profile row through centroid
cy = int(ys.mean()*8); cx = int(xs.mean()*8)
print("cy,cx", cy, cx)
print(np.round(sub[cy, cx-400:cx+400:20],1))
