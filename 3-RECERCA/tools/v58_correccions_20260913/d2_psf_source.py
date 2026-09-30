from common58 import *
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
claim();det=json.loads((O/'D1_stars_detected.json').read_text());stars=[]
for d in sorted(det['candidates'],key=lambda x:-x['contrast']):
 if all(np.hypot(d['x']-s['x'],d['y']-s['y'])>10 for s in stars):stars.append(d)
# Source extraction fits measured stellar light, keeps background and residual noise, no cloned texture.
rad=32;yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];rr=np.hypot(xx,yy);X=np.stack([np.ones_like(xx),xx/rad,yy/rad,(xx/rad)**2,xx*yy/rad**2,(yy/rad)**2],axis=-1);fitmask=rr<30;ann=(rr>18)&(rr<30)
def extract(q,x,y,shape=None):
 bg=np.linalg.lstsq(X[ann],q[ann],rcond=None)[0];res=q-X@bg;sd=1.4826*np.median(np.abs(res[ann]-np.median(res[ann])))+1e-9;norm=max(res[rr<5].max(),sd);z=res/norm
 def psf(p):
  dx,dy,sx,sy,ang,beta=p[:6];t=np.deg2rad(ang);u=np.cos(t)*(xx-dx)+np.sin(t)*(yy-dy);v=-np.sin(t)*(xx-dx)+np.cos(t)*(yy-dy);return (1+(u/sx)**2+(v/sy)**2)**(-beta)
 if shape is None:
  def fun(p):return ((p[6]*psf(p)+X@p[7:]-z)[fitmask]).ravel()
  p0=[0,0,5,5,0,2.5,1,0,0,0,0,0,0];low=[-4,-4,1.5,1.5,-90,1.1,0,-3,-3,-3,-3,-3,-3];high=[4,4,18,18,90,8,5,3,3,3,3,3,3]
  fit=least_squares(fun,p0,bounds=(low,high),loss='soft_l1',f_scale=max(.03,sd/norm),max_nfev=120);shape=fit.x[:6]
 model=psf(shape);D=np.concatenate([model[...,None],X],axis=-1);coef=np.linalg.lstsq(D[fitmask],q[fitmask],rcond=None)[0];component=max(0,coef[0])*model
 # finite subtraction reaches zero smoothly only beyond the fitted PSF wing, 24..32px.
 taper=np.clip((32-rr)/8,0,1);taper=taper*taper*(3-2*taper);component*=taper
 after=q-component;resafter=after-X@coef[1:];return component,shape,dict(peak=coef[0],noise=sd,snr=coef[0]/sd,remaining_core_sigma=float(np.max(gaussian_filter(resafter,2)[rr<8])/(sd/7.09)),shape=shape.tolist(),wing24_sigma=float(np.max(component[(rr>24)&(rr<25)])/sd))
F=np.load(V42/'cau/fusion_total_v42.npy',mmap_mode='r');rep=[];samples=[]
for i,s in enumerate(stars):
 x,y=s['x'],s['y'];q=np.array(F[y-rad:y+rad+1,x-rad:x+rad+1,1],float);component,shape,r=extract(q,x,y);r.update(star=s);rep.append(r);samples.append((q,q-component))
 print(i,s['TYC'],r,flush=True)
np.savez_compressed(O/'arrays/D2_psf_pilot.npz',before=np.stack([q[0] for q in samples]),after=np.stack([q[1] for q in samples]));save('D2_psf_pilot.json',rep)
can=Image.new('RGB',(8*140,((len(samples)+3)//4)*150),(25,25,25));draw=ImageDraw.Draw(can)
for i,(a,b) in enumerate(samples):
 lo,hi=np.percentile(a,[2,99]);x0=(i%4)*280;y0=(i//4)*150
 for j,q in enumerate((a,b)):
  tile=Image.fromarray(np.uint8(np.clip((q-lo)/(hi-lo),0,1)*255)).resize((130,130));can.paste(tile,(x0+j*140,y0+18))
 draw.text((x0,y0),f'{i}: {stars[i]["TYC"]}',fill='white')
can.save(O/'vistes/D2_psf_galeria.png')
