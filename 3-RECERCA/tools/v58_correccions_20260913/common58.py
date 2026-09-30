from pathlib import Path
import json,hashlib,zlib
import numpy as np
from scipy.ndimage import gaussian_filter,map_coordinates
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v58_correccions_20260913';T=R/'research/tools/v58_correccions_20260913';V42=R/'research/tools/v42_20260910';CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
ROI=(4377,2777,6377,4777)
def claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V58_SIX_CORRECTIONS_20260913'
def save(n,d):
 p=O/n;assert not p.exists(),p;p.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def chan(l,c):
 i=next((i for i,q in enumerate(l._record.channel_info) if int(q.id)==c),None)
 if i is None:return None
 w,h=(l._record.mask_data.width,l._record.mask_data.height) if c==-2 else (l.width,l.height);cd=l._channels[i]
 if int(cd.compression)==3:return np.cumsum(np.frombuffer(zlib.decompress(cd.data),dtype='>u2').reshape(h,w),axis=1,dtype=np.uint16)
 return np.frombuffer(cd.get_data(w,h,16,2),dtype='>u2').reshape(h,w)
def roi(idx,c=1):
 p=O/'arrays'/f'L{idx:02d}_{"G" if c==1 else "C"+str(c)}_roi.npy'
 return np.load(p) if p.exists() else np.full((2000,2000),65535,np.uint16)
def bp(a,lo=24,hi=96):
 fy=np.fft.fftfreq(a.shape[0])[:,None];fx=np.fft.rfftfreq(a.shape[1])[None,:];f=np.hypot(fy,fx)
 w=np.clip((f-1/hi)/(0.25/hi),0,1)*np.clip((1/lo-f)/(0.25/lo),0,1);return np.fft.irfft2(np.fft.rfft2(a)*w,s=a.shape).astype('float32')
def ncc(a,b):
 a=a-a.mean();b=b-b.mean();return float(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))
