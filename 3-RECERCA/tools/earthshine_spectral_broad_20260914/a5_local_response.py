"""New exploratory response model after A4 extrapolated linear gain at the limb.

Estimate a smooth local photographic derivative from 32-64px measured texture,
using even sectors and no marked pixels. The frozen global response supplies
the prior inside the excluded region; local data update it elsewhere. This is a
new candidate with unchanged reference tests, not a relaxation of A4 gates.
"""
from pathlib import Path
import ast,json,numpy as np
from scipy.ndimage import convolve1d
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914';T=Path(__file__).parent
# Load only read/geometry/filter definitions; stop before the old fit/candidate.
tree=ast.parse((T/'a4_protected_source.py').read_text());body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='S' for t in node.targets):break
 body.append(node)
exec(compile(ast.Module(body=body,type_ignores=[]),str(T/'a4_protected_source.py'),'exec'))
P0=P.copy();source=src.copy();s=filt(ps,32,64);p=filt(pp,32,64)
def to_cart(a):return map_coordinates(np.c_[a,a[:,:1]],[(rad-.5)/.5,ang*1440/(2*np.pi)],order=1,mode='nearest')
S=to_cart(s);Q=to_cart(p);Sb=to_cart(filt(ps,24,256))
guard=(x>=500)&(x<773)&(y>=852)&(y<1098);even=((ang/(np.pi/6)).astype(int)%2)==0
fit=physical&~guard&even;hold=physical&~guard&~even
# Cubic B-spline compact kernel, support +/-64px. No spatial image resampling.
t=np.arange(-64,65)/32;a=np.abs(t);ker=np.where(a<1,(4-6*a*a+3*a**3)/6,np.where(a<2,(2-a)**3/6,0));ker/=ker.sum()
def local(v):return convolve1d(convolve1d(v,ker,axis=0,mode='constant'),ker,axis=1,mode='constant')
den=local(S*S*fit);mass=local(fit.astype(float));support=(mass>.001)
cf=np.array(json.loads((O/'A4_protected_source.json').read_text())['coefficients']);u=(rad/460)**2;prior=cf[0]*(1-u)**2+cf[1]*2*u*(1-u)+cf[2]*u*u
# Conditional source uncertainty from disjoint source stacks, frozen before
# inspecting this candidate. It regularizes the response, never image pixels.
zz=np.load(O/'arrays/A2_local_polar.npz');pp0=zz['fit'][...,1];pp1=zz['test'][...,1];rf=zz['r'];ff=np.fft.rfftfreq(1440)[None,:]*1440/(2*np.pi*rf[:,None]);hh=(ff>=1/64)&(ff<=1/32)
nd=np.fft.irfft(np.fft.rfft(pp0-pp1,axis=1)*hh,n=1440,axis=1)/2;noise=float(np.var(nd[rf<190]))
beta=np.maximum(local(S*Q*fit)+noise*prior,0)/np.maximum(den+noise,1e-12)
L=beta*Sb;L[~physical]=0
protocol=dict(method=__doc__,template_source='Vixen Gclean',band_px=[24,256],response_fit_band=[32,64],response_kernel='Cubic B spline +-64px; finite support; global A4 prior where data absent',source_noise_ridge=noise,fit='physical support/even sectors/outside mark+50guard; positive derivative',limits=['Broad optical scatter is not identified by the template','Reference comparisons remain exploratory after multiple candidate trials','No radius-dependent mask or image geometry changes'])
(O/'A5_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
before,_=s8_eval(P,edge);after,_=s8_eval(P-L,edge);after+=L;delta=after-before;delta[~physical]=0
photo=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float);candidate=photo+delta[...,None]
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);domain=rad<420;good=(rad>80)&(rad<390)&~guard
def sm(a,s):return gaussian_filter(a*domain,s)/np.maximum(gaussian_filter(domain.astype(float),s),1e-10)
report=dict(protocol=protocol,response_heldout_correlation=float(np.corrcoef(Q[hold],(beta*S)[hold])[0,1]),mark_template_support_fraction=float(support[mark].mean()),beta_mark=np.percentile(beta[mark],[0,50,100]).tolist(),delta_mark=np.percentile(delta[mark],[0,50,100]).tolist(),delta_contour=np.percentile(delta[(rad>435)&physical],[0,50,100]).tolist(),clipped_visible=int(((candidate.min(-1)<0)|(candidate.max(-1)>65535))[physical].sum()),comparisons=[],status='COUNTERFACTUAL_NOT_APPROVED')
refs=np.load(R/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz')
for sig in [(8,32),(16,64),(32,96)]:
 a=sm(photo.mean(-1),sig[0])-sm(photo.mean(-1),sig[1]);b=sm(candidate.mean(-1),sig[0])-sm(candidate.mean(-1),sig[1])
 for key in ['DHS530','DHS400','LROC']:
  q=sm(refs[key],sig[0])-sm(refs[key],sig[1]);gain=np.cov(a[good],q[good],bias=True)[0,1]/np.var(a[good]);offset=q[good].mean()-gain*a[good].mean();sd=q[good].std();row=dict(sigmas=sig,reference=key)
  for tag,v in [('before',a),('after',b)]:
   d=(gain*v+offset-q)/sd;row[tag]=dict(mark_rms=float(np.sqrt(np.mean(d[mark]**2))),mark_bias=float(np.mean(d[mark])),control_rms=float(np.sqrt(np.mean(d[good]**2))))
  report['comparisons'].append(row);print(row,flush=True)
np.savez_compressed(O/'arrays/A5_local_response_NOT_APPROVED.npz',candidate=candidate.astype('float32'),delta=delta.astype('float32'),template=L.astype('float32'),beta=beta.astype('float32'))
(O/'A5_local_response.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['comparisons','protocol']},flush=True)
pan=Image.new('RGB',(2000,1040),'#202020');draw=ImageDraw.Draw(pan)
for j,(name,a) in enumerate([('V68',photo),('LOCAL RESPONSE PILOT - NOT APPROVED',candidate)]):
 im=np.uint8(np.clip((a.mean(-1)-6500)/8000,0,1)*255+.5);im[rad>460]=0;pic=Image.fromarray(im).convert('RGB');ImageDraw.Draw(pic).rectangle([550,902,723,1048],outline='#eead35',width=2)
 pan.paste(pic.crop((200,200,1200,1200)),(j*1000,40));draw.text((j*1000+10,12),name+' | fixed diagnostic stretch',fill='white')
pan.save(O/'vistes/A5_local_response_NOT_APPROVED.png')
