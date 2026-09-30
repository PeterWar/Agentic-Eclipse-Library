#!/usr/bin/env python3
"""Read-only sources -> local color/tone pilot; no project/PSB mutations.

Prototype rendering, not photometric calibration. Native source luminance is
kept; only low-frequency chromaticity is estimated using observed RGB samples.
Every output is accompanied by its observed-valid mask. Missing data stay absent.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import cv2
from scipy.optimize import least_squares
from PIL import Image, ImageDraw

ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026')
SOURCES=Path('/private/tmp/v105_base_sources_20260926')
OUT=Path('/private/tmp/v105_color_pilot_20260926')

def digest(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def decode(c):
    c=np.asarray(c,float)
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def encode_unclipped(c):
    c=np.maximum(c,0)
    return np.where(c<=.0031308,12.92*c,1.055*c**(1/2.4)-.055)

def color_ratios(E,mask,sigma=24):
    L=(E[...,0]+2*E[...,1]+E[...,2])/4
    w=mask.astype(np.float32)
    conv=lambda x:cv2.GaussianBlur(np.asarray(x,np.float32),(0,0),sigma,borderType=cv2.BORDER_CONSTANT)
    den=conv(w)
    sm=np.stack([conv(np.where(mask,E[...,c],0))/np.maximum(den,1e-20) for c in range(3)],-1)
    smL=(sm[...,0]+2*sm[...,1]+sm[...,2])/4
    q=sm/np.maximum(smL[...,None],1e-20)
    return L,q

def old_render(L,q,delta=0):
    tone=np.clip(.74+.22*np.log10(np.maximum(L*np.exp(delta),1e-30)/70736.46875),.045,1)
    yl=decode(tone);qm=q.max(-1)
    wg=np.clip(np.where(qm>1,(1/np.maximum(yl,1e-20)-1)/np.maximum(qm-1,1e-20),1),0,1)
    lin=yl[...,None]*(1+wg[...,None]*(q-1))
    enc=encode_unclipped(np.clip(lin,0,1))
    mx=enc.max(-1);mapped=np.where(mx>.75,.75+.15*(1-np.exp(-(mx-.75)/.15)),mx)
    rgb=enc*(mapped/np.maximum(mx,1e-20))[...,None]
    return rgb,{'tone':tone,'wg':wg,'yl':yl,'lin':lin}

def common_render(L,q,params,Lref,delta=0):
    """Global tone + diagonal color fit, then common positive linear gain.

    Max-channel shoulder is monotone with positive derivative. Unlike the old
    gamut-wg rule, it never sets the max channel exactly to one and never changes
    chromaticity as a function of luminance. No encoded or channel-wise clip.
    """
    anchor,slope,logrg,logbg=params
    gains=np.exp(np.array([logrg,0,logbg]))
    qc=q*gains
    qc/=np.maximum((qc[...,0]+2*qc[...,1]+qc[...,2])[...,None]/4,1e-30)
    tone=anchor+slope*np.log10(np.maximum(L*np.exp(delta),1e-30)/Lref)
    # Only a nonpositive-log-domain floor far from the evaluated bright band.
    lin=decode(np.maximum(tone,.001))[...,None]*qc
    mx=lin.max(-1)
    knee,head=float(decode(.75)),float(decode(.90))
    mapped=np.where(mx>knee,knee+(head-knee)*(1-np.exp(-(mx-knee)/(head-knee))),mx)
    gain=mapped/np.maximum(mx,1e-30)
    rgb=encode_unclipped(lin*gain[...,None])
    return rgb,{'tone':tone,'raw_max':mx,'common_gain':gain,'qc':qc}

def stats(v,z):
    a=v[z]
    if not len(a):return {'n':0}
    return {'n':len(a),'p05':np.percentile(a,5,axis=0).tolist(),'median':np.median(a,axis=0).tolist(),
            'p95':np.percentile(a,95,axis=0).tolist(),'min':np.min(a,axis=0).tolist(),'max':np.max(a,axis=0).tolist()}

def jacobian(fun):return (fun(.005)[0]-fun(-.005)[0])/.01

def make_panel(items,path,title,zoom=False):
    w,h=items[0][1].shape[1],items[0][1].shape[0]
    if zoom:w*=3;h*=3
    img=Image.new('RGB',(w*len(items),h+65),'#202226');d=ImageDraw.Draw(img);d.text((10,8),title,fill='white')
    for i,(label,a,valid) in enumerate(items):
        p=np.where(valid[...,None],a,.025)
        p=Image.fromarray(np.uint8(np.clip(p,0,1)*255))
        if zoom:p=p.resize((w,h),Image.Resampling.NEAREST)
        img.paste(p,(i*w,65));d.text((i*w+10,36),label,fill='white')
    img.save(path)

def fit_model(L,q,B,z,Lref,fixed_slope):
    iy,ix=np.nonzero(z)
    # Deterministic spatial sample over the complete eligible calibration annulus.
    take=np.arange(0,len(iy),max(1,len(iy)//16000))
    y,x=iy[take],ix[take];ll,qq,bb=L[y,x],q[y,x],B[y,x]
    if fixed_slope:
        unpack=lambda p:np.array([p[0],.22,p[1],p[2]])
        initial=[.72,0.,0.];bounds=([.2,-1.5,-1.5],[1.2,1.5,1.5])
    else:
        unpack=lambda p:p
        initial=[.72,.22,0.,0.];bounds=([.2,.03,-1.5,-1.5],[1.2,.5,1.5,1.5])
    def residual(p):return (common_render(ll,qq,unpack(p),Lref)[0]-bb).ravel()
    opt=least_squares(residual,initial,bounds=bounds,loss='soft_l1',f_scale=.01,max_nfev=100)
    return unpack(opt.x),{'success':bool(opt.success),'nfev':int(opt.nfev),'fit_sample_count':len(ll),
                           'cost':float(opt.cost),'fixed_slope':bool(fixed_slope)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    b=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L3.npz')
    B=np.stack([b[f'c{c}'] for c in range(3)],-1)[77:1477,77:1477].astype(np.float32)/65535
    report={'recipe':'Fit at source dreal25..100 only; sigma24 observed chromaticity; native luminance; common linear shoulder .75->.90 encoded equivalent.',
            'negative':[],'sources':{},'limits':['Photographic color fit to current L3, not new scientific color calibration.',
                'No boundary pixels in fitting; no geometric warp, limb replacement or final alpha.',
                'No Photoshop adjustment/native gamut validation; outputs are encoded photographic prototypes.',
                'Invalid RGB remains absent. No saturation reconstruction or color-channel filling.']}
    # Reproduce old f2b from the actual E/F input, before f2c overrides it.
    p=ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz'
    e=np.load(p);F=e['F'];box=e['box'];y0,y1,x0,x1=map(int,box)
    sup=np.load(ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103/support.npy',mmap_mode='r')[y0:y1,x0:x1]
    oldmask=sup&np.isfinite(F[...,1])&(F[...,1]>0)
    LF,qF=color_ratios(F,oldmask)
    oldF,detailF=old_render(LF,qF)
    jF=jacobian(lambda delta:old_render(LF,qF,delta))
    oldfile=np.load(ROOT/'4-RESULTATS/v103_banda_20260926/E/base_v103/base_v103_u16.npy',mmap_mode='r')[y0:y1,x0:x1].astype(float)/65535
    np.savez_compressed(OUT/'f2b_diagnostic.npz',box=box,RGB=oldF.astype(np.float32),tone=detailF['tone'].astype(np.float32),
                        wg=detailF['wg'].astype(np.float32),jacobian_rgb_logL=jF.astype(np.float32),valid=oldmask)
    d0=np.load(SOURCES/'572A2975.npz')['d_presentation_circle']
    report['old_f2b']={'plateau_rgb_max_encoded':float(.75+.15*(1-np.exp(-.25/.15))),
        'formula':'When wg<1 and R=qmax, lin_R=yl*(1+(1/yl-1))=1 exactly; encoded R after shoulder is constant.',
        'ROI_recipe_vs_saved_f2b':stats(oldF-oldfile,oldmask&(d0>0)&(d0<100)), 'bands':{}}
    for lo,hi in [(0,3),(3,10),(10,25),(25,100)]:
        z=oldmask&(d0>=lo)&(d0<hi)
        report['old_f2b']['bands'][f'{lo}-{hi}']={'tone':stats(detailF['tone'],z),'wg_lt_1_fraction':float(np.mean(detailF['wg'][z]<.999999)),
              'max_channel_R_fraction':float(np.mean(np.argmax(qF[z],axis=-1)==0)),
              'RGB':stats(oldF,z),'jacobian_rgb_per_logL':stats(jF,z)}
    # Fixed geometry: no registration or input modifications.
    for name in ['572A2969','572A2975']:
        srcpath=SOURCES/f'{name}.npz';a=np.load(srcpath);E=np.asarray(a['E'],np.float32)
        mask=a['valid_rgb']&np.all(np.isfinite(E)&(E>0),-1)
        d=a['dreal'];L,q=color_ratios(E,mask)
        fitz=mask&(d>=25)&(d<100)&np.all((B>.05)&(B<.95),axis=-1)
        Lref=float(np.median(L[fitz]))
        old,oldinfo=old_render(L,q);jold=jacobian(lambda delta:old_render(L,q,delta))
        r={'input':str(srcpath),'input_sha256':digest(srcpath),'Lref':Lref,'fit_n':int(fitz.sum()),'models':{},
           'valid_positive_rgb_pixels':int(mask.sum()),'observation_metadata':json.loads(str(a['metadata_json']))}
        results={}
        for fixed in [True,False]:
            key='fixed_slope022' if fixed else 'free_slope'
            params,fitinfo=fit_model(L,q,B,fitz,Lref,fixed)
            rgb,info=common_render(L,q,params,Lref)
            jac=jacobian(lambda delta:common_render(L,q,params,Lref,delta))
            r['models'][key]={'params_anchor_slope_logRG_logBG':params.tolist(),'fit':fitinfo,
                              'training_RGB_residual':stats(rgb-B,fitz),'bands':{}}
            for lo,hi in [(0,3),(3,10),(10,25),(25,100)]:
                z=mask&(d>=lo)&(d<hi)
                r['models'][key]['bands'][f'{lo}-{hi}']={'RGB':stats(rgb,z),'jacobian_rgb_per_logL':stats(jac,z),
                    'old_jacobian_rgb_per_logL':stats(jold,z),'R_derivative_nonpositive_fraction':float(np.mean(jac[...,0][z]<=0)),
                    'common_gain':stats(info['common_gain'],z)}
            results[key]=rgb
            np.savez_compressed(OUT/f'{name}_{key}.npz',RGB=rgb.astype(np.float32),valid=mask,box=box,
                luminance=L.astype(np.float32),smoothed_chromaticity=q.astype(np.float32),
                jacobian_rgb_logL=jac.astype(np.float32),common_gain=info['common_gain'].astype(np.float32),
                params=params,Lref=np.asarray(Lref),dreal=d)
        report['sources'][name]=r
        # All crops are supplemental comparison-only; no output geometry is changed.
        crops={'top':(650,860,210,295),'upper_left':(310,520,275,360),'left':(210,330,600,750)}
        for region,(x0c,x1c,y0c,y1c) in crops.items():
            sl=np.s_[y0c:y1c,x0c:x1c]
            items=[('Current L3',B[sl],np.ones(mask[sl].shape,bool)),
                   ('Old f2b(E source)',old[sl],mask[sl]),
                   ('Common shoulder; slope .22',results['fixed_slope022'][sl],mask[sl]),
                   ('Common shoulder; fitted slope',results['free_slope'][sl],mask[sl])]
            make_panel(items,OUT/f'{name}_{region}_comparison.png',f'{name}: no alignment change; native detail; same RGB display',zoom=True)
    report['script_sha256']=digest(Path(__file__))
    (OUT/'COLOR_PILOT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'out':str(OUT),'old_f2b':report['old_f2b']['bands'],
       'models':{s:{k:{'params':v['params_anchor_slope_logRG_logBG'],'fit_resid':v['training_RGB_residual']['median'],
       'rim_dRGB_dlogL':v['bands']['0-3']['jacobian_rgb_per_logL']['median']} for k,v in z['models'].items()}
            for s,z in report['sources'].items()}},indent=2))

if __name__=='__main__':main()
