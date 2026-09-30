#!/usr/bin/env python3
"""Global monotonic photographic HDR tone, independent of radiance producer.

Fixed nominal log10-luminance slope .14; .10/.18 are prespecified sensitivity
variants. Fit anchor and two global color gains at source dreal25..100 only.
The common linear RGB shoulder begins at encoded maximum .95 and approaches1.
No channel-wise clipping or gamut desaturation. All writes are temporary.
"""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from color_pilot import color_ratios,decode,encode_unclipped,stats,make_panel,jacobian,digest

OUT=Path('/private/tmp/v105_color_pilot_20260926')
SRC=Path('/private/tmp/v105_base_sources_20260926')
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026')

def render_headroom(L,q,anchor,slope,logRG,logBG,Lref,delta=0.):
    """L is positive calibrated luminance; q is observed low-frequency RGB/L.
    Returns encoded RGB and intermediate maps. No geometry or radiance fitting.
    Caller owns source validity, blend, ICC interpretation, and final native QA.
    """
    gains=np.exp(np.array([logRG,0.,logBG]))
    qc=q*gains
    qc/=np.maximum(((qc[...,0]+2*qc[...,1]+qc[...,2])/4)[...,None],1e-30)
    tone=anchor+slope*np.log10(np.maximum(L*np.exp(delta),1e-30)/Lref)
    linear=decode(np.maximum(tone,.001))[...,None]*qc
    maximum=linear.max(-1)
    knee=float(decode(.95));head=1.
    # expm1 avoids cancellation right at the shoulder knee. The selected branch
    # has derivative exp(-(maximum-knee)/(head-knee)) >0 for finite arguments.
    beyond=np.maximum(maximum-knee,0)/(head-knee)
    newmaximum=np.where(maximum>knee,knee-(head-knee)*np.expm1(-beyond),maximum)
    common_gain=newmaximum/np.maximum(maximum,1e-30)
    rgb=encode_unclipped(linear*common_gain[...,None])
    return rgb,dict(tone=tone,qc=qc,raw_maximum=maximum,common_gain=common_gain,
                    max_shoulder_derivative=np.where(maximum>knee,np.exp(-beyond),1.))

