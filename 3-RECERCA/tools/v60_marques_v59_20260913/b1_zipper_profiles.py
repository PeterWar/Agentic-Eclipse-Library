from common60 import *
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw
claim()
items=[('V59 Moon',R/'output/earthshine_v56_three_routes_20260913/arrays/R8_candidate_rgb.npy'),('V49 input',R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_ch1_roi.npy'),('preCR',R/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy'),('V45 live',R/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy'),('V45 source',R/'research/tools/v45_earthshine_20260910/cau/combined_reference.npy'),('Sony reference',R/'output/earthshine_detail_20260911/B2_sony_reference.npz')]
can=Image.new('RGB',(1000,1200),(25,25,25));d=ImageDraw.Draw(can);out={}
for k,(n,p) in enumerate(items):
 a=np.load(p);a=a['reference'] if isinstance(a,np.lib.npyio.NpzFile) else a;g=a.astype(float);g=g.mean(-1) if g.ndim==3 else g
 g=np.nan_to_num(g);h=g-gaussian_filter1d(g,2,axis=0);crop=h[660:740,245:745];scale=max(1e-7,float(np.quantile(abs(crop),.99)))
 im=Image.fromarray(np.uint8(np.clip(.5+.45*crop/scale,0,1)*255)).convert('RGB').resize((1000,160));can.paste(im,(0,k*200+25));d.text((3,k*200+5),n+' transverse residual (sigma2)',fill='white')
 q=np.mean(h[650:750,270:680]**2,axis=1)**.5
 out[n]={'rms_rows_650_750':q.tolist(),'peakrows':(np.argsort(q)[-12:]+650).tolist(),'scale':scale}
can.save(O/'vistes/B1_transverse_zipper.png');save('B1_transverse_profiles.json',out);print({n:v['peakrows'] for n,v in out.items()})
