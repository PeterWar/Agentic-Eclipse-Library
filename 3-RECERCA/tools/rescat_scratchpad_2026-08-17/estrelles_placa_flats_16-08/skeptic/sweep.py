import rawpy, numpy as np, os, json, sys
from concurrent.futures import ProcessPoolExecutor
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
files=sorted(f for f in os.listdir(D) if f.endswith(".CR3"))
def work(f):
    try:
        with rawpy.imread(D+f) as r:
            full=r.raw_image.astype(np.float64)
            vis=full[108:108+4639,172:172+6959]
            rp=full.mean(axis=1)
            h,w=vis.shape; sm=np.zeros((4,4))
            for i in range(4):
                for j in range(4):
                    sm[i,j]=vis[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4].mean()
            d=dict(f=f, vmean=float(vis.mean()), vmed=float(np.median(vis)), vstd=float(vis.std()),
                   vmax=float(vis.max()), n1000=int((vis>1000).sum()), n700=int((vis>700).sum()),
                   p999=float(np.percentile(vis,99.9)),
                   secamp=float(sm.max()-sm.min()), secmin=float(sm.min()), secmax=float(sm.max()),
                   r05=float(rp[:6].mean()), tm=float(rp[:108].mean()),
                   left=float(full[108:108+4639,:172].mean()),
                   std4=float(full[::4,::4].std()),
                   top40=float(vis[:40].mean()), bot40=float(vis[-40:].mean()))
        return d
    except Exception as e:
        return dict(f=f, err=str(e))
if __name__=="__main__":
    out=[]
    with ProcessPoolExecutor(max_workers=8) as ex:
        for i,d in enumerate(ex.map(work, files, chunksize=4)):
            out.append(d)
            if i%100==0: print(i, flush=True)
    json.dump(out, open("sweep768.json","w"))
    print("done", len(out))