def fit_anchor_color(L,q,B,z,slope,Lref):
    iy,ix=np.nonzero(z);take=np.arange(0,len(iy),max(1,len(iy)//16000));y,x=iy[take],ix[take]
    def residual(p):return (render_headroom(L[y,x],q[y,x],p[0],slope,p[1],p[2],Lref)[0]-B[y,x]).ravel()
    opt=least_squares(residual,[.72,0.,-.2],bounds=([.2,-1.5,-1.5],[1.2,1.5,1.5]),
                      loss='soft_l1',f_scale=.01,max_nfev=100)
    return opt.x,dict(success=bool(opt.success),nfev=int(opt.nfev),sample_count=len(x),cost=float(opt.cost))

def main():
    name='572A2969';srcpath=SRC/f'{name}.npz';source=np.load(srcpath)
    E=source['E'];valid=source['valid_rgb']&np.all(np.isfinite(E)&(E>0),-1)
    L,q=color_ratios(E,valid)
    b=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L3.npz')
    B=np.stack([b[f'c{c}'] for c in range(3)],-1)[77:1477,77:1477].astype(np.float32)/65535
    d=source['dreal'];dp=source['d_presentation_circle']
    fit=valid&(d>=25)&(d<100)&np.all((B>.05)&(B<.95),-1)
    Lref=float(np.median(L[fit]))
    eligible=valid&(d>=0)&(dp>=0)
    sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v97_refundacio_20260924'))
    from jutge_comu import Estat,comp
    S=Estat(ROOT/'4-RESULTATS/v103_banda_20260926/E/estat_v103');P=S.pila(box=(4677,3077,6077,4477))
    oldbase=next(f for lid,m,f,a in P if lid==3)
    oldcomp,_=comp([(m,f,a) for lid,m,f,a in P],1400,1400)
    report=dict(source=str(srcpath),source_sha256=digest(srcpath),Lref=Lref,nominal_slope=.14,
        predeclared_sensitivity_slopes=[.10,.18],params_fit='Anchor and global R/G,B/G gains only, dreal25..100. No slope tuning.',
        curve='Calibrated L -> encoded log10 tone -> linear RGB q -> common linear shoulder at encoded max .95, asymptote1 -> encoding. No channel clip or wg.',
        limits=['Photographic tone tradeoff; not 100% reference-contrast retention.', 'Source radiance/calibration/coverage separate from tone function.',
        'Old-filter emulation lacks Photoshop adjustment layers; final alpha undecided.', 'Quantization can saturate near the asymptote even where analytic derivative stays positive.'],models={})
    images={};comps={}
    for slope in [.10,.14,.18]:
        key=f'{slope:.2f}';p,fitinfo=fit_anchor_color(L,q,B,fit,slope,Lref)
        call=lambda delta:render_headroom(L,q,p[0],slope,p[1],p[2],Lref,delta)
        RGB,maps=call(0.);J=jacobian(call)
        validout=eligible&np.all(np.isfinite(RGB)&(RGB>=0)&(RGB<=1),-1)
        ready=np.where(validout[...,None],RGB,0).astype(np.float32)
        R16=np.rint(np.clip(ready,0,1)*65535).astype(np.uint16)
        config=dict(anchor=float(p[0]),slope=slope,logRG=float(p[1]),logBG=float(p[2]),Lref=Lref,
                    shoulder_encoded_knee=.95,shoulder_encoded_head=1.,sigma_color=24.)
        r=dict(config=config,fit=fitinfo,training_residual_RGB=stats(RGB-B,fit),bands={})
        for lo,hi in [(0,3),(3,10),(10,25),(25,100)]:
            z=eligible&(d>=lo)&(d<hi)
            r['bands'][f'{lo}-{hi}']=dict(RGB=stats(RGB,z),jacobian_RGB_per_lnL=stats(J,z),
                nonpositive_jacobian_fraction=(np.mean(J[z]<=0,axis=0)).tolist(),
                RGB_out_of_unit_fraction=float(np.mean(np.any((RGB[z]<0)|(RGB[z]>1),-1))),
                quantized_u16_equal65535_fraction=np.mean(R16[z]==65535,axis=0).tolist(),
                shoulder_active_fraction=float(np.mean(maps['raw_maximum'][z]>decode(.95))),
                chromaticity_deviation_from_common_scaling=0.)
        t=np.clip((dp-50)/100,0,1);w=validout*(1-t*t*(3-2*t))
        replacement=(1-w[...,None])*oldbase+w[...,None]*ready
        C,_=comp([(m,replacement if lid==3 else f,a) for lid,m,f,a in P],1400,1400)
        images[key]=replacement;comps[key]=C
        np.savez_compressed(OUT/f'HEADROOM_{name}_s{key}_ready.npz',RGB=ready,maskwhereupdate=validout,
            valid_source=valid,box=source['box'],dreal=d,d_presentation_circle=dp,
            config_json=np.asarray(json.dumps(config)),jacobian_RGB_lnL=J.astype(np.float32))
        np.savez_compressed(OUT/f'HEADROOM_{name}_s{key}_emulated.npz',RGB=C,base_RGB=replacement,
                            provisional_weight=w,box=source['box'])
        report['models'][key]=r
    # Full inner ROI in one common display, alongside supplemental native crops.
    fullmask=np.ones((1400,1400),bool)
    make_panel([('Current composite',oldcomp,fullmask)]+[(f'Headroom slope {k}',comps[k],fullmask) for k in ['0.10','0.14','0.18']],
        OUT/'HEADROOM_full_inner_EMULATED.png','DIAGNOSTIC 1400px ROI: .14 nominal; .10/.18 sensitivity; before adjustment layers')
    for label,(x0,x1,y0,y1) in {'top':(650,860,210,295),'upper_left':(310,520,275,360),'left':(210,330,600,750)}.items():
        sl=np.s_[y0:y1,x0:x1];v=np.ones(fullmask[sl].shape,bool)
        make_panel([('Current composite',oldcomp[sl],v)]+[(f'Headroom slope {k}',comps[k][sl],v) for k in ['0.10','0.14','0.18']],
            OUT/f'HEADROOM_{label}_EMULATED.png','DIAGNOSTIC: old filters retained; .14 nominal chosen before QA; provisional blend',zoom=True)
        make_panel([('Current base',oldbase[sl],v)]+[(f'Headroom slope {k}',images[k][sl],v) for k in ['0.10','0.14','0.18']],
            OUT/f'HEADROOM_{label}_BASE.png','Base-only native samples: no additional sharpening or transferred local residual',zoom=True)
    report['source_hash_still_matches']=digest(srcpath)==report['source_sha256']
    report['script_sha256']=digest(Path(__file__))
    (OUT/'HEADROOM.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:{'config':v['config'],'rim_jac':v['bands']['0-3']['jacobian_RGB_per_lnL']['median'],
         'rim_rgb':v['bands']['0-3']['RGB']['median'],'rim_nonpositive':v['bands']['0-3']['nonpositive_jacobian_fraction'],
         'rim_u16sat':v['bands']['0-3']['quantized_u16_equal65535_fraction']} for k,v in report['models'].items()},indent=2))

if __name__=='__main__':main()
