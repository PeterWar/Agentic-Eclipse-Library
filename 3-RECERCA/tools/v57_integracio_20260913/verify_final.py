from pathlib import Path
import json,hashlib,io
import numpy as np,tifffile as tf
from PIL import Image,ImageCms
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v57_integracio_20260913'
gate=(O/'D1_photoshop_gate.txt').read_text().strip();assert gate=='OBRE 10551 px x 7506 px · 35 capes',gate
ref=tf.imread(O/'V57_noSolar_native.tif');a=tf.imread(O/'V57_final_readback.tif')
assert a.dtype==ref.dtype==np.uint16 and a.shape==ref.shape==(7506,10551,3)
mx=0;changed=0
for y in range(len(a)):
 d=np.abs(a[y].astype('int32')-ref[y].astype('int32'));mx=max(mx,int(d.max()));changed+=int(np.any(d,axis=1).sum())
assert mx==0,(mx,changed)
with tf.TiffFile(O/'V57_final_readback.tif') as t:icc=t.pages[0].tags[34675].value
for name,arr,size in [('V57_final_full.png',a,(1583,1126)),('V57_final_moon_1a1.png',a[3077:4477,4677:6077],None)]:
 im=Image.fromarray((arr.astype('uint32')*255//65535).astype('uint8'))
 if size:im.thumbnail(size,Image.Resampling.LANCZOS)
 im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB');im.save(O/'vistes'/name)
sources=json.loads((O/'A0_sources.json').read_text());verified=[]
for label,src in sources.items():
 with open(src['path'],'rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==src['sha256'];verified.append(dict(label=label,path=src['path'],sha256=sha,exact=True))
rep=dict(PASS=True,Photoshop=gate,readback_max_DN16=mx,changed_pixels=changed,sources_unchanged=verified,
 independent_reader='ImageMagick identify PSB 10551x7506 16-bit',
 ICC_profile='Adobe RGB (1998); display PNGs converted to sRGB',
 limitations=['Thin exterior lunar rim is still accentuated by the inherited V42 filter stack. No new limb remedy applied.','No new resolution or DHS equivalence claim.'])
(O/'D2_final_QA.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2));print(json.dumps(rep,ensure_ascii=False),flush=True)
