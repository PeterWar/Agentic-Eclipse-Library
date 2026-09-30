"""Freeze photographic residual; linear source-band differential transport.
Re-evaluating Camera Raw noise reduction failed C4. This distinct branch keeps
the user's saved rendering and transports only a source delta through a fixed
empirical band response; it does not pretend to reproduce unknown CR sliders.
"""
from b2_judge import *
from PIL import Image
claim();old=np.load(OUT/'arrays/V53_moon_rgb.npy').astype('int32')
pre=np.load(SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy').mean(-1)
P,_=polar(pre);Q,_=polar(old.mean(-1));A=band(P,40,64);B=band(Q,40,64)
train=np.broadcast_to((rr[:,None]>=100)&(rr[:,None]<435),(len(rr),nt))&((np.arange(nt)[None,:]//120)%2==0)
test=np.broadcast_to((rr[:,None]>=100)&(rr[:,None]<435),(len(rr),nt))&~train
# Single global photometric slope, no sector model or source selection.
beta=float(np.sum(A[train]*B[train])/np.sum(A[train]**2));assert 0<beta<2
save('D1_design.json',dict(method=__doc__,beta=beta,fit='V53 versus preCR40-64px tangential Fourier band; even30deg sectors,r100-435; one least-squares coefficient through zero; no Sony fit',
    heldout_r=corr(A,B,test),heldout_residual_rms=float(np.std((B-beta*A)[test])),
    C_branch='REJECTED: native paired40-64 injection ranged0.747-1.131; no product published from it.',
    acceptance='Frozen original gate: photographic retention triples (not independent) retained; paired unseen source injection0.90-1.10; matched V53 limb diagnostics, exact geometry/masks, native Photoshop QA.'))
sd=np.load(OUT/'arrays/B3_preCR_delta.npy').mean(-1);mask=np.load(OUT/'arrays/V53_lunar_mask.npy');delta=np.rint(beta*sd).astype('int32');delta[mask==0]=0
new=old+delta[...,None];assert new.min()>=0 and new.max()<=65535;new=new.astype('uint16')
np.save(OUT/'arrays/D1_candidate_rgb.npy',new)
# Original saved CameraRaw response plus transported SOURCE injection delta.
# Same unseen eight-angle field from C1, no changes to its seed or amplitude.
ib=np.load(OUT/'arrays/C4_injection_native_responses.npz')['baseline']
baseinj=np.load(OUT/'arrays/C1_blind_base.npy').astype('int32');candidinj=np.load(OUT/'arrays/C1_blind_candidate.npy').astype('int32')
did=(candidinj-baseinj).mean(-1)-sd
response=ib+beta*did
Ab=band(map_coordinates(ib,co,order=3),40,64);Bb=band(map_coordinates(response,co,order=3),40,64)
inj=[]
for a,b in [(100,300),(300,370),(370,435),(435,449)]:
    for sec in range(12):
        m=np.broadcast_to((rr[:,None]>=a)&(rr[:,None]<b),(len(rr),nt))&((np.arange(nt)[None,:]//120)==sec)
        x=Ab[m];y=Bb[m];g=float(x@y/max(x@x,1e-30));inj.append(dict(radius=[a,b],sector=sec,transfer=g,r=corr(Ab,Bb,m),pass_gate=.9<=g<=1.1))
save('D1_injection.json',dict(rows=inj,all_pass=all(v['pass_gate'] for v in inj),limits='Empirical differential display model with the saved CR residual fixed, not a new raw-to-display reconstruction. Native response of baseline injection measured, not assumed.'))
print('D1 beta',beta,'injection',min(v['transfer'] for v in inj),max(v['transfer'] for v in inj),'all',all(v['pass_gate'] for v in inj),flush=True)
