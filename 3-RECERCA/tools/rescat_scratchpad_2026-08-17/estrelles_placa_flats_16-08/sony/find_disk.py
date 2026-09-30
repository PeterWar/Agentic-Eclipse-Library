import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import plane
for nm in ["DSC06983.ARW","DSC06995.ARW","DSC06982.ARW","DSC06973.ARW","DSC07000.ARW"]:
    g=plane(nm)
    # coarse: downsample by 8
    h,w=g.shape
    d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    thr=np.percentile(d,99.9)*0.05
    ys,xs=np.nonzero(d>thr)
    print(nm, g.shape, "max",g.max(), "thr",round(thr,1),
          "bbox y",ys.min()*8,ys.max()*8,"x",xs.min()*8,xs.max()*8,
          "centroid", round(np.average(xs,weights=d[ys,xs])*8,1), round(np.average(ys,weights=d[ys,xs])*8,1))
