from pathlib import Path
import numpy as np,json,ast,cv2,tifffile as tf
from scipy.ndimage import gaussian_filter,binary_dilation
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';V=O/'vistes';C=R/'research/tools/v42_20260910/cau';sl=np.s_[2777:4777,4377:6377]
tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb']],type_ignores=[]),'pure','exec'))
base=np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;lin=a_lineal(base);Y=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;d=np.nan_to_num(np.array(np.load(C/'fusion_total_v42_sense_estrelles.npy',mmap_mode='r')[sl]));m=np.load(C/'support_v42.npy',mmap_mode='r')[sl].astype('float32');L=(d[...,0]+2*d[...,1]+d[...,2])/4
rr=np.hypot(*np.meshgrid(np.arange(2777,4777)-3776.647534140857,np.arange(4377,6377)-5376.568111973117,indexing='ij'));ex=(d[...,0]>2.5*d[...,1])&(d[...,1]>0)&(m>0)&(rr<650);w=m*(~ex);den=gaussian_filter(L*w,24);q=np.stack([gaussian_filter(d[...,c]*w,24)/np.maximum(den,1e-8) for c in range(3)],-1);mx=q.max(-1);limit=1/np.maximum(mx,1);protect=gaussian_filter(binary_dilation(ex,iterations=2).astype('float32'),1);protect[ex]=1
# Same measured colour estimator; change only highlight mapping, keeping colour when luminance reaches gamut.
# Smooth C1 shoulder, asymptote maximum in-gamut luminance. No clipping or spatial luminance filtering.
old=tf.imread(O/'A2_clean_ROI.tif').astype('float32')/65535;cum=tf.imread(O/'A2_c01_filters.tif').astype('float32')/65535;no=tf.imread(O/'A2_c00_base.tif').astype('float32')/65535
coeff=np.ones((2000,2000,3),np.float32)
for id in [30,76,83,96]:
 aa=np.load(A/f'L{id}_C-1.npy').astype('float32')/65535*np.load(A/f'L{id}_C-2.npy').astype('float32')/65535;coeff*=1-aa[...,None]
# local filter transfer measured natively; ACHF includes tiny affine term so this is preview only, native validation later.
transfer=np.divide(cum[...,:3],no[...,:3],out=np.zeros_like(cum[...,:3]),where=no[...,:3]>.001)
views=[('V64 Pere',old[...,:3])];reports=[]
for k in [.8,.9,.95]:
 start=k*limit;v=np.maximum(Y-start,0);Yn=np.where(Y>start,start+v/(1+v/np.maximum(limit-start,1e-6)),Y);newlin=Yn[...,None]*q;change=(Y>start)&(base.max(-1)>0)&(den>1e-5)&(rr<850);fade=(1-protect)*change;newlin=lin+(newlin-lin)*fade[...,None];new=np.clip(a_srgb(newlin),0,1);new[~change]=base[~change];u=np.rint(new*65535).astype('uint16');np.save(A/f'B11_base_k{k}.npy',u);preview=old[...,:3]+(new-base)*transfer*coeff;views.append((f'shoulder {k}',preview));changed=np.any(u!=np.rint(base*65535),-1);reports.append(dict(k=k,changed=int(changed.sum()),max_delta=float(abs(new-base).max()),change_near_limit850=int(changed[(rr>840)&(rr<850)].sum())))
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
for name,bb in [('NW',(4960,3300,5450,3590)),('west',(4840,3500,5030,3900)),('full',(4750,3190,5990,4400))]:
 x0,y0,x1,y1=bb;scale=1 if name=='full' else 2;w=(x1-x0)*scale;h=(y1-y0)*scale;pan=Image.new('RGB',(w*2,(h+25)*2));draw=ImageDraw.Draw(pan)
 for j,(label,a) in enumerate(views):pan.paste(view(a[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w,h)),((j%2)*w,(j//2)*(h+25)+25));draw.text(((j%2)*w+5,(j//2)*(h+25)+5),label,fill='white')
 pan.save(V/f'B11_{name}.png')
(O/'B11_highlight_pilot.json').write_text(json.dumps(dict(cause='Gamut compression in old producer desaturates at high display luminance; candidate uses invertible shoulder preserving measured colour, no alignment change.',candidates=reports,status='approximate preview only; not promoted'),indent=2));print(reports)
