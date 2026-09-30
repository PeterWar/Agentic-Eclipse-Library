"""Source-gradient HDR pilot on the previously fixed upper-limb rectangle.

The gradient of a weighted radiance sum contains derivatives of the weights.
Instead combine only differences whose TWO observed endpoints are valid, then
solve a screened Poisson problem over the entire rectangular diagnostic domain.
This is a new exploratory source compositor, not a reproduction of a paper,
not a mask repair, and not yet a validated photographic result.
"""
from pathlib import Path
import json,sys,numpy as np
from scipy.fft import dctn,idctn
from scipy.ndimage import gaussian_filter1d
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng
OUT=ROOT/'output/earthshine_reconstruction_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_RECONSTRUCTION_20260911'

def inputs(path):
    z=np.load(path/'source_arrays.npz');meta=json.loads((path/'source_inputs.json').read_text());names=meta['order']
    g=np.array([z[n+'_g'] for n in names]).astype(float);q=np.array([z[n+'_q'] for n in names]);v=np.array([z[n+'_variance'] for n in names]);weights=[]
    for j,n in enumerate(names):
        valid=np.isfinite(g[j])&np.isfinite(v[j])&(v[j]>0)&(q[j]>0)
        vs,_=ng(v[j],valid,4.);weights.append(np.where(valid,q[j]/np.maximum(vs*meta['alpha'][n],1e-12),0))
    return g,np.array(weights),names

def solve(g,w,length=16,log=True):
    total=w.sum(0);assert np.all(total>0)
    base=np.sum(w*np.nan_to_num(g),axis=0)/total
    good=(w>0)&np.isfinite(g)&(g>0 if log else True)
    u=np.log(np.maximum(np.nan_to_num(g),1e-9)) if log else np.nan_to_num(g)
    b=np.log(base) if log else base
    grads=[];coverage=[]
    for axis in [1,2]:
        sl0=[slice(None)]*3;sl1=sl0.copy();sl0[axis]=slice(None,-1);sl1[axis]=slice(1,None);sl0=tuple(sl0);sl1=tuple(sl1)
        # Harmonic precision of the two endpoints; no fabricated differences
        # across the boundary of a saturated source's support.
        ww=np.where(good[sl0]&good[sl1],2*w[sl0]*w[sl1]/np.maximum(w[sl0]+w[sl1],1e-30),0)
        den=ww.sum(0);gr=np.sum(ww*(u[sl1]-u[sl0]),axis=0)/np.maximum(den,1e-30)
        assert np.all(den>0),'No arbitrary fill for unobserved gradient'
        grads.append(gr);coverage.append(float((den>0).mean()))
    gy,gx=grads;rhs=np.zeros_like(base);rhs[:-1]-=gy;rhs[1:]+=gy;rhs[:,:-1]-=gx;rhs[:,1:]+=gx
    h,wi=base.shape;lap=(2-2*np.cos(np.pi*np.arange(h)/h))[:,None]+(2-2*np.cos(np.pi*np.arange(wi)/wi))[None,:]
    a=1/length**2;uout=idctn(dctn(rhs+a*b,type=2,norm='ortho')/(lap+a),type=2,norm='ortho')
    return (np.exp(uout) if log else uout),base,coverage

def metrics(im):
    core=im[25:52,35:195];df=np.diff(np.log(np.maximum(core,1e-9)),axis=0);j=np.argmin(df,axis=0)
    aa=df[np.maximum(j-1,0),np.arange(160)];bb=df[j,np.arange(160)];cc=df[np.minimum(j+1,len(df)-1),np.arange(160)]
    sub=np.clip(.5*(aa-cc)/np.maximum(aa-2*bb+cc,1e-30),-.5,.5);pos=j+sub
    return dict(max_fractional_drop_median=float(np.median(1-np.exp(bb))),edge_position_highpass_rms=float(np.std(pos-gaussian_filter1d(pos,5))),negative_count=int((im<=0).sum()))

if __name__=='__main__':
    arrays={};rep={}
    for label,path in [('coronal_geometry',ROOT/'output/earthshine_compatibility_20260911/source_pilot'),('lunar_geometry',OUT/'source_pilot')]:
        if not (path/'source_arrays.npz').exists():continue
        g,w,names=inputs(path);results={}
        for mode in ['linear','log']:
            for length in [8,16,32]:
                im,base,coverage=solve(g,w,length,mode=='log');key=f'{mode}_{length}';arrays[label+'_'+key]=im;results[key]=metrics(im)
                # Known common-source signal at all observed endpoints; fixed
                # weights isolate compositor transfer, not the RAW chain.
                yy,xx=np.mgrid[:im.shape[0],:im.shape[1]]
                injections=[]
                for scale in [8,16,32,48,64]:
                    signal=.001*base*np.sin(2*np.pi*(xx+.37*yy)/scale)
                    changed=solve(g+signal[None],w,length,mode=='log')[0]-im
                    m=np.zeros_like(base,bool);m[12:-12,20:-20]=True
                    ratio=float(np.sum(changed[m]*signal[m])/np.sum(signal[m]**2));err=float(np.sqrt(np.mean((changed[m]-signal[m])**2))/np.sqrt(np.mean(signal[m]**2)))
                    injections.append(dict(scale=scale,transfer=ratio,relative_error=err))
                results[key]['fixed_weight_injections']=injections
        arrays[label+'_base']=base;arrays[label+'_short']=g[names.index('572A2976')];results['base']=metrics(base);results['short']=metrics(g[names.index('572A2976')]);rep[label]=results
        print(label,json.dumps(results),flush=True)
    np.savez_compressed(OUT/'C0_gradient_pilot.npz',**arrays)
    (OUT/'C0_gradient_pilot.json').write_text(json.dumps(dict(method=__doc__,nominal_length_pixels=16,sensitivity=[8,16,32],results=rep,limits=['Small rectangle pilot; full-field boundaries and independent Sony judge pending','Injection after RAW mapping with fixed weights is only an operator unit control, not end-to-end transfer','No PSB or original source modified; screening may carry low-frequency HDR bias']),indent=2))
