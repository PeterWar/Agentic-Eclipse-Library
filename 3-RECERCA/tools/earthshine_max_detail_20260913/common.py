"""Isolated maximum-detail campaign; no legacy executable imports."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026')
HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/earthshine_max_detail_20260913'
CLAIM='CODEX_EARTHSHINE_MAX_DETAIL_RGB_FPN_20260913'
N=1400;CX=699.568111973117;CY=699.6475341408573;X0=4677;Y0=3077
RUNROOT=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS')
RUNS={'vixen':RUNROOT/'019_VIXEN_CIENCIA_20260827T212404Z','sony':RUNROOT/'016_SONYTOT_CIENCIA_20260827T183356Z'}
CAU36=ROOT/'research/tools/v36_20260908/cau'
CI=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
def claim():
    assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data):
    claim()
    with (OUT/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item() if isinstance(a,np.generic) else str(a));f.write('\n')
def frames():return json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames']
def geometry():
    y,x=np.mgrid[:N,:N];return np.hypot(x-CX,y-CY),np.arctan2(y-CY,x-CX)%(2*np.pi)
def corr(a,b,mask):
    good=mask&np.isfinite(a)&np.isfinite(b);a=a[good].astype(float);b=b[good].astype(float);a-=a.mean();b-=b.mean()
    if len(a)<50:return float('nan')
    return float(a@b/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
