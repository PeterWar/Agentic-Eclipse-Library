"""Bounded causal ablation: least-squares monotone veil vs running maximum.

This replaces the positive running-envelope bias of historical S8 with its
weighted least-squares isotonic estimate. All other controls remain historical.
No external image is used to construct the candidate. No Photoshop mutation.
"""
from pathlib import Path
import numpy as np,json,sys
from scipy.ndimage import gaussian_filter1d,map_coordinates,median,gaussian_filter
from scipy.optimize import isotonic_regression
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/earthshine_taca_source_20260914';C=R/'research/tools/earthshine_v50_temporal_20260912/cau'
sys.path.insert(0,str(R/'research/tools/earthshine_broad_lroc_20260914'))
from s8_operator import s8_eval
G=np.load(C/'lun_ch1_roi.npy').astype(float);edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
y,x=np.mgrid[:1400,:1400];r=np.hypot(x-699.568111973117,y-699.6475341408573);ang=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi)
f=gaussian_filter1d(edge,3,mode='wrap');d=r-np.interp(ang,np.linspace(0,2*np.pi,1441),np.r_[f,f[0]]);sec=(ang*72/(2*np.pi)).astype(int)
dc=np.arange(-299,3,2.);ib=np.floor((d+300)/2).astype(int);v=(ib>=0)&(ib<len(dc));labels=sec[v]*len(dc)+ib[v];counts=np.bincount(labels,minlength=72*len(dc)).reshape(72,-1)
dc1=np.arange(-69.5,1,1.);ib1=np.floor(d+70).astype(int);v1=(ib1>=0)&(ib1<len(dc1));labels1=sec[v1]*len(dc1)+ib1[v1];counts1=np.bincount(labels1,minlength=72*len(dc1)).reshape(72,-1)
si=(ang*72/(2*np.pi)-.5)%72;di=np.interp(d,dc,np.arange(len(dc)));di1=np.interp(d,dc1,np.arange(len(dc1)))
def evaluate(g):
 P=median(g[v],labels=labels,index=np.arange(72*len(dc))).reshape(72,-1);P[counts<12]=np.nan
 for k in range(72):
  ok=np.isfinite(P[k]);P[k]=np.interp(dc,dc[ok],P[k,ok])
 base=np.median(P[:,(dc>=-260)&(dc<=-200)],axis=1)
 E=gaussian_filter1d(gaussian_filter1d(P-base[:,None],1.5,axis=1),2,axis=0,mode='wrap')
 W=np.zeros_like(E);fit=dc>=-260
 for k in range(72):W[k,fit]=np.maximum(isotonic_regression(E[k,fit],weights=np.maximum(counts[k,fit],1)).x,0)
 W*=np.clip((dc+260)/60,0,1)
 wf=map_coordinates(np.r_[W,W[:1]],[si,di],order=1,mode='nearest');wf[d<-300]=0
 Ln=np.clip(g-wf,0,65535)
 rr=median(Ln[v1],labels=labels1,index=np.arange(72*len(dc1))).reshape(72,-1)-base[:,None]
 rr[counts1<6]=0;rr=gaussian_filter1d(gaussian_filter1d(rr,1,axis=0,mode='wrap'),1,axis=1)
 tap=np.clip((dc1+70)/30,0,1);rr*=tap*tap*(3-2*tap)
 rf=map_coordinates(np.r_[rr,rr[:1]],[si,di1],order=1,mode='nearest');rf[(d<-70)|(d>1)]=0
 wf=np.maximum(wf+rf,0)
 return np.clip(g-wf,0,65535),wf

