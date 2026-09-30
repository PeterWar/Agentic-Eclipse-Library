"""Product QA: fixed LROC judge, exact cyan support, unique angular nulls,
weak-signal transfer on measured backgrounds and directional transfer tests.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter
from f3b_detall_log import local_detail

def load_lroc():
    lr=np.load(HERE42/'cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox']
    L=np.zeros((N,N),np.float32);y,x=bb[1]-Y0,bb[0]-X0;L[y:y+lr.shape[0],x:x+lr.shape[1]]=lr[...,:3].mean(-1)
    return np.log(np.maximum(L,1e-3))

def qa_polar():
    na=1440;rr=np.arange(.83*RL,RL,1.);th=np.arange(na)*2*np.pi/na
    mx=(CXT+rr[:,None]*np.cos(th)).astype(np.float32);my=(CYT+rr[:,None]*np.sin(th)).astype(np.float32)
    def polar(z):return cv2.remap(np.asarray(z,np.float32),mx,my,cv2.INTER_LINEAR)
    L=polar(load_lroc());cyan=cv2.remap(np.load(CAU44/'marques_cian.npy').astype(np.uint8),mx,my,cv2.INTER_NEAREST)>0
    freq=np.fft.rfftfreq(na)[None,:]*na/(2*np.pi*rr[:,None]);bands=(freq>=1/24)&(freq<=1/16)
    filt=lambda z:np.fft.irfft(np.fft.rfft(z,axis=1)*bands,n=na,axis=1)
    ll=filt(L)
    ims={'V43_raw_log':np.log(np.maximum(np.load(CAU43/'e43_lineal_tessella.npy')[...,1],1e-3)),
         'V44_raw_log':np.log(np.maximum(np.load(CAU44/'surface_clean_rgb.npy')[...,1],1e-3)),
         'V44_isotropic':np.load(CAU44/'surface_clean_detail_log.npy'),
         'V44_tangential':np.load(CAU44/'surface_clean_detail_tangent.npy'),
         'V44_final_relief':np.load(CAU44/'relief_display_DN.npy'),
         'V44_final_display':np.log(np.maximum(np.load(CAU44/'earthshine_natural_disc.npy')[...,1],1e-4))}
    out={}
    for name,z in ims.items():
        q=filt(polar(np.nan_to_num(z)));rows={}
        for a,b in [(.84,.88),(.88,.92),(.92,.96),(.96,.995)]:
            m=cyan & (rr[:,None]>=a*RL)&(rr[:,None]<b*RL)
            score=pear(q,ll,m);nulls=[pear(q,np.roll(ll,na*k//12,axis=1),m) for k in range(1,12)]
            rows[f'{a:.2f}-{b:.3f}']=dict(n=int(m.sum()),r=score,nulls_unique_30_to_330=nulls,max_abs_null=max(map(abs,nulls)),passes=bool(score>max(map(abs,nulls))))
        out[name]=rows
    return out

def weak_probe():
    full=np.load(CAU44/'surface_clean_rgb.npy')[...,1];rows=[]
    # Real inner and outer backgrounds; source perturbation is0.05DN, independent of LROC.
    for label,xy in [('inner',(560,560)),('outer',(560,272))]:
        x0,y0=xy;g=full[y0:y0+256,x0:x0+256].astype(float)
        def op(x):
            z=np.log(np.maximum(x,1e-3));return local_detail(z)*np.exp(gaussian_filter(z,8))
        base=op(g);y,x=np.mgrid[:256,:256];m=(x>=64)&(x<192)&(y>=64)&(y<192);transfer=[]
        for lam in (8.,12.,16.,24.):
            vals=[]
            for ang in (0.,np.pi/4,np.pi/2):
                s=np.sin(2*np.pi*(x*np.cos(ang)+y*np.sin(ang))/lam+.73)
                delta=(op(g+.05*s)-base)/.05
                vals.append(float(np.sum(s[m]*delta[m])/np.sum(s[m]**2)))
            transfer.append(dict(wavelength=lam,min=min(vals),max=max(vals),passes=bool(min(vals)>=.9 and max(vals)<=1.1)))
        rows.append(dict(region=label,top_left=[x0,y0],amplitude_DN=.05,transfer=transfer))
    # Tangential operator has explicitly anisotropic response: m=0 must be zero.
    rr=430.;na=4096;th=np.arange(na)*2*np.pi/na;f=np.fft.rfftfreq(na)*na/(2*np.pi*rr)
    fil=(1-np.exp(-(f*40)**8))*np.exp(-(f*10.)**8)
    tang=[]
    for lam in (16.,20.,24.):
        k=int(round(2*np.pi*rr/lam));s=np.sin(k*th+.73);o=np.fft.irfft(np.fft.rfft(s)*fil,n=na)
        v=float(s@o/(s@s));tang.append(dict(wavelength=2*np.pi*rr/k,transfer=v,passes=.9<=v<=1.1))
    # Same faint signal in both real backgrounds: the B correction must retain it.
    gb=np.load(CAU44/'surface_sonyB_rgb.npy')[560:816,560:816,1].astype(float)
    gc=full[560:816,560:816].astype(float);beta=np.load(CAU44/'sonyB_beta.npy')[560:816,560:816]
    y,x=np.mgrid[:256,:256];m=(x>=64)&(x<192)&(y>=64)&(y<192)
    def bop(z,lo):
        ln=np.log(np.maximum(z,1e-3));return local_detail(ln,lam_low=lo)*np.exp(gaussian_filter(ln,8))
    c0=bop(gc,5.5);cn=bop(gc,10.);bn=bop(gb,10.);mix0=c0+beta*(bn-cn);btest=[]
    for lam in (16.,24.):
        for ang in (0.,np.pi/4,np.pi/2):
            si=np.sin(2*np.pi*(x*np.cos(ang)+y*np.sin(ang))/lam+.73)
            mix=bop(gc+.05*si,5.5)+beta*(bop(gb+.05*si,10.)-bop(gc+.05*si,10.))
            dd=(mix-mix0)/.05;val=float(np.sum(si[m]*dd[m])/np.sum(si[m]**2))
            btest.append(dict(wavelength=lam,angle=float(ang),transfer=val,passes=.9<=val<=1.1))
    return dict(real_background_injection=rows,tangential=tang,SonyB_common_signal_injection=btest,radial_m0_transfer=float(fil[0]),scope='tests detail derivation after calibrated single-remap stack; not a measurement of optical resolution')

def main():
    prepare();rep={'polar_lambda16_24_exact_cyan':qa_polar(),'weak_signal':weak_probe(),'display_join':json.loads((REB44/'F5_render.json').read_text())['join']}
    savejson(REB44/'F6_QA.json',rep)
    for key,rows in rep['polar_lambda16_24_exact_cyan'].items():print(key,{k:(round(v['r'],4),round(v['max_abs_null'],4),v['passes']) for k,v in rows.items()},flush=True)
    print('WEAK',json.dumps(rep['weak_signal']),flush=True)

if __name__=='__main__':main()
