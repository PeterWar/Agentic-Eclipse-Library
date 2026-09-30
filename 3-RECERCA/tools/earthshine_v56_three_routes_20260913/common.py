"""Isolated three-route campaign, explicitly frozen V55 and previous sources."""
from pathlib import Path
import numpy as np,json,hashlib,datetime
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026');HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/earthshine_v56_three_routes_20260913';OLD=ROOT/'output/earthshine_max_detail_20260913';OLD54=ROOT/'output/earthshine_v54_detail_20260913'
CLAIM='CODEX_EARTHSHINE_V56_THREE_ROUTES_20260913';N=1400;CX=699.568111973117;CY=699.6475341408573;X0=4677;Y0=3077
CI=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors');V55=CI/'Earthshine_V55.psb';V55_SHA='90d6559f922ab6cbda0db6508678f46026921c70d17b9255e95182409754a28f'
def claim():assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data):
 claim()
 with (OUT/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item() if isinstance(a,np.generic) else str(a));f.write('\n')
def geometry():
 y,x=np.mgrid[:N,:N];return np.hypot(x-CX,y-CY),np.arctan2(y-CY,x-CX)%(2*np.pi)
def frames():return json.loads((OLD/'A1_native_rgb_all.json').read_text())['frames']
def corr(a,b,mask):
 m=mask&np.isfinite(a)&np.isfinite(b);x=a[m].astype(float);y=b[m].astype(float);x-=x.mean();y-=y.mean();return float(x@y/max(np.linalg.norm(x)*np.linalg.norm(y),1e-30))
def pull(a,shift):
 sx,sy=shift;ix=int(np.floor(sx));iy=int(np.floor(sy));qx=sx-ix;qy=sy-iy
 return sum(w*np.roll(a,(-dy,-dx),(0,1)) for dy,dx,w in [(iy,ix,(1-qy)*(1-qx)),(iy,ix+1,(1-qy)*qx),(iy+1,ix,qy*(1-qx)),(iy+1,ix+1,qy*qx)])
