"""Comparacio dels DOS trens a la MATEIXA hora, amb filtre, just abans de la
totalitat. Limbe SOLAR. Localitzacio del centre per votacio de Hough amb el
radi solar conegut, que es el que permet mesurar creixents prims."""
import sys, numpy as np, math, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import load,pick,fit_circle,stack_esf,fit_esf,Phi
from run import TRAINS
from scipy.optimize import least_squares
from scipy.ndimage import uniform_filter
DIR={'vixen':"/Users/USUARI/Desktop/Eclipse 2026/Vixen/",'sony':"/Users/USUARI/Desktop/Eclipse 2026/300mm/"}
EXT={'vixen':'.CR3','sony':'.ARW'}

def hough(v,Rpx):
    k=4
    h,w=v.shape
    s=np.clip(v,0,None)[:h//k*k,:w//k*k].reshape(h//k,k,w//k,k).mean(axis=(1,3))
    thr=0.5*np.percentile(s,99.9)
    gy,gx=np.gradient(s)
    g=np.hypot(gx,gy)
    ys,xs=np.nonzero((g>np.percentile(g,99.5)))
    if xs.size>20000:
        i=np.random.default_rng(3).choice(xs.size,20000,replace=False); xs,ys=xs[i],ys[i]
    # direccio del gradient apunta cap a dins (mes brillant): centre = punt + R*grad_norm
    gxx=gx[ys,xs]; gyy=gy[ys,xs]; n=np.hypot(gxx,gyy)+1e-9
    R=Rpx/k
    cx=xs+R*gxx/n; cy=ys+R*gyy/n
    H,xe,ye=np.histogram2d(cx,cy,bins=[np.arange(-R,s.shape[1]+R,2),np.arange(-R,s.shape[0]+R,2)])
    H=uniform_filter(H,3)
    i,j=np.unravel_index(H.argmax(),H.shape)
    return (0.5*(xe[i]+xe[i+1]))*k,(0.5*(ye[j]+ye[j+1]))*k

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

def solar(train,name):
    t=TRAINS[train]
    v,c,white=load(DIR[train]+name+EXT[train])
    x,y,val=pick(v,c,'G')
    Rpx=946.0/t['scale']
    cx,cy=hough(v,Rpx)
    R=Rpx
    for w in (40.,20.):
        cx,cy,R,sd,ng=fit_circle(x,y,-val,cx,cy,R,win=w)
        if abs(R*t['scale']-946)>60: R=Rpx
    Ras=R*t['scale']
    f=sfs(x,y,val,cx,cy,Rpx,30/t['scale'],240,(white-512)*0.93)
    if len(f)<15: return dict(bad='sect=%d R=%.0f'%(len(f),Ras))
    xc,ym,e,cnt=stack_esf(f,align=True,xlim=20/t['scale'],bw=0.05)
    fit=fit_esf(xc,ym,e,boxw=1.0)
    return dict(R=Ras,n=len(f),fwhm=fit['fwhm_tot']*t['scale'],
                snr=float(np.median([q['snr'] for q in f])))

PAIRS=[('20:22:21','572A2923','DSC06957'),('20:22:51','572A2924','DSC06958'),
       ('20:23:20','572A2925','DSC06959'),('20:23:50','572A2926','DSC06960'),
       ('20:24:19','572A2927','DSC06961'),('20:24:49','572A2928','DSC06962'),
       ('20:25:18','572A2929','DSC06963')]
for tt,vn,sn in PAIRS:
    rv=solar('vixen',vn); rs=solar('sony',sn)
    def fmt(r,tr):
        if 'bad' in r: return f"{tr}=REFUSAT({r['bad']})"
        return f"{tr}: R={r['R']:.0f}\" sec={r['n']:3d} FWHM={r['fwhm']:5.2f}\" S/N={r['snr']:.0f}"
    print(f"{tt}  {fmt(rv,'VIXEN '+vn)}   ||   {fmt(rs,'SONY '+sn)}",flush=True)
