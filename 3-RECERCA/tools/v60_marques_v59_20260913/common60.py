from pathlib import Path
import json,hashlib,zlib
import numpy as np
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v60_marques_v59_20260913';T=R/'research/tools/v60_marques_v59_20260913';PREV=R/'output/v58_correccions_20260913';SRC=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V59.psb');CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544;ROI=(4377,2777,6377,4777)
def claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V60_V59_MARKS_20260913'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,d):
 p=O/n;assert not p.exists(),p;p.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def chan(l,c):
 i=next((i for i,q in enumerate(l._record.channel_info) if int(q.id)==c),None)
 if i is None:return None
 w,h=(l._record.mask_data.width,l._record.mask_data.height) if c==-2 else (l.width,l.height);cd=l._channels[i]
 if int(cd.compression)==3:return np.cumsum(np.frombuffer(zlib.decompress(cd.data),dtype='>u2').reshape(h,w),axis=1,dtype=np.uint16)
 return np.frombuffer(cd.get_data(w,h,16,2),dtype='>u2').reshape(h,w)
def box(l,c,bb=ROI):
 out=np.full((bb[3]-bb[1],bb[2]-bb[0]),0,np.uint16);a=chan(l,c)
 if a is None:return out
 x,y=(l._record.mask_data.left,l._record.mask_data.top) if c==-2 else (l.left,l.top);h,w=a.shape;x0,y0=max(x,bb[0]),max(y,bb[1]);x1,y1=min(x+w,bb[2]),min(y+h,bb[3]);
 if x1>x0 and y1>y0:out[y0-bb[1]:y1-bb[1],x0-bb[0]:x1-bb[0]]=a[y0-y:y1-y,x0-x:x1-x]
 return out
