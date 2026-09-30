"""S8: source protection belongs to the broad estimator, not the limb fit.

A4 incorrectly transported its linear source template through the final limb
normalization, where its photographic response is not valid. Here the existing
last-70px operation sees the original photographic signal and baseline, exactly
as before. This adds no radius, mask or geometry, and must reproduce S8 at L=0.
"""
from pathlib import Path
import ast,json,numpy as np
from scipy.ndimage import gaussian_filter1d,map_coordinates,median,gaussian_filter
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914'
METHOD=__doc__
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_SPECTRAL_BROAD_20260914'
source=R/'research/tools/earthshine_broad_lroc_20260914/s8_operator.py';text=source.read_text();exec(compile(text,str(source),'exec'))
protected=text.replace('def s8_eval(G,edge,centered=False):','def evaluate(G,edge,L,centered=False):')
protected=protected.replace('P=median(G[valid],labels=labels,index=np.arange(72*len(dc))).reshape(72,-1)','P=median((G-L)[valid],labels=labels,index=np.arange(72*len(dc))).reshape(72,-1)\n    Porig=median(G[valid],labels=labels,index=np.arange(72*len(dc))).reshape(72,-1)')
protected=protected.replace('Ln=np.clip(G-wf,0,65535)','base=np.median(Porig[:,(dc>=-260)&(dc<=-200)],axis=1)\n    Ln=np.clip(G-wf,0,65535)')
exec(compile(protected,'separate_limb_operator','exec'))
P=np.load(R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_ch1_roi.npy').astype(float);edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
L=np.load(O/'arrays/A4_protected_source_NOT_APPROVED.npz')['template'].astype(float)
before,_=s8_eval(P,edge);null,_=evaluate(P,edge,np.zeros_like(P));assert np.max(abs(null-before))==0
after,_=evaluate(P,edge,L);delta=after-before
y,x=np.mgrid[:1400,:1400];rad=np.hypot(x-699.568111973117,y-699.6475341408573);ang=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi);physical=rad<np.interp(ang,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);delta[~physical]=0
photo=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float);candidate=photo+delta[...,None]
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098);domain=rad<420;good=(rad>80)&(rad<390)&~guard
def sm(a,s):return gaussian_filter(a*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
rep=dict(method=METHOD,null_max_error=0,delta_mark=np.percentile(delta[mark],[0,50,100]).tolist(),delta_contour=np.percentile(delta[(rad>435)&physical],[0,50,100]).tolist(),clipped_visible=int(((candidate.min(-1)<0)|(candidate.max(-1)>65535))[physical].sum()),comparisons=[],status='CANDIDATE_GATES_PENDING')
refs=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz')
for sig in [(8,32),(16,64),(32,96)]:
 a=sm(photo.mean(-1),sig[0])-sm(photo.mean(-1),sig[1]);b=sm(candidate.mean(-1),sig[0])-sm(candidate.mean(-1),sig[1])
 for key in ['DHS530','DHS400','LROC']:
  q=sm(refs[key],sig[0])-sm(refs[key],sig[1]);gain=np.cov(a[good],q[good],bias=True)[0,1]/np.var(a[good]);offset=q[good].mean()-gain*a[good].mean();sd=q[good].std();row=dict(sigmas=sig,reference=key)
  for tag,v in [('before',a),('after',b)]:
   d=(gain*v+offset-q)/sd;row[tag]=dict(mark_rms=float(np.sqrt(np.mean(d[mark]**2))),mark_bias=float(np.mean(d[mark])),control_rms=float(np.sqrt(np.mean(d[good]**2))))
  rep['comparisons'].append(row)
np.savez_compressed(O/'arrays/A6_separate_limb_NOT_APPROVED.npz',candidate=candidate.astype('float32'),delta=delta.astype('float32'))
(O/'A6_separate_limb.json').write_text(json.dumps(rep,indent=2)+'\n');print(rep,flush=True)
