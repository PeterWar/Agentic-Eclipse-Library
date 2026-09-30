"""V48 versus candidate photographic retention on the frozen nine green marks.
Coarse photographic source already includes Sony: this is retention, not an
independent new-sensor discovery claim. Independent source ablation is B1.
Use the historical 1440-angle grid, four bands and upper-mark radial restriction.
"""
from native_common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
CAU45=ROOT/'research/tools/v45_earthshine_20260910/cau'
raw={'old':np.load(SRC/'C3_candidate_rgb.npy').mean(-1),'new':np.load(OUT/'C3_candidate_rgb.npy').mean(-1)}
for k,fn,field in [('S','sony_reference.npy',None),('SA8','epoch_sony_A_1.npz','g'),('SB8','epoch_sony_B_2.npz','g')]:
    a=np.load(CAU45/fn);raw[k]=a.astype(float) if field is None else a[field].astype(float)
lr=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];L=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw['L']=L
rr=np.arange(300.,454.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
valid={k:np.isfinite(a)&(a>0) for k,a in raw.items()};common=np.logical_and.reduce([map_coordinates(v.astype(float),co,order=1,mode='constant',cval=0)>.999 for v in valid.values()])
labels,n=label(np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green']);upper=int(labels[313,630]);regions={}
for j in range(1,n+1):
    if (labels==j).sum()<100:continue
    w=common&(map_coordinates((labels==j).astype(float),co,order=1,mode='constant',cval=0)>.999)
    if j==upper:w&=(rr[:,None]>=370)&(rr[:,None]<435)
    if w.sum()>=50:regions[str(j)]=w
def corr(a,b,w):
    a=a[w];b=b[w];a=a-a.mean();b=b-b.mean();return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
def compare(a,b,w):
    r=corr(a,b,w);mx=max(abs(corr(a,np.roll(b,120*j,axis=1),w)) for j in range(1,12));return dict(r=r,null_max_abs=mx,pass_null=r>mx)
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);x=(xx-CX)/500;y=(yy-CY)/500;results={};loss=[];gain=[]
for mode in ['linear','log']:
    pol={}
    for k,g in raw.items():
        v=valid[k];ix=distance_transform_edt(~v,return_distances=False,return_indices=True);g=g[tuple(ix)]
        if mode=='log':g=np.log(g)
        w=v&(r<435);A=np.stack([np.ones(w.sum()),x[w],y[w]],1);p=np.linalg.lstsq(A,g[w],rcond=None)[0];pol[k]=map_coordinates(g-p[0]-p[1]*x-p[2]*y,co,order=3,mode='nearest')
    results[mode]={}
    for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
        h=(freq>=1/hi)&(freq<=1/lo);band={k:np.fft.irfft(np.fft.rfft(a,axis=1)*h,n=nt,axis=1) for k,a in pol.items()};rows=[]
        for name,w in regions.items():
            for ref in ['S','SA8','SB8']:
                pairs={v+'_'+key:compare(band[v],band[key],w) for v in ['old','new'] for key in [ref,'L']};pairs[ref+'_L']=compare(band[ref],band['L'],w)
                triple={v:all(pairs[k]['pass_null'] for k in [v+'_'+ref,v+'_L',ref+'_L']) for v in ['old','new']};row=dict(mark=name,reference=ref,n=int(w.sum()),pairs=pairs,triple=triple);rows.append(row)
                if triple['old'] and not triple['new']:loss.append(dict(mode=mode,band=[lo,hi],mark=name,reference=ref))
                if triple['new'] and not triple['old']:gain.append(dict(mode=mode,band=[lo,hi],mark=name,reference=ref))
        results[mode][f'{lo}_{hi}']=rows
save('C5_retention.json',dict(method=__doc__,upper_mark=upper,results=results,loss=loss,gain=gain,no_lost_old_triples=not loss,limits=['Same-image photographic retention, not all-limb recovery','Rotational null exploratory and region comparisons correlated']))
print('LOSS',json.dumps(loss),'GAIN',json.dumps(gain),flush=True)
