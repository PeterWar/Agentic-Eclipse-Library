"""Earthshine display derivatives, physically measured relief and additive join.
All source radiance arrays and Pere's 09 remain unchanged. No LROC pixels enter.
The fitted edge response represents optics plus Pere's tone, not a physical PSF.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from scipy.optimize import least_squares
from scipy.special import ndtr

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def veil(g):
    rr=np.arange(.5,RL+41,1.);th=np.arange(1440)*2*np.pi/1440
    mx=(CXT+np.cos(th[:,None])*rr).astype(np.float32);my=(CYT+np.sin(th[:,None])*rr).astype(np.float32)
    p=cv2.remap(np.nan_to_num(g),mx,my,cv2.INTER_LINEAR)
    vr=np.interp(R,rr,np.median(p,axis=0))
    x=(XX-CXT)/500;y=(YY-CYT)/500;m=R<.83*RL
    terms=[x**i*y**j for i in range(5) for j in range(5-i)]
    aa=np.stack([t[m] for t in terms],1);cf=np.linalg.lstsq(aa,(g-vr)[m],rcond=None)[0]
    v0=vr+sum(c*t for c,t in zip(cf,terms))
    tab=[]
    for j in range(36):
        ids=(np.arange(j*40-40,j*40+41)%1440)
        t=np.median(p[ids],axis=0);tab.append(np.exp(gaussian_filter1d(np.log(np.maximum(t,1e-3)),1.)))
    tab=np.array(tab,dtype=np.float32);tab=np.r_[tab,tab[:1]]
    vs=cv2.remap(tab,((R-.5)).astype(np.float32),((PHI%(2*np.pi))*36/(2*np.pi)).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    a=smooth(.82*RL,.90*RL,R)
    return ((1-a)*v0+a*vs).astype(np.float32)

def join_response(base,edge):
    nl=len(edge);th=np.arange(nl)*2*np.pi/nl;rr=np.arange(440.,479.,.25)
    mx=(CXT+np.cos(th[:,None])*rr).astype(np.float32);my=(CYT+np.sin(th[:,None])*rr).astype(np.float32)
    lin=comu.a_lineal(base);pol=cv2.remap(lin,mx,my,cv2.INTER_LINEAR)
    ext=(rr>=464)&(rr<=478);X=np.c_[np.ones(ext.sum()),rr[ext]-464]
    co=np.linalg.lstsq(X,np.log(np.maximum(pol[:,ext,:],1e-6)).transpose(1,0,2).reshape(ext.sum(),-1),rcond=None)[0].reshape(2,nl,3)
    co=gaussian_filter1d(co,4.,axis=1,mode='wrap')
    pred=np.exp(co[0,:,None,:]+co[1,:,None,:]*(rr[None,:,None]-464))
    lum=lambda x:(x[...,0]+2*x[...,1]+x[...,2])/4
    q=lum(pol)/np.maximum(lum(pred),1e-8);dist=rr[None,:]-edge[:,None]
    sector=(np.arange(nl)*36//nl);train=sector%2==0;sel=(dist>-5)&(dist<12)&(q<1.2)&(q>=0)
    harmonics=np.c_[np.cos(th),np.sin(th),np.cos(2*th),np.sin(2*th)]
    def model(par):
        phase=harmonics@par[2:]
        return ndtr((dist-phase[:,None])/par[0])**par[1]
    def fit(mask):
        def fun(par):return (model(par)[mask][sel[mask]]-q[mask][sel[mask]])
        return least_squares(fun,[2.1,10.,-.9,.4,-1.7,.9],bounds=([.5,1.,-4.,-4.,-4.,-4.],[5.,30.,4.,4.,4.,4.]),loss='soft_l1',f_scale=.05)
    opt=fit(train);sigma,gamma=opt.x[:2];phase_coeff=opt.x[2:];qm=model(opt.x)
    # Predict the north/south mismatch without training on those sectors.
    pole=(abs(np.cos(th))<np.sin(np.radians(20)))
    pole_fit=fit(~pole);pole_mae=float(np.mean(abs(model(pole_fit.x)[pole][sel[pole]]-q[pole][sel[pole]])))
    errors={k:float(np.mean(abs(qm[s][sel[s]]-q[s][sel[s]]))) for k,s in [('train',train),('held_out',~train)]}
    phi=PHI%(2*np.pi);idx=phi*nl/(2*np.pi)
    rlim=np.interp(idx,np.arange(nl),edge,period=nl)
    # Subpixel quadrature of effective coverage; source radiance isn't blurred.
    coverage=np.zeros_like(R,dtype=float)
    for oy in (-.375,-.125,.125,.375):
        for ox in (-.375,-.125,.125,.375):
            phi_=np.arctan2(YY+oy-CYT,XX+ox-CXT)%(2*np.pi)
            rl_=np.interp(phi_*nl/(2*np.pi),np.arange(nl),edge,period=nl)
            ph=phase_coeff[0]*np.cos(phi_)+phase_coeff[1]*np.sin(phi_)+phase_coeff[2]*np.cos(2*phi_)+phase_coeff[3]*np.sin(2*phi_)
            d=np.hypot(XX+ox-CXT,YY+oy-CYT)-rl_-ph
            coverage+=(1-ndtr(d/sigma)**gamma)/16
    c0=np.stack([np.interp(idx,np.arange(nl),co[0,:,c],period=nl) for c in range(3)],-1)
    c1=np.stack([np.interp(idx,np.arange(nl),co[1,:,c],period=nl) for c in range(3)],-1)
    outer=np.exp(c0+c1*(np.clip(R,440,479)-464)[...,None])
    photo=np.min(np.clip(1-lin/np.maximum(outer,1e-9),0,1),axis=2)
    w=np.minimum(coverage,photo);w[R>470]=0
    protected=(np.max(lin/np.maximum(outer,1e-9),axis=2)>=1)&(R>440)&(R<470)
    rep=dict(sigma_effective_px=float(sigma),tone_exponent=float(gamma),response_phase_cos_sin_cos2_sin2_px=phase_coeff.tolist(),MAE_normalized_response=errors,north_south_held_out_MAE=pole_mae,north_south_held_out_parameters=pole_fit.x.tolist(),geometry='fixed observed Vixen contour; no scale change; angular phase belongs only to09 display response',quadrature='4x4 subpixels for coverage only',protected_pixels=int(protected.sum()),role='auxiliary effective display response, not inferred physical PSF')
    return w,lin,protected,rep

def main():
    prepare();g=np.load(CAU44/'surface_clean_rgb.npy');v=veil(g[...,1]);np.save(CAU44/'veil_clean.npy',v)
    residual=g[...,1]-v;np.save(CAU44/'residual_clean.npy',residual)
    # Broad relief retains the established radial/2D veil approach. Fine relief is restored independently.
    d=np.load(CAU44/'surface_clean_detail_log.npy')
    broad=gaussian_filter(np.nan_to_num(residual),3.)
    fine=d-gaussian_filter(d,3.)
    broad*=1-smooth(.84*RL,.90*RL,R)
    iso=(broad+fine)*(1-smooth(.90*RL,.925*RL,R))
    tang=np.load(CAU44/'surface_clean_detail_tangent.npy')
    wt=smooth(.88*RL,.915*RL,R)*(1-smooth(.955*RL,.965*RL,R))
    b_add=np.load(CAU44/'sonyB_interior_correction_DN.npy')
    relief=iso+wt*tang+b_add
    np.save(CAU44/'relief_display_DN.npy',relief)
    med=np.median(g[R<.8*RL],axis=0);lum=float((med[0]+2*med[1]+med[2])/4);col=med/lum
    # Same declared base tone; level chosen close to Pere's marked file, approximately0.176 sRGB.
    def flat(l):return to_srgb(np.full((8,8,3),l,np.float32)*col,np.ones((8,8),bool))[4,4,1]
    lo,hi=1.,1000.
    for _ in range(40):
        mid=np.sqrt(lo*hi)
        if flat(mid)<.176:lo=mid
        else:hi=mid
    level=np.sqrt(lo*hi);rho=relief/lum
    base=np.load(CAU44/'pere09_rgb.npy').astype(np.float32)/65535
    edge=np.load(CAU44/'vixen_optical_edge.npy');w,lin,protected,jrep=join_response(base,edge)
    np.save(CAU44/'join_coverage.npy',w.astype(np.float32))
    rep={'relief':'broad measured clean residual + isotropic8-24 to0.90R, transition to directional angular16-24 detail at0.915R; directional taper0.955-0.965R','SonyB':'interior16-24 detail only, exposure-validity weights, excluded within140px of ghost, full from180px; fade0.86-0.88R; noB exterior','lunar_level_G_srgb':.176,'level_linear':float(level),'color':col.tolist(),'join':jrep,'variants':{}}
    for title,contrast in [('natural',.12),('relleu24',.24)]:
        def display(k):return to_srgb((level*col)[None,None,:]*np.maximum(1+k*rho,1e-4)[...,None],np.ones_like(R,bool))
        lo,hi=0.,200.
        for _ in range(24):
            mid=(lo+hi)/2;im=display(mid);vals=im[...,1][R<.8*RL];p5,p95=np.percentile(vals,[5,95]);cc=(p95-p5)/np.median(vals)
            if cc<contrast:lo=mid
            else:hi=mid
        k=(lo+hi)/2;disc=display(k);target=np.clip(comu.a_srgb(lin+w[...,None]*comu.a_lineal(disc)),0,1)
        delta=np.maximum(target-base,0);delta[protected]=0;target=np.clip(base+delta,0,1)
        u=np.round(delta*65535).astype(np.uint16);np.save(CAU44/f'earthshine_{title}_delta_u16.npy',u)
        np.save(CAU44/f'earthshine_{title}_disc.npy',disc.astype(np.float32))
        png(f'F5_{title}_compost_1a1.png',target);png(f'F5_{title}_disc_1a1.png',disc*(R<RL)[...,None])
        rep['variants'][title]=dict(K=float(k),contrast_target=contrast,protected_changed=int(np.any(u[protected]!=0,axis=1).sum()),outside_470_nonzero=int(np.any(u[R>470]!=0,axis=1).sum()),pixels_decreased=int((delta<0).sum()))
        if title=='natural':
            np.save(CAU44/'expected_moon_u16.npy',np.clip(np.load(CAU44/'pere09_rgb.npy').astype(np.uint32)+u,0,65535).astype(np.uint16))
            old=np.load(CAU44/'v43_rgb.npy').astype(float)/65535;mask=np.load(CAU44/'v43_mask.npy').astype(float)/65535;before=base*(1-mask[...,None])+old*mask[...,None]
            png('F5_abans_V43_1a1.png',before)
            for name,xy in [('nord',(700,246)),('sud',(700,1154)),('est',(245,700)),('oest',(1154,700))]:
                x,y=xy;sl=np.s_[y-35:y+35,x-70:x+70];row=np.concatenate([before[sl],target[sl]],1);png(f'F5_limbe_{name}_x4.png',cv2.resize(row,None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST))
    hdr=to_srgb(np.nan_to_num(np.load(CAU44/'epoch_clean_rgb.npy')),R<RL+40)
    np.save(CAU44/'earthshine_HDR_u16.npy',np.round(hdr*65535).astype(np.uint16))
    np.save(CAU44/'HDR_mask_u16.npy',np.round((1-smooth(RL+32,RL+40,R))*65535).astype(np.uint16))
    savejson(REB44/'F5_render.json',rep);print(json.dumps(rep,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
