import rawpy, numpy as np, pickle, sys
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
OFF=pickle.load(open("offsets2.pkl","rb"))['off']
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
def show(xr,yr,frames,H=9):
    for n in frames:
        dx,dy=OFF[n]; x=int(round(xr+dx)); y=int(round(yr+dy))
        md=np.load(f"masterdark_{int(EXP[n])}s.npy")
        with rawpy.imread(D+n+".ARW") as r:
            raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
        bkg=np.load(f"bkg_{n}.npy")
        st=(raw-md-bkg)[y-H:y+H+1,x-H:x+H+1]/EXP[n]
        cc=col[y-H:y+H+1,x-H:x+H+1]
        g=(cc==1)|(cc==3)
        print(f"--- {n} ({EXP[n]}s) sensor=({x},{y})  green residual, ADU/s ---")
        for i in range(st.shape[0]):
            print("  "+" ".join(f"{st[i,j]:6.0f}" if g[i,j] else "     ." for j in range(st.shape[1])))
        del raw,bkg
xr,yr=int(sys.argv[1]),int(sys.argv[2])
show(xr,yr,sys.argv[3].split(","))
