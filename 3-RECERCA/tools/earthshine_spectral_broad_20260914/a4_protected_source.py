"""Unpromoted counterfactual: protect measured lunar texture inside S8.

Template from calibrated Vixen G, no atlas or Sony pixels. Response is learned
on alternating sectors at 32-64 px, then frozen for the declared 24-256 px
range. This tests whether a source template stops broad texture absorption.
Angular filtering cannot establish isotropic resolution; no PSB is generated.
"""
from pathlib import Path
import json,sys,numpy as np
from scipy.ndimage import map_coordinates,gaussian_filter,distance_transform_edt
from scipy.optimize import nnls
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_SPECTRAL_BROAD_20260914'
sys.path.insert(0,str(R/'research/tools/earthshine_broad_lroc_20260914'))
from s8_operator import s8_eval
N=1400;CX=699.568111973117;CY=699.6475341408573
y,x=np.mgrid[:N,:N];rad=np.hypot(x-CX,y-CY);ang=np.arctan2(y-CY,x-CX)%(2*np.pi)
edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');er=np.interp(ang,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);physical=rad<er
src=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean'].astype(float)
P=np.load(R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_ch1_roi.npy').astype(float)
rr=np.arange(.5,460.,.5);th=np.arange(1440)*2*np.pi/1440;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
freq=np.fft.rfftfreq(1440)[None,:]*1440/(2*np.pi*rr[:,None]);ps=map_coordinates(src,co,order=1,mode='nearest');pp=map_coordinates(P,co,order=1,mode='nearest')
def transfer(lo,hi):
 a=np.clip((freq-1/(hi*1.25))/(1/hi-1/(hi*1.25)),0,1);b=np.clip((freq-1/lo)/(1/(lo*.8)-1/lo),0,1)
 return (.5-.5*np.cos(np.pi*a))*(.5+.5*np.cos(np.pi*b))
def filt(a,lo,hi):return np.fft.irfft(np.fft.rfft(a,axis=1)*transfer(lo,hi),n=1440,axis=1)
S=filt(ps,32,64);T=filt(pp,32,64);u=(rr[:,None]/460)**2;basis=np.broadcast_to(np.stack([(1-u)**2,2*u*(1-u),u*u],-1),(*S.shape,3))
px=co[1];py=co[0];guard=(px>=500)&(px<773)&(py>=852)&(py<1098);fit=(rr[:,None]>60)&(rr[:,None]<410)&((np.arange(1440)[None,:]//120)%2==0)&~guard;hold=(rr[:,None]>60)&(rr[:,None]<410)&((np.arange(1440)[None,:]//120)%2==1)&~guard
A=S[...,None]*basis;cf,_=nnls(A[fit],T[fit]);beta=np.sum(basis*cf,axis=-1)
Lpolar=filt(ps,24,256)*beta
# Only measured image values contribute; template outside lunar support zero.
L=map_coordinates(np.c_[Lpolar,Lpolar[:,:1]],[(rad-.5)/.5,ang*1440/(2*np.pi)],order=1,mode='nearest');L[~physical]=0
protocol=dict(method=__doc__,response_basis='Nonnegative degree2 Bernstein r squared; 32-64px, r60-410, even sectors, orange guard excluded',protected_band_px=[24,256],filter='Raised cosine skirts at .8*lo and 1.25*hi, angular radius-dependent physical arc wavelengths',limitations=['Template shares unknown broad optical scatter; this pilot alone cannot identify true albedo','No source-resolution or calibration claim','No publication before isotropic transfer, cross-sensor and contour retention gates'])
(O/'A4_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
before,_=s8_eval(P,edge);after,_=s8_eval(P-L,edge);after+=L
delta=after-before;delta[~physical]=0
photo=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float);candidate=photo+delta[...,None]
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);g=(x>=500)&(x<773)&(y>=852)&(y<1098);domain=rad<420;good=(rad>80)&(rad<390)&~g
def sm(a,s):return gaussian_filter(a*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
report=dict(protocol=protocol,coefficients=cf.tolist(),response_heldout_correlation=float(np.corrcoef(T[hold],(A@cf)[hold])[0,1]),delta_mark=np.percentile(delta[mark],[0,50,100]).tolist(),delta_contour=np.percentile(delta[(rad>435)&physical],[0,50,100]).tolist(),clipped_visible=int(((candidate.min(-1)<0)|(candidate.max(-1)>65535))[physical].sum()),comparisons=[],status='COUNTERFACTUAL_NOT_APPROVED')
refs=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz')
for sig in [(8,32),(16,64),(32,96)]:
 a=sm(photo.mean(-1),sig[0])-sm(photo.mean(-1),sig[1]);b=sm(candidate.mean(-1),sig[0])-sm(candidate.mean(-1),sig[1])
 for key in ['DHS530','DHS400','LROC']:
  q=sm(refs[key],sig[0])-sm(refs[key],sig[1]);gain=np.cov(a[good],q[good],bias=True)[0,1]/np.var(a[good]);offset=q[good].mean()-gain*a[good].mean();sd=q[good].std();row=dict(sigmas=sig,reference=key)
  for tag,v in [('before',a),('after',b)]:
   d=(gain*v+offset-q)/sd;row[tag]=dict(mark_rms=float(np.sqrt(np.mean(d[mark]**2))),mark_bias=float(np.mean(d[mark])),control_rms=float(np.sqrt(np.mean(d[good]**2))))
  report['comparisons'].append(row);print(row,flush=True)
np.savez_compressed(O/'arrays/A4_protected_source_NOT_APPROVED.npz',candidate=candidate.astype('float32'),delta=delta.astype('float32'),template=L.astype('float32'))
(O/'A4_protected_source.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['comparisons','protocol']},flush=True)
pan=Image.new('RGB',(2000,1040),'#202020');draw=ImageDraw.Draw(pan)
for j,(name,a) in enumerate([('V68',photo),('SOURCE PROTECTION PILOT - NOT APPROVED',candidate)]):
 im=np.uint8(np.clip((a.mean(-1)-6500)/8000,0,1)*255+.5);im[rad>460]=0;pic=Image.fromarray(im).convert('RGB');ImageDraw.Draw(pic).rectangle([550,902,723,1048],outline='#eead35',width=2)
 pan.paste(pic.crop((200,200,1200,1200)),(j*1000,40));draw.text((j*1000+10,12),name+' | fixed diagnostic stretch',fill='white')
pan.save(O/'vistes/A4_protected_source_NOT_APPROVED.png')
