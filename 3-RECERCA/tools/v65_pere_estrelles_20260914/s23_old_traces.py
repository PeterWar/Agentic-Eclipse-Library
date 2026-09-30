from pathlib import Path
import numpy as np,json,tifffile as tf
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
from PIL import Image,ImageDraw,ImageCms
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';cat=json.loads((O/'S22_final_catalog.json').read_text())['stars'];scene=tf.imread(O/'D8_artifacts_full.tif');old=json.loads((R/'output/v58_correccions_20260913/D4_sources.json').read_text())['selected'];old={v['star'].get('TYC'):(i,v['star']) for i,v in enumerate(old)};YY,XX=np.mgrid[-24:25,-24:25];rad=np.hypot(XX,YY);B=np.c_[XX.ravel()*0+1,XX.ravel()/24,YY.ravel()/24,(XX.ravel()/24)**2,(YY.ravel()/24)**2,XX.ravel()*YY.ravel()/24**2];ann=rad>13;roi=rad<14;rows=[];panels=[];icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
for r in cat:
 x,y=int(round(r['x'])),int(round(r['y']));sl=np.s_[y-24:y+25,x-24:x+25];p=scene[sl][...,:3].astype(float)/65535;ident=next((v for v in r['identifications'] if v in old),None);templates=[];source='native PSF Gaussian approximation'
 if ident:
  i,s=old[ident];path=R/f'output/v58_correccions_20260913/sources/fusion_star_{i:03d}.npz'
  if path.exists():
   z=np.load(path);c=z['component'];sx,sy=z['xy'];g=(c[...,0]+2*c[...,1]+c[...,2])/4;xx=XX+x-sx+32;yy=YY+y-sy+32;t=map_coordinates(g,[yy,xx],order=1,mode='constant');t/=max(t.max(),1e-20);templates.append(t);source='fixed independently corroborated V58 native stellar light component'
 if not templates:templates=[np.exp(-.5*(((XX-(r['x']-x))/2.0)**2+((YY-(r['y']-y))/2.0)**2))]
 t0=templates[0];luma=(p[...,0]+2*p[...,1]+p[...,2])/4;noise=max(1.4826*np.median(abs((luma.ravel()-B@np.linalg.lstsq(B[ann.ravel()],luma[ann],rcond=None)[0])[ann.ravel()])),1/65535)
 def solve(shift,ret=False):
  t=map_coordinates(t0,[YY+24-shift[1],XX+24-shift[0]],order=1,mode='constant');t[rad>20]=0;D=np.c_[t.ravel(),B];co=np.linalg.lstsq(D,luma.ravel(),rcond=None)[0]
  if ret:return t,D,co
  return (D@co-luma.ravel())[roi.ravel()]/noise
 fit=least_squares(solve,[0,0],bounds=(-4,4),loss='soft_l1',f_scale=2,max_nfev=25);t,D,co=solve(fit.x,True);err=noise*np.linalg.norm(np.linalg.pinv(D)[0]);snr=float(co[0]/err);component=np.zeros_like(p)
 # Only already-confirmed native stars; the image fit estimates their remaining point light, never fills background pixels.
 if snr>=5:
  for c in range(3):
   q=np.linalg.lstsq(D,p[...,c].ravel(),rcond=None)[0];amp=max(q[0],0);lim=np.min(p[...,c][t>1e-3]/t[t>1e-3]);amp=min(amp,lim*.98);component[...,c]=amp*t
 delta=np.rint(component*65535).astype('uint16');np.savez_compressed(O/f'S23_trace_{r["id"]}.npz',component=delta,xy=[x,y],template=t);out=dict(id=r['id'],TYC=r['TYC'],xy=[x,y],source=source,shift_of_point_model=fit.x.tolist(),remaining_stellar_component_SNR=snr,subtracted=bool(np.any(delta)),max_component_DN16=int(delta.max()),pixels=int(np.any(delta,-1).sum()));rows.append(out)
 def im(z):
  a=Image.fromarray(np.uint8(np.clip(z,0,1)*255+.5));return ImageCms.profileToProfile(a,icc,srgb,outputMode='RGB').resize((196,196),Image.Resampling.NEAREST)
 # Gaussian reconstruction over the original background after only point-component subtraction.
 from scipy.special import erf
 sx=r['x']-x;sy=r['y']-y;sigma=1.5;g=(erf((XX+.5-sx)/(np.sqrt(2)*sigma))-erf((XX-.5-sx)/(np.sqrt(2)*sigma)))*(erf((YY+.5-sy)/(np.sqrt(2)*sigma))-erf((YY-.5-sy)/(np.sqrt(2)*sigma)))/4;g*=2*np.pi*sigma**2;recon=np.array(r['display_RGB_peak'])*g[...,None];after=np.clip(p-component+recon,0,1);pan=Image.new('RGB',(392,221));pan.paste(im(p),(0,25));pan.paste(im(after),(196,25));draw=ImageDraw.Draw(pan);draw.text((4,6),r['id']+' V'+str(round(r['V'],2))+' subtract '+str(out['subtracted']),fill='white');panels.append(pan)
for k in range(0,len(panels),12):
 pane=Image.new('RGB',(392*3,221*4));
 for j,p in enumerate(panels[k:k+12]):pane.paste(p,((j%3)*392,(j//3)*221))
 pane.save(O/f'vistes/S23_stars_{k//12+1}.png')
(O/'S23_trace_models.json').write_text(json.dumps(dict(rows=rows,subtracted=sum(r['subtracted'] for r in rows),method='Subtract only fitted nonnegative point component at independently detected star positions. Original scene samples outside the component are exactly untouched, no background synthesis or image transformation.'),indent=2));print('subtracted',sum(r['subtracted'] for r in rows),'of',len(rows),flush=True)
