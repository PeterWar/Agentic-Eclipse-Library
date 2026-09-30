from pathlib import Path
import numpy as np,json,pandas as pd,tifffile as tf
from scipy.ndimage import label
from s19_native_measure import c_final
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';d=json.loads((O/'S19_native_measure.json').read_text());cal=json.loads((O/'S21_photometry_calibration.json').read_text());spec=json.loads((O/'S14_multiband_detection.json').read_text());W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');plates=json.loads((W/'xmatch/final_solution.json').read_text());grid=json.loads((R/'research/tools/v29/cau_final/direct_grid_receipt.json').read_text());metas={k:json.loads((O/(v+'.json')).read_text()) for k,v in [('Sony','S9_native_manifest'),('Vixen','S11_vixen_manifest')]};known={tag:pd.read_csv(W/f'xmatch/final_match_{s}.csv') for tag,s in [('Sony','sony'),('Vixen','r6')]};source=tf.imread(O/'D8_artifacts_full.tif');project=pd.read_csv(R/'output/v58_correccions_20260913/catalog_projected.csv').set_index('TYC')

def combine(ms):
 F=[];E=[]
 for c in [0,1,2,3]:
  a=[]
  for m in ms:
   q=m['planes'][c];z=cal[m['frame']];f=q['flux']*z['calibration'];e=np.hypot(q['error']*z['calibration'],q['flux']*z['error']);a.append((f,e))
  a=np.array(a);w=1/a[:,1]**2;F.append(float(np.sum(w*a[:,0])/max(w.sum(),1e-30)));E.append(float(1/np.sqrt(max(w.sum(),1e-30))))
 w=1/np.array(E)[[1,3]]**2;g=float(np.dot(w,np.array(F)[[1,3]])/w.sum());ge=float(1/np.sqrt(w.sum()));return dict(RGB=[F[0],g,F[2]],error=[E[0],ge,E[2]])
# Native instrumental throughput ratio from shared training references; holdout unchanged.
ref={}
for tag in ['Sony','Vixen']:
 ref[tag]={}
 for _,r in known[tag].iterrows():
  ms=[m for m in d['references'] if m['source']==tag and m['det']==r.det]
  if ms:ref[tag][r.TYC]=dict(**combine(ms),reserved=bool(ms[0]['reserved']),V=float(r.V))
ratios=[];held=[]
for tyc in set(ref['Sony'])&set(ref['Vixen']):
 s,v=ref['Sony'][tyc],ref['Vixen'][tyc]
 if min(s['RGB'][1]/s['error'][1],v['RGB'][1]/v['error'][1])<8:continue
 rr=dict(TYC=tyc,ratio=s['RGB'][1]/v['RGB'][1],reserved=s['reserved'] or v['reserved']);(held if rr['reserved'] else ratios).append(rr)
ratio=float(np.median([r['ratio'] for r in ratios]));print('throughput',ratio,'train',len(ratios),'held',held,flush=True)

