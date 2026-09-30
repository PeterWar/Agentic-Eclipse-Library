from pathlib import Path
import numpy as np,tifffile as tf,json
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';V=O/'vistes';A=O/'arrays';marks=json.loads((O/'A3_marks.json').read_text());icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
names=['A2_c00_base','A2_c01_filters','A2_c02_Moon','A2_c03_interiors','A2_c04_copy12','A2_c05_Pere_detail'];imgs={n:tf.imread(O/(n+'.tif')) for n in names};layers={i:tf.imread(O/f'A2_L{i}_masked.tif') for i in [3,30,76,83,96]}
def rgb(a):
 q=a.astype(float)/65535
 return q[...,:3]+.12*(1-q[...,3:]) if q.shape[-1]==4 else q

def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(rgb(a),0,1)*255+.5)),icc,srgb,outputMode='RGB')
clean=tf.imread(O/'A2_clean_ROI.tif');assert np.array_equal(clean,imgs[names[-1]])
for n in ['A2_clean_full','A2_clean_ROI']:
 a=tf.imread(O/(n+'.tif'));sc=6 if 'full' in n else 2;view(a[::sc,::sc]).save(V/(n+'.png'))
rows=[]
for m in marks:
 x0,y0,x1,y1=m['bbox'];pad=14 if m['index']<7 else 8;x0-=pad;y0-=pad;x1+=pad;y1+=pad;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];k=min(6,max(2,500//max(x1-x0,y1-y0)));w=(x1-x0)*k;h=(y1-y0)*k;panel=Image.new('RGB',(w*3,(h+24)*2));draw=ImageDraw.Draw(panel);stats=[]
 for j,n in enumerate(names):
  a=imgs[n][sl];panel.paste(view(a).resize((w,h),Image.Resampling.NEAREST),((j%3)*w,(j//3)*(h+24)+24));draw.text(((j%3)*w+4,(j//3)*(h+24)+5),n[6:],fill='white')
  if j:stats.append(dict(stage=n,changed_samples=int(np.count_nonzero(imgs[n][sl][...,:3]!=imgs[names[j-1]][sl][...,:3])),max_abs_RGB_DN16=int(abs(imgs[n][sl][...,:3].astype('int32')-imgs[names[j-1]][sl][...,:3].astype('int32')).max())))
 panel.save(V/f'B1_mark_{m["index"]:02d}_cumulative.png');rows.append(dict(mark=m,changes=stats))
# Crop-independent exact native effect of each final stage.
rep=dict(marks=rows,copy12_effect_max_DN16=int(abs(imgs[names[4]].astype('int32')-imgs[names[3]].astype('int32')).max()),Pere_detail_effect_max_DN16=int(abs(imgs[names[5]].astype('int32')-imgs[names[4]].astype('int32')).max()),cumulative_reproduces_clean_exact=True)
(O/'B1_artifact_diagnostics.json').write_text(json.dumps(rep,indent=2)+'\n');print('COMPLETE',rep['copy12_effect_max_DN16'],rep['Pere_detail_effect_max_DN16'])
