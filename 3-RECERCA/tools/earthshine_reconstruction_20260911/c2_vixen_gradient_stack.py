"""Vixen-only source compositor; Sony remains completely outside reconstruction.

All67 available Vixen sources contribute where physically valid. Six epoch2
captures use the new single-CFA render; other sources keep archived V45 mapping.
No intensity gradient is formed across an invalid endpoint. Log-domain source
differences are fused before a whole-rectangle screened Poisson reconstruction.
Length8 was selected from the prior pilot;16 is sensitivity, not a new search.
Not a delivered image: geometry, source systematics and other-train tests open.
"""
from pathlib import Path
import sys,json,numpy as np
from scipy.fft import dctn,idctn
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng,ALPHA,component
OUT=ROOT/'output/earthshine_reconstruction_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_RECONSTRUCTION_20260911'
frames=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];frames=[m for m in frames if m['tren']=='vixen']
new=np.load(OUT/'full_epoch2/source_arrays.npz');newnames=json.loads((OUT/'full_epoch2/source_inputs.json').read_text())['order']
n=1400;num=np.zeros((n,n));den=num.copy();gy=np.zeros((n-1,n));wy=gy.copy();gx=np.zeros((n,n-1));wx=gx.copy();rows=[]
for count,m in enumerate(frames):
    if m['stem'] in newnames:g,q,v=[new[m['stem']+'_'+k].astype(float) for k in ['g','q','variance']]
    else:
        z=np.load(m['native']['file']);g,q,v=[z[k].astype(float) for k in ['g','q','variance']]
    valid=np.isfinite(g)&np.isfinite(v)&(q>0)&(v>0)
    nonpositive=int((valid&(g<=0)).sum());assert nonpositive==0,(m['stem'],'Log model cannot silently drop negative faint samples',nonpositive)
    vs,_=ng(v,valid,4);w=np.where(valid,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
    num+=w*np.nan_to_num(g);den+=w;u=np.log(np.maximum(np.nan_to_num(g),1e-9))
    for axis,G,W in [(0,gy,wy),(1,gx,wx)]:
        a=[slice(None)]*2;b=a.copy();a[axis]=slice(None,-1);b[axis]=slice(1,None);a=tuple(a);b=tuple(b)
        ww=np.where(valid[a]&valid[b],2*w[a]*w[b]/np.maximum(w[a]+w[b],1e-30),0)
        G+=ww*(u[b]-u[a]);W+=ww
    rows.append(dict(frame=m['stem'],exp=m['exp'],new_native=bool(m['stem'] in newnames),nonpositive=nonpositive,valid=int(valid.sum()),conditional_variance_multiplier=ALPHA[component(m)]))
    if count%10==0:print(count,m['stem'],flush=True)
assert np.all(den>0) and np.all(wy>0) and np.all(wx>0),'No fill for missing physical coverage'
base=num/den;gy/=wy;gx/=wx;rhs=np.zeros_like(base);rhs[:-1]-=gy;rhs[1:]+=gy;rhs[:,:-1]-=gx;rhs[:,1:]+=gx
lap=(2-2*np.cos(np.pi*np.arange(n)/n))[:,None]+(2-2*np.cos(np.pi*np.arange(n)/n))[None,:]
arr=dict(base=base,source_gradient_y=gy,source_gradient_x=gx,weight=den)
for length in [8,16]:
    a=1/length**2;out=np.exp(idctn(dctn(rhs+a*np.log(base),type=2,norm='ortho')/(lap+a),type=2,norm='ortho'));arr['log'+str(length)]=out
np.savez_compressed(OUT/'C2_vixen67.npz',**arr)
(OUT/'C2_vixen67.json').write_text(json.dumps(dict(method=__doc__,frames=rows,frame_count=len(rows),sony_frames_in_reconstruction=0,canvas_source_rectangle=[1400,1400],origin=[4677,3077],nominal_length=8,sensitivity_length=16,geometry='Provisional residual lunar correction only2977/2978;2976 reference; remaining61 retain V45 mapping. No radius change.',status='EXPLORATORY_SOURCE_CANDIDATE; no PSB and no independent PASS yet'),indent=2))
print('DONE',flush=True)
