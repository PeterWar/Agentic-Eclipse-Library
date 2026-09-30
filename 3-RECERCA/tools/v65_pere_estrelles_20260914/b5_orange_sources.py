from pathlib import Path
import numpy as np,json
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913/arrays';V=O/'vistes';icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
x0,y0,x1,y1=5245,3285,5320,3365;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];pan=Image.new('RGB',((x1-x0)*6*4,((y1-y0)*6+25)*2));draw=ImageDraw.Draw(pan)
for j in range(7):
 raw=np.stack([np.load(P/f'V57_L{j:02d}_C{c}.npy')[sl] for c in range(3)],-1)/65535;pan.paste(view(raw).resize(((x1-x0)*6,(y1-y0)*6),Image.Resampling.NEAREST),((j%4)*(x1-x0)*6,(j//4)*((y1-y0)*6+25)+25));draw.text(((j%4)*(x1-x0)*6+4,(j//4)*((y1-y0)*6+25)+5),f'Original {12-j}',fill='white')
pan.save(V/'B5_original_top_colour.png')
