"""Diagnostic only. Cross-epoch colours in rings wholly inside the lunar disc.

Avoid the global DCT of A1: its distant, bright corona contaminates deep lunar
bands. No reference photograph enters the colour estimator. Both temporal
partitions and several spatial supports must agree before spectral separation.
"""
from pathlib import Path
import json,numpy as np
from scipy.ndimage import map_coordinates,distance_transform_edt
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_SPECTRAL_BROAD_20260914'
CX=699.568111973117;CY=699.6475341408573
rr=np.arange(80.,411.,1.);th=np.arange(1440)*2*np.pi/1440
co=np.array([CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)])
f=np.fft.rfftfreq(1440)[None,:]*1440/(2*np.pi*rr[:,None])
def polar(a):
 valid=np.isfinite(a);ix=distance_transform_edt(~valid,return_distances=False,return_indices=True)
 v=map_coordinates(valid.astype(float),co,order=1,mode='constant')>.999
 # Local bilinear interpolation: outside-corona values cannot reach the disc.
 b=map_coordinates(a[tuple(ix)],co,order=1,mode='nearest')
 return b,v
def band(a,lo,hi):return np.fft.irfft(np.fft.rfft(a,axis=1)*((f>=1/hi)&(f<=1/lo)),n=1440,axis=1)
def stats(a,b,m):
 a=a[m];b=b[m];a-=a.mean(0);b-=b.mean(0)
 C=(a.T@b+b.T@a)/(2*len(a));ev,U=np.linalg.eigh(C);c=U[:,-1]/U[1,-1]
 cr=np.array([[np.corrcoef(a[:,i],b[:,j])[0,1] for j in range(3)] for i in range(3)])
 return dict(covariance=C.tolist(),eigenvalues=ev.tolist(),color=c.tolist(),correlation=cr.tolist())
groups={};supports={};m0=R/'output/earthshine_v50_causal_20260912'
for stem in ['572A2978','572A2996']:
 z=np.load(m0/f'M0_camera_{stem}.npz')['camera'];pv=[polar(z[...,c]) for c in range(3)]
 groups[stem]=np.stack([q[0] for q in pv],-1);supports[stem]=np.all([q[1] for q in pv],axis=0)
z=np.load(R/'output/earthshine_max_detail_20260913/arrays/A2_color_stacks.npz')
for part in ['fit','test','early','late']:
 pv=[polar(z[part+'_'+c]) for c in ['R','G','B']];groups[part]=np.stack([q[0] for q in pv],-1);supports[part]=np.all([q[1] for q in pv],axis=0)
rows=[]
for lo,hi in [(16,32),(32,64),(64,128),(128,256)]:
 b={k:np.stack([band(a[...,c],lo,hi) for c in range(3)],-1) for k,a in groups.items()}
 for pair in [('572A2978','572A2996'),('fit','test'),('early','late')]:
  for rlo,rhi in [(80,190),(190,330),(330,410)]:
   for parity in [0,1]:
    # Ring-local estimator: r<190 training never shares any patch pixels.
    m=(rr[:,None]>=rlo)&(rr[:,None]<rhi)&((np.arange(1440)[None,:]//120)%2==parity)&supports[pair[0]]&supports[pair[1]]
    q=dict(band=[lo,hi],pair=pair,radius=[rlo,rhi],parity=parity,**stats(b[pair[0]],b[pair[1]],m));rows.append(q)
    if parity==0:print(q['pair'],q['band'],q['radius'],'color',q['color'],'crossG',q['correlation'][1][1],flush=True)
(O/'A2_local_color.json').write_text(json.dumps(dict(method=__doc__,rows=rows,status='DIAGNOSTIC_ONLY'),indent=2)+'\n')
np.savez_compressed(O/'arrays/A2_local_polar.npz',r=rr,theta=th,**groups)
