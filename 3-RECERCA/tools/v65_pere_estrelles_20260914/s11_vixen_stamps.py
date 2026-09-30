from pathlib import Path
import numpy as np,json,pandas as pd,rawpy,hashlib
from astropy.io import fits
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');V=W/'vixen';X=W/'xmatch';D=Path('/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat');F=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/0-calibracio/FLAT_RADIAL.fits');cat=pd.read_csv(X/'cat2_r6.csv');project=pd.read_csv(R/'output/v58_correccions_20260913/catalog_projected.csv').set_index('TYC');plate=json.loads((X/'final_solution.json').read_text())['r6_radial'];u=cat.xh_as.to_numpy();v=cat.yh_as.to_numpy();Q=np.c_[u*0+1,u,v,u*(u*u+v*v),v*(u*u+v*v)];xy=Q@np.array([plate['px'],plate['py']]).T;known=pd.read_csv(X/'final_match_r6.csv');SH=json.loads((V/'shifts_start.json').read_text());frames={'572A2978':1.,'572A2979':2.,'572A2980':2.,'572A2981':2.,'572A2982':10.3,'572A2983':10.3,'572A2984':10.3,'572A2996':1.};rows=[]
for kind in ['catalog','rotated_null']:
 p=xy.copy()
 if kind=='rotated_null':p=2*np.array([plate['sun_x'],plate['sun_y']])-p
 for i,q in enumerate(p):
  if not(45<q[0]<6910 and 45<q[1]<4590) or np.linalg.norm(q-[plate['sun_x'],plate['sun_y']])<465:continue
  r=cat.iloc[i];proj=project.loc[r.TYC];rows.append(dict(kind=kind,catalog_index=int(i),TYC=r.TYC,HIP=r.HIP,V=float(r.Vuse),expected=q.tolist(),x_final=float(proj.x_pred),y_final=float(proj.y_pred)))
for i,r in known.iterrows():rows.append(dict(kind='psf_reference',det=str(r.det),TYC=r.TYC,V=float(r.V),reserved=bool(i%3==0),expected=[r.x,r.y]))
records=[]
with fits.open(F,memmap=True) as hd:
 flat=hd[0].data
 for name,e in frames.items():
  path=D/(name+'.CR3');dk=np.load(V/f'dark_med_{10 if e>10 else int(e)}.npy',mmap_mode='r');st=[];col=[];valid=[];origin=[];coords=[]
  with rawpy.imread(str(path)) as rr:
   raw=rr.raw_image_visible;colors=rr.raw_colors_visible;tm,lm=rr.sizes.top_margin,rr.sizes.left_margin;wb=np.array(rr.daylight_whitebalance);wb/=wb[1]
   for r in rows:
    q=np.array(r['expected'])+np.array(SH[name][1:]);ix,iy=np.rint(q).astype(int);sl=np.s_[iy-12:iy+13,ix-12:ix+13];fl=np.asarray(flat[iy-12+tm:iy+13+tm,ix-12+lm:ix+13+lm]);z=(raw[sl].astype(float)-dk[sl])/fl/e;st.append(z.astype('float32'));col.append(colors[sl].copy());valid.append((raw[sl]<15800)&np.isfinite(z)&(fl>.1));origin.append([ix,iy]);coords.append(q)
  np.savez_compressed(O/f'S11_{name}.npz',data=np.array(st),colour=np.array(col),valid=np.array(valid),origin=np.array(origin),expected=np.array(coords),wb=wb,exposure=e);records.append(dict(name=name,path=str(path),bytes=path.stat().st_size,mtime_ns=path.stat().st_mtime_ns,exposure=e,wb=wb.tolist(),visible_margin=[lm,tm],shift=SH[name]));print(name,len(rows),flush=True)
(O/'S11_vixen_manifest.json').write_text(json.dumps(dict(flat=str(F),flat_sha=hashlib.file_digest(open(F,'rb'),'sha256').hexdigest(),rows=rows,frames=records,calibration='Native RAW - exposure dark, physically same CFA flat before resampling; no Bayer mixing or spatial interpolation.'),indent=2));print('COMPLETE')
