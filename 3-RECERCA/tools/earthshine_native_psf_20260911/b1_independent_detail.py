"""Interpolation ablation: disjoint temporal sums and external Sony/LROC checks.
Painted marks only select report regions. No mark or external source enters
the reconstruction. Angular bands suppress a constant bright circular rim.
Exploratory rotation controls are not calibrated discovery probabilities.
"""
from native_common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
CAU45=ROOT/'research/tools/v45_earthshine_20260910/cau'
raw={}
for version in ['old','new']:
    for group in ['all','early','late']:
        z=np.load(OUT/f'B0_{version}_{group}.npz');raw[version+'_'+group]=z['candidate'] if group=='all' else z['all']
raw['S']=np.load(SRC/'B2_sony_reference.npz')['reference']
raw['SA8']=np.load(CAU45/'epoch_sony_A_1.npz')['g'];raw['SB8']=np.load(CAU45/'epoch_sony_B_2.npz')['g']
lr=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];L=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw['L']=L
rr=np.arange(300.,454.,.5);nt=2880;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
valid={k:np.isfinite(v)&(v>0) for k,v in raw.items()};pv={k:map_coordinates(v.astype(float),co,order=1,mode='constant',cval=0)>.999 for k,v in valid.items()}
marks=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];labels,n=label(marks);regions={}
for j in range(1,n+1):
    if np.sum(labels==j)>=100:regions[f'green_{j}']=map_coordinates((labels==j).astype(float),co,order=1,mode='constant',cval=0)>.999
for sector in range(12):
    for lo,hi in [(420,435),(435,449),(449,454)]:regions[f'r{lo}_{hi}_s{sector}']=(rr[:,None]>=lo)&(rr[:,None]<hi)&(np.arange(nt)[None,:]//240==sector)
def corr(a,b,w):
    a=a[w];b=b[w];a=a-a.mean();b=b-b.mean();return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
def compare(a,b,w,rotations=True):
    r=corr(a,b,w);z=dict(r=r)
    if rotations:
        null=[corr(a,np.roll(b,240*j,axis=1),w) for j in range(1,12)];mx=max(map(abs,null));z.update(null_max_abs=mx,pass_null=r>mx)
    return z
yy,xx=np.mgrid[:N,:N];radius=np.hypot(xx-CX,yy-CY);xx=(xx-CX)/500;yy=(yy-CY)/500
results={}
for mode in ['linear','log']:
    pol={}
    for k,g in raw.items():
        v=valid[k];ix=distance_transform_edt(~v,return_distances=False,return_indices=True);g=g[tuple(ix)]
        if mode=='log':g=np.log(g)
        w=v&(radius<435);A=np.stack([np.ones(w.sum()),xx[w],yy[w]],1);f=np.linalg.lstsq(A,g[w],rcond=None)[0];pol[k]=map_coordinates(g-f[0]-f[1]*xx-f[2]*yy,co,order=3,mode='nearest')
    results[mode]={}
    for lo,hi in [(2,4),(4,8),(8,16),(16,24),(24,40),(40,64)]:
        keep=(freq>=1/hi)&(freq<=1/lo);band={k:np.fft.irfft(np.fft.rfft(v,axis=1)*keep,n=nt,axis=1) for k,v in pol.items()};rows=[]
        for name,region in regions.items():
            base=region&pv['old_all']&pv['new_all']&pv['old_early']&pv['new_early']&pv['old_late']&pv['new_late']
            if base.sum()<100:continue
            temporal={version:compare(band[version+'_early'],band[version+'_late'],base) for version in ['old','new']}
            delta=compare(band['new_early']-band['old_early'],band['new_late']-band['old_late'],base)
            row=dict(region=name,n=int(base.sum()),temporal=temporal,delta_temporal=delta,external={})
            for ref in ['S','SA8','SB8']:
                w=base&pv[ref]&pv['L']
                if w.sum()<100:continue
                pairs={k:compare(band[k],band[ref],w) for k in ['old_all','new_all']};pairs['L_ref']=compare(band['L'],band[ref],w)
                for k in ['old_all','new_all']:pairs[k+'_L']=compare(band[k],band['L'],w)
                row['external'][ref]=dict(n=int(w.sum()),pairs=pairs,triple={v:all(pairs[k]['pass_null'] for k in [v+'_all',v+'_all_L','L_ref']) for v in ['old','new']})
            rows.append(row)
        results[mode][f'{lo}_{hi}']=rows
        print(mode,lo,hi,'temporal',*[sum(r['temporal'][v]['pass_null'] for r in rows) for v in ['old','new']],'delta',sum(r['delta_temporal']['pass_null'] for r in rows),'external',*[sum(e['triple'][v] for r in rows for e in r['external'].values()) for v in ['old','new']],flush=True)
save('B1_independent_detail.json',dict(method=__doc__,results=results,limits=['Temporal captures disjoint; calibration and geometry previously global','Temporal comparisons use plain weighted sums, not the shared temporal preference','Candidate full67 uses frozen V48 preference and gradient compositor','2-8px cross-Sony results are descriptive because Sony resolution differs','Rotations exploratory; no universal all-limb recovery PASS']))
