import numpy as np, json
FR=[('572A2978',1.0,73742.55),('572A2979',2.0,73744.45),('572A2980',2.0,73747.35),('572A2981',2.0,73750.26),
    ('572A2982',10.3,73753.41),('572A2983',10.3,73766.48),('572A2984',10.3,73779.88),('572A2996',1.0,73804.26)]
seeds=[(6548.47,1622.03),(1131.82,298.03),(5881.93,4183.48),(4021.31,391.36),(82.28,3243.45),
       (6451.73,1157.89),(3091.45,3333.42),(6081.62,3299.79)]
V=np.array([0.199,-0.214])
S={f:np.load('snr_%s.npy'%f) for f,_,_ in FR}
def centroid(img,x,y,box=7):
    x0=int(round(x)); y0=int(round(y))
    sub=img[max(0,y0-box):y0+box+1, max(0,x0-box):x0+box+1].astype(np.float64)
    if sub.size==0: return None
    w=np.clip(sub,0,None)**2
    if w.sum()<=0: return None
    yy,xx=np.mgrid[0:sub.shape[0],0:sub.shape[1]]
    cx=(w*xx).sum()/w.sum(); cy=(w*yy).sum()/w.sum()
    return max(0,x0-box)+cx, max(0,y0-box)+cy, sub.max()
for tref in ['start','end']:
    print('=== EXIF interpretation:',tref)
    def mid(exp,t): return t+exp/2 if tref=='start' else t-exp/2
    t0=mid(10.3,73753.41)
    out={}
    for f,exp,t in FR:
        dt=mid(exp,t)-t0
        pred=V*dt
        ds=[]
        for (sx,sy) in seeds:
            px,py=sx+pred[0],sy+pred[1]
            # coarse: max in +-10 box
            x0,y0=int(round(px)),int(round(py))
            sub=S[f][max(0,y0-10):y0+11,max(0,x0-10):x0+11]
            if sub.size==0: continue
            j,i=np.unravel_index(np.argmax(sub),sub.shape)
            gx=max(0,x0-10)+i; gy=max(0,y0-10)+j
            if sub.max()<5: continue
            c=centroid(S[f],gx,gy,box=6)
            if c is None: continue
            ds.append((c[0]-sx,c[1]-sy,c[2]))
        ds=np.array(ds)
        med=np.median(ds[:,:2],axis=0)
        rms=np.std(ds[:,:2]-med,axis=0)
        print('  %s dt=%7.2f  n=%d  dx=%7.3f dy=%7.3f  scatter (%.2f,%.2f)  pred(%.2f,%.2f)'%(f,dt,len(ds),med[0],med[1],rms[0],rms[1],pred[0],pred[1]))
        out[f]=(dt,med[0],med[1])
    # fit v
    dts=np.array([out[f][0] for f,_,_ in FR]); dxs=np.array([out[f][1] for f,_,_ in FR]); dys=np.array([out[f][2] for f,_,_ in FR])
    A=np.vstack([dts,np.ones_like(dts)]).T
    cx,_,_,_=np.linalg.lstsq(A,dxs,rcond=None); cy,_,_,_=np.linalg.lstsq(A,dys,rcond=None)
    rx=dxs-A@cx; ry=dys-A@cy
    print('  fit vx=%.4f vy=%.4f px/s |v|=%.4f px/s = %.3f arcsec/s  resid rms=(%.3f,%.3f) px'%(cx[0],cy[0],np.hypot(cx[0],cy[0]),np.hypot(cx[0],cy[0])*2.158,rx.std(),ry.std()))
    json.dump({f:out[f] for f,_,_ in FR},open('shifts_%s.json'%tref,'w'))
