from pathlib import Path
import numpy as np,json,cv2
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
cx,cy=5361.768111973117,3775.747534140857
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
source=np.load(P/'arrays/V57_L00_C0.npy').astype(float)/65535;source=cv2.warpAffine(source,M,(2000,2000),flags=cv2.INTER_CUBIC)
target=np.load(A/'L83_C0.npy').astype(float)/65535
def detail(a):return gaussian_filter(a,0.7)-gaussian_filter(a,3)
s=detail(source);b=detail(target)
yy,xx=np.mgrid[0:2000:2,0:2000:2];x=xx+4377;y=yy+2777;r=np.hypot(x-5376.568111973117,y-3776.647534140857);theta=np.arctan2(y-3776.647534140857,x-5376.568111973117)%(2*np.pi)
sel=(r>420)&(r<650)&(source[yy,xx]>.003);x=x[sel].astype(float);y=y[sel].astype(float);v=s[yy[sel],xx[sel]];sector=np.floor(theta[sel]*12/(2*np.pi)).astype(int);fit=(sector%2==0)
def matrix(q):
    dx,dy,deg,scale=q;t=np.deg2rad(deg);rot=scale*np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]]);return np.c_[rot,np.array([cx,cy])+[dx,dy]-rot@np.array([cx,cy])]
def score(q,field=b,sel=fit):
    t=matrix(q);xx=t[0,0]*x[sel]+t[0,1]*y[sel]+t[0,2];yy=t[1,0]*x[sel]+t[1,1]*y[sel]+t[1,2];w=map_coordinates(field,[yy-2777,xx-4377],order=1);return float(np.corrcoef(v[sel],w)[0,1])
def solve(field):
    starts=[(score([dx,dy,th,1],field),[dx,dy,th,1]) for dx in [-2,0,2] for dy in [-2,0,2] for th in [-.5,0,.5]]
    ans=[]
    for _,q in sorted(starts,reverse=True)[:3]:
        ans.append(minimize(lambda q:-score(q,field),q,method='Nelder-Mead',bounds=[(-6,6),(-6,6),(-1,1),(.99,1.01)],options={'maxiter':1600,'xatol':1e-6}))
    return min(ans,key=lambda z:z.fun)
opt=solve(b);q=opt.x;rows=[]
for k in range(12):
    sel=sector==k
    if sel.sum()<40:continue
    rows.append(dict(sector=k,reserved=bool(k%2),points=int(sel.sum()),before=score([0,0,0,1],sel=sel),after=score(q,sel=sel)))
rep=dict(source='Original photo 12 with existing V61 common transform',target='Pere extra layer83, source pixels unmasked',sampling_transform_source_to_extra=q.tolist(),matrix_global=matrix(q).tolist(),fit_ncc=score(q),reserved_ncc=score(q,sel=~fit),before=score([0,0,0,1]),rows=rows,status='diagnostic; no transformation applied')
(O/'C1_extra12_registration.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
