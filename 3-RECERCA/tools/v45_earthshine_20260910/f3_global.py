"""Single Cartesian high-pass, no patch mosaic, no angular detail overlay.
Background's radial profiles are not radially smoothed; cubic interpolation.
"""
from comu45 import *
from scipy.ndimage import map_coordinates,distance_transform_edt,gaussian_filter,gaussian_filter1d

def fill(a):
    a=np.asarray(a,dtype=float);valid=np.isfinite(a)
    if not valid.any():raise ValueError('No finite source')
    if valid.all():return a.copy(),valid
    ix=distance_transform_edt(~valid,return_distances=False,return_indices=True)
    return a[tuple(ix)],valid

def background(a,cx=CXT,cy=CYT):
    assert np.isfinite(a).all()
    yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];rad=np.hypot(xx-cx,yy-cy);phi=np.arctan2(yy-cy,xx-cx)
    rr=np.arange(.5,RL+41,1.);th=np.arange(1440)*2*np.pi/1440
    p=map_coordinates(a,[cy+np.sin(th[:,None])*rr,cx+np.cos(th[:,None])*rr],order=3,mode='nearest')
    ri=np.clip(rad-.5,0,len(rr)-1)
    vr=map_coordinates(np.median(p,axis=0),[ri],order=3,mode='nearest')
    x,y=(xx-cx)/500,(yy-cy)/500;m=rad<.83*RL
    terms=[x**i*y**j for i in range(5) for j in range(5-i)]
    design=np.stack([t[m] for t in terms],axis=1);co=np.linalg.lstsq(design,(a-vr)[m],rcond=None)[0]
    v0=vr+sum(c*t for c,t in zip(co,terms));tab=[]
    for j in range(36):tab.append(np.median(p[np.arange(j*40-40,j*40+41)%1440],axis=0))
    tab=np.pad(np.array(tab),((3,3),(0,0)),mode='wrap')
    vs=map_coordinates(tab,[(phi%(2*np.pi))*36/(2*np.pi)+3,ri],order=3,mode='nearest')
    t=np.clip((rad-.82*RL)/(.08*RL),0,1);w=t*t*(3-2*t)
    return (1-w)*v0+w*vs

def detail(g,logarithmic=True,cx=CXT,cy=CYT,sigma=16):
    g,valid=fill(g)
    a=np.log(np.maximum(g,1e-3)) if logarithmic else g
    bg=background(a,cx,cy);res=a-bg
    yy,xx=np.mgrid[:g.shape[0],:g.shape[1]]
    ph=np.arctan2(yy-cy,xx-cx)%(2*np.pi)
    edge=np.load(CAU44/'vixen_optical_edge.npy')
    lim=np.interp(ph*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
    surface=(np.hypot(xx-cx,yy-cy)<lim)&valid
    # Only observed lunar samples enter the detail operator, even at the last
    # pixel. Normalize the truncated Cartesian kernel by its actual support.
    den=gaussian_filter(surface.astype(float),sigma)
    low=gaussian_filter(res*surface,sigma)/np.maximum(den,1e-30)
    h=res-low
    h[~surface]=0.
    return h,bg,valid

def main():
    claim45();report={}
    for name in ['vixen_all','vixen_reference','vixen_corrected','sony_all','sony_reference','sony_corrected','combined_all','combined_reference','combined_corrected']:
        g=np.load(CAU45/(name+'.npy'));h,bg,valid=detail(g)
        np.save(CAU45/(name+'_logdetail.npy'),h.astype(np.float32));np.save(CAU45/(name+'_logbg.npy'),bg.astype(np.float32))
        scale=float(np.std(h[R<.8*RL]));display=np.clip(.176+.022*h/max(scale,1e-12),0,1)*(R<454)
        png45('F3_'+name+'.png',np.repeat(display[...,None],3,axis=2))
        report[name]=dict(negative_inner=int(((g<=0)&(R<454)).sum()),rms_inner=float(np.std(h[R<.8*RL])),rms_420_435=float(np.std(h[(R>420)&(R<435)])),rms_435_450=float(np.std(h[(R>435)&(R<450)])))
        print(name,report[name],flush=True)
    savejson(REB45/'F3_global.json',report)
if __name__=='__main__':main()
