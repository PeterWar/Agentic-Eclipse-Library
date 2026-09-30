from common58 import *
import ast
from scipy.optimize import nnls
from PIL import Image,ImageDraw
claim();tree=ast.parse((T/'d1_detect_stars.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='detect');exec(compile(ast.Module(body=[fn],type_ignores=[]),'detect','exec'))
F=np.load(V42/'cau/fusion_total_v42.npy',mmap_mode='r');A=np.load(V42/'cau/sony_A_corr_v42.npy',mmap_mode='r');B=np.load(V42/'cau/sony_B_total_v42.npy',mmap_mode='r');rows=json.loads((O/'D2_psf_pilot.json').read_text());rad=32;yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];rr=np.hypot(xx,yy);X=np.stack([np.ones_like(xx),xx/rad,yy/rad,(xx/rad)**2,xx*yy/rad**2,(yy/rad)**2],axis=-1);ann=(rr>=16)&(rr<30);valid=rr<22;nodes=np.arange(-6,7,3);G=np.stack([np.exp(-((xx-a)**2+(yy-b)**2)/(2*2.0**2)) for a in nodes for b in nodes],axis=-1);D=G[valid];reps=[];samps=[]
def extract_empirical(q):
 coef=np.linalg.lstsq(X[ann],q[ann],rcond=None)[0]
 for _ in range(3):
  res=q-X@coef;sd=1.4826*np.median(np.abs(res[ann]-np.median(res[ann])))+1e-9;k=ann&(np.abs(res)<3*sd);coef=np.linalg.lstsq(X[k],q[k],rcond=None)[0]
 bg=X@coef;z=q-bg;p,_=nnls(D,z[valid],maxiter=1000);comp=G@p;after=q-comp;sm=gaussian_filter(after-bg,2);old=gaussian_filter(q-bg,2);outer=sm[(rr>16)&(rr<27)];noise=1.4826*np.median(np.abs(outer-np.median(outer)))+1e-9
 return comp,dict(core_before_sigma=float(old[rr<8].max()/noise),core_after_sigma=float(sm[rr<8].max()/noise),negative_after_sigma=float(sm[rr<8].min()/noise),component_peak=float(comp.max()),component_mass=float(comp.sum()),mass_r10=float(comp[rr<10].sum()/max(comp.sum(),1e-9)),noise_sm=noise)
for i,row in enumerate(rows):
 s=row['star'];x,y=s['x'],s['y'];a=detect(A,x,y,5);b=detect(B,x,y,5);q=np.array(F[y-rad:y+rad+1,x-rad:x+rad+1,1],float);comp,r=extract_empirical(q);r.update(star=s,sonyA=a,sonyB=b);r['repeat_AB']=bool(a and b and min(a['snr'],b['snr'])>7 and min(a['contrast'],b['contrast'])>2 and np.hypot(a['x']-b['x'],a['y']-b['y'])<6);reps.append(r);samps.append((q,q-comp));print(i,s['TYC'],round(r['core_before_sigma'],1),round(r['core_after_sigma'],1),round(r['negative_after_sigma'],1),'AB',r['repeat_AB'],'mass10',round(r['mass_r10'],3),flush=True)
save('D3_empirical_pilot.json',reps);np.savez_compressed(O/'arrays/D3_empirical_pilot.npz',before=np.stack([q[0] for q in samps]),after=np.stack([q[1] for q in samps]));can=Image.new('RGB',(1120,((len(samps)+3)//4)*150),(25,25,25));draw=ImageDraw.Draw(can)
for i,(a,b) in enumerate(samps):
 lo,hi=np.percentile(a,[2,99]);x0=(i%4)*280;y0=(i//4)*150
 for j,q in enumerate((a,b)):can.paste(Image.fromarray(np.uint8(np.clip((q-lo)/(hi-lo),0,1)*255)).resize((130,130)),(x0+j*140,y0+18))
 draw.text((x0,y0),f'{i}: {reps[i]["star"]["TYC"]}',fill='white')
can.save(O/'vistes/D3_empirical_galeria.png')
