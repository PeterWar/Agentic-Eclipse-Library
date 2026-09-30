import numpy as np, json, lib, warnings; warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
cand=np.load('cand.npy'); SH=json.load(open('shifts_start.json'))
FR=[('572A2978',1.0,'1'),('572A2979',2.0,'2'),('572A2980',2.0,'2'),('572A2981',2.0,'2'),
    ('572A2982',10.3,'10'),('572A2983',10.3,'10'),('572A2984',10.3,'10'),('572A2996',1.0,'1')]
hm={k:lib.hotmask('dark_med_%s.npy'%k) for k in ['1','2','10']}
dk={k:np.load('dark_med_%s.npy'%k)[:lib.H,:lib.W] for k in ['1','2','10']}
K=380
G={}
for f,exp,dkey in FR:
    im=lib.load_raw(f); sat=im>=lib.SAT; im=im-dk[dkey]
    bad=ndi.binary_dilation(sat|hm[dkey],np.ones((3,3)))
    G[f]=lib.green_full(im,bad); del im,sat,bad
allp=[]
for tid in [0,2]:
    X0,Y0=cand[tid,0],cand[tid,1]
    num=np.zeros((2*K+1,2*K+1)); den=np.zeros((2*K+1,2*K+1))
    for f,exp,dkey in FR:
        g=G[f]; dt,dx,dy=SH[f]
        X,Y=X0+dx,Y0+dy; xi,yi=int(round(X)),int(round(Y))
        if xi<K or yi<K or xi>=lib.W-K or yi>=lib.H-K: print(' skip',f); continue
        raw=g[yi-K:yi+K+1,xi-K:xi+K+1].astype(np.float64)
        okm0=np.isfinite(raw)
        sub=ndi.shift(np.nan_to_num(raw),(-(Y-yi),-(X-xi)),order=1,cval=0)
        okm=ndi.shift(okm0.astype(float),(-(Y-yi),-(X-xi)),order=1,cval=0)>0.99
        sig=np.median(np.abs(raw[okm0]-np.median(raw[okm0])))*1.4826
        w=np.where(okm,(exp/sig)**2,0.0)
        num+=w*np.where(okm,sub/exp,0); den+=w
    st=np.where(den>0,num/np.maximum(den,1e-12),np.nan)
    sg=np.where(den>0,1/np.sqrt(np.maximum(den,1e-12)),np.nan)
    yy,xx=np.mgrid[-K:K+1,-K:K+1]; rr=np.hypot(xx,yy)
    m=(rr>200)&(rr<=K)&np.isfinite(st)
    A=np.vstack([np.ones(m.sum()),xx[m],yy[m],xx[m]**2,yy[m]**2,xx[m]*yy[m],xx[m]**3,yy[m]**3]).T
    c,_,_,_=np.linalg.lstsq(A,st[m],rcond=None)
    bg=(c[0]+c[1]*xx+c[2]*yy+c[3]*xx**2+c[4]*yy**2+c[5]*xx*yy+c[6]*xx**3+c[7]*yy**3)
    d=st-bg
    tot=np.nansum(d[rr<=12])
    # systematics floor: scatter of annulus medians in 200-380 (should be 0)
    ctrl=[]
    for a in range(200,370,20):
        k=(rr>=a)&(rr<a+20)&np.isfinite(d); ctrl.append(np.median(d[k]))
    sysfl=np.std(ctrl)
    print('=== id=%d  total(r<12)=%.1f ADU/s   background systematic floor = %.3f ADU/s/px'%(tid,tot,sysfl))
    bins=[0,1,2,3,4,5,6,8,10,13,16,20,25,32,40,50,63,80,100,130,170]
    print('   r_px    r_arcsec   I(ADU/s/px)   I/Itot     stat_err   -> 3sig upper limit on I/Itot')
    for a,b in zip(bins[:-1],bins[1:]):
        k=(rr>=a)&(rr<b)&np.isfinite(d)
        if k.sum()<3: continue
        v=np.median(d[k]); n=np.nanmedian(sg[k])/np.sqrt(k.sum())*1.25
        e=np.hypot(n,sysfl)
        print('   %3d-%3d %8.1f  %12.4f  %10.3e  %9.4f    %.2e'%(a,b,(a+b)/2*2.158,v,v/tot,e,3*e/tot))
