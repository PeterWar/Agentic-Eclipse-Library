from composite60 import *
from scipy.ndimage import gaussian_filter,maximum_filter,distance_transform_edt
from PIL import Image,ImageCms,ImageDraw
claim();moon=read(29,-2);dist=distance_transform_edt(moon==0);wl=np.clip((dist-4)/8,0,1);wl=wl*wl*(3-2*wl)
red=np.load(PREV/'arrays/L10_C0_roi.npy')/65535;green=np.load(PREV/'arrays/L10_G_roi.npy')/65535;prom=red-green>.25;pm=np.clip(gaussian_filter(maximum_filter(prom.astype('float32'),size=9),2),0,1)
w=np.load(PREV/'prepared_layers/RHEF_protection_weight.npy');assert np.max(abs(w-wl*(1-pm)))<1e-7
changes={};masks={};base=read(9,-2);rep={}
for i in range(11,17):
 f=read(i,1);valid=(w>=1-1e-6)&(read(i,-2)>.999)&(read(i,-1)>.999);den=gaussian_filter(valid.astype(float),16);bg=gaussian_filter(f*valid,16)/np.maximum(den,1e-30)
 hit=(wl<1)&(base>0);new=f.copy();new[hit]=wl[hit]*f[hit]+(1-wl[hit])*bg[hit];m=read(i,-2);m[hit]=(base*(1-pm))[hit];changes[i]=new;masks[i]=m
 np.save(O/'arrays'/f'C2_L{i:02d}_gray.npy',np.rint(new*65535).astype('uint16'));np.save(O/'arrays'/f'C2_L{i:02d}_mask.npy',np.rint(m*65535).astype('uint16'))
 rep[str(i)]={'changed_region':int(hit.sum()),'outside_exact':bool(np.array_equal(new[~hit],f[~hit])),'prominence_mask_preserved':True}
masks[29]=np.load(O/'arrays/B4_L29_mask.npy')/65535;old=np.load(O/'arrays/composite_model.npy');native=np.load(O/'arrays/V59_clean_native_RGB_roi.npy')/65535;photo=np.clip(native+render(changes,masks)-old,0,1);np.save(O/'arrays/C2_combined_candidate_model.npy',photo);np.save(O/'arrays/C2_lunar_protection.npy',wl);np.save(O/'arrays/C2_prominence_protection.npy',pm)
prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));can=Image.new('RGB',(1400,750),(25,25,25));d=ImageDraw.Draw(can)
for j,(name,v) in enumerate([('V59',native),('C2 + B4; same prominence protection',photo)]):
 im=Image.fromarray(np.uint8(v[300:1700,300:1700]*255));im=ImageCms.profileToProfile(im,prof,ImageCms.createProfile('sRGB'),outputMode='RGB').resize((700,700));can.paste(im,(j*700,30));d.text((j*700+4,6),name,fill='white')
can.save(O/'vistes/C2_all_marks_pilot.png');save('C2_keep_prominences.json',rep);print('C2 READY')
