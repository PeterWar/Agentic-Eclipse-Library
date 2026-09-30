from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';cat=pd.read_csv(R/'output/v58_correccions_20260913/catalog_projected.csv').set_index('TYC');W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');allout={}
def combine_planes(row):
 out=[]
 for c in range(4):
  p=[v[c] for v in row['native_planes'].values()];w=np.array([1/q['error']**2 for q in p]);fl=np.dot(w,[q['flux'] for q in p])/max(w.sum(),1e-30);err=1/np.sqrt(max(w.sum(),1e-30));out.append([fl,err])
 return np.array(out)
for train,file in [('Sony','S10_native_detection.json'),('Vixen','S13_vixen_detection.json')]:
 d=json.loads((O/file).read_text());known=pd.read_csv(W/'xmatch'/('final_match_sony.csv' if train=='Sony' else 'final_match_r6.csv')).set_index('det');rows=d['rows'];refs=[]
 for r in rows:
  tyc=r.get('TYC') if r.get('TYC') else known.loc[r['det']].TYC;bv=float(cat.loc[tyc].BVuse) if tyc in cat.index else np.nan;r['TYC']=tyc;r['BV']=bv;p=combine_planes(r);r['combined_CFA_flux_error']=p.tolist();wg=1/p[[1,3],1]**2;fg=np.dot(wg,p[[1,3],0])/wg.sum();eg=1/np.sqrt(wg.sum());
  if r['kind']=='psf_reference' and np.isfinite(bv):refs.append(dict(det=r['det'],reserved=r.get('reserved',False),BV=bv,G=fg,Gerr=eg,R=p[0,0],Rerr=p[0,1],B=p[2,0],Berr=p[2,1]))
 coef={};report=[]
 for c in ['R','B']:
  sel=[r for r in refs if not r['reserved'] and r['G']/r['Gerr']>=15 and r[c]/r[c+'err']>=5];x=np.array([r['BV'] for r in sel]);y=np.log([r[c]/r['G'] for r in sel]);B=np.c_[x*0+1,x];sol=least_squares(lambda p:B@p-y,np.linalg.lstsq(B,y,rcond=None)[0],loss='soft_l1',f_scale=.1);coef[c]=sol.x.tolist();held=[r for r in refs if r['reserved'] and r['G']/r['Gerr']>=10 and r[c]/r[c+'err']>=4];er=[float(np.log(r[c]/r['G'])-(sol.x[0]+sol.x[1]*r['BV'])) for r in held];report.append(dict(channel=c,train=len(sel),coefficients=sol.x.tolist(),held=[dict(det=r['det'],log_error=e) for r,e in zip(held,er)],median_abs_log_error=float(np.median(abs(np.array(er))))));print(train,report[-1],flush=True)
 groups=({'A':['DSC06984','DSC06985','DSC06987'],'B':['DSC06991','DSC06993','DSC06996','DSC06999']} if train=='Sony' else {'A':['572A2979','572A2981','572A2982'],'B':['572A2978','572A2980','572A2983','572A2984','572A2996']})
 for r in rows:
  bv=np.clip(r['BV'],0,1.8) if np.isfinite(r['BV']) else .65;q=np.array([np.exp(coef['R'][0]+coef['R'][1]*bv),1,np.exp(coef['B'][0]+coef['B'][1]*bv),1]);summary={}
  for g,names in dict(**groups,all=list(r['native_planes'])).items():
   pp=np.array([[[z['flux'],z['error']] for z in r['native_planes'][name]] for name in names]);w=1/pp[...,1]**2;den=np.sum(w*q*q);f=np.sum(w*q*pp[...,0])/max(den,1e-30);e=1/np.sqrt(max(den,1e-30));summary[g]=dict(flux=float(f),error=float(e),snr=float(f/e))
  accept=summary['all']['snr']>=8 and min(summary['A']['snr'],summary['B']['snr'])>=4
  if train=='Sony' and r['kind']!='psf_reference':accept=accept and r['separation']<=2.5
  r['multiband']=summary;r['multiband_accept']=bool(accept);r['union_accept']=bool(accept or r['native_accept'])
 d.update(spectral_coefficients=coef,spectral_validation=report,rows=rows)
 for kind in ['catalog','rotated_null']:print(train,kind,sum(r['kind']==kind and r['union_accept'] for r in rows),flush=True)
 allout[train]=d
(O/'S14_multiband_detection.json').write_text(json.dumps(allout,indent=2));print('COMPLETE')
