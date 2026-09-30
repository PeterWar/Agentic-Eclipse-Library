from pathlib import Path
import numpy as np,tifffile as tf,json
from PIL import Image,ImageCms,ImageDraw
from scipy.ndimage import map_coordinates,gaussian_filter1d
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913'
icc=ImageCms.ImageCmsProfile(str(P/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def cv(a):
 return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
items=[]
for tag in ['base','base_moon','base_moon_plus_41','base_moon_plus_42','base_moon_plus_43','base_moon_plus_44','base_moon_plus_45','base_moon_plus_46','base_moon_plus_47','default']:
 a=tf.imread(O/f'A1_{tag}.tif').astype('float32')/65535;items.append((tag,a))
for tag,bb in [('top',(5245,3297,5310,3351)),('NW',(4970,3460,5050,3550)),('west',(4870,3720,4970,3970)),('SE',(5770,3910,5820,3990)),('bottom',(5080,4110,5320,4230))]:
 x0,y0,x1,y1=bb;k=3 if tag!='west' else 2;w=(x1-x0)*k;h=(y1-y0)*k;pan=Image.new('RGB',(w*5,(h+24)*2),(20,20,20));dr=ImageDraw.Draw(pan)
 for i,(label,a) in enumerate(items):
  im=cv(a[y0-2777:y1-2777,x0-4377:x1-4377,:3]);pan.paste(im.resize((w,h),Image.Resampling.NEAREST),(i%5*w,i//5*(h+24)+24));dr.text((i%5*w+3,i//5*(h+24)+5),label,fill='white')
 pan.save(O/'vistes'/f'A2_{tag}_stack.png')
f4=gaussian_filter1d(np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');th=np.linspace(0,2*np.pi,1440,endpoint=False);d=np.arange(-8,16,.25);rr=f4[:,None]+d;xx=5376.568111973117+np.cos(th[:,None])*rr-4377;yy=3776.647534140857+np.sin(th[:,None])*rr-2777
all_profiles={}
for tag,a in items:
 p=np.stack([map_coordinates(a[...,c],[yy,xx],order=1) for c in range(3)],-1);all_profiles[tag]=p
np.savez(O/'arrays/A2_polar.npz',theta=th,d=d,**all_profiles)
pan=Image.new('RGB',(1440,125*len(items)),(20,20,20));dr=ImageDraw.Draw(pan)
for i,(tag,_) in enumerate(items):
 p=all_profiles[tag];pan.paste(cv(np.transpose(p,(1,0,2))),(0,i*125+24));dr.text((4,i*125+4),tag+' | radial -8 to +16 px | angle 0 to 360',fill='white')
pan.save(O/'vistes/A2_all_limb_polar.png')
print('VIEWS READY',flush=True)
