"""Fixed candidate versus separate late Sony 2s captures; no source pixels from judge.
Uses unpainted sectors, original texture geometry, fixed bands and rotated nulls.
A source compositor control, not proof of lunar texture at every last pixel.
"""
from validation_common import *
from scipy.ndimage import map_coordinates,gaussian_filter,distance_transform_edt
from scipy.fft import dctn,idctn
z=np.load(OUT/'C0_temporal_ensemble.npz');raw={'reference':np.load(CAU45/'vixen_reference.npy'),'sum':z['base'],'candidate':z['candidate']}
for stem in ['DSC06996','DSC06999']:
 d=np.load(CAU45/('native_sony_'+stem+'.npz'));a=d['g'].astype(float);a[(d['q']<=0)|~np.isfinite(a)]=np.nan;raw[stem]=a
rr=np.arange(350.,452.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None]);pol={};valid={}
for k,a in raw.items():
 m=np.isfinite(a)&(a>0);valid[k]=map_coordinates(m.astype(float),co,order=1,mode='constant',cval=0)>.999
 idx=distance_transform_edt(~m,return_distances=False,return_indices=True);v=a[tuple(idx)];pol[k]=map_coordinates(np.log(v),co,order=3,mode='nearest')
marks=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz');paint=marks['green']|marks['purple'];unpaint=map_coordinates(paint.astype(float),co,order=1,mode='constant',cval=1)==0
def corr(a,b,m):
 a=a[m];b=b[m];a-=a.mean();b-=b.mean();return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
rows=[]
for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
 h=(freq>=1/hi)&(freq<=1/lo);band={k:np.fft.irfft(np.fft.rfft(p,axis=1)*h,n=nt,axis=1) for k,p in pol.items()}
 for ref in ['DSC06996','DSC06999']:
  for sector in range(12):
   m=unpaint&valid[ref]&valid['reference']&valid['candidate']&(np.arange(nt)[None,:]//120==sector)
   if m.sum()<200:continue
   pairs={}
   for k in ['reference','sum','candidate']:
    r=corr(band[k],band[ref],m);null=[corr(band[k],np.roll(band[ref],j*120,1),m) for j in range(1,12)];pairs[k]=dict(r=r,null=max(map(abs,null)),pass_null=r>max(map(abs,null)))
   rows.append(dict(band=[lo,hi],ref=ref,sector=sector,n=int(m.sum()),pairs=pairs))
# Full-asimuth alignment, exclude liminal field and all painted samples.
shifts=np.arange(-16,17);alignment=[]
for ref in ['DSC06996','DSC06999']:
 h=(freq>=1/64)&(freq<=1/24);aa=np.fft.irfft(np.fft.rfft(pol['candidate'],axis=1)*h,n=nt,axis=1);bb=np.fft.irfft(np.fft.rfft(pol[ref],axis=1)*h,n=nt,axis=1)
 m=unpaint&valid[ref]&(rr[:,None]<430);scores=[corr(aa,np.roll(bb,int(j),1),m) for j in shifts];alignment.append(dict(ref=ref,peak_degrees=float(shifts[np.argmax(scores)]*.25),r_peak=max(scores),r_zero=scores[16],r_null180=corr(aa,np.roll(bb,720,1),m)))
loss=[r for r in rows if r['pairs']['reference']['pass_null'] and not r['pairs']['candidate']['pass_null']];gains=[r for r in rows if not r['pairs']['reference']['pass_null'] and r['pairs']['candidate']['pass_null']]
save('C3_new_captures_judge.json',dict(method=__doc__,rows=rows,alignment=alignment,pass_losses=len(loss),pass_gains=len(gains),limit='These individual captures are external to Vixen reconstruction; not independent of historical whole-project exploration. Fourier validity fill used only by judge.'))
print('comparison count',len(rows),'pass losses',len(loss),'pass gains',len(gains),'alignment',alignment,flush=True)
