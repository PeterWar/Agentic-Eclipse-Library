"""Read-only comparison of full-context native renders, writing only agent tmp."""
from pathlib import Path
import numpy as np, tifffile, json, hashlib, sys
OUT=Path('/private/tmp/v105_base_sources_20260926')
D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/private/tmp/v105_root_pilots_20260926/P05/native_probe')
q=np.load('/private/tmp/v105_root_pilots_20260926/P05/Q_OBSERVED.npz')
cx,cy,r=map(float,q['centre']);yy,xx=np.mgrid[3000:4550,4600:6150];dr=np.hypot(xx-cx,yy-cy)-r
by0,by1,bx0,bx1=map(int,q['box'])
inside=(xx>=bx0)&(xx<bx1)&(yy>=by0)&(yy<by1)
regions={'all':np.ones(dr.shape,bool),'outside150':dr>=150,'outside_base_ROI':~inside,'0-10':(dr>=0)&(dr<10),'10-25':(dr>=10)&(dr<25),'25-100':(dr>=25)&(dr<100)}
report={'input_directory':str(D),'crop_xyxy':[4600,3000,6150,4550],'centre_radius':[cx,cy,r],'method':'Read TIFF uint16. Every crop derives from full-canvas merged duplicate before crop. Delta is new minus old. Source base native exact outside150 was audited independently.','cases':{}}
deltas={}
def metrics(a,sel):
 t=a[sel]
 return {'n':int(sel.sum()),'nonzero_pixels':int(np.any(t!=0,axis=-1).sum()),'median_DN':np.median(t,axis=0).tolist(),'mean_DN':np.mean(t,axis=0).tolist(),'p01_DN':np.percentile(t,1,axis=0).tolist(),'p99_DN':np.percentile(t,99,axis=0).tolist(),'max_abs_DN':np.max(abs(t),axis=0).tolist()}
for case in ['both_off','luz_off_clarity_on','luz_on_clarity_off','both_on']:
 paths=[D/(case+'_'+side+'.tif') for side in ('old','new')]
 if not all(p.exists() for p in paths):continue
 try:
  old,new=[tifffile.imread(p) for p in paths]
 except Exception as e:
  report.setdefault('incomplete_reads',{})[case]=str(e);continue
 assert old.shape==new.shape==(1550,1550,3) and old.dtype==new.dtype==np.uint16
 delta=new.astype(np.int32)-old.astype(np.int32);deltas[case]=delta
 rec={'files':[str(p)for p in paths],'file_sha256':[hashlib.file_digest(p.open('rb'),'sha256').hexdigest()for p in paths],'regions':{n:metrics(delta,s)for n,s in regions.items()},'test_point_4813_3549':{'old':old[549,213].tolist(),'new':new[549,213].tolist(),'delta':delta[549,213].tolist()}}
 rec['new_clipped_counts_RGB']=np.sum((old<65535)&(new==65535),axis=(0,1)).tolist()
 rec['old_clipped_counts_RGB']=np.sum(old==65535,axis=(0,1)).tolist()
 rec['new_total_clipped_counts_RGB']=np.sum(new==65535,axis=(0,1)).tolist()
 report['cases'][case]=rec
if len(deltas)==4:
 report['complete']=True
 contrast={'effect_luz_alone':deltas['luz_on_clarity_off']-deltas['both_off'],'effect_clarity_alone':deltas['luz_off_clarity_on']-deltas['both_off'],'interaction':deltas['both_on']-deltas['luz_on_clarity_off']-deltas['luz_off_clarity_on']+deltas['both_off']}
 report['factorial_delta_contrasts']={n:{k:metrics(a,s)for k,s in regions.items()}for n,a in contrast.items()}
else:report['complete']=False
path=OUT/('NATIVE_'+D.parent.name+'_ADJUSTMENT_QA'+(''if report['complete']else'_PARTIAL')+'.json')
path.write_text(json.dumps(report,indent=2))
print(path)
for case,rec in report['cases'].items():print(case,'outside150',rec['regions']['outside150'],'new_clip',rec['new_clipped_counts_RGB'])
print('COMPLETE',report['complete'])
