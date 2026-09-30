"""V31 independent scientific outputs. Native canvas; observed G radiance only."""
from pathlib import Path
import os, json, time, hashlib
os.environ['V29_FINAL_GRID']='1'
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
D=Path(__file__).resolve().parent
ROOT=D.parents[2]; C=D/'cau'; OUT=ROOT/'output/v31_purs_20260906'
OLD=ROOT/'research/tools/v29/cau_final'; FIX=ROOT/'research/tools/v29_c03_fix'
H,W=7506,10551
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
cv2.setNumThreads(4)
def log(s): print(time.strftime('%H:%M:%S'),s,flush=True)
def savejson(p,d): Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def coords(shape=(H,W),origin=(0,0)):
 y,x=np.ogrid[origin[0]:origin[0]+shape[0],origin[1]:origin[1]+shape[1]]
 return np.hypot(x-CX,y-CY), np.arctan2(y-CY,x-CX)
def smooth(a,lo,hi):
 t=np.clip((a-lo)/(hi-lo),0,1);return t*t*(3-2*t)
def gaussian(a,s,truncate=3):
 k=2*int(truncate*s+.5)+1
 return cv2.GaussianBlur(np.asarray(a,np.float32),(k,k),s,borderType=cv2.BORDER_REPLICATE)
def ng(a,m,s,truncate=3):
 den=gaussian(m.astype('float32'),s,truncate)
 return gaussian(np.where(m,a,0),s,truncate)/np.maximum(den,1e-20)
def readbase(): return np.load(C/'base_G.npy',mmap_mode='r'),np.load(C/'support.npy')
def save_output(tag,a,m,parameters,display=None):
 a=np.asarray(a,np.float32); assert np.isfinite(a[m]).all(),tag
 a[~m]=np.nan; np.save(C/(tag+'_float.npy'),a)
 sample=a[::4,::4];sample=sample[np.isfinite(sample)]
 percentile_display=display is None
 if display is None: display=[float(x) for x in np.percentile(sample,[.1,99.9])]
 lo,hi=display; assert hi>lo
 u=np.round(np.clip(np.nan_to_num((a-lo)/(hi-lo),nan=0),0,1)*65535).astype('uint16')
 np.save(C/(tag+'_u16.npy'),u)
 from PIL import Image
 im=Image.fromarray((u//257).astype('uint8'));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/(tag+'_full.png'))
 rep={'tag':tag,'parameters':parameters,'physical_support_pixels':int(m.sum()),'float_sha256':sha(C/(tag+'_float.npy')),'display':{'type':'one global affine LUT only; scientific float retained','black':lo,'white':hi,'sample_percentiles':[.1,99.9] if percentile_display else None,'clipped_low_fraction':float(np.mean(a[m]<lo)),'clipped_high_fraction':float(np.mean(a[m]>hi))},'u16_sha256':sha(C/(tag+'_u16.npy'))}
 savejson(D/'receipts'/(tag+'.json'),rep);log('saved '+tag)
 return rep
