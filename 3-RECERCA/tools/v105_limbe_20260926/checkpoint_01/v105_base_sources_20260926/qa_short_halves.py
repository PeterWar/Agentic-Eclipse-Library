from pathlib import Path
import json,numpy as np,cv2
from scipy.ndimage import gaussian_filter,minimum_filter,gaussian_filter1d
O=Path('/private/tmp/v105_base_sources_20260926');ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026');SRC=Path('/private/tmp/v105_raw_pilot_20260926/no_floor_all67');CAU=ROOT/'4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'
meta=json.loads((SRC/'METADATA.json').read_text());orig=json.loads((CAU/'vixen_meta.json').read_text());Q=int(orig['Q']);y0,y1,x0,x1=meta['box_y0y1x0x1'];yy,xx=np.mgrid[y0:y1,x0:x1];h,w=yy.shape;N=np.load(SRC/'numerator.npy',mmap_mode='r');W=np.load(SRC/'weight.npy',mmap_mode='r');D=np.load(SRC/'distance_model.npy',mmap_mode='r');matrix=np.asarray(meta['matrix']);gain=np.asarray(meta['gain'])
old=np.load(ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz');cx,cy,rad=old['centre'];d=np.hypot(xx-cx,yy-cy)-rad;theta=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360;sector=(theta//30).astype(int);sil=np.load(ROOT/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz');rm=meta['radius_model'];phi={c:np.load(CAU/f'vixen_{c}_phi.npy',mmap_mode='r') for c in 'RGB'}
f=json.loads(Path('/private/tmp/v105_qa_20260926/factorial_frozen_corrections.json').read_text())['cases']['remove_phi']['16']['572A2969.CR3']['camera_channels'];gconst=np.array([f[c]['constant']['full_fit']['gain'] for c in 'RGB'])
def phi_crop(ar):
 ay0=max(0,y0//Q-1);ax0=max(0,x0//Q-1);ay1=min(ar.shape[0],(y1+Q-1)//Q+1);ax1=min(ar.shape[1],(x1+Q-1)//Q+1);a=np.asarray(ar[ay0:ay1,ax0:ax1],np.float32);b=cv2.resize(a,(a.shape[1]*Q,a.shape[0]*Q),interpolation=cv2.INTER_LINEAR);return b[y0-ay0*Q:y1-ay0*Q,x0-ax0*Q:x1-ax0*Q]
def smooth(x):
 z=np.clip((x-.6)/(2-.6),0,1);return z*z*(3-2*z)
groups={'alternate_A':[0,2,4,6],'alternate_B':[1,3,5,7],'early_A':[0,1,2,3],'late_B':[4,5,6,7]};acc={k:{'N':np.zeros((h,w,3)),'W':np.zeros((h,w,3)),'W2':np.zeros((h,w)),'NF':np.zeros((h,w),np.int16),'DRMIN':np.full((h,w),np.inf),'DRMAX':np.full((h,w),-np.inf)} for k in groups}
for j in range(8):
 frame=meta['frames'][j];oj=frame['original_index'];assert orig['frames'][oj]['name']==frame['name'];assert frame['name']==f'572A{2959+j}.CR3'
 dm=np.asarray(D[j],float);iy,ix=h//2,w-100;gx=(dm[iy,ix+1]-dm[iy,ix-1])/2;gy=(dm[iy+1,ix]-dm[iy-1,ix])/2;cxf=ix+x0-(dm[iy,ix]+rm)*gx;cyf=iy+y0-(dm[iy,ix]+rm)*gy;pa=np.degrees(np.arctan2(-(yy-cyf),xx-cxf))%360;dr=dm+(rm-rad)-np.interp(pa.ravel(),sil['pa'],sil['e'],period=360).reshape(h,w)
 nj=np.asarray(N[j],float)*np.exp(np.stack([phi_crop(phi[c][oj]) for c in 'RGB'],-1))*gconst;wj=np.asarray(W[j],float);valid=np.isfinite(nj).all(-1)&np.isfinite(wj).all(-1)&(wj>0).all(-1);gate=smooth(dr)*valid
 for k,inds in groups.items():
  if j not in inds:continue
  a=acc[k];a['N']+=np.where(valid[...,None],nj,0)*gate[...,None];a['W']+=np.where(valid[...,None],wj,0)*gate[...,None];a['W2']+=(wj[...,1]*gate)**2;a['NF']+=gate>0;a['DRMIN']=np.where(gate>0,np.minimum(a['DRMIN'],dr),a['DRMIN']);a['DRMAX']=np.where(gate>0,np.maximum(a['DRMAX'],dr),a['DRMAX'])
 print('frame',frame['name'],flush=True)
for k,a in acc.items():
 cam=np.divide(a['N'],a['W'],out=np.full_like(a['N'],np.nan),where=a['W']>0);a['E']=np.einsum('ij,hwj->hwi',matrix,cam*gain).astype('float32');a['NEFF']=np.divide(a['W'][...,1]**2,a['W2'],out=np.zeros_like(a['W2']),where=a['W2']>0);a['valid']=np.isfinite(a['E']).all(-1);np.savez_compressed(O/f'SHORT_HALF_{k}.npz',E=a['E'],W=a['W'].astype('float32'),NF=a['NF'],NEFF=a['NEFF'].astype('float32'),DRMIN=a['DRMIN'].astype('float32'),DRMAX=a['DRMAX'].astype('float32'),box=[y0,y1,x0,x1],frames=[meta['frames'][j]['name'] for j in groups[k]],gain_constant=gconst)
def hp(v,s):
 valid=np.isfinite(v)&(v>0);l=np.where(valid,np.log(np.maximum(np.nan_to_num(v),1e-12)),0);out=[]
 for sig in [s,2*s]:out.append(gaussian_filter(l,sig,truncate=4)/np.maximum(gaussian_filter(valid.astype(float),sig,truncate=4),1e-12))
 return out[0]-out[1]
def corr(x,y):return float(np.corrcoef(x,y)[0,1]) if len(x)>100 else None
def angular_only(v,z):
 if not z.any():return np.full_like(v,np.nan)
 ring=np.rint(np.hypot(xx-cx,yy-cy)).astype(int);n=np.bincount(ring[z]);su=np.bincount(ring[z],weights=v[z]);mean=np.divide(su,n,out=np.zeros_like(su),where=n>0);return v-mean[np.minimum(ring,len(mean)-1)]
report={'scope':'4+4 conditional consistency only; shared dark/flat/registration/k/matrix and pooled calibration, NOT independent train or absolute validation','short_camera_gain':gconst.tolist(),'groups':{k:[meta['frames'][j]['name'] for j in inds] for k,inds in groups.items()},'corrections':'noFloor; undo frozen phi per source; keep additive offsets b; fixed common saturation weights and physical ramp0.6..2','quality_threshold_warning':'NF counts nonzero partial weights; green full frame weight=2e; NF>=3 and Wg>=1.5e do not certify SNR or pure corona','pairs':{}}
for ka,kb in [('alternate_A','alternate_B'),('early_A','late_B')]:
 a,b=acc[ka],acc[kb];common=a['valid']&b['valid']&(a['NF']>=3)&(b['NF']>=3);L=lambda ar:(ar[...,0]+2*ar[...,1]+ar[...,2])/4;AL,BL=L(a['E']),L(b['E']);rows=[]
 for lo,hi in [(0,2),(2,10),(10,25),(25,100)]:
  for sec in [-1,2,3,4,7,8]:
   z=common&(d>=lo)&(d<hi);z&=(sector==sec) if sec>=0 else True;n=int(z.sum());row={'band_presentation':[lo,hi],'sector_deg':'all' if sec<0 else [sec*30,(sec+1)*30],'n':n}
   if n:
    for name,aa,bb in [('G',a['E'][...,1],b['E'][...,1]),('L',AL,BL)]:
     rel=(aa[z]-bb[z])/((aa[z]+bb[z])/2);row[name]={'median_half_difference_pct':float(np.median(rel)*100),'robust_half_difference_sigma_pct':float(1.4826*np.median(abs(rel-np.median(rel)))*100),'median_of_halves_pct':[float(np.median(aa[z])),float(np.median(bb[z]))]}
    row['NEFF_median']=[float(np.median(v['NEFF'][z])) for v in [a,b]];row['max_source_distance_p10_median']=[np.quantile(v['DRMAX'][z],[.1,.5]).tolist() for v in [a,b]]
   rows.append(row)
 hp_rows=[]
 for s in [2,4]:
  for name,aa,bb in [('G',a['E'][...,1],b['E'][...,1]),('L',AL,BL)]:
   safe=minimum_filter((common&(a['DRMIN']>2)&(b['DRMIN']>2)&(aa>0)&(bb>0)).astype('uint8'),size=16*s+1,mode='constant',cval=0)>0
   ah,bh=hp(aa,s),hp(bb,s);base=safe&(d>=10)&(d<150);ar,br=angular_only(ah,base),angular_only(bh,base)
   for lo,hi in [(0,2),(2,10),(10,25),(25,100)]:
    for sec in [-1,2,3,4,7,8]:
     z=safe&(d>=lo)&(d<hi);z&=(sector==sec) if sec>=0 else True;n=int(z.sum());hp_rows.append({'sigma':s,'channel':name,'band_presentation':[lo,hi],'sector_deg':'all' if sec<0 else [sec*30,(sec+1)*30],'n':n,'rho':corr(ah[z],bh[z]),'rho_radial_mean_removed':corr(ar[z],br[z])})
 report['pairs'][ka+'__'+kb]={'point_consistency':rows,'strict_guard_highpass':hp_rows};print(ka,kb,[(r['sigma'],r['channel'],r['rho_radial_mean_removed']) for r in hp_rows if r['band_presentation']==[25,100] and r['sector_deg']=='all'],flush=True)
(O/'SHORT_HALVES_QA.json').write_text(json.dumps(report,indent=2));print('COMPLETE',flush=True)