protocol=dict(hypothesis='Running maximum can propagate a bright lunar feature into excessive outward subtraction. Weighted isotonic regression removes the envelope bias, but the physical veil assumption still needs testing.',candidate='Replace only the profile envelope with weighted isotonic least squares and correct the known half-sector coordinate. No tuning after judges.',judges='The eight same broad signed injections and exact external references used before; no reference pixels construct candidate.',promotion='Requires 0.90-1.10 full refit transfer for every broad injection, no new limb seam, and improvement with fixed reference comparison coefficients; otherwise reject.')
(O/'A3_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
before,w=s8_eval(G,edge);after,wa=evaluate(G)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);valid=r<435;guard=(x>=500)&(x<773)&(y>=852)&(y<1098)
rep=dict(protocol=protocol,delta_mark_DN16=np.percentile((after-before)[mark],[0,50,100]).tolist(),injections=[])
for cx,cy,sig in [(636,975,50),(636,975,90),(1000,680,50),(500,440,50)]:
 e=np.exp(-((x-cx)**2+(y-cy)**2)/(2*sig**2));use=(e>.05)&valid
 for amplitude in [-200,200]:
  z,_=evaluate(G+amplitude*e);response=(z-after)/amplitude;gain=float(np.sum(response[use]*e[use])/np.sum(e[use]**2))
  row=dict(center=[cx,cy],sigma=sig,amplitude=amplitude,refit_gain=gain,pass_090_110=bool(.9<=gain<=1.1));rep['injections'].append(row);print(row,flush=True)
photo=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float);delta=w-wa;candidate=photo+delta[...,None]
rep['candidate_minmax']=[float(candidate.min()),float(candidate.max())];rep['all_injections_pass']=all(q['pass_090_110'] for q in rep['injections'])
refs=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz');domain=r<420;good=(r>80)&(r<390)&~guard
def smooth(a,s):return gaussian_filter(a*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
rep['diagnostic_judges']=[]
for sig in [(8,32),(16,64),(32,96)]:
 p=photo.mean(-1);n=candidate.mean(-1);p=smooth(p,sig[0])-smooth(p,sig[1]);n=smooth(n,sig[0])-smooth(n,sig[1])
 for key in ['DHS530','DHS400','LROC']:
  ref=smooth(refs[key],sig[0])-smooth(refs[key],sig[1]);gain=np.cov(p[good],ref[good],bias=True)[0,1]/np.var(p[good]);offset=ref[good].mean()-gain*p[good].mean();sd=ref[good].std()
  item=dict(sigmas=sig,reference=key,coefficients_fixed_from_original=[float(gain),float(offset)])
  for name,a in [('before',p),('after',n)]:
   e=(gain*a+offset-ref)/sd;item[name]=dict(mark_bias=float(e[mark].mean()),mark_rmse=float(np.sqrt(np.mean(e[mark]**2))),control_rmse=float(np.sqrt(np.mean(e[good]**2))))
  rep['diagnostic_judges'].append(item);print(item,flush=True)
rep['status']='REJECTED_TRANSFER' if not rep['all_injections_pass'] else 'OTHER_GATES_PENDING'
np.savez_compressed(O/'arrays/A3_isotonic_candidate_NOT_APPROVED.npz',rgb=candidate.astype('float32'),delta=delta.astype('float32'))
(O/'A3_isotonic_result.json').write_text(json.dumps(rep,indent=2)+'\n')
pan=Image.new('RGB',(2000,1040),'#202020');draw=ImageDraw.Draw(pan)
for j,(name,a) in enumerate([('V68',photo),('ISOTONIC PILOT - NOT APPROVED',candidate)]):
 im=np.uint8(np.clip((a.mean(-1)-6500)/8000,0,1)*255+.5);im[r>460]=0
 pic=Image.fromarray(im).convert('RGB');dd=ImageDraw.Draw(pic);dd.rectangle([550,902,723,1048],outline='#eead35',width=2)
 pan.paste(pic.crop((200,200,1200,1200)),(j*1000,40));draw.text((j*1000+10,12),name+' | fixed diagnostic stretch',fill='white')
pan.save(O/'vistes/A3_isotonic_whole_moons_NOT_APPROVED.png');print(rep['status'],flush=True)
