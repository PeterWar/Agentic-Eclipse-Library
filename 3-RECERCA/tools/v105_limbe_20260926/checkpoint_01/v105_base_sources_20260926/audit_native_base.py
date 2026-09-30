from pathlib import Path
import json,sys,hashlib,io
import numpy as np
R=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/v105_base_sources_20260926');B=Path('/private/tmp/v105_root_pilots_20260926/P01');sys.path.insert(0,str(R/'3-RECERCA/tools/v71_marques_v69_20260916'));sys.path.insert(0,str(B.parent));from psb69 import PSB
from build_stage import records
from psd_tools.constants import Tag
paths={'source':R/'1-PHOTOSHOP/V104.psb','stage':B/'V105_P01_stage.psb','native':B/'native/V105_P01.psb'};psbs={k:PSB(p) for k,p in paths.items()};rect=(4677,3077,6077,4477);x0,y0,x1,y1=rect;roi=np.load(B/'BASE_ROI.npz')['base_rgb_u16'];report={'paths':{k:str(v) for k,v in paths.items()},'channels':{},'metadata':{},'tags':{}}
def stat(a,b):
 d=a.astype(np.int32)-b.astype(np.int32);return {'different':int(np.count_nonzero(d)),'max_abs_DN16':int(np.max(abs(d))) if d.size else 0,'mean_DN16':float(d.mean()) if d.size else 0,'quantile_DN16':np.quantile(d,[0,.01,.5,.99,1]).tolist() if d.size else []}
yy,xx=np.mgrid[y0:y1,x0:x1];outer=np.hypot(xx-5375.786804312011,yy-3775.9774911631)-452.9785129274736>=150
for cid in [0,1,2,-1,-2]:
 source,origin=psbs['source'].channel(3,cid);row={}
 for key,lid in [('stage',3),('stage',304),('native',3),('native',304)]:
  arr,org=psbs[key].channel(lid,cid);assert org==origin
  roiarr=arr[y0:y1,x0:x1];srcroi=source[y0:y1,x0:x1];s={'whole_vs_source':stat(arr,source),'ROI_vs_source':stat(roiarr,srcroi),'outside150_in_ROI_vs_source':stat(roiarr[outer],srcroi[outer]),'sample4813_3549':{'value':int(arr[3549,4813]),'source':int(source[3549,4813])}}
  if cid>=0:s['ROI_vs_BASE_ROI']=stat(roiarr,roi[...,cid]);s['outside_ROI_vs_source']={'different':int(np.count_nonzero(arr[:y0]!=source[:y0])+np.count_nonzero(arr[y1:]!=source[y1:])+np.count_nonzero(arr[y0:y1,:x0]!=source[y0:y1,:x0])+np.count_nonzero(arr[y0:y1,x1:]!=source[y0:y1,x1:]))}
  row[f'{key}_{lid}']=s;del arr
 report['channels'][str(cid)]=row;del source;print('channel',cid,json.dumps({k:{'outer150':v['outside150_in_ROI_vs_source'],'whole':v['whole_vs_source']} for k,v in row.items()}),flush=True)
for key,p in paths.items():
 rr=records(p)['recs'];found={int(r.tagged_blocks.get_data(Tag.LAYER_ID)):r for r,_ in rr}
 for lid in [3,304]:
  if lid not in found:continue
  r=found[lid];report['metadata'][f'{key}_{lid}']={k:v for k,v in psbs[key].layer(lid).items() if k!='chans'};report['metadata'][f'{key}_{lid}']['flags']=repr(r.flags);report['metadata'][f'{key}_{lid}']['blending_ranges']=repr(r.blending_ranges);tags={}
  for tag,block in r.tagged_blocks.items():
   try:
    f=io.BytesIO();block.write(f,version=2);data=f.getvalue();tags[str(tag)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'repr':repr(block.data)[:250]}
   except Exception as e:tags[str(tag)]={'repr':repr(block)[:400],'exception':str(e)}
  report['tags'][f'{key}_{lid}']=tags
with paths['source'].open('rb') as f:report['source_current_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
report['source_matches_expected']=report['source_current_sha256']=='da2b0792db66e91e93a064540feaceafc25ea9cfc6e328d54d3c8980eabc60fa'
(O/'NATIVE_BASE_ROUNDTRIP_AUDIT.json').write_text(json.dumps(report,indent=2));print('COMPLETE source intact',report['source_matches_expected'],flush=True)
