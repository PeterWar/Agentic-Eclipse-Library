from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageDraw,ImageCms
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';new=tf.imread(O/'D11_candidate.tif');ex=tf.imread(O/'S24_expected.tif');old=tf.imread(O/'A2_clean_full.tif');dd=np.abs(new.astype('int32')-ex);support=np.any(ex!=old,-1);rep=dict(maximum_DN16=int(dd.max()),alpha_max_DN16=int(dd[...,3].max()),outside_edits_max_DN16=int(np.abs(new.astype('int32')-old)[~support].max()),above4=int(np.count_nonzero(dd>4)),changed_pixels=int(np.any(new!=old,-1).sum()));print(rep,flush=True)
# Direct protection of the opaque photographic bead/prominence signal contributed by Pere's own added layer96.
photo=tf.imread(O/'A2_L96_masked.tif');roi=np.s_[2777:4777,4377:6377];core=photo[...,3]==65535;delta=np.abs(new[roi].astype('int32')-old[roi]);rep['Pere_photo96_opaque_core_pixels']=int(core.sum());rep['Pere_photo96_opaque_core_max_DN16']=int(delta[core].max()) if core.any() else None
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(q):
 z=q.astype(float)/65535;rgb=z[...,:3]+.12*(1-z[...,3:]);return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5)),icc,srgb,outputMode='RGB')
ma=np.load(O/'arrays/L30_C-2.npy');ys,xs=np.nonzero(ma>32767);cx=xs.mean()+4377;cy=ys.mean()+2777;radius=np.sqrt(len(xs)/np.pi);pan=Image.new('RGB',(1200,4*225));draw=ImageDraw.Draw(pan)
for i,th in enumerate(np.arange(12)*2*np.pi/12):
 x,y=int(round(cx+radius*np.cos(th))),int(round(cy+radius*np.sin(th)));sl=np.s_[y-50:y+50,x-50:x+50];xx=(i%3)*400;yy=(i//3)*225;pan.paste(view(old[sl]).resize((200,200),Image.Resampling.NEAREST),(xx,yy+25));pan.paste(view(new[sl]).resize((200,200),Image.Resampling.NEAREST),(xx+200,yy+25));draw.text((xx+4,yy+5),f'{i*30} graus: Pere | V65',fill='white')
pan.save(O/'vistes/D12_contorn_360.png')
marks=json.loads((O/'A3_marks.json').read_text());print('marks schema',type(marks),flush=True)
for tag,box in [('perles',(4870,3430,5025,3705)),('superior',(5235,3260,5335,3390)),('inferior',(5060,4090,5330,4260))]:
 x0,y0,x1,y1=box;sl=np.s_[y0:y1,x0:x1];w=x1-x0;h=y1-y0;pan=Image.new('RGB',(w*6,h*3+30));draw=ImageDraw.Draw(pan)
 for i,(label,q) in enumerate([('Pere',old),('V65',new)]):pan.paste(view(q[sl]).resize((w*3,h*3),Image.Resampling.NEAREST),(i*w*3,30));draw.text((i*w*3+5,7),label,fill='white')
 pan.save(O/f'vistes/D12_{tag}.png')
rep['PASS']=rep['maximum_DN16']<=4 and rep['outside_edits_max_DN16']<=4 and rep['alpha_max_DN16']==0 and rep['Pere_photo96_opaque_core_max_DN16'] in [0,1,2,3,4,None];(O/'D12_native_candidate_check.json').write_text(json.dumps(rep,indent=2));print(rep,flush=True)
