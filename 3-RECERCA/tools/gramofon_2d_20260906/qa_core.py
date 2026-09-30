from experiment import *
from operators import kernel, robust_refit

def main():
    ny,nx=151,173;y,x=np.mgrid[:ny,:nx];r=np.hypot(x+210,y-75)
    qr=np.log(r/100);mask=(x+.4*y>24);mask[60:80,80:97]=False
    a=1+.003*x-.004*y+.000013*x*x-.000017*x*y+.000009*y*y
    rows=[]
    rng=np.random.default_rng(89127);z=a+.001*rng.normal(size=a.shape)
    for kind in ['quadratic','lograd']:
        model=LocalModel(mask,24,kind,qr)
        assert np.array_equal(model.valid,mask)
        target=a if kind=='quadratic' else 3-3*qr
        residual=model.apply(target)[0]
        err=float(np.max(np.abs(residual[mask])));assert err<1e-8
        out=model.apply(z)[0]
        sentinels=[]
        for v in [0,np.nan,1e30]:
            zz=z.copy();zz[~mask]=v
            e=float(np.max(np.abs((model.apply(zz)[0]-out)[mask])));assert e==0
            sentinels.append({'sentinel':str(v),'max_change':e})
        rotated=LocalModel(np.rot90(mask),24,kind,np.rot90(qr))
        e=float(np.max(np.abs((rotated.apply(np.rot90(z))[0]-np.rot90(out))[np.rot90(mask)])))
        assert e<1e-8
        rows.append({'method':kind,'identity_error':err,'invalid_sentinels':sentinels,
                     'rotate90_max_error':e,'all_observed_defined':True})
    # Direct weighted least-squares at edge, missing patch, and full interior.
    q=LocalModel(mask,24,'quadratic',qr);bg=q.background(z);w,xx,yy=kernel(24)
    checks=[]
    for px,py in [(25,8),(78,57),(100,100)]:
        dy,dx=np.mgrid[:ny,:nx];ux=(dx-px)/24;uy=(dy-py)/24;dist=np.hypot(ux,uy)
        ww=np.maximum(1-dist,0)**4*(1+4*dist)*mask
        good=ww>0;P=np.stack([np.ones_like(ux),ux,uy,ux*ux,ux*uy,uy*uy],axis=-1)[good]
        beta=np.linalg.lstsq(P*np.sqrt(ww[good,None]),z[good]*np.sqrt(ww[good]),rcond=None)[0]
        err=abs(float(beta[0]-bg[py,px]));assert err<1e-8
        checks.append({'xy':[px,py],'direct_WLS_error':err})
    save('core_validation',{'PASS':True,'rows':rows,'direct_reference':checks,
                           'scope':'implementation algebra and geometry; not general artifact removal'})
    log('core QA COMPLETE')

if __name__=='__main__':main()
