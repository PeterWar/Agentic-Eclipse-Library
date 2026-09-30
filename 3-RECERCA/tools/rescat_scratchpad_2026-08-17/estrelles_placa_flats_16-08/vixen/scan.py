import numpy as np, rawpy, glob, os, json
D = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
files = sorted(glob.glob(D+"*.CR3"))
out = []
for f in files:
    with rawpy.imread(f) as raw:
        img = raw.raw_image_visible
    sat = int((img >= 16000).sum())
    hi = int((img >= 4000).sum())
    p999 = float(np.percentile(img[::7, ::7], 99.99))
    out.append((os.path.basename(f), sat, hi, p999, int(img.max())))
    print(out[-1], flush=True)
json.dump(out, open("scan.json","w"))
