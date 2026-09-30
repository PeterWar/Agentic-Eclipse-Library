"""Frozen-geometry QA for physical unit-tension controls; keep old failures."""
from a27_boundary_qa import *
from a46_analytic_physical import scene,namespace

def main():
 root=O/'analytic_physical_T_R02';receipt=json.loads((root/'COMPLETE.json').read_text());assert receipt['PASS'] and len(receipt['products'])==16
 for row in receipt['products']:
  path=root/row['case']/(row['tag']+'.npy');assert sha(path)==row['sha256'];a=np.load(path,mmap_mode='r');assert a.shape==((7506,10551) if row['tag'].startswith('WOW') else (2800,2800)) and a.dtype==np.float32
  for yy in range(0,a.shape[0],256):assert np.isfinite(a[yy:yy+256]).all()
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=z['box'];x0-=700;y0-=700;x1+=700;y1+=700;sl=(slice(y0,y1),slice(x0,x1));moon=np.zeros((2800,2800),bool);moon[700:2100,700:2100]=z['support'];distance=distance_transform_edt(~moon);physical=np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r');valid=physical[sl]&~moon;y,x=np.mgrid[y0:y1,x0:x1];r=np.hypot(y-3775.747534140857,x-5361.768111973117);theta=np.arctan2(y-3775.747534140857,x-5361.768111973117);sector=np.floor((theta+np.pi)*36/(2*np.pi)).astype(int)%36;rows=[]
 def read(path):
  a=np.load(path,mmap_mode='r');return np.asarray(a[sl] if a.shape==(7506,10551) else a,np.float64)
 def measure(tag,case,base,inj,oracle,ioracle):
  err=base-oracle;row={'tag':tag,'case':case,'bands':[]};d0=ioracle-oracle;d1=inj-base
  for lo,hi in BANDS:
   m=valid&(distance>lo)&(distance<=hi);e=err[m];row['bands'].append({'distance_px':[lo,hi],'n':int(m.sum()),'median':float(np.median(e)),'rms':float(np.sqrt(np.mean(e*e))),'p95abs':float(np.percentile(abs(e),95)),'sector_medians':[float(np.median(err[m&(sector==k)])) if np.any(m&(sector==k)) else None for k in range(36)]})
  trans=[]
  for i,lam in enumerate([5.,18.,70.]):
   for j,orient in enumerate(['radial','tangential','oblique']):
    angle=-np.pi+(i*3+j+.5)*2*np.pi/9;da=np.arctan2(np.sin(theta-angle),np.cos(theta-angle));window=np.exp(-(da/.13)**8)*np.exp(-((r-490)/90)**8)
    for lo,hi in BANDS:
     m=valid&(distance>lo)&(distance<=hi)&(window>.1);u=d1[m];v=d0[m];power=float(v@v)
     if m.sum()<20 or power<1e-16:continue
     trans.append({'orientation':orient,'wavelength_px':lam,'distance_px':[lo,hi],'n':int(m.sum()),'oracle_power':power,'gain':float(u@v/power),'nrmse':float(np.sqrt(np.sum((u-v)**2)/power))})
  row['transfer']=trans;row['gain_failures']=sum(not(.9<=q['gain']<=1.1) for q in trans);rows.append(row);print('PHYSICAL_QA',tag,case,'fail',row['gain_failures'],'/',len(trans),'RMS',[(q['distance_px'],round(q['rms'],6)) for q in row['bands'][:5]],flush=True)
 for tag in ['01','04','05','06','WOW','WOW_bilateral']:
  if tag.startswith('WOW'):oldroot=O/'analytic_biharmonic';ob=O/'analytic_boundary/base_oracle'/(tag+'.npy');oi=O/'analytic_boundary/injected_oracle'/(tag+'.npy');oldbase=oldroot/'base_D_A'/(tag+'.npy');oldinj=oldroot/'injected_D_A'/(tag+'.npy')
  else:oldroot=O/'analytic_local';ob=oldroot/'base_oracle'/(tag+'.npy');oi=oldroot/'injected_oracle'/(tag+'.npy');oldbase=oldroot/'base_T'/(tag+'.npy');oldinj=oldroot/'injected_T'/(tag+'.npy')
  oracle,ioracle=read(ob),read(oi);measure(tag,'delivered_R01',read(oldbase),read(oldinj),oracle,ioracle);measure(tag,'physical_T_R02',read(root/'base'/(tag+'.npy')),read(root/'injected'/(tag+'.npy')),oracle,ioracle)
 # MGN production changes only global gamma normalization when observed extrema
 # change; align the old selected/oracle at observed judged pixels, preserving
 # its old detailed convolution and all old receipts.
 ns=namespace(root);rr,tt=ns['coords']();truth,injection,_=scene(dict(np=np,r=rr,t=tt));limits=json.loads((root/'LIMITS.json').read_text());old={};maxerrors=[]
 for isinj,label in [(False,'base'),(True,'injected')]:
  a=(truth*np.exp(injection,dtype=np.float32) if isinj else truth)[sl];lim=next(q for q in limits if q['case']==label)
  def gamma(a,limits):lo,hi=limits;return np.clip((a-lo)/(hi-lo),0,1)**(1/3.2)
  delta=.7*(gamma(a,lim['physical'])-gamma(a,lim['old_domain']));old[label]=read(O/'analytic_local'/(label+'_D')/'MGN.npy')+delta;adjusted_oracle=read(O/'analytic_local'/(label+'_oracle')/'MGN.npy')+delta;paired=read(root/label/'MGN_oracle.npy');maxerrors.append(float(np.max(np.abs(adjusted_oracle[valid]-paired[valid]))));assert maxerrors[-1]<5e-7,maxerrors
 oracle=read(root/'base/MGN_oracle.npy');ioracle=read(root/'injected/MGN_oracle.npy');measure('MGN','delivered_R01_with_physical_gamma',old['base'],old['injected'],oracle,ioracle);measure('MGN','physical_T_R02',read(root/'base/MGN.npy'),read(root/'injected/MGN.npy'),oracle,ioracle)
 save(O/'PHYSICAL_R02_BOUNDARY_QA.json',{'input_integrity_PASS':True,'rows':rows,'bands_px':BANDS,'gain_limit':[.9,1.1],'mask':'same physical exterior and final photographic Moon exclusion as R01','MGN_adaptation':'old selected global gamma changed to physical limits at judged observed pixels only; fresh physical-limit oracle, old scientific results preserved','MGN_adapted_oracle_max_float_error':maxerrors,'limitations':['known-truth development test; not blind validation','injection includes unknown hidden field; error combines observed detail retention and continuation assumptions','E3 before display/SN/H1; no direct Photoshop composite acceptance','different physical and photographic unknown masks are not proof of valid radiance under photograph'],'scientific_PASS':None})
 print('PHYSICAL_R02_QA_COMPLETE')
if __name__=='__main__':guard();main()
