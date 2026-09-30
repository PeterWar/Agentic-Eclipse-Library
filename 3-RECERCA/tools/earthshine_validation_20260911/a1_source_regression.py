"""Localise existing regressions to temporal selection versus the six new renders.
No parameter fitting or candidate changes. Same diagnostic bands and marks.
"""
from validation_common import *
from scipy.ndimage import label,map_coordinates,distance_transform_edt
oldmeta=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text());keys=oldmeta['groups']['vixen']['keys']
pref=np.load(CAU45/'vixen_epoch_ref_weights.npy');weights=np.stack([np.load(CAU45/f'epoch_{k}.npz')['weight'] for k in keys])
lab,_=label(np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green']);fractions={}
for j in [1,3,6,9]:
    m=lab==j;fractions[j]={kind:{k:float(w[m].sum()/ww[:,m].sum()) for k,w in zip(keys,ww)} for kind,ww in [('reference',pref),('all',weights)]}
raw={'old_reference':np.load(CAU45/'vixen_reference.npy'),'old_all':np.load(CAU45/'vixen_all.npy'),'new_all':np.load(PREV/'C3_vixen67.npz')['base'],'C5':np.load(PREV/'C5_signed_frequency_compositor.npz')['band8_16'],'epoch2_old':np.load(CAU45/'epoch_vixen_2.npz')['g'],'epoch2_new':np.load(PREV/'C1_full_epoch2.npz')['base'],'epoch3':np.load(CAU45/'epoch_vixen_3.npz')['g'],'SA8':np.load(CAU45/'epoch_sony_A_1.npz')['g'],'SB8':np.load(CAU45/'epoch_sony_B_2.npz')['g']}
rr=np.arange(300.,454.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
Y,X=np.mgrid[:N,:N];r=np.hypot(X-CX,Y-CY);x=(X-CX)/500;y=(Y-CY)/500;freq=np.fft.rfftfreq(nt)[None]*nt/(2*np.pi*rr[:,None])
results={};planes={}
def corr(a,b,w):
    a=a[w];b=b[w];a=a-a.mean();b=b-b.mean();return float(np.sum(a*b)/max(np.sqrt(np.sum(a*a)*np.sum(b*b)),1e-30))
for mode in ['linear','log']:
    pol={};valid={}
    for key,a in raw.items():
        vi=np.isfinite(a)&(a>0);valid[key]=map_coordinates(vi.astype(float),co,order=1,mode='constant',cval=0)>.999
        ix=distance_transform_edt(~vi,return_distances=False,return_indices=True);g=a[tuple(ix)].astype(float)
        if mode=='log':g=np.log(g)
        m=vi&(r<435);A=np.stack([np.ones(m.sum()),x[m],y[m]],1);c=np.linalg.lstsq(A,g[m],rcond=None)[0];pol[key]=map_coordinates(g-c[0]-c[1]*x-c[2]*y,co,order=3,mode='nearest')
    results[mode]={}
    for mark,lo,hi in [(6,8,16),(3,24,40),(3,40,64)]:
        b={k:np.fft.irfft(np.fft.rfft(v,axis=1)*((freq>=1/hi)&(freq<=1/lo)),n=nt,axis=1) for k,v in pol.items()}
        # Fixed common support across the compared sources, explicit count.
        w=(map_coordinates((lab==mark).astype(float),co,order=1,mode='constant',cval=0)>.999)&np.logical_and.reduce(list(valid.values()))
        row={}
        for key in raw:
            if key.startswith('S'):continue
            row[key]={s:dict(r=corr(b[key],b[s],w),null_max_abs=max(abs(corr(b[key],np.roll(b[s],nt*j//12,1),w)) for j in range(1,12))) for s in ['SA8','SB8']}
        results[mode][f'mark{mark}_{lo}_{hi}']=dict(support=int(w.sum()),sources=row)
save('A1_source_regression.json',dict(method=__doc__,epoch_weight_fractions=fractions,results=results,limits='Exploratory source attribution; not new held-out validation. Filtering individual epochs with partial angular validity is only diagnostic, never output.'))
print(json.dumps(results),flush=True)
