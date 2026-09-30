"""Before/after CFA ablation, identical footprint within each independent Sony
reference. Do not restrict a comparison to unrelated references' coverage.
Photographic marks and final435..449 fringe are reported separately. Same frozen
bands and 11 rotated controls as historical judge, not a new parameter search.
"""
from detail_common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
z=np.load(OUT/'B1_full_native_ensemble.npz');raw={'old':np.load(PREV/'C0_temporal_ensemble.npz')['candidate'],'new':z['candidate'],'base':z['base'],'Snew':np.load(OUT/'B2_sony_reference.npz')['reference'],'Sold':np.load(CAU45/'sony_reference.npy'),'SA8':np.load(CAU45/'epoch_sony_A_1.npz')['g'],'SB8':np.load(CAU45/'epoch_sony_B_2.npz')['g']}
lr=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];L=np.zeros((N,N));oy,ox=bb[1]-3077,bb[0]-4677;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw['L']=L
rr=np.arange(300.,454.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None]);valid={k:np.isfinite(a)&(a>0) for k,a in raw.items()};pv={k:map_coordinates(v.astype(float),co,order=1,mode='constant',cval=0)>.999 for k,v in valid.items()}
mask=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,nlab=label(mask);regions={}
for i in range(1,nlab+1):
 if (lab==i).sum()<100:continue
 regions['green_'+str(i)]=map_coordinates((lab==i).astype(float),co,order=1,mode='constant',cval=0)>.999
for sector in range(12):regions['last_'+str(sector)]=(rr[:,None]>=435)&(rr[:,None]<449)&(np.arange(nt)[None,:]//120==sector)
def corr(a,b,w):
 a=a[w];b=b[w];a-=a.mean();b-=b.mean();return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);xx=(x-CX)/500;yy=(y-CY)/500;results={}
for mode in ['linear','log']:
 pol={}
 for k,a in raw.items():
  ix=distance_transform_edt(~valid[k],return_distances=False,return_indices=True);g=a[tuple(ix)]
  if mode=='log':g=np.log(g)
  m=valid[k]&(r<435);A=np.stack([np.ones(m.sum()),xx[m],yy[m]],1);f=np.linalg.lstsq(A,g[m],rcond=None)[0];pol[k]=map_coordinates(g-f[0]-f[1]*xx-f[2]*yy,co,order=3,mode='nearest')
 results[mode]={}
 for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
  h=(freq>=1/hi)&(freq<=1/lo);band={k:np.fft.irfft(np.fft.rfft(p,axis=1)*h,n=nt,axis=1) for k,p in pol.items()};rows=[]
  for ref in ['Sold','Snew','SA8','SB8']:
   support=pv['old']&pv['new']&pv['base']&pv['L']&pv[ref]
   for name,region in regions.items():
    w=support&region;n=int(w.sum())
    if n<100:continue
    pairs={}
    for a,b in [(a,b) for a in ['old','new','base'] for b in [ref,'L']]+[(ref,'L')]:
     rho=corr(band[a],band[b],w);null=[corr(band[a],np.roll(band[b],120*j,axis=1),w) for j in range(1,12)];mx=max(map(abs,null));pairs[a+'_'+b]=dict(r=rho,null_max_abs=mx,pass_null=rho>mx)
    triple={a:all(pairs[k]['pass_null'] for k in [a+'_'+ref,a+'_L',ref+'_L']) for a in ['old','new','base']};rad=rr[np.where(w)[0]];rows.append(dict(region=name,ref=ref,samples=n,radius_range=[float(rad.min()),float(rad.max())],pairs=pairs,triple=triple))
  results[mode][f'{lo}_{hi}']=rows;print(mode,lo,hi,'old,new',sum(v['triple']['old'] for v in rows),sum(v['triple']['new'] for v in rows),flush=True)
save('B4_full_source_judge.json',dict(method=__doc__,results=results,limits=['Rotation controls exploratory, no globally calibrated discovery threshold','Per-reference coverage differs; old/new compared only on identical samples','No new photographic product or full RAW injection PASS']))
