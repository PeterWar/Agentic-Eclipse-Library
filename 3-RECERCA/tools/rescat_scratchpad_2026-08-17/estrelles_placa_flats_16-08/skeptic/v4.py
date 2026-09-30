import rawpy, numpy as np, json
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
names=["572A3332","572A3350","572A3444","572A3462","572A3558","572A3576","572A4012","572A4030",
       "572A4125","572A4143","572A4240","572A4258","572A5219","572A6712","572A6730","572A6843"]
T={"572A3332":41,"572A3350":40,"572A3444":44,"572A3462":44,"572A3558":44,"572A3576":44,
   "572A4012":39,"572A4030":39,"572A4125":42,"572A4143":41,"572A4240":42,"572A4258":41,
   "572A5219":42,"572A6712":42,"572A6730":41,"572A6843":44}
rows=[]; secs=[]; prof=[]
for n in names:
    with rawpy.imread(D+n+".CR3") as r:
        full=r.raw_image.astype(np.float64)
        cols=r.raw_colors_visible
        vis=full[108:108+4639,172:172+6959]
        rp=full.mean(axis=1)
        # per-bayer pedestal on visible
        ped=[float(np.median(vis[cols==c])) for c in range(4)]
        sd =[float(vis[cols==c].std()) for c in range(4)]
        # 4x4 sector means of visible
        h,w=vis.shape; sm=np.zeros((4,4))
        for i in range(4):
            for j in range(4):
                sm[i,j]=vis[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4].mean()
        # image top rows (first 40 rows of the visible area) vs bulk
        toprows=vis[:40].mean(); bulk=vis[200:].mean()
    rows.append(dict(n=n,T=T[n],r05=float(rp[:6].mean()),r0=float(rp[0]),r1=float(rp[1]),r2=float(rp[2]),
        r3=float(rp[3]),r4=float(rp[4]),r5=float(rp[5]),r6=float(rp[6]),r7=float(rp[7]),r8=float(rp[8]),
        tm=float(rp[:108].mean()),
        vmean=float(vis.mean()),vstd=float(vis.std()),vmed=float(np.median(vis)),
        vmax=float(vis.max()),n1000=int((vis>1000).sum()),ped=ped,sd=sd,
        secmin=float(sm.min()),secmax=float(sm.max()),secamp=float(sm.max()-sm.min()),
        toprows=float(toprows),bulk=float(bulk)))
    prof.append(rp[:200])
    print(rows[-1]["n"],rows[-1]["T"],"r0-5=%8.1f"%rows[-1]["r05"],"r2=%6.1f r3=%6.1f r6=%6.1f r7=%6.1f"%(rows[-1]["r2"],rows[-1]["r3"],rows[-1]["r6"],rows[-1]["r7"]),
          "vis mean %.4f std %.4f max %.0f n>1000=%d"%(rows[-1]["vmean"],rows[-1]["vstd"],rows[-1]["vmax"],rows[-1]["n1000"]),
          "ped",np.round(ped,2),"secamp %.4f"%rows[-1]["secamp"],"top40 %.4f bulk %.4f"%(toprows,bulk))
np.save("prof16.npy",np.array(prof))
json.dump(rows,open("rows16.json","w"),indent=1)
