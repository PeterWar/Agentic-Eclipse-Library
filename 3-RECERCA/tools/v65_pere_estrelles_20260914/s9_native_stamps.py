from pathlib import Path
import json,numpy as np,pandas as pd,pickle,rawpy,hashlib
from astropy.io import fits
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');S=W/'sony';D=Path('/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA');F=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/016_SONYTOT_CIENCIA_20260827T183356Z/0-calibracio/FLAT_RADIAL.fits')
EXP={'DSC06984':2.,'DSC06985':1.,'DSC06987':8.,'DSC06991':1.,'DSC06993':8.,'DSC06996':2.,'DSC06999':2.};OFF=pickle.load(open(S/'offsets6.pkl','rb'))['off'];M=np.load(S/'warpM.npy');T=np.load(S/'warpT.npy');C=np.load(S/'warpC.npy');rows=json.loads((O/'S8_detection_refined.json').read_text())['rows'];known=pd.read_csv(W/'xmatch/final_match_sony.csv')
# Train/holdout partition fixed before native fitting. Native stamps of all candidates and identical rotated controls.
for i,r in known.iterrows():
 measured=json.loads((O/'S1_psf_stacks.json').read_text());ca=next(v for v in measured if v['det']==r.det and v['group']=='C');aa=next(v for v in measured if v['det']==r.det and v['group']=='A');c=np.array([ca['x'],ca['y']]);a=np.array([aa['x'],aa['y']]);rows.append(dict(kind='psf_reference',det=r.det,reserved=bool(i%3==0),V=r.V,A=dict(x=a[0],y=a[1]),C=dict(x=c[0],y=c[1])))
positions={};records=[]
with fits.open(F,memmap=True) as hd:
 flat=hd[0].data;assert flat.shape==(5320,8000);flat=flat[:,:7968]
 for name,e in EXP.items():
  g='A' if name in ['DSC06984','DSC06985','DSC06987'] else 'C';path=D/(name+'.ARW');md=np.load(S/f'masterdark_{int(e)}s.npy',mmap_mode='r');stamps=[];colours=[];valid=[];origin=[];xy=[]
  with rawpy.imread(str(path)) as rr:
   raw=rr.raw_image_visible;col=rr.raw_colors_visible;wb=np.array(rr.daylight_whitebalance);wb=wb/wb[1]
   for r in rows:
    p=np.array([r[g]['x'],r[g]['y']])+OFF[name];ix,iy=np.rint(p).astype(int);sl=np.s_[iy-12:iy+13,ix-12:ix+13];fl=np.array(flat[sl],float);z=(raw[sl].astype(float)-md[sl])/fl/e;v=(raw[sl]<15600)&np.isfinite(z)&(fl>.1);stamps.append(z.astype('float32'));colours.append(col[sl].copy());valid.append(v);origin.append([ix,iy]);xy.append(p)
  np.savez_compressed(O/f'S9_{name}.npz',data=np.array(stamps),colour=np.array(colours),valid=np.array(valid),origin=np.array(origin),expected=np.array(xy),wb=wb,exposure=e)
  records.append(dict(name=name,path=str(path),bytes=path.stat().st_size,mtime_ns=path.stat().st_mtime_ns,exposure=e,wb=wb.tolist(),offset=list(map(float,OFF[name]))));print(name,len(stamps),flush=True)
(O/'S9_native_manifest.json').write_text(json.dumps(dict(flat=str(F),flat_sha=hashlib.file_digest(open(F,'rb'),'sha256').hexdigest(),calibration='RAW minus exposure master dark, flat before any interpolation, nominal exposure; fitting every CFA plane separately. No raster interpolation.',rows=rows,frames=records),indent=2))
