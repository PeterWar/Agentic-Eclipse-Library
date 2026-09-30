"""Expanded exposure graph and held-apart checks for translation/similarity."""
from pathlib import Path
import json,numpy as np,cv2
from scipy.ndimage import gaussian_filter
from registration_core import fit,matrix,limb_gap,local_ncc,RS
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
meta=json.loads((OUT/'B0_patch_meta.json').read_text());z=np.load(OUT/'coronal_patches.npz')
names=[int(m['frame'][4:8]) for m in meta['frames']]
centres=np.array([[p['radius']*RS*np.cos(np.deg2rad(p['angle'])),p['radius']*RS*np.sin(np.deg2rad(p['angle']))] for p in meta['patches']])
data={};valid={};dn={}
for n in names:
    q=np.log(np.maximum(z[str(n)],1e-6)).astype(np.float32)
    data[n]=np.array([gaussian_filter(a,2)-gaussian_filter(a,8) for a in q])
    valid[n]=np.array([a.mean() for a in z[f'{n}_valid']]);dn[n]=np.median(z[f'{n}_rawdn'],axis=(1,2))
pairs=[(2976,2970),(2976,2977),(2977,2978),(2978,2979),(2976,2978),(2994,2995),(2995,2996),(2976,2994),(2977,2995),(2978,2996),
 (2969,2970),(2970,2971),(2971,2972),(2971,2977),(2972,2978),(2974,2975),(2975,2976),(2970,2976),(2979,2980),(2980,2981),(2979,2981),
 (2988,2989),(2989,2990),(2989,2995),(2990,2996),(2993,2994),(2970,2988),(2971,2989),(2972,2990),(2975,2993),(2988,3000),(2989,3001),(2990,3002),(3000,3001),(3001,3002)]
pairs=list(dict.fromkeys(tuple(sorted(p)) for p in pairs));rows=[]
for a,b in pairs:
    idx=[];scores=[]
    for i in range(len(centres)):
        if min(valid[a][i],valid[b][i])<.995 or min(dn[a][i],dn[b][i])<64:continue
        r,boundary=local_ncc(data[a][i],data[b][i]);scores.append(dict(index=i,r=r,boundary=boundary))
        if r>=.35 and not boundary:idx.append(i)
    rec=dict(reference=a,moving=b,eligible=idx,scores=scores)
    for sim in [False,True]:
        key='similarity' if sim else 'translation'
        f=fit(data[a],data[b],idx,centres,sim)
        halves=[fit(data[a],data[b],[i for i in idx if (meta['patches'][i]['angle']//30)%2==j],centres,sim) for j in [0,1]]
        gap=limb_gap(*halves);ok=bool(f and len(idx)>=4 and gap is not None and gap<=.5 and max(abs(v) for v in f['parameters'])<3)
        rec[key]=dict(fit=f,halves=halves,max_limb_half_gap=gap,pass_halves=ok)
    rows.append(rec);print(a,b,'n',len(idx),'gap2/4',[rec[k]['max_limb_half_gap'] for k in ['translation','similarity']],flush=True)
    (OUT/'B0_geometry.partial.json').write_text(json.dumps(rows,indent=2))
# Known observation-derived shifts test the estimator, not true physical geometry.
base=data[2977];control=[];idx=next(r['eligible'] for r in rows if (r['reference'],r['moving'])==(2977,2978))
yy,xx=np.mgrid[:224,:224].astype(np.float32)
for sim in [False,True]:
    t=np.array([.75,-.5,.12,-.09] if sim else [.75,-.5]);moved=[]
    # Warp by the inverse of the imposed forward relation about the solar centre.
    F=matrix({'parameters':t});inv=np.linalg.inv(F)
    for k,a in enumerate(base):
        px=xx-112+centres[k][0];py=yy-112+centres[k][1]
        mx=(inv[0,0]*px+inv[0,1]*py+inv[0,2]-centres[k][0]+112).astype(np.float32)
        my=(inv[1,0]*px+inv[1,1]*py+inv[1,2]-centres[k][1]+112).astype(np.float32)
        moved.append(cv2.remap(a,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT))
    f=fit(base,np.array(moved),idx,centres,sim);control.append(dict(similarity=sim,imposed=t.tolist(),fit=f,max_limb_error=limb_gap(f,{'parameters':t})))
    print('CONTROL',control[-1],flush=True)
result=dict(pairs=rows,controls=control,gates=dict(half_gap_max_limb=.5,known_transform_error_max=.1,min_regions=4),scope='Relative solar geometry only; angular splits, no cross-train lunar validation or new product')
(OUT/'B0_geometry.json').write_text(json.dumps(result,indent=2))
