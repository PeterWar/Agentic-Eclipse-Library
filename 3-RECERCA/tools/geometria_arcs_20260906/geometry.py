"""Fixed Cartesian samples; forward radial regression; no product modification."""
from pathlib import Path
import sys, json, time
import numpy as np
from scipy.linalg import solveh_banded
from scipy.optimize import minimize
import cv2
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research/tools/eclipse_determinista'))
from comu import Run
RUN=Run('GEOMETRIA_ARCS','20260906',str(ROOT/'output/geometria_arcs_20260906'))
for p in [RUN.vista(''),RUN.lliurable(''),RUN.rebut('')]:Path(p).mkdir(parents=True,exist_ok=True)
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
LUNAR=np.array([5361.877319859359,3774.7412178166314])
cv2.setNumThreads(2)

def log(s):print(time.strftime('%H:%M:%S'),s,flush=True)
def save(name,j):Path(RUN.rebut(name+'.json')).write_text(json.dumps(j,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')
def gauss(a,s):
    k=2*int(3*s+.5)+1
    return cv2.GaussianBlur(np.asarray(a,np.float32),(k,k),s,borderType=cv2.BORDER_REFLECT_101)

class Samples:
    def __init__(self,center=(CX,CY),radial=(2.5*RS,4.5*RS),step=4,nsectors=12,margin_deg=9):
        self.center=np.array(center,float);self.radial=radial;self.step=step
        self.nsectors=nsectors;self.margin_deg=margin_deg
        extent=int(np.ceil(radial[1]/step))*step
        self.x0=int(np.floor(center[0]))-extent
        self.y0=int(np.floor(center[1]))-extent
        y,x=np.mgrid[self.y0:self.y0+2*extent+1:step,self.x0:self.x0+2*extent+1:step]
        r=np.hypot(x-center[0],y-center[1]);th=np.mod(np.arctan2(y-center[1],x-center[0]),2*np.pi)
        width=2*np.pi/nsectors;phase=np.mod(th,width)
        good=(r>=radial[0])&(r<=radial[1])&(phase>np.deg2rad(margin_deg))&(phase<width-np.deg2rad(margin_deg))
        self.x=x[good];self.y=y[good];self.sector=np.floor(th[good]/width).astype(int)
        self.knots=np.arange(np.floor(radial[0]-300),np.ceil(radial[1]+300)+2,2.)
        self.spacing=2.

    def radius(self,p):
        dx=self.x-(self.center[0]+p[0]);dy=self.y-(self.center[1]+p[1])
        e1,e2=p[2:4] if len(p)>2 else (0.,0.)
        e=np.hypot(e1,e2);c=np.cosh(e);s=np.sinh(e)/e if e>1e-12 else 1.
        return np.sqrt(np.maximum(c*(dx*dx+dy*dy)+s*(e1*(dx*dx-dy*dy)+2*e2*dx*dy),0))

    def basis(self,p):
        u=(self.radius(p)-self.knots[0])/self.spacing
        j=np.floor(u).astype(np.int32);f=u-j
        assert j.min()>=0 and j.max()+1<len(self.knots)
        return j,f

def fit_profile(j,f,z,sel,n):
    j=j[sel];f=f[sel];z=z[sel];a=1-f
    diag=np.bincount(j,weights=a*a,minlength=n)+np.bincount(j+1,weights=f*f,minlength=n)
    off=np.bincount(j,weights=a*f,minlength=n)
    rhs=np.bincount(j,weights=a*z,minlength=n)+np.bincount(j+1,weights=f*z,minlength=n)
    # Only unused knots need a tiny diagonal; no radial smoothing penalty.
    ab=np.zeros((2,n));ab[0]=diag+1e-10;ab[1,:-1]=off[:-1]
    return solveh_banded(ab,rhs,lower=True,check_finite=False)

def prediction(j,f,b):return (1-f)*b[j]+f*b[j+1]
def metrics(z,p):
    error=np.mean((z-p)**2);baseline=np.mean(z*z)
    return {'RMS':float(np.sqrt(error)),'baseline_RMS':float(np.sqrt(baseline)),
        'explained_fraction':float(1-error/baseline),'correlation':float(np.corrcoef(z,p)[0,1]),
        'prediction_RMS':float(np.sqrt(np.mean(p*p)))}

class Fit:
    def __init__(self,samples,z,parity):
        self.s=samples;self.z=np.asarray(z,float);self.train=samples.sector%2==parity
        self.valid=~self.train;self.norm=np.mean(self.z[self.train]**2)
        self.calls=0
    def evaluate(self,p,full=False):
        self.calls+=1;j,f=self.s.basis(p)
        b=fit_profile(j,f,self.z,self.train,len(self.s.knots));pred=prediction(j,f,b)
        loss=np.mean((self.z[self.train]-pred[self.train])**2)/self.norm
        if full:
            return {'parameters':np.asarray(p).tolist(),'center_xy':(self.s.center+np.asarray(p)[:2]).tolist(),
                'offset_from_reference_px':float(np.linalg.norm(p[:2])),
                'axis_ratio':float(np.exp(np.hypot(*p[2:4]))) if len(p)>2 else 1.,
                'major_axis_angle_deg':float((.5*np.degrees(np.arctan2(p[3],p[2]))+90)%180) if len(p)>2 else None,
                'train':metrics(self.z[self.train],pred[self.train]),'heldout':metrics(self.z[self.valid],pred[self.valid]),
                'sector_heldout':[dict(sector=int(k),**metrics(self.z[self.s.sector==k],pred[self.s.sector==k])) for k in np.unique(self.s.sector[self.valid])],
                'profile':b,'knots':self.s.knots,'heldout_prediction':pred[self.valid]}
        return loss
    def optimize(self,ellipse=False,seed=None,quick=False):
        scale=np.array([32.,32.,.02,.02]) if ellipse else np.array([32.,32.])
        bounds=[(-4,4),(-4,4)]+([(-3,3),(-3,3)] if ellipse else [])
        if not ellipse:
            grid=[np.array([x,y],float) for x in range(-128,129,32) for y in range(-128,129,32)]
            scored=sorted([(self.evaluate(p),i) for i,p in enumerate(grid)])
            promising=[grid[i] for _,i in scored[:(2 if quick else 4)]]
            fine=[np.clip(p+[x,y],-128,128) for p in promising for x in [-16,0,16] for y in [-16,0,16]]
            fine_scored=sorted([(self.evaluate(p),i) for i,p in enumerate(fine)])
            starts=[fine[i] for _,i in fine_scored[:(2 if quick else 4)]]
        else:
            seed=np.asarray(seed)[:2]
            # Joint center/shape grid: the best circle can be far from the
            # center of a true ellipse, so it cannot be the only seed.
            grid=[np.array([x,y,e1,e2],float) for x in range(-128,129,32)
                for y in range(-128,129,32) for e1 in [-.04,0,.04] for e2 in [-.04,0,.04]]
            scored=sorted([(self.evaluate(p),i) for i,p in enumerate(grid)])
            # Diversify centers: the highest grid scores can cluster around
            # the same aliased radial phase. The control exposed that failure.
            starts=[];seen=set()
            for _,i in scored:
                key=tuple(grid[i][:2])
                if key not in seen:
                    starts.append(grid[i]);seen.add(key)
                if len(starts)>=(24 if quick else 40):break
            starts += [np.r_[seed,0.,0.]]
        sols=[]
        for p in starts:
            opt=minimize(lambda v:self.evaluate(v*scale),p/scale,method='L-BFGS-B',bounds=bounds,
                options={'maxiter':70,'ftol':1e-10,'gtol':1e-6,'eps':.002})
            sols.append({'parameters':(opt.x*scale).tolist(),'loss':float(opt.fun),'success':bool(opt.success),'nit':int(opt.nit)})
        best=min(sols,key=lambda z:z['loss']);row=self.evaluate(best['parameters'],True)
        row['optimizer_solutions']=sols;row['calls']=self.calls
        row['at_boundary']=any(abs(v)>lim-tol for v,lim,tol in zip(best['parameters'],[128,128,.06,.06],[.05,.05,1e-4,1e-4]))
        return row

def compact(row):return {k:v for k,v in row.items() if k not in ['profile','knots','heldout_prediction']}
