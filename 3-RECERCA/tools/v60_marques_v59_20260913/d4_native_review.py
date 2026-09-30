from common60 import *
import tifffile as tf
from PIL import Image,ImageCms,ImageDraw
claim();old4=tf.imread(O/'V59_clean_native.tif');new4=tf.imread(O/'V60_native.tif');assert old4.shape==new4.shape==(7506,10551,4);alpha_diff=int(abs(old4[...,3].astype('int32')-new4[...,3].astype('int32')).max());old=old4[...,:3];new=new4[...,:3];prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'))
def im(a):return ImageCms.profileToProfile(Image.fromarray((a.astype('uint32')*255//65535).astype('uint8')),prof,ImageCms.createProfile('sRGB'),outputMode='RGB')
im(new[::4,::4]).save(O/'vistes/V60_llenc_quart.png');im(new[3077:4477,4677:6077]).save(O/'vistes/V60_luna_1a1.png');can=Image.new('RGB',(1800,1000),(25,25,25));d=ImageDraw.Draw(can)
for j,(name,a) in enumerate([('V59',old),('V60',new)]):
 for k,(label,bb) in enumerate([('North limb',(5150,3077,5600,3527)),('West / blue',(4750,3430,5200,3880)),('South',(5150,4177,5600,4627)),('East',(5750,3530,6200,3980))]):
  v=im(a[bb[1]:bb[3],bb[0]:bb[2]]);can.paste(v,(k*450,j*500+30));d.text((k*450+4,j*500+5),name+' '+label,fill='white')
can.save(O/'vistes/D4_native_limbs_1a1.png')
dif=abs(old.astype('int32')-new.astype('int32'));roi=dif[2777:4777,4377:6377].copy();dif[2777:4777,4377:6377]=0;outside=int(dif.max());del dif
arr=new[2777:4777,4377:6377];rgb=np.stack([np.load(O/'arrays'/f'L29_C{c}_roi.npy') for c in range(3)],-1);mask=np.load(O/'arrays/B4_L29_mask.npy');full=mask==65535;dm=abs(arr.astype('int32')-rgb.astype('int32'))[full]
marks={}
for n in ['verd','lila','blau']:
 xy=np.load(O/'arrays'/f'mark_{n}_1_xy.npy');dd=roi[xy[:,1]-2777,xy[:,0]-4377];marks[n]={'max_change_DN16':int(dd.max()),'mean_abs_change_DN16':float(dd.mean())}
rep={'outside_2000_ROI_max_DN16':outside,'native_composite_alpha_max_change_DN16':alpha_diff,'opaque_lunar_native_vs_unchanged_RGB_max_DN16':int(dm.max()),'opaque_lunar_count':int(full.sum()),'marked_region_changes':marks,'preview':'Native recomposition; true 1:1 pixels for limb panels','model_vs_native_max_DN16':float(abs(arr.astype(float)-np.load(O/'arrays/C2_combined_candidate_model.npy')*65535).max())};assert outside<=3 and dm.max()<=3
save('D4_native_review.json',rep);print(rep)
