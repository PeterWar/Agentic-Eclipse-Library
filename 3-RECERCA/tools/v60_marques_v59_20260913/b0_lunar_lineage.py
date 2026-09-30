from common60 import *
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
claim()
items=[('V53',R/'output/earthshine_v54_detail_20260913/arrays/V53_moon_rgb.npy'),('V54',R/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy'),('V55',R/'output/earthshine_max_detail_20260913/arrays/D10_candidate_rgb.npy'),('V56',R/'output/earthshine_v56_three_routes_20260913/arrays/R8_candidate_rgb.npy'),('pre Camera Raw',R/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy')]
can=Image.new('RGB',(1200,1000),(25,25,25));d=ImageDraw.Draw(can);rows=[]
for k,(n,p) in enumerate(items):
 a=np.load(p);g=a.astype('float64').mean(-1);hp=g-gaussian_filter(g,10);strip=hp[640:760,180:780];scale=1200 if g.max()>100 else .02
 v=np.clip(.5+strip/scale,0,1);im=Image.fromarray(np.uint8(v*255)).convert('RGB').resize((1200,180));can.paste(im,(0,k*200+20));d.text((4,k*200+3),n,fill='white')
 rows.append({'stage':n,'shape':a.shape,'range':[float(a.min()),float(a.max())],'seam_at_y700':np.quantile(abs(hp[699:702,260:690]),[.5,.9,.99]).tolist()})
can.save(O/'vistes/B0_lunar_lineage_highpass.png');save('B0_lunar_lineage.json',rows);print(rows)
