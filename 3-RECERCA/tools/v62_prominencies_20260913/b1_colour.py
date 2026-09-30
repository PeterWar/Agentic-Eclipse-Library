from pathlib import Path
import ast,json,numpy as np,cv2
from scipy.ndimage import binary_dilation
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';V42=R/'research/tools/v42_20260910/cau';ROI=np.s_[2777:4777,4377:6377]
gauss=lambda a,s:cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101)
tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb','corba_to']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'comu_pure','exec'))
base=np.stack([np.load(A/f'V61_L02_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
tot=np.asarray(np.load(V42/'fusion_total_v42_sense_estrelles.npy',mmap_mode='r')[ROI]).copy();m=np.load(V42/'support_v42.npy',mmap_mode='r')[ROI].astype('float32');data=np.nan_to_num(tot);L=(data[...,0]+2*data[...,1]+data[...,2])/4;tone=corba_to(L,m>0,70736.46875,pend=.22,anc=.74,terra=.045);ylin=a_lineal(tone)
def field(weight,sigma=24):
 den=gauss(L*weight,sigma);return np.stack([gauss(data[...,c]*weight,sigma)/np.maximum(den,1e-8) for c in range(3)],-1)
def render(q):
 qm=q.max(-1);wg=np.clip(np.where(qm>1,(1/np.maximum(ylin,1e-8)-1)/np.maximum(qm-1,1e-8),1),0,1);return a_srgb(ylin[...,None]*(1+wg[...,None]*(q-1)))*m[...,None]
q=field(m);ref=render(q)
expected=np.load(V42/'base_corba_total_v42_u16.npy',mmap_mode='r')[ROI]/65535
err=np.max(abs(ref[100:-100,100:-100]-expected[100:-100,100:-100]))*65535
print('reproduction maxDN',err)
# A causal perturbation of the existing colour producer: isolate highly red source support.
# This is diagnostic only, not a promoted exclusion or a physical claim.
ratio=np.divide(data[...,0],data[...,1],out=np.zeros_like(L),where=data[...,1]>0)
ys,xs=np.mgrid[2777:4777,4377:6377];lr=np.hypot(xs-5376.5681,ys-3776.6475)
reps=[];outviews=[('V61 base',base),('q24 reproduced',ref)]
for threshold in [2.5,3,4,6]:
 mask=(ratio>threshold)&(m>0)&(lr<650);weight=m*(~mask);qn=field(weight);cand=render(qn)
 delta=cand-ref;changed=base+delta;np.save(A/f'B1_colour_trial_RoverG_{threshold:g}.npy',changed);np.save(A/f'B1_q_{threshold:g}.npy',qn)
 regs=[]
 for side,bb in [('west',(4824,3713,4900,3904)),('east',(5829,3706,5856,3806)),('north',(5310,3280,5460,3310))]:
  x0,y0,x1,y1=bb;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];ok=(m[sl]>0)&(data[sl][...,1]>0)
  regs.append(dict(side=side,raw_RG_quantiles=np.percentile(ratio[sl][ok],[10,50,90]).tolist(),excluded=int(mask[sl].sum()),median_delta_RGB=np.median(delta[sl][ok],axis=0).tolist()))
 reps.append(dict(threshold=threshold,excluded=int(mask.sum()),regions=regs));outviews.append((f'exclude R/G>{threshold:g}',changed))
src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def cv(v):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(v,0,1)*255)),src,dst,outputMode='RGB')
for tag,bb in [('west',(4790,3690,4970,3940)),('east',(5780,3670,5900,3840))]:
 x0,y0,x1,y1=bb;w=x1-x0;h=y1-y0;k=3;panel=Image.new('RGB',(w*k*3,(h*k+25)*2))
 for j,(name,a) in enumerate(outviews):
  im=cv(a[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w*k,h*k));panel.paste(im,((j%3)*w*k,(j//3)*(h*k+25)+25));ImageDraw.Draw(panel).text(((j%3)*w*k+4,(j//3)*(h*k+25)+5),name,fill='white')
 panel.save(O/'vistes'/f'B1_{tag}.png')
for train,p in [('vixen',R/'output/v58_correccions_20260913/sources/vixen_starless.npy'),('sony',R/'output/v58_correccions_20260913/sources/sony_starless.npy')]:
 t=np.asarray(np.load(p,mmap_mode='r')[ROI]);np.save(A/f'B1_{train}_linear.npy',t)
(O/'B1_colour_diagnostic.json').write_text(json.dumps(dict(reproduction_max_DN16=float(err),trials=reps,decision='diagnostic only'),indent=2));print(json.dumps(reps,indent=2))
