import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
from scipy.optimize import least_squares
from scipy.ndimage import binary_fill_holes, label, binary_closing
DIR={'vixen':"/Users/USUARI/Desktop/Eclipse 2026/Vixen/",'sony':"/Users/USUARI/Desktop/Eclipse 2026/300mm/"}
EXT={'vixen':'.CR3','sony':'.ARW'}
def bright_blob(v,k=8,q=0.30):
    s=np.clip(v,0,None); h,w=s.shape
    sb=s[:h//k*k,:w//k*k].reshape(h//k,k,w//k,k).mean(axis=(1,3))
    m=binary_fill_holes(binary_closing(sb>q*np.percentile(sb,99.99),np.ones((3,3))))
    lab,n=label(m); sz=np.bincount(lab.ravel()); sz[0]=0; i=sz.argmax()
    ys,xs=np.nonzero(lab==i)
    return (xs.mean()+0.5)*k,(ys.mean()+0.5)*k, math.sqrt(sz[i]/math.pi)*k
def sfs(x,y,val,cx,cy,R,halfwin,nsec,sat,minc=80.,maxr=0.15):
    dx=x-cx; dy=y-cy; r=np.hypot(dx,dy); sel=np.abs(r-R)<halfwin
    u=-(r[sel]-R); th=np.arctan2(dy[sel],dx[sel]); vv=val[sel]
    ib=((th+np.pi)/(2*np.pi)*nsec).astype(int)%nsec
    o=np.argsort(ib,kind='stable'); u=u[o]; vv=vv[o]; ib=ib[o]
    b=np.searchsorted(ib,np.arange(nsec+1)); out=[]
    for a in range(nsec):
        i0,i1=b[a],b[a+1]
        if i1-i0<18: continue
        us=u[i0:i1]; vs=vv[i0:i1]
        if np.max(vs)>sat: continue
        P0=np.median(vs[us<-0.5*halfwin]); O0=np.median(vs[us>0.5*halfwin])
        if not np.isfinite(P0) or not np.isfinite(O0) or (O0-P0)<minc: continue
        def res(p):
            P,c0,c1,u0,s=p
            return P+(c0+c1*us)*Phi((us-u0)/s)-vs
        try: sol=least_squares(res,[P0,O0-P0,0.,0.,1.],bounds=([-np.inf,1e-3,-np.inf,-4.,0.15],[np.inf,np.inf,np.inf,4.,8.]),max_nfev=400)
        except Exception: continue
        if not sol.success: continue
        P,c0,c1,u0,s=sol.x; rms=math.sqrt(np.mean(sol.fun**2))
        if abs(u0)>3 or c0<=0 or rms/c0>maxr: continue
        den=c0+c1*us; ok=den>0.3*c0
        out.append(dict(a=a,u=us[ok],y=(vs[ok]-P)/den[ok],u0=u0,s=s,c0=c0,rms=rms,snr=c0/rms,n=int(ok.sum())))
    return out
def solar(train,name,tt=''):
    t=TRAINS[train]
    v,c,white=load(DIR[train]+name+EXT[train])
    x,y,val=pick(v,c,'G')
    cx,cy,R=bright_blob(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(x,y,-val,cx,cy,R,win=w)
    Ras=R*t['scale']
    if abs(Ras-946)>40: return dict(train=train,frame=name,t=tt,bad='R=%.0f"'%Ras)
    f=sfs(x,y,val,cx,cy,R,30/t['scale'],240,(white-512)*0.93)
    if len(f)<25: return dict(train=train,frame=name,t=tt,bad='sect=%d'%len(f))
    xc,ym,e,cnt=stack_esf(f,align=True,xlim=20/t['scale'],bw=0.05)
    fit=fit_esf(xc,ym,e,boxw=1.0)
    return dict(train=train,frame=name,t=tt,R=Ras,n=len(f),
                fwhm=fit['fwhm_tot']*t['scale'],snr=float(np.median([q['snr'] for q in f])))
if __name__=='__main__':
    import json
    for train,name,tt in json.loads(sys.argv[1]):
        r=solar(train,name,tt)
        if 'bad' in r: print(f"{train:5s} {name} {tt} REFUSAT {r['bad']}",flush=True)
        else: print(f"{train:5s} {name} {tt} R={r['R']:.0f}\" sect={r['n']:3d} FWHM={r['fwhm']:.2f}\" S/N={r['snr']:.0f}",flush=True)
