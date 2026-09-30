"""Joint photometric translation fit; keep each patch's directional information.

Exploratory eligibility r>=.35 is not an acceptance gate. Accept only through
independent angular halves, imposed shift and exposure-graph cycle closure.
No patches are pasted into a science image. No transform is applied to a PSB.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import *
from scipy.ndimage import gaussian_filter
OUT=ROOT/'output/earthshine_strategies_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_STRATEGIES_20260911'
z0=np.load(OUT/'coronal_patches.npz');meta=json.loads((OUT/'B0_patch_meta.json').read_text());prior=json.loads((OUT/'B1_coronal_graph.json').read_text())
names=[int(m['frame'][4:8]) for m in meta['frames']]
data={n:np.array([gaussian_filter(np.log(np.maximum(a,1e-6)),2)-gaussian_filter(np.log(np.maximum(a,1e-6)),8) for a in z0[str(n)]]) for n in names}
PAD=40;CORE=144;YY,XX=np.mgrid[PAD:PAD+CORE,PAD:PAD+CORE].astype(np.float32)
def fit(A,B,indices):
    if len(indices)<2:return None
    ref=A[indices,PAD:PAD+CORE,PAD:PAD+CORE];mov=B[indices]
    gy=np.array([np.gradient(a,axis=0) for a in mov]);gx=np.array([np.gradient(a,axis=1) for a in mov])
    t=np.zeros(2);start_cost=None;trace=[]
    for it in range(12):
        H=np.zeros((2,2));rhs=np.zeros(2);cost=0;counts=0
        mapx=(XX+t[0]).astype(np.float32);mapy=(YY+t[1]).astype(np.float32)
        for j in range(len(indices)):
            obs=cv2.remap(mov[j],mapx,mapy,cv2.INTER_LINEAR)
            dr=ref[j]-ref[j].mean();do=obs-obs.mean();a=float(np.sum(dr*do)/np.maximum(np.sum(dr*dr),1e-30))
            err=do-a*dr
            sigma=max(float(np.median(abs(err-np.median(err)))/.67448975),1e-6)
            # Robust residual weights, not a painted spatial correction.
            w=np.minimum(1,2.5*sigma/np.maximum(abs(err),1e-12))/(sigma*sigma)
            jx=cv2.remap(gx[j],mapx,mapy,cv2.INTER_LINEAR);jy=cv2.remap(gy[j],mapx,mapy,cv2.INTER_LINEAR)
            # Project out each patch's brightness offset and multiplicative gain.
            for q in [jx,jy]:q-=q.mean();q-=dr*np.sum(q*dr)/np.maximum(np.sum(dr*dr),1e-30)
            H+=np.array([[np.sum(w*jx*jx),np.sum(w*jx*jy)],[np.sum(w*jx*jy),np.sum(w*jy*jy)]])
            rhs+=np.array([np.sum(w*jx*err),np.sum(w*jy*err)]);cost+=float(np.sum(w*err*err));counts+=err.size
        delta=-np.linalg.solve(H,rhs);delta=np.clip(delta,-.5,.5);t+=delta
        if start_cost is None:start_cost=cost/counts
        trace.append(dict(iteration=it,dx=float(t[0]),dy=float(t[1]),step=float(np.linalg.norm(delta))))
        if np.linalg.norm(delta)<.006:break
    return dict(dx=float(t[0]),dy=float(t[1]),n=len(indices),condition=float(np.linalg.cond(H)),iterations=trace,start_cost=start_cost,end_cost=cost/counts)
rows=[]
for p in prior['pairs']:
    a,b=p['reference'],p['moving'];eligible=[x['index'] for x in p['rows'] if not x['boundary'] and x['r']>=.35]
    f=fit(data[a],data[b],eligible)
    halves=[fit(data[a],data[b],[i for i in eligible if (meta['patches'][i]['angle']//30)%2==j]) for j in [0,1]]
    gap=float(np.hypot(halves[0]['dx']-halves[1]['dx'],halves[0]['dy']-halves[1]['dy'])) if all(halves) else None
    # Independent spatial split rather than reusing the fit's covariance as QA.
    ok=bool(f and len(eligible)>=4 and gap is not None and gap<=.5 and abs(f['dx'])<3 and abs(f['dy'])<3)
    row=dict(reference=a,moving=b,eligible=eligible,fit=f,halves=halves,half_gap=gap,pass_halves=ok);rows.append(row)
    print(a,b,'fit',None if not f else [f['dx'],f['dy']],'gap',gap,'PASS',ok,flush=True)
lookup={(r['reference'],r['moving']):r['fit'] for r in rows}
def vec(a,b):
    if (a,b) in lookup and lookup[a,b]:return np.array([lookup[a,b]['dx'],lookup[a,b]['dy']])
    if (b,a) in lookup and lookup[b,a]:return -vec(b,a)
    return None
cycles=[]
for ns in [(2976,2977,2978),(2976,2977,2995,2994),(2977,2978,2996,2995)]:
    vv=[vec(a,b) for a,b in zip(ns,ns[1:]+ns[:1])]
    if all(v is not None for v in vv):cycles.append(dict(nodes=list(ns),error=float(np.linalg.norm(np.sum(vv,axis=0)))))
# Known translation of observed coronal structures, controls image metric only.
pair=next(p for p in rows if p['reference']==2977 and p['moving']==2978)
base=data[2977];moved=np.array([cv2.warpAffine(a,np.array([[1,0,.75],[0,1,-.5]],np.float32),(a.shape[1],a.shape[0]),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT) for a in base])
c=fit(base,moved,pair['eligible']);control=dict(imposed=[.75,-.5],fit=c,error=float(np.hypot(c['dx']-.75,c['dy']+.5)))
result=dict(method='Joint robust photometric translation in unmasked bright coronal patches; 2x2 image-gradient normal matrix retains directional information',rows=rows,cycles=cycles,control=control,
  gates=dict(min_regions=4,max_angular_half_gap=.5,max_cycle_error=.5,max_control_error=.1),
  graph_validated=bool(all(p['pass_halves'] for p in rows) and all(c['error']<=.5 for c in cycles) and control['error']<=.1),
  limits='Exploratory diagnostic; temporal motion/PSF and cross-train lunar consistency still required. No new product or source cache mutation.')
(OUT/'B2_joint_registration.json').write_text(json.dumps(result,indent=2));print('cycles',cycles,'control_error',control['error'],flush=True)
