"""Independent observed lunar-edge check after solar registration; no masks edited."""
from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter1d,minimum_filter1d
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
z=np.load(OUT/'C0_native_profiles.npz');th=z['theta'];rad=z['distance'];angle=th*np.pi/180
shifts=json.loads((OUT/'B1_relative_geometry.json').read_text())['source_shifts']
A=np.column_stack([np.ones(len(th)),np.cos(angle),np.sin(angle)])
def fit(edge,good):
    mask=good.copy()
    if mask.sum()<120:return None
    for _ in range(5):
        cf=np.linalg.lstsq(A[mask],edge[mask],rcond=None)[0];err=edge-A@cf
        scale=max(float(np.median(abs(err[mask]-np.median(err[mask])))/.67448975),.2)
        mask=good&(abs(err)<3*scale)
    return dict(radius_offset=float(cf[0]),dx=float(cf[1]),dy=float(cf[2]),n=int(mask.sum()),angular_fraction=float(mask.mean()),robust_scatter=float(scale))
rows=[];arrays={}
for n in sorted(map(int,shifts)):
    valid=z[f'valid{n}'];g=z[f'g{n}'];raw=z[f'native{n}']
    gg=gaussian_filter1d(g,2,axis=1,mode='wrap');der=gaussian_filter1d(gg,3,axis=0,order=1)
    safe=minimum_filter1d(minimum_filter1d(valid.astype(np.uint8),25,axis=0,mode='constant'),13,axis=1,mode='wrap').astype(bool)
    ids=np.where((rad>=-8)&(rad<=8))[0]
    # Locate the actual derivative maximum first, then test its support.
    # Maximising only within the valid domain mistakes its censoring boundary
    # for an optical edge and can pass angular-half checks on a false circle.
    j=ids[np.argmax(der[ids],axis=0)];cols=np.arange(len(th))
    aa,bb,cc=der[j-1,cols],der[j,cols],der[j+1,cols]
    sub=np.clip(.5*(aa-cc)/np.minimum(aa-2*bb+cc,-1e-30),-.5,.5)
    edge=rad[j]+.25*sub
    noise=np.std(np.diff(gg[(rad>=-40)&(rad<=-25)],axis=0),axis=0)
    good=safe[j,cols]&(j>ids[0])&(j<ids[-1])&(bb>3*noise)
    f=fit(edge,good);halves=[fit(edge,good&((th//15).astype(int)%2==i)) for i in [0,1]]
    gap=None
    if all(halves):gap=float(abs(halves[0]['radius_offset']-halves[1]['radius_offset'])+np.hypot(halves[0]['dx']-halves[1]['dx'],halves[0]['dy']-halves[1]['dy']))
    field=z[f'field{n}'];row=dict(frame=n,fit=f,halves=halves,max_limb_half_gap=gap,pass_geometry=bool(f and f['angular_fraction']>.6 and gap is not None and gap<=.5),field_range=[float(field.min()),float(field.max())])
    rows.append(row);arrays[f'edge{n}']=np.where(good,edge,np.nan)
    print(n,'f',f,'gap',gap,'PASS',row['pass_geometry'],flush=True)
(OUT/'C1_lunar_geometry.json').write_text(json.dumps(dict(method='Observed native G edge, derivative sigma0.75px, angular sigma0.5deg; all contributing neighbourhoods unsaturated. Independent 15-degree sector halves.',rows=rows,limits='Optical edge response includes seeing and PSF; this diagnostic does not identify terrain below native resolution and edits no mask.'),indent=2))
np.savez_compressed(OUT/'C1_observed_edges.npz',theta=th,**arrays)
