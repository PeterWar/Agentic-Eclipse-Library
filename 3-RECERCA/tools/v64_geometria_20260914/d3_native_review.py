from pathlib import Path
import numpy as np,tifffile as tf,json
from PIL import Image,ImageCms,ImageDraw
from scipy.ndimage import map_coordinates,gaussian_filter1d
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays';V=O/'vistes'
before=tf.imread(O/'A0_clean.tif').astype(float)/65535;after=tf.imread(O/'D1_candidate_with83.tif').astype(float)/65535
mask=np.load(A/'L76_C-2.npy');delta=abs(after[...,:3]-before[...,:3])*65535;outside=mask==0
rep=dict(outside_user_selection_max_DN16=float(delta[outside].max()),changed_RGB_samples=int(np.count_nonzero(delta)),new_nonopaque_pixels=int(np.count_nonzero(after[...,3]<1)) if after.shape[-1]==4 else 0)
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a[...,:3],0,1)*255+.5)),icc,srgb,outputMode='RGB')
can=Image.new('RGB',(2000,1024));dr=ImageDraw.Draw(can)
for j,(name,a) in enumerate([('V63 Pere',before),('Native V64 candidate',after)]):can.paste(view(a).resize((1000,1000),Image.Resampling.LANCZOS),(j*1000,24));dr.text((j*1000+5,5),name,fill='white')
can.save(V/'D3_whole_Moon.png')
f4=gaussian_filter1d(np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');th=np.arange(1440)*np.pi/720;drad=np.arange(-10,18,.25);r=f4[:,None]+drad;xx=5376.568111973117+np.cos(th[:,None])*r-4377;yy=3776.647534140857+np.sin(th[:,None])*r-2777
can=Image.new('RGB',(1440,274));dr=ImageDraw.Draw(can)
for j,(name,a) in enumerate([('V63 Pere',before),('Native V64 candidate',after)]):
    pol=np.stack([map_coordinates(a[...,c],[yy,xx],order=1) for c in range(3)],-1);can.paste(view(pol.transpose(1,0,2)),(0,j*137+25));dr.text((5,j*137+5),name+' 360 degrees',fill='white')
can.save(V/'D3_whole_limb_polar.png');(O/'D3_native_review.json').write_text(json.dumps(rep,indent=2)+'\n');print(rep,flush=True)
