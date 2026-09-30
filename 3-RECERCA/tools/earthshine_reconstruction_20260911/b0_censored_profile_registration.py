"""Fit observed UNSATURATED profile wings, never a maximum at a validity edge.

Diagnostic only: test whether relative lunar geometry explains the HDR seam.
Reference samples are interpolated before censoring. Per-angle gain and offset
are nuisance variables, not photographic corrections. Alternating 15-degree
sectors and a imposed-shift/censoring control test identifiability.
"""
from pathlib import Path
import json,numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/earthshine_reconstruction_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_RECONSTRUCTION_20260911'
z=np.load(ROOT/'output/earthshine_compatibility_20260911/C0_native_profiles.npz')
di=z['distance'];theta=z['theta'];cols=np.arange(0,len(theta),8)
th=np.deg2rad(theta[cols]);rr=di[(di>=-20)&(di<=3)][::2]
rows=np.rint((rr-di[0])/.25).astype(int)
ref=z['g2976'].astype(np.float64);refvalid=z['valid2976']
D=np.stack([np.cos(th),np.sin(th),np.ones(len(th))],axis=1)

def solve(g,valid,selection,dim=2):
    obs=g[np.ix_(rows,cols)].astype(float)
    # Fixed observed validity; unknown shifts do not change eligible pixels.
    w=valid[np.ix_(rows,cols)] & (rr[:,None]<=1)
    # Keep complete reference interpolation support across the allowed search.
    for delta in [-3,0,3]:
        safe=map_coordinates(refvalid.astype(float),[(rr[:,None]+delta-di[0])/.25+np.zeros_like(th),np.zeros_like(rr[:,None])+cols],order=1,mode='constant',cval=0)>.999
        w &=safe
    good=(w.sum(axis=0)>=20)&selection
    w=w[:,good];obs=obs[:,good];basis=D[good,:dim];c=cols[good]
    if len(c)<25:return None
    scale=np.sqrt(np.maximum(np.sum(w*(obs-np.sum(w*obs,0)/w.sum(0))**2,0)/w.sum(0),1))
    def residual(p,details=False):
        shift=basis@p
        pred=map_coordinates(ref,[(rr[:,None]-shift-di[0])/.25+np.zeros(len(c)),np.zeros_like(rr[:,None])+c],order=3,mode='nearest')
        n=w.sum(0);pm=np.sum(w*pred,0)/n;om=np.sum(w*obs,0)/n
        pc=pred-pm;oc=obs-om
        gain=np.sum(w*pc*oc,0)/np.maximum(np.sum(w*pc*pc,0),1e-30)
        off=om-gain*pm;err=(obs-pred*gain-off)/scale
        return (err,w,gain,off,c) if details else err[w]
    f=least_squares(residual,np.zeros(dim),bounds=(-3,3),loss='soft_l1',f_scale=.1,diff_step=.01,max_nfev=70)
    e,w,a,b,c=residual(f.x,True)
    e0=residual(np.zeros(dim));sv=np.linalg.svd(f.jac,compute_uv=False)
    return dict(parameters=f.x.tolist(),angle_count=len(c),rms=float(np.sqrt(np.mean(e[w]**2))),zero_rms=float(np.sqrt(np.mean(e0**2))),gain_q=np.percentile(a,[5,50,95]).tolist(),condition=float(sv[0]/sv[-1]),at_bound=bool(np.max(abs(f.x))>2.95))

def one(g,v):
    ans={}
    for dim in [2,3]:
        fits=[solve(g,v,np.ones(len(th),bool),dim)]+[solve(g,v,((theta[cols]//15).astype(int)%2)==j,dim) for j in [0,1]]
        gap=None
        if all(fits):
            delta=np.array(fits[1]['parameters'])-fits[2]['parameters'];gap=float(np.max(abs(D[:,:dim]@delta)))
        ans[str(dim)]=dict(fits=fits,half_gap=gap,consistent=bool(all(fits) and gap<=.5 and all(np.isfinite(f['condition']) and f['condition']<1e4 for f in fits) and not any(f['at_bound'] for f in fits)))
    return ans

if __name__=='__main__':
    out={}
    for n in [2977,2978,2979,2988,2990,2994]:
        out[str(n)]=one(z[f'g{n}'],z[f'valid{n}']);print(n,json.dumps(out[str(n)]),flush=True)
    imposed=np.array([.6,-.7,.2])
    full=np.stack([np.cos(np.deg2rad(theta)),np.sin(np.deg2rad(theta)),np.ones(len(theta))],1)@imposed
    synthetic=map_coordinates(ref,[(di[:,None]-full-di[0])/.25+np.zeros(len(theta)),np.zeros_like(di[:,None])+np.arange(len(theta))],order=3,mode='nearest')
    control=one(synthetic,z['valid2978']);print('CONTROL',json.dumps(control),flush=True)
    (OUT/'B0_profile_registration.json').write_text(json.dumps(dict(method=__doc__,frames=out,control=dict(imposed=imposed.tolist(),result=control),status='DIAGNOSTIC; no geometry or source changed'),indent=2))
