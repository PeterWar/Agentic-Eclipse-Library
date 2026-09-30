"""Paired perturbations through the actual angular, radial and display chain.

Source perturbation is delta lnG (equivalent to multiplicative radiance).
RAW validity and photometric calibration are frozen, as in these visual layers.
"""
from angular_pilots import *
import angular_pilots as AP
from audit_geometry import polar

def main():
    AP.SIGMAS=(0.,4.,8.);r,t=coords();rep={'seed':300507,'amplitude_lnG':.0001,'components':[],'scope':'same small multiplicative radiance injection in both trains; actual angular normalized convolution, polar/cartesian interpolation, radial regularization, tanh, S/N and refitted H1; fixed RAW support, weights, calibration and post-contrast profiles','transfer':{}}
    rng=np.random.default_rng(rep['seed']);delta=np.zeros_like(r)
    for lam,n in [(96,32),(160,64),(256,128)]:
        ph=rng.uniform(0,2*np.pi,2);delta+=rep['amplitude_lnG']*np.sin(2*np.pi*r/lam+ph[0])*np.cos(n*t+ph[1]);rep['components'].append({'radial_lambda_px':lam,'angular_harmonic':n,'phases':ph.tolist()})
    masks={}
    for tag in ('vixen','sony'):
        old=np.load(CAU/f'{tag}_total.npy' if tag=='vixen' else CAU/'sony_corrected_total.npy',mmap_mode='r')[...,1];masks[tag]=np.load(CAU/f'{tag}_support.npy')&np.isfinite(old)&(old>0)
        AP.angular_pilots(delta,masks[tag],r,t,'inj_'+tag)
    m=masks['vixen']|masks['sony'];wv=(1-smooth(r/RS,2,2.65))*masks['vixen'];wv=np.where(masks['sony'],wv,masks['vixen'].astype('float32'));ws=(1-wv)*masks['sony'];oldrep=json.loads((CAU/'gran_azimuthal_receipt.json').read_text());scale=np.zeros_like(r)
    for tag,w in [('vixen',wv),('sony',ws)]:
        p=oldrep['post_contrast_profiles'][tag];scale+=w*np.interp(np.log(np.maximum(r/RS,1e-5)),p['lnr_centres'],p['robust_contrast']).astype('float32')
    rs=np.arange(1.2*RS,7.5*RS,8,dtype='float32')/RS;fourier={};linear={}
    for s in AP.SIGMAS:
        inj=wv*np.load(D/f'cau/angular_inj_vixen_r{s:g}.npy',mmap_mode='r')+ws*np.load(D/f'cau/angular_inj_sony_r{s:g}.npy',mmap_mode='r');inj=np.where(m,inj/np.maximum(scale,.002),0)
        base=np.load(FIX/'gran_raw.npy' if s==0 else D/f'cau/gran_r{s:g}_raw.npy',mmap_mode='r')
        def render(d):
            sm,_=sn_smooth(.5*np.tanh(d/oldrep['scale_tanh']),m);cen,hist=centre_rings(sm,m,r);a=np.clip(.5+cen,0,1);a[~m]=.5;return a
        # Baselines are unquantized, avoiding one-DN quantization dominating
        # a deliberately tiny injected perturbation.
        a=render(base+inj)-render(base);P=polar(a,CX,CY,RS,rs,nth=2048);fourier[s]=np.fft.rfft(P,axis=1);linear[s]=np.fft.rfft(polar(inj,CX,CY,RS,rs,nth=2048),axis=1)
        log(f'paired injection radial{s:g} through display ready')
    for s in (4.,8.):
        rows=[]
        for c in rep['components']:
            n=c['angular_harmonic']
            for lo,hi in [(1.2,2),(2,3.5),(3.5,5),(5,7.5)]:
                ok=(rs>=lo)&(rs<hi);ref=fourier[0.][ok,n];new=fourier[s][ok,n];lr=linear[0.][ok,n];ln=linear[s][ok,n]
                gain=float(np.real(np.vdot(ref,new))/max(np.real(np.vdot(ref,ref)),1e-30));lg=float(np.real(np.vdot(lr,ln))/max(np.real(np.vdot(lr,lr)),1e-30));corr=float(np.real(np.vdot(ref,new))/np.sqrt(np.real(np.vdot(ref,ref))*np.real(np.vdot(new,new))))
                rows.append({'radial_lambda_px':c['radial_lambda_px'],'angular_harmonic':n,'R':[lo,hi],'linear_relative_gain':lg,'display_relative_gain':gain,'phase_coherence':corr,'PASS_relative_090_110':.90<=gain<=1.10})
        rep['transfer'][str(s)]=rows
    rep['default_r4_PASS']=all(z['PASS_relative_090_110'] for z in rep['transfer']['4.0'])
    rep['soft_r8_PASS_lambda_ge160']=all(z['PASS_relative_090_110'] for z in rep['transfer']['8.0'] if z['radial_lambda_px']>=160)
    savejson(D/'cau/injection_receipt.json',rep);log('Injection finished '+str({k:v for k,v in rep.items() if k.startswith('default') or k.startswith('soft')}))
if __name__=='__main__':main()
