from pathlib import Path
import numpy as np,json,tifffile as tf,cv2
from scipy.ndimage import gaussian_filter,label,binary_dilation,map_coordinates
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
j=json.loads((P/'A0_sources.json').read_text())['V57']['layers'];yy,xx=np.ogrid[2777:4777,4377:6377];rad=np.hypot(xx-5376.568111973117,yy-3776.647534140857);inner=(rad>410)&(rad<430)
raw=[];masks=[];stats=[];confidence=[]
for i in range(7):
    rgb=np.stack([np.load(P/'arrays'/f'V57_L{i:02d}_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;raw.append(rgb)
    m=np.load(P/'arrays'/f'V57_L{i:02d}_C-2.npy').astype('float32')/65535
    if not j[i]['visible']:m*=0
    masks.append(m);med=float(np.median(rgb[...,1][inner]));sig=max(float(np.median(abs(rgb[...,1][inner]-med))*1.4826),1/65535);stats.append(dict(layer=12-i,black_background=med,robust_sigma=sig))
    if i<3:confidence.append(np.clip((rgb[...,1]-med-3*sig)/(3*sig),0,1))
confidence=np.sort(confidence,axis=0)[1];old=np.load(R/'output/v63_encaix_contorn_20260913/arrays/B6_foreground_alpha.npy').astype('float32')/65535;native=tf.imread(P/'V61_interiors_only.tif')[...,:3].astype('float32')/65535
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
def warp(a):return cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_CUBIC)
results={}
for cutoff,sigma in [(6,8),(3,8),(9,8),(6,6),(6,10)]:
    bgmix=np.zeros((2000,2000),np.float32);dbg=[]
    for i,(rgb,m,st) in enumerate(zip(raw,masks,stats)):
        if not j[i]['visible']:continue
        lab,n=label(rgb[...,1]<(st['black_background']+cutoff*st['robust_sigma']));core=lab==lab[1000,1000];valid=~binary_dilation(core,iterations=5);den=gaussian_filter(valid.astype('float32'),sigma);bg=gaussian_filter(rgb[...,1]*valid,sigma)/np.maximum(den,1e-8)
        bgmix+=m*(bg-bgmix)
    desired=np.clip(native[...,1]/np.maximum(bgmix,1e-8),0,1)
    new=old+confidence*np.maximum(desired-old,0)
    # Preserve the previously validated invalid-continuum exclusion in dark core.
    oldsupport=np.load(R/'output/v63_encaix_contorn_20260913/arrays/B6_support.npy');new=np.where(oldsupport>0,new,old)
    new=np.clip(new,0,1);key=f'k{cutoff}_s{sigma}';results[key]=warp(new)
    if key=='k6_s8':np.save(A/'B6_alpha_source.npy',np.rint(new*65535).astype('uint16'));np.save(A/'B6_confidence_source.npy',confidence);np.save(A/'B6_continuum_source.npy',bgmix)
    print(key,'done',flush=True)
np.save(A/'B6_alpha_global.npy',results['k6_s8']);np.savez(O/'B6_parameter_probes.npz',**results)
rows=[]
for m in json.loads((O/'A2_green_marks.json').read_text()):
    x,y=m['centre'];theta=np.arctan2(y-3776.647534140857,x-5376.568111973117);rr=np.arange(440,475,.125);xx=5376.568111973117+np.cos(theta)*rr;yy=3776.647534140857+np.sin(theta)*rr;es={}
    for name,a in results.items():
        p=map_coordinates(a,[yy-2777,xx-4377],order=1);hits=np.flatnonzero((p[:-1]<.5)&(p[1:]>=.5));es[name]=float(rr[hits[0]]+.125*(.5-p[hits[0]])/(p[hits[0]+1]-p[hits[0]])) if len(hits) else None
    rows.append(dict(mark=m['index'],edge50=es,sensitivity_range_px=float(max(es.values())-min(es.values()))))
rep=dict(method='Estimate each exposure continuum before combining with original masks; correct only an under-estimated group opacity, keep original divider and pixels. Increase requires signal above measured black background in two of photos12/11/10. Existing invalid-continuum exclusion preserved.',production=dict(core_cutoff_sigma=6,continuum_sigma=8,dilation=5,signal_support_sigma=[3,6],corroborating_photos=2),source_stats=stats,parameter_probes=rows,status='candidate, not yet native validated')
(O/'B6_exposure_matte.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rows),flush=True)
