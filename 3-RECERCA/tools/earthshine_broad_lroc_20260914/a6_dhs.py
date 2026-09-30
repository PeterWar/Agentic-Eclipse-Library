"""Reference-only sampling. Registration supplied by independent read-only audit.
No reference pixels enter the photographic producer. Exclude mark+50pxguard.
"""
from pathlib import Path
import numpy as np,json,hashlib
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,map_coordinates
R=Path.cwd();O=R/'output/earthshine_broad_lroc_20260914';geo=json.loads((R/'research/tools/estudi_druckmuller/geometria.json').read_text())
Y,X=np.mgrid[:1400,:1400];xx=X-699.568111973117;yy=Y-699.6475341408573;r=np.hypot(xx,yy)
params={'400':[-43.309098148741285,-.3141708296119896,-.6396722000081778,-.014027127783527172],'530':[-46.577373526128625,.06710123804654282,-.5148840649620089,-.012657960276107529],'200':[-43.65471078322604,-.38886003278305603,-.6475112713981995,-.013239634745965116]}
arr={};files=[]
for mm,p in params.items():
 name=f'TSE_2026_{mm}mm_DHS.png';g=geo[name];path=Path('/Users/USUARI/Desktop/Eclipse 2026/Drukmuller fotos finals')/name
 im=np.asarray(Image.open(path).convert('RGB'),float).mean(axis=2)
 s=g['R_lluna_px']/449*(1+p[3]);a=np.deg2rad(p[0]);mx=g['cx']+g['marc'][2]+p[1]+s*(np.cos(a)*xx-np.sin(a)*yy);my=g['cy']+g['marc'][0]+p[2]+s*(np.sin(a)*xx+np.cos(a)*yy)
 arr['DHS'+mm]=map_coordinates(im,[my,mx],order=1)
 with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 files.append(dict(path=str(path),sha256=h,reference_only_parameters=p))
arr['LROC']=np.load(R/'output/v68_lroc_revisio_20260914/arrays/L62_exact_psb.npz')['rgb'].mean(axis=2).astype(float)
arr['V68']=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].mean(axis=2).astype(float)
arr['SectorCentered']=np.load(O/'arrays/A4_centered_candidate.npz')['rgb'].mean(axis=2).astype(float)
arr['V49_noS8']=np.load(R/'output/earthshine_v49_pere_reveal_20260912/A0_Pere_moon_RGB16.npy').mean(axis=2).astype(float)
domain=r<420;good=(r>80)&(r<390)&~((X>500)&(X<773)&(Y>852)&(Y<1098));mark=(X>=550)&(X<723)&(Y>=902)&(Y<1048)
def smooth(a,s):return gaussian_filter(a*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
rows=[];display={}
for sig in [(8,32),(16,64),(32,96),(64,160)]:
 bands={k:smooth(a,sig[0])-smooth(a,sig[1]) for k,a in arr.items()};ref=bands['LROC'];std=ref[good].std()
 for k,a in bands.items():
  gain=np.cov(a[good],ref[good],bias=True)[0,1]/np.var(a[good]);offset=np.mean(ref[good])-gain*np.mean(a[good]);scaled=gain*a+offset;res=(scaled-ref)/std
  row=dict(band_sigma=list(sig),name=k,corr=float(np.corrcoef(a[good],ref[good])[0,1]),gain=float(gain),offset=float(offset),mark_mean_residual_sigma=float(res[mark].mean()),mark_RMS_residual_sigma=float(np.sqrt(np.mean(res[mark]**2))))
  rows.append(row)
  if sig==(16,64):display[k]=scaled/std
  if k in ['V68','SectorCentered','DHS400','DHS530']:print(row,flush=True)
np.savez_compressed(O/'arrays/A6_reference_only.npz',**arr)
pan=Image.new('RGB',(660*3,588*2),'#191919');draw=ImageDraw.Draw(pan)
for j,k in enumerate(['V68','DHS400','DHS530','LROC','SectorCentered','V49_noS8']):
 a=display[k];im=Image.fromarray(np.uint8(np.clip(.5+a/5,0,1)[833:1103,462:792]*255+.5)).convert('RGB');ix=j%3*660;iy=j//3*588;pan.paste(im.resize((660,540)),(ix,iy+38));draw.text((ix+9,iy+9),k+' | sigma16-64 | outside-mark gain+offset',fill='white')
pan.save(O/'vistes/A6_DHS_band_comparison.png')
(O/'A6_DHS.json').write_text(json.dumps(dict(reference_files=files,rows=rows,scope='Photographic corroboration, not calibrated albedo. DHS200 includes DHS400 sources. No reference pixels enter a photographic correction.',registration_fitted_on='texture outside orange+50px guard; alternating sectors held out',heldout_registration_correlations={'DHS400':.948,'DHS530':.897,'DHS200':.882}),indent=2)+'\n')
