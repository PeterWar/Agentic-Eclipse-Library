"""Same fixed judge after controlled restoration of V45 lunar texture registration."""
"""Other-telescope judge of candidate source stacks, all substantial green marks.
The upper mark/scales were previously explored. Other components are spatial
checks, not new untouched captures. LROC and Sony supply no candidate pixels.
"""
from pathlib import Path
import sys,json,numpy as np
from scipy.ndimage import map_coordinates,distance_transform_edt,label
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import *
OUT=ROOT/'output/earthshine_detail_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_DETAIL_20260911'
raw={'Pere':np.load(ROOT/'output/earthshine_reconstruction_20260911/A0_live_layer21_rgb.npy').mean(-1),'V47':np.load(ROOT/'output/earthshine_validation_20260911/G3_candidate_rgb.npy').mean(-1),'C0':np.load(ROOT/'output/earthshine_validation_20260911/C0_temporal_ensemble.npz')['candidate']}
for key,fn,field in [('V45','vixen_reference.npy',None),('Vlong','epoch_vixen_3.npz','g'),('Sref','sony_reference.npy',None),('SA8','epoch_sony_A_1.npz','g'),('SB8','epoch_sony_B_2.npz','g')]:
    a=np.load(CAU45/fn);raw[key]=(a if field is None else a[field]).astype(float)
lr=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox']
L=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw['L']=L
mask=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,nlab=label(mask);upper=int(lab[313,630])
rr=np.arange(300.,454.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CYT+rr[:,None]*np.sin(th),CXT+rr[:,None]*np.cos(th)]
valid={k:np.isfinite(a)&(a>0) for k,a in raw.items()};common=np.logical_and.reduce([map_coordinates(v.astype(float),co,order=1,mode='constant',cval=0)>.999 for v in valid.values()])
weights={};marks={}
for j in range(1,nlab+1):
    m=lab==j
    if m.sum()<100:continue
    w=(map_coordinates(m.astype(float),co,order=1,mode='constant',cval=0)>.999)&common
    if j==upper:w&=(rr[:,None]>=370)&(rr[:,None]<435)
    if w.sum()<50:continue
    weights[str(j)]=w;marks[str(j)]=dict(pixels=int(m.sum()),polar_samples=int(w.sum()),upper=bool(j==upper))
Y,X=np.mgrid[:N,:N];r=np.hypot(X-CXT,Y-CYT);x=(X-CXT)/500;y=(Y-CYT)/500
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
def corr(a,b,w):
    aa=a[w];bb=b[w];aa=aa-aa.mean();bb=bb-bb.mean();return float(np.sum(aa*bb)/max(np.sqrt(np.sum(aa*aa)*np.sum(bb*bb)),1e-30))
results={}
for mode in ['linear','log']:
    pol={}
    for key,a in raw.items():
        vi=valid[key];ix=distance_transform_edt(~vi,return_distances=False,return_indices=True);g=a[tuple(ix)]
        if mode=='log':g=np.log(np.maximum(g,1e-30))
        m=vi&(r<435);A=np.stack([np.ones(m.sum()),x[m],y[m]],1);fit=np.linalg.lstsq(A,g[m],rcond=None)[0]
        pol[key]=map_coordinates(g-fit[0]-fit[1]*x-fit[2]*y,co,order=3,mode='nearest')
    results[mode]={}
    for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
        keep=(freq>=1/hi)&(freq<=1/lo);b={k:np.fft.irfft(np.fft.rfft(p,axis=1)*keep,n=nt,axis=1) for k,p in pol.items()};regions={}
        for mark,w in weights.items():
            pairs={}
            for a,c in [(a,c) for a in ['Pere','V47'] for c in ['Sref','SA8','SB8','L']]+[(s,'L') for s in ['Sref','SA8','SB8']]:
                rho=corr(b[a],b[c],w);null=[corr(b[a],np.roll(b[c],j*4,1),w) for j in range(11,350)];ceiling=float(np.quantile(np.abs(null),.95));p=(1+sum(abs(q)>=rho for q in null))/(1+len(null));pairs[a+'_'+c]=dict(r=rho,null_q95=ceiling,p_rotation=float(p),pass_null=bool(rho>ceiling))
            triples={a+'_'+s:bool(all(pairs[k]['pass_null'] for k in [a+'_'+s,a+'_L',s+'_L'])) for a in ['Pere','V47'] for s in ['Sref','SA8','SB8']}
            regions[mark]=dict(pairs=pairs,triples=triples)
        results[mode][f'{lo}_{hi}']=regions
        print('completed',mode,lo,hi,flush=True)
(OUT/'A1_rotation_controls.json').write_text(json.dumps(dict(method=__doc__,marks=marks,upper_mark=upper,bands=[[8,16],[16,24],[24,40],[40,64]],results=results,limits=['Screened reconstruction changes radiometry; correlations alone do not validate it','Global67frame source mapping is only partly refined','V47 photographic PSB passed; this checks final source layer without mask or solar contamination']),indent=2))

# Intersection-of-three rotation evidence. BH values are descriptive because
# the Moon is not stationary under rotations; they are not calibrated p-values.
rep={'controls':'339 offsets 11..349 degrees; exclude nearby true-signal autocorrelation','scope':'Exploratory rotation null, multiple-testing sensitivity, not an astronomical discovery claim','modes':{}}
for mode,bands in results.items():
 for candidate in ['Pere','V47']:
  tests=[]
  for band,regions in bands.items():
   for mark,reg in regions.items():
    for ref in ['Sref','SA8','SB8']:
     p=max(reg['pairs'][key]['p_rotation'] for key in [candidate+'_'+ref,candidate+'_L',ref+'_L']);tests.append(dict(band=band,mark=mark,ref=ref,p=p))
  order=np.argsort([t['p'] for t in tests]);n=len(tests);q=np.minimum.accumulate((np.array([tests[i]['p'] for i in order])*n/np.arange(1,n+1))[::-1])[::-1]
  for i,v in zip(order,q):tests[i]['q_BH_descriptive']=min(1,float(v))
  rep['modes'][mode+'_'+candidate]=tests
(OUT/'A1_multiple_controls.json').write_text(json.dumps(rep,indent=2))
print('FDR sensitivity written',flush=True)
