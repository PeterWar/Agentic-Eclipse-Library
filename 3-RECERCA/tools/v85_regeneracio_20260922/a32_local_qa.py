"""Paired known-truth assessment of local MGN and RGB ACHF pre-display data."""
from a27_boundary_qa import *

def main():
 root=O/'analytic_local';receipt=json.loads((root/'COMPLETE.json').read_text());assert receipt['PASS'] and len(receipt['products'])==33
 for row in receipt['products']:
  p=root/row['case']/(row['tag']+'.npy');assert sha(p)==row['sha256'];a=np.load(p,mmap_mode='r');assert a.shape==(2800,2800) and a.dtype==np.float32 and np.isfinite(a).all()
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=z['box'];x0-=700;y0-=700;x1+=700;y1+=700;moon=np.zeros((2800,2800),bool);moon[700:2100,700:2100]=z['support'];distance=distance_transform_edt(~moon);valid=np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r')[y0:y1,x0:x1]&~moon;y,x=np.mgrid[y0:y1,x0:x1];r=np.hypot(y-3775.747534140857,x-5361.768111973117);theta=np.arctan2(y-3775.747534140857,x-5361.768111973117);rows=[]
 for tag in ['01','04','05','06','MGN']:
  oracle=np.load(root/'base_oracle'/(tag+'.npy')).astype(np.float64);d0=np.load(root/'injected_oracle'/(tag+'.npy')).astype(np.float64)-oracle
  for case in (['A','D'] if tag=='MGN' else ['A','C','T']):
   a=np.load(root/('base_'+case)/(tag+'.npy')).astype(np.float64);err=a-oracle;row={'tag':tag,'case':case,'bands':[]}
   for lo,hi in BANDS:
    m=valid&(distance>lo)&(distance<=hi);v=err[m];row['bands'].append({'distance_px':[lo,hi],'n':int(m.sum()),'median':float(np.median(v)),'rms':float(np.sqrt(np.mean(v*v))),'p95abs':float(np.percentile(np.abs(v),95))})
   ip=root/('injected_'+case)/(tag+'.npy')
   if ip.exists():
    d1=np.load(ip).astype(np.float64)-a;trans=[]
    for i,lam in enumerate([5.,18.,70.]):
     for j,orient in enumerate(['radial','tangential','oblique']):
      angle=-np.pi+(i*3+j+.5)*2*np.pi/9;da=np.arctan2(np.sin(theta-angle),np.cos(theta-angle));window=np.exp(-(da/.13)**8)*np.exp(-((r-490)/90)**8)
      for lo,hi in BANDS:
       m=valid&(distance>lo)&(distance<=hi)&(window>.1);u=d1[m];v=d0[m];power=float(v@v)
       if m.sum()<20 or power<1e-16:continue
       trans.append({'orientation':orient,'wavelength_px':lam,'distance_px':[lo,hi],'n':int(m.sum()),'oracle_power':power,'gain':float(u@v/power),'nrmse':float(np.sqrt(np.sum((u-v)**2)/power))})
    row['transfer']=trans
   rows.append(row);print(tag,case,'RMS',[(v['distance_px'],round(v['rms'],5)) for v in row['bands'][:6]],'transfer',len(row.get('transfer',[])),flush=True)
 save(O/'LOCAL_BOUNDARY_QA.json',{'input_integrity_PASS':True,'scope':json.loads((root/'SCOPE.json').read_text()),'rows':rows,'scientific_PASS':None,'interpretation':'known-truth development control; report failing distance/scale/orientation cases, do not claim universal retention'})

if __name__=='__main__':guard();main()
