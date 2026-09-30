"""Conditional display transport paired with B10's exact source operator test.
No rerun or identification of native CameraRaw. The frozen additive detector
estimate is invariant under a scene-common injection (tested in B10).
"""
from common import *
claim();b=json.loads((OUT/'B14_repeatable_injections.json').read_text());assert b['all_scene_pass'] and b['all_detector_no_amplification']
old=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').astype(np.int32);new=np.load(OUT/'arrays/D10_candidate_rgb.npy').astype(np.int32);delta=np.load(OUT/'arrays/D10_delta.npy')
assert np.array_equal(new,old+delta[...,None]);r,t=geometry();y,x=np.mgrid[:N,:N];mask=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_mask.npy');alpha=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_alpha.npy');visible=(mask>0)&(alpha>0);rng=np.random.default_rng(551309);rows=[]
for j,wl in enumerate([18.,22.,28.,36.,44.,58.]):
    ang=rng.uniform(0,2*np.pi);ph=rng.uniform(0,2*np.pi);q=np.rint(12*np.sin(2*np.pi*((x-CX)*np.cos(ang)+(y-CY)*np.sin(ang))/wl+ph)).astype(np.int32);q[~visible]=0
    injected_before=old+q[...,None];injected_after=injected_before+delta[...,None]
    assert injected_before.min()>=0 and injected_before.max()<=65535 and injected_after.min()>=0 and injected_after.max()<=65535
    a=injected_before[...,1]-old[...,1];z=injected_after[...,1]-new[...,1]
    for lo,hi in [[60,250],[250,350],[350,410],[410,435],[435,449]]:
        for sec in range(12):
            m=(r>=lo)&(r<hi)&((t//(np.pi/6)).astype(int)==sec)&visible;aa=a[m].astype(float);zz=z[m].astype(float);gain=float(aa@zz/max(aa@aa,1e-30));err=int(np.max(abs(a[m]-z[m])));rows.append(dict(injection=j,wavelength=wl,radius=[lo,hi],sector=sec,transfer=gain,max_DN16=err,pass_gate=.9<=gain<=1.1))
save('D14_differential_injection.json',dict(method=__doc__,rows=rows,all_pass=all(z['pass_gate'] for z in rows),source_receipt_sha256=sha(OUT/'B14_repeatable_injections.json'),candidate_sha256=sha(OUT/'arrays/D10_candidate_rgb.npy'),max_DN16=max(z['max_DN16'] for z in rows),limits=['Conditional display transport with fixed coefficients/covariance and preserved saved appearance.','Scene invariance follows additive-model structure and B10; not independent proof of recovered features.','Not an end-to-end RAW to native CameraRaw experiment. External source comparison and detector-only controls are required.']))
print('DISPLAY CONDITIONAL INJECTIONS',len(rows),'PASS',flush=True)
