"""Frozen known-truth comparisons; calculation success is not scientific PASS."""
from a4_sources import *
from scipy.ndimage import distance_transform_edt

BANDS=[(0,2),(2,4),(4,8),(8,16),(16,32),(32,64),(64,128),(128,256),(256,512)]

def main():
 z=np.load(O/'current_lunar_support.npz');smallmoon=z['support'];x0,y0,x1,y1=z['box'];x0-=700;y0-=700;x1+=700;y1+=700;moon=np.zeros((2800,2800),bool);moon[700:2100,700:2100]=smallmoon;sl=(slice(y0,y1),slice(x0,x1));physical=np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r');valid=physical[sl]&~moon;distance=distance_transform_edt(~moon);dy,dx=np.gradient(distance);norm=np.hypot(dy,dx);dy/=np.maximum(norm,1e-30);dx/=np.maximum(norm,1e-30);y,x=np.mgrid[y0:y1,x0:x1];r=np.hypot(y-3775.747534140857,x-5361.768111973117);theta=np.arctan2(y-3775.747534140857,x-5361.768111973117);sector=np.floor((theta+np.pi)*36/(2*np.pi)).astype(int)%36
 outputs={};a=O/'analytic_boundary';b=O/'analytic_biharmonic'
 if '--final' in sys.argv:
  for folder,count in [(a,12),(b,12)]:
   receipt=json.loads((folder/'COMPLETE.json').read_text());assert receipt['PASS'] and len(receipt['products'])==count
   for row in receipt['products']:
    path=folder/row['case']/(row['filter']+'.npy');assert sha(path)==row['sha256'];arr=np.load(path,mmap_mode='r');assert arr.shape==(7506,10551) and arr.dtype==np.float32
    for yy in range(0,7506,256):assert np.isfinite(arr[yy:yy+256]).all()

 for profile,tag in [('A','WOW'),('A','WOW_bilateral'),('B','WOW')]:
  label=profile+'_'+tag;root=a if profile=='A' else b;suffix='' if profile=='A' else '_B';oracle=root/('base_oracle'+suffix)/(tag+'.npy');io=root/('injected_oracle'+suffix)/(tag+'.npy');rows=[]
  if not oracle.exists():continue
  ref=np.load(oracle,mmap_mode='r');refroi=np.asarray(ref[sl],np.float64)
  for case in ['A','B','C','D']:
   folder=(b/('base_D_A') if case=='D' and profile=='A' else root/('base_'+case+suffix));path=folder/(tag+'.npy')
   if not path.exists():continue
   q=np.load(path,mmap_mode='r');err=np.asarray(q[sl],np.float64)-refroi;ey,ex=np.gradient(err);normal=ey*dy+ex*dx;row={'case':case,'path':str(path.relative_to(R)),'bands':[]}
   for lo,hi in BANDS:
    m=valid&(distance>lo)&(distance<=hi);e=err[m];row['bands'].append({'distance_px':[lo,hi],'n':int(m.sum()),'median':float(np.median(e)),'rms':float(np.sqrt(np.mean(e*e))),'p95abs':float(np.percentile(np.abs(e),95)),'normal_gradient_rms':float(np.sqrt(np.mean(normal[m]**2))),'sector_medians':[float(np.median(err[m&(sector==k)])) if np.any(m&(sector==k)) else None for k in range(36)]})
   n=0;sse=0.;maximum=0.
   for yy in range(0,7506,256):
    mm=np.array(physical[yy:yy+256]);ya=max(yy,y0);yb=min(yy+256,y1)
    if yb>ya:mm[ya-yy:yb-yy,x0:x1]&=~moon[ya-y0:yb-y0]
    e=np.asarray(q[yy:yy+256],np.float64)[mm]-np.asarray(ref[yy:yy+256],np.float64)[mm];n+=len(e);sse+=float(e@e);maximum=max(maximum,float(np.max(np.abs(e))))
   row['full_canvas']={'n':n,'rms':(sse/n)**.5,'maxabs':maximum};inj=(b/'injected_D_A' if case=='D' and profile=='A' else root/('injected_'+case+suffix))/(tag+'.npy')
   if io.exists() and inj.exists():
    d0=np.asarray(np.load(io,mmap_mode='r')[sl],np.float64)-refroi;d1=np.asarray(np.load(inj,mmap_mode='r')[sl],np.float64)-np.asarray(q[sl],np.float64);trans=[]
    for i,lam in enumerate([5.,18.,70.]):
     for j,orient in enumerate(['radial','tangential','oblique']):
      angle=-np.pi+(i*3+j+.5)*2*np.pi/9;da=np.arctan2(np.sin(theta-angle),np.cos(theta-angle));window=np.exp(-(da/.13)**8)*np.exp(-((r-490)/90)**8)
      for lo,hi in BANDS:
       m=valid&(distance>lo)&(distance<=hi)&(window>.1);v=d0[m];u=d1[m];power=float(v@v)
       if m.sum()<20 or power<1e-16:continue
       trans.append({'orientation':orient,'wavelength_px':lam,'distance_px':[lo,hi],'n':int(m.sum()),'oracle_power':power,'gain':float((u@v)/power),'nrmse':float(np.sqrt(np.sum((u-v)**2)/power)),'correlation':(float(np.corrcoef(u,v)[0,1]) if np.std(u)>0 and np.std(v)>0 else None)})
    row['transfer']=trans
   rows.append(row)
  outputs[label]=rows
 save(O/'BOUNDARY_QA.json',{'bands_px':BANDS,'sector_count':36,'mask':'same physical exterior and exact lunar mask for every case','profile_A_WOW_limit':'shared-input boundary ablation; production WOW is profileB','gain_limit':[.9,1.1],'calculated_cases':outputs,'scientific_pass':None,'roi_shape':[2800,2800],'gradient_scope':'central differences; first boundary band can straddle numerical Moon pixels','final_integrity_verified':'--final' in sys.argv,'interpretation':'requires comparative assessment; final flag verifies input completion/hashes/shape/finiteness, not scientific acceptance'})
 for label,rows in outputs.items():
  for row in rows:
   print(label,row['case'],'rms',[(r['distance_px'],round(r['rms'],5),round(r['normal_gradient_rms'],5)) for r in row['bands'][:6]],'transfer',len(row.get('transfer',[])),flush=True)

if __name__=='__main__':guard();main()
