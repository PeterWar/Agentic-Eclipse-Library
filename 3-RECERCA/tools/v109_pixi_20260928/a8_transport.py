"""Transport a measured native operator delta to the exact manual Pixi composite.

The unknown residual between Pixi's baked base244 and native A is retained.
No source image is replaced by a reconstruction. Local manual retouch is protected.
"""
from pathlib import Path
import sys,json,io
import numpy as np,tifffile,cv2
from PIL import Image,ImageCms
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'4-RESULTATS/v109_pixi_20260928'
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v71_marques_v69_20260916'))
from psb69 import PSB
P=np.load(O/'entrades/PIXI_net.npy',mmap_mode='r')
A=tifffile.memmap(O/'entrades/Artefactes_sense307_natiu.tif')
Q=tifffile.memmap(O/'cel_retirat_natiu/visible_complet.tif')
assert P.shape==A.shape==Q.shape
ps=PSB(str(O/'entrades/pixi_capes.psb'));box=(0,0,ps.width,ps.height)
alpha=ps.channel_box(308,-1,box);mask=ps.channel_box(308,-2,box,fill=65535)
assert ps.layer(308)['opacity']==120 and ps.layer(308)['blend']=='NORMAL'
local=mask>3478; np.save(O/'entrades/retoc_local_mask.npy',local)
eff=(alpha.astype(np.float32)/65535)*(mask.astype(np.float32)/65535)*(120/255)
out=np.lib.format.open_memmap(O/'V109_candidat_rgb.npy',mode='w+',dtype=np.uint16,shape=P.shape)
dm=np.lib.format.open_memmap(O/'correccio_mask.npy',mode='w+',dtype=bool,shape=P.shape[:2])
report=dict(formula='q(P + (1-opacity308*alpha308*mask308)*(Q-A)); local manual support protected exactly',
            P='PIXI_net',A='Artefactes_sense307 native',Q='native noCEL same knee',
            changed=0,protected_local_pixels=int(local.sum()),raw_delta_local_pixels=0,raw_delta_local_maxDN=0,
            clipping_low=0,clipping_high=0,max_delta_DN=0,quantization='32768 intervals')
for y in range(0,len(P),128):
 s=slice(y,min(y+128,len(P)));b=P[s].astype(np.float64)
 d=(Q[s].astype(np.float64)-A[s])*(1-eff[s][...,None])
 ll=local[s];report['raw_delta_local_pixels']+=int(np.any(d[ll]!=0,axis=-1).sum())
 if ll.any():report['raw_delta_local_maxDN']=max(report['raw_delta_local_maxDN'],float(np.abs(d[ll]).max()))
 d[ll]=0;u=b+d
 report['clipping_low']+=int((u<0).sum());report['clipping_high']+=int((u>65535).sum())
 v=np.round(np.round(np.clip(u,0,65535)*32768/65535)*65535/32768).astype(np.uint16)
 out[s]=v;dm[s]=np.any(v!=P[s],axis=-1);report['changed']+=int(dm[s].sum())
 report['max_delta_DN']=max(report['max_delta_DN'],int(np.abs(v.astype(np.int32)-P[s]).max()))
assert np.array_equal(out[local],P[local]);out.flush();dm.flush()
report['local_exact']=True
(O/'TRANSPORT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
icc=(O/'entrades/AdobeRGB.icc').read_bytes()
tr=ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),'RGB','RGB')
def save(a,name,width=2000):
 if width:a=cv2.resize(a,(width,round(a.shape[0]*width/a.shape[1])),interpolation=cv2.INTER_AREA)
 ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a/257,0,255))),tr).save(O/'vistes'/name)
save(out,'V109_candidat.png');save(out[2850:4500,4400:6200],'V109_interior_1a1.png',None)
save(P[2850:4500,4400:6200],'PIXI_interior_1a1.png',None)
save(out[4250:4650,5600:6900],'V109_petites_1a1.png',None)
