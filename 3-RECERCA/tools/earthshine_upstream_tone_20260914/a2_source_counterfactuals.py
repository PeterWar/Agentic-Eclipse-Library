"""Trace actual upstream temporal selection and source/display curvature.
All counterfactuals are diagnostics, not image edits. Fourier comparisons use
complete polar rings to avoid exterior-corona leakage into the lunar chart.
"""
from a1_trace import *
from scipy.fft import rfft,irfft

def polar(a):
    th=np.arange(2048)*2*np.pi/2048;rr=np.arange(.5,420,.5)
    mx=(CXT+np.cos(th[:,None])*rr).astype('float32');my=(CYT+np.sin(th[:,None])*rr).astype('float32')
    return cv2.remap(np.nan_to_num(a).astype('float32'),mx,my,cv2.INTER_LINEAR),rr,th,mx,my

def band(p,rr,lo,hi):
    freq=np.arange(p.shape[0]//2+1)[:,None]/(2*np.pi*rr[None,:])
    rise=np.clip((freq-1/(hi*1.5))/(1/hi-1/(hi*1.5)),0,1)
    fall=np.clip((1/(lo/1.5)-freq)/(1/(lo/1.5)-1/lo),0,1)
    h=(.5-.5*np.cos(np.pi*rise))*(.5-.5*np.cos(np.pi*fall));h[0]=0
    return irfft(rfft(p,axis=0)*h,n=p.shape[0],axis=0)

def main():
    c=ROOT/'research/tools/v45_earthshine_20260910/cau'
    aa={k:np.load(c/(k+'.npy')) for k in ['combined_all','combined_reference','vixen_all','vixen_reference','sony_all','sony_reference']}
    z=np.load(ROOT/'output/earthshine_native_psf_20260911/B0_new_all.npz')
    aa.update({'newVixen_'+k:z[k] for k in ['all','reference','candidate']})
    z=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')
    aa.update({'newSony_'+k:z[k] for k in ['all','reference']})
    refs=np.load(ROOT/'output/earthshine_broad_lroc_20260914/arrays/A6_reference_only.npz')
    aa.update({k:refs[k] for k in ['DHS400','DHS530','LROC','V68']})
    aa['V45_display']=np.load(c/'combined_reference_display_u16.npy')[...,1]
    aa['V45_live']=np.load(ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1)
    # Units/gauges differ. Global linear relation is fitted separately on
    # training sectors only for each candidate; mark and test sectors excluded.
    pp={k:polar(v)[0] for k,v in aa.items()}
    _,rr,th,mx,my=polar(aa['combined_all'])
    mask=(mx>=550)&(mx<723)&(my>=902)&(my<1048)
    guard=(mx>=500)&(mx<773)&(my>=852)&(my<1098)
    sectors=(np.arange(2048)*24//2048)[:,None]
    fit=(rr[None,:]>80)&(rr[None,:]<390)&~guard&(sectors%2==0)
    held=(rr[None,:]>80)&(rr[None,:]<390)&~guard&(sectors%2==1)
    rows=[];effects=[]
    for lo,hi in [(32,64),(64,128),(128,256)]:
        bb={k:band(v,rr,lo,hi) for k,v in pp.items()}
        for ref in ['newSony_all','newSony_reference','DHS400','DHS530']:
            b=bb[ref];sd=float(np.std(b[fit]))
            for name,a in bb.items():
                if name.startswith(('DHS','LROC')) or name==ref:continue
                cf=np.linalg.lstsq(np.c_[a[fit],np.ones(fit.sum())],b[fit],rcond=None)[0]
                resid=(cf[0]*a+cf[1]-b)/sd
                row=dict(band_px=[lo,hi],name=name,reference=ref,gain=float(cf[0]),held_rms=float(np.sqrt(np.mean(resid[held]**2))),held_corr=float(np.corrcoef(a[held],b[held])[0,1]),mark_bias=float(np.mean(resid[mask])),mark_rms=float(np.sqrt(np.mean(resid[mask]**2))))
                rows.append(row)
                if ref=='DHS530' and lo==128:print(row,flush=True)
        for pre,post in [('combined_all','combined_reference'),('vixen_all','vixen_reference'),('sony_all','sony_reference'),('newVixen_all','newVixen_reference')]:
            diff=bb[post]-bb[pre]
            effects.append(dict(band_px=[lo,hi],before=pre,after=post,mark_delta_source_DN=q(diff,mask),held_delta_rms=float(np.std(diff[held]))))
    # Relative derivative of the first fixed tone, no inferred physical PSF.
    g=aa['combined_reference'];tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
    deriv=tone['scale']/np.sqrt(tone['soft']**2+(g-tone['mid'])**2)*65535
    save('A2_source_counterfactuals.json',dict(method=__doc__,comparisons=rows,selection_effects=effects,first_tone_derivative_DN16_per_sourceDN=dict(mark=q(deriv,MARK),held=q(deriv,HELD)),scope='Exploratory upstream falsification. References never used in producer; no candidate approved. Angular band excludes m0 and cannot identify radial optical field.'))
    np.savez_compressed(OUT/'arrays/A2_sources.npz',**{k:v.astype('float32') for k,v in aa.items() if not k.startswith(('DHS','LROC','V68'))})
    print('Selection effects',json.dumps(effects,indent=2),flush=True)

if __name__=='__main__':main()
