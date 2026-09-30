from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';old=tf.imread(O/'A2_clean_ROI.tif');new=tf.imread(O/'D2_pilot_native.tif');p=np.load(A/'B10_photo_pilot.npz');delta=np.zeros((2000,2000));delta[300:1700,301:1701]=p['delta'];coef=np.ones((2000,2000))
for id in [30,76,96]:
 al=np.load(A/f'L{id}_C-1.npy').astype(float)/65535*np.load(A/f'L{id}_C-2.npy')/65535
 if id==96:al*=227/255
 coef*=al if id==30 else 1-al
# Native Photoshop TIFF declares ASSOCALPHA. Compare premultiplied colour deltas.
with tf.TiffFile(O/'D2_pilot_native.tif') as tt: assert int(tt.pages[0].extrasamples[0])==1
expected=old[...,:3].astype(float)+(np.load(A/'B8_colour_normal.npy')-np.load(A/'B8_old.npy'))*new[...,3,None]+delta[...,None]*coef[...,None];err=abs(new[...,:3]-expected);diff=new[...,:3].astype(int)-old[...,:3].astype(int)
# This numerical compositor is an approximate independent implementation; exact native readback is a separate final gate.
report={'approximate_differential_max_DN16':float(err.max()),'approximate_p99_DN16':float(np.percentile(err,99)),'changed_pixels':int(np.any(diff!=0,-1).sum()),'alpha_max_change_DN16':int(abs(new[...,3].astype(int)-old[...,3].astype(int)).max()),'injections_all_pass':json.loads((O/'B13_injections.json').read_text())['all_pass'],'photographic_claims_lost':len(json.loads((O/'B11_exact_retention.json').read_text())['lost_triples'])}
regions={'top':(5305,3275,5520,3370),'SW':(4940,3980,5070,4100),'east':(5760,3910,5840,4000),'inside':(5170,3910,5470,4170),'whole':(4780,3180,5980,4380)}
profile=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
for name,(x0,y0,x1,y1) in regions.items():
 ss=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];scale=1 if name=='whole' else 3;ww=(x1-x0)*scale;hh=(y1-y0)*scale;can=Image.new('RGB',(ww*2,hh+30),'#151515');dr=ImageDraw.Draw(can)
 for j,arr in enumerate([old,new]):
  q=arr[ss][...,:3].astype(float)/65535
  if name=='inside':q*=4
  im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(q,0,1)*255+.5)),profile,srgb,outputMode='RGB');can.paste(im.resize((ww,hh),Image.Resampling.NEAREST),(j*ww,30));dr.text((j*ww+8,8),['V67','V68 pilot | native Photoshop'][j],fill='white')
 can.save(V/f'D3_{name}.png');report[name]={'difference_minmax': [int(diff[ss].min()),int(diff[ss].max())],'expected_error_max':float(err[ss].max())}
report['PASS']=report['injections_all_pass'] and report['photographic_claims_lost']==0 and report['approximate_differential_max_DN16']<=10 and report['alpha_max_change_DN16']==0
(O/'D3_pilot_qa.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
