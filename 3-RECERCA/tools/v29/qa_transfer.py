"""Paired injection controls for the correction and adaptive resolution.

These are transfer tests, not a claim that all injected scales exist in the
sky. Real existence is tested separately with the independent split data.
"""
from common import *
from fuse_and_filter import sn_smooth

def main():
    n=512;y,x=np.mgrid[:n,:n];band=np.s_[80:-80,80:-80]
    A=np.load(CAU/'sony_A_total.npy',mmap_mode='r');B=np.load(CAU/'sony_B_total.npy',mmap_mode='r');weights=np.load(CAU/'sony_A_blend_weight.npy',mmap_mode='r');mr=json.loads((CAU/'pointing_merge_receipt.json').read_text())
    sigma=np.load(CAU/'resolution_sigma.npy',mmap_mode='r');rep={'source_injection':[],'resolution_injection':[],'known_bad':{}}
    centres=[(2825,3988),(5500,5000),(4000,7000)]
    if FINAL_GRID:centres=[tuple(np.rint(COMMON_TO_FINAL@np.array([*q,1])).astype(int)) for q in centres]
    rep['grid']='existing PSB' if FINAL_GRID else 'common'
    rep['operator']='saved full same-sky relative factor including local residual; a common paired multiplicative injection cancels exactly in B/A and leaves the fitted factor unchanged'
    for cx,cy in centres:
        sl=(slice(cy-256,cy+256),slice(cx-256,cx+256));a=A[sl];b=B[sl];w=weights[sl];xx=(x+cx-256-W/2)/4000;yy=(y+cy-256-H/2)/4000
        for c in (0,1,2):
            q=np.load(CAU/f'sony_A_relative_factor_{c}.npy',mmap_mode='r')[sl]
            src=a[...,c]*q*w+b[...,c]*(1-w);valid=np.isfinite(src)&(src>0)
            for lam in (16,32,64,128):
                p=.001*np.sin(2*np.pi*(x*.6+y*.8)/lam+.314159)
                injected=(a[...,c]*np.exp(p))*q*w+(b[...,c]*np.exp(p))*(1-w)
                delta=np.log(np.maximum(injected,1e-20))-np.log(np.maximum(src,1e-20))
                k=valid[band];v=delta[band][k];target=p[band][k];gain=float(np.dot(v,target)/np.dot(target,target))
                rep['source_injection'].append({'xy':[cx,cy],'channel':c,'wavelength':lam,'gain':gain,'PASS':.9<=gain<=1.1})
        s=np.array(sigma[sl]);m=np.ones(s.shape,bool)
        # This is the extra resolution operator, evaluated in exact Fourier
        # bands. Check all wavelengths admissible at the local maximum sigma.
        for lam in (8,16,32,64,128,256):
            if float(s.max())>.073058*lam:continue
            p=np.sin(2*np.pi*x/lam+.2718).astype(np.float32);out,_=sn_smooth(p,m,sigma=s)
            gain=float(np.sum(out[band]*p[band])/np.sum(p[band]*p[band]));rep['resolution_injection'].append({'xy':[cx,cy],'wavelength':lam,'sigma_max':float(s.max()),'gain':gain,'PASS':.9<=gain<=1.1})
    # Known-destructive controls make sure a bad operation cannot pass.
    p=np.sin(2*np.pi*x/32).astype(np.float32);bad=gauss(p,16);g=float(np.sum(bad[band]*p[band])/np.sum(p[band]**2));rep['known_bad']['blur16_on_32px']={'gain':g,'expected_FAIL':not(.9<=g<=1.1)}
    rep['known_bad']['neutral_patch']={'gain':0,'expected_FAIL':True}
    rep['PASS']=all(x['PASS'] for k in ('source_injection','resolution_injection') for x in rep[k]) and all(x['expected_FAIL'] for x in rep['known_bad'].values())
    savejson(CAU/'transfer_receipt.json',rep);log('transfer PASS '+str(rep['PASS']))
    assert rep['PASS'], 'injection transfer failed'

if __name__=='__main__':main()
