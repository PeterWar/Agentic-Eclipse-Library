"""Conditional new-band transfer plus inherited native-response overlap test.
Saved CameraRaw is not replayed. New24-40 response uses frozen fitted beta.
The40-64 overlap additionally uses the actual earlier native CameraRaw paired
response and all V54/V55 additive corrections; no reset of cumulative gain.
"""
from common import *
from scipy.ndimage import map_coordinates
claim();z=np.load(OUT/'arrays/R8_operator.npz');confidence=z['confidence'];pm=z['mask_polar'];H=z['H'];beta=float(z['beta']);strength=float(z['strength']);rr=z['rr'];nt=H.shape[1]*2-2;r,t=geometry();th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*np.maximum(rr[:,None],.25));visible=(np.load(OLD54/'arrays/V53_lunar_mask.npy')>0)&(np.load(OLD54/'arrays/V53_lunar_alpha.npy')>0);old=np.load(OLD/'arrays/D10_candidate_rgb.npy').astype(np.int32);new=np.load(OUT/'arrays/R8_candidate_rgb.npy').astype(np.int32);delta=np.load(OUT/'arrays/R8_delta.npy');assert np.array_equal(new,old+delta[...,None])
save('R11_protocol.json',dict(method=__doc__,seed=560913,new_band=[24,40],periods=[25,28,31,34,37,39],gate=[.9,1.1],radii=[[100,300],[300,370],[370,435],[435,449]],sectors=12,cumulative='Original actualC4 native40-64 response ib; add originalV54 empirical differential and currentR8 new-band increment. V55/R5 fixed additive detector corrections are common-scene invariant, qualified separately.',limits='New24-40 injection is conditional on empirical beta, not a native RAW-to-CameraRaw measurement. Original40-64 cumulative control reuses measured native baseline. Neither proves new resolution.'))
def pol(a):return map_coordinates(a,co,order=3,mode='nearest')
def cart(a):
 pad=np.c_[a[:,-2:],a,a[:,:2]];return map_coordinates(pad,[np.minimum(r/.5,len(rr)-1),t*nt/(2*np.pi)+2],order=3,mode='nearest')
def op(a):
 band=np.fft.irfft(np.fft.rfft(pol(a),axis=1)*H,n=nt,axis=1);out=beta*cart(strength*confidence*band*pm);out[~visible]=0;return out
def judge(a,b,lo,hi,j):
 hh=(freq>=1/hi)&(freq<=1/lo);A=np.fft.irfft(np.fft.rfft(pol(a),axis=1)*hh,n=nt,axis=1);B=np.fft.irfft(np.fft.rfft(pol(b),axis=1)*hh,n=nt,axis=1);rows=[]
 for r0,r1 in [(100,300),(300,370),(370,435),(435,449)]:
  for sec in range(12):
   m=np.broadcast_to((rr[:,None]>=r0)&(rr[:,None]<r1),A.shape)&(np.arange(nt)[None,:]//240==sec);x=A[m];y=B[m];gain=float(x@y/max(x@x,1e-30));rows.append(dict(injection=j,radius=[r0,r1],sector=sec,transfer=gain,pass_gate=.9<=gain<=1.1))
 return rows
y,x=np.mgrid[:N,:N];rng=np.random.default_rng(560913);rows=[]
for j,period in enumerate([25,28,31,34,37,39]):
 ang=rng.uniform(0,2*np.pi);phase=rng.uniform(0,2*np.pi);q=16*np.sin(2*np.pi*((x-CX)*np.cos(ang)+(y-CY)*np.sin(ang))/period+phase);q[~visible]=0;ib=beta*q;response=ib+op(q);rows+=judge(ib,response,24,40,j)
pre=np.load(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy');baseinj=np.load(OLD54/'arrays/C1_blind_base.npy').astype(float);candin=np.load(OLD54/'arrays/C1_blind_candidate.npy').astype(float);q=(baseinj-pre).mean(-1);ib=np.load(OLD54/'arrays/C4_injection_native_responses.npz')['baseline'];oldbeta=json.loads((OLD54/'D1_design.json').read_text())['beta'];sd=np.load(OLD54/'arrays/B3_preCR_delta.npy').mean(-1);v54response=ib+oldbeta*((candin-baseinj).mean(-1)-sd);totalresponse=v54response+op(q);cumulative=judge(ib,totalresponse,40,64,'V53_native_to_candidate');previous=judge(ib,v54response,40,64,'V53_native_to_V55')
np.savez_compressed(OUT/'arrays/R11_injections.npz',native_baseline=ib,prior_response=v54response,cumulative_response=totalresponse,source_injection=q)
rep=dict(new_band=rows,cumulative_overlap=cumulative,previous_overlap=previous,all_pass=all(q['pass_gate'] for q in rows+cumulative),new_range=[min(q['transfer'] for q in rows),max(q['transfer'] for q in rows)],cumulative_range=[min(q['transfer'] for q in cumulative),max(q['transfer'] for q in cumulative)],limits=__doc__);save('R11_photo_injections.json',rep);print('PHOTO INJECTIONS',rep['new_range'],rep['cumulative_range'],rep['all_pass'],flush=True)
