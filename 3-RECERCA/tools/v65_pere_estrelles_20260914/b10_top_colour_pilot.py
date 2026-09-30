from pathlib import Path
import numpy as np,json,cv2,ast,tifffile as tf
from scipy.ndimage import gaussian_filter,map_coordinates,binary_dilation,label
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913/arrays';V=O/'vistes';tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb']],type_ignores=[]),'pure','exec'))
old=np.stack([np.load(A/f'L76_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;orig=np.stack([np.load(P/f'V57_L01_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;ref10=np.stack([np.load(P/f'V57_L02_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;dx,dy,_,_=json.loads((O/'B9_top_colour_registration.json').read_text())['parameters'];y,x=np.mgrid[:2000,:2000];mapped=np.stack([map_coordinates(orig[...,c],[y-dy,x-dx],order=1) for c in range(3)],-1);mapped10=np.stack([map_coordinates(ref10[...,c],[y-dy,x-dx],order=1) for c in range(3)],-1)
# Colour reference is the shorter unsaturated photograph. Only colour is transferred; native luminance, alpha and geometry stay exact.
box=(x+4377>5257)&(x+4377<5302)&(y+2777>3298)&(y+2777<3339);quiet=box&(((x+4377)<5270)|((x+4377)>5290))&(y+2777<3327)
def continuum(a):
 v=np.log(np.maximum(a[...,0],.001)/np.maximum(a[...,1],.001));B=np.c_[np.ones(quiet.sum()),(x[quiet]-900)/30,(y[quiet]-540)/30];p=np.linalg.lstsq(B,v[quiet],rcond=None)[0];bg=p[0]+p[1]*(x-900)/30+p[2]*(y-540)/30;noise=1.4826*np.median(abs(v[quiet]-bg[quiet]));return v-bg,noise
ex,noise=continuum(mapped);ex10,n10=continuum(mapped10);sig=np.minimum(np.clip((ex-3*noise)/(3*noise),0,1),np.clip((ex10-3*n10)/(3*n10),0,1));sig*=box
mask=gaussian_filter(sig,.75);mask*=box;mask[mapped[...,1]<.01]=0
lin=a_lineal(old);rlin=a_lineal(mapped);Y=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;Yr=(rlin[...,0]+2*rlin[...,1]+rlin[...,2])/4;q=rlin/np.maximum(Yr[...,None],1e-8);target=Y[...,None]*q;qm=target.max(-1);target/=np.maximum(qm,1)[...,None];new=lin+(target-lin)*mask[...,None];rgb=a_srgb(new);u=np.rint(np.clip(rgb,0,1)*65535).astype('uint16');u[mask==0]=np.rint(old[mask==0]*65535).astype('uint16');np.save(A/'B10_L76_colour.npy',u);np.save(A/'B10_colour_support.npy',mask)
final=tf.imread(O/'A2_clean_ROI.tif').astype(float)/65535;alpha=np.load(A/'L76_C-1.npy')/65535*np.load(A/'L76_C-2.npy')/65535;upper=np.ones(alpha.shape)
for id in [83,96]:upper*=1-np.load(A/f'L{id}_C-1.npy')/65535*np.load(A/f'L{id}_C-2.npy')/65535
preview=final[...,:3]+(u/65535-old)*alpha[...,None]*upper[...,None];icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB');pan=Image.new('RGB',(500*3,650+25));draw=ImageDraw.Draw(pan)
for j,(name,img) in enumerate([('Pere V64',final[...,:3]),('Short-exposure colour',preview),('Source 11 mapped - colour only',mapped)]):
 a=img[3285-2777:3350-2777,5250-4377:5300-4377];im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255)),icc,srgb,outputMode='RGB').resize((500,650),Image.Resampling.NEAREST);pan.paste(im,(j*500,25));draw.text((j*500+5,5),name,fill='white')
pan.save(V/'B10_top_colour.png');rep=dict(changed_pixels=int(np.any(u!=np.rint(old*65535),-1).sum()),support_pixels=int((mask>0).sum()),noise_logRG11=float(noise),noise_logRG10=float(n10),reference='Original photo11, line signal corroborated in10; mapped for colour with upper-stem fit and lower-stem holdout.',alignment_changes=False,alpha_changes=False,status='pilot; no geometry copied');(O/'B10_colour_pilot.json').write_text(json.dumps(rep,indent=2));print(rep)
