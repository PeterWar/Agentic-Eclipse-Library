from pathlib import Path
import numpy as np,json,hashlib
from s8_operator import s8_eval
R=Path.cwd();O=R/'output/earthshine_broad_lroc_20260914';C=R/'research/tools/earthshine_v50_temporal_20260912/cau'
G=np.load(C/'lun_ch1_roi.npy').astype(float);edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
before,w=s8_eval(G,edge);after,wc=s8_eval(G,edge,True)
stored=np.load(C/'lun_rgb_vel_u16.npy');oldw=np.load(C/'vel_field.npy');assert np.array_equal(np.rint(before).astype('uint16'),stored[...,1])
y,x=np.mgrid[:1400,:1400];r=np.hypot(x-699.568111973117,y-699.6475341408573);mark=(x>=550)&(x<723)&(y>=902)&(y<1048);valid=r<435;dd=after-before
rep=dict(reproduces_historical_G_exact=True,field_float32_max_difference=float(np.max(abs(w-oldw))),change_mark_DN16=np.percentile(dd[mark],[0,50,100]).tolist(),change_inner_DN16=np.percentile(dd[valid],[0,50,100]).tolist(),clipped_mark=int((before[mark]<=0).sum()),mark_G_range=np.percentile(before[mark],[0,50,100]).tolist(),injections=[])
for (cx,cy,sig) in [(636,975,50),(636,975,90),(1000,680,50),(500,440,50)]:
    e=np.exp(-((x-cx)**2+(y-cy)**2)/(2*sig**2));m=(e>.05)&valid;outside=(e<.01)&valid
    for amplitude in [-200,200]:
        response,_=s8_eval(G+amplitude*e,edge);z=(response-before)/amplitude
        rep['injections'].append(dict(center=[cx,cy],sigma=sig,amplitude=amplitude,refit_gain=float(np.sum(z[m]*e[m])/np.sum(e[m]**2)),outside_max_DN16=float(np.max(abs(response-before)[outside])),error_RMS_DN16=float(np.sqrt(np.mean(((z-e)*amplitude)[m]**2)))))
        print(rep['injections'][-1],flush=True)
# Transport only the exact field difference; keep every later photographic delta.
v68=np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float)
candidate=v68+(w-wc)[...,None]
np.savez_compressed(O/'arrays/A4_centered_candidate.npz',rgb=candidate.astype('float32'),delta=(w-wc).astype('float32'))
np.save(O/'arrays/A4_field_original.npy',w.astype('float32'));np.save(O/'arrays/A4_field_centered.npy',wc.astype('float32'))
(O/'A4_s8_audit.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
