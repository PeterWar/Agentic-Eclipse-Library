import numpy as np, json, lib, warnings; warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
cand=np.load('cand.npy'); SH=json.load(open('shifts_start.json'))
FR=[('572A2978',1.0,'1'),('572A2979',2.0,'2'),('572A2980',2.0,'2'),('572A2981',2.0,'2'),
    ('572A2982',10.3,'10'),('572A2983',10.3,'10'),('572A2984',10.3,'10'),('572A2996',1.0,'1')]
hm={k:lib.hotmask('dark_med_%s.npy'%k) for k in ['1','2','10']}
dk={k:np.load('dark_med_%s.npy'%k)[:lib.H,:lib.W] for k in ['1','2','10']}
K=170
targets=[(0,cand[0,0],cand[0,1]),(1,cand[1,0],cand[1,1]),(2,cand[2,0],cand[2,1])]
G={}
for f,exp,dkey in FR:
    im=lib.load_raw(f); sat=im>=lib.SAT; im=im-dk[dkey]
    bad=ndi.binary_dilation(sat|hm[dkey],np.ones((3,3)))
    g=lib.green_full(im,bad); G[f]=(g,exp)
    del im,sat,bad
prof={}
for (tid,X0,Y0) in targets:
    num=np.zeros((2*K+1,2*K+1)); den=np.zeros((2*K+1,2*K+1))
    for f,exp,dkey in FR:
        g,_=G[f]; dt,dx,dy=SH[f]
        X,Y=X0+dx,Y0+dy; xi,yi=int(round(X)),int(round(Y))
        if xi<K or yi<K or xi>=lib.W-K or yi>=lib.H-K: continue
        sub=g[yi-K:yi+K+1,xi-K:xi+K+1].astype(np.float64)
        # shift by subpixel remainder so the star sits at the centre
        rx,ry=X-xi,Y-yi
        sub=ndi.shift(np.nan_to_num(sub,nan=0.0),(-ry,-rx),order=1,cval=0)
        okm=ndi.shift(np.isfinite(sub).astype(float)*np.isfinite(g[yi-K:yi+K+1,xi-K:xi+K+1]).astype(float),(-ry,-rx),order=1,cval=0)>0.99
        sig=np.nanmedian(np.abs(sub-np.nanmedian(sub)))*1.4826
        w=np.where(okm,(exp/sig)**2,0.0)
        num+=w*np.where(okm,sub/exp,0); den+=w
    st=np.where(den>0,num/np.maximum(den,1e-12),np.nan)
    sg=np.where(den>0,1/np.sqrt(np.maximum(den,1e-12)),np.nan)
    yy,xx=np.mgrid[-K:K+1,-K:K+1]; rr=np.hypot(xx,yy)
    # background: plane+quadratic fit on 120<r<K
    m=(rr>120)&(rr<=K)&np.isfinite(st)
    A=np.vstack([np.ones(m.sum()),xx[m],yy[m],xx[m]**2,yy[m]**2,xx[m]*yy[m]]).T
    c,_,_,_=np.linalg.lstsq(A,st[m],rcond=None)
    bg=c[0]+c[1]*xx+c[2]*yy+c[3]*xx**2+c[4]*yy**2+c[5]*xx*yy
    d=st-bg
    tot=np.nansum(d[rr<=12])
    bins=[0,1,2,3,4,5,6,8,10,13,16,20,25,32,40,50,63,80,100,120]
    print('=== source id=%d  total flux(r<12) = %.1f ADU/s'%(tid,tot))
    print('  r_px  r_arcsec   I(ADU/s/px)   I/Itot(1/px)   snr_of_annulus')
    rows=[]
    for a,b in zip(bins[:-1],bins[1:]):
        k=(rr>=a)&(rr<b)&np.isfinite(d)
        if k.sum()<3: continue
        v=np.median(d[k]); n=np.nanmedian(sg[k])/np.sqrt(k.sum())*1.25
        print('  %3d-%3d %7.1f  %12.4f  %13.3e  %8.1f'%(a,b,(a+b)/2*2.158,v,v/tot,v/max(n,1e-9)))
        rows.append(((a+b)/2,v,v/tot,v/max(n,1e-9)))
    prof[tid]=rows
json.dump({str(k):v for k,v in prof.items()},open('wings.json','w'))
