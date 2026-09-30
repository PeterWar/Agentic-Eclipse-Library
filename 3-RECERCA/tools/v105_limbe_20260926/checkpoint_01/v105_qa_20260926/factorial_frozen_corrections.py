"""Ablate ONLY frozen phi and additive offsets from measured no-floor samples.
No refitted spatial fields, radiance filling, PSF/T correction, or product output.
"""
from pathlib import Path
import ast,json
import numpy as np
import cv2
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026');OUT=Path('/private/tmp/v105_qa_20260926')
RAW=Path('/private/tmp/v105_raw_pilot_20260926/no_floor')
CAU=ROOT/'4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'
assert json.loads((RAW/'COMPLETE.json').read_text())['PASS']
meta=json.loads((RAW/'METADATA.json').read_text());orig=json.loads((CAU/'vixen_meta.json').read_text());Q=int(orig['Q'])
y0,y1,x0,x1=meta['box_y0y1x0x1'];N=np.load(RAW/'numerator.npy',mmap_mode='r');W=np.load(RAW/'weight.npy',mmap_mode='r')
geo=json.loads((ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
yy,xx=np.mgrid[y0:y1,x0:x1];d=np.hypot(xx-geo['cx'],yy-geo['cy'])-geo['R'];roi=(d>=25)&(d<100);iy,ix=np.nonzero(roi);py,px=iy+y0,ix+x0
matrix=np.asarray(meta['matrix']);gain=np.asarray(meta['gain']);phis={c:np.load(CAU/f'vixen_{c}_phi.npy',mmap_mode='r') for c in 'RGB'}
# Reuse the previously declared regression and heldout metrics, not its main code.
tree=ast.parse((OUT/'binned_floor_calibration.py').read_text())
fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['fit','metrics']]
exec(compile(ast.Module(body=fns,type_ignores=[]),'QA functions','exec'))
def phi_crop(array):
    ay0=max(0,y0//Q-1);ax0=max(0,x0//Q-1);ay1=min(array.shape[0],(y1+Q-1)//Q+1);ax1=min(array.shape[1],(x1+Q-1)//Q+1)
    small=np.asarray(array[ay0:ay1,ax0:ax1],np.float32)
    large=cv2.resize(small,(small.shape[1]*Q,small.shape[0]*Q),interpolation=cv2.INTER_LINEAR)
    return large[y0-ay0*Q:y1-ay0*Q,x0-ax0*Q:x1-ax0*Q]
# Verify exact equivalence to the producer's literal full upsample in this interior crop.
full=cv2.resize(np.asarray(phis['G'][0],np.float32),(phis['G'].shape[2]*Q,phis['G'].shape[1]*Q),interpolation=cv2.INTER_LINEAR)
local=phi_crop(phis['G'][0]);delta=abs(full[y0:y1,x0:x1]-local);upsample_qa={'max_abs':float(delta.max()),'exact':bool(np.array_equal(full[y0:y1,x0:x1],local))}
assert upsample_qa['exact'],upsample_qa
del full,local,delta
inputs={};indices=list(range(8))+[10,16]
for j in indices:
    f=meta['frames'][j];oj=int(f.get('original_index',j));assert orig['frames'][oj]['name']==f['name']
    phi=np.stack([phi_crop(phis[c][oj])[roi] for c in 'RGB'],-1)
    inputs[j]={'n':np.asarray(N[j,iy,ix],float),'w':np.asarray(W[j,iy,ix],float),
               'phi':phi,'b':np.array(orig['frames'][oj]['offset_RGB'])}
def corrected_n(j,remove_phi,remove_b):
    s=inputs[j];out=s['n'].copy()
    if remove_phi:out*=np.exp(s['phi'])
    if remove_b:out-=s['b']*s['w']*(1 if remove_phi else np.exp(-s['phi']))
    return out
def cells(n,w,cell):
    ids0=(py//cell)*((x1+cell-1)//cell)+(px//cell);un,ids=np.unique(ids0,return_inverse=True);nc=len(un)
    count=np.bincount(ids,minlength=nc);tx=np.bincount(ids,weights=px,minlength=nc)/count;ty=np.bincount(ids,weights=py,minlength=nc)/count
    sec=(np.degrees(np.arctan2(-(ty-geo['cy']),tx-geo['cx']))%360//30).astype(int)
    out=np.full((nc,3),np.nan)
    for c in range(3):
        valid=np.isfinite(n[:,c])&np.isfinite(w[:,c])&(w[:,c]>0)
        sw=np.bincount(ids,weights=np.where(valid,w[:,c],0),minlength=nc);sn=np.bincount(ids,weights=np.where(valid,n[:,c],0),minlength=nc)
        cnt=np.bincount(ids,weights=valid,minlength=nc);ok=(count>=.6*cell*cell)&(cnt>=.6*cell*cell)&(sw>0)
        out[ok,c]=sn[ok]/sw[ok]
    return out,sec
def compare(a,b,sec):
    output={};fits={}
    for c,ch in enumerate('RGB'):
        valid=np.isfinite(a[:,c])&np.isfinite(b[:,c])&(a[:,c]>0)&(b[:,c]>0)
        x,y,ss=a[valid,c],b[valid,c],sec[valid];methods={}
        for kind in ['constant','direct_affine','reverse_affine']:
            full=fit(x,y,kind);cv=[]
            for fold in [0,1]:
                tr=ss%2==fold;cc=fit(x[tr],y[tr],kind);fits[(ch,kind,fold)]=cc;te=~tr
                cv.append({'fit':cc,'heldout':metrics(cc['gain']*x[te]+cc['offset'],y[te],ss[te]) if cc else None})
            methods[kind]={'full_fit':full,'cv':cv}
        output[ch]=methods
    post={};usable=np.isfinite(a).all(-1)&np.isfinite(b).all(-1)&(b>0).all(-1)
    for kind in ['constant','direct_affine','reverse_affine']:
        cv=[]
        for fold in [0,1]:
            cc=[fits[(ch,kind,fold)] for ch in 'RGB'];te=usable&(sec%2!=fold)
            if not all(cc):cv.append(None);continue
            g=np.array([z['gain'] for z in cc]);off=np.array([z['offset'] for z in cc])
            ep=np.einsum('ij,...j->...i',matrix,(a[te]*g+off)*gain);er=np.einsum('ij,...j->...i',matrix,b[te]*gain)
            cv.append({ch:metrics(ep[:,c],er[:,c],sec[te]) for c,ch in enumerate('RGB')})
        post[kind]=cv
    return {'camera_channels':output,'postmatrix_heldout':post}
report={'scope':'Factorial removal of FROZEN corrections applied to ALL sources and references consistently; no new fields fit.',
 'formula':'N_cached=(remap(pl*w*k)+b*W)*exp(-phi); remove_phi:N*=exp(phi); remove_b:N-=b*W*(1 if phi removed else exp(-phi))',
 'upsample_crop_equivalence':upsample_qa,'region_px':[25,100],'cell_sizes':[8,16,32],
 'references':['572A2969.CR3','572A2975.CR3'],'source':'sum N / sum W over 2959..2966 after each fixed ablation',
 'upsample_parent_source':'raw_replay/s4_v51_core_comu38.py:upsample',
 'offsets':{meta['frames'][j]['name']:inputs[j]['b'].tolist() for j in indices},
 'phi_sample_stats':{meta['frames'][j]['name']:{c:np.percentile(inputs[j]['phi'][:,i],[1,50,99]).tolist() for i,c in enumerate('RGB')} for j in indices},
 'cases':{}}
for case,rp,rb in [('keep_both',False,False),('remove_phi',True,False),('remove_b',False,True),('remove_both',True,True)]:
    pooledN=sum(corrected_n(j,rp,rb) for j in range(8));pooledW=sum(inputs[j]['w'] for j in range(8))
    refs={j:corrected_n(j,rp,rb) for j in [10,16]};res={}
    for cell in [8,16,32]:
        a,sec=cells(pooledN,pooledW,cell);rd={}
        for j in [10,16]:
            b,_=cells(refs[j],inputs[j]['w'],cell);rd[meta['frames'][j]['name']]=compare(a,b,sec)
        res[str(cell)]=rd
    report['cases'][case]=res;print(case,flush=True)
(OUT/'factorial_frozen_corrections.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print('DONE',upsample_qa)
