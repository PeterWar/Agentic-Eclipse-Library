from pathlib import Path
import json,hashlib,datetime,shutil,gc,zlib
import numpy as np
from psd_tools import PSDImage
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v58_correccions_20260913'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V58_SIX_CORRECTIONS_20260913'
S=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V57.psb')
with S.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
snapshot=O/'V57_Pere_input.psb'
if not snapshot.exists():shutil.copyfile(S,snapshot)
with snapshot.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
s=PSDImage.open(snapshot)
print('SOURCE',sha,len(s),s.size,s.depth,flush=True)
def channel(l,c):
 i=next((i for i,ci in enumerate(l._record.channel_info) if int(ci.id)==c),None)
 if i is None:return None
 w,h=(l._record.mask_data.width,l._record.mask_data.height) if c==-2 else (l.width,l.height)
 cd=l._channels[i]
 if int(cd.compression)==3:
  return np.cumsum(np.frombuffer(zlib.decompress(cd.data),dtype='>u2').reshape(h,w),axis=1,dtype=np.uint16)
 return np.frombuffer(cd.get_data(w,h,16,2),dtype='>u2').reshape(h,w)
def crop(a,box,target,fill=0):
 out=np.full((target[3]-target[1],target[2]-target[0]),fill,np.uint16);x0,y0=max(box[0],target[0]),max(box[1],target[1]);x1,y1=min(box[2],target[2]),min(box[3],target[3]);
 if x0<x1 and y0<y1:out[y0-target[1]:y1-target[1],x0-target[0]:x1-target[0]]=a[y0-box[1]:y1-box[1],x0-box[0]:x1-box[0]]
 return out
roi=(4377,2777,6377,4777);layers=[]
for idx,l in enumerate(s):
 box=list(l.bbox);row=dict(index=idx,name=l.name,bbox=box,visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode),channels=[dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)],mask=None if l._record.mask_data is None else l._record.mask_data.tobytes().hex())
 g=channel(l,1);np.save(O/'arrays'/f'L{idx:02d}_G_roi.npy',crop(g,box,roi))
 # Native grid reduced strictly for overview/alignment sampling. Source pixels remain untouched.
 out=np.zeros((1877,2638),np.uint16);yy=np.arange(0,7506,4);xx=np.arange(0,10551,4);iy=np.flatnonzero((yy>=box[1])&(yy<box[3]));ix=np.flatnonzero((xx>=box[0])&(xx<box[2]));out[np.ix_(iy,ix)]=g[np.ix_(yy[iy]-box[1],xx[ix]-box[0])];np.save(O/'arrays'/f'L{idx:02d}_G_quarter.npy',out)
 for c in (-1,-2):
  a=channel(l,c)
  if a is None:continue
  mb=box if c==-1 else [l._record.mask_data.left,l._record.mask_data.top,l._record.mask_data.right,l._record.mask_data.bottom]
  default=0 if c==-1 else int(l._record.mask_data.background_color)*257
  row[f'channel{c}_bbox']=mb;np.save(O/'arrays'/f'L{idx:02d}_C{c}_roi.npy',crop(a,mb,roi,default))
 layers.append(row);print(idx,l.name,box,'visible',l.visible,flush=True);del g,out;gc.collect()
rep=dict(source=str(S),snapshot=str(snapshot),sha256=sha,bytes=S.stat().st_size,previous_delivery_sha256='ef4ee9fe93370e1d9c9bc453a788b6f67c1415061383887fa06ac2762b8f156a',native_documents_initial='NONE',layers=layers,size=list(s.size),depth=s.depth,roi=roi,created=datetime.datetime.now(datetime.timezone.utc).isoformat())
(O/'A0_freeze.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2));print('FROZEN',flush=True)
