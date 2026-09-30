"""DHS530 reference-only global monotone-tone comparison outside the mark."""
from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter
from scipy.optimize import isotonic_regression
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/earthshine_taca_source_20260914';z=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz')
y,x=np.mgrid[:1400,:1400];r=np.hypot(x-699.568111973117,y-699.6475341408573);a=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi);sec=(a*12/(2*np.pi)).astype(int)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098);domain=r<420;valid=(r>80)&(r<390);train=valid&~guard&(sec%2==0);test=valid&~guard&(sec%2==1)
def smooth(v,s):return gaussian_filter(v*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
rows=[];views={}
for sigma in [4,16,32]:
 ref=smooth(z['DHS530'],sigma)
 for name in ['V68','V49_noS8','DHS400']:
  v=smooth(z[name],sigma);cuts=np.unique(np.quantile(v[train],np.linspace(0,1,65)));idx=np.digitize(v[train],cuts[1:-1]);xx=[];yy=[];ww=[]
  for k in range(len(cuts)-1):
   m=idx==k
   if m.sum():xx.append(np.mean(v[train][m]));yy.append(np.mean(ref[train][m]));ww.append(m.sum())
  yy=isotonic_regression(yy,weights=ww).x;pred=np.interp(v,xx,yy);res=pred-ref
  rows.append(dict(sigma=sigma,name=name,heldout_rmse=float(np.sqrt(np.mean(res[test]**2))),mark_mean_DHS_DN=float(np.mean(res[mark])),mark_rmse=float(np.sqrt(np.mean(res[mark]**2))),mark_outside_training_range=int(((v<xx[0])|(v>xx[-1]))[mark].sum()),range=np.percentile(ref[mark],[5,50,95]).tolist()))
  if sigma==4:views[name]=pred
 if sigma==4:views['DHS530']=ref
pan=Image.new('RGB',(1000*2,1040*2),'#202020');draw=ImageDraw.Draw(pan)
for j,name in enumerate(['V68','DHS530','V49_noS8','DHS400']):
 im=np.clip(views[name],0,255);im[~domain]=0
 pic=Image.fromarray(np.uint8(np.rint(im))).convert('RGB');d=ImageDraw.Draw(pic);d.rectangle([550,902,723,1048],outline='#efad35',width=2)
 pic=pic.crop((200,200,1200,1200));ix=(j%2)*1000;iy=(j//2)*1040;pan.paste(pic,(ix,iy+40));draw.text((ix+12,iy+10),name+' | global monotone tone outside mark | diagnostic',fill='white')
pan.save(O/'vistes/A2_whole_moons_global_tone.png')
(O/'A2_global_tone.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
