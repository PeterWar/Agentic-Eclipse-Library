from pathlib import Path
import json,numpy as np,cv2
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v62_prominencies_20260913';P=R/'output/v61_interiors_limbe_20260913/arrays';A=O/'arrays'
old=json.loads((R/'output/v61_interiors_limbe_20260913/A0_sources.json').read_text())['V57']['layers'];L=[]
for i in range(7):
 rgb=np.stack([np.load(P/f'V57_L{i:02d}_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
 al=np.load(P/f'V57_L{i:02d}_C-1.npy').astype('float32')/65535;mp=P/f'V57_L{i:02d}_C-2.npy';m=np.load(mp).astype('float32')/65535 if mp.exists() else np.ones_like(al);L.append((rgb,al*m,old[i]['name']))
def comp(hidden=[]):
 a=np.zeros((2000,2000),np.float32);v=np.zeros((2000,2000,3),np.float32)
 for i,(rgb,al,n) in enumerate(L):
  if i==6 or i in hidden:continue
  # All native source layers normal.
  v=rgb*al[...,None]+v*(1-al[...,None]);a=al+a*(1-al)
 return v
p=json.loads((R/'output/v61_interiors_limbe_20260913/C2_common_rigid.json').read_text())['transform_output_dx_dy_deg'];th=np.deg2rad(p[2]);c=np.array([5361.768111973117-4377,3775.747534140857-2777]);rot=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]]);M=np.c_[rot,c+np.array(p[:2])-rot@c].astype('float32')
warp=lambda q:cv2.warpAffine(q,M,(2000,2000),flags=cv2.INTER_CUBIC)
src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB');cv=lambda a:ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255)),src,dst,outputMode='RGB')
items=[('ALL',warp(comp()))]+[(f'omit {12-i:02d}',warp(comp([i]))) for i in range(6)]+[(f'RAW layer {12-i:02d}',warp(l[0])) for i,l in enumerate(L[:5])]
for name,bb in [('top',(5250,3303,5305,3350))]:
 x0,y0,x1,y1=bb;w=x1-x0;h=y1-y0;k=4;pan=Image.new('RGB',(w*k*4,(h*k+25)*3))
 for j,(title,im) in enumerate(items):
  pan.paste(cv(im[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w*k,h*k),Image.Resampling.NEAREST),((j%4)*w*k,(j//4)*(h*k+25)+25));ImageDraw.Draw(pan).text(((j%4)*w*k+2,(j//4)*(h*k+25)+5),title,fill='white')
 pan.save(O/'vistes'/f'B4_{name}.png')
rows=[]
for i,(rgb,al,n) in enumerate(L):
 q=warp(rgb);a=warp(al);rows.append(dict(name=n,samples=[dict(x=5278,y=y,RGB=q[y-2777,5278-4377].tolist(),mask=float(a[y-2777,5278-4377])) for y in [3315,3322,3330,3335]]))
(O/'B4_inner_layers.json').write_text(json.dumps(rows,indent=2))
