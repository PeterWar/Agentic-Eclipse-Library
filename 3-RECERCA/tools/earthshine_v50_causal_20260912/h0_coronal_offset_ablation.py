"""Exact registered-source ablation of coronal C03 additive offsets.
The native A0 sampler applies b and phi AFTER quincunx interpolation. Therefore
subtracting b*field from its registered g exactly removes this calibration term
up to float32 storage, with geometry, variance, quality and all weights frozen.
No fitted lunar plane, radial fade, radius or image mask enters the correction.
"""
from common50 import *
import cv2,time,gc
SRC=ROOT/'output/earthshine_native_psf_20260911'
frames=[m for m in json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'] if m['tren']=='vixen']
inputs={m['stem']:m for m in json.loads((SRC/'A2_all_native.json').read_text())['frames']}
meta=json.loads((ROOT/'research/tools/v36_20260908/cau/vixen_meta.json').read_text())
phis=np.load(ROOT/'research/tools/v36_20260908/cau/vixen_G_phi.npy',mmap_mode='r')
old=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');weights=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
dst=OUT/'H0_G_without_coronal_offset.npy';assert not dst.exists()
new=np.lib.format.open_memmap(dst,mode='w+',dtype=np.float32,shape=old.shape)
yy,xx=np.mgrid[Y0:Y0+N,X0:X0+N].astype(np.float32);r=np.hypot(xx-X0-CX,yy-Y0-CY)
den=np.zeros((N,N));num=den.copy();records=[]
for i,m in enumerate(frames):
 t=time.time();stem=m['stem'];j=next(j for j,a in enumerate(meta['frames']) if a['name']==m['nom']);row=meta['frames'][j];sx,sy=inputs[stem]['shift'];b=row['offset_RGB'][1]
 phi=cv2.resize(np.asarray(phis[j],np.float32),(10548,7504),interpolation=cv2.INTER_LINEAR)
 # All queried ROI coordinates are far inside the non-padded array.
 field=np.exp(-cv2.remap(phi,xx-sx,yy-sy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));delta=b*field
 new[i]=(old[i].astype(float)-delta).astype(np.float32);w=weights[i].astype(float);den+=w;num+=w*delta
 regions={}
 for lo,hi in [(0,350),(415,435),(435,449),(449,454)]:
  use=(r>=lo)&(r<hi)&(w>0)
  regions[f'{lo}_{hi}']=dict(n=int(use.sum()),before=np.percentile(old[i][use],[5,50,95]).tolist(),after=np.percentile(new[i][use],[5,50,95]).tolist(),removed=np.percentile(delta[use],[5,50,95]).tolist()) if use.any() else dict(n=0)
 records.append(dict(stem=stem,exposure=m['exp'],time=m['t_mid_C2'],offset=b,field_range=np.percentile(field[r<460],[0,50,100]).tolist(),regions=regions))
 if i%10==0:print(i,stem,'DONE',round(time.time()-t,2),flush=True)
 del phi,field,delta;gc.collect()
new.flush();np.save(OUT/'H0_weighted_coronal_offset.npy',num/np.maximum(den,1e-30))
save('H0_coronal_offset_ablation.json',dict(method=__doc__,frames=records,weights='Frozen old source W; no noise or physical zero-level claim',source_sha256=sha(SRC/'compositor_cache/G.npy'),status='Cause ablation, not qualified lunar recovery'))
print('DONE',len(frames),flush=True)