def platexy(p,u,v):return np.array([1,u,v,u*(u*u+v*v),v*(u*u+v*v)])@np.array([p['px'],p['py']]).T
def jac(p,u,v):return np.stack([(platexy(p,u+.01,v)-platexy(p,u-.01,v))/.02,(platexy(p,u,v+.01)-platexy(p,u,v-.01))/.02],axis=1)
rows=[]
for r in d['catalog']:
 ms=[m for m in d['measurements'] if m['TYC']==r['TYC']];measurements={tag:[m for m in ms if (m['source'] in ['Sony','extra'] if tag=='Sony' else m['source']=='Vixen')] for tag in ['Sony','Vixen']};phot={tag:combine(q) for tag,q in measurements.items() if q};spos=[m for m in measurements['Sony'] if m['green_snr']>=5];p=project.loc[r['TYC']]
 if spos:
  ww=np.array([min(m['green_snr'],60)**2 for m in spos]);cs=np.array([m['C_reference'] for m in spos]);c=np.average(cs,axis=0,weights=ww);xy=c_final(c);scatter=float(np.sqrt(np.average(np.sum((cs-c)**2,axis=1),weights=ww))*1.49);posmethod='native Sony centroids through existing C reference and V42 projection'
 else:
  c=platexy(plates['sony_radial'],p.xh_as,p.yh_as);vm=[m for m in measurements['Vixen'] if m['green_snr']>=5];res=[]
  for m in vm:
   row=metas['Vixen']['rows'][m['index']];fr=next(q for q in metas['Vixen']['frames'] if q['name']==m['frame']);off=json.loads((O/'S13_vixen_detection.json').read_text())['models'][m['frame']]['offset'];res.append(np.array(m['xy'])-fr['shift'][1:]-off-np.array(row['expected']))
  if res:c+=jac(plates['sony_radial'],p.xh_as,p.yh_as)@np.linalg.solve(jac(plates['r6_radial'],p.xh_as,p.yh_as),np.average(res,axis=0,weights=[m['green_snr']**2 for m in vm]))
  xy=c_final(c);scatter=float('nan');posmethod='existing native plates plus Vixen centroid residual; lower precision'
 x,y=xy;inside=15<x<10536 and 15<y<7491;coverage=bool(inside and source[int(round(y))-10:int(round(y))+11,int(round(x))-10:int(round(x))+11,3].min()>65000)
 if not coverage:continue
 fl=[];we=[];colors=[];ce=[]
 for tag,q in phot.items():
  f=np.array(q['RGB']);e=np.array(q['error']);scale=1 if tag=='Sony' else ratio;fl.append(f[1]*scale);we.append(1/max((e[1]*scale)**2,1e-9));bv=float(np.clip(r['BV'],0,1.8)) if np.isfinite(r['BV']) else .65;co=spec[tag]['spectral_coefficients'];prior=np.array([np.exp(co['R'][0]+co['R'][1]*bv),1,np.exp(co['B'][0]+co['B'][1]*bv)])*max(f[1],1e-9);priorerr=.35*prior
  # No catalogue photometric amplitude. Spectral prior regularizes only poorly measured native colour.
  ff=(f/e**2+prior/np.maximum(priorerr,1e-5)**2)/(1/e**2+1/np.maximum(priorerr,1e-5)**2);ff=np.maximum(ff,1e-6);wb=np.array(metas[tag]['frames'][0]['wb'])[:3];M=np.array(grid['runs'][tag.lower()]['matrix']);gain=np.array(grid['runs'][tag.lower()]['gain']);lin=(M@(ff*wb))*gain
  # Linear sRGB -> linear Adobe RGB (D65), retaining document profile.
  S=np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]]);AD=np.array([[.5767309,.1855540,.1881852],[.2973769,.6273491,.0752741],[.0270343,.0706872,.9911085]]);lin=np.linalg.solve(AD,S@lin);lin=np.maximum(lin,0);lin/=max(np.max(lin),1e-9);colors.append(lin);ce.append((f[1]/max(e[1],1e-9))**2)
 flux=float(np.average(fl,weights=we));error=float(1/np.sqrt(sum(we)));color=np.average(colors,axis=0,weights=ce);color/=color.max();rows.append(dict(TYC=r['TYC'],HIP=int(r['HIP']) if np.isfinite(r['HIP']) else None,V=r['V'],BV=r['BV'],x=float(x),y=float(y),sigma_final_px=1.5,FWHM_final_px=3.5322300675,position_scatter_px=scatter,position_method=posmethod,green_flux_sony_units=flux,green_error=error,native_photometry=phot,linear_AdobeRGB_chromaticity=color.tolist(),detection_support=dict(Sony_SNR=r.get('Sony_SNR'),Vixen_SNR=r.get('Vixen_SNR'),extra=bool(r.get('Sony_extra')))))
# Unresolved companions are the same photon support. Choose the measurement with smaller fractional error, do not add fitted flux twice.
merged=[];done=set()
for i,r in enumerate(rows):
 if i in done:continue
 near=[j for j,q in enumerate(rows) if j not in done and np.hypot(q['x']-r['x'],q['y']-r['y'])<2];best=min(near,key=lambda j:rows[j]['green_error']/max(rows[j]['green_flux_sony_units'],1e-9));q=dict(rows[best]);q['identifications']=[rows[j]['TYC'] for j in near];q['unresolved_blend']=len(near)>1;done.update(near);merged.append(q)
merged.sort(key=lambda r:r['V']);peakmax=.74;maxflux=max(r['green_flux_sony_units'] for r in merged)
for i,r in enumerate(merged):r['id']=f'S{i+1:02d}';r['display_peak']=float(peakmax*(max(r['green_flux_sony_units'],0)/maxflux)**.55);r['display_RGB_peak']=(np.array(r['linear_AdobeRGB_chromaticity'])**(1/2.19921875)*r['display_peak']).tolist()
rep=dict(stars=merged,distinct_sources=len(merged),catalogue_identifications=sum(len(r['identifications']) for r in merged),throughput_sony_over_vixen=ratio,throughput_train=ratios,throughput_held=held,output_PSF='Circular pixel-integrated Gaussian sigma 1.5 final pixels; photographic point-source regularization, no claim of resolved stellar surfaces or improved diffraction limit.',display_transfer='Peak=.74*(native measured green flux / brightest measured green flux)^.55, AdobeRGB encoded photographic amplitude. Catalogue retains linear flux and uncertainty. Display Gaussian shape is defined in document encoded coordinates.',source_coverage='Whole 21x21 footprint must have original composed alpha >65000, same canvas/FOV. No recovered stars are placed outside source coverage.');(O/'S22_final_catalog.json').write_text(json.dumps(rep,indent=2));pd.DataFrame([{k:v for k,v in r.items() if k not in ['native_photometry','detection_support']} for r in merged]).to_csv(O/'V65_estrelles.csv',index=False);print('FINAL',len(merged),'identifications',rep['catalogue_identifications'],flush=True)
