"""Matched spatial-cell QA for parent's bit-exact floor12 and floor0 RAW pilots.
No RAW processing and no product output. Negative noisy samples are retained in
cell sums; only positive cell means enter ratio regressions. No T correction.
"""
from pathlib import Path
import json
import numpy as np
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026');OUT=Path('/private/tmp/v105_qa_20260926')
P=Path('/private/tmp/v105_raw_pilot_20260926')
assert json.loads((P/'CONTROL12_REPLAY.json').read_text())['PASS']
for mode in ['control12','no_floor']:assert json.loads((P/mode/'COMPLETE.json').read_text())['PASS']
meta=json.loads((P/'no_floor/METADATA.json').read_text());frames=meta['frames'];y0,y1,x0,x1=meta['box_y0y1x0x1']
geo=json.loads((ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
yy,xx=np.mgrid[y0:y1,x0:x1];dist=np.hypot(xx-geo['cx'],yy-geo['cy'])-geo['R']
fitregion=(dist>=25)&(dist<100);iy,ix=np.nonzero(fitregion);py,px=iy+y0,ix+x0
theta=np.degrees(np.arctan2(-(py-geo['cy']),px-geo['cx']))%360
matrix=np.array(meta['matrix']);gain=np.array(meta['gain'])
data={mode:{k:np.load(P/mode/(k+'.npy'),mmap_mode='r') for k in ['numerator','weight','distance_model']} for mode in ['control12','no_floor']}
refidx=next(i for i,f in enumerate(frames) if f['name']=='572A2969.CR3')
refN=np.asarray(data['control12']['numerator'][refidx,iy,ix],float)
refW=np.asarray(data['control12']['weight'][refidx,iy,ix],float)
sil=np.load(ROOT/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz');rm=float(meta['radius_model'])
def dreal(j):
    dm=data['no_floor']['distance_model'][j];qy,qx=(y1-y0)//2,x1-x0-100
    gy=(float(dm[qy+1,qx])-float(dm[qy-1,qx]))/2;gx=(float(dm[qy,qx+1])-float(dm[qy,qx-1]))/2
    cx=qx+x0-(float(dm[qy,qx])+rm)*gx;cy=qy+y0-(float(dm[qy,qx])+rm)*gy
    pa=np.degrees(np.arctan2(-(py-cy),px-cx))%360
    return np.asarray(dm[iy,ix],float)+rm-geo['R']-np.interp(pa,sil['pa'],sil['e'],period=360)
def fit(x,y,kind):
    if len(x)<30:return None
    if kind=='constant':g=float(np.median(y/x));b=0.
    else:
        dx=x-x.mean();dy=y-y.mean();xy=np.dot(dx,dy)
        if abs(xy)<1e-30:return None
        g=float(xy/np.dot(dx,dx)) if kind=='direct_affine' else float(np.dot(dy,dy)/xy)
        b=float(y.mean()-g*x.mean())
    return {'gain':g,'offset':b,'offset_fraction_reference_median':float(b/np.median(y)),'n_cells':len(x)}
def metrics(pred,y,sec):
    ok=np.isfinite(pred)&np.isfinite(y)&(y>0);pred,y,sec=pred[ok],y[ok],sec[ok]
    if len(y)==0:return None
    delta=(pred-y)/y;rs={}
    for i in range(12):
        z=delta[sec==i]
        if len(z)>=4:rs[str(i*30)+'..'+str((i+1)*30)]={'n':len(z),'median_bias_pct':float(100*np.median(z)),'median_abs_error_pct':float(100*np.median(abs(z)))}
    return {'n_cells':len(y),'median_bias_pct':float(100*np.median(delta)),'median_abs_error_pct':float(100*np.median(abs(delta))),
        'max_abs_sector_median_bias_pct':max([abs(v['median_bias_pct']) for v in rs.values()],default=None),'sectors':rs}
report={'control_replay':{'PASS':True,'exact_comparisons':len(json.loads((P/'CONTROL12_REPLAY.json').read_text())['comparisons'])},
 'region':'25..100 px from presentation circle; per-frame dreal>=10; fixed global spatial cells',
 'estimator':'sum numerator / sum weight in each fixed cell; includes negative noisy N, never conditions pixels on N>0; output is measurement QA only',
 'models':['constant median ratio','direct affine OLS (noisy source predictor)','reverse affine OLS: source=a*reference+b, then gain=1/a,offset=-b/a'],
 'reference':'control12 572A2969.CR3, common geometric cell footprints; high exposure reference is used as predictor for reverse affine',
 'validation':'fit even 30-degree sectors, validate odd; reverse folds; no near-limb fit',
 'limitations':['Weighted cell means can differ with the floor-dependent within-cell sampling; that is part of the mechanism under test.',
   'Reverse affine reduces source-predictor noise attenuation but does not prove reference noiselessness or remove common calibration errors.',
   'These are calibration candidates and validation numbers, not authorization to insert extrapolated radiance.'], 'frames':[]}
coeffpacket=[]
for j,f in enumerate(frames):
    dr=dreal(j);physical=dr>=10
    it={'name':f['name'],'exposure':f['exposure'],'modes':{}}
    for mode in ['control12','no_floor']:
        n=np.asarray(data[mode]['numerator'][j,iy,ix],float);w=np.asarray(data[mode]['weight'][j,iy,ix],float)
        sizes={}
        for cell in [8,16,32]:
            # fixed cells anchored to global canvas, not to data values or sector boundaries.
            ids0=(py//cell)*((x1+cell-1)//cell)+(px//cell);unique,ids=np.unique(ids0,return_inverse=True);nc=len(unique)
            count=np.bincount(ids,weights=physical,minlength=nc)
            tx=np.bincount(ids,weights=px*physical,minlength=nc)/np.maximum(count,1)
            ty=np.bincount(ids,weights=py*physical,minlength=nc)/np.maximum(count,1)
            sec=(np.degrees(np.arctan2(-(ty-geo['cy']),tx-geo['cx']))%360//30).astype(int)
            a=np.full((nc,3),np.nan);b=np.full_like(a,np.nan);channels={};coeffcv={}
            for c,ch in enumerate('RGB'):
                good=physical&np.isfinite(n[:,c])&np.isfinite(w[:,c])&(w[:,c]>0)
                refgood=physical&np.isfinite(refN[:,c])&np.isfinite(refW[:,c])&(refW[:,c]>0)
                sw=np.bincount(ids,weights=np.where(good,w[:,c],0),minlength=nc)
                sn=np.bincount(ids,weights=np.where(good,n[:,c],0),minlength=nc)
                rw=np.bincount(ids,weights=np.where(refgood,refW[:,c],0),minlength=nc)
                rn=np.bincount(ids,weights=np.where(refgood,refN[:,c],0),minlength=nc)
                cnt=np.bincount(ids,weights=good,minlength=nc);rcnt=np.bincount(ids,weights=refgood,minlength=nc)
                goodcell=(count>=.6*cell*cell)&(cnt>=max(8,.1*cell*cell))&(rcnt>=.6*cell*cell)&(sw>0)&(rw>0)
                a[goodcell,c]=sn[goodcell]/sw[goodcell];b[goodcell,c]=rn[goodcell]/rw[goodcell]
                use=goodcell&(a[:,c]>0)&(b[:,c]>0);x,y,ss=a[use,c],b[use,c],sec[use]
                output={}
                for kind in ['constant','direct_affine','reverse_affine']:
                    coeff=fit(x,y,kind);cv=[]
                    for fold in [0,1]:
                        train=ss%2==fold;cc=fit(x[train],y[train],kind);coeffcv[(ch,kind,fold)]=cc
                        test=~train;mm=metrics(cc['gain']*x[test]+cc['offset'],y[test],ss[test]) if cc else None
                        cv.append({'fit':cc,'heldout':mm})
                    output[kind]={'full_fit':coeff,'cv':cv}
                channels[ch]=output
            post={}
            use=np.isfinite(a).all(-1)&np.isfinite(b).all(-1)&(b>0).all(-1)
            for kind in ['constant','direct_affine','reverse_affine']:
                cv=[]
                for fold in [0,1]:
                    coeffs=[coeffcv[(ch,kind,fold)] for ch in 'RGB']
                    if not all(coeffs):cv.append(None);continue
                    te=use&(sec%2!=fold);g=np.array([k['gain'] for k in coeffs]);off=np.array([k['offset'] for k in coeffs])
                    ep=np.einsum('ij,...j->...i',matrix,(a[te]*g+off)*gain)
                    er=np.einsum('ij,...j->...i',matrix,b[te]*gain)
                    cv.append({ch:metrics(ep[:,c],er[:,c],sec[te]) for c,ch in enumerate('RGB')})
                post[kind]=cv
            sizes[str(cell)]={'camera_channels':channels,'postmatrix_heldout':post}
        it['modes'][mode]=sizes
    report['frames'].append(it)
    print(f['name'],flush=True)
(OUT/'binned_floor_calibration.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
# Coefficient file is deliberately a candidate, not auto-selected for production.
for f in report['frames']:
    channels=f['modes']['no_floor']['16']['camera_channels']
    coeffpacket.append({'name':f['name'],'camera_coefficients':{c:{kind:channels[c][kind]['full_fit'] for kind in ['constant','reverse_affine']} for c in 'RGB'},
        'postmatrix_heldout':f['modes']['no_floor']['16']['postmatrix_heldout']})
(OUT/'no_floor_tile16_coefficients_candidates.json').write_text(json.dumps(coeffpacket,indent=2,allow_nan=False)+'\n')
print('DONE')
