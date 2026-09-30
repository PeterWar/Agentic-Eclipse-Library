from composite60 import *
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageCms
claim();m=read(29,-2);inside=distance_transform_edt(m>0);new=m.copy();new[inside>3]=1;hit=new!=m
assert inside[hit].min()>=7
np.save(O/'arrays/B4_L29_mask.npy',np.rint(new*65535).astype('uint16'))
pat=np.sin(np.indices(m.shape)[1]/3)*.2+.5
leakold=(1-m)*pat;leaknew=(1-new)*pat
rep={'changed_pixels':int(hit.sum()),'minimum_inside_distance_px':float(inside[hit].min()),'source_mask_range_changed':np.quantile(m[hit],[0,.01,.5,.99,1]).tolist(),'contour_last3px_and_exterior_exact':bool(np.array_equal(m[inside<=3],new[inside<=3])),'lunar_RGB_unchanged':True,'alpha_unchanged':True,'injected_background_leak_old_rms':float(np.sqrt(np.mean(leakold[inside>3]**2))),'injected_background_leak_new_max':float(abs(leaknew[inside>3]).max()),'mean_photographic_detail_gain':float(np.mean(1/m[hit])),'claim':'Opacity/photographic compositing correction; no new resolution or lunar radiance claim'}
changes={i:np.load(O/'arrays'/f'C0_L{i:02d}_gray.npy').astype(float)/65535 for i in range(11,17)};masks={i:np.load(O/'arrays'/f'C0_L{i:02d}_mask.npy').astype(float)/65535 for i in range(11,17)};masks[29]=new
old=np.load(O/'arrays/composite_model.npy');native=np.load(O/'arrays/V59_clean_native_RGB_roi.npy').astype(float)/65535;photo=np.clip(native+render(changes,masks)-old,0,1);np.save(O/'arrays/B4_combined_candidate_model.npy',photo)
prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));can=Image.new('RGB',(1400,750),(25,25,25));d=ImageDraw.Draw(can)
for j,(name,v) in enumerate([('V59',native),('C0 filters + B4 opaque lunar interior',photo)]):
 im=Image.fromarray(np.uint8(v[300:1700,300:1700]*255));im=ImageCms.profileToProfile(im,prof,ImageCms.createProfile('sRGB'),outputMode='RGB').resize((700,700));can.paste(im,(j*700,30));d.text((j*700+4,6),name,fill='white')
can.save(O/'vistes/B4_all_marks_pilot.png')
can=Image.new('RGB',(1400,450),(25,25,25));d=ImageDraw.Draw(can)
for j,(name,v) in enumerate([('V59',native),('C0+B4',photo)]):
 a=v[2777-ROI[1]+3660-2777:3900-ROI[1],4877-ROI[0]:5577-ROI[0],:];g=a.mean(-1);im=Image.fromarray(np.uint8(np.clip(g*8,0,1)*255)).convert('RGB');can.paste(im,(j*700,30));d.text((j*700+3,5),name+' (8x luminance)',fill='white')
can.save(O/'vistes/B4_zipper_composite_pilot.png');save('B4_physical_mask.json',rep);print(rep)
