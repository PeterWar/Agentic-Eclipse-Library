import rawpy, numpy as np
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
N=["572A3342","572A3343","572A3344","572A3454","572A3455","572A3456","572A3568","572A3569","572A3570",
   "572A4022","572A4023","572A4024","572A4135","572A4136","572A4137","572A4250","572A4251","572A4252",
   "572A4817","572A5288","572A6722","572A6723","572A6724","572A6836","572A6837"]
T=[40,40,40,44,44,44,44,43,43,39,38,38,41,41,41,41,41,41,44,44,41,41,40,44,44]
res=[]
for n,t in zip(N,T):
    with rawpy.imread(D+n+".CR3") as r:
        full=r.raw_image.astype(np.float64)
        vis=full[108:108+4639,172:172+6959]
        h,w=vis.shape; sm=np.array([[vis[i*h//4:(i+1)*h//4,j*w//4:(j+1)*w//4].mean() for j in range(4)] for i in range(4)])
        d=(t,float(vis.mean()),float(np.median(vis)),float(vis.std()),float(vis.max()),
           int((vis>1000).sum()),float(sm.max()-sm.min()),float(full[:6].mean()),float(full[:108].mean()),
           float(full[::4,::4].std()))
    res.append((n,)+d)
    print("%s T=%d mean %.4f med %.1f std %.4f max %.0f n>1k %5d secamp %.4f r05 %.1f tm %.2f std4 %.3f"%((n,)+d))
import numpy as np
a=np.array([r[2] for r in res]); tt=np.array([r[1] for r in res])
print("\nmean of frame means %.5f  sd %.5f  min %.4f max %.4f"%(a.mean(),a.std(),a.min(),a.max()))
for grp,lab in [(tt<=40,"T<=40"),(tt==41,"T==41"),(tt>=43,"T>=43")]:
    print(lab,"n=%d level %.4f  noise %.4f"%(grp.sum(),a[grp].mean(),np.array([r[4] for r in res])[grp].mean()))
p=np.polyfit(tt,a,1); print("fit level vs T: %.5f*T + %.3f ; r=%.4f"%(p[0],p[1],np.corrcoef(tt,a)[0,1]))
