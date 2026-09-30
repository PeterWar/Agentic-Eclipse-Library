from composite60 import *
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageCms,ImageDraw
claim();w=np.load(PREV/'prepared_layers/RHEF_protection_weight.npy');base=read(9,-2);changes={};masks={};rep={}
for i in range(11,17):
 f=read(i,1);valid=(w>=1-1e-6)&(read(i,-2)>.999)&(read(i,-1)>.999)
 den=gaussian_filter(valid.astype(float),16);bg=gaussian_filter(f*valid,16)/np.maximum(den,1e-30)
 hit=(w<1)&(base>0);assert den[hit].min()>0
 new=f.copy();new[hit]=w[hit]*f[hit]+(1-w[hit])*bg[hit]
 m=read(i,-2);m[hit]=base[hit];masks[i]=m;changes[i]=new
 np.save(O/'arrays'/f'C0_L{i:02d}_gray.npy',np.rint(new*65535).astype('uint16'));np.save(O/'arrays'/f'C0_L{i:02d}_mask.npy',np.rint(m*65535).astype('uint16'))
 rep[str(i)]={'edited_pixels':int(hit.sum()),'F_old':np.quantile(f[hit],[0,.5,1]).tolist(),'F_new':np.quantile(new[hit],[0,.5,1]).tolist(),'outside_exact':bool(np.array_equal(new[~hit],f[~hit]))}
new=render(changes,masks);old=np.load(O/'arrays/composite_model.npy');native=np.load(O/'arrays/V59_clean_native_RGB_roi.npy').astype(float)/65535;photo=np.clip(native+new-old,0,1);np.save(O/'arrays/C0_candidate_model.npy',photo)
prof=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));can=Image.new('RGB',(1400,750),(25,25,25));d=ImageDraw.Draw(can)
for j,(name,v) in enumerate([('V59',native),('C0 fixed DC and protected detail',photo)]):
 im=Image.fromarray(np.uint8(v[300:1700,300:1700]*255));im=ImageCms.profileToProfile(im,prof,ImageCms.createProfile('sRGB'),outputMode='RGB').resize((700,700));can.paste(im,(j*700,30));d.text((j*700+4,6),name,fill='white')
can.save(O/'vistes/C0_green_pilot.png');save('C0_boundary_pilot.json',rep);print('GREEN PILOT READY')
