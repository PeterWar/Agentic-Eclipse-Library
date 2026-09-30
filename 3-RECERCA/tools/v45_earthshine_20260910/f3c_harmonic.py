"""Linear low angular harmonic nuisance projection, no sector medians.
Low angular harmonics of the sky/glare are not identifiable as lunar terrain.
Their explicit removal/transfer is measured, never claimed lossless.
"""
from f3_global import *

def background_harmonic(a,cx=CXT,cy=CYT,modes=2):
    yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];rad=np.hypot(xx-cx,yy-cy);phi=np.arctan2(yy-cy,xx-cx)%(2*np.pi)
    rr=np.arange(.5,RL+41,1.);th=np.arange(1440)*2*np.pi/1440
    p=map_coordinates(a,[cy+np.sin(th[:,None])*rr,cx+np.cos(th[:,None])*rr],order=3,mode='nearest')
    ff=np.fft.rfft(p,axis=0);ff[modes+1:]=0;tab=np.fft.irfft(ff,n=1440,axis=0)
    ri=np.clip(rad-.5,0,len(rr)-1);tab=np.pad(tab,((3,3),(0,0)),mode='wrap')
    out=map_coordinates(tab,[phi*1440/(2*np.pi)+3,ri],order=3,mode='nearest')
    return out

def detail_harmonic(g,cx=CXT,cy=CYT,modes=2,sigma=64):
    g,valid=fill(g);z=np.log(np.maximum(g,1e-3));bg=background_harmonic(z,cx,cy,modes)
    yy,xx=np.mgrid[:g.shape[0],:g.shape[1]];ph=np.arctan2(yy-cy,xx-cx)%(2*np.pi);edge=np.load(CAU44/'vixen_optical_edge.npy');lim=np.interp(ph*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
    surface=(np.hypot(xx-cx,yy-cy)<lim)&valid;res=z-bg
    den=gaussian_filter(surface.astype(float),sigma);h=res-gaussian_filter(res*surface,sigma)/np.maximum(den,1e-30);h[~surface]=0
    return h,bg,valid

def main():
    claim45();g=np.load(CAU45/'combined_reference.npy')
    from f4_judge import judge
    for modes in [1,2,3,4,6]:
        h,bg,valid=detail_harmonic(g,modes=modes)
        np.save(CAU45/f'harmonic{modes}_logdetail.npy',h.astype(np.float32));np.save(CAU45/f'harmonic{modes}_logbg.npy',bg.astype(np.float32))
        d=np.clip(.176+.022*h/np.std(h[R<.8*RL]),0,1)*(R<454);png45(f'F3c_harmonic{modes}.png',np.repeat(d[...,None],3,axis=2))
        q=judge(h);savejson(REB45/f'F4_harmonic{modes}.json',q)
        print(modes,{b:{k:(round(v['r'],3),round(v['max_abs_null'],3)) for k,v in r.items() if k in ['cyan400_428','ring428_440','ring440_449','lila440_449']} for b,r in q.items()},flush=True)
if __name__=='__main__':main()
