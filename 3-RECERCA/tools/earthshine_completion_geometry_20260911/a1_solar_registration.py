"""Register observed outer corona against a target-excluded short reference.
The Moon and the problematic435-449px annulus never select these parameters.
"""
from geometry_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import least_squares
import time
reference=np.load(OUT/'A0_solar_reference.npz');image=reference['smoothed'];gy,gx=np.gradient(image);frames={r['stem']:r for r in json.loads((OUT/'A0_solar_reference.json').read_text())['frames']};yy,xx=np.mgrid[:N,:N].astype(float);radius=np.hypot(xx-CX,yy-CY);angle=np.arctan2(yy-CY,xx-CX)%(2*np.pi);aperture=(radius>=470)&(radius<650)&((xx.astype(int)%2)==0)&((yy.astype(int)%2)==0);rows=[]
def sample(field,x,y):return map_coordinates(field,[y,x],order=1,mode='constant',cval=0,prefilter=False)
for stem in CAL+TEST+LONG:
    start=time.time();z=np.load(SRC/f'A0_quincunx_{stem}.npz');valid=np.isfinite(z['g'])&(z['q']>0)&np.isfinite(z['variance']);mass=gaussian_filter(valid.astype(float),2,truncate=5);smoothed=gaussian_filter(np.where(valid,z['g'],0).astype(float),2,truncate=5)/np.maximum(mass,1e-30);variance=gaussian_filter(np.where(valid,z['variance'],0).astype(float),4)/np.maximum(gaussian_filter(valid.astype(float),4),1e-30);center=frames[stem]['solar_center'];sx=xx-center[0]+CX;sy=yy-center[1]+CY;support=sample(reference['mass'],sx,sy);good=aperture&(mass>=.999)&(support>=.999);x=sx[good];y=sy[good];values=smoothed[good];noise=np.sqrt(np.maximum(variance[good]*14.826313721285086,1));ph=angle[good];fits=[]
    for part in ['all',0,1]:
        use=np.ones(len(x),bool) if part=='all' else (np.floor(ph/(np.pi/6)).astype(int)%2)==part;X=x[use];Y=y[use];target=values[use];sigma=noise[use]
        if len(X)<1000:
            fits.append(dict(part=part,parameters=None,success=False,samples=int(len(X)),reason='INSUFFICIENT_UNCENSORED_OUTER_CORONA'));continue
        def fun(p):return (p[2]*sample(image,X-p[0],Y-p[1])+p[3]-target)/sigma
        def jac(p):return np.stack([-p[2]*sample(gx,X-p[0],Y-p[1]),-p[2]*sample(gy,X-p[0],Y-p[1]),sample(image,X-p[0],Y-p[1]),np.ones(len(X))],1)/sigma[:,None]
        opt=least_squares(fun,[0,0,1,0],jac=jac,bounds=([-4,-4,.5,-5000],[4,4,1.5,5000]),x_scale=[1,1,.03,200],loss='soft_l1',f_scale=3,max_nfev=100,ftol=1e-10,xtol=1e-9,gtol=1e-8);fits.append(dict(part=part,parameters=opt.x.tolist(),success=bool(opt.success),samples=int(use.sum()),relative_rms=float(np.sqrt(np.mean((fun(opt.x)*sigma)**2))/np.median(abs(target))),nfev=int(opt.nfev)))
    solved=all(r['success'] for r in fits);gap=float(np.linalg.norm(np.array(fits[1]['parameters'][:2])-fits[2]['parameters'][:2])) if solved else None;row=dict(stem=stem,heldout=stem in TEST,long_target=stem in LONG,fits=fits,angular_half_gap=gap,eligible=bool(solved and gap<=.30 and max(abs(np.array(fits[0]['parameters'][:2])))<3.95),seconds=time.time()-start);rows.append(row);save('A1_solar_registration.json',dict(method=__doc__,frames=rows));print(stem,fits[0]['parameters'],'gap',gap,'eligible',row['eligible'],flush=True)
print('DONE',len(rows),flush=True)
