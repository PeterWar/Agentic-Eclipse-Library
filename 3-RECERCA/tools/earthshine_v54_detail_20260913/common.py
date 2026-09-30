"""V54: isolated campaign. No legacy campaign imports or implicit writes."""
from pathlib import Path
import json, hashlib, datetime
import numpy as np
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
HERE = Path(__file__).resolve().parent
OUT = ROOT/'output/earthshine_v54_detail_20260913'
SRC = ROOT/'output/earthshine_native_psf_20260911'
CLAIM = 'CODEX_EARTHSHINE_V54_DETAIL_20260913'
CI = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
V53 = CI/'Earthshine_V53.psb'
V53_SHA = '6ef9a0cccf063ef796c1390495aa806e216f207b75924dead38c601e9ed9745a'
N=1400; CX=699.568111973117; CY=699.6475341408573; X0=4677; Y0=3077
def claim():
    assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
def sha(path):
    with open(path,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data):
    claim()
    with (OUT/name).open('x') as f: json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
def frame_list():
    return json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames']
def channel(layer,cid):
    ix=[int(c.id) for c in layer._record.channel_info].index(cid)
    if cid==-2:
        m=layer._record.mask_data; w,h=m.right-m.left,m.bottom-m.top
    else: w,h=layer.width,layer.height
    return np.frombuffer(layer._channels[ix].get_data(w,h,16,2),dtype='>u2').reshape(h,w).astype(np.uint16)
def fingerprint(l):
    return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
        channels=[dict(id=int(i.id),compression=int(c.compression),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)],
        mask=None if l._record.mask_data is None else dict(left=l._record.mask_data.left,top=l._record.mask_data.top,right=l._record.mask_data.right,bottom=l._record.mask_data.bottom,bg=l._record.mask_data.background_color))
def geometry():
    y,x=np.mgrid[:N,:N]; r=np.hypot(x-CX,y-CY); theta=np.arctan2(y-CY,x-CX)%(2*np.pi)
    from scipy.ndimage import gaussian_filter1d
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
    edge=gaussian_filter1d(edge,3.,mode='wrap')
    er=np.interp(theta,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi)
    return r,theta,r-er
def corr(a,b,mask):
    a=np.asarray(a)[mask].astype(float);b=np.asarray(b)[mask].astype(float)
    a-=a.mean();b-=b.mean();return float(a@b/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
