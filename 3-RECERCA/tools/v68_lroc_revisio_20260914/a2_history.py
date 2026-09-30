from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/v68_lroc_revisio_20260914';P=R/'output/v68_artefactes_20260914';C=R/'research/tools/earthshine_v50_temporal_20260912/cau'
paths={'V45 legacy abans CR':R/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy','V48 font abans CR':R/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy','V49 abans nou revelat':R/'output/earthshine_v49_pere_reveal_20260912/A0_previous_moon_RGB16.npy','V49 revelat Pere':R/'output/earthshine_v49_pere_reveal_20260912/A0_Pere_moon_RGB16.npy','V53 resta de vel':C/'lun_rgb_vel_u16.npy','V53 capa exacta':R/'output/earthshine_v54_detail_20260913/arrays/V53_moon_rgb.npy'}
s={k:np.load(p).astype(float).mean(-1) for k,p in paths.items()};s['V68']=np.load(P/'arrays/B10_photo_pilot.npz')['candidate'].mean(-1);s['LROC V58']=np.load(O/'arrays/L62_exact_psb.npz')['rgb'].mean(-1)
s['Sony font']=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];s['Vixen font']=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean']
y,x=np.mgrid[:1400,:1400];r=np.hypot(x-699.568,y-699.648);ss=np.s_[3910-3077:4180-3077,5140-4678:5470-4678];outer=(x>=460)&(x<790)&(y>=833)&(y<1103)&(r<420);marked=(x>=550)&(x<723)&(y>=902)&(y<1048);controls=outer&~marked
rows=[]
for mode in ['wide','band12_64','band64_256']:
 pan=Image.new('RGB',(660*4,572*3),'#151515');dr=ImageDraw.Draw(pan)
 for j,(name,q) in enumerate(s.items()):
  if mode=='band12_64':a=gaussian_filter(q,2)-gaussian_filter(q,16)
  elif mode=='band64_256':a=gaussian_filter(q,16)-gaussian_filter(q,64)
  else:a=q
  lo,hi=np.percentile(a[outer],[2,98]);im=Image.fromarray(np.uint8(np.clip((a[ss]-lo)/(hi-lo),0,1)*255+.5)).convert('RGB');xx=j%4*660;yy=j//4*572;pan.paste(im.resize((660,540),Image.Resampling.NEAREST),(xx,yy+32));dr.text((xx+8,yy+8),name+' | '+mode,fill='white')
  rows.append(dict(source=name,mode=mode,median_mark=float(np.median(a[marked])),median_control=float(np.median(a[controls])),contrast_in_control_sigma=float((np.median(a[marked])-np.median(a[controls]))/np.std(a[controls]))))
 pan.save(O/'vistes'/f'A2_history_{mode}.png')
for a,b in [('V49 revelat Pere','V53 resta de vel'),('V53 resta de vel','V53 capa exacta'),('V53 capa exacta','V68')]:
 d=s[b]-s[a];print(a,'->',b,'mark change',np.percentile(d[marked],[0,50,100]).tolist(),'whole',np.percentile(d[r<430],[0,50,100]).tolist())
(O/'A2_history.json').write_text(json.dumps(dict(paths={k:str(v) for k,v in paths.items()},rows=rows),ensure_ascii=False,indent=2)+'\n');print('HISTORY DONE')
