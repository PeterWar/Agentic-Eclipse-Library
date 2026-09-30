"""V29: explicit coordinates and immutable upstream reads."""
from pathlib import Path
import sys, json, time, os
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter1d
from astropy.io import fits
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CAU=HERE/'cau'
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_20260905')
CT=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
OLD=ROOT/'research/tools/v25_lineal/cau_v25'
sys.path.insert(0,str(ROOT/'research/tools/eclipse_determinista'))
import comu
RUNROOT=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS')
RUNS={'vixen':RUNROOT/'019_VIXEN_CIENCIA_20260827T212404Z','sony':RUNROOT/'016_SONYTOT_CIENCIA_20260827T183356Z'}
LL=json.loads((RUNS['vixen']/'4-rebuts/F1.2_sol_llenc.json').read_text())['llenc']
W,H,RS=LL['W'],LL['H'],LL['R_sol_px']
M=np.asarray(json.loads((OLD/'geometria_v27.json').read_text())['M_llenc_a_v23'],np.float64)
CX,CY=(M@np.array([W/2,H/2,1])).tolist()
FW,FH=10551,7506
COMMON_TO_FINAL=M.copy(); ORIGINAL_COMMON_WH=(W,H)
SUN_XY=(W/2,H/2);GHOST_XY=(2825,3988)
FINAL_GRID=os.environ.get('V29_FINAL_GRID')=='1'
if FINAL_GRID:
    CAU=HERE/'cau_final';CAU.mkdir(exist_ok=True)
    GHOST_XY=tuple((M@np.array([2825,3988,1])).tolist())
    W,H=FW,FH;SUN_XY=(CX,CY);M=np.array([[1,0,0],[0,1,0]],np.float64)
cv2.setNumThreads(6)
def log(s): print(time.strftime('%H:%M:%S'),s,flush=True)
def savejson(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')
def smooth(x,a,b):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def coords():
    y,x=np.ogrid[:H,:W]
    return np.hypot(y-SUN_XY[1],x-SUN_XY[0]).astype(np.float32),np.arctan2(y-SUN_XY[1],x-SUN_XY[0]).astype(np.float32)
def gauss(a,s): return cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101)
def normgauss(a,w,s):
    den=gauss(w,s)
    return gauss(np.where(w>0,a,0)*w,s)/np.maximum(den,1e-8)
def radial_profile(a,m,r,nb=600,stride=3):
    # Sample only to estimate the smooth background; filtering remains full size.
    rr=r[::stride,::stride]; aa=a[::stride,::stride]; mm=m[::stride,::stride]&np.isfinite(aa)
    q=np.log(np.maximum(rr[mm]/RS,1e-5)); v=aa[mm]
    edges=np.linspace(float(q.min()),float(q.max()),nb+1); cen=(edges[:-1]+edges[1:])/2
    idx=np.clip(np.searchsorted(edges,q)-1,0,nb-1); o=np.argsort(idx,kind='stable'); v=v[o]; idx=idx[o]
    cuts=np.searchsorted(idx,np.arange(nb+1)); p=np.full(nb,np.nan)
    for i in range(nb):
        if cuts[i+1]-cuts[i]>=12: p[i]=np.median(v[cuts[i]:cuts[i+1]])
    ok=np.isfinite(p); p=np.interp(cen,cen[ok],p[ok]); p=gaussian_filter1d(p,3,mode='nearest')
    return cen,p
def detrend(a,m,r):
    cen,p=radial_profile(a,m,r)
    bg=np.interp(np.log(np.maximum(r/RS,1e-5)),cen,p).astype(np.float32)
    return np.where(m,a-bg,0).astype(np.float32)
def warp(a,mask=False):
    return cv2.warpAffine(np.ascontiguousarray(a),M,(FW,FH),flags=cv2.INTER_LINEAR if mask else cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
