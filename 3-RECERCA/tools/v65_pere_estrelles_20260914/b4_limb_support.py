from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';V=O/'vistes';marks=json.loads((O/'A3_marks.json').read_text());raw=np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1)/65535;a=np.load(A/'L3_C-1.npy')/65535;m=np.load(A/'L3_C-2.npy')/65535;la=np.load(A/'L30_C-1.npy')/65535;lm=np.load(A/'L30_C-2.npy')/65535;final=tf.imread(O/'A2_clean_ROI.tif')/65535;rows=[]
for r in marks[6:]:
 x0,y0,x1,y1=r['bbox'];pad=7;x0-=pad;y0-=pad;x1+=pad;y1+=pad;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];f=final[sl];channels=[('base R',raw[...,0]),('base alpha',a),('base mask',m),('Moon alpha',la),('Moon mask',lm),('composite alpha',final[...,3])];w=x1-x0;h=y1-y0;scale=9;pan=Image.new('RGB',(w*scale*3,(h*scale+25)*2));draw=ImageDraw.Draw(pan)
 for j,(n,z) in enumerate(channels):im=Image.fromarray(np.uint8(np.clip(z[sl],0,1)*255)).convert('RGB').resize((w*scale,h*scale),Image.Resampling.NEAREST);pan.paste(im,((j%3)*w*scale,(j//3)*(h*scale+25)+25));draw.text(((j%3)*w*scale+4,(j//3)*(h*scale+25)+5),n,fill='white')
 pan.save(V/f'B4_black{r["index"]}.png');rows.append(dict(mark=r['index'],visible_zero_RGB=int(((raw[sl].max(-1)==0)&(m[sl]*a[sl]>0)&(lm[sl]*la[sl]<1)).sum()),partial_alpha=int(((f[...,3]>0)&(f[...,3]<1)).sum()),base_alpha_values=np.unique(a[sl]).tolist(),base_mask_partial=int(((m[sl]>0)&(m[sl]<1)).sum())))
(O/'B4_limb_support.json').write_text(json.dumps(rows,indent=2));print(rows)
