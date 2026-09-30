"""Bounded calibration/eligibility audit. No T correction and no rendered product.

All fits use camera_rgb=N/W before the declared matrix; original channel weights
are retained for requested dominance calculations. Outputs restricted to TMP QA.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates

ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026')
OUT=Path('/private/tmp/v105_qa_20260926')
SRC=Path('/private/tmp/v105_base_sources_20260926')
LF=ROOT/'4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'
meta=json.loads((LF/'METADATA.json').read_text())
geo=json.loads((ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
y0,y1,x0,x1=meta['box_y0y1x0x1']
yy,xx=np.mgrid[y0:y1,x0:x1]; dist=np.hypot(xx-geo['cx'],yy-geo['cy'])-geo['R']
theta=np.degrees(np.arctan2(-(yy-geo['cy']),xx-geo['cx']))%360
alpha=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][y0-3000:y1-3000,x0-4600:x1-4600]/65535.
near=(dist>=-5)&(dist<15)&(alpha<=.95); ny,nx=np.nonzero(near)
clean=(dist>=25)&(dist<100); fy,fx=np.nonzero(clean)
fit_pa=theta[clean]; fit_sector=(fit_pa//30).astype(int); nd=dist[near]; nt=theta[near]; na=alpha[near]
N=np.load(LF/'numerator.npy',mmap_mode='r'); W=np.load(LF/'weight.npy',mmap_mode='r'); D=np.load(LF/'distance_model.npy',mmap_mode='r')
sil=np.load(ROOT/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); rm=float(meta['radius_model'])
nF=len(meta['frames']); nP=len(ny)
elig0=np.zeros((nF,nP),np.float32); elig6=np.zeros_like(elig0)
near_weights=np.zeros((nF,nP,3),np.float32); support_bits=np.zeros((nF,nP),np.uint8)
def smooth(d,lo,hi=2.):
    t=np.clip((d-lo)/(hi-lo),0,1);return t*t*(3-2*t)
def samples(j,iy,ix):
    n=np.asarray(N[j,iy,ix,:],float);w=np.asarray(W[j,iy,ix,:],float)
    good=(w>0)&np.isfinite(w)&np.isfinite(n)&(n>0)
    v=np.full_like(n,np.nan);np.divide(n,w,out=v,where=good)
    return v,w,good
def dreal_samples(j,iy,ix):
    dm=D[j];py,px=(y1-y0)//2,x1-x0-100
    gy=(float(dm[py+1,px])-float(dm[py-1,px]))/2;gx=(float(dm[py,px+1])-float(dm[py,px-1]))/2
    cx=px+x0-(float(dm[py,px])+rm)*gx;cy=py+y0-(float(dm[py,px])+rm)*gy
    pa=np.degrees(np.arctan2(-(iy+y0-cy),ix+x0-cx))%360
    return np.asarray(dm[iy,ix],float)+rm-geo['R']-np.interp(pa,sil['pa'],sil['e'],period=360)
def fit(x,y,affine=False):
    if x.size<200:return None
    g=float(np.median(y/x));b=0.
    if affine:
        for _ in range(5):
            residual=y-(g*x+b);scale=max(1.4826*np.median(abs(residual-np.median(residual))),1e-15)
            w=np.minimum(1,1.5*scale/np.maximum(abs(residual),1e-30))
            sw=w.sum();mx=np.sum(w*x)/sw;my=np.sum(w*y)/sw
            den=np.sum(w*(x-mx)**2)
            if den<=1e-30:return None
            g=float(np.sum(w*(x-mx)*(y-my))/den);b=float(my-g*mx)
    return {'gain':g,'offset':b,'n':int(x.size),'offset_fraction_target_median':float(b/np.median(y))}
def evaluate(x,y,pa_sector,coeff):
    if coeff is None:return None
    delta=(coeff['gain']*x+coeff['offset']-y)/y
    out={'n':int(len(delta)),'median_bias_pct':float(100*np.median(delta)),
         'median_abs_error_pct':float(100*np.median(abs(delta))), 'sectors':{}}
    for sec in range(12):
        q=delta[pa_sector==sec]
        if len(q)>=50:out['sectors'][str(sec*30)+'..'+str((sec+1)*30)]={'n':int(q.size),'bias_pct':float(100*np.median(q)),
            'median_abs_error_pct':float(100*np.median(abs(q)))}
    out['max_abs_sector_bias_pct']=max((abs(v['bias_pct']) for v in out['sectors'].values()),default=None)
    return out

refs={}
for name in ['572A2969.CR3','572A2975.CR3']:
    j=next(i for i,f in enumerate(meta['frames']) if f['name']==name)
    refs[name]=samples(j,fy,fx)
report={'method':'camera_rgb=N/W calibrated before color matrix; no T correction; no rendered image',
 'predeclared_fit_region':'25<=distance from presentation circle<100 px AND each frame dreal>=10px; common positive channel support',
 'cross_validation':'12 fixed 30-degree sectors; train even, validate odd, then reverse. No near-limb pixels fit.',
 'fixed_selection_rules':{'constant_is_default':True,'affine_requires_each_fold_relative_MAE_improvement':.20,
    'affine_max_abs_sector_bias_pct_each_fold':2.,'affine_gain_allowed':[.8,1.25],
    'affine_max_abs_offset_relative_target_median':.02,
    'constant_max_abs_sector_bias_pct_for_calibrated_label':2.,
    'otherwise':'candidate coefficients retained but calibration_unresolved; never pretend accepted'},
 'dominance':'uses ORIGINAL per-camera-channel weight times smoothstep(dreal,lo,2); no T squared. Pure geometric eligibility does not certify PSF-free corona.',
 'frames':[]}
selected_gains=np.ones((nF,3));selected_offsets=np.zeros((nF,3));selected_names=[]
for j,f in enumerate(meta['frames']):
    v,w,good=samples(j,fy,fx); drfit=dreal_samples(j,fy,fx)
    vn,wn,gn=samples(j,ny,nx);dr=dreal_samples(j,ny,nx)
    elig0[j]=smooth(dr,0);elig6[j]=smooth(dr,.6)
    near_weights[j]=np.where(gn,wn,0)
    for c in range(3):support_bits[j]|=(gn[:,c].astype(np.uint8)<<c)
    item={'index':j,'name':f['name'],'time':f['time'],'exposure':f['exposure'],'reference_fits':{},'selected':{}}
    for refname,(rv,rw,rg) in refs.items():
        channels={}
        for c,ch in enumerate('RGB'):
            valid=good[:,c]&rg[:,c]&(drfit>=10)
            x,y,ss=v[valid,c],rv[valid,c],fit_sector[valid]
            full={kind:fit(x,y,kind=='affine') for kind in ['constant','affine']}
            cv=[]
            for fold in [0,1]:
                tr=ss%2==fold;te=~tr
                result={}
                for kind in ['constant','affine']:
                    cc=fit(x[tr],y[tr],kind=='affine')
                    result[kind]={'fit':cc,'heldout':evaluate(x[te],y[te],ss[te],cc)}
                cv.append(result)
            channels[ch]={'full_fit':full,'cross_validation':cv}
            if refname=='572A2969.CR3':
                eligible=True
                for fold in cv:
                    a,b=fold['affine'],fold['constant']
                    eligible &= bool(a['fit'] and b['fit'] and a['heldout'] and b['heldout'])
                    if eligible:
                        eligible &= (.8<=a['fit']['gain']<=1.25 and abs(a['fit']['offset_fraction_target_median'])<=.02 and
                            a['heldout']['max_abs_sector_bias_pct'] is not None and a['heldout']['max_abs_sector_bias_pct']<=2 and
                            a['heldout']['median_abs_error_pct']<=.8*b['heldout']['median_abs_error_pct'])
                kind='affine' if eligible else 'constant';cc=full[kind]
                calibrated=bool(cc) and all(vv[kind]['heldout'] is not None and vv[kind]['heldout']['max_abs_sector_bias_pct'] is not None
                    and vv[kind]['heldout']['max_abs_sector_bias_pct']<=2 for vv in cv)
                if cc:selected_gains[j,c]=cc['gain'];selected_offsets[j,c]=cc['offset']
                item['selected'][ch]={'method':kind,'coefficients':cc,'calibration_status':'passes_sector_2pct' if calibrated else 'calibration_unresolved'}
        item['reference_fits'][refname]=channels
    report['frames'].append(item)
    print('calibration',f['name'],flush=True)

# Distances to alpha=.05 are display coordinates only, never physical validity.
angles=np.arange(0,360,.25);radii=np.arange(geo['R']-12,geo['R']+18,.025)
th=np.deg2rad(angles)[None,:];rr=radii[:,None]
coords=np.array([geo['cy']-rr*np.sin(th)-y0,geo['cx']+rr*np.cos(th)-x0])
ap=map_coordinates(alpha,coords,order=1,mode='constant',cval=1,prefilter=False)
edge=radii[np.argmin(abs(ap-.05),axis=0)]
display_distance=nd+geo['R']-np.interp(nt,angles,edge,period=360)
sectors=[('top',60,120),('upper_left',120,150),('prominence',150,180),('left',180,210),
         ('lower_left',210,240),('lower_left_exception',240,270),('bottom',270,300),('right',300,60)]
dominance={}
dompack={}
for case,elig in [('nominal0to2',elig0),('margin06to2',elig6)]:
    ww=near_weights*elig[...,None];den=ww.sum(0);frac=np.divide(ww,den[None],out=np.zeros_like(ww),where=den[None]>0)
    topidx=np.argmax(ww,axis=0);topfrac=frac.max(0);neff=np.divide(den**2,(ww**2).sum(0),out=np.zeros_like(den),where=den>0)
    # Count sensitivity of dominant-source choice to photometric gain variance scaling.
    wvar=ww/selected_gains[:,None,:]**2;topvar=np.argmax(wvar,axis=0)
    out={}
    for name,lo,hi in sectors:
        sec=((nt>=lo)&(nt<hi)) if lo<hi else ((nt>=lo)|(nt<hi))
        rows=[]
        for distance_name,distance in [('presentation_circle',nd),('display_alpha005',display_distance)]:
            for a,b in [(0,1),(1,2),(0,2),(2,3),(3,5),(5,10)]:
                mask=sec&(distance>=a)&(distance<b)&(na<=.05)
                entry={'distance_coordinate':distance_name,'band_px':[a,b],'pixels':int(mask.sum()),'channels':{}}
                for c,ch in enumerate('RGB'):
                    good=mask&(den[:,c]>0);n=int(good.sum())
                    meanfrac=frac[:,good,c].mean(1) if n else np.zeros(nF)
                    order=np.argsort(-meanfrac)[:8]
                    short=np.array([f['exposure']<=1/800 for f in meta['frames']])
                    entry['channels'][ch]={'covered_fraction':float(n/max(1,int(mask.sum()))),
                        'mean_weight_fraction_short_exposures':float(meanfrac[short].sum()),
                        'top_sources':[{'name':meta['frames'][i]['name'],'mean_weight_fraction':float(meanfrac[i])} for i in order if meanfrac[i]>0],
                        'median_top_source_fraction':float(np.median(topfrac[good,c])) if n else None,
                        'median_effective_n':float(np.median(neff[good,c])) if n else None,
                        'dominant_source_changes_if_W_div_gain_squared_fraction':float(np.mean(topidx[good,c]!=topvar[good,c])) if n else None}
                rows.append(entry)
        out[name]=rows
    dominance[case]=out
    dompack[case+'_dominant_frame']=topidx.astype(np.int16);dompack[case+'_dominant_fraction']=topfrac.astype(np.float16)
    dompack[case+'_sum_original_weight']=den;dompack[case+'_effective_n']=neff

(OUT/'calibration_67_candidates.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
(OUT/'dominance_first2px.json').write_text(json.dumps(dominance,indent=2,allow_nan=False)+'\n')
np.savez_compressed(OUT/'eligibility_and_calibration_candidates.npz',global_x=nx+x0,global_y=ny+y0,
    d_presentation=nd,d_display_alpha005=display_distance,display_alpha=na,angle_deg=nt,
    frame_names=np.asarray([f['name'] for f in meta['frames']]),
    eligibility_nominal0to2=elig0.astype(np.float16),eligibility_margin06to2=elig6.astype(np.float16),
    camera_channel_support_bits=support_bits,candidate_camera_gains=selected_gains,candidate_camera_offsets=selected_offsets,**dompack)
print('DONE',flush=True)
