"""Low radial dimensionality model of angularly varying glare.
Unrestricted profile ONLY in angular mean; no independent profile per sector.
No synthetic terrain. An empirical nuisance fit, not absolute PSF recovery.
"""
from f3_global import *

def background_lowrank(a,cx=CXT,cy=CYT,ret=False):
    yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];rad=np.hypot(xx-cx,yy-cy);phi=np.arctan2(yy-cy,xx-cx)%(2*np.pi)
    rr=np.arange(.5,RL+41,1.);th=np.arange(1440)*2*np.pi/1440
    p=map_coordinates(a,[cy+np.sin(th[:,None])*rr,cx+np.cos(th[:,None])*rr],order=3,mode='nearest')
    profile=np.mean(p,axis=0);ri=np.clip(rad-.5,0,len(rr)-1)
    vr=map_coordinates(profile,[ri],order=3,mode='nearest')
    x,y=(xx-cx)/500,(yy-cy)/500;m=rad<.8*RL
    terms=[x**i*y**j for i in range(5) for j in range(5-i)]
    design=np.stack([t[m] for t in terms],axis=1);co=np.linalg.lstsq(design,(a-vr)[m],rcond=None)[0]
    poly=sum(c*t for c,t in zip(co,terms))
    pp=map_coordinates(poly,[cy+np.sin(th[:,None])*rr,cx+np.cos(th[:,None])*rr],order=3,mode='nearest')
    resid=p-profile[None]-pp
    # Only FIVE radial degrees of freedom across130pixels. Each basis is
    # anchored to zero at r360; no radial median can follow a crater packet.
    u=np.maximum((rr-360)/100,0)
    shape=gaussian_filter1d(profile,2.)
    ip=int(round(360-.5));shape=shape-shape[ip]
    shape[rr<360]=0
    derivative=np.gradient(gaussian_filter1d(profile,2.))
    derivative=derivative-derivative[ip];derivative[rr<360]=0
    basis=np.array([u,u*u,u*u*u,shape,derivative]).T
    fit=(rr>=365)&(rr<=475)
    scale=np.linalg.norm(basis[fit],axis=0);bb=basis/np.maximum(scale,1e-9)
    cf=np.linalg.lstsq(bb[fit],resid[:,fit].T,rcond=None)[0]
    # All amplitudes: smooth in angle20px at the rim. Derivative/phase: only
    # global plus m1,m2 harmonics, avoiding a free local shift per crater.
    cf=gaussian_filter1d(cf,20/(2*np.pi*RL/1440),axis=1,mode='wrap')
    ff=np.fft.rfft(cf[-1]);ff[3:]=0;cf[-1]=np.fft.irfft(ff,n=1440)
    correction=(bb@cf).T
    padded=np.pad(correction,((3,3),(0,0)),mode='wrap')
    cart=map_coordinates(padded,[phi*1440/(2*np.pi)+3,ri],order=3,mode='nearest')
    bg=vr+poly+cart
    return (bg,profile,cf,scale) if ret else bg

def detail_lowrank(g,cx=CXT,cy=CYT,sigma=64):
    g,valid=fill(g);z=np.log(np.maximum(g,1e-3));bg=background_lowrank(z,cx,cy)
    yy,xx=np.mgrid[:g.shape[0],:g.shape[1]];ph=np.arctan2(yy-cy,xx-cx)%(2*np.pi);edge=np.load(CAU44/'vixen_optical_edge.npy');lim=np.interp(ph*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
    surface=(np.hypot(xx-cx,yy-cy)<lim)&valid;res=z-bg
    den=gaussian_filter(surface.astype(float),sigma);low=gaussian_filter(res*surface,sigma)/np.maximum(den,1e-30);h=res-low;h[~surface]=0
    return h,bg,valid

def main():
    claim45();name=sys.argv[1] if len(sys.argv)>1 else 'combined_reference';g=np.load(CAU45/(name+'.npy'));h,bg,valid=detail_lowrank(g)
    np.save(CAU45/(name+'_lowrank_logdetail.npy'),h.astype(np.float32));np.save(CAU45/(name+'_lowrank_logbg.npy'),bg.astype(np.float32))
    d=np.clip(.176+.022*h/np.std(h[R<.8*RL]),0,1)*(R<454);png45('F3b_'+name+'.png',np.repeat(d[...,None],3,axis=2))
    from f4_judge import judge
    q=judge(h);savejson(REB45/('F4_lowrank_'+name+'.json'),q)
    print({b:{k:v for k,v in r.items() if k in ['cyan400_428','ring428_440','ring440_449']} for b,r in q.items()},flush=True)
if __name__=='__main__':main()
